"""Attribution stored beside immutable event payloads, including legacy events."""

import json

OWNER = "Puneet Vishnawat"


def install(db):
    if db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='view' AND name='history_with_actor'"
    ).fetchone():
        return
    db.execute("""CREATE TABLE IF NOT EXISTS attribution(
        event_id TEXT PRIMARY KEY REFERENCES history(id), actor_type TEXT NOT NULL,
        actor_name TEXT NOT NULL, model_release TEXT, identity_basis TEXT NOT NULL,
        decision_id TEXT, decision_actor TEXT, decision_release TEXT)""")
    for op in ("UPDATE", "DELETE"):
        db.execute(f"""CREATE TRIGGER IF NOT EXISTS attribution_{op} BEFORE {op} ON attribution
                     BEGIN SELECT RAISE(ABORT,'append-only attribution'); END""")
    db.execute("""CREATE VIEW IF NOT EXISTS history_with_actor AS SELECT h.*, a.actor_type,a.actor_name,
                  a.model_release,a.identity_basis,a.decision_id,a.decision_actor,a.decision_release
                  FROM history h JOIN attribution a ON a.event_id=h.id""")
    missing = db.execute("""SELECT h.id,h.kind,h.payload FROM history h LEFT JOIN attribution a ON a.event_id=h.id
                          WHERE a.event_id IS NULL ORDER BY h.seq""").fetchall()
    for row in missing:
        attribute(db, row[0], row[1], json.loads(row[2]), legacy=True)


def attribute(db, event_id, kind, payload, *, legacy=False):
    actor, name, release, basis = "software", "Foolshot", None, "event_type"
    cause = payload.get("decision") or payload.get("intent") or payload.get("postcheck")
    if kind == "intent":
        cause = payload.get("specification", {}).get("decision")
    if kind in ("user_input", "owner_decision", "withdrawal_record"):
        actor, name, basis = "human", OWNER, "project_owner"
    if kind in (
        "model_response",
        "redundant_response",
        "review_proposal",
        "question",
        "lesson",
        "change_proposal",
    ):
        receipt = payload.get("receipt") or {}
        release = receipt.get("release")
        if receipt.get("basis") == "test_double":
            actor, name, basis = "fixture", "scripted-test-double", "test_double"
        elif release:
            actor, name, basis = "model", release, receipt["basis"]
        else:
            actor, name, basis = (
                "unknown",
                "Unverified author",
                "legacy_unrecorded" if legacy else "no_verified_response",
            )
    if payload.get("owner_authored") and kind in (
        "question",
        "lesson",
        "change_proposal",
    ):
        actor, name, basis = "human", OWNER, "author_declared"
    if kind in ("reflection", "trial_verdict"):
        cause = event_id.rsplit("/", 1)[0]
    parent = (
        db.execute("SELECT * FROM attribution WHERE event_id=?", (cause,)).fetchone()
        if isinstance(cause, str)
        else None
    )
    decision_actor = decision_release = None
    if parent:
        decision_actor = parent["decision_actor"] or parent["actor_name"]
        decision_release = parent["decision_release"] or parent["model_release"]
        cause = parent["decision_id"] or cause
        if kind in ("reflection", "trial_verdict"):
            actor, name, release, basis = (
                parent[k]
                for k in ("actor_type", "actor_name", "model_release", "identity_basis")
            )
    db.execute(
        "INSERT INTO attribution VALUES(?,?,?,?,?,?,?,?)",
        (
            event_id,
            actor,
            name,
            release,
            basis,
            cause,
            decision_actor,
            decision_release,
        ),
    )
