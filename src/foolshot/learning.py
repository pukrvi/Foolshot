"""Prospective AI paper experiments. The decision commits before outcome data is opened."""

import argparse
import json
from datetime import datetime, time
from pathlib import Path
from time import monotonic
from typing import Literal

from pydantic import AwareDatetime, Field, model_validator

from .audit import DEFAULT_DB, append, history, transaction
from .clock import IST
from .journal import digest, encoded
from .review import dispatch
from .routing import route
from .schemas import Record
from .study import PAPER, attempt, load_settings, state


class Tick(Record):
    at: AwareDatetime
    bid: int = Field(strict=True, gt=0)
    ask: int = Field(strict=True, gt=0)
    bid_qty: int = Field(strict=True, ge=0)
    ask_qty: int = Field(strict=True, ge=0)

    @model_validator(mode="after")
    def ordered(self):
        if self.ask < self.bid:
            raise ValueError("crossed quote")
        return self


class Snapshot(Record):
    case: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    source: Literal["synthetic"]
    symbol: str = Field(min_length=1)
    cutoff: AwareDatetime
    observations: list[Tick] = Field(min_length=1)

    @model_validator(mode="after")
    def point_in_time(self):
        times = [v.at for v in self.observations]
        local = self.cutoff.astimezone(IST)
        if not time(9, 45) <= local.time() < time(14, 30):
            raise ValueError("outside regular fixture entry window")
        if sorted(set(times)) != times or times[-1] > self.cutoff:
            raise ValueError("future or unordered decision evidence")
        if any(t.astimezone(IST).date() != local.date() for t in times):
            raise ValueError("fixture spans multiple sessions")
        if (self.cutoff - times[-1]).total_seconds() > 10:
            raise ValueError("stale decision quote")
        return self


class Decision(Record):
    action: Literal["pass", "long"]
    hypothesis: str = Field(min_length=1)
    evidence: list[int] = Field(min_length=1)
    invalidation: str = Field(min_length=1)
    used_memory_ids: list[str] = Field(default_factory=list)
    probability_up_pct: int = Field(ge=0, le=100, strict=True)
    limit: int = Field(ge=0, strict=True)
    stop: int = Field(ge=0, strict=True)
    target: int = Field(ge=0, strict=True)


class OperationsReview(Record):
    right: str = Field(min_length=1)
    wrong_or_unknown: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    next_check: str = Field(min_length=1)


class Reflection(OperationsReview):
    hypothesis: str = Field(min_length=1)
    test_on_later_data: str = Field(min_length=1)
    rejection_criterion: str = Field(min_length=1)
    proposed_harness_change: str = Field(min_length=1)


def model_record(path, session, key, prompt, schema, client, invoke, check, task):
    with transaction(path) as db:
        selected = route(db, client, task)
        spec = {
            "client": client,
            "prompt": prompt,
            "schema": schema.model_json_schema(),
            "route": selected,
        }
        append(db, session, "model_request", spec, key + "/request")
        saved = db.execute("SELECT payload FROM history WHERE id=?", (key,)).fetchone()
        if saved:
            return json.loads(saved[0])
    # Concurrent invocations can cost another model call. Only the first result becomes operative.
    started = monotonic()
    try:
        wire = json.dumps(spec, ensure_ascii=False, separators=(",", ":"))
        if invoke is None:
            raw, receipt = dispatch(path, selected, wire)
        else:
            raw = invoke(client, wire)
            receipt = {**selected, "release": None, "basis": "test_double"}
        obj = schema.model_validate_json(raw)
        check(obj)
        result = {"valid": True, "value": obj.model_dump(), "raw": raw}
    except (ValueError, OSError) as exc:
        result = {"valid": False, "error": str(exc), "raw": locals().get("raw")}
    result["receipt"] = locals().get(
        "receipt", dict(selected, basis="no_verified_response", release=None)
    )
    result["latency_ms"] = round((monotonic() - started) * 1000)
    with transaction(path) as db:
        saved = db.execute("SELECT payload FROM history WHERE id=?", (key,)).fetchone()
        if saved:
            append(db, session, "redundant_response", {"request": key, **result})
            return json.loads(saved[0])
        append(db, session, "model_response", result, key)
    return result


def memory(db, cutoff):
    day = cutoff.astimezone(IST).date().isoformat()
    retained = []
    for r in history(db):
        if r["kind"] == "reflection" and (
            r["payload"]["through"] < day
            or (
                r["payload"].get("available_after")
                and datetime.fromisoformat(r["payload"]["available_after"]) < cutoff
            )
        ):
            retained.append({"id": r["id"], "reflection": r["payload"]["lesson"]})
        elif r["kind"] == "trial_verdict" and r["payload"]["through"] < day:
            retained.append(
                {"id": r["id"], "prior_theory_assessment": r["payload"]["assessment"]}
            )
        elif r["kind"] == "case_result":
            # Compare instants explicitly; offsets can differ between fixture files.
            if datetime.fromisoformat(r["payload"]["end"]) < cutoff:
                retained.append({"id": r["id"], "result": r["payload"]["result"]})
        elif (
            r["kind"] == "owner_decision"
            and datetime.fromisoformat(r["recorded"]) <= cutoff
        ):
            retained.append({"id": r["id"], "steer": r["payload"]["text"]})
    weekly = [entry for entry in retained if "/weekly/" in entry["id"]]
    recent = retained[-11:]
    if weekly and weekly[-1] not in recent:
        recent.insert(0, weekly[-1])
    return recent


def run_case(
    path,
    snapshot_file,
    future_file,
    client,
    invoke=None,
    *,
    adaptive=True,
    model_id=None,
):
    snap = Snapshot.model_validate_json(snapshot_file.read_bytes())
    day = snap.cutoff.astimezone(IST).date()
    session = "cases/" + snap.case
    key = session + "/decision"
    settings = load_settings()
    with transaction(path) as db:
        earlier = history(db, session, exact=True)
        frozen = next(
            (r["payload"] for r in earlier if r["kind"] == "decision_context"), None
        )
        if frozen is None:
            prior_cases = [
                r for r in history(db, "cases/") if r["kind"] == "decision_context"
            ]
            completed = {
                r["session"]: r
                for r in history(db, "cases/")
                if r["kind"] == "case_result"
            }
            for prior in prior_cases:
                last = completed.get(prior["session"])
                if (
                    not last
                    or datetime.fromisoformat(last["payload"]["end"]) >= snap.cutoff
                ):
                    raise ValueError(
                        "resolve previous case or advance beyond its outcome before another decision"
                    )
            ledger = state(history(db, PAPER), day, settings)
            frozen = {
                "snapshot": snap.model_dump(mode="json"),
                "memory": memory(db, snap.cutoff) if adaptive else [],
                "ledger": ledger,
                "policy": settings.model_dump(),
                "client": client,
                "model_id": model_id,
                "adaptive": adaptive,
            }
            append(db, session, "decision_context", frozen, session + "/context")
        if (
            frozen["snapshot"] != snap.model_dump(mode="json")
            or frozen["adaptive"] != adaptive
            or frozen["model_id"] != model_id
            or frozen["client"] != client
            or frozen["policy"] != settings.model_dump()
        ):
            raise ValueError("case already frozen under different inputs")
    prompt = {
        "task": "Choose pass or a long paper entry, form a falsifiable hypothesis, cite zero-based observation indices. Forecast the probability that the closing observed bid exceeds the last decision ask. List any memory IDs that influenced the decision. Prices in paise. Return only JSON matching schema. Memory contains unvalidated hypotheses.",
        "context": frozen,
    }

    def validate(choice):
        if not set(choice.used_memory_ids) <= {m["id"] for m in frozen["memory"]}:
            raise ValueError("unavailable memory cited")
        if any(i < 0 or i >= len(snap.observations) for i in choice.evidence):
            raise ValueError("unknown observation")
        if (
            choice.action == "long"
            and not 0 < choice.stop < choice.limit < choice.target
        ):
            raise ValueError("invalid long bracket")

    response = model_record(
        path, session, key, prompt, Decision, client, invoke, validate, "decision"
    )
    # Outcome file intentionally opened only after the decision is durable.
    future = [Tick.model_validate(x) for x in json.loads(future_file.read_bytes())]
    times = [q.at for q in future]
    if sorted(set(times)) != times or any(
        t <= snap.cutoff or t.astimezone(IST).date() != day for t in times
    ):
        raise ValueError("invalid post-decision timeline")
    ticks = []
    for i, q in enumerate(future):
        local = q.at.astimezone(IST).time()
        if local >= time(15, 30):
            raise ValueError("outcome after regular fixture session")
        window = "entry"
        if local >= time(15):
            window = "flatten"
        elif local >= time(14, 30) or (q.at - snap.cutoff).total_seconds() > 60:
            window = "observe"
        ticks.append([i + 1, q.bid, q.ask, q.bid_qty, q.ask_qty, window])
    with transaction(path) as db:
        append(
            db,
            session,
            "outcome_tape",
            {"quotes": [q.model_dump(mode="json") for q in future]},
            session + "/tape",
        )
        existing = db.execute(
            "SELECT payload FROM history WHERE id=?", (session + "/result",)
        ).fetchone()
        if existing:
            return json.loads(existing[0])
    choice = response.get("value", {})
    if choice.get("action") == "long":
        try:
            result = attempt(
                path,
                day,
                key,
                choice["hypothesis"],
                ticks,
                settings,
                levels=[choice[k] for k in ("limit", "stop", "target")],
                decision=key,
            )
        except ValueError as exc:
            result = {"outcome": "blocked", "reason": str(exc), "net_paise": None}
    else:
        result = {
            "outcome": "pass" if response["valid"] else "invalid_response_pass",
            "net_paise": 0,
        }
    score = None
    if response["valid"] and future:
        observed = int(future[-1].bid > snap.observations[-1].ask)
        score = {
            "probability_up_pct": choice["probability_up_pct"],
            "observed_up": observed,
            "brier": (choice["probability_up_pct"] / 100 - observed) ** 2,
        }
    output = {
        "forecast_score": score,
        "decision": key,
        "end": (times[-1] if times else snap.cutoff).isoformat(),
        "date": str(day),
        "result": result,
        "frozen_cash_comparator_net_paise": 0,
    }
    with transaction(path) as db:
        append(db, session, "case_result", output, session + "/result")
    return output


def dream(path, day, period, client, invoke=None, *, boundary=None):
    from datetime import timedelta

    first = day - timedelta(days=day.weekday()) if period == "weekly" else day
    session = f"dream/{period}/{day}"
    with transaction(path) as db:
        rows = history(db)
        if period in ("position", "incident"):
            results = [
                r
                for r in rows
                if r["kind"] == "case_result"
                and r["payload"]["date"] == str(day)
                and (boundary is None or r["id"] == boundary)
            ]
            if not results:
                raise ValueError("no case result for position review")
            rows = [r for r in rows if r["seq"] <= results[-1]["seq"]]
        relevant = {
            r["session"]
            for r in rows
            if r["kind"] == "case_result"
            and str(first) <= r["payload"]["date"] <= str(day)
        }
        evidence = [
            r
            for r in rows
            if r["session"] in relevant
            or (
                r["session"].startswith(PAPER)
                and str(first) <= r["session"][6:] <= str(day)
            )
            or (
                period == "weekly"
                and r["kind"] == "reflection"
                and r["payload"]["period"] in ("position", "daily", "incident")
                and str(first) <= r["payload"]["through"] <= str(day)
            )
        ]
        if not evidence:
            raise ValueError("no recorded evidence for this review")
        if period in ("daily", "weekly") and not any(
            r["kind"] == "close" and r["session"] == PAPER + str(day) for r in evidence
        ):
            raise ValueError("close the final session before a daily or weekly review")
    # Raw tapes, duplicated model requests and historical prompt contexts remain in SQLite.
    evidence = [
        r
        for r in evidence
        if r["kind"]
        not in {
            "model_request",
            "decision_context",
            "fixture_depth",
            "outcome_tape",
            "paper_mark",
        }
    ]
    ids = {r["id"] for r in evidence}
    prompt = {
        "task": "Return JSON only. Audit pre-entry hypotheses against actual paper outcomes and fees. Say what went right, wrong or is unknown. Cite event IDs. For weekly dreaming generate a novel falsifiable alternative or harness fix; specify later data, acceptance and rejection. No changes to risk limits.",
        "period": period,
        "events": [
            {
                "id": r["id"],
                "kind": r["kind"],
                "data": (
                    r["payload"].get("value", {"valid": False})
                    if r["kind"] == "model_response"
                    else {"request_logged": True}
                    if r["kind"] == "model_request"
                    else r["payload"]
                ),
            }
            for r in evidence
        ],
    }

    schema = Reflection if period in {"weekly", "incident"} else OperationsReview
    if schema is OperationsReview:
        prompt["task"] = (
            "Summarise observed results and faults. Cite supplied IDs. List one operational check. Do not originate hypotheses, strategy changes or trade instructions. Return only JSON matching the schema."
        )

    def validate(reflection):
        if not set(reflection.evidence_ids) <= ids:
            raise ValueError("unknown review evidence ID")

    key = session + "/" + digest(encoded([sorted(ids), client]))
    response = model_record(
        path, session, key, prompt, schema, client, invoke, validate, period
    )
    if response["valid"]:
        available = (
            max(
                (r["payload"]["end"] for r in evidence if r["kind"] == "case_result"),
                key=datetime.fromisoformat,
                default=None,
            )
            if period in ("position", "incident")
            else None
        )
        with transaction(path) as db:
            append(
                db,
                session,
                "reflection",
                {
                    "through": str(day),
                    "period": period,
                    "available_after": available,
                    "lesson": response["value"],
                    "status": "hypothesis_pending_future_test",
                },
                key + "/lesson",
            )
    return response


def main():
    from datetime import date

    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = cli.add_subparsers(dest="action", required=True)
    run = sub.add_parser("case")
    run.add_argument("snapshot", type=Path)
    run.add_argument("outcome", type=Path)
    reflect = sub.add_parser("dream")
    reflect.add_argument("period", choices=["daily", "weekly", "incident", "position"])
    reflect.add_argument("day", type=date.fromisoformat)
    for cmd in (run, reflect):
        cmd.add_argument("--client", choices=["codex", "claude"], required=True)
    args = cli.parse_args()
    if args.action == "case":
        result = run_case(args.db, args.snapshot, args.outcome, args.client)
        day = date.fromisoformat(result["date"])
        with transaction(args.db) as db:
            incident = any(
                r["kind"] == "review_requested"
                and r["payload"]["postcheck"]
                == str(result["result"].get("intent")) + "/post"
                for r in history(db, PAPER + str(day), exact=True)
            )
        if incident:
            dream(args.db, day, "incident", args.client)
        elif result["result"]["outcome"] in (
            "paper_stop",
            "paper_target",
            "daily_stop",
        ):
            dream(args.db, day, "position", args.client)
    else:
        result = dream(args.db, args.day, args.period, args.client)
    print(json.dumps(result))
    return int(result.get("valid") is False)


if __name__ == "__main__":
    raise SystemExit(main())
