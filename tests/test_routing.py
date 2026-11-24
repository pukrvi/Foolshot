import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from foolshot.audit import append, history, transaction
from foolshot.review import dispatch, parse_receipt
from foolshot.routing import route, selections


class RoutingTests(unittest.TestCase):
    def test_policy_and_latest_visible_version(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.dict("os.environ", {"CODEX_HOME": temp}),
        ):
            models = [
                {"slug": s, "visibility": v}
                for s, v in [
                    ("gpt-6.2-astra", "list"),
                    ("gpt-6.10-astra", "list"),
                    ("gpt-7-astra", "hide"),
                    ("gpt-6.2-sol", "list"),
                ]
            ]
            (Path(temp) / "models_cache.json").write_text(
                json.dumps({"models": models})
            )
            self.assertEqual(selections("codex")["thinking"], "gpt-6.10-astra")
            with self.assertRaises(ValueError):
                selections("codex", "gpt-6.2-sol")
            with transaction(Path(temp) / "audit.db") as db:
                for task in ("decision", "incident", "weekly", "trial"):
                    self.assertEqual(
                        route(db, "claude", task)["requested_model"], "fable"
                    )
                for task in ("position", "daily"):
                    self.assertEqual(
                        route(db, "claude", task)["requested_model"], "opus"
                    )

    def test_claude_resolution_and_pin(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "audit.db"
            with transaction(path) as db:
                selected = route(db, "claude", "decision")
            value = parse_receipt(
                "claude",
                json.dumps({"result": "ok", "modelUsage": {"claude-fable-5-2": {}}}),
                "fable",
            )
            with patch("foolshot.review.ask_model", return_value=value) as call:
                dispatch(path, selected, "first")
                dispatch(path, selected, "second")
                self.assertEqual(
                    [c.args[2] for c in call.call_args_list],
                    ["fable", "claude-fable-5-2"],
                )
            with self.assertRaises(ValueError):
                parse_receipt(
                    "claude",
                    '{"result":"ok","modelUsage":{"claude-opus-5-5":{}}}',
                    "fable",
                )

    def test_actor_and_trade_lineage(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            transaction(Path(temp) / "audit.db") as db,
        ):
            append(db, "chat", "user_input", {"text": "steer"}, "steer")
            append(
                db,
                "cases/x",
                "model_response",
                {
                    "receipt": {
                        "release": "gpt-6.2-astra",
                        "basis": "explicit_cli_selection",
                    }
                },
                "d",
            )
            append(db, "paper/day", "intent", {"specification": {"decision": "d"}}, "i")
            append(db, "paper/day", "paper_entry", {"intent": "i"}, "fill")
            user, _, _, fill = history(db)
            self.assertEqual(user["actor_name"], "Puneet Vishnawat")
            self.assertEqual(
                (fill["actor_name"], fill["decision_id"], fill["decision_release"]),
                ("Foolshot", "d", "gpt-6.2-astra"),
            )
            self.assertTrue(fill["recorded"].endswith("+00:00"))

    def test_codex_usage_and_evidence(self):
        stdout = '{"type":"item.completed","item":{"type":"agent_message","text":"ok"}}\n{"type":"turn.completed","usage":{"input_tokens":71}}'
        msg, meta = parse_receipt("codex", stdout, "gpt-6.2-sol")
        self.assertEqual(
            (msg, meta["basis"], meta["usage"]["input_tokens"]),
            ("ok", "explicit_cli_selection", 71),
        )
