# Foolshot

Foolshot studies whether an AI can improve its later decisions by learning from its own trading record. Start with the [study protocol](docs/research/study-protocol.md) and the [adaptive cohort runner](#start-here-for-the-adaptive-experiment). The lower-level commands below exercise individual broker and simulator components.

## Run the fixture

From this folder, use Python 3.12 and uv.

```sh
uv venv --python 3.12
uv pip sync requirements.lock
./scripts/replay
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The default session reads three synthetic INR quotes for DEMO. All prices and limits use integer paise. The JSON result includes mode, run ID, status, unique quote count and duplicate count. The CLI exits nonzero on blocked or failed runs. Use `./scripts/replay --help` for input paths, date and journal overrides.

## Inspect a run

```sh
sqlite3 data/runs/foolshot.sqlite3 'SELECT id, manifest FROM runs;'
sqlite3 data/runs/foolshot.sqlite3 'SELECT run_id, seq, body FROM events ORDER BY run_id, seq;'
```

The journal stores input bytes by SHA-256, source code hashes, normalized UTC timestamps and the final outcome. A transaction commits the whole fixture or rolls it back. Replaying identical inputs on the same code verifies the stored events without adding rows. A blank quote file represents zero observations. Only an explicitly closed calendar date accepts that file as a holiday. The checked-in calendar is invented test data.

## Build status

| Available | Next |
|---|---|
| Validated limits, dated instrument master, fixture calendar, session clock | Licensed data contract, reviewed exchange calendar, master validity periods |
| Receipt-ordered, tick-validated quote playback and conflict detection | Completed minute bars, feed freshness and point-in-time snapshots |
| Durable run manifests, raw fixture inputs and replay checks | Baseline, model decisions, risk enforcement, paper fills, ledger and scorecards |

The Python dependencies are pinned in requirements.lock. The full multi-platform uv lock is pending registry access. The default fixture replay runs offline. The weekly target, draft risk limits and 90-day study apply to later phases. See the [implementation plan](Foolshot_Implementation_Plan.md) and [project dossier](Foolshot_Project_Dossier.md).

## Dhan integration

DhanHQ v2 is the broker API. Both coding clients can run the same local commands. Register the hosted MCP separately in each interactive client. Registration changes the client's settings. Complete the broker consent screen when prompted.

```sh
./scripts/dhan rehearsal
./scripts/dhan mcp-claude
./scripts/dhan mcp-codex
```

For API reads, provide DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN to the local worker through its environment. Keep credentials outside the repo and model prompts. Then run the following commands, supplying an NSE equity security ID from Dhan's current instrument list for the second command.

```sh
./scripts/dhan preflight
./scripts/dhan quote "$NSE_SECURITY_ID"
```

Preflight checks account identity, token expiry, equity activation, data subscription status, open positions and outstanding orders. Unknown order states require review. A pass applies only to these reads. Depth capture stores bid, ask, local receipt time and Dhan's last **trade** time. That timestamp cannot establish when the order book last changed. SQLite retains redacted results in data/runs/dhan.sqlite3. Dhan's interactive MCP has its own permissions and sits outside the local worker's controls.

For an always-on Linux host, the user-level systemd units under ops/systemd schedule the account preflight at 08:45 IST each day. They expect the checkout at ~/Foolshot and credentials in ~/.config/foolshot/dhan.env (mode 0600). Install the two units in ~/.config/systemd/user/, run systemctl --user daemon-reload, then systemctl --user enable --now foolshot-dhan.timer. The user manager must remain running. The timer also checks on market holidays. It is an account check only.

The rehearsal exercises a single synthetic long position with a fixed fee/slippage allowance. It checks sizing, available loss room and attempt limits, then simulates an exit at observed bid depth. Live stop placement, partial-fill protection, kill-switch execution, continuous ledger reconciliation, external alerts, unattended model sessions and live scheduling remain open work. Broker onboarding must establish which execution route this account can use.

[Dhan authentication](https://dhanhq.co/docs/v2/authentication/) · [Dhan market depth](https://dhanhq.co/docs/v2/market-quote/) · [Dhan MCP](https://docs.dhanhq.co/mcp/) · [Dhan Super Orders](https://dhanhq.co/docs/v2/super-order/)

## Start here for the adaptive experiment

[Research protocol](docs/research/study-protocol.md) · [Owner decisions and verbatim alignment](docs/decisions/Foolshot_Alignment_Log.md) · [Allocation research](offline-research/design-notes/paper-baseline.md)

The main entry point for Codex and Claude Code is the paired cohort runner. It runs the selected model in two paper books, gives prior reflections to the adaptive arm, then writes paired_daily.csv and study_report.md. The supplied three-session cohort uses invented prices. It can make multiple billable model calls. Choose the authenticated client. The router selects model releases by task.

```sh
./scripts/cohort tests/fixtures/study/manifest.json data/private/pilot-codex --client codex
./scripts/cohort tests/fixtures/study/manifest.json data/private/pilot-claude --client claude
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Use separate study directories for independent model versions and policy changes. Repeating identical runs reuses stored responses. The dated fixture roster drives automatic position, incident, daily and weekly reviews within a cohort. It can be invoked as a batch; the existing Linux wall-clock timer runs only Dhan preflight.

| Directory | Purpose |
|---|---|
| docs/decisions, docs/research | Alignment record, research question, trial methods and publication plan |
| src/foolshot, scripts | Shared implementation and command-line entry points |
| tests/fixtures/study | Split pre-decision observations and post-decision tapes |
| offline-research | Source register, original plans and reviewed evidence |
| ops/hooks, ops/systemd | Prompt capture configuration and host service templates |
| data/private | Local SQLite records, cohort manifests inside each database, reports and raw model responses; excluded from Git |
| data/runs | Older replay and Dhan read-only journals, retained at their original paths |

**Project memory.** The project Claude settings register the prompt hook. For Codex CLI in a trusted Git checkout, merge ops/hooks/codex-hooks.json into .codex/hooks.json and trust the hook through the client. These hooks apply to clients that load the project configuration. Current chat history was seeded explicitly. When hooks are unavailable, use scripts/study note with stdin and a stable message ID. To inspect records use scripts/study history chat/ or scripts/study --db data/private/pilot-codex/adaptive.sqlite3 history dream/. Capture occurs when the client supplies the prompt; earlier unrelated conversations require an explicit import.

**Steering a study.** Record owner decisions using scripts/study --db PATH note chat/owner owner_decision and provide the text on stdin. The adaptive arm can use owner decisions recorded by its decision cutoff. A study directory has separate arm databases; record input in the relevant book. A historical synthetic replay cannot use owner decisions made after that historical cutoff.

**Research limitations.** The fixed allowance in paper fills is illustrative. An unresolved open position blocks the next session. Three successive losses across sessions pause entries pending review. The current paper book keeps that hold in force; resumption needs a new documented trial. The transfer of real profits is manual. There is no active real-money order worker.

After a subsequent matched week closes, the AI challenges the previous weekly hypothesis against later data and saves its verdict under trials/. To record a hypothetical manual transfer after closing a paper session, use scripts/study --db PATH record-transfer --day YYYY-MM-DD --paise AMOUNT --reference UNIQUE_ID. This moves an amount out of the paper reserve and preserves trading P&L. It never initiates a bank transfer.

## Model and actor audit

Inspect scripts/study --db PATH history for actor_type, actor_name, model_release, identity_basis, decision_id, decision_actor and decision_release. history_with_actor exposes the same fields in SQLite. Legacy replay and Dhan journals use events_with_actor. Timestamps distinguish UTC recording from the simulated quote time when known. Human inputs use Puneet Vishnawat. For a manually recorded lesson, question or change proposal, pass --owner or --author-model followed by the exact release.

scripts/cohort selects Astra/Sol from the Codex catalog and Fable/Opus via Claude Code product aliases. An explicit --model selects a numbered thinking release. Model responses keep structured usage where the CLI provides it. Codex can omit the served model in its JSON stream; identity_basis then records explicit_cli_selection. Claude requires a matching numbered model usage receipt. Existing pre-routing cohorts remain historical; use a fresh directory for the two-tier policy.
