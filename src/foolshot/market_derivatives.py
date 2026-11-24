"""Rights-aware import and coverage notes for private derivative market history.

This module deliberately performs no network access, subscription purchase, or
broker operation. It accepts owner-provided source exports and preserves raw
bytes through ``market_store``. Rows without an explicit publication/availability
timestamp remain unavailable to point-in-time queries.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from .clock import IST

START_DAILY = date(2023, 11, 23)
START_INTRADAY = date(2025, 11, 23)
END = date(2026, 11, 22)
CUTOFF = datetime.fromisoformat("2026-11-23T00:00:00+05:30")
DATASETS = {"derivatives_daily", "intraday_bars", "quotes", "trades", "option_chain_snapshots", "contract_specs"}


def _timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    stamp = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("timestamps must include a UTC offset")
    return stamp


def _number(value: str | None):
    if value is None or value.strip() == "":
        return None
    return float(value)


def _csv_bytes(path: Path, raw: bytes) -> bytes:
    # Content-addressed raw blobs keep no filename suffix, so detect the
    # container from its magic bytes as well as the supplied path.
    if raw[:2] == b"\x1f\x8b" or path.suffix.lower() == ".gz":
        return gzip.decompress(raw)
    if raw[:2] == b"PK" or path.suffix.lower() == ".zip":
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = [n for n in archive.namelist() if not n.endswith("/") and n.lower().endswith(".csv")]
            if len(names) != 1:
                raise ValueError("ZIP export must contain exactly one CSV")
            return archive.read(names[0])
    return raw


def _session(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    for pattern in ("%Y-%m-%d", "%Y%m%d", "%d-%b-%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            pass
    return _timestamp(value).astimezone(IST).date()  # type: ignore[union-attr]


def parse_csv(path: Path, dataset: str, *, default_symbol: str | None = None) -> list[dict]:
    """Parse a provider export using explicit event and instrument columns.

    Recognized aliases cover common broker exports. Quotes are kept as quote
    records; no quotes, trades, or bars are synthesized from OHLC data.
    """
    if dataset not in DATASETS:
        raise ValueError(f"unsupported dataset: {dataset}")
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(_csv_bytes(path, raw).decode("utf-8-sig")))
    if not reader.fieldnames:
        raise ValueError("CSV has no header")
    field_aliases = {
        "traddt": "trad_dt", "bizdt": "biz_dt", "tckrsymb": "tckr_symb",
        "xprydt": "xpry_dt", "strkpric": "strk_pric", "optntp": "optn_tp",
        "opnpric": "opn_pric", "hghpric": "hgh_pric", "lwpric": "lw_pric",
        "clspric": "cls_pric", "sttlmpric": "sttlm_pric", "ttltradgvol": "ttl_tradg_vol",
        "lastpric": "last_pric", "prvsclsgpric": "prvs_clsg_pric",
        "undrlygpric": "undrlyg_pric", "ttltrfval": "ttl_trf_val",
        "ttlnboftxsexctd": "ttl_nb_of_txs_exctd", "fininstrmtp": "fin_instrm_tp",
        "fininstrmnm": "fin_instrm_nm", "sctysrs": "scty_srs", "isin": "isin",
        "opnintrst": "opn_intrst", "chnginopnintrst": "chng_in_opn_intrst",
        "fininstrmid": "fin_instrm_id", "newbrdlotqty": "lot_size",
        "undrlyg": "underlying",
        "open_int": "open_interest", "openint": "open_interest",
        "chg_in_oi": "oi_change", "chgin_oi": "oi_change", "contracts": "volume",
        "val_inlakh": "turnover_lakh", "tradeid": "trade_id", "quoteid": "quote_id",
        "sequencenumber": "sequence_number",
    }
    aliases = {}
    for field in reader.fieldnames:
        normalized = field.strip().lower().replace(" ", "_")
        aliases[field_aliases.get(normalized, normalized)] = field

    def get(row, *names):
        for name in names:
            col = aliases.get(name)
            if col is not None and row.get(col, "").strip():
                return row[col].strip()
        return None

    rows = []
    for line, row in enumerate(reader, 2):
        symbol = get(row, "symbol", "tradingsymbol", "instrument", "contract", "tckr_symb", "underlying", "undrlyg") or default_symbol
        event_value = get(row, "event_at", "timestamp", "datetime", "date_time", "time")
        event = _timestamp(event_value) if event_value else None
        session_date = _session(get(row, "session", "trad_dt", "biz_dt", "date"))
        if not symbol or (event is None and session_date is None):
            raise ValueError(f"row {line}: requires a symbol and event timestamp or session date")
        session_date = event.astimezone(IST).date() if event else session_date
        session = session_date.isoformat() if session_date else None
        availability_at = _timestamp(get(row, "available_at", "published_at", "publication_time"))
        values = {}
        for canonical, choices in {
            "open": ("open", "o", "opn_pric"), "high": ("high", "h", "hgh_pric"), "low": ("low", "l", "lw_pric"),
            "close": ("close", "c", "ltp", "cls_pric"), "volume": ("volume", "vol", "ttl_tradg_vol"),
            "open_interest": ("open_interest", "opn_intrst", "oi"), "bid": ("bid", "best_bid"),
            "ask": ("ask", "best_ask"), "bid_qty": ("bid_qty", "bid_quantity"),
            "ask_qty": ("ask_qty", "ask_quantity"), "trade_price": ("trade_price", "price"),
            "trade_qty": ("trade_qty", "quantity", "qty"), "expiry": ("expiry", "expiry_date", "xpry_dt"),
            "strike": ("strike", "strike_price", "strk_pric"), "option_type": ("option_type", "right", "optn_tp"),
            "contract_id": ("contract_id", "fin_instrm_id"), "underlying": ("underlying", "undrlyg"),
            "lot_size": ("lot_size",), "currency": ("currency",), "settlement": ("settlement", "sttlm_pric"),
            "oi_change": ("oi_change", "chng_in_opn_intrst"),
            "turnover_lakh": ("turnover_lakh",), "interval": ("interval", "timeframe", "bar_interval"),
            "last_price": ("last_price", "last_pric"), "previous_close": ("previous_close", "prvs_clsg_pric"),
            "underlying_price": ("underlying_price", "undrlyg_pric"),
            "turnover_rupees": ("turnover_rupees", "ttl_trf_val"),
            "trades": ("trades", "ttl_nb_of_txs_exctd"),
            "instrument_type": ("instrument_type", "fin_instrm_tp"),
            "contract_name": ("contract_name", "fin_instrm_nm"),
            "isin": ("isin",),
        }.items():
            value = get(row, *choices)
            if value is not None:
                values[canonical] = value if canonical in {
                    "expiry", "option_type", "contract_id", "underlying", "currency",
                    "interval", "instrument_type", "contract_name", "isin",
                } else _number(value)
        if dataset == "quotes" and not ("bid" in values and "ask" in values):
            raise ValueError(f"row {line}: quote requires bid and ask")
        if dataset == "quotes":
            if event is None:
                raise ValueError(f"row {line}: quote requires an offset-aware event timestamp")
            if not all(key in values for key in ("bid_qty", "ask_qty")):
                raise ValueError(f"row {line}: quote requires bid and ask sizes")
            if values["bid"] > values["ask"] or values["bid_qty"] < 0 or values["ask_qty"] < 0:
                raise ValueError(f"row {line}: invalid quote spread or size")
        if dataset == "trades" and "trade_price" not in values:
            raise ValueError(f"row {line}: trade requires trade price")
        if dataset == "trades" and event is None:
            raise ValueError(f"row {line}: trade requires an offset-aware event timestamp")
        if dataset in {"derivatives_daily", "intraday_bars"} and not all(k in values for k in ("open", "high", "low", "close")):
            raise ValueError(f"row {line}: candle requires OHLC")
        event_text = event.isoformat() if event else None
        source_id = get(row, "id", "trade_id", "quote_id", "sequence", "sequence_number")
        contract_id = get(row, "contract_id", "fin_instrm_id")
        underlying = get(row, "underlying") or symbol
        expiry = get(row, "expiry", "expiry_date", "xpry_dt")
        strike = get(row, "strike", "strike_price", "strk_pric")
        right = get(row, "option_type", "right", "optn_tp")
        if dataset in {"derivatives_daily", "contract_specs"}:
            if contract_id:
                key = f"{contract_id}|{session}"
            elif underlying and session and expiry and strike and right:
                key = f"{underlying}|{expiry}|{strike}|{right}|{session}"
            else:
                raise ValueError(f"row {line}: insufficient contract fields for a stable daily key")
        elif dataset == "intraday_bars":
            if event_text is None:
                raise ValueError(f"row {line}: minute bar requires an offset-aware event timestamp")
            key = f"{contract_id or symbol}|{event_text}|{values.get('interval', '')}"
        elif dataset in {"quotes", "trades"}:
            if not source_id:
                raise ValueError(f"row {line}: {dataset} requires a provider id or sequence")
            key = f"{symbol}|{event_text}|{source_id}"
        elif dataset == "option_chain_snapshots":
            if event_text is None or not (contract_id or (expiry and strike is not None and right)):
                raise ValueError(f"row {line}: option snapshot requires timestamp and contract identity")
            key = f"{symbol}|{event_text}|{contract_id or f'{expiry}|{strike}|{right}'}"
        else:
            raise ValueError(f"row {line}: no stable key rule for dataset {dataset}")
        if key in {existing["key"] for existing in rows}:
            raise ValueError(f"row {line}: duplicate or ambiguous {dataset} natural key")
        rows.append({"key": key, "session": session, "symbol": symbol,
                     "event_at": event_text,
                     "available_at": availability_at.isoformat() if availability_at else None,
                     "availability": "verified" if availability_at else "unknown",
                     "availability_basis": "explicit source publication timestamp" if availability_at else "source export lacks publication/availability timestamp",
                     "values": values})
    return rows


def ingest_export(root: Path, path: Path, *, dataset: str, source: str,
                  url: str, acquired_at: str | None = None,
                  default_symbol: str | None = None, notes: str = "") -> dict:
    """Ingest a documented, locally supplied CSV export without altering it."""
    from .market_store import ingest_batch

    parsed = parse_csv(path, dataset, default_symbol=default_symbol)
    return ingest_batch(root, dataset=dataset, source=source, url=url,
                        raw_path=path, rows=parsed, acquired_at=acquired_at,
                        notes=notes)


def source_report(root: Path | None = None) -> dict:
    """Current source access assessment and measured local counts."""
    env = os.environ
    counts = {dataset: 0 for dataset in sorted(DATASETS)}
    sessions = {dataset: 0 for dataset in sorted(DATASETS)}
    files = {dataset: 0 for dataset in sorted(DATASETS)}
    window = {}
    if root is not None:
        from .market_store import read_db

        with read_db(root) as db:
            for dataset, rows, days, first, last in db.execute("""
                SELECT dataset, COUNT(*), COUNT(DISTINCT session), MIN(session), MAX(session)
                FROM observation GROUP BY dataset
            """):
                if dataset in counts:
                    counts[dataset] = rows
                    sessions[dataset] = days
                    window[dataset] = [first, last]
            for dataset, total in db.execute("SELECT dataset, COUNT(*) FROM receipt GROUP BY dataset"):
                if dataset in files:
                    files[dataset] = total
    return {
        "cutoff": CUTOFF.isoformat(), "coverage_window": {
            "derivatives_daily": [START_DAILY.isoformat(), END.isoformat()],
            "intraday_bars": [START_INTRADAY.isoformat(), END.isoformat()],
        },
        "as_of": datetime.now(IST).isoformat(),
        "sources": [
            {"name": "DhanHQ Data API", "status": "blocked_credentials_unavailable_subscription_unverified",
             "docs_url": "https://dhanhq.co/docs/v2/historical-data/",
             "plan_url": "https://dhan.co/support/platforms/dhanhq-api/what-are-the-available-api-subscription-plans-and-how-can-i-subscribe-to-them/",
             "expired_futures_note_url": "https://blog.dhan.co/support/platforms/dhanhq-api/how-can-i-retrieve-data-for-expired-futures-contracts-using-the-apis/",
             "credentials_present": bool(env.get("DHAN_ACCESS_TOKEN") and env.get("DHAN_CLIENT_ID")),
             "error": "DHAN_ACCESS_TOKEN and/or DHAN_CLIENT_ID unavailable in current process environment",
             "rights": "Official Data API subscription required; no purchase/signup performed.",
             "supported": "Daily candles; intraday 1/5/15/25/60 minute candles; option-chain/expired-option data per official documentation.",
             "limitation": "Dhan support says expired futures intraday history is not supported; daily data is continuous via current expiry security ID, so it does not replace contract-wise daily archives."},
            {"name": "TrueData", "status": "blocked", "error": "HTTP 401 (previous attempt, reported by task owner)",
             "rights": "No access workaround attempted."},
            {"name": "NSE public F&O archives", "status": "daily_archives_imported",
             "url": "https://www.nseindia.com/all-reports-derivatives",
             "collector": "foolshot.market_nse_archive",
             "rights": "The reviewed daily UDiFF bhavcopy objects were fetched at a polite rate for a private, non-redistributed research store. NSE website terms restrict systematic collection and redistribution; exchange terms remain applicable.",
             "imported": f"{counts['derivatives_daily']} contract rows over {sessions['derivatives_daily']} sessions from {files['derivatives_daily']} daily files.",
             "limitation": "Daily archive files do not carry a per-file publication timestamp, so rows stay availability=unknown and are excluded from strict point-in-time evidence. Minute bars, genuine historical quotes and historical option-chain snapshots are not part of the free daily archive."},
            {"name": "NSE licensed historical market data", "status": "not_subscribed",
             "url": "https://www.nseindia.com/static/market-data/eod-historical-data-subscription",
             "rights": "NSE identifies paid EOD/historical subscription products including F&O historical order/trade data; no subscription or access attempt made."},
        ],
        "local_exports": {"status": "nse_daily_archives_imported" if counts["derivatives_daily"] else "none_found",
                           "files": files["derivatives_daily"],
                           "checked": str(root) if root is not None else None},
        "observed_counts": counts,
        "observed_sessions": sessions,
        "observed_window": window,
        "remaining_gaps": [
            "One-year minute candles, including expired contracts.",
            "Historical genuine bid/ask quotes and intraday option-chain snapshots.",
            "Historical contract specification and lot-change masters.",
            "Verified per-file publication/availability timestamps for point-in-time replay.",
        ],
        "notes": "No synthetic bars, quote reconstruction, or inferred option-chain snapshots accepted.",
    }


def write_source_report(root: Path) -> Path:
    report = root / "reports" / "derivatives-sources.json"
    report.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(report.parent, 0o700)
    report.write_text(json.dumps(source_report(root), indent=2, sort_keys=True) + "\n")
    os.chmod(report, 0o600)
    return report


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/private/market-data"))
    parser.add_argument("--import-csv", type=Path, help="owner-provided source export")
    parser.add_argument("--dataset", choices=sorted(DATASETS))
    parser.add_argument("--source")
    parser.add_argument("--url", default="local-export")
    parser.add_argument("--symbol")
    args = parser.parse_args(argv)
    os.umask(0o077)
    if args.import_csv:
        if not (args.dataset and args.source):
            parser.error("--import-csv requires --dataset and --source")
        result = ingest_export(args.root, args.import_csv, dataset=args.dataset,
                               source=args.source, url=args.url, default_symbol=args.symbol)
        print(json.dumps(result, sort_keys=True))
    report = write_source_report(args.root)
    print(json.dumps({"source_report": str(report)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
