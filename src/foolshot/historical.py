"""Run a regular NSE equity session from archived top-of-book quotes."""

import argparse
import csv
import io
import json
import os
import tempfile
from datetime import date, datetime, time
from pathlib import Path
from time import monotonic

from .clock import IST
from .cohort import run
from .journal import digest
from .learning import Snapshot, Tick


def prepare(tape, directory, day, symbol, provider, cutoff, research=None):
    raw = tape.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    fields = ["at", "symbol", "bid", "ask", "bid_qty", "ask_qty"]
    if sorted(reader.fieldnames or []) != sorted(fields):
        raise ValueError("required CSV fields: " + ",".join(fields))
    boundary = datetime.combine(day, cutoff, IST)
    if day.weekday() >= 5:
        raise ValueError("regular weekday sessions only")
    ticks = []
    for i, row in enumerate(reader, start=2):
        stamp = datetime.fromisoformat(row["at"])
        if stamp.tzinfo is None or row["symbol"] != symbol:
            raise ValueError(f"row {i}: expected offset-aware time and {symbol}")
        stamp = stamp.astimezone(IST)
        if stamp.date() != day or not time(9, 15) <= stamp.time() < time(15, 30):
            raise ValueError(f"row {i}: outside requested session")
        if ticks and stamp <= ticks[-1].at:
            raise ValueError(f"row {i}: timestamps must increase")
        ticks.append(Tick(at=stamp, **{key: int(row[key]) for key in fields[2:]}))
    before = [q for q in ticks if q.at <= boundary]
    after = [q for q in ticks if q.at > boundary]
    if not after or after[-1].at.time() < time(15):
        raise ValueError("missing afternoon flattening observations")
    evidence = research.read_bytes() if research else b"[]"
    snap = Snapshot(case=f"historical-{day}", symbol=symbol, source="historical",
                    provider=provider, cutoff=boundary, preparation=json.loads(evidence),
                    observations=before[-60:])
    plan = {"study": "historical-equity", "sessions": [str(day)],
            "input_sha256": digest(raw), "research_sha256": digest(evidence),
            "cases": [{"snapshot": "snapshot.json", "outcome": "outcome.json"}]}
    files = {"quotes.csv": raw, "preparation.json": evidence,
             "manifest.json": json.dumps(plan).encode(),
             "snapshot.json": snap.model_dump_json().encode(),
             "outcome.json": json.dumps([q.model_dump(mode="json") for q in after]).encode()}
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "inputs"
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        staged = Path(tmp) / "inputs"
        staged.mkdir()
        for name, body in files.items():
            (staged / name).write_bytes(body)
        if not target.exists():
            try:
                staged.rename(target)
            except OSError:
                if not target.is_dir():
                    raise
        if any((target / n).read_bytes() != b for n, b in files.items()):
            raise ValueError("registered inputs differ; use a fresh study directory")
    return target / "manifest.json"


def main():
    os.umask(0o077)
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("tape", type=Path)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--day", type=date.fromisoformat, required=True)
    cli.add_argument("--symbol", required=True)
    cli.add_argument("--provider", required=True)
    cli.add_argument("--cutoff", type=time.fromisoformat, default=time(10))
    cli.add_argument("--research", type=Path)
    cli.add_argument("--client", choices=("codex", "claude"), default="codex")
    args = cli.parse_args()
    started = monotonic()
    manifest = prepare(args.tape, args.directory, args.day, args.symbol, args.provider,
                       args.cutoff, args.research)
    report = run(manifest, args.directory, args.client)
    print(json.dumps({"results": str(report), "elapsed_seconds": round(monotonic()-started, 3)}))


if __name__ == "__main__":
    main()
