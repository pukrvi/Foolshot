# Repo review register — second sweep

22 November 2026 · repos surfaced by the X sweep in `offline-research/x-india-sweep/`. Reviewed against the existing register at [`../../resources/INDEX.md`](../../resources/INDEX.md) by upstream `owner/repo` before anything was downloaded.

No repo on this page appeared in the earlier register, so none is a duplicate download and no rejected repo was re-downloaded. `marketcalls/openalgo` (kept earlier) came up again with a new release; it was not downloaded again and the new evidence is recorded in [`../notes/learning.md`](../notes/learning.md) as R2.

## Working shortlist

| Upstream | Decision | License | Local copy | Files inspected | Reason and use | Discovery source |
|---|---|---|---|---|---|---|
| [raiaashish-code/bazaar-trader-skill](https://github.com/raiaashish-code/bazaar-trader-skill) | **Adopt pattern** | MIT (LICENSE present; copyright 2026 Jake Schincariol for the original US pack) | `raiaashish-code/bazaar-trader-skill/` (260 KB, downloaded 2026-11-22) | `README.md` · `lib/honest.py` · `lib/india_clock.py` · `bazaar-risk/check.py` · `bazaar-budget/size.py` · `bazaar-broker/ticket.py` · `tests/test_clock_and_honest.py` | Use the IST session clock/holiday list and flat-by rules, the honest-fill model (first print after signal, slippage, stop at traded extreme), the full NSE charge stack for net scoring, and the deterministic risk/sizing gates. Paper-only by design; never sends orders. This is the single most useful artifact of the sweep for Foolshot's cost/reconciliation model. | [@Aashish10_03](https://x.com/Aashish10_03/status/2117861001227891004) |
| [LogeshR15/screener-mcp](https://github.com/LogeshR15/screener-mcp) | **Adopt pattern / reference** | MIT (LICENSE present, Copyright 2026 Logesh Ramasamy) | `LogeshR15/screener-mcp/` (2.1 MB, downloaded 2026-11-22) | `README.md` · `server.py` (30 tool definitions, resources) · `src/screener_mcp/core/nse_client.py` · `src/screener_mcp/parsers/screener.py` · `src/screener_mcp/tools/portfolio.py` | Reference for the research-agent tool surface: NSE announcements/bulk deals/PIT insider filings, Screener.in company pages and screens, and local portfolio P&L. Use it to design Foolshot's research tools and to see how NSE sessions/cookies are handled; do not rely on it as an execution feed. | [@Logesh11667187](https://x.com/Logesh11667187/status/2122534692943794634) |

## Reviewed, not downloaded

| Upstream | Decision | License | File inspected | Reason | Discovery source |
|---|---|---|---|---|---|
| [javajack/skill-algotrader](https://github.com/javajack/skill-algotrader) | **Reference only, no local copy** | **No LICENSE file** in the upstream tree (README badge claims MIT; GitHub API returns no license). Treat as all-rights-reserved. | `README.md`, `KNOWLEDGE.md` (1,780 lines), `NUANCES.md` (1,044 lines) read upstream | The production notes are directly relevant (tick-size rejects, position reconciliation, naked-stop failure, backtest-live divergence) and are paraphrased into learning R10b/R11–R14. Not copied or mirrored because there is no license. Revisit if a LICENSE file appears and the project need is still current. | [@tom_doerr](https://x.com/tom_doerr/status/2080288259570020756) · [@DanKornas](https://x.com/DanKornas/status/2069946422586122698) |
| [Hitheshkaranth/OpenTerminalUI](https://github.com/Hitheshkaranth/OpenTerminalUI) | **Skip download** | MIT | `README.md` upstream | ~143 MB FastAPI + React research terminal; the relevant patterns (reviewable action proposals, runs with recorded tool results, resumable/cancellable sessions) are described in the README and noted in learning R22/R11-adjacent; no single file is needed for Foolshot and the app is UI-first. | [@HitheshKaranth](https://x.com/HitheshKaranth/status/2106005764410315136) |
| [85599/KJStockScreener](https://github.com/85599/KJStockScreener) | **Skip** | MIT | `README.md` upstream | Streamlit NSE screener with breakout scanner, option chain and an ML Nifty gap predictor. It duplicates the research-tooling role of screener-mcp, adds a UI layer Foolshot does not need, and offers no execution/reconciliation pattern. | [@khushaljai48011](https://x.com/khushaljai48011/status/2094736832676471024) |
| [bharavi1905/agentmesh](https://github.com/bharavi1905/agentmesh) | **Skip** | **No LICENSE** (GitHub API returns none) | `README.md` upstream | NSE/BSE event-alert mesh with Telegram delivery and a scoring agent. Alert-only, no execution or reconciliation role; overlaps screener-mcp's NSE data surface; no license to reuse. | [@EntangledUser](https://x.com/EntangledUser/status/2035451829073608764) |

## Rejected

| Upstream | Decision | Reason | Discovery source |
|---|---|---|---|
| [pairsync/pairdesk-builder](https://github.com/pairsync/pairdesk-builder) | Reject | GitHub API returns 404 for the repo (private or removed); the post is a crypto pairs-research desk builder, outside Foolshot's Indian-equity scope. | [@PairSync](https://x.com/PairSync/status/2122679573511057725) |
| [openqodex/open](https://github.com/openqodex/open) | Reject | Ad appearing in a captured thread: open-source AI code review. No market data, execution or research role. | Ad in [@siddhantmohan1](https://x.com/siddhantmohan1/status/2124434361550622747) reply stream |
| [Tracer-Cloud/opensre](https://github.com/Tracer-Cloud/opensre) | Reject | Ad in a captured thread: SRE/AI code review. Not trading infrastructure. | Ad in [@vincent_hus](https://x.com/vincent_hus/status/2124200000000000000) thread under the DevMagg circular post |

## Linked services (not repositories)

- **NSE MCP server** — [nseindia.com/nse-mcp](https://www.nseindia.com/nse-mcp). Free, official, 36 tools, no API key, Streamable HTTP: live `mcp.nseindia.in/cmmkt/mcp`, EOD `mcp.nseindia.in/bhavcopy/cm/mcp`. Cash market only, no F&O or intraday candles, live data ~1–3 min delayed. Decision: **trial as a research data source**, not an execution feed. Source [@AKtrader1108](https://x.com/AKtrader1108/status/2124168217946178021).
- **Dhan MCP / Dhan Skills / Dhan Cloud** — vendor tooling described by Dhan's Piyush Chaudhry and used in Kirubakaran's 6-step workflow; Dhan Cloud hosts strategies on DhanHQ. Decision: **evaluate for the Dhan-primary route**; no local artifact (video posts). Sources [@piyushchaudhry](https://x.com/piyushchaudhry/status/2076243687542231529), [@kirubaakaran](https://x.com/kirubaakaran/status/2070491176311070942), [@YashGup74155629](https://x.com/YashGup74155629/status/2124149134894813612).
- **Kite MCP** — Zerodha's official MCP; sessions reset daily and have had availability/auth incidents (learning R7–R9). Decision: reference for a read-only fallback, not a primary execution path.
- **FNOTrader MCP** — commercial NIFTY options backtest via natural language, 1-minute data, equity indices/stocks only. Decision: **skip** (commercial, no edge evidence). Source [@Sakthidoss7](https://x.com/Sakthidoss7/status/2080602796035059766).
- **Quantplay** — commercial agent that reads real positions across 10+ brokers for risk questions. Decision: **reference only** (read-only broker context). Source [@QuantplayHQ](https://x.com/QuantplayHQ/status/2124135583350206486).

## Non-repo links captured (for completeness)

Opened while reviewing the posts above; none is a repository: [nseindia.com/nse-mcp](https://www.nseindia.com/nse-mcp) and the `mcp.nseindia.in` endpoints (NSE MCP service), [screener.in](https://screener.in/) (data source behind screener-mcp), [docs.openalgo.in upgrade guide](https://docs.openalgo.in/installation-guidelines/getting-started/upgrade) and the [freeze-limits release](https://github.com/marketcalls/openalgo/releases/tag/openalgo-freeze-limits-muhurat-session) (existing kept repo), [quantplay.tech](https://quantplay.tech/) (commercial broker-agent product), [mohakailani.com](https://mohakailani.com/) (SEBI research-analyst site, not an AI product), [kjstockscreener.streamlit.app](https://kjstockscreener.streamlit.app/) (demo of a repo reviewed above), [sahicarts.com](https://sahicarts.com/) and [vibedream.ai](https://vibedream.ai/) (author product links), [devfestmumbai.com](https://devfestmumbai.com/) (event linked from the read-only-agent post).

## Local copy map

```
repos/
  raiaashish-code/bazaar-trader-skill/    MIT   260 KB  downloaded 2026-11-22
  LogeshR15/screener-mcp/               MIT   2.1 MB  downloaded 2026-11-22
```

No packages were installed, no broker was connected, and no orders were placed. Clones are read-only reference copies with `.git` removed.

Cross-reference: the earlier register at [`../../resources/INDEX.md`](../../resources/INDEX.md) still governs its 21 reviewed repos and its 16 do-not-download entries; this page adds only the repos surfaced by the second sweep.
