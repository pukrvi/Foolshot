# X India sweep — second Foolshot research pass

**Sweep run:** 22 November 2026, ~16:50–18:00 IST, on the signed-in X session (`@unhype.ai`) in Safari. **Status:** Tier 1–4 and the new variants are run and logged; journey threads are saved verbatim; repo decisions are recorded. Open questions are listed at the end.

This folder is deliberately separate from `offline-research/` so the first collection stays untouched. Everything here was produced by this sweep except `QUERIES.md` and `tools/xgrab.sh`, which were the starting kit and have been extended in place.

## What the sweep covered

- **33 logged X queries.** 25 from `QUERIES.md` (Tier 1–4: discovery, evidence, tooling, author follow-ups) plus 8 new variants added during the sweep. Every query has a row with its capture count in [`notes/search-log.md`](notes/search-log.md). All queries ran on the **Latest** tab, one probe on Top. The 33 queries rendered 396 post entries in total; 196 unique posts are indexed in [`snapshots/_all-search-posts.json`](snapshots/_all-search-posts.json) for the later runs, with earlier queries' pages kept in `snapshots/search/`.
- **Author coverage.** The six already-covered authors were checked for follow-ups with `from:` queries. New material came from @pranjalsoni_ (a second live run), @hb_stocks (new NSE/Claude fundamental-analysis series), and new authors documenting live or paper runs (@dharmikgohil_, @ShyamdasMallya, @kirubaakaran, @Aashish10_03, @AKtrader1108, @piyushchaudhry, @Logesh11667187).
- **Regulatory window.** The sweep landed three days after NSE Circular 58/2026 on static IPs for retail algos, so the circular and the market's reaction are captured as first-class findings.
- **Repos.** Seven GitHub repos were surfaced, checked against the existing register, and decided; two useful MIT repos were downloaded. See [`repos/INDEX.md`](repos/INDEX.md).

## New findings (what matters for Foolshot)

1. **NSE Circular 58/2026 (20 Nov 2026) changes the execution setup.** Static IP access is now restricted to "tech-savvy" retail clients who code their own algos; brokers must collect a written undertaking; third-party algo providers cannot hand static IPs to retail clients; clients waive the exchange grievance route for losses caused by algo logic; providers face empanelment action. For a Dhan-primary API experiment this is a launch blocker to be satisfied, not a research note. Sources and flags: learning R1, plus @DevMagg, @algotradingdesk, @abhip_me, @subuonelifee, @thesanjay15, @REDBOXINDIA, @Alphaalgo7 threads in [`snapshots/posts/`](snapshots/posts/).
2. **A second @pranjalsoni_ live run failed forward in public (3–6 Nov).** Documented verbatim in [`threads/pranjalsoni-second-run.md`](threads/pranjalsoni-second-run.md): IP change blocked an exit and the broker closed the position; the author moved to a fixed-IP Mumbai server; a stale-holiday-check bug switched paper trading off at 09:16 on a normal Friday; he overrode his own no-trade rule ("use the margin") and lost; a 1-minute scalping test showed zero edge before costs; the account was reported down ~1.6% over five days. This is the single richest operational case in the sweep.
3. **Two new public journey threads.** [`threads/dharmikgohil-claude-nifty-paper.md`](threads/dharmikgohil-claude-nifty-paper.md) — Claude paper-trading ₹1,00,000 of NIFTY options, retest entry recovered a −₹9,204 stop-out for +₹10,403, then "trade more" gave it all back and a 13-minutes-to-expiry lottery option expired worthless. [`threads/shyamdas-mallya-autonomous-bot.md`](threads/shyamdas-mallya-autonomous-bot.md) — a fully autonomous NSE bot with ₹91k live equities on Dhan and ₹1.64L on Zerodha options, 15+ production bugs, no P&L published.
4. **Dhan now has an agent-native surface.** Dhan MCP, Dhan Skills and Dhan Cloud (official Dhan material) plus a 6-step Dhan-MCP workflow from @kirubaakaran. Relevant to the primary broker; not independently tested here. Learning R10.
5. **NSE runs a free official MCP server.** 36 tools, no API key, live data ~1–3 minutes delayed, five years of EOD, cash market only, no F&O or intraday candles. A plausible research-data input; not an execution feed. Learning R36.
6. **Two MIT repos worth adopting patterns from.** [`repos/raiaashish-code/bazaar-trader-skill/`](repos/raiaashish-code/bazaar-trader-skill/) gives Foolshot a ready IST clock/holiday table, honest-fill model and the full NSE charge stack, plus deterministic risk/sizing gates and a human-consent ticket. [`repos/LogeshR15/screener-mcp/`](repos/LogeshR15/screener-mcp/) is a 30-tool Indian research MCP (Screener.in + NSE announcements/bulk deals/PIT filings + local portfolio). Learning R15–R20, R37.
7. **Broker operational detail.** Kite MCP sessions reset daily (Zerodha says a fix is coming) and Kite MCP has downtime/auth reports (R7–R9); Dhan API historical data was used for 2-year 1-minute backtests (archived Shivansh thread); Dhan's new MCP/Skills/Cloud are in R10; order prices must be tick-rounded (R10b).
8. **A production-notes file that must not be copied but should be read.** `javajack/skill-algotrader` has no license, but its `KNOWLEDGE.md`/`NUANCES.md` document tick-size rejects, naked-stop cancel-then-place failures, startup reconciliation, WebSocket degradation and backtest-live divergence. Paraphrased in learning R11–R14; no local copy. See [`repos/INDEX.md`](repos/INDEX.md).

## Duplicates skipped (already known)

- **Shivansh:** the five archived sessions and their P&L were not re-collected. His recent posts are Meta-ads updates, not trading, so nothing new was saved (Q21).
- **Pranjal, first week:** the archived +₹4,250 week, the 16 failure paths and the 86%-losing-weeks audit are not repeated. The new second run is saved separately.
- **Haseeb:** the archived NSE-data step is not repeated; only his new Nov 18 Claude fundamental-analyst series and the Sheets follow-ups are logged (R35, R38).
- **Repos:** no repo from the earlier register was re-downloaded; `marketcalls/openalgo` (kept earlier) only gained a new release note (R2). None of the 16 earlier rejects was reopened.
- **Strategy notes:** the archived strategies (expiry option buying, mechanical replays, capped-risk selling, BTC 20/50, ETH screening, insider-purchase events) were not re-logged. This sweep's new lessons live in `notes/learning.md` only.

## Where the artifacts are

| Path | What it holds |
|---|---|
| [`QUERIES.md`](QUERIES.md) | The 25 starting queries, the operator cheat sheet, and the 22 Nov additions: 8 variants that worked/what didn't, 20 ready-to-run variants, and the vocabulary that paid off. |
| [`notes/search-log.md`](notes/search-log.md) | 33 rows: exact query, tab, captured-post count, error flag, what it yielded, plus method and rate-limit notes. |
| [`notes/learning.md`](notes/learning.md) | 39 rows across regulatory, broker, execution/risk and strategy lessons; flags for sizing, stops, costs, reconciliation, broker quirks, SEBI/NSE rules; a "what changes for Foolshot" summary and a rejected-claims list. |
| [`threads/pranjalsoni-second-run.md`](threads/pranjalsoni-second-run.md) | Verbatim second live run, 3–6 Nov 2026, replies included, Notes below. |
| [`threads/dharmikgohil-claude-nifty-paper.md`](threads/dharmikgohil-claude-nifty-paper.md) | Verbatim paper-trading thread, 3 June 2026, with Notes. |
| [`threads/shyamdas-mallya-autonomous-bot.md`](threads/shyamdas-mallya-autonomous-bot.md) | Verbatim root post and replies, 26 March 2026, with Notes and the missing-series caveat. |
| [`repos/INDEX.md`](repos/INDEX.md) | Seven upstream repos plus linked services: decision, license, file inspected, reason, discovery source. Two MIT repos retained offline. |
| [`repos/raiaashish-code/bazaar-trader-skill/`](repos/raiaashish-code/bazaar-trader-skill/) · [`repos/LogeshR15/screener-mcp/`](repos/LogeshR15/screener-mcp/) | Offline copies (`.git` removed), with LICENSE and README. |
| [`snapshots/search/`](snapshots/search/) | 33 query snapshots (`qNN.txt`, plus JSON for q13–q33) with query, URL, tab, error flag and count in the header, then the captured page text. |
| [`snapshots/posts/`](snapshots/posts/) | Per-post captures (`tree.txt` AX dump, `thread.txt` article text, `posts.json`). |
| [`snapshots/mirrors/`](snapshots/mirrors/) | 12 full-text mirror copies for long posts whose X page truncates. |
| [`snapshots/_all-search-posts.json`](snapshots/_all-search-posts.json) · [`snapshots/_fulltexts.json`](snapshots/_fulltexts.json) | Aggregated candidate index (196 unique posts across searches) and full article texts for re-use/writing. |
| [`tools/xgrab.sh`](tools/xgrab.sh) · [`tools/capture-notes.md`](tools/capture-notes.md) | Legacy clipboard script (now blocked in this environment) and the working capture recipe from this sweep. |

## Open questions

1. **Circular 58/2026 primary text.** All summaries are secondary X posts. The NSE circular PDF, the broker undertaking wording, and the effective implementation date at Dhan/Zerodha need to be fetched and quoted directly (not done here: the sweep's authority is X, and the primary doc was never opened).
2. **Does Dhan require a static IP for API order placement now, and how does the "tech-savvy" undertaking work in practice?** Dhan support/FAQ is the source, not X.
3. **Shyamdas's promised series** (bugs, P&L, pivots) was not captured; the account and its follow-up posts need a profile sweep. The root post alone is not performance evidence.
4. **Pranjal's second run has no broker P&L link.** The "6.5k something" reply and the −1.6% over five days are author-reported. If he posts a Dhan/Zerodha statement, add it to the thread file.
5. **Mohak Ailani's table** is a SEBI-registered research analyst's recommendation record, not an AI-executed portfolio; do not use it as evidence of AI trading. If the underlying trade log is published, revisit.
6. **Kite MCP session behaviour after Zerodha's promised fix** — retest before relying on a Zerodha fallback, and check whether Dhan MCP has the same daily-login constraint.
7. **NSE MCP / Dhan MCP rate limits and reliability** — neither is documented; a timed trial with failure logging is needed before either appears in a live path.
8. **Bazaar Trader and screener-mcp data licence/coverage** — Bazaar's slippage and charge constants are author assumptions; screener-mcp scrapes Screener.in/NSE. Verify terms and data freshness before production use.
9. **Long-form post capture.** The AX label truncates long posts; the mirror fallback worked here, but if teapawt/nitter go down the capture path needs a CUA click on "Show more" or a browser automation alternative.

## Caveats

- **Every P&L in this folder is author-reported unless stated otherwise.** No broker statement was linked in the captured posts, except the older archived Shivansh Dhan links. Nothing here is audited or replayed.
- **Search counts are capture counts, not index totals.** X does not show a total in this UI; the number is unique rendered posts per query after scrolling. See `notes/search-log.md` for the definition.
- **The sweep is X-shaped.** Primary regulatory documents, broker docs and repo licenses outside X were only opened where a post linked them.
- **One session, one day.** The Nov 20–22 regulatory cluster is fresh; reactions and broker implementation may change within days.

## Definition of done (from the brief)

- [x] Every Tier 1–2 query has a search-log row with a result count (Q1–Q14, plus all Tier 3–4 and new variants).
- [x] Every new journey thread saved verbatim with source and date (Pranjal second run, Dharmik's paper run, Shyamdas's autonomous bot; each has its own Notes section below the verbatim block).
- [x] `notes/learning.md` holds strategies/lessons not already in `strategy-notes.md`, with author-reported marks and flags.
- [x] Every repo mentioned in a saved post has a decision in `repos/INDEX.md`; useful ones downloaded (2), duplicates/rejects skipped.
- [x] This README lists new findings, duplicates skipped, artifacts and open questions.

## Continuing the sweep

Start with [`tools/capture-notes.md`](tools/capture-notes.md) for the working Safari/CUA capture recipe (the old `xgrab.sh` clipboard path is blocked in this environment). Then run the "ready-to-run variants" at the end of `QUERIES.md` and append rows to `notes/search-log.md` and, if appropriate, `notes/learning.md`. Keep every new artifact inside this folder; do not edit the first collection except to add a pointer, and do not re-download a repo already decided here or in `offline-research/resources/INDEX.md`.
