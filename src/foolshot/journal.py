import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


def encoded(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def journal_metadata(db):
    db.execute(
        """CREATE TABLE IF NOT EXISTS event_times(id TEXT PRIMARY KEY REFERENCES events(id), recorded_utc TEXT NOT NULL)"""
    )
    for op in ("UPDATE", "DELETE"):
        db.execute(
            f"""CREATE TRIGGER IF NOT EXISTS immutable_event_times_{op} BEFORE {op} ON event_times BEGIN SELECT RAISE(ABORT,'append-only journal'); END"""
        )
    db.execute("""CREATE VIEW IF NOT EXISTS events_with_actor AS
        SELECT e.*, 'software' AS actor_type, 'Foolshot' AS actor_name, NULL AS model_release,
        t.recorded_utc, coalesce(json_extract(e.body,'$.quote.exchange'),json_extract(e.body,'$.received')) AS source_time
        FROM events e LEFT JOIN event_times t ON e.id=t.id""")


def record(
    path: Path, manifest: dict, events: list[dict], inputs: dict[str, bytes]
) -> str:
    """Commit one small fixture run atomically, verifying any existing copy."""
    run_id = digest(encoded(manifest))
    rows = []
    for seq, event in enumerate(events):
        body = encoded(event).decode()
        event_id = digest(encoded([run_id, seq, event]))
        rows.append((run_id, seq, event_id, body))
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=15)) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("""CREATE TABLE IF NOT EXISTS runs
                   (id TEXT PRIMARY KEY, manifest TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS events
                   (run_id TEXT REFERENCES runs(id), seq INTEGER, id TEXT UNIQUE,
                    body TEXT NOT NULL, PRIMARY KEY(run_id, seq))""")
        db.execute("""CREATE TABLE IF NOT EXISTS artifacts
                   (hash TEXT PRIMARY KEY, content BLOB NOT NULL)""")
        for table in ("runs", "events", "artifacts"):
            for operation in ("UPDATE", "DELETE"):
                db.execute(f"""CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation}
                               BEFORE {operation} ON {table} BEGIN
                               SELECT RAISE(ABORT, 'append-only journal'); END""")
        with db:
            db.execute("BEGIN IMMEDIATE")
            journal_metadata(db)
            for key, data in inputs.items():
                checksum = manifest["inputs"][key]
                db.execute(
                    "INSERT OR IGNORE INTO artifacts VALUES (?,?)", (checksum, data)
                )
                saved = db.execute(
                    "SELECT content FROM artifacts WHERE hash=?", (checksum,)
                ).fetchone()
                if saved != (data,):
                    raise ValueError(f"stored artifact differs for {key}")
            previous = db.execute(
                "SELECT manifest FROM runs WHERE id=?", (run_id,)
            ).fetchone()
            manifest_text = encoded(manifest).decode()
            if previous is None:
                db.execute("INSERT INTO runs VALUES (?,?)", (run_id, manifest_text))
                db.executemany("INSERT INTO events VALUES (?,?,?,?)", rows)
                recorded = datetime.now(UTC).isoformat()
                db.executemany(
                    "INSERT INTO event_times VALUES (?,?)",
                    [(row[2], recorded) for row in rows],
                )
            else:
                saved = db.execute(
                    "SELECT * FROM events WHERE run_id=? ORDER BY seq", (run_id,)
                ).fetchall()
                if previous != (manifest_text,) or saved != rows:
                    raise ValueError("stored run differs from replay")
    return run_id
