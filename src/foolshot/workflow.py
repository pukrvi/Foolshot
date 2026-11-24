import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .audit import DEFAULT_DB, ROOT, append, capture_hook, history, transaction
from .review import review
from .study import attempt, close_day, record_transfer


def main():
    parser = argparse.ArgumentParser(
        description="Foolshot private notebook and synthetic paper book"
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    cmds = parser.add_subparsers(dest="cmd", required=True)
    cmds.add_parser("hook")
    note = cmds.add_parser("note")
    note.add_argument("session")
    note.add_argument(
        "kind",
        choices=[
            "user_input",
            "question",
            "owner_decision",
            "lesson",
            "change_proposal",
        ],
    )
    note.add_argument("--id")
    note.add_argument(
        "--author-model", help="Exact release of the model that authored a note"
    )
    note.add_argument(
        "--owner", action="store_true", help="Note authored by Puneet Vishnawat"
    )
    log = cmds.add_parser("history")
    log.add_argument("prefix", nargs="?", default="")
    trade = cmds.add_parser("attempt")
    trade.add_argument("--key", required=True)
    trade.add_argument("--thesis", required=True)
    trade.add_argument(
        "--ticks", type=Path, default=ROOT / "tests/fixtures/dhan_stop_drill.json"
    )
    transfer = cmds.add_parser("record-transfer")
    transfer.add_argument("--day", type=date.fromisoformat, required=True)
    transfer.add_argument("--paise", type=int, required=True)
    transfer.add_argument("--reference", required=True)
    close = cmds.add_parser("close")
    inspect = cmds.add_parser("review")
    inspect.add_argument("period", choices=["daily", "weekly", "incident"])
    for cmd in [trade, close, inspect]:
        cmd.add_argument("--day", type=date.fromisoformat, required=True)
        cmd.add_argument("--review-with", choices=["codex", "claude"])
    args = parser.parse_args()
    try:
        if args.cmd == "hook":
            capture_hook(args.db, json.load(sys.stdin))
            return 0
        if args.cmd == "note":
            if args.session.startswith(("paper/", "review/")):
                raise ValueError("use a separate notebook session name")
            data = {"text": sys.stdin.read()}
            if args.kind in {"question", "lesson", "change_proposal"}:
                if bool(args.author_model) == bool(args.owner):
                    raise ValueError(
                        "identify the note author with --author-model RELEASE or --owner"
                    )
                if args.author_model:
                    from .routing import family_release

                    if not any(
                        family_release(client, tier, args.author_model)
                        for client in ("codex", "claude")
                        for tier in ("thinking", "operations")
                    ):
                        raise ValueError("an exact model release is required")
                    data["receipt"] = {
                        "release": args.author_model,
                        "basis": "author_declared",
                    }
                else:
                    data["owner_authored"] = True
            elif args.author_model:
                raise ValueError(
                    "use user_input or owner_decision only for the owner's input"
                )
            with transaction(args.db) as db:
                result = append(db, args.session, args.kind, data, args.id)
        elif args.cmd == "history":
            with transaction(args.db) as db:
                result = history(db, args.prefix)
        elif args.cmd == "attempt":
            result = attempt(
                args.db,
                args.day,
                args.key,
                args.thesis,
                json.loads(args.ticks.read_bytes()),
            )
            with transaction(args.db) as db:
                requests = [
                    r
                    for r in history(db, "paper/" + str(args.day), exact=True)
                    if r["kind"] == "review_requested"
                    and r["payload"]["postcheck"] == result["intent"] + "/post"
                ]
            if requests:
                result["incident_review"] = review(
                    args.db, args.day, "incident", args.review_with
                )
        elif args.cmd == "record-transfer":
            result = record_transfer(args.db, args.day, args.reference, args.paise)
        elif args.cmd == "close":
            result = close_day(args.db, args.day)
            review(args.db, args.day, "daily", args.review_with)
        else:
            result = review(args.db, args.day, args.period, args.review_with)
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
