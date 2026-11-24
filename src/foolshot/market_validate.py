"""Measure local historical coverage and report evidence eligibility and gaps."""

import argparse
import json
from pathlib import Path

from .market_download import write_json
from .market_store import CUTOFF, DATASETS, DB_NAME, SESSION, _latest_query, read_db, sha256_file

DAILY = {"equity_daily", "equity_delivery", "derivatives_daily", "indices", "flows"}
INTRADAY = {"intraday_bars", "quotes", "trades", "option_chain_snapshots"}
REQUEST_START = {
    key: ("2025-11-23" if key in INTRADAY else
          "2025-11-24" if key in {"derivatives_daily", "contract_specs"} else
          "2023-11-23" if key == "indices" else
          "2021-11-23" if key in {"macro", "flows", "filings", "news", "economic_events"} else
          "2023-11-23")
    for key in DATASETS
}
THROUGH = "2026-11-22"

# Adapters retain their own numeric units. Ratio checks compare fields in the same unit.
OHLC_ERROR = """
    CASE WHEN dataset IN ('equity_daily','derivatives_daily','intraday_bars','indices')
         AND open_price IS NOT NULL AND high IS NOT NULL AND low IS NOT NULL AND close IS NOT NULL
         AND (MIN(open_price,high,low,close) < 0 OR
              (MIN(open_price,high,low,close) > 0 AND
               (low > MIN(open_price,close) OR high < MAX(open_price,close))))
         THEN 1 ELSE 0 END
"""


def _metrics(db):
    fields = ", ".join(
        f"COALESCE(json_extract(values_json,'$.{field}_paise'),"
        f"json_extract(values_json,'$.{field}_rupees'),json_extract(values_json,'$.{field}')) AS {alias}"
        for field, alias in (("open", "open_price"), ("high", "high"), ("low", "low"), ("close", "close"))
    )
    return [dict(row) for row in db.execute(f"""
        WITH prices AS (
            SELECT o.*,r.outcome_only, {fields},
              COALESCE(json_extract(values_json,'$.volume_shares'),json_extract(values_json,'$.volume')) AS volume,
              json_extract(values_json,'$.delivery_shares') AS delivery,
              json_extract(values_json,'$.delivery_pct') AS delivery_pct,
              COALESCE(NULLIF(json_extract(values_json,'$.contract_id'),''),NULLIF(json_extract(values_json,'$.isin'),''),symbol) AS instrument
            FROM observation o JOIN receipt r ON r.id=o.receipt_id
        )
        SELECT dataset,source,outcome_only,COUNT(*) AS normalized_rows,COUNT(DISTINCT record_key) AS record_keys,
               COUNT(DISTINCT instrument) AS instruments,COUNT(DISTINCT session) AS sessions,
               MIN(session) AS from_session,MAX(session) AS through_session,
               MIN(json_extract(values_json,'$.valid_from')) AS first_valid_from,
               MAX(json_extract(values_json,'$.valid_to')) AS last_valid_to,
               SUM(availability='verified') AS verified_timestamp_rows,
               SUM(availability='inferred') AS inferred_rows,SUM(availability='unknown') AS unknown_rows,
               SUM({OHLC_ERROR}) AS invalid_ohlc,
               SUM(CASE WHEN volume<0 OR delivery<0 OR delivery>volume
                        OR delivery_pct<0 OR delivery_pct>100 THEN 1 ELSE 0 END) AS invalid_quantity,
               SUM(CASE WHEN dataset IN ('equity_daily','derivatives_daily','intraday_bars','indices')
                        AND (open_price IS NULL OR high IS NULL OR low IS NULL OR close IS NULL)
                        THEN 1 ELSE 0 END) AS incomplete_ohlc
        FROM prices GROUP BY dataset,source,outcome_only ORDER BY dataset,source,outcome_only
    """)]


def validate(root, cutoff=CUTOFF):
    root = Path(root)
    with read_db(root) as db:
        integrity = [r[0] for r in db.execute("PRAGMA quick_check")]
        refs = [dict(r) for r in db.execute("SELECT * FROM receipt ORDER BY dataset,source,id")]
        receipt_counts = dict(db.execute("SELECT receipt_id,count(*) FROM observation GROUP BY receipt_id"))
        metrics = _metrics(db)
        covered = {}
        for dataset in DATASETS:
            cte, bind = _latest_query(dataset, cutoff)
            covered[dataset] = [dict(row) for row in db.execute(cte + """
                SELECT source, COUNT(*) AS eligible_rows, MIN(session) AS from_session,
                       MAX(session) AS through_session, MAX(available_at) AS max_available_at_utc
                FROM latest GROUP BY source
            """, bind)]
        days = {}
        for ds in DAILY:
            days[ds] = {r[0] for r in db.execute("""
                SELECT DISTINCT o.session FROM observation o JOIN receipt r ON r.id=o.receipt_id
                WHERE o.dataset=? AND r.outcome_only=0 AND o.session IS NOT NULL
            """, (ds,))}
        official = {row[0] for row in db.execute("""
            SELECT session FROM observation
            WHERE dataset='calendar' AND json_extract(values_json,'$.segment')='NSE_CM'
              AND json_extract(values_json,'$.trading')=1
        """)}
        outcomes = db.execute("""
            SELECT COUNT(*) FROM observation o JOIN receipt r ON r.id=o.receipt_id
            WHERE o.session=? AND o.dataset='equity_daily' AND r.outcome_only=1
        """, (str(SESSION),)).fetchone()[0]
        reference = {row[0] for row in db.execute("""
            SELECT DISTINCT o.session FROM observation o JOIN receipt r ON r.id=o.receipt_id
            WHERE o.dataset='equity_daily' AND r.outcome_only=0
              AND o.source='TejHQ Indian Markets parquet'
              AND o.session BETWEEN ? AND ?
        """, (REQUEST_START["equity_daily"], THROUGH))}
    errors = []
    hashes = {}
    for receipt in refs:
        sha = receipt["raw_sha256"]
        raw = root / "raw" / sha[:2] / sha
        hashes.setdefault(sha, (raw, receipt["raw_bytes"]))
        if receipt_counts.get(receipt["id"]) != receipt["records"]:
            errors.append({"receipt": receipt["id"], "error": "receipt row count mismatch"})
    for sha, (raw, size) in hashes.items():
        if not raw.is_file() or raw.stat().st_size != size or sha256_file(raw) != sha:
            errors.append({"raw_sha256": sha, "error": "raw blob or checksum mismatch"})
    for row in metrics:
        row["validated_rows"] = row["normalized_rows"] - row["invalid_ohlc"] - row["invalid_quantity"]
    datasets = {}
    for ds in DATASETS:
        actual = [row for row in metrics if row["dataset"] == ds]
        downloads = [x for x in refs if x["dataset"] == ds]
        blobs = {x["raw_sha256"]: x["raw_bytes"] for x in downloads}
        datasets[ds] = {
            "requested_from": REQUEST_START[ds], "requested_through": THROUGH,
            "source_storage_bytes": sum(blobs.values()), "source_files": len(blobs),
            "normalized": actual, "strict_eligibility": covered[ds],
            "missing_official_sessions": (
                sorted(day for day in official if REQUEST_START[ds] <= day <= THROUGH and day not in days[ds])
                if official and ds in ("equity_daily", "equity_delivery") else None
            ),
            "missing_reference_sessions": (
                sorted(day for day in reference if REQUEST_START[ds] <= day <= THROUGH and day not in days[ds])
                if reference and ds in ("equity_daily", "equity_delivery", "derivatives_daily", "indices")
                else None
            ),
        }
    return {
        "database": str(root / DB_NAME),
        "database_bytes": (root / DB_NAME).stat().st_size,
        "session": str(SESSION), "cutoff_exclusive": cutoff,
        "sqlite_integrity": integrity, "source_hashes_verified": len(hashes) - sum(
            "raw_sha256" in error for error in errors
        ),
        "outcome_only_monday_rows": outcomes, "errors": errors, "datasets": datasets,
        "untestable_checks": {
            "official_calendar_gaps": "No authorized complete segment calendar was supplied" if not official else None,
            "official_listings_and_delistings": "Source-derived symbol intervals do not establish exchange listing or delisting dates",
            "intraday_session_completeness": "No entitled minute, tick or quote history and complete segment calendar",
            "contract_lot_changes_and_coverage": "No sourced historical contract specification and contract universe",
            "independent_provider_parity": "No independently permissioned broad matching index, equity or derivatives history",
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--cutoff", default=CUTOFF)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(args.root, args.cutoff)
    if args.output:
        write_json(args.output, report)
        print(args.output)
    else:
        print(json.dumps(report, indent=2))
    return int(bool(report["errors"]) or report["sqlite_integrity"] != ["ok"])


if __name__ == "__main__":
    raise SystemExit(main())
