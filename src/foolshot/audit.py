"""Private, append-only event stream shared by the paper runner and both clients."""

import json
import sqlite3
from contextlib import closing, contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .journal import digest, encoded
from .provenance import attribute, install

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data/private/audit.sqlite3"


@contextmanager
def transaction(path):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with closing(sqlite3.connect(path, timeout=20)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS history (
            seq INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, session TEXT NOT NULL,
            kind TEXT NOT NULL, recorded TEXT NOT NULL, payload TEXT NOT NULL)""")
        db.execute("CREATE INDEX IF NOT EXISTS by_session ON history(session,seq)")
        for op in ("UPDATE", "DELETE"):
            db.execute(f"""CREATE TRIGGER IF NOT EXISTS history_{op} BEFORE {op} ON history
                BEGIN SELECT RAISE(ABORT,'append-only'); END""")
        with db:
            db.execute("BEGIN IMMEDIATE")
            install(db)
            yield db


def append(db, session, kind, payload, event_id=None):
    event_id = event_id or str(uuid4())
    body = encoded(payload).decode()
    row = db.execute(
        "SELECT session,kind,payload FROM history WHERE id=?", (event_id,)
    ).fetchone()
    if row:
        if tuple(row) != (session, kind, body):
            raise ValueError("event ID reused with different content")
    else:
        db.execute(
            "INSERT INTO history(id,session,kind,recorded,payload) VALUES(?,?,?,?,?)",
            (event_id, session, kind, datetime.now(UTC).isoformat(), body),
        )
        attribute(db, event_id, kind, payload)
    return event_id


def history(db, prefix="", *, exact=False):
    predicate = "session=?" if exact else "substr(session,1,length(?))=?"
    args = (prefix,) if exact else (prefix, prefix)
    rows = db.execute(
        f"SELECT * FROM history_with_actor WHERE {predicate} ORDER BY seq", args
    )
    return [dict(row) | {"payload": json.loads(row["payload"])} for row in rows]


def capture_hook(path, raw):
    # The hooks can also be installed at user scope. Never capture another project.
    cwd = Path(raw["cwd"]).resolve()
    if not cwd.is_relative_to(ROOT):
        return
    session = "chat/" + raw["session_id"]
    prompt = raw["prompt"]
    if not isinstance(prompt, str):
        raise TypeError("missing prompt")
    turn = raw.get("turn_id")
    key = digest(encoded([session, turn, "prompt"])) if turn else None
    with transaction(path) as db:
        append(db, session, "user_input", {"text": prompt}, key)
