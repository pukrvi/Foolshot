import unittest
from dataclasses import replace
from datetime import datetime
from unittest.mock import patch

import yaml

from foolshot.clock import IST
from foolshot.dhan import DhanError, depth_snapshot, fetch, preflight
from foolshot.paper_drill import LossRoom, drill, permitted_quantity
from foolshot.replay import ROOT
from foolshot.schemas import Settings


class DhanTests(unittest.TestCase):
    def setUp(self):
        self.profile = {"dhanClientId": "demo", "tokenValidity": "24/11/2026 17:00",
                        "activeSegment": "Equity, Derivative", "dataPlan": "Active"}
        self.data = {"profile": self.profile, "orders": [], "positions": []}
        self.settings = Settings.model_validate(yaml.safe_load((ROOT / "config/experiment.yaml").read_bytes()))

    def check_account(self):
        return preflight(datetime(2026, 11, 24, 9, tzinfo=IST), lambda k, _: self.data[k],
                         {"DHAN_CLIENT_ID": "demo", "DHAN_ACCESS_TOKEN": "test"})

    def test_preflight_flat_and_unresolved(self):
        self.assertEqual(self.check_account()["status"], "checks_passed")
        self.data.update(positions=[{"netQty": -2}], orders=[{"orderStatus": "UNKNOWN"}])
        self.assertEqual(self.check_account()["status"], "review_required")

    def test_account_failures(self):
        for field, value in [("tokenValidity", "23/11/2026 15:30"), ("dhanClientId", "other"),
                             ("activeSegment", "Derivative"), ("dataPlan", "Deactive")]:
            with self.subTest(field=field), patch.dict(self.profile, {field: value}), self.assertRaises(DhanError):
                self.check_account()

    def test_no_order_writes(self):
        with self.assertRaises(DhanError):
            fetch("super/orders", "test")

    def test_quote_and_missing_side(self):
        book = {"buy": [{"quantity": 2, "price": 499.95}], "sell": [{"quantity": 3, "price": 500}]}
        data = {"status": "success", "data": {"NSE_EQ": {"1": {
            "depth": book, "last_trade_time": "24/11/2026 09:45:00"}}}}
        self.assertEqual(depth_snapshot(data, 1)["bid_paise"], 49995)
        book["sell"][0]["quantity"] = 0
        with self.assertRaises(DhanError):
            depth_snapshot(data, 1)

    def test_stop_gap_and_missing_exit(self):
        ticks = [(1, 49995, 50000, 50, 50), (2, 49400, 49410, 50, 50)]
        self.assertEqual(drill(self.settings, ticks)[-1]["net_paise"], -13000)
        self.assertEqual(drill(self.settings, ticks[:1])[-1]["kind"], "unresolved_exit")
        self.assertEqual(drill(self.settings, [])[-1]["kind"], "unfilled")

    def test_remaining_risk_and_halts(self):
        room = LossRoom(1000000, 5000, 100000, 500000, 1, 0, False)
        def size(r):
            return permitted_quantity(self.settings, r, 50000, 49600, 50)
        self.assertEqual(size(room), 11)
        for change in [{"occupied": True}, {"attempts": 2}, {"consecutive_losses": 3},
                       {"weekly_remaining": 0}, {"study_remaining": -1}]:
            self.assertEqual(size(replace(room, **change)), 0)
