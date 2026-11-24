"""Normalize locally held NSE cash-market daily archives.

This module deliberately has no downloader. NSE's Terms of Use prohibit
systematic or automated collection, so archives must be obtained through a
permitted process and supplied as local files with their source URL recorded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

from .market_store import ingest_batch

DEFAULT_ROOT = Path("/Users/vishmac/Documents/GitHub/Foolshot/data/private/market-data")
TEJHQ_SOURCE = "TejHQ Indian Markets parquet"
TEJHQ_BASE = "https://huggingface.co/datasets/tejhq/indian-markets/resolve/main/"
WINDOW_FROM = "2023-11-23"
WINDOW_THROUGH = "2026-11-22"


def _date(value) -> str | None:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)[:10]


def _parquet_rows(path: Path, columns: str, predicates: str):
    """Stream parquet rows without loading a whole yearly partition into memory."""
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError("install the project DuckDB dependency to ingest parquet") from exc
    connection = duckdb.connect()
    connection.execute(f"SELECT {columns} FROM read_parquet(?) WHERE {predicates}", [str(path)])
    names = [column[0] for column in connection.description]
    try:
        while batch := connection.fetchmany(20_000):
            for values in batch:
                yield dict(zip(names, values))
    finally:
        connection.close()


def _receipt_row(key: str, session: str | None, symbol: str | None,
                 values: dict, *, basis: str) -> dict:
    return {
        "key": key, "session": session, "symbol": symbol,
        "event_at": None, "available_at": None,
        "availability": "unknown", "availability_basis": basis,
        "values": values,
    }


def _ingest_tejhq_file(root: Path, local: Path, remote: str, dataset: str,
                       rows, *, notes: str) -> dict:
    return ingest_batch(
        root, dataset=dataset, source=TEJHQ_SOURCE, url=TEJHQ_BASE + remote,
        raw_path=local, rows=rows,
        notes=("Derived third-party parquet; its data terms allow private personal/research use and local storage, prohibit raw publication, disclaim any exchange license, and leave exchange terms applicable. " + notes),
    )


def ingest_tejhq_history(root: Path, source_root: Path) -> dict:
    """Ingest the documented TejHQ NSE yearly parquet slice, excluding Monday."""
    results = {}
    for year in range(2023, 2027):
        start = max(WINDOW_FROM, f"{year}-01-01")
        end = min(WINDOW_THROUGH, f"{year}-12-31")
        if start > end:
            continue

        price_rel = f"nse/year={year}/nse_{year}.parquet"
        price_path = source_root / price_rel
        prices = (
            _receipt_row(
                f"{_date(row['date'])}|{row['isin'] or row['symbol']}|{row['series']}",
                _date(row["date"]), row["symbol"], {
                    "isin": row["isin"], "series": row["series"], "instrument_name": row["name"],
                    "open_rupees": row["open"], "high_rupees": row["high"],
                    "low_rupees": row["low"], "close_rupees": row["close"],
                    "last_rupees": row["last"], "previous_close_rupees": row["prev_close"],
                    "volume_shares": row["volume"], "turnover_rupees": row["turnover"],
                    "trade_count": row["trades"],
                }, basis="unknown; TejHQ parquet snapshot has no per-record first-publication time",
            )
            for row in _parquet_rows(
                price_path, "date,symbol,series,isin,name,open,high,low,close,last,prev_close,volume,turnover,trades",
                f"date >= DATE '{start}' AND date <= DATE '{end}'",
            )
        )
        results[f"equity_daily:{year}"] = _ingest_tejhq_file(
            root, price_path, price_rel, "equity_daily", prices,
            notes=f"Session dates filtered to {start} through {end}; source numeric price/turnover units retained as rupees.",
        )

        delivery_rel = f"delivery/nse/year={year}/nse_{year}.parquet"
        delivery_path = source_root / delivery_rel
        delivery = (
            _receipt_row(
                f"{_date(row['date'])}|{row['symbol']}|{row['series']}",
                _date(row["date"]), row["symbol"], {
                    "series": row["series"], "volume_shares": row["volume"],
                    "delivery_shares": row["delivery_qty"], "delivery_pct": row["delivery_pct"],
                }, basis="unknown; TejHQ parquet snapshot has no per-record first-publication time",
            )
            for row in _parquet_rows(
                delivery_path, "date,symbol,series,volume,delivery_qty,delivery_pct",
                f"date >= DATE '{start}' AND date <= DATE '{end}'",
            )
        )
        results[f"equity_delivery:{year}"] = _ingest_tejhq_file(
            root, delivery_path, delivery_rel, "equity_delivery", delivery,
            notes=f"Session dates filtered to {start} through {end}; source units retained (shares and percent).",
        )

        action_rel = f"actions/nse_{year}.parquet"
        action_path = source_root / action_rel
        action = (
            _receipt_row(
                hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest(),
                _date(row["ex_date"]), row["symbol"], {
                    "exchange": row["exchange"], "isin": row["isin"], "company": row["company"],
                    "record_date": _date(row["record_date"]), "action_type": row["type"],
                    "ratio_numerator": row["ratio_num"], "ratio_denominator": row["ratio_den"],
                    "cash_amount_source_units": row["cash_amount"],
                    "face_value_from": row["face_value_from"], "face_value_to": row["face_value_to"],
                    "raw_subject": row["raw_subject"],
                }, basis="unknown; TejHQ parquet snapshot has no announcement/publication timestamp",
            )
            for row in _parquet_rows(
                action_path, "exchange,symbol,isin,company,ex_date,record_date,type,ratio_num,ratio_den,cash_amount,face_value_from,face_value_to,raw_subject",
                f"ex_date >= DATE '{start}' AND ex_date <= DATE '{end}'",
            )
        )
        results[f"corporate_actions:{year}"] = _ingest_tejhq_file(
            root, action_path, action_rel, "corporate_actions", action,
            notes=f"Ex-dates filtered to {start} through {end}; announcement availability remains unknown.",
        )

    listing_rel = "symbol_history/nse.parquet"
    listing_path = source_root / listing_rel
    listings = (
        _receipt_row(
            f"{row['isin']}|{row['symbol']}|{_date(row['valid_from'])}",
            None, row["symbol"], {
                "exchange": row["exchange"], "isin": row["isin"],
                "valid_from": _date(row["valid_from"]), "valid_to": _date(row["valid_to"]),
                "trading_days": row["trading_days"],
            }, basis="unknown; current symbol-history snapshot has no per-record first-publication time",
        )
        for row in _parquet_rows(
            listing_path, "exchange,isin,symbol,valid_from,valid_to,trading_days",
            f"valid_from <= DATE '{WINDOW_THROUGH}' AND (valid_to IS NULL OR valid_to >= DATE '{WINDOW_FROM}')",
        )
    )
    results["listings"] = _ingest_tejhq_file(
        root, listing_path, listing_rel, "listings", listings,
        notes=f"NSE symbol-history intervals overlapping {WINDOW_FROM} through {WINDOW_THROUGH}; retains source validity dates.",
    )
    return results


def _paise(value: str, field: str, row_number: int) -> int | None:
    if not value:
        return None
    try:
        amount = Decimal(value)
    except Exception as exc:
        raise ValueError(f"row {row_number}: invalid {field}: {value!r}") from exc
    paise = amount * 100
    if paise != paise.to_integral_value():
        raise ValueError(f"row {row_number}: {field} has fractions of a paise")
    return int(paise)


def read_bhavcopy(path: Path) -> tuple[list[dict], dict]:
    """Read a supplied CM bhavcopy ZIP into one row per cash-market instrument."""
    raw = path.read_bytes()
    raw_sha256 = hashlib.sha256(raw).hexdigest()
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = [name for name in archive.namelist() if not name.endswith("/")]
            if len(members) != 1 or not members[0].lower().endswith(".csv"):
                raise ValueError("expected one CSV member in the supplied ZIP")
            member = members[0]
            payload = archive.read(member)
    except zipfile.BadZipFile as exc:
        raise ValueError("input is not a valid ZIP archive") from exc

    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    required = {"TradDt", "Sgmt", "ISIN", "TckrSymb", "SctySrs", "FinInstrmNm",
                "OpnPric", "HghPric", "LwPric", "ClsPric", "LastPric",
                "PrvsClsgPric", "TtlTradgVol", "TtlTrfVal", "TtlNbOfTxsExctd"}
    missing = required.difference(reader.fieldnames or [])
    if missing:
        raise ValueError("missing bhavcopy fields: " + ",".join(sorted(missing)))

    result = []
    dates: set[str] = set()
    for line, source_row in enumerate(reader, start=2):
        session = date.fromisoformat(source_row["TradDt"]).isoformat()
        dates.add(session)
        symbol = source_row["TckrSymb"] or None
        isin = source_row["ISIN"] or None
        series = source_row["SctySrs"] or None
        # The CM file includes non-equity instruments too. Preserve cash
        # securities, but leave index and other non-stock rows out of equity_daily.
        if source_row.get("FinInstrmTp") not in {"STK"} or not symbol:
            continue
        natural = isin or symbol
        key = f"{session}|{natural}|{series or ''}"
        result.append({
            "key": key,
            "session": session,
            "symbol": symbol,
            "event_at": None,
            "available_at": None,
            "availability": "unknown",
            "availability_basis": "official end-of-day file; exact public availability time not recorded",
            "values": {
                "isin": isin,
                "series": series,
                "instrument_name": source_row["FinInstrmNm"] or None,
                "open_paise": _paise(source_row["OpnPric"], "OpnPric", line),
                "high_paise": _paise(source_row["HghPric"], "HghPric", line),
                "low_paise": _paise(source_row["LwPric"], "LwPric", line),
                "close_paise": _paise(source_row["ClsPric"], "ClsPric", line),
                "last_paise": _paise(source_row["LastPric"], "LastPric", line),
                "previous_close_paise": _paise(source_row["PrvsClsgPric"], "PrvsClsgPric", line),
                "volume_shares": int(source_row["TtlTradgVol"] or 0),
                "turnover_rupees": source_row["TtlTrfVal"] or None,
                "trade_count": int(source_row["TtlNbOfTxsExctd"] or 0),
                "source_instrument_type": source_row["FinInstrmTp"],
                "source_instrument_id": source_row.get("FinInstrmId") or None,
            },
        })
    if len(dates) != 1:
        raise ValueError(f"expected one trading date in archive; found {len(dates)}")
    return result, {
        "zip_sha256": raw_sha256,
        "member": member,
        "member_sha256": hashlib.sha256(payload).hexdigest(),
        "member_bytes": len(payload),
        "session": next(iter(dates)),
    }


def ingest_local_bhavcopy(root: Path, path: Path, *, source: str, url: str,
                          outcome_only: bool = False, notes: str = "") -> dict:
    rows, receipt = read_bhavcopy(path)
    receipt["result"] = ingest_batch(
        root, dataset="equity_daily", source=source, url=url, raw_path=path,
        rows=rows, outcome_only=outcome_only,
        notes=(notes + " " if notes else "") + json.dumps(receipt, sort_keys=True),
    )
    return receipt


def read_preparation_daily(path: Path) -> tuple[list[dict], str]:
    """Normalize the two explicitly reconstructed RELIANCE rows in the saved prep."""
    evidence = json.loads(path.read_text(encoding="utf-8"))
    item = next((entry for entry in evidence if "RELIANCE NSE daily observations reconstructed" in entry.get("text", "")), None)
    if item is None:
        raise ValueError("preparation does not contain the documented RELIANCE reconstruction")
    import re

    text = item["text"]
    pattern = re.compile(
        r"(?P<day>\d{4}-\d{2}-\d{2}) O/H/L/C INR "
        r"(?P<open>[\d,.]+)/(?P<high>[\d,.]+)/(?P<low>[\d,.]+)/(?P<close>[\d,.]+), "
        r"volume (?P<volume>[\d,]+)"
    )
    rows = []
    for match in pattern.finditer(text):
        day = date.fromisoformat(match["day"]).isoformat()
        rows.append({
            "key": f"{day}|INE002A01018|EQ",
            "session": day,
            "symbol": "RELIANCE",
            "event_at": None,
            "available_at": item["available_at"],
            "availability": "inferred",
            "availability_basis": "saved preparation records this time; source page was not preserved and observation is reconstructed",
            "values": {
                "isin": "INE002A01018", "series": "EQ",
                "open_paise": _paise(match["open"].replace(",", ""), "open", 0),
                "high_paise": _paise(match["high"].replace(",", ""), "high", 0),
                "low_paise": _paise(match["low"].replace(",", ""), "low", 0),
                "close_paise": _paise(match["close"].replace(",", ""), "close", 0),
                "volume_shares": int(match["volume"].replace(",", "")),
                "source_note": "reconstructed from dated historical rows; source page not archived",
            },
        })
    if len(rows) != 2:
        raise ValueError(f"expected exactly two documented RELIANCE rows; found {len(rows)}")
    return rows, item["source"]


def ingest_preparation_daily(root: Path, path: Path) -> dict:
    rows, source = read_preparation_daily(path)
    # Keep the saved preparation as the immutable local receipt. The linked
    # pages are citations only; no automated requests are made to either host.
    return ingest_batch(
        root, dataset="equity_daily", source=source, url=source, raw_path=path,
        rows=rows,
        notes="Reconstructed RELIANCE daily bars from saved pre-session preparation; source pages were not archived.",
    )


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("archive", type=Path, nargs="?", help="locally held NSE CM ZIP archive")
    cli.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    cli.add_argument("--source", help="source name for provenance")
    cli.add_argument("--url", help="original archive URL")
    cli.add_argument("--tejhq-dir", type=Path,
                     help="local root of TejHQ NSE parquet files downloaded from Hugging Face")
    cli.add_argument("--preparation", type=Path,
                     help="saved preparation JSON containing the reconstructed 19/20 Nov rows")
    cli.add_argument("--outcome-only", action="store_true",
                     help="mark observations as outcomes; never eligible as pre-decision inputs")
    cli.add_argument("--notes", default="")
    args = cli.parse_args()
    if args.tejhq_dir:
        print(json.dumps(ingest_tejhq_history(args.root, args.tejhq_dir), indent=2, sort_keys=True))
        return
    if args.preparation:
        print(json.dumps(ingest_preparation_daily(args.root, args.preparation), indent=2, sort_keys=True))
        return
    if not args.archive or not args.source or not args.url:
        cli.error("provide ARCHIVE with --source and --url, or choose --tejhq-dir/--preparation")
    print(json.dumps(ingest_local_bhavcopy(
        args.root, args.archive, source=args.source, url=args.url,
        outcome_only=args.outcome_only, notes=args.notes,
    ), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
