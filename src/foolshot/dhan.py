"""Dhan account checks. Persist summaries only; broker payloads stay in memory."""
import json
import os
from decimal import Decimal, InvalidOperation
from datetime import datetime
from http.client import HTTPException
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .clock import IST


class DhanError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


READ_PATHS = {"profile", "positions", "orders"}


def fetch(path, token, *, security_id=None, client=None):
    market = path == "marketfeed/quote" and type(security_id) is int and security_id > 0 and client
    if path not in READ_PATHS and not market:
        raise DhanError("unsupported account check")
    headers = {"access-token": token}
    body = None
    if market:
        headers.update({"client-id": client, "Content-Type": "application/json"})
        body = json.dumps({"NSE_EQ": [security_id]}).encode()
    request = Request(f"https://api.dhan.co/v2/{path}", data=body, headers=headers)
    try:
        with build_opener(NoRedirect()).open(request, timeout=10) as response:
            raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise DhanError("response exceeds size limit")
            return json.loads(raw, parse_float=Decimal)
    except HTTPError as exc:
        raise DhanError(f"{path}: HTTP {exc.code}") from None
    except (OSError, ValueError, HTTPException) as exc:
        raise DhanError(f"{path}: {type(exc).__name__}") from None


def depth_snapshot(payload, security_id):
    try:
        if payload["status"] != "success":
            raise ValueError()
        quote = payload["data"]["NSE_EQ"][str(security_id)]
        prices = {}
        for side in ("buy", "sell"):
            levels = []
            for row in quote["depth"][side]:
                qty = row["quantity"]
                if type(qty) is not int or qty < 0:
                    raise ValueError()
                if qty == 0:
                    continue
                paise = Decimal(str(row["price"])) * 100
                if not paise.is_finite() or paise <= 0 or paise != paise.to_integral_value():
                    raise ValueError()
                levels.append(int(paise))
            prices[side] = (max if side == "buy" else min)(levels)
        if prices["buy"] > prices["sell"]:
            raise ValueError()
        traded = datetime.strptime(quote["last_trade_time"], "%d/%m/%Y %H:%M:%S").replace(tzinfo=IST)
    except (KeyError, IndexError, TypeError, ValueError, InvalidOperation):
        raise DhanError("invalid or unavailable Dhan quote depth") from None
    return {"security_id": security_id, "bid_paise": prices["buy"], "ask_paise": prices["sell"],
            "last_trade_time": traded.isoformat()}


def preflight(now, reader=fetch, environ=None):
    env = os.environ if environ is None else environ
    token, client = env.get("DHAN_ACCESS_TOKEN"), env.get("DHAN_CLIENT_ID")
    if not token or not client:
        raise DhanError("Dhan credentials unavailable")
    profile = reader("profile", token)
    if not isinstance(profile, dict) or profile.get("dhanClientId") != client:
        raise DhanError("Dhan profile identity mismatch")
    try:
        expiry = datetime.strptime(profile["tokenValidity"], "%d/%m/%Y %H:%M").replace(tzinfo=IST)
        equity = "equity" in {v.strip().lower() for v in profile["activeSegment"].split(",")}
    except (ValueError, TypeError, KeyError, AttributeError):
        raise DhanError("unrecognized Dhan profile format") from None
    if expiry <= now:
        raise DhanError("expired Dhan token")
    if not equity or profile.get("dataPlan") != "Active":
        raise DhanError("equity segment or data subscription unavailable")
    positions = reader("positions", token)
    orders = reader("orders", token)
    if not isinstance(positions, list) or not isinstance(orders, list):
        raise DhanError("unrecognized Dhan account response")
    for row in positions:
        if not isinstance(row, dict) or type(row.get("netQty")) is not int:
            raise DhanError("invalid position quantity")
    for row in orders:
        if not isinstance(row, dict) or not isinstance(row.get("orderStatus"), str):
            raise DhanError("invalid order status")
    open_positions = sum(p["netQty"] != 0 for p in positions)
    terminal = {"TRADED", "REJECTED", "CANCELLED", "EXPIRED"}
    pending = sum(o["orderStatus"] not in terminal for o in orders)
    return {"status": "review_required" if open_positions or pending else "checks_passed",
            "open_positions": open_positions, "nonterminal_orders": pending,
            "token_expires": expiry.isoformat()}


def main():
    from .journal import record
    from .replay import ROOT
    from datetime import timezone

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--quote", type=int, metavar="NSE_SECURITY_ID")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    manifest = {"schema": 1, "broker": "dhan", "mode": "depth_snapshot" if args.quote is not None else "account_preflight",
                "checked_at": now.isoformat(), "date": now.astimezone(IST).date().isoformat(),
                "inputs": {}}
    try:
        if args.quote is None:
            result = preflight(now)
        else:
            token = os.getenv("DHAN_ACCESS_TOKEN")
            client = os.getenv("DHAN_CLIENT_ID")
            if not token or not client:
                raise DhanError("Dhan credentials unavailable")
            payload = fetch("marketfeed/quote", token, security_id=args.quote, client=client)
            received = datetime.now(timezone.utc)
            result = {"status": "observed", "received": received.isoformat(),
                      **depth_snapshot(payload, args.quote)}
    except DhanError as exc:
        result = {"status": "blocked", "reason": str(exc)}
    run_id = record(ROOT / "data/runs/dhan.sqlite3", manifest, [result], {})
    print(json.dumps({"run_id": run_id, **manifest, **result}))
    return int(result["status"] not in {"checks_passed", "observed"})


if __name__ == "__main__":
    raise SystemExit(main())
