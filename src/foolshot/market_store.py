"""Private immutable market inputs and revision-aware, read-only evidence queries."""

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing, contextmanager
from datetime import UTC, date, datetime
from pathlib import Path

SESSION = date(2026, 11, 23)
CUTOFF = "2026-11-23T00:00:00+05:30"
DB_NAME = "market.sqlite3"
DATASETS = (
    "equity_daily", "equity_delivery", "listings", "corporate_actions",
    "derivatives_daily", "intraday_bars", "quotes", "trades",
    "option_chain_snapshots", "contract_specs", "calendar", "indices", "macro",
    "flows", "filings", "news", "economic_events",
)
AVAILABILITY = ("verified", "inferred", "unknown")
REFERENCE_DATA = ("listings", "corporate_actions", "contract_specs", "calendar", "economic_events")
SCHEMA = """
CREATE TABLE IF NOT EXISTS receipt (
    id TEXT PRIMARY KEY, dataset TEXT NOT NULL, source TEXT NOT NULL,
    url TEXT NOT NULL, raw_sha256 TEXT NOT NULL, raw_bytes INTEGER NOT NULL,
    acquired_at TEXT NOT NULL, outcome_only INTEGER NOT NULL CHECK(outcome_only IN (0,1)),
    notes TEXT NOT NULL, records INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS observation (
    receipt_id TEXT NOT NULL REFERENCES receipt(id), dataset TEXT NOT NULL,
    source TEXT NOT NULL, record_key TEXT NOT NULL, session TEXT,
    symbol TEXT, event_at TEXT, event_source_time TEXT,
    available_at TEXT, availability_source_time TEXT,
    availability TEXT NOT NULL CHECK(availability IN ('verified','inferred','unknown')),
    availability_basis TEXT NOT NULL, values_json TEXT NOT NULL CHECK(json_valid(values_json)),
    PRIMARY KEY (receipt_id, record_key)
);
CREATE INDEX IF NOT EXISTS observations_by_cutoff
ON observation(dataset, availability, session, symbol, available_at);
CREATE INDEX IF NOT EXISTS observations_by_revision
ON observation(dataset, source, record_key, available_at);
"""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def instant(value):
    stamp = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(stamp, datetime) or stamp.utcoffset() is None:
        raise ValueError("timestamp must include a UTC offset")
    return stamp.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sha256_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def raw_blob(root, source_path):
    """Publish a complete hash-addressed blob without replacing an existing object."""
    raw = Path(root) / "raw"
    raw.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile(dir=raw, prefix=".stage-", delete=False) as scratch:
        staging = Path(scratch.name)
        try:
            with Path(source_path).open("rb") as source:
                shutil.copyfileobj(source, scratch)
            scratch.flush()
            os.fsync(scratch.fileno())
            size, sha = staging.stat().st_size, sha256_file(staging)
            target = raw / sha[:2] / sha
            target.parent.mkdir(exist_ok=True, mode=0o700)
            try:
                os.link(staging, target)
            except FileExistsError:
                if sha256_file(target) != sha:
                    raise ValueError("stored raw blob failed its SHA-256 check") from None
            return sha, size, target
        finally:
            staging.unlink(missing_ok=True)


@contextmanager
def read_db(root):
    path = (Path(root) / DB_NAME).resolve()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=30)) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        with db:
            db.execute("BEGIN")
            yield db


def row_data(row, dataset, source, receipt_id):
    key = row["key"]
    if not isinstance(key, str) or not key.strip():
        raise ValueError("record key must be a nonempty string")
    day = row.get("session")
    if day is not None:
        day = date.fromisoformat(str(day)).isoformat()
    event, available = row.get("event_at"), row.get("available_at")
    event_utc = instant(event) if event is not None else None
    available_utc = instant(available) if available is not None else None
    availability = row["availability"]
    if availability not in AVAILABILITY or (availability == "unknown") != (available_utc is None):
        raise ValueError("availability type and timestamp disagree")
    basis = row["availability_basis"]
    if not isinstance(basis, str) or not basis.strip():
        raise ValueError("an availability basis is required")
    if not isinstance(row["values"], dict):
        raise ValueError("values must be an object")
    if event_utc and available_utc and available_utc < event_utc and dataset not in REFERENCE_DATA:
        raise ValueError("observation availability precedes its event")
    return (
        receipt_id, dataset, source, key, day, row.get("symbol"), event_utc,
        str(event) if event is not None else None, available_utc,
        str(available) if available is not None else None, availability, basis,
        canonical(row["values"]),
    )


def ingest_batch(root, *, dataset, source, url, raw_path, rows, acquired_at=None,
                 outcome_only=False, notes=""):
    """Ingest a source file in one transaction. Identical normalized reruns add zero rows.

    Incorporate source version and partition in the source URL if the provider's single
    object is openly reused across independent subsets. A changed raw object is a new
    receipt. Raw bytes may survive a failed import so a parser fix can reuse them.
    """
    root = Path(root)
    if dataset not in DATASETS or not source.strip() or not url.strip():
        raise ValueError("known dataset and attributable source are required")
    sha, size, _ = raw_blob(root, raw_path)
    receipt_id = hashlib.sha256(
        canonical([dataset, source, url, sha, bool(outcome_only)]).encode()
    ).hexdigest()
    acquisition = instant(acquired_at or datetime.now(UTC))
    path = root / DB_NAME
    with closing(sqlite3.connect(path, timeout=60)) as db:
        db.execute("PRAGMA busy_timeout=60000")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(SCHEMA)
        with db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT records FROM receipt WHERE id=?", (receipt_id,)).fetchone()
            if existing:
                return {"receipt_id": receipt_id, "raw_sha256": sha, "records": existing[0], "inserted": 0}
            db.execute("INSERT INTO receipt VALUES (?,?,?,?,?,?,?,?,?,0)", (
                receipt_id, dataset, source, url, sha, size, acquisition, int(outcome_only), notes,
            ))
            before = db.total_changes
            db.executemany("INSERT INTO observation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                row_data(row, dataset, source, receipt_id) for row in rows
            ))
            count = db.total_changes - before
            if not count:
                raise ValueError("source contains no normalized records")
            db.execute("UPDATE receipt SET records=? WHERE id=?", (count, receipt_id))
    return {"receipt_id": receipt_id, "raw_sha256": sha, "records": count, "inserted": count}


def _latest_query(dataset, cutoff, *, through=None, symbol=None, source=None):
    cutoff_utc = instant(cutoff)
    local_cutoff = datetime.fromisoformat(cutoff) if isinstance(cutoff, str) else cutoff
    # Date-only daily observations require a completed session in the exchange's timezone.
    from .clock import IST
    prior_boundary = local_cutoff.astimezone(IST).date().isoformat()
    where = [
        "o.dataset = ?", "o.availability = 'verified'", "o.available_at < ?",
        "r.outcome_only = 0",
    ]
    bind = [dataset, cutoff_utc]
    if dataset not in REFERENCE_DATA:
        where.extend([
            "(o.event_at IS NOT NULL OR o.session IS NOT NULL)",
            "(o.event_at IS NULL OR o.event_at < ?)",
        ])
        bind.append(cutoff_utc)
        where.append("(o.session IS NULL OR o.session < ? OR (? AND o.event_at IS NOT NULL))")
        bind.extend([prior_boundary, dataset in ("intraday_bars", "quotes", "trades", "option_chain_snapshots", "news", "filings")])
    if symbol is not None:
        where.append("o.symbol = ?")
        bind.append(symbol)
    if through is not None:
        where.append("o.session <= ?")
        bind.append(date.fromisoformat(str(through)).isoformat())
    if source is not None:
        where.append("o.source = ?")
        bind.append(source)
    cte = """
        WITH eligible AS (
            SELECT o.*, r.url, r.raw_sha256, r.acquired_at,
                   DENSE_RANK() OVER (
                       PARTITION BY o.source,o.record_key ORDER BY o.available_at DESC
                   ) AS version
            FROM observation o JOIN receipt r ON r.id=o.receipt_id
            WHERE """ + " AND ".join(where) + """
        ), best AS (
            SELECT source, record_key, MIN(receipt_id) AS receipt_id
            FROM eligible WHERE version=1 GROUP BY source,record_key
            HAVING COUNT(DISTINCT values_json)=1
        ), latest AS (
            SELECT e.* FROM eligible e JOIN best b ON
                e.source=b.source AND e.record_key=b.record_key AND e.receipt_id=b.receipt_id
            WHERE e.version=1
        )
    """
    return cte, bind


def observations(root, dataset, cutoff, *, through=None, symbol=None, source=None, limit=100):
    """Select bounded observations strictly before cutoff and resolve versions per source."""
    if dataset not in DATASETS:
        raise ValueError("unknown dataset")
    if not 1 <= limit <= 2_000:
        raise ValueError("evidence limit must be between 1 and 2000")
    cte, bind = _latest_query(dataset, cutoff, through=through, symbol=symbol, source=source)
    with read_db(root) as db:
        rows = db.execute(cte + """
            SELECT dataset,source,record_key,session,symbol,event_at,event_source_time,
                   available_at,availability_source_time,availability_basis,values_json,
                   url,raw_sha256,acquired_at,receipt_id
            FROM latest
            ORDER BY COALESCE(session, '') DESC, COALESCE(event_at, '') DESC,
                     available_at DESC, source, record_key LIMIT ?
        """, (*bind, limit))
        result = []
        for row in rows:
            record = dict(row)
            record["values"] = json.loads(record.pop("values_json"))
            result.append(record)
        return result
