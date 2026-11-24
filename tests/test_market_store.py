import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from foolshot import market_download, market_evidence, market_store
from foolshot.market_derivatives import parse_csv
from foolshot.learning import Snapshot


class _Response:
    def __init__(self, body, length, url):
        self.body = body
        self.length = length
        self.url = url
        self.status = 200
        self.headers = {"Content-Length": str(length), "ETag": '"fixture"'}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, _size=-1):
        body, self.body = self.body, b""
        return body


def _row(key, *, available_at, value, availability="verified", event_at="2026-11-22T15:00:00+05:30"):
    return {
        "key": key,
        "session": "2026-11-22",
        "symbol": "NIFTY",
        "event_at": event_at,
        "available_at": available_at,
        "availability": availability,
        "availability_basis": "synthetic test evidence",
        "values": {"close": value},
    }


def _ingest(root, tmp, name, rows, *, source="fixture", url=None, outcome_only=False):
    raw = Path(tmp) / f"{name}.csv"
    raw.write_text(name)
    return market_store.ingest_batch(
        root,
        dataset="derivatives_daily",
        source=source,
        url=url or f"https://example.test/{name}.csv",
        raw_path=raw,
        rows=rows,
        acquired_at="2026-11-24T00:00:00Z",
        outcome_only=outcome_only,
    )


def _values(root, *, cutoff="2026-11-23T00:00:00+05:30"):
    return {
        row["record_key"]: row["values"]["close"]
        for row in market_store.observations(root, "derivatives_daily", cutoff)
    }


class MarketStoreTests(unittest.TestCase):
  def test_cutoff_is_strict_instant_and_excludes_unknown_and_outcome_only(self):
    cutoff = "2026-11-23T00:00:00+05:30"
    with tempfile.TemporaryDirectory() as directory:
        root, tmp = Path(directory) / "store", Path(directory)
        root.mkdir()
        _ingest(root, tmp, "before", [_row(
            "before", available_at="2026-11-22T18:29:59.999999Z", value=1,
        )])
        _ingest(root, tmp, "at-cutoff", [_row(
            "at-cutoff", available_at="2026-11-23T00:00:00+05:30", value=2,
        )])
        _ingest(root, tmp, "unknown", [_row(
            "unknown", available_at=None, availability="unknown", value=3,
        )])
        _ingest(root, tmp, "outcome", [_row(
            "outcome", available_at="2026-11-22T12:00:00Z", value=4,
        )], outcome_only=True)

        self.assertEqual(_values(root, cutoff=cutoff), {"before": 1.0})
        # The same instant in a different offset is still exactly at cutoff.
        self.assertEqual(_values(root, cutoff="2026-11-22T18:30:00Z"), {"before": 1.0})


  def test_later_correction_versions_earlier_row_and_unknown_never_enters(self):
    with tempfile.TemporaryDirectory() as directory:
        root, tmp = Path(directory) / "store", Path(directory)
        root.mkdir()
        _ingest(root, tmp, "original", [_row(
            "bar-1", available_at="2026-11-22T17:00:00Z", value=100,
        )])
        _ingest(root, tmp, "correction", [_row(
            "bar-1", available_at="2026-11-22T19:00:00Z", value=101,
        )])
        _ingest(root, tmp, "unknown-revision", [_row(
            "bar-1", available_at=None, availability="unknown", value=102,
        )])

        self.assertEqual(_values(root, cutoff="2026-11-22T18:30:00Z"), {"bar-1": 100.0})
        self.assertEqual(_values(root, cutoff="2026-11-23T18:31:00Z"), {"bar-1": 101.0})


  def test_same_timestamp_conflicting_revision_is_quarantined(self):
    with tempfile.TemporaryDirectory() as directory:
        root, tmp = Path(directory) / "store", Path(directory)
        root.mkdir()
        stamp = "2026-11-22T19:00:00Z"
        _ingest(root, tmp, "conflict-a", [_row("bar-x", available_at=stamp, value=50)], source="same-feed")
        _ingest(root, tmp, "conflict-b", [_row("bar-x", available_at=stamp, value=51)], source="same-feed")

        self.assertEqual(_values(root, cutoff="2026-11-22T20:00:00Z"), {})


  def test_repeat_import_adds_zero_rows(self):
    with tempfile.TemporaryDirectory() as directory:
        root, tmp = Path(directory) / "store", Path(directory)
        root.mkdir()
        row = _row("same", available_at="2026-11-22T18:00:00Z", value=20)
        first = _ingest(root, tmp, "repeat", [row], url="https://example.test/stable.csv")
        again = market_store.ingest_batch(
            root, dataset="derivatives_daily", source="fixture",
            url="https://example.test/stable.csv", raw_path=tmp / "repeat.csv",
            rows=[row], acquired_at="2026-11-24T00:00:00Z",
        )

        self.assertEqual(first["inserted"], 1)
        self.assertEqual(again["inserted"], 0)
        self.assertEqual(again["receipt_id"], first["receipt_id"])
        self.assertEqual(again["raw_sha256"], first["raw_sha256"])


  def test_duplicate_key_batch_rolls_back_receipt_and_observations(self):
    with tempfile.TemporaryDirectory() as directory:
        root, tmp = Path(directory) / "store", Path(directory)
        root.mkdir()
        rows = [
            _row("duplicate", available_at="2026-11-22T18:00:00Z", value=20),
            _row("duplicate", available_at="2026-11-22T18:01:00Z", value=21),
        ]
        with self.assertRaises(sqlite3.IntegrityError):
            _ingest(root, tmp, "dupe", rows)

        with market_store.read_db(root) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM receipt").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM observation").fetchone()[0], 0)


  def test_download_retries_incomplete_body_then_checkpoints_cached_hash(self):
    url = "https://data.example.test/archive.zip"
    payload = b"complete synthetic archive"
    partial = _Response(b"short", len(payload), url)
    complete = _Response(payload, len(payload), url)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        with patch.object(market_download, "urlopen", side_effect=[partial, complete]) as open_mock, \
             patch.object(market_download.time, "sleep") as sleep_mock:
            blob, info = market_download.fetch(root, url)

        self.assertEqual(open_mock.call_count, 2)
        sleep_mock.assert_called_once_with(1)
        self.assertEqual(blob.read_bytes(), payload)
        self.assertEqual(info["raw_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(len(info["prior_attempts"]), 1)
        self.assertIn("IncompleteRead", info["prior_attempts"][0])
        checkpoint = root / "checkpoints" / (hashlib.sha256(url.encode()).hexdigest() + ".json")
        self.assertEqual(json.loads(checkpoint.read_text())["raw_sha256"], info["raw_sha256"])

        with patch.object(market_download, "urlopen", side_effect=AssertionError("cache miss")):
            cached, cached_info = market_download.fetch(root, url)
        self.assertEqual(cached, blob)
        self.assertEqual(cached_info["raw_sha256"], hashlib.sha256(payload).hexdigest())


  def test_derivatives_parser_preserves_contract_fields_and_marks_availability_unknown(self):
    with tempfile.TemporaryDirectory() as directory:
      tmp_path = Path(directory)
      source = tmp_path / "fo.csv"
      source.write_text(
          "TradDt,TckrSymb,FinInstrmId,XpryDt,StrkPric,OptnTp,OpnPric,HghPric,LwPric,ClsPric,SttlmPric,TtlTradgVol,OpnIntrst,ChngInOpnIntrst\n"
          "22-Nov-2026,NIFTY,12345,26-Nov-2026,25000,CE,100,125,90,110,112,1234,4567,89\n"
      )

      (row,) = parse_csv(source, "derivatives_daily")

      self.assertEqual(row["session"], "2026-11-22")
      self.assertEqual(row["key"], "12345|2026-11-22")
      self.assertEqual(row["symbol"], "NIFTY")
      self.assertIsNone(row["event_at"])
      self.assertIsNone(row["available_at"])
      self.assertEqual(row["availability"], "unknown")
      self.assertEqual(row["values"], {
          "close": 110.0,
          "contract_id": "12345",
          "expiry": "26-Nov-2026",
          "high": 125.0,
          "low": 90.0,
          "oi_change": 89.0,
          "open": 100.0,
          "open_interest": 4567.0,
          "option_type": "CE",
          "settlement": 112.0,
          "strike": 25000.0,
          "volume": 1234.0,
      })

      next_day = tmp_path / "fo-next-day.csv"
      next_day.write_text(source.read_text().replace("22-Nov-2026", "23-Nov-2026"))
      corrected = tmp_path / "fo-corrected.csv"
      corrected.write_text(source.read_text().replace(",110,112,", ",111,112,"))
      self.assertEqual(parse_csv(next_day, "derivatives_daily")[0]["key"], "12345|2026-11-23")
      self.assertEqual(parse_csv(corrected, "derivatives_daily")[0]["key"], row["key"])


  def test_quote_parser_requires_genuine_two_sided_depth_and_non_crossed_market(self):
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "quotes.csv"
        source.write_text(
            "timestamp,symbol,sequence,bid,ask,bid_qty,ask_qty\n"
            "2026-11-22T10:00:00+05:30,NIFTY,17,100,101,4,5\n"
        )
        (row,) = parse_csv(source, "quotes")
        self.assertEqual(row["key"], "NIFTY|2026-11-22T10:00:00+05:30|17")
        self.assertEqual(row["availability"], "unknown")

        source.write_text(source.read_text().replace(",100,101,", ",102,101,"))
        with self.assertRaisesRegex(ValueError, "invalid quote spread or size"):
            parse_csv(source, "quotes")

        source.write_text(
            "timestamp,symbol,sequence,bid,ask,bid_qty\n"
            "2026-11-22T10:00:00+05:30,NIFTY,17,100,101,4\n"
        )
        with self.assertRaisesRegex(ValueError, "requires bid and ask sizes"):
            parse_csv(source, "quotes")

  def test_pre_session_packet_and_harness_preparation_are_cutoff_safe(self):
    with tempfile.TemporaryDirectory() as directory:
        root, tmp = Path(directory) / "store", Path(directory)
        root.mkdir()
        before = tmp / "reliance.csv"
        before.write_text("pre-cutoff")
        market_store.ingest_batch(
            root, dataset="equity_daily", source="fixture", url="https://example.test/reliance.csv",
            raw_path=before, rows=[{
                "key": "reliance-2026-11-20", "session": "2026-11-20", "symbol": "RELIANCE",
                "event_at": "2026-11-20T15:30:00+05:30", "available_at": "2026-11-22T18:29:59.999999Z",
                "availability": "verified", "availability_basis": "synthetic publication time",
                "values": {"series": "EQ", "isin": "INE002A01018", "close_rupees": 1450.0,
                           "previous_close_rupees": 1440.0, "volume_shares": 2000},
            }], acquired_at="2026-11-22T18:30:00Z",
        )
        outcome = tmp / "monday-outcome.csv"
        outcome.write_text("post-cutoff-outcome")
        market_store.ingest_batch(
            root, dataset="equity_daily", source="fixture", url="https://example.test/monday.csv",
            raw_path=outcome, rows=[{
                "key": "reliance-2026-11-23", "session": "2026-11-23", "symbol": "RELIANCE",
                "event_at": "2026-11-23T15:30:00+05:30", "available_at": "2026-11-23T15:35:00+05:30",
                "availability": "verified", "availability_basis": "synthetic close availability",
                "values": {"series": "EQ", "isin": "INE002A01018", "close_rupees": 1490.0,
                           "previous_close_rupees": 1450.0, "volume_shares": 3000},
            }], acquired_at="2026-11-23T16:00:00+05:30", outcome_only=True,
        )

        evidence = market_evidence.packet(root)
        self.assertEqual(evidence["outcome_only_rows_excluded"], 1)
        self.assertEqual(len(evidence["channels"]["equity_daily"]), 1)
        self.assertEqual(evidence["channels"]["equity_daily"][0]["session"], "2026-11-20")
        self.assertEqual(evidence["max_available_at_utc"], "2026-11-22T18:29:59.999999Z")
        preparation = market_evidence.harness_preparation(evidence)
        self.assertEqual(len(preparation), 1)
        self.assertEqual(set(preparation[0]), {"available_at", "source", "text"})
        snap = Snapshot.model_validate({
            "case": "packet-test", "source": "historical", "provider": "synthetic fixture",
            "preparation": preparation, "symbol": "RELIANCE",
            "cutoff": "2026-11-23T10:00:00+05:30",
            "observations": [{"at": "2026-11-23T09:59:55+05:30", "bid": 144900, "ask": 145000,
                              "bid_qty": 5, "ask_qty": 6}],
        })
        self.assertEqual(snap.preparation, preparation)
