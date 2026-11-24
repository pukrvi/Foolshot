import json
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import closing
from datetime import date, datetime
from pathlib import Path

from foolshot.clock import hours_for, phase
from foolshot.replay import ROOT, replay
from foolshot.schemas import Calendar


class FoundationTests(unittest.TestCase):
    day = date(2026, 1, 12)

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.temp = Path(temp.name)
        self.db = self.temp / "run.sqlite3"
        self.paths = {"settings": ROOT / "config/experiment.yaml",
                      "calendar": ROOT / "config/calendar/fixture.json",
                      "instruments": ROOT / "tests/fixtures/instruments.json",
                      "quotes": ROOT / "tests/fixtures/quotes.jsonl"}

    def replace(self, key, content):
        self.paths[key] = self.temp / key
        self.paths[key].write_text(content)

    def run_day(self, day=None):
        return replay(day or self.day, self.paths, self.db)

    def test_cli_restart_and_deterministic_evidence(self):
        args = [str(ROOT / "scripts/replay"), "--db", str(self.db)]
        first = subprocess.check_output(args)
        self.assertEqual(first, subprocess.check_output(args))
        with closing(sqlite3.connect(self.db)) as db:
            rows = db.execute("SELECT body FROM events ORDER BY seq").fetchall()
            ids = [json.loads(row[0])["quote"]["id"] for row in rows[1:-1]]
            self.assertEqual(ids, ["q1", "q2", "q3"])
            self.assertEqual(db.execute("SELECT count(*) FROM artifacts").fetchone(), (4,))
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("DELETE FROM events")

    def test_clock_boundaries_and_short_session(self):
        cal = Calendar.model_validate_json(self.paths["calendar"].read_bytes())
        for day, at, expected in [
            (12, "09:44:59", "warmup"), (12, "09:45:00", "evaluation"),
            (12, "14:30:00", "observe_only"), (12, "15:30:00", "closed"),
            (14, "18:29:59", "warmup"), (14, "18:30:00", "observe_only"),
        ]:
            with self.subTest(day=day, at=at):
                current = date(2026, 1, day)
                stamp = datetime.fromisoformat(f"{current}T{at}+05:30")
                self.assertEqual(phase(stamp, current, hours_for(cal, current)), expected)

    def test_missing_date_and_holiday_are_distinct(self):
        self.replace("quotes", "")
        self.assertEqual(self.run_day(date(2026, 1, 13))["status"], "holiday")
        self.assertEqual(self.run_day(date(2026, 1, 15))["status"], "blocked")
        self.assertEqual(self.run_day()["status"], "blocked")

    def test_duplicate_and_conflict(self):
        original = self.paths["quotes"].read_text()
        line = original.splitlines()[0]
        self.replace("quotes", original + line)
        self.assertEqual(self.run_day()["duplicate_rows"], 1)
        self.replace("quotes", original + line.replace("49995", "49990"))
        self.assertIn("conflicting", self.run_day()["reason"])

    def test_missing_input_is_journaled(self):
        self.paths["calendar"] = self.temp / "absent.json"
        result = self.run_day()
        self.assertEqual(result["status"], "blocked")
        with closing(sqlite3.connect(self.db)) as db:
            self.assertIn("missing inputs: calendar", db.execute("SELECT body FROM events").fetchone()[0])

    def test_bad_quotes(self):
        original = json.loads(self.paths["quotes"].read_text().splitlines()[0])
        for change in [{"ask": 50006}, {"bid": 50010}, {"symbol": "UNKNOWN"}, {"ask": 50005.5},
                       {"received": "2026-01-12T03:44:59Z"}, {"exchange": "2026-01-12T03:45:00"}]:
            with self.subTest(change=change):
                self.replace("quotes", json.dumps(original | change))
                self.assertEqual(self.run_day()["status"], "blocked")

    def test_invalid_settings_or_future_master(self):
        original = self.paths["settings"].read_text()
        for settings in [original.replace("replay", "live"), original.replace("12500", "0")]:
            self.replace("settings", settings)
            self.assertEqual(self.run_day()["status"], "blocked")
        self.replace("settings", original)
        self.replace("instruments", self.paths["instruments"].read_text().replace("01-12", "01-13"))
        self.assertIn("future", self.run_day()["reason"])

    def test_distinct_inputs_get_distinct_runs(self):
        first = self.run_day()
        self.replace("quotes", self.paths["quotes"].read_text() + "\n")
        self.assertNotEqual(self.run_day()["run_id"], first["run_id"])


if __name__ == "__main__":
    unittest.main()
