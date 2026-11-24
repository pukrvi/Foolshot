"""Download and normalize NSE public daily archives for private research.

The store keeps the exchange's consolidated daily files for the NSE derivatives
and index families. NSE's website terms restrict systematic automated
collection, so this collector is intentionally narrow: it fetches only the
reviewed daily archive objects, waits between requests, and keeps the raw bytes,
hashes, source URLs and acquisition times local. The data is not redistributed.
No orders, subscriptions or trials are involved.

Two archive families are handled:

* F&O UDiFF bhavcopy (``BhavCopy_NSE_FO_...csv.zip``) for every F&O contract,
  including expired options and futures.
* Index close files (``ind_close_all_DDMMYYYY.csv``) for the broad index,
  sector index and India VIX history.

A session list is derived from the already imported cash-market history so that
exchange holidays are not guessed from weekdays.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import time
import zipfile
from datetime import date, datetime
from pathlib import Path

from .market_download import fetch, write_json
from .market_store import ingest_batch, read_db

DEFAULT_ROOT = Path("/Users/vishmac/Documents/GitHub/Foolshot/data/private/market-data")
FO_SOURCE = "NSE official F&O UDiFF bhavcopy archive"
INDEX_SOURCE = "NSE official index close archive"
FO_URL = "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{day}_F_0000.csv.zip"
INDEX_URL = "https://nsearchives.nseindia.com/content/indices/ind_close_all_{day}.csv"
FO_DATASET = "derivatives_daily"
INDEX_DATASET = "indices"
KINDS = {"fo": (FO_DATASET, FO_SOURCE, FO_URL),
         "indices": (INDEX_DATASET, INDEX_SOURCE, INDEX_URL)}


def _compact(day: str, pattern: str = "%Y%m%d") -> str:
    return date.fromisoformat(day).strftime(pattern)


def archive_url(kind: str, day: str) -> str:
    pattern = "%d%m%Y" if kind == "indices" else "%Y%m%d"
    return KINDS[kind][2].format(day=_compact(day, pattern))


def reference_sessions(root: Path, start: str, end: str) -> list[str]:
    """Completed NSE sessions already established by the imported cash history."""
    with read_db(root) as db:
        return [row[0] for row in db.execute("""
            SELECT DISTINCT o.session FROM observation o JOIN receipt r ON r.id=o.receipt_id
            WHERE o.dataset='equity_daily' AND r.outcome_only=0
              AND o.source='TejHQ Indian Markets parquet'
              AND o.session BETWEEN ? AND ?
            ORDER BY o.session
        """, (start, end))]


def _number(value):
    if value is None:
        return None
    text = value.strip().replace(",", "")
    if text in {"", "-", "--"}:
        return None
    return float(text)


def _index_day(value: str) -> str:
    return datetime.strptime(value.strip(), "%d-%m-%Y").date().isoformat()


def _csv_payload(path: Path) -> bytes:
    raw = path.read_bytes()
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise ValueError("F&O archive must contain exactly one CSV")
            return archive.read(names[0])
    if raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)
    return raw


FO_FIELDS = {
    "session": "TradDt", "contract_id": "FinInstrmId", "symbol": "TckrSymb",
    "expiry": "XpryDt", "strike": "StrkPric", "option_type": "OptnTp",
    "open": "OpnPric", "high": "HghPric", "low": "LwPric", "close": "ClsPric",
    "last_price": "LastPric", "previous_close": "PrvsClsgPric",
    "underlying_price": "UndrlygPric", "settlement": "SttlmPric",
    "open_interest": "OpnIntrst", "oi_change": "ChngInOpnIntrst",
    "volume": "TtlTradgVol", "turnover_rupees": "TtlTrfVal",
    "trades": "TtlNbOfTxsExctd", "lot_size": "NewBrdLotQty",
    "instrument_type": "FinInstrmTp", "contract_name": "FinInstrmNm",
}
FO_TEXT = {"session", "contract_id", "symbol", "expiry", "option_type",
           "instrument_type", "contract_name"}


def parse_fo(path: Path) -> list[dict]:
    """Fast path for the reviewed NSE UDiFF F&O bhavcopy layout."""
    reader = csv.reader(io.StringIO(_csv_payload(path).decode("utf-8-sig")))
    header = next(reader, None)
    if not header or "FinInstrmId" not in header or "OptnTp" not in header:
        raise ValueError("F&O archive is not the reviewed UDiFF bhavcopy")
    index = {name: position for position, name in enumerate(header)}
    missing = [column for column in FO_FIELDS.values() if column not in index]
    if missing:
        raise ValueError(f"F&O archive is missing reviewed columns: {missing}")
    rows = []
    for line, record in enumerate(reader, 2):
        values = {}
        for field, column in FO_FIELDS.items():
            text = record[index[column]].strip()
            if field in FO_TEXT:
                if text:
                    values[field] = text
                continue
            if text:
                values[field] = float(text)
        session = values.pop("session", None)
        contract_id = values.get("contract_id")
        if not session or not contract_id:
            raise ValueError(f"row {line}: F&O contract requires session and instrument id")
        if not all(field in values for field in ("open", "high", "low", "close")):
            raise ValueError(f"row {line}: F&O contract requires OHLC")
        rows.append({
            "key": f"{contract_id}|{session}", "session": session,
            "symbol": values.get("symbol"), "event_at": None, "available_at": None,
            "availability": "unknown",
            "availability_basis": "public daily archive; no per-file publication timestamp retained",
            "values": values,
        })
    if not rows:
        raise ValueError("F&O archive contains no contract rows")
    return rows


def parse_indices(path: Path) -> list[dict]:
    """Normalize the NSE index close CSV without changing source values."""
    raw = path.read_bytes()
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not reader.fieldnames or "Index Name" not in reader.fieldnames:
        raise ValueError("index archive is not the reviewed NSE close file")
    rows = []
    for line, row in enumerate(reader, 2):
        name = (row.get("Index Name") or "").strip()
        if not name:
            continue
        session = _index_day(row.get("Index Date") or "")
        values = {}
        for column, field in (
            ("Open Index Value", "open"), ("High Index Value", "high"),
            ("Low Index Value", "low"), ("Closing Index Value", "close"),
            ("Points Change", "points_change"), ("Change(%)", "change_pct"),
            ("Volume", "volume"), ("Turnover (Rs. Cr.)", "turnover_crore"),
            ("P/E", "pe"), ("P/B", "pb"), ("Div Yield", "div_yield"),
        ):
            number = _number(row.get(column))
            if number is not None:
                values[field] = number
        if "close" not in values:
            raise ValueError(f"row {line}: index close requires a closing value")
        rows.append({
            "key": f"NSE_INDEX|{name}|{session}", "session": session, "symbol": name,
            "event_at": None, "available_at": None, "availability": "unknown",
            "availability_basis": "public daily archive; no per-file publication timestamp retained",
            "values": values,
        })
    if not rows:
        raise ValueError("index archive contains no rows")
    return rows


def _check_blob(kind: str, blob: Path) -> None:
    with blob.open("rb") as stream:
        head = stream.read(32)
    if kind == "fo":
        if head[:2] != b"PK":
            raise ValueError("F&O archive is not a ZIP object")
        with zipfile.ZipFile(blob) as archive:
            names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise ValueError("F&O archive must contain exactly one CSV")
    else:
        if not head.lstrip(b"\xef\xbb\xbf").startswith(b"Index Name"):
            raise ValueError("index archive does not start with the reviewed header")


def download(root: Path, kind: str, sessions: list[str], *, delay: float = 1.0,
             refresh: bool = False, max_bytes: int = 64_000_000) -> list[dict]:
    """Fetch each reviewed archive object, checkpointing every complete response."""
    results = []
    for position, day in enumerate(sessions, 1):
        url = archive_url(kind, day)
        try:
            blob, info = fetch(root, url, refresh=refresh, max_bytes=max_bytes)
            _check_blob(kind, blob)
            results.append({"session": day, "status": "ok", "url": url,
                            "raw_sha256": info["raw_sha256"], "raw_bytes": info["raw_bytes"],
                            "acquired_at": info["acquired_at"]})
        except Exception as exc:  # keep the run resumable across per-object failures
            results.append({"session": day, "status": "error", "url": url, "error": str(exc)})
        if position < len(sessions):
            time.sleep(delay)
    return results


def _checkpoint(root: Path, url: str) -> dict:
    key = hashlib.sha256(url.encode()).hexdigest()
    path = root / "checkpoints" / (key + ".json")
    if not path.is_file():
        raise FileNotFoundError(f"no completed download checkpoint for {url}")
    return json.loads(path.read_text())


def _receipt_exists(root: Path, dataset: str, url: str) -> bool:
    with read_db(root) as db:
        return db.execute(
            "SELECT 1 FROM receipt WHERE dataset=? AND url=? LIMIT 1", (dataset, url)
        ).fetchone() is not None


def import_downloads(root: Path, kind: str, sessions: list[str]) -> list[dict]:
    """Parse and ingest each checkpointed archive; identical reruns add no rows."""
    dataset, source, _ = KINDS[kind]
    results = []
    for day in sessions:
        url = archive_url(kind, day)
        try:
            if _receipt_exists(root, dataset, url):
                results.append({"session": day, "status": "already_imported", "url": url})
                continue
            info = _checkpoint(root, url)
            blob = root / info["raw_path"]
            if kind == "fo":
                rows = parse_fo(blob)
            else:
                rows = parse_indices(blob)
            result = ingest_batch(
                root, dataset=dataset, source=source, url=url, raw_path=blob,
                rows=rows, acquired_at=info["acquired_at"],
                notes=("Reviewed public NSE daily archive retained locally for private "
                       "research; exchange terms restrict redistribution and systematic "
                       "collection. Per-file publication times are kept in the download "
                       "checkpoint but are not asserted as verified observation availability."),
            )
            results.append({"session": day, "status": "imported", **result})
        except Exception as exc:
            results.append({"session": day, "status": "error", "url": url, "error": str(exc)})
    return results


def coverage(root: Path, kind: str, sessions: list[str]) -> dict:
    """Measured coverage for one archive family against the reference sessions."""
    dataset, source, _ = KINDS[kind]
    with read_db(root) as db:
        receipts = [dict(row) for row in db.execute("""
            SELECT id,url,raw_sha256,raw_bytes,acquired_at,records
            FROM receipt WHERE dataset=? AND source=? ORDER BY url
        """, (dataset, source))]
        stats = dict(db.execute("""
            SELECT COUNT(*) AS rows, COUNT(DISTINCT session) AS sessions,
                   MIN(session) AS first_session, MAX(session) AS last_session,
                   COUNT(DISTINCT symbol) AS symbols
            FROM observation WHERE dataset=? AND source=?
        """, (dataset, source)).fetchone())
        present = {row[0] for row in db.execute(
            "SELECT DISTINCT session FROM observation WHERE dataset=? AND source=?",
            (dataset, source))}
        option_rows = db.execute("""
            SELECT COUNT(*) FROM observation WHERE dataset=? AND source=?
              AND UPPER(json_extract(values_json,'$.option_type')) IN ('CE','PE','C','P','CALL','PUT')
        """, (dataset, source)).fetchone()[0]
        future_rows = db.execute("""
            SELECT COUNT(*) FROM observation WHERE dataset=? AND source=?
              AND (json_extract(values_json,'$.option_type') IS NULL
                   OR UPPER(json_extract(values_json,'$.option_type')) NOT IN ('CE','PE','C','P','CALL','PUT'))
        """, (dataset, source)).fetchone()[0]
        underlyings = [(row[0], row[1]) for row in db.execute("""
            SELECT symbol, COUNT(*) FROM observation WHERE dataset=? AND source=?
            GROUP BY symbol ORDER BY COUNT(*) DESC LIMIT 15
        """, (dataset, source))]
    missing = [day for day in sessions if day not in present]
    return {
        "dataset": dataset, "source": source,
        "requested_from": sessions[0] if sessions else None,
        "requested_through": sessions[-1] if sessions else None,
        "reference_sessions": len(sessions),
        "downloaded_files": len(receipts),
        "normalized_rows": stats["rows"], "sessions": stats["sessions"],
        "first_session": stats["first_session"], "last_session": stats["last_session"],
        "symbols": stats["symbols"], "option_rows": option_rows, "future_rows": future_rows,
        "missing_sessions": missing,
        "source_storage_bytes": sum(item["raw_bytes"] for item in receipts),
        "top_underlyings": [{"symbol": symbol, "rows": count} for symbol, count in underlyings],
        "receipts": receipts,
    }


def run(root: Path, kind: str, start: str, end: str, *, delay: float = 1.0,
        refresh: bool = False, download_only: bool = False,
        import_only: bool = False) -> dict:
    sessions = reference_sessions(root, start, end)
    if not sessions:
        raise ValueError("no completed reference sessions in the requested window")
    result = {"kind": kind, "from": start, "through": end, "sessions": len(sessions)}
    if not import_only:
        downloads = download(root, kind, sessions, delay=delay, refresh=refresh)
        result["downloads"] = {
            "ok": sum(item["status"] == "ok" for item in downloads),
            "errors": [item for item in downloads if item["status"] == "error"],
        }
    if not download_only:
        imports = import_downloads(root, kind, sessions)
        result["imports"] = {
            "imported": sum(item["status"] == "imported" for item in imports),
            "already_imported": sum(item["status"] == "already_imported" for item in imports),
            "errors": [item for item in imports if item["status"] == "error"],
        }
        result["coverage"] = coverage(root, kind, sessions)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--kind", choices=sorted(KINDS), required=True)
    parser.add_argument("--start", default="2025-11-24")
    parser.add_argument("--end", default="2026-11-22")
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--download-only", action="store_true")
    parser.add_argument("--import-only", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    result = run(args.root, args.kind, args.start, args.end, delay=args.delay,
                 refresh=args.refresh, download_only=args.download_only,
                 import_only=args.import_only)
    if args.report:
        write_json(args.report, result)
        print(args.report)
    summary = {key: value for key, value in result.items() if key != "coverage"}
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if not (result.get("downloads", {}).get("errors")
                     or result.get("imports", {}).get("errors")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
