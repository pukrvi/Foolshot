"""Single long-position stop drill using integer paise and synthetic depth."""

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from .journal import digest, record
from .replay import ROOT
from .schemas import Settings


@dataclass(frozen=True)
class LossRoom:
    available_cash: int
    daily_remaining: int
    weekly_remaining: int
    study_remaining: int
    attempts: int
    consecutive_losses: int
    occupied: bool


def permitted_quantity(settings, room, entry, stop, cost_per_share):
    if not 0 < stop < entry or cost_per_share <= 0:
        raise ValueError("invalid long stop or cost allowance")
    if (
        room.occupied
        or room.attempts >= settings.max_attempts
        or room.consecutive_losses >= 3
    ):
        return 0
    budget = min(
        settings.trade_loss_paise,
        room.daily_remaining,
        room.weekly_remaining,
        room.study_remaining,
    )
    return max(
        0,
        min(
            settings.pilot_exposure_paise // entry,
            room.available_cash // (entry + cost_per_share),
            budget // (entry - stop + cost_per_share),
        ),
    )


def drill(settings, ticks, room=None, levels=None):
    # One frozen synthetic intent. Each element represents a later observed quote.
    limit, stop, target = levels or (50_000, 49_600, 51_000)
    cost = 50  # Synthetic allowance per share, in paise.
    if not 0 < stop < limit < target:
        raise ValueError("invalid long bracket")
    room = room or LossRoom(
        settings.capital_paise,
        settings.daily_loss_paise,
        settings.weekly_loss_paise,
        settings.study_loss_paise,
        0,
        0,
        False,
    )
    size = permitted_quantity(settings, room, limit, stop, cost)
    events = [
        {
            "kind": "paper_intent",
            "quantity": size,
            "limit": limit,
            "stop": stop,
            "target": target,
        }
    ]
    if not size:
        return events + [{"kind": "risk_rejected"}]
    entry = None
    previous = 0
    for tick in ticks:
        seq, bid, ask, bid_qty, ask_qty = tick[:5]
        window = tick[5] if len(tick) == 6 else "entry"
        if len(tick) not in (5, 6) or window not in ("entry", "observe", "flatten"):
            raise ValueError("invalid fixture window")
        if seq <= previous or not 0 < bid <= ask or min(bid_qty, ask_qty) < 0:
            raise ValueError("invalid fixture quote")
        previous = seq
        if entry is not None:
            events.append(
                {
                    "kind": "paper_mark",
                    "sequence": seq,
                    "bid": bid,
                    "quantity": size,
                    "net_paise": size * (bid - entry - cost),
                }
            )
        if entry is None:
            if window != "entry" or bid <= stop or ask > limit or ask_qty < size:
                continue
            entry = ask
            events.append(
                {"kind": "paper_entry", "sequence": seq, "price": ask, "quantity": size}
            )
        elif (
            window == "flatten"
            or bid <= stop
            or bid >= target
            or size * (entry - bid + cost) >= room.daily_remaining
        ):
            if bid_qty < size:
                return events + [
                    {"kind": "unresolved_exit", "sequence": seq, "open_quantity": size}
                ]
            events.append(
                {
                    "kind": "paper_stop"
                    if bid <= stop
                    else (
                        "paper_target"
                        if bid >= target
                        else ("session_exit" if window == "flatten" else "daily_stop")
                    ),
                    "sequence": seq,
                    "price": bid,
                    "quantity": size,
                    "net_paise": size * (bid - entry - cost),
                }
            )
            return events
    return events + [{"kind": "unfilled" if entry is None else "unresolved_exit"}]


def main():
    settings = (ROOT / "config/experiment.yaml").read_bytes()
    fixture = (ROOT / "tests/fixtures/dhan_stop_drill.json").read_bytes()
    inputs = {"settings": settings, "ticks": fixture}
    events = drill(
        Settings.model_validate(yaml.safe_load(settings)), json.loads(fixture)
    )
    manifest = {
        "schema": 1,
        "broker_design": "dhan",
        "mode": "synthetic_stop_drill",
        "code": digest(Path(__file__).read_bytes()),
        "inputs": {k: digest(v) for k, v in inputs.items()},
    }
    run = record(ROOT / "data/runs/dhan-drill.sqlite3", manifest, events, inputs)
    print(json.dumps({"run_id": run, "mode": manifest["mode"], "events": events}))
    return int(events[-1]["kind"] != "paper_stop")


if __name__ == "__main__":
    raise SystemExit(main())
