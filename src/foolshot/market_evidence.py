"""Read-only, bounded market evidence for Foolshot preparations."""

import argparse
import json
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .clock import IST
from .market_download import write_json
from .market_store import CUTOFF, DATASETS, SESSION, _latest_query, instant, observations, read_db

PRICE_WINDOWS = 20
MARKET_INDEXES = ("NIFTY 50", "NIFTY 500", "NIFTY BANK", "INDIA VIX")


def value(values, field):
    for key, scale in ((field + "_paise", 100), (field + "_rupees", 1), (field, 1)):
        raw = values.get(key)
        if raw is None:
            continue
        try:
            number = Decimal(str(raw)) / scale
        except InvalidOperation:
            return None
        return number if number.is_finite() else None
    return None


def lineage(row):
    return {key: row[key] for key in (
        "dataset", "source", "record_key", "session", "available_at",
        "availability_basis", "url", "raw_sha256", "receipt_id",
    )}


def completed_sessions(root, dataset, cutoff, **filters):
    if dataset not in ("equity_daily", "derivatives_daily", "indices", "macro", "flows"):
        raise ValueError("completed session query expects daily or period data")
    return observations(root, dataset, cutoff, **filters)


def trends(rows, *, symbol, series="EQ", window=PRICE_WINDOWS):
    """Close change and mean close/volume from one eligible source and instrument."""
    if window < 2:
        raise ValueError("trend window must contain at least two sessions")
    series_rows = [r for r in rows if r["symbol"] == symbol
                   and r["values"].get("series") == series and r["session"] is not None]
    if not series_rows:
        return None
    latest = series_rows[0]
    identity = latest["values"].get("isin")
    chosen = [r for r in series_rows if r["source"] == latest["source"]
              and r["values"].get("isin") == identity][:window]
    if len({r["session"] for r in chosen}) != window:
        return None
    closes = [value(r["values"], "close") for r in chosen]
    volumes = [r["values"].get("volume_shares", r["values"].get("volume")) for r in chosen]
    if any(close is None or close <= 0 for close in closes):
        return None
    return {
        "kind": "derived", "method": "unadjusted close change and arithmetic moving averages",
        "symbol": symbol, "series": series, "observations": window,
        "return_pct": str(100 * (closes[0] / closes[-1] - 1)),
        "sma_close_inr": str(sum(closes) / window),
        "mean_volume_shares": (
            str(sum(Decimal(str(volume)) for volume in volumes) / window)
            if all(volume is not None for volume in volumes) else None
        ),
        "inputs": [lineage(row) for row in chosen],
    }


def price_volume_trend(root, cutoff, symbol, *, window=PRICE_WINDOWS):
    rows = completed_sessions(root, "equity_daily", cutoff, symbol=symbol, limit=window * 4)
    return trends(rows, symbol=symbol, window=window)


def relative_strength(root, cutoff, symbol, index, *, sessions=5):
    equity = completed_sessions(root, "equity_daily", cutoff, symbol=symbol, limit=sessions * 4)
    equity = [r for r in equity if r["values"].get("series") == "EQ" and r["session"]]
    indices = completed_sessions(root, "indices", cutoff, symbol=index, limit=sessions * 4)
    if not equity or not indices or sessions < 2:
        return None
    eq_source, eq_isin = equity[0]["source"], equity[0]["values"].get("isin")
    ix_source = indices[0]["source"]
    eq = {r["session"]: r for r in equity if r["source"] == eq_source and r["values"].get("isin") == eq_isin}
    ix = {r["session"]: r for r in indices if r["source"] == ix_source and r["session"]}
    if len(eq) != sum(r["source"] == eq_source and r["values"].get("isin") == eq_isin for r in equity):
        return None
    if len(ix) != sum(r["source"] == ix_source and bool(r["session"]) for r in indices):
        return None
    dates = sorted(eq.keys() & ix.keys(), reverse=True)[:sessions]
    if len(dates) != sessions:
        return None
    pairs = [(eq[day], ix[day]) for day in dates]
    levels = [value(row["values"], "close") for pair in (pairs[0], pairs[-1]) for row in pair]
    if any(level is None or level <= 0 for level in levels):
        return None
    latest_stock, latest_index, first_stock, first_index = levels
    return {
        "kind": "derived", "method": "unadjusted stock minus index return over common sessions",
        "symbol": symbol, "index": index, "sessions": sessions,
        "percentage_points": str(100 * (latest_stock / first_stock - latest_index / first_index)),
        "inputs": [lineage(row) for pair in pairs for row in pair],
    }


def equity_breadth(root, cutoff, session):
    cte, bind = _latest_query("equity_daily", cutoff, through=session)
    with read_db(root) as db:
        result = db.execute(cte + """
            SELECT source, receipt_id, url, raw_sha256, MAX(available_at) AS available_at,
                   SUM(close > prev) AS advances, SUM(close < prev) AS declines,
                   SUM(close = prev) AS unchanged
            FROM (
                SELECT *,
                       COALESCE(json_extract(values_json,'$.close_rupees'),
                                json_extract(values_json,'$.close_paise') / 100.0) AS close,
                       COALESCE(json_extract(values_json,'$.previous_close_rupees'),
                                json_extract(values_json,'$.previous_close_paise') / 100.0,
                                json_extract(values_json,'$.prev_close_paise') / 100.0) AS prev
                FROM latest WHERE session=? AND json_extract(values_json,'$.series')='EQ'
            ) WHERE close > 0 AND prev > 0
            GROUP BY source,receipt_id,url,raw_sha256 ORDER BY source,receipt_id LIMIT 20
        """, (*bind, date.fromisoformat(str(session)).isoformat()))
        return [dict(row) | {"kind": "derived", "session": str(session),
                            "universe_scope": "eligible EQ rows in the listed source receipt"}
                for row in result]


def observed_universe(root, cutoff, *, limit=100):
    """First and last eligible *observations* by instrument, separate from listings."""
    if not 1 <= limit <= 2_000:
        raise ValueError("invalid universe limit")
    cte, bind = _latest_query("equity_daily", cutoff)
    with read_db(root) as db:
        return [dict(row) for row in db.execute(cte + """
            SELECT source,symbol,json_extract(values_json,'$.isin') AS isin,
                   json_extract(values_json,'$.series') AS series,
                   MIN(session) AS first_observed,MAX(session) AS last_observed,
                   COUNT(DISTINCT session) AS sessions
            FROM latest GROUP BY source,symbol,isin,series
            ORDER BY source,symbol,isin,series LIMIT ?
        """, (*bind, limit))]


def listed_universe(root, cutoff, session, *, limit=100):
    """Read effective intervals already known when the packet was cut."""
    if not 1 <= limit <= 2_000:
        raise ValueError("invalid universe limit")
    day = date.fromisoformat(str(session)).isoformat()
    if day > datetime.fromisoformat(instant(cutoff)).astimezone(IST).date().isoformat():
        raise ValueError("membership day exceeds cutoff date")
    cte, bind = _latest_query("listings", cutoff)
    with read_db(root) as db:
        return [dict(row) for row in db.execute(cte + """
            SELECT source,symbol,json_extract(values_json,'$.isin') AS isin,
                   json_extract(values_json,'$.valid_from') AS valid_from,
                   json_extract(values_json,'$.valid_to') AS valid_to,
                   available_at,url,raw_sha256,receipt_id
            FROM latest WHERE valid_from <= ? AND (valid_to IS NULL OR valid_to >= ?)
            ORDER BY source,symbol,isin LIMIT ?
        """, (*bind, day, day, limit))]


def end_of_day_chain(root, cutoff, symbol, session, *, limit=100):
    cte, bind = _latest_query("derivatives_daily", cutoff, through=session, symbol=symbol)
    if not 1 <= limit <= 2_000:
        raise ValueError("invalid chain limit")
    with read_db(root) as db:
        rows = db.execute(cte + """
            SELECT dataset,source,record_key,session,symbol,available_at,availability_basis,
                   url,raw_sha256,receipt_id,values_json
            FROM latest WHERE session=?
              AND UPPER(json_extract(values_json,'$.option_type')) IN ('CE','PE','C','P','CALL','PUT')
            ORDER BY source,json_extract(values_json,'$.expiry'),
                CAST(json_extract(values_json,'$.strike') AS REAL),record_key LIMIT ?
        """, (*bind, date.fromisoformat(str(session)).isoformat(), limit))
        result = []
        for row in rows:
            record = dict(row)
            record["values"] = json.loads(record.pop("values_json"))
            result.append(record)
        return {"kind": "end_of_day_contract_rows", "session": str(session),
                "symbol": symbol, "rows": result}


def research_observations(root, dataset, *, through=None, symbol=None, source=None, limit=100):
    """Read the latest stored source rows regardless of availability classification.

    This is a dataset-inspection helper, not evidence. Rows returned here are
    explicitly marked ``not_point_in_time`` and must never be passed to a replay
    packet or treated as information available at a historical cutoff.
    """
    if dataset not in DATASETS:
        raise ValueError("unknown dataset")
    if not 1 <= limit <= 2_000:
        raise ValueError("research limit must be between 1 and 2000")
    where = ["o.dataset=?", "r.outcome_only=0"]
    bind = [dataset]
    if symbol is not None:
        where.append("o.symbol=?")
        bind.append(symbol)
    if source is not None:
        where.append("o.source=?")
        bind.append(source)
    if through is not None:
        where.append("o.session<=?")
        bind.append(date.fromisoformat(str(through)).isoformat())
    with read_db(root) as db:
        rows = db.execute("""
            WITH ranked AS (
                SELECT o.*, r.url, r.raw_sha256, r.acquired_at,
                       ROW_NUMBER() OVER (
                           PARTITION BY o.source,o.record_key
                           ORDER BY o.available_at DESC, o.receipt_id
                       ) AS version
                FROM observation o JOIN receipt r ON r.id=o.receipt_id
                WHERE """ + " AND ".join(where) + """
            )
            SELECT dataset,source,record_key,session,symbol,event_at,available_at,
                   availability,availability_basis,values_json,url,raw_sha256,
                   acquired_at,receipt_id
            FROM ranked WHERE version=1
            ORDER BY COALESCE(session,'') DESC, COALESCE(event_at,'') DESC,
                     source, record_key LIMIT ?
        """, (*bind, limit))
        result = []
        for row in rows:
            record = dict(row)
            record["values"] = json.loads(record.pop("values_json"))
            record["eligibility"] = "not_point_in_time"
            result.append(record)
        return result


def research_chain(root, symbol, session, *, expiry=None, limit=500):
    """All stored option contracts for one underlying and session, newest source first."""
    if not 1 <= limit <= 2_000:
        raise ValueError("chain limit must be between 1 and 2000")
    day = date.fromisoformat(str(session)).isoformat()
    where = ["o.dataset='derivatives_daily'", "o.symbol=?", "o.session=?",
             "UPPER(json_extract(o.values_json,'$.option_type')) IN ('CE','PE','C','P','CALL','PUT')",
             "r.outcome_only=0"]
    bind = [symbol, day]
    if expiry is not None:
        where.append("json_extract(o.values_json,'$.expiry')=?")
        bind.append(date.fromisoformat(str(expiry)).isoformat())
    with read_db(root) as db:
        rows = db.execute("""
            SELECT o.source,o.record_key,o.session,o.symbol,o.values_json,o.availability,
                   o.availability_basis,r.url,r.raw_sha256,r.acquired_at
            FROM observation o JOIN receipt r ON r.id=o.receipt_id
            WHERE """ + " AND ".join(where) + """
            ORDER BY json_extract(o.values_json,'$.expiry'),
                     CAST(json_extract(o.values_json,'$.strike') AS REAL),
                     json_extract(o.values_json,'$.option_type'), o.record_key LIMIT ?
        """, (*bind, limit))
        result = []
        for row in rows:
            record = dict(row)
            record["values"] = json.loads(record.pop("values_json"))
            record["eligibility"] = "not_point_in_time"
            result.append(record)
        return {"kind": "research_option_chain", "session": day, "symbol": symbol,
                "expiry": expiry, "rows": result}


def packet(root, cutoff=CUTOFF, *, symbol="RELIANCE"):
    moment = datetime.fromisoformat(instant(cutoff)).astimezone(IST)
    if moment > datetime.fromisoformat(CUTOFF):
        raise ValueError("packet cutoff exceeds the registered pre-session boundary")
    channels = {
        "equity_daily": observations(root, "equity_daily", cutoff, symbol=symbol, limit=20),
        "indices": observations(root, "indices", cutoff, limit=40),
        "macro": observations(root, "macro", cutoff, limit=24),
        "flows": observations(root, "flows", cutoff, limit=10),
        "derivatives_daily": [
            row for name in ("NIFTY", "BANKNIFTY")
            for row in observations(root, "derivatives_daily", cutoff, symbol=name, limit=12)
        ],
        "economic_events": observations(root, "economic_events", cutoff, limit=12),
        "filings": observations(root, "filings", cutoff, symbol=symbol, limit=12),
        "news": observations(root, "news", cutoff, limit=12),
    }
    days = [r["session"] for name in ("equity_daily", "indices")
            for r in channels[name] if r["session"]]
    latest_day = max(days, default=None)
    derived = {
        "breadth": equity_breadth(root, cutoff, latest_day) if latest_day else [],
        "price_volume": price_volume_trend(root, cutoff, symbol),
        "relative_strength": relative_strength(root, cutoff, symbol, MARKET_INDEXES[0]),
    }
    stamps = [r["available_at"] for records in channels.values() for r in records]
    stamps.extend(row["available_at"] for row in derived["breadth"])
    for name in ("price_volume", "relative_strength"):
        if derived[name]:
            stamps.extend(row["available_at"] for row in derived[name]["inputs"])
    with read_db(root) as db:
        outcome_count = db.execute("""
            SELECT COUNT(*) FROM observation o JOIN receipt r ON r.id=o.receipt_id
            WHERE r.outcome_only=1 AND o.dataset='equity_daily' AND o.session=?
        """, (str(SESSION),)).fetchone()[0]
    return {
        "schema": "foolshot.pre_session_evidence.v1", "session": str(SESSION),
        "cutoff_exclusive": moment.isoformat(), "symbol": symbol,
        "max_available_at_utc": max(stamps, default=None), "channels": channels,
        "derived": derived,
        "gaps": [key for key, items in (channels | derived).items() if not items],
        "outcome_only_rows_excluded": outcome_count,
    }


def harness_preparation(evidence):
    """Translate bounded records to the existing historical harness preparation schema."""
    rows = []
    for records in evidence["channels"].values():
        for row in records:
            rows.append({
                "available_at": row["available_at"], "source": row["url"],
                "text": json.dumps({
                    "dataset": row["dataset"], "session": row["session"],
                    "symbol": row["symbol"], "key": row["record_key"],
                    "source_sha256": row["raw_sha256"], "values": row["values"],
                }, ensure_ascii=False, sort_keys=True),
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--cutoff", default=CUTOFF)
    parser.add_argument("--symbol", default="RELIANCE")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    show = subparsers.add_parser("query")
    show.add_argument("dataset", choices=DATASETS)
    show.add_argument("--source")
    show.add_argument("--limit", type=int, default=20)
    show.add_argument("--all-availability", action="store_true",
                      help="research inspection only; rows are not point-in-time eligible")
    chain = subparsers.add_parser("chain")
    chain.add_argument("--session", required=True)
    chain.add_argument("--expiry")
    chain.add_argument("--limit", type=int, default=200)
    export = subparsers.add_parser("packet")
    export.add_argument("--output", type=Path)
    export.add_argument("--preparation", type=Path)
    args = parser.parse_args()
    if args.operation == "query":
        if args.all_availability:
            result = research_observations(
                args.root, args.dataset, source=args.source,
                symbol=args.symbol or None, limit=args.limit,
            )
        else:
            result = observations(args.root, args.dataset, args.cutoff, source=args.source,
                                  symbol=args.symbol or None, limit=args.limit)
    elif args.operation == "chain":
        result = research_chain(args.root, args.symbol, args.session,
                                expiry=args.expiry, limit=args.limit)
    else:
        result = packet(args.root, args.cutoff, symbol=args.symbol)
        if args.preparation:
            write_json(args.preparation, harness_preparation(result))
        if args.output:
            write_json(args.output, result)
            print(str(args.output))
            return
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
