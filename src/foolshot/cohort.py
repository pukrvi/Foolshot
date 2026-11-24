"""Paired, restartable paper experiment with matched frozen and adaptive model arms."""

import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from .audit import append, history, transaction
from .clock import IST
from .journal import digest, encoded
from .learning import Snapshot, dream, run_case
from .routing import selections
from .study import close_day, load_settings


def run(manifest_path, directory, client, model=None, invoke=None):
    plan = json.loads(manifest_path.read_bytes())
    routes = selections(client, model)
    existing = directory / "adaptive.sqlite3"
    if existing.is_file():
        with transaction(existing) as db:
            registration = db.execute(
                "SELECT payload FROM history WHERE id='registration'"
            ).fetchone()
        if registration:
            saved = json.loads(registration[0])
            if saved.get("model_routes") and (
                model is None or model == saved["model_routes"]["thinking"]
            ):
                routes = saved["model_routes"]
    model = routes["thinking"]
    groups = defaultdict(list)
    cases = set()
    last = None
    hashes = {}
    for row in plan["cases"]:
        before = manifest_path.parent / row["snapshot"]
        after = manifest_path.parent / row["outcome"]
        snap = Snapshot.model_validate_json(before.read_bytes())
        if snap.case in cases or (last and snap.cutoff <= last):
            raise ValueError("duplicate or nonchronological case in study manifest")
        cases.add(snap.case)
        groups[snap.cutoff.astimezone(IST).date()].append((before, after))
        hashes[snap.case] = {
            "snapshot": digest(before.read_bytes()),
            "outcome": digest(after.read_bytes()),
        }
        last = snap.cutoff
    sessions = [date.fromisoformat(d) for d in plan["sessions"]]
    if (
        not sessions
        or sorted(set(sessions)) != sessions
        or not set(groups) <= set(sessions)
    ):
        raise ValueError("invalid session roster")
    source_hash = digest(
        encoded(
            {
                p.name: digest(p.read_bytes())
                for p in sorted(Path(__file__).parent.glob("*.py"))
            }
        )
    )
    meta = {
        "plan": plan,
        "client": client,
        "model": model,
        "model_routes": routes,
        "source": source_hash,
        "snapshots": hashes,
        "policy": load_settings().model_dump(),
        "metric": "paired daily net P&L after fixture cost",
    }
    for arm in ("adaptive", "frozen"):
        dbpath = directory / (arm + ".sqlite3")
        with transaction(dbpath) as db:
            append(db, "study", "preregistration", meta | {"arm": arm}, "registration")
    for i, day in enumerate(sessions):
        for arm in ("adaptive", "frozen"):
            dbpath = directory / (arm + ".sqlite3")
            if arm == "frozen":
                with transaction(directory / "adaptive.sqlite3") as db:
                    pin = db.execute(
                        "SELECT id,payload FROM history WHERE id=?",
                        (f"model-pin/{client}/thinking",),
                    ).fetchone()
                if pin:
                    with transaction(dbpath) as db:
                        append(
                            db,
                            "routing",
                            "model_release_pin",
                            json.loads(pin["payload"]),
                            pin["id"],
                        )
            for before, after in groups[day]:
                result = run_case(
                    dbpath,
                    before,
                    after,
                    client,
                    invoke,
                    adaptive=arm == "adaptive",
                    model_id=model,
                )
                if arm == "adaptive":
                    with transaction(dbpath) as db:
                        triggers = [
                            r
                            for r in history(db, "paper/" + str(day), exact=True)
                            if r["kind"] == "review_requested"
                            and r["payload"]["postcheck"]
                            == str(result["result"].get("intent")) + "/post"
                        ]
                    if triggers:
                        dream(
                            dbpath,
                            day,
                            "incident",
                            client,
                            invoke,
                            boundary=result["decision"].rsplit("/", 1)[0] + "/result",
                        )
                    elif result["result"]["outcome"] in (
                        "paper_stop",
                        "paper_target",
                        "daily_stop",
                        "session_exit",
                    ):
                        dream(
                            dbpath,
                            day,
                            "position",
                            client,
                            invoke,
                            boundary=result["decision"].rsplit("/", 1)[0] + "/result",
                        )
            close_day(dbpath, day)
            if arm == "adaptive":
                checks = [dream(dbpath, day, "daily", client, invoke)]
                end_week = day.weekday() == 4 or (
                    i + 1 < len(sessions)
                    and sessions[i + 1].isocalendar()[:2] != day.isocalendar()[:2]
                )
                if end_week:
                    checks.append(dream(dbpath, day, "weekly", client, invoke))
                if not all(c["valid"] for c in checks):
                    raise ValueError(
                        "invalid model reflection; evidence preserved for investigation"
                    )
        if end_week:
            from .trials import challenge

            challenge(directory, day, client, invoke)
    path = export(directory)
    from .publication import update_report

    update_report(directory, path)
    return path


def export(directory):
    economics = {}
    for arm in ("adaptive", "frozen"):
        dbpath = directory / (arm + ".sqlite3")
        if not dbpath.is_file():
            raise ValueError("missing study arm")
        with transaction(dbpath) as db:
            rows = history(db)
        totals = {}
        for r in rows:
            if r["kind"] == "close":
                day = r["session"][6:]
                day_cases = {
                    x["session"] for x in rows
                    if x["kind"] == "case_result" and x["payload"]["date"] == day
                }
                snapshots = [x["payload"]["snapshot"] for x in rows
                             if x["kind"] == "decision_context" and x["session"] in day_cases]
                modes = {s["source"] for s in snapshots}
                if len(modes) > 1:
                    raise ValueError("mixed historical and synthetic decisions")
                # Equity is realized P&L plus the current marked position.
                realized = peak = drawdown = cost = vetoes = 0
                entry = None
                for event in rows:
                    if event["session"] != r["session"]:
                        continue
                    kind, info = event["kind"], event["payload"]
                    if kind == "risk_rejected":
                        vetoes += 1
                    elif kind == "paper_entry":
                        entry = info["price"]
                    elif kind == "paper_mark":
                        equity = realized + info["net_paise"]
                        peak = max(peak, equity)
                        drawdown = max(drawdown, peak - equity)
                    elif kind in {"paper_stop", "paper_target", "session_exit", "daily_stop"}:
                        realized += info["net_paise"]
                        cost += (info["price"] - entry) * info["quantity"] - info["net_paise"]
                cases = [
                    x["payload"]["result"]["outcome"]
                    for x in rows
                    if x["kind"] == "case_result" and x["payload"]["date"] == day
                ]
                scores = [
                    x["payload"]["forecast_score"]["brier"]
                    for x in rows
                    if x["kind"] == "case_result"
                    and x["payload"]["date"] == day
                    and x["payload"]["forecast_score"] is not None
                ]
                totals[day] = {
                    "mode": next(iter(modes), "synthetic"),
                    "marked_drawdown_paise": drawdown,
                    "fill_cost_paise": cost,
                    "risk_vetoes": vetoes,
                    "decision_latency_ms": sum(x["payload"]["latency_ms"] for x in rows
                                               if x["session"] in day_cases and x["kind"] == "model_response"),
                    "scored_forecasts": len(scores),
                    "mean_brier": sum(scores) / len(scores) if scores else "",
                    "net_paise": r["payload"]["net_paise"],
                    "attempts": r["payload"]["attempts"],
                    "passes": cases.count("pass"),
                    "invalid": cases.count("invalid_response_pass"),
                    "blocked": cases.count("blocked"),
                    "opportunities": len(cases),
                    "close_id": r["id"],
                }
        economics[arm] = totals
    if (
        not economics["adaptive"]
        or economics["adaptive"].keys() != economics["frozen"].keys()
    ):
        raise ValueError("matched session close records required for both arms")
    target = directory / "paired_daily.csv"
    fields = [
        "date",
        "mode",
        "arm",
        "net_paise",
        "marked_drawdown_paise",
        "fill_cost_paise",
        "risk_vetoes",
        "decision_latency_ms",
        "attempts",
        "passes",
        "invalid",
        "blocked",
        "opportunities",
        "scored_forecasts",
        "mean_brier",
        "close_id",
        "adaptive_minus_frozen_paise",
    ]
    with target.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for day in sorted(economics["adaptive"]):
            difference = (
                economics["adaptive"][day]["net_paise"]
                - economics["frozen"][day]["net_paise"]
            )
            for arm in economics:
                writer.writerow(
                    {
                        "arm": arm,
                        "date": day,
                        **economics[arm][day],
                        "adaptive_minus_frozen_paise": difference,
                    }
                )
    return target


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("manifest", type=Path)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--client", choices=["codex", "claude"], required=True)
    cli.add_argument("--model", help="Optional explicit thinking-tier release")
    args = cli.parse_args()
    print(run(args.manifest, args.directory, args.client, args.model))


if __name__ == "__main__":
    main()
