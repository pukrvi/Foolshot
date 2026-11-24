"""Ask the AI to challenge a previous weekly theory using only later, paired sessions."""

from datetime import date, timedelta
from typing import Literal

from pydantic import Field

from .audit import append, history, transaction
from .journal import digest, encoded
from .learning import Reflection, model_record
from .schemas import Record


class TrialVerdict(Record):
    verdict: Literal["inconclusive", "weakened", "consistent"]
    evidence_ids: list[str] = Field(min_length=1)
    interpretation: str = Field(min_length=1)
    competing_explanation: str = Field(min_length=1)
    next_experiment: str = Field(min_length=1)


def challenge(directory, day: date, client, invoke):
    start = day - timedelta(days=day.weekday())
    adaptive = directory / "adaptive.sqlite3"
    with transaction(adaptive) as db:
        older = [
            r
            for r in history(db, "dream/weekly/")
            if r["kind"] == "reflection" and r["payload"]["through"] < str(start)
        ]
    if not older:
        return None
    theory = older[-1]
    result = []
    for arm in ("adaptive", "frozen"):
        with transaction(directory / (arm + ".sqlite3")) as db:
            for r in history(db):
                evidence_day = (
                    r["session"][6:]
                    if r["kind"] == "close"
                    else r["payload"].get("date")
                    if r["kind"] == "case_result"
                    else None
                )
                if evidence_day and str(start) <= evidence_day <= str(day):
                    result.append(
                        {
                            "id": arm + "/" + r["id"],
                            "kind": r["kind"],
                            "date": evidence_day,
                            "data": r["payload"],
                        }
                    )
    closed = [
        {
            r["date"]
            for r in result
            if r["kind"] == "close" and r["id"].startswith(arm + "/")
        }
        for arm in ("adaptive", "frozen")
    ]
    if not closed[0] or closed[0] != closed[1] or str(day) not in closed[0]:
        raise ValueError(
            "both study arms must close before testing a weekly hypothesis"
        )
    lesson = Reflection.model_validate(theory["payload"]["lesson"])
    prompt = {
        "task": "Test the earlier theory against subsequent matched observations. Cite only supplied later event IDs. If the proposed test was not run or data are insufficient, return inconclusive. Correlation cannot establish the cause. Offer a competing explanation and next experiment. Return JSON matching the schema.",
        "theory_id": theory["id"],
        "hypothesis": lesson.hypothesis,
        "proposed_test": lesson.test_on_later_data,
        "rejection_criterion": lesson.rejection_criterion,
        "later_evidence": result,
    }
    ids = {r["id"] for r in result}

    def validate(verdict):
        if not set(verdict.evidence_ids) <= ids:
            raise ValueError("trial verdict refers to unavailable evidence")

    session = f"trials/{day}"
    key = session + "/" + digest(encoded(prompt))
    reply = model_record(
        adaptive, session, key, prompt, TrialVerdict, client, invoke, validate, "trial"
    )
    if reply["valid"]:
        with transaction(adaptive) as db:
            append(
                db,
                session,
                "trial_verdict",
                {
                    "through": str(day),
                    "theory": theory["id"],
                    "assessment": reply["value"],
                },
                key + "/verdict",
            )
    return reply
