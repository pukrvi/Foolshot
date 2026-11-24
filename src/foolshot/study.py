"""One paper book. Sessions use synthetic sequenced depth; no broker clients."""

import json
from datetime import date, timedelta

import yaml

from .audit import ROOT, append, history, transaction
from .journal import digest, encoded
from .paper_drill import LossRoom, drill
from .schemas import Settings

PAPER = "paper/"


def state(rows, day, settings):
    principal = settings.capital_paise
    tradable, reserve, streak, daily, weekly, lifetime, attempts = (
        principal,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    pending = set()
    halted = closed = False
    last_check = None
    week = day - timedelta(days=day.weekday())
    withdrawn = 0
    for row in rows:
        session_day = date.fromisoformat(row["session"][len(PAPER) :])
        if session_day > day:
            raise ValueError("paper book already contains a later session")
        item, kind = row["payload"], row["kind"]
        if kind == "intent":
            pending.add(row["id"])
            attempts += session_day == day
        elif kind == "postcheck":
            last_check = row["id"]
            if not item["unresolved"]:
                pending.discard(item["intent"])
            pnl = item["net_paise"]
            if pnl is not None:
                tradable += pnl
                lifetime += pnl
                daily += pnl if session_day == day else 0
                weekly += pnl if session_day >= week else 0
                if pnl:
                    streak = streak + 1 if pnl < 0 else 0
            halted |= session_day == day and daily <= -settings.daily_loss_paise
        elif kind == "withdrawal_record":
            reserve -= item["amount_paise"]
            withdrawn += item["amount_paise"]
        elif kind == "close":
            tradable -= item["reserved_paise"]
            reserve += item["reserved_paise"]
            closed |= session_day == day
    return {
        "tradable": min(tradable, principal),
        "book_balance": tradable,
        "reserve": reserve,
        "withdrawn": withdrawn,
        "daily": daily,
        "weekly": weekly,
        "study": lifetime,
        "streak": streak,
        "attempts": attempts,
        "pending": sorted(pending),
        "closed": closed,
        "halted": halted,
        "latest_postcheck": last_check,
    }


def load_settings():
    return Settings.model_validate(
        yaml.safe_load((ROOT / "config/experiment.yaml").read_bytes())
    )


def attempt(
    path, day, key, thesis, ticks, settings=None, *, levels=None, decision=None
):
    settings = settings or load_settings()
    if not thesis.strip() or not key.strip():
        raise ValueError("intent ID and pre-entry thesis required")
    session = PAPER + day.isoformat()
    intent = digest(encoded([session, key]))
    specification = {
        "key": key,
        "thesis": thesis,
        "ticks_hash": digest(encoded(ticks)),
        "levels": list(levels or (50000, 49600, 51000)),
        "decision": decision,
        "model": "linked-model-decision" if decision else "fixed-fixture-rule-v1",
        "policy": settings.model_dump(),
        "engine_hash": digest((ROOT / "src/foolshot/paper_drill.py").read_bytes()),
    }
    with transaction(path) as db:
        rows = history(db, PAPER)
        previous = next((r for r in rows if r["id"] == intent), None)
        if previous:
            if previous["payload"]["specification"] != specification:
                raise ValueError("conflicting intent retry")
            stored = previous["payload"]
        else:
            current = state(rows, day, settings)
            if rows and rows[-1]["session"] != session:
                prior = rows[-1]["session"]
                if not any(
                    r["session"] == prior and r["kind"] == "close" for r in rows
                ):
                    raise ValueError("previous session requires close")
            if (
                current["pending"]
                or current["closed"]
                or current["halted"]
                or current["streak"] >= 3
            ):
                raise ValueError("paper session closed, unresolved or under review")
            room = LossRoom(
                current["tradable"],
                settings.daily_loss_paise + min(0, current["daily"]),
                settings.weekly_loss_paise + min(0, current["weekly"]),
                settings.study_loss_paise + min(0, current["study"]),
                current["attempts"],
                current["streak"],
                False,
            )
            if rows and any(
                r["kind"] == "intent"
                and r["payload"]["specification"]["policy"] != settings.model_dump()
                for r in rows
            ):
                raise ValueError("start a separate study for a new risk policy")
            if current["attempts"] >= settings.max_attempts:
                raise ValueError("daily attempt cap reached")
            stored = {
                "specification": specification,
                "room": vars(room),
                "prior_check": current["latest_postcheck"],
                "evidence": "see linked decision and pre-entry packet"
                if decision
                else "frozen synthetic long fixture",
            }
            append(db, session, "intent", stored, intent)
    # A crash here leaves a durable decision. Repeating its key resumes the same fixture.
    with transaction(path) as db:
        result_id = intent + "/post"
        existing = db.execute(
            "SELECT payload FROM history WHERE id=?", (result_id,)
        ).fetchone()
        if existing:
            return json.loads(existing[0])
        events = drill(settings, ticks, LossRoom(**stored["room"]), levels)
        append(
            db,
            session,
            "fixture_depth",
            {"intent": intent, "ticks": ticks},
            intent + "/depth",
        )
        tape = (
            db.execute(
                "SELECT payload FROM history WHERE id=?",
                (decision.rsplit("/", 1)[0] + "/tape",),
            ).fetchone()
            if decision
            else None
        )
        quote_times = [q["at"] for q in json.loads(tape[0])["quotes"]] if tape else []
        for i, event in enumerate(events):
            seq = event.get("sequence")
            if seq and quote_times:
                event["occurred_at"] = quote_times[seq - 1]
            append(
                db, session, event["kind"], {"intent": intent, **event}, f"{intent}/{i}"
            )
        outcome = events[-1]
        result = {
            "intent": intent,
            "outcome": outcome["kind"],
            "net_paise": outcome.get("net_paise"),
            "unresolved": outcome["kind"] == "unresolved_exit",
        }
        append(db, session, "postcheck", result, result_id)
        current = state(history(db, PAPER), day, settings)
        reasons = []
        if current["streak"] >= 3:
            reasons.append("three_consecutive_net_losses")
        if current["halted"]:
            reasons.append("daily_loss_limit")
        if current["pending"]:
            reasons.append("unresolved_position")
        if reasons:
            append(
                db,
                session,
                "review_requested",
                {"reasons": reasons, "postcheck": result_id},
                intent + "/review",
            )
        return result


def close_day(path, day):
    settings = load_settings()
    with transaction(path) as db:
        rows = history(db, PAPER)
        session = PAPER + day.isoformat()
        existing = next(
            (r for r in rows if r["session"] == session and r["kind"] == "close"), None
        )
        if existing:
            return existing["payload"]
        current = state(rows, day, settings)
        if current["pending"]:
            raise ValueError("unresolved intent or exposure blocks close")
        if (
            rows
            and rows[-1]["session"] != session
            and not any(
                r["kind"] == "close" and r["session"] == rows[-1]["session"]
                for r in rows
            )
        ):
            raise ValueError("previous session requires close")
        amount = max(0, current["book_balance"] - settings.capital_paise)
        summary = {
            "net_paise": current["daily"],
            "attempts": current["attempts"],
            "streak": current["streak"],
            "reserved_paise": amount,
            "total_reserved_paise": current["reserve"] + amount,
            "next_tradable_paise": current["book_balance"] - amount,
            "postchecks": [
                r["id"]
                for r in rows
                if r["session"] == session and r["kind"] == "postcheck"
            ],
        }
        append(db, session, "close", summary, session + "/close")
        return summary


def record_transfer(path, day, reference, amount):
    """Record a manual paper reserve transfer after close, with no effect on sizing or P&L."""
    if not reference.strip() or type(amount) is not int or amount <= 0:
        raise ValueError("a transfer needs a reference and positive integer paise")
    event_id = "reserve-transfer/" + reference
    session = PAPER + str(day)
    payload = {"reference": reference, "amount_paise": amount}
    with transaction(path) as db:
        previous = db.execute(
            "SELECT session,payload FROM history WHERE id=?", (event_id,)
        ).fetchone()
        if previous:
            if previous[0] != session or json.loads(previous[1]) != payload:
                raise ValueError("conflicting manual transfer record")
            return event_id
        current = state(history(db, PAPER), day, load_settings())
        if not current["closed"] or amount > current["reserve"]:
            raise ValueError("close the session and use only reserved funds")
        return append(db, session, "withdrawal_record", payload, event_id)
