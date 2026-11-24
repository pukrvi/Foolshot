import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from foolshot.audit import ROOT, capture_hook, history, transaction
from foolshot.cohort import run
from foolshot.learning import run_case
from foolshot.study import attempt, close_day, load_settings, record_transfer, state

FIX = ROOT / "tests/fixtures/study"
LOSS = [[1, 49995, 50000, 100, 100], [2, 49400, 49405, 100, 100]]
GAIN = [[1, 49995, 50000, 100, 100], [2, 51000, 51005, 100, 100]]


class StudyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name)
        self.db = self.directory / "book.sqlite3"
        self.day = date(2026, 1, 15)

    def test_streak_across_days_retry_and_attempt_cap(self):
        result = attempt(self.db, self.day, "A", "gap drill", LOSS)
        self.assertEqual(attempt(self.db, self.day, "A", "gap drill", LOSS), result)
        attempt(self.db, self.day, "B", "second", LOSS)
        with self.assertRaisesRegex(ValueError, "attempt cap"):
            attempt(self.db, self.day, "C", "excess", LOSS)
        close_day(self.db, self.day)
        tomorrow = self.day + timedelta(days=1)
        attempt(self.db, tomorrow, "C", "third loss", LOSS)
        with self.assertRaisesRegex(ValueError, "under review"):
            attempt(self.db, tomorrow, "D", "blocked by streak", GAIN)
        with transaction(self.db) as db:
            self.assertIn(
                "three_consecutive_net_losses",
                history(db, "paper/")[-1]["payload"]["reasons"],
            )

    def test_ringfence_and_loss_recovery(self):
        attempt(self.db, self.day, "A", "up", GAIN)
        close = close_day(self.db, self.day)
        self.assertEqual(close["reserved_paise"], 19000)
        self.assertEqual(close["next_tradable_paise"], 10000000)
        tomorrow = self.day + timedelta(days=1)
        attempt(self.db, tomorrow, "B", "down", LOSS)
        close = close_day(self.db, tomorrow)
        self.assertEqual(close["reserved_paise"], 0)
        self.assertEqual(close["next_tradable_paise"], 9987000)
        self.assertEqual(close["total_reserved_paise"], 19000)

    def test_manual_reserve_transfer_is_not_pnl(self):
        attempt(self.db, self.day, "A", "gain", GAIN)
        close_day(self.db, self.day)
        for _ in range(2):
            record_transfer(self.db, self.day, "example", 10000)
        with transaction(self.db) as db:
            book = state(history(db, "paper/"), self.day, load_settings())
        self.assertEqual(
            (book["withdrawn"], book["reserve"], book["tradable"], book["daily"]),
            (10000, 9000, 10000000, 19000),
        )
        with self.assertRaises(ValueError):
            record_transfer(self.db, self.day, "excess", 9001)

    def test_absolute_daily_gap_stop_before_attempt_cap(self):
        gap = [LOSS[0], [2, 47000, 47005, 100, 100]]
        attempt(self.db, self.day, "A", "gap", gap)
        with self.assertRaisesRegex(ValueError, "under review"):
            attempt(self.db, self.day, "B", "retry after gap", GAIN)
        with transaction(self.db) as db:
            reason = history(db, "paper/")[-1]["payload"]["reasons"]
        self.assertIn("daily_loss_limit", reason)

    def test_prompt_verbatim_and_duplicate(self):
        raw = {
            "cwd": str(ROOT),
            "prompt": "  first line\nsecond ",
            "session_id": "s",
            "turn_id": "t",
        }
        capture_hook(self.db, raw)
        capture_hook(self.db, raw)
        with transaction(self.db) as db:
            rows = history(db)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["payload"]["text"], raw["prompt"])

    def fake_model(self, client, prompt):
        spec = json.loads(prompt)
        if spec["schema"]["title"] == "Decision":
            self.assertNotIn("outcome_tape", spec["prompt"]["context"]["snapshot"])
            return json.dumps(
                {
                    "action": "long",
                    "hypothesis": "test momentum",
                    "evidence": [0, 1],
                    "invalidation": "bid fades",
                    "probability_up_pct": 55,
                    "limit": 50000,
                    "stop": 49600,
                    "target": 51000,
                }
            )
        if spec["schema"]["title"] == "TrialVerdict":
            event = spec["prompt"]["later_evidence"][0]
            return json.dumps(
                {
                    "verdict": "inconclusive",
                    "evidence_ids": [event["id"]],
                    "interpretation": "small sample",
                    "competing_explanation": "price path",
                    "next_experiment": "test later dates",
                }
            )
        evidence = spec["prompt"]["events"]
        if spec["schema"]["title"] == "OperationsReview":
            return json.dumps(
                {
                    "right": "size checked",
                    "wrong_or_unknown": "unknown",
                    "next_check": "check depth",
                    "evidence_ids": [evidence[0]["id"]],
                }
            )
        return json.dumps(
            {
                "right": "size constrained",
                "wrong_or_unknown": "signal uncertain",
                "evidence_ids": [evidence[0]["id"]],
                "next_check": "compare spreads",
                "hypothesis": "spread matters",
                "test_on_later_data": "next week",
                "rejection_criterion": "no net gain",
                "proposed_harness_change": "log spread",
            }
        )

    def test_paired_study_feedback_and_repeatability(self):
        out = run(
            FIX / "manifest.json",
            self.directory,
            "codex",
            "gpt-6.2-astra",
            self.fake_model,
        )
        original = out.read_bytes()
        from foolshot.trials import challenge

        tested = challenge(self.directory, date(2026, 1, 19), "codex", self.fake_model)
        self.assertEqual(tested["value"]["verdict"], "inconclusive")
        with transaction(self.directory / "adaptive.sqlite3") as db:
            rows = history(db)
            contexts = [r["payload"] for r in rows if r["kind"] == "decision_context"]
            self.assertTrue(any("reflection" in m for m in contexts[-1]["memory"]))
            self.assertTrue(
                any(
                    r["kind"] == "reflection" and r["payload"]["period"] == "weekly"
                    for r in rows
                )
            )
        with transaction(self.directory / "frozen.sqlite3") as db:
            self.assertTrue(
                all(
                    not r["payload"]["memory"]
                    for r in history(db)
                    if r["kind"] == "decision_context"
                )
            )
        self.assertEqual(
            run(
                FIX / "manifest.json",
                self.directory,
                "codex",
                "gpt-6.2-astra",
                lambda *_: self.fail("duplicate model call"),
            ).read_bytes(),
            original,
        )

    def test_archived_quote_import_and_paired_replay(self):
        from datetime import time
        from foolshot.historical import prepare

        tape = self.directory / "sample.csv"
        rows = ["at,symbol,bid,ask,bid_qty,ask_qty"]
        for stamp, bid in [("09:59:59", 49990), ("10:00:00", 49995),
                           ("10:00:01", 49995), ("15:05:00", 51000)]:
            rows.append(f"{self.day}T{stamp}+05:30,DEMO,{bid},{bid+5},100,100")
        tape.write_text("\n".join(rows))
        args = (tape, self.directory, self.day, "DEMO", "test feed", time(10))
        manifest = prepare(*args)
        inputs = manifest.parent
        snapshot = json.loads((inputs / "snapshot.json").read_bytes())
        self.assertEqual([q["bid"] for q in snapshot["observations"]], [49990, 49995])
        result = run(manifest, self.directory, "codex", "gpt-6.2-astra", self.fake_model)
        self.assertEqual(result.read_text().count(",historical,"), 2)
        self.assertEqual(prepare(*args), manifest)
        with self.assertRaisesRegex(ValueError, "decision unavailable"):
            run_case(self.db, inputs / "snapshot.json", inputs / "missing.json",
                     "codex", lambda *_: "{}")
        evidence = self.directory / "news.json"
        evidence.write_text(json.dumps([{"source": "test", "text": "late update",
                                         "available_at": f"{self.day}T09:00:00+05:30"}]))
        with self.assertRaisesRegex(ValueError, "must precede"):
            prepare(*args, research=evidence)
        tape.write_text(tape.read_text().replace("51000", "50995"))
        with self.assertRaisesRegex(ValueError, "registered inputs differ"):
            prepare(*args)

    def test_model_decision_durable_before_outcome_read(self):
        before = FIX / "synthetic-2026-01-15.json"
        with self.assertRaises(FileNotFoundError):
            run_case(
                self.db, before, self.directory / "missing", "claude", self.fake_model
            )
        with transaction(self.db) as db:
            self.assertEqual(history(db)[-1]["kind"], "model_response")
        tape = FIX / "synthetic-2026-01-15-outcome.json"
        result = run_case(
            self.db, before, tape, "claude", lambda *_: self.fail("called again")
        )
        self.assertEqual(result["result"]["net_paise"], -13000)

    def test_malformed_decision_and_unknown_evidence(self):
        before = FIX / "synthetic-2026-01-15.json"
        result = run_case(
            self.db,
            before,
            FIX / "synthetic-2026-01-15-outcome.json",
            "codex",
            lambda *_: "garbage",
        )
        self.assertEqual(result["result"]["outcome"], "invalid_response_pass")
