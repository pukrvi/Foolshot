"""Derivative research report; full prompts and receipts stay in the private databases."""

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

from .audit import append, history, transaction


def update_report(directory: Path, csv_path: Path):
    with csv_path.open(newline="") as f:
        daily = list(csv.DictReader(f))
    weeks = defaultdict(dict)
    for row in daily:
        iso = date.fromisoformat(row["date"]).isocalendar()
        arms = weeks[(iso.year, iso.week)]
        arms.setdefault(row["arm"], []).append(row)
    lines = [
        "# Paired paper experiment",
        "",
        ("Historical quotes with simulated fills" if any(row["mode"] == "historical" for row in daily)
         else "Synthetic fixture fills") + " with a fixed per-share allowance. Each arm uses the same dated opportunity roster.",
        "Difference measures the entire adaptive workflow, including different decisions about passing. Model and hosting costs are unmeasured.",
        "",
        "| ISO week | Sessions | Adaptive net ₹ | Frozen net ₹ | Difference ₹ | Prior weekly hypotheses available |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    with transaction(directory / "adaptive.sqlite3") as db:
        reflections = [
            r for r in history(db, "dream/weekly/") if r["kind"] == "reflection"
        ]
        for (year, week), arms in sorted(weeks.items()):
            a, b = arms["adaptive"], arms["frozen"]
            if [r["date"] for r in a] != [r["date"] for r in b]:
                raise ValueError("unmatched sessions")
            net_a = sum(int(r["net_paise"]) for r in a)
            net_b = sum(int(r["net_paise"]) for r in b)
            earlier = [r for r in reflections if r["payload"]["through"] < a[0]["date"]]
            prior = earlier[-1]["id"] if earlier else None
            result = {
                "first": a[0]["date"],
                "last": a[-1]["date"],
                "sessions": len(a),
                "adaptive_net_paise": net_a,
                "frozen_net_paise": net_b,
                "prior_weekly_reflection": prior,
                "difference_paise": net_a - net_b,
            }
            append(
                db,
                "research/paired",
                "prospective_comparison",
                result,
                "comparison/" + a[-1]["date"],
            )
            lines.append(
                f"| {year}-W{week:02d} | {len(a)} | {net_a / 100:.2f} | {net_b / 100:.2f} | {(net_a - net_b) / 100:.2f} | {'Yes' if prior else 'No'} |"
            )
    lines += [
        "",
        "Use the trace IDs in paired_daily.csv to inspect the private close records. A better week alone cannot establish that a particular lesson caused the difference.",
    ]
    path = directory / "study_report.md"
    path.write_text("\n".join(lines) + "\n")
    return path
