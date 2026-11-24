"""Federal Reserve H.10 USD/INR observations and separately dated releases."""

import argparse
import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from zoneinfo import ZoneInfo

from .market_download import fetch, write_json
from .market_store import SESSION, ingest_batch

BASE = "https://www.federalreserve.gov/releases/h10/"
HISTORY = BASE + "hist/dat00_in.htm"
SOURCE = "Federal Reserve Board H.10"
NY = ZoneInfo("America/New_York")
START = date(2021, 11, 23)
RELEASES = (date(2026, 11, 2), date(2026, 11, 9), date(2026, 11, 16), SESSION)
SCHEDULE = "https://www.federalreserve.gov/data/releaseschedule.htm"


class TableRows(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("th", "td") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag):
        if tag in ("th", "td") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def observation(day, text, release=None):
    if text == "ND":
        return None
    rate = Decimal(text)
    if not rate.is_finite() or rate <= 0:
        raise ValueError("H.10 exchange rate must be positive and finite")
    available = datetime.combine(release, time(16, 15), NY).isoformat() if release else None
    return {
        "key": f"USDINR/{day}", "session": str(day), "symbol": "USDINR",
        "event_at": datetime.combine(day, time(12), NY).isoformat(),
        "available_at": available, "availability": "verified" if release else "unknown",
        "availability_basis": (
            "Release-specific H.10 archive and Board statistical calendar for 16:15 New York"
            if release else "Consolidated source can contain revisions without publication vintages"
        ),
        "values": {
            "value": str(rate), "unit": "INR per USD", "series": "New York noon buying rate",
            "release_date": str(release) if release else None,
            "release_schedule": SCHEDULE if release else None,
        },
    }


def history_rows(text):
    if "Historical Rates for the Indian Rupee" not in text:
        raise ValueError("expected Federal Reserve India H.10 history")
    for cells in TableRows(text).rows:
        if len(cells) == 2 and re.fullmatch(r"\d{1,2}-[A-Z]{3}-\d{2}", cells[0]):
            day = datetime.strptime(cells[0], "%d-%b-%y").date()
            if START <= day < SESSION:
                row = observation(day, cells[1])
                if row is not None:
                    yield row


def release_rows(text, day):
    match = re.search(r"Release Date:\s*([A-Za-z]+ \d{1,2}, \d{4})", text)
    if match is None or datetime.strptime(match[1], "%B %d, %Y").date() != day:
        raise ValueError(f"H.10 body date does not match dated release {day}")
    cells = TableRows(text).rows
    headers = next(row[2:] for row in cells if row[:2] == ["COUNTRY", "CURRENCY"])
    values = next(row[2:] for row in cells if row[:2] == ["INDIA", "RUPEE"])
    if len(headers) != len(values) or len(headers) != 5:
        raise ValueError("unexpected H.10 weekly layout")
    for header, value in zip(headers, values, strict=True):
        month_day = header.replace(".", "")
        observed_day = datetime.strptime(f"{month_day} {day.year}", "%b %d %Y").date()
        if observed_day >= day and day.month == 1:
            observed_day = observed_day.replace(year=day.year - 1)
        if not timedelta(0) < day - observed_day <= timedelta(days=10):
            raise ValueError("invalid H.10 observation date in a release")
        row = observation(observed_day, value, day)
        if row is not None:
            yield row


def backfill(root, refresh=False):
    receipts = []
    items = [(HISTORY, history_rows)]
    items.extend((BASE + day.strftime("%Y%m%d") + "/", lambda text, day=day: release_rows(text, day))
                 for day in RELEASES)
    for url, parser in items:
        try:
            path, info = fetch(root, url, refresh=refresh)
            rows = list(parser(path.read_text(encoding="utf-8")))
            result = ingest_batch(
                root, dataset="macro", source=SOURCE, url=url, raw_path=path, rows=rows,
                acquired_at=info["acquired_at"], notes="Board public-domain H.10 data. " + (
                    "Dated release." if url != HISTORY else "Consolidated revisions unknown."
                ),
            )
            receipts.append({"source": SOURCE, "url": url, "http": info["status"], **result})
        except (OSError, ValueError, StopIteration) as exc:
            receipts.append({"source": SOURCE, "url": url, "operation": "download and import", "error": str(exc)})
    write_json(root / "reports" / "h10-sources.json", receipts)
    return receipts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    for receipt in backfill(args.root, args.refresh):
        print(receipt)


if __name__ == "__main__":
    main()
