# Foolshot resource review register

22 November 2026 · 21 upstream repositories · 22 downloaded source trees. Each decision follows a local README, license and code review. Adoption means adapting the named pattern in a later build. No dependency was installed or connected to a broker.

## Check before downloading

1. Match GitHub resources by upstream `owner/repo`. Compare case-insensitively and ignore URL suffixes such as `.git`, branch paths, release links, and ZIP links. Resolve redirects to the current upstream name when needed.
2. Reuse the active local copy for a kept repo. Skip repositories in the do-not-download list, including mirrors and duplicate snapshots of the same source. A new mention on X can add evidence to the existing entry.
3. For a new repo, inspect its upstream README, license, and relevant file first. Download only when you can name the file or pattern Foolshot will use. Record the upstream link, discovery source, review date, decision, and reason here. Mark the review date on the new entry.
4. Revisit a skipped repo when a new capability or a changed project need addresses the recorded reason. Record the new evidence and the prior decision before downloading it again.

## Working shortlist

| Upstream | Decision | Local license | Code or skill reviewed | Reason and use | Source in collection |
|---|---|---|---|---|---|
| [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) | Adopt workflow | MIT | [skills/backtest-expert/SKILL.md](tradermonty/claude-trading-skills/skills/backtest-expert/SKILL.md) | Use the Backtest Expert sensitivity, slippage and holdout checks during weekly strategy review. Supply NSE costs and executable quotes. Its suggested sample lengths do not delay the live launch. | @chatgptricks |
| [virattt/ai-hedge-fund](https://github.com/virattt/ai-hedge-fund) | Adopt pattern | MIT | [hedge_fund/risk/limits.py](virattt/ai-hedge-fund/hedge_fund/risk/limits.py) | Adapt the deterministic RiskLimits and ClampEvent pattern before order submission. Log requested and approved size, firing limit and idle cash. Use rupee limits and whole shares. | bodila roundup |
| [marketcalls/openalgo](https://github.com/marketcalls/openalgo) | Reference | AGPL-3.0 | [broker/dhan/api/order_api.py](openalgo-HEAD/broker/dhan/api/order_api.py) · [Zerodha order API](openalgo-HEAD/broker/zerodha/api/order_api.py) | Compare Dhan order and trade-book calls against the direct API and compare Zerodha tag-based recovery during timeout drills. Both adapters exist in source. OpenAlgo would be a separate execution route with its own session and credentials. No live compatibility test was run. | Shivansh Day 1 reply |
| [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | Reference | LGPL-3.0 | [crates/execution/src/reconciliation/positions.rs](nautechsystems/nautilus_trader/crates/execution/src/reconciliation/positions.rs) | Use check_position_reconciliation and its late-fill/snapshot cases for restart tests. Require exact signed quantities for NSE shares. Only broker records establish fills. | bodila roundup |
| [freqtrade/freqtrade](https://github.com/freqtrade/freqtrade) | Reference | GPL-3.0 | [freqtrade/optimize/analysis/lookahead.py](freqtrade/freqtrade/freqtrade/optimize/analysis/lookahead.py) | Use LookaheadAnalysis.analyze_indicators as the design for a full-history versus truncated-history comparison at each decision time. Its crypto exchange execution stays outside the pilot. | bodila roundup |

## Do not download again

These sixteen projects were reviewed on 22 November 2026. Their upstream links, review evidence, and reasons stay in this register after the staging folder is deleted.

| Upstream | Decision | Local license | Code or skill reviewed | Reason and use | Source in collection |
|---|---|---|---|---|---|
| [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | Skip | Apache-2.0 | `tradingagents/agents/risk_mgmt/conservative_debator.py` | Bull/bear and risk-debate prompts add calls without a deterministic limit or an execution test. | bodila roundup and desk guide |
| [janestreet/agent_skills](https://github.com/janestreet/agent_skills) | Skip | MIT | `socratic-tutor/SKILL.md` | The sole Socratic tutor skill serves teaching sessions. | bodila roundup |
| [goldmansachs/gs-quant](https://github.com/goldmansachs/gs-quant) | Skip | Apache-2.0 | `gs_quant/backtests/equity_vol_engine.py` | Its equity volatility backtest engine does not supply the missing NSE signals, quotes or broker reconciliation. | bodila roundup, BTC replay and paper-terminal guide |
| [quantopian/zipline](https://github.com/quantopian/zipline) | Skip | Apache-2.0 | `zipline/finance/slippage.py` | Its slippage simulator adds a second historical engine without the broker order lifecycle needed here. | bodila roundup |
| [OpenBB-finance/OpenBB](https://github.com/OpenBB-finance/OpenBB) | Skip | Apache-2.0 | `openbb_platform/providers/nasdaq/openbb_nasdaq/models/company_news.py` | The examined Nasdaq news provider adds a data abstraction when this pilot already uses Dhan and NSE filings. | bodila roundup and guide replies |
| [microsoft/qlib](https://github.com/microsoft/qlib) | Skip | MIT | `examples/workflow_by_code.py` | Its training, recorder and portfolio evaluation workflow duplicates the smaller versioned experiment journal. | bodila roundup |
| [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) | Skip | MIT | `src/alpaca_mcp_server/toolsets.py` | Its named operation sets target Alpaca, while the experiment measures Dhan’s own MCP. | bodila roundup and guide replies |
| [jpmorganchase/python-training](https://github.com/jpmorganchase/python-training) | Skip | Apache-2.0 | `notebooks/2_straddle.ipynb` | The notebook teaches straddle pricing and did not generate the cited BTC replay. | ludoonchart’s BTC replay |
| [shiyu-coder/Kronos](https://github.com/shiyu-coder/Kronos) | Skip | MIT | `examples/prediction_example.py` | The example generates candle forecasts without an Indian post-cost result or execution role. | ludoonchart paper-terminal guide |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | Skip | MIT | `dspy/teleprompt/bootstrap.py` | Bootstrap prompt optimization needs a stable evaluation set. It would add an uncontrolled search dimension to this short run. | ludoonchart paper-terminal guide |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | Skip | Apache-2.0 | `mem0/memory/main.py` | Model-managed semantic memory adds a second source for facts already available in dated, append-only decision records. | ludoonchart paper-terminal guide |
| [microsoft/RD-Agent](https://github.com/microsoft/RD-Agent) | Skip | MIT | `rdagent/core/evolving_agent.py` | The evolving-agent loop duplicates the versioned hypothesis and independent-review process. | ludoonchart paper-terminal guide |
| [janestreet/magic-trace](https://github.com/janestreet/magic-trace) | Skip | MIT | `demo/demo.ml` | Low-level process tracing does not trace broker acknowledgements, fills or human consent. | ludoonchart paper-terminal guide |
| [ZhuLinsen/daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) | Skip | MIT | `src/core/pipeline.py` | Its market-report pipeline targets other venues and adds a second data and publishing stack. | ludoonchart paper-terminal guide |
| [pmorissette/bt](https://github.com/pmorissette/bt) | Skip | MIT | `bt/backtest.py` | Portfolio-level backtesting does not resolve partial fills or missing stop orders. | Reply to bodila’s desk guide |
| [ranaroussi/yfinance](https://github.com/ranaroussi/yfinance) | Skip | Apache-2.0 | `yfinance/scrapers/history.py` | Yahoo historical bars cannot establish executable NSE bid/ask quotes, fill times or charges. | bodila desk guide |

## Staged snapshot paths

Paths below are relative to `offline-research/resources/delete/`. All 17 were moved and verified. The final entry duplicates the retained namespaced NautilusTrader tree. Reuse the retained copy for future mentions. Empty parent folders are staged under `empty-parent-folders/`.

- `TauricResearch/TradingAgents/`
- `janestreet/agent_skills/`
- `goldmansachs/gs-quant/`
- `quantopian/zipline/`
- `OpenBB-finance/OpenBB/`
- `microsoft/qlib/`
- `alpacahq/alpaca-mcp-server/`
- `jpmorganchase/python-training/`
- `shiyu-coder/Kronos/`
- `stanfordnlp/dspy/`
- `mem0-HEAD/`
- `microsoft/RD-Agent/`
- `janestreet/magic-trace/`
- `daily_stock_analysis-HEAD/`
- `pmorissette/bt/`
- `ranaroussi/yfinance/`
- `nautilus_trader-HEAD/`

## Snapshot verification

Compared filenames, bytes and symlink targets against original downloaded trees or their original ZIPs. The two NautilusTrader source trees matched, including executable modes. Finder metadata was excluded. No source differences or ambiguous ownership were found. Puneet requested this single staging folder for later deletion. The PDF and research notes are outside the cleanup set.

[Research overview](../README.md) · [LEAPS paper](LEAPS_2610.25919v1.pdf) · [arXiv record](https://arxiv.org/abs/2610.25919)

## Linked services and unavailable source

## Second sweep additions — integrated 24 November 2026

The [second-sweep register](../x-india-sweep/repos/INDEX.md) is part of this register and must be checked before any future download. It adds two retained MIT references and seven non-downloaded decisions. Preserve its reasons even if source snapshots are removed. The two retained trees stay in `../x-india-sweep/repos/`; no duplicate copy is needed.

| Upstream | Decision | Reason |
|---|---|---|
| `raiaashish-code/bazaar-trader-skill` | Keep, adapt paper patterns | Honest fills, cost model, calendar, deterministic sizing and risk tests; verify assumptions. |
| `LogeshR15/screener-mcp` | Keep, research reference | Optional company/filing tool design; not an execution feed. |
| `javajack/skill-algotrader` | Do not download | No verified license; use dated paraphrased operational lessons only. |
| `Hitheshkaranth/OpenTerminalUI` | Do not download | UI-heavy and no needed unique module. |
| `85599/KJStockScreener` | Do not download | Overlapping screener and no reconciliation capability. |
| `bharavi1905/agentmesh` | Do not download | Alert-only overlap; no verified license. |
| `pairsync/pairdesk-builder` | Do not download | Unavailable and crypto-focused. |
| `openqodex/open` | Do not download | Unrelated code-review ad. |
| `Tracer-Cloud/opensre` | Do not download | Unrelated SRE ad. |
| `marketcalls/openalgo` | Reuse existing | New release mentions freeze limits and session updates; verify official rules, not a duplicate snapshot. |

All discovery links, review dates, license details and inspected files remain in the linked sweep register. Together the two registers cover 30 distinct upstream projects, with seven retained and 23 not retained.

- [LEAPS benchmark code](https://github.com/howard-yen/LEAPS) is the URL printed in the paper. GitHub and its source download both returned 404 when checked.
- [NSE historical archives](https://betanseapi.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives), [SEC EDGAR](https://www.sec.gov/edgar/search/), [SEC insider data](https://www.sec.gov/dera/data/form-345), [OpenInsider](http://openinsider.com/), and [Ebitta](https://ebitta.com/) are linked reference services. The bookmarks did not specify a single dataset export to keep for them.
- The [bodila guide](https://nitter.cf/51bodila/article/2110409939600462238) mentions hosted GrokBot and an optional Jev integration. The [BTC replay post](https://x.com/ludoonchart/status/2123898954211553534) describes a custom replay engine without a source download.

24 November 2026 · [Paper baseline source review](../design-notes/paper-baseline.md). Reused Dhan's tariff and SEBI's cash and derivatives studies to choose a cash-only paper control. Loss streaks and rupee limits require experimental calibration.
