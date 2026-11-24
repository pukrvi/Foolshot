import argparse
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

import yaml

from .clock import IST, hours_for, phase
from .journal import digest, record
from .schemas import Calendar, Master, Quote, Settings

ROOT = Path(__file__).resolve().parents[2]


def read_quotes(data: bytes, day, hours, master):
    instruments = {item.symbol: item for item in master.instruments}
    if len(instruments) != len(master.instruments):
        raise ValueError("duplicate instrument in master")
    quotes = {}
    duplicates = 0
    for line in data.splitlines():
        if not line.strip():
            continue
        quote = Quote.model_validate_json(line)
        instrument = instruments.get(quote.symbol)
        if instrument is None or any(p % instrument.tick_paise for p in (quote.bid, quote.ask)):
            raise ValueError(f"unknown instrument or off-tick price for {quote.id}")
        if quote.exchange.astimezone(IST).date() != day or phase(quote.exchange, day, hours) in {"holiday", "closed"}:
            raise ValueError(f"quote {quote.id} outside selected session")
        if quote.id in quotes:
            if quotes[quote.id] != quote:
                raise ValueError(f"conflicting quote ID {quote.id}")
            duplicates += 1
        quotes[quote.id] = quote
    return sorted(quotes.values(), key=lambda q: (q.received, q.exchange, q.id)), duplicates


def replay(day: date, paths: dict[str, Path], database: Path):
    inputs = {}
    missing = []
    for key, path in paths.items():
        try:
            inputs[key] = path.read_bytes()
        except FileNotFoundError:
            missing.append(key)
    module_dir = Path(__file__).parent
    code = {p.name: digest(p.read_bytes()) for p in sorted(module_dir.glob("*.py"))}
    manifest = {
        "schema": 1, "missing": sorted(missing), "mode": "replay", "source": "synthetic", "date": day.isoformat(),
        "inputs": {k: digest(v) for k, v in inputs.items()}, "code": code,
    }
    events = []
    try:
        if missing:
            raise ValueError("missing inputs: " + ", ".join(sorted(missing)))
        config = Settings.model_validate(yaml.safe_load(inputs["settings"]))
        calendar = Calendar.model_validate_json(inputs["calendar"])
        hours = hours_for(calendar, day)
        master = Master.model_validate_json(inputs["instruments"])
        if master.effective_date > day:
            raise ValueError("instrument master is from the future")
        quotes, duplicates = read_quotes(inputs["quotes"], day, hours, master)
        if hours and not quotes:
            raise ValueError("open session has no fixture quotes")
        events.append({"kind": "session", "study": config.study_id, "limits": config.model_dump(),
                       "hours": hours.model_dump(mode="json") if hours else None})
        for quote in quotes:
            events.append({"kind": "quote", "phase": phase(quote.received, day, hours),
                           "quote": quote.model_dump(mode="json")})
        result = {"status": "completed" if hours else "holiday", "quotes": len(quotes),
                  "duplicate_rows": duplicates}
    except (ValueError, yaml.YAMLError) as exc:
        result = {"status": "blocked", "reason": str(exc)}
    events.append({"kind": "outcome", **result})
    return {"run_id": record(database, manifest, events, inputs), "mode": "replay", **result}


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay one synthetic Foolshot fixture session")
    parser.add_argument("--date", type=date.fromisoformat, default=date(2026, 1, 12))
    defaults = {"settings": "config/experiment.yaml", "calendar": "config/calendar/fixture.json",
                "instruments": "tests/fixtures/instruments.json", "quotes": "tests/fixtures/quotes.jsonl"}
    for key, path in defaults.items():
        parser.add_argument(f"--{key}", type=Path, default=ROOT / path)
    parser.add_argument("--db", type=Path, default=ROOT / "data/runs/foolshot.sqlite3")
    args = parser.parse_args()
    try:
        result = replay(args.date, {key: getattr(args, key) for key in defaults}, args.db)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return int(result["status"] == "blocked")


if __name__ == "__main__":
    raise SystemExit(main())
