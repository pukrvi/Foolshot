"""Lawful, point-in-time market context ingestion helpers.

This module intentionally contains no web scraper. Each source needs an explicit
reuse basis before its bytes are collected. The only source imported here by
default is a locally saved news receipt already held by the owner; we preserve
its metadata and hash, never the article body.
"""

from __future__ import annotations

import hashlib
import json
from email.utils import parsedate_to_datetime
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator


DEFAULT_INTAKE = Path(
    "/Users/vishmac/Documents/GitHub/Foolshot/data/private/"
    "monday-20261123-intake"
)
DEFAULT_MARKET_ROOT = Path(
    "/Users/vishmac/Documents/GitHub/Foolshot/data/private/market-data"
)
EIA_PETROLEUM_BULK_URL = "https://www.eia.gov/opendata/bulk/PET.zip"
EIA_WTI_DAILY_SERIES = "PET.RWTC.D"
CONTEXT_START = "2021-11-22"
CONTEXT_CUTOFF = "2026-11-22"


def _aware_iso(value: str) -> str:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"timestamp must include a UTC offset: {value!r}")
    return parsed.isoformat()


def ingest_saved_news_metadata(
    root: Path,
    *,
    intake_dir: Path = DEFAULT_INTAKE,
) -> dict[str, Any]:
    """Ingest the known ET story's local receipt without reading article text.

    `source-receipts.json` is the receipt of the previously captured HTML. The
    local preparation file is deliberately not opened: it contains an excerpt.
    The page's publisher update time is used as the earliest known availability
    timestamp, and is not represented as proof of the page's original publish
    time or of what an earlier version contained.
    """
    from .market_store import ingest_batch

    receipts_path = intake_dir / "source-receipts.json"
    receipt = json.loads(receipts_path.read_text(encoding="utf-8"))
    source = str(receipt["sunday_source"])
    updated = _aware_iso(str(receipt["sunday_publisher_updated"]))
    page_hash = str(receipt["sunday_page_sha256"])
    if len(page_hash) != 64 or any(c not in "0123456789abcdef" for c in page_hash):
        raise ValueError("sunday_page_sha256 must be a lowercase SHA-256 hex digest")

    # Hash the receipt itself so the normalized row remains anchored to exact
    # local acquisition evidence without copying any copyrighted article text.
    receipt_hash = hashlib.sha256(receipts_path.read_bytes()).hexdigest()
    row = {
        "key": f"et:{page_hash}",
        "session": updated[:10],
        "symbol": None,
        "event_at": None,
        "available_at": updated,
        "availability": "verified",
        "availability_basis": (
            "publisher update timestamp preserved in local source receipt; "
            "does not establish original publication time or prior-version content"
        ),
        "values": {
            "publisher": "Economic Times",
            "url": source,
            "publisher_updated_at": updated,
            "captured_page_sha256": page_hash,
            "receipt_sha256": receipt_hash,
            "content_stored": False,
            "content_basis": "metadata only; no article body or excerpt copied",
        },
    }
    return ingest_batch(
        root,
        dataset="news",
        source="Economic Times locally saved source receipt",
        url=source,
        raw_path=receipts_path,
        rows=[row],
        acquired_at=datetime.now().astimezone().isoformat(),
        notes=(
            "Metadata-only import from the existing local receipt. The receipt's "
            "publisher update timestamp is not treated as original publication time."
        ),
    )


def _read_eia_series(zip_path: Path, series_id: str) -> dict[str, Any]:
    """Read one JSON line from EIA's documented petroleum bulk ZIP."""
    with zipfile.ZipFile(zip_path) as archive:
        members = [name for name in archive.namelist() if name.endswith(".txt")]
        if len(members) != 1:
            raise ValueError(f"expected one .txt member in EIA ZIP, found {members!r}")
        with archive.open(members[0]) as stream:
            for line in stream:
                if series_id.encode("ascii") not in line:
                    continue
                item = json.loads(line)
                if item.get("series_id") == series_id:
                    return item
    raise LookupError(f"EIA bulk file has no series {series_id}")


def eia_wti_rows(
    zip_path: Path,
    *,
    start: str = CONTEXT_START,
    cutoff: str = CONTEXT_CUTOFF,
) -> Iterator[dict[str, Any]]:
    """Normalize EIA daily WTI observations, retaining unknown historical availability.

    The current bulk file is a revised snapshot; it is not an ALFRED-style
    vintage archive. Consequently no observation receives a guessed release
    timestamp, and consumers must not treat it as point-in-time information.
    """
    series = _read_eia_series(zip_path, EIA_WTI_DAILY_SERIES)
    series_updated = _aware_iso(str(series["last_updated"]))
    for yyyymmdd, value in series["data"]:
        day = f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"
        if start <= day <= cutoff and value is not None:
            yield {
                "key": f"eia:{EIA_WTI_DAILY_SERIES}:{day}",
                "session": day,
                "symbol": "WTI",
                "event_at": None,
                "available_at": None,
                "availability": "unknown",
                "availability_basis": (
                    "current EIA bulk snapshot is revised; series last_updated "
                    "is not the historical release time for this observation"
                ),
                "values": {
                    "series_id": EIA_WTI_DAILY_SERIES,
                    "name": series["name"],
                    "price_usd_per_barrel": float(value),
                    "units": series["units"],
                    "source_series_last_updated": series_updated,
                    "vintage_status": "current_revised_snapshot_no_historical_vintage",
                },
            }


def ingest_eia_wti_bulk(
    root: Path = DEFAULT_MARKET_ROOT,
    *,
    zip_path: Path | None = None,
    start: str = CONTEXT_START,
    cutoff: str = CONTEXT_CUTOFF,
) -> dict[str, Any]:
    """Ingest five years of EIA daily WTI spot prices from the official bulk file."""
    from .market_store import ingest_batch

    raw_path = zip_path or (root / "raw" / "eia" / "PET.zip")
    rows = list(eia_wti_rows(raw_path, start=start, cutoff=cutoff))
    acquired_at = datetime.fromtimestamp(raw_path.stat().st_mtime).astimezone().isoformat()
    return ingest_batch(
        root,
        dataset="macro",
        source="U.S. Energy Information Administration Petroleum Bulk Data",
        url=EIA_PETROLEUM_BULK_URL,
        raw_path=raw_path,
        rows=rows,
        acquired_at=acquired_at,
        outcome_only=False,
        notes=(
            "EIA identifies its data as public-domain and permits use/distribution. "
            "Source: EIA, Cushing OK WTI Spot Price FOB, Daily (PET.RWTC.D). "
            "Current revised snapshot only; observation-level release vintages are "
            "unavailable, so availability is unknown and this import is outcome-only."
        ),
    )


def ingest_bls_employment_event(
    root: Path = DEFAULT_MARKET_ROOT,
) -> dict[str, Any]:
    """Record the official BLS Employment Situation release as metadata only.

    The saved sidecar is limited to bibliographic fields and the source's stated
    release time. No release body, tables, or excerpts are downloaded or stored.
    BLS calendar time is U.S. Eastern Time; on this date it was UTC-05:00.
    """
    from .market_store import ingest_batch

    source_url = "https://www.bls.gov/news.release/archives/empsit_11062026.htm"
    release_at = "2026-11-06T08:30:00-05:00"
    sidecar = root / "raw" / "bls" / "USDL-26-1632.metadata.json"
    sidecar.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    metadata = {
        "title": "The Employment Situation — October 2026",
        "release_number": "USDL-26-1632",
        "source": "U.S. Bureau of Labor Statistics",
        "source_url": source_url,
        "source_release_time": release_at,
        "metadata_only": True,
        "body_downloaded": False,
        "metadata_basis": (
            "Official BLS release record identifies an embargo time of 08:30 ET "
            "on 2026-11-06; BLS dissemination policy says releases appear on its "
            "homepage within seconds of official release time."
        ),
    }
    raw_bytes = (json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    sidecar.write_bytes(raw_bytes)
    row = {
        "key": "bls:USDL-26-1632",
        "session": "2026-11-06",
        "symbol": "US_EMPLOYMENT_SITUATION",
        "event_at": release_at,
        "available_at": release_at,
        "availability": "inferred",
        "availability_basis": (
            "official BLS embargo/release time; exact successful public page "
            "receipt time was not captured"
        ),
        "values": {
            "title": metadata["title"],
            "release_number": metadata["release_number"],
            "country": "US",
            "release_type": "employment",
            "reference_period": "2026-10",
            "source_url": source_url,
            "metadata_only": True,
            "body_downloaded": False,
        },
    }
    return ingest_batch(
        root,
        dataset="economic_events",
        source="U.S. Bureau of Labor Statistics release metadata",
        url=source_url,
        raw_path=sidecar,
        rows=[row],
        acquired_at=datetime.now().astimezone().isoformat(),
        notes=(
            "Metadata-only event record. BLS's stated embargo time is used; "
            "exact public-page receipt time was not captured. Source: BLS; "
            "accessed 2026-11-24."
        ),
    )


def ingest_eia_wpsr_wti_release(
    root: Path = DEFAULT_MARKET_ROOT,
    *,
    pdf_path: Path | None = None,
    headers_path: Path | None = None,
) -> dict[str, Any]:
    """Ingest one dated WPSR WTI observation with its dated release evidence.

    Unlike the EIA bulk-history snapshot, the Nov. 18, 2026 WPSR is a dated
    release artifact. Its prices table reports WTI Cushing at $91.96/barrel for
    Nov. 13. The saved response Last-Modified time is used as a conservative,
    inferred availability bound; the ordinary 10:30 ET schedule alone is not
    treated as proof of actual publication time.
    """
    from .market_store import ingest_batch

    pdf = pdf_path or (root / "raw" / "eia" / "wpsr-highlights-20261118.pdf")
    headers = headers_path or (root / "raw" / "eia" / "wpsr-highlights-20261118.headers")
    header_text = headers.read_text(encoding="latin-1")
    last_modified_line = next(
        (line.split(":", 1)[1].strip() for line in header_text.splitlines()
         if line.lower().startswith("last-modified:")),
        None,
    )
    if not last_modified_line:
        raise ValueError("EIA WPSR HTTP headers do not contain Last-Modified")
    available = parsedate_to_datetime(last_modified_line).isoformat()
    url = "https://www.eia.gov/petroleum/supply/weekly/pdf/highlights.pdf?date=20261118"
    row = {
        "key": "eia:wpsr:WTI-CUSHING:2026-11-13:vintage-2026-11-18",
        "session": "2026-11-13",
        "symbol": "WTI",
        "event_at": None,
        "available_at": available,
        "availability": "inferred",
        "availability_basis": (
            "dated EIA WPSR report release 2026-11-18; PDF HTTP Last-Modified "
            f"{last_modified_line}; exact public availability time was not captured"
        ),
        "values": {
            "series": "WTI Crude Oil - Cushing",
            "price_usd_per_barrel": 91.96,
            "units": "Dollars per Barrel",
            "observation_date": "2026-11-13",
            "report_release_date": "2026-11-18",
            "source_vintage": "EIA WPSR dated 2026-11-18",
            "source_last_modified": last_modified_line,
            "source_table": "Prices table in Weekly Petroleum Status Report highlights",
        },
    }
    return ingest_batch(
        root,
        dataset="macro",
        source="U.S. Energy Information Administration WPSR release",
        url=url,
        raw_path=pdf,
        rows=[row],
        acquired_at=datetime.fromtimestamp(pdf.stat().st_mtime).astimezone().isoformat(),
        notes=(
            "Source: U.S. Energy Information Administration, Weekly Petroleum "
            "Status Report, publication date November 18, 2026. Data point is "
            "WTI Cushing $91.96/barrel dated November 13. EIA public-domain data; "
            "the exact public availability timestamp was not captured."
        ),
    )

