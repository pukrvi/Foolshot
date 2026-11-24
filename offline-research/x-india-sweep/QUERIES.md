# X search strings — Indian-market AI trading sweep

Goal: find posts that add to Foolshot's evidence base, not posts that restate what is already archived. Relevance is judged on three things: Indian instruments or brokers, an AI/agent stack that actually trades or researches, and some form of evidence (live P&L, backtest, repo, dataset, failure report).

## Already covered — do not re-collect

| Author | What is archived | File |
|---|---|---|
| @shivanshco | Five live Dhan sessions, replies | `../threads/shivansh-mehendiratta.md` |
| @pranjalsoni_ | Zerodha week, 16 failure paths, backtest audit | `../threads/pranjal-soni.md` |
| @hb_stocks | NSE data export step | `../threads/resource-posts.md` |
| @chatgptricks | Claude Trading Skills | `../threads/resource-posts.md` |
| @51bodila | LEAPS benchmark, 10-repo roundup, six-agent desk | `../threads/resource-posts.md`, `../articles/` |
| @ludoonchart | BTC 20/50 replay, paper-terminal guide | `../threads/resource-posts.md`, `../articles/` |

Exclude those handles from discovery queries (`-from:shivanshco -from:pranjalsoni_ ...`) and use `from:` queries only to catch new follow-ups.

## Tier 1 — core discovery

Paste into X search, then switch to **Latest** and work backwards. Add `since:2026-09-01` to keep the sweep recent.

1. `(claude OR chatgpt OR "ai agent" OR llm) (nifty OR banknifty OR sensex OR "indian market" OR "indian stock") (trade OR trading OR trader) -filter:replies`
2. `(zerodha OR dhan OR upstox OR groww OR angelone OR fyers OR kotakneo) (claude OR chatgpt OR mcp OR "ai agent")`
3. `("ai trading" OR "agentic trading" OR "claude trading" OR "ai trader") india`
4. `(nifty OR banknifty) (claude OR chatgpt OR "ai agent") (backtest OR strategy OR pnl OR "paper trading" OR "live trading")`
5. `(mcp OR "model context protocol") (zerodha OR dhan OR nse OR nifty OR "indian broker")`
6. `(claude code OR codex OR cursor OR "gemini cli") (nifty OR banknifty OR "indian market") trading`

## Tier 2 — evidence and outcomes

These target the part Foolshot actually scores: net results after costs, live incidents, and failed variants.

7. `("₹1 lakh" OR "1 lakh" OR "100000" OR "one lakh") (claude OR ai OR agent) trading`
8. `(claude OR ai) (intraday OR "options buying" OR expiry OR "option selling") nifty`
9. `("paper trading" OR "live trading") (claude OR gpt OR gemini OR grok OR deepseek) (india OR nse OR nifty)`
10. `(nifty OR banknifty) ("stopped out" OR "square off" OR "auto square" OR "token expired" OR "ip whitelist")`
11. `("trading bot" OR "algo trading") (india OR nse) (ai OR llm OR agent) -filter:replies`
12. `(backtest OR "walk forward" OR "out of sample") (nifty OR banknifty OR "indian options") (claude OR llm OR agent)`
13. `min_faves:40 (claude OR chatgpt OR "ai agent") (nifty OR banknifty OR "indian market")`
14. `filter:links (claude OR "ai agent" OR llm) (nifty OR zerodha OR dhan OR nse)`

## Tier 3 — repos, data and tooling

15. `(nsepython OR "jugaad-data" OR "nse data" OR openalgo OR "indian broker api" OR "kite connect") (ai OR llm OR agent OR claude)`
16. `("dhan mcp" OR "kite mcp" OR "zerodha mcp" OR "upstox mcp" OR "groww mcp")`
17. `("trading agent" OR "multi-agent") (india OR nse OR nifty OR "indian market")`
18. `(github.com) (nifty OR banknifty OR zerodha OR dhan OR nse) (claude OR llm OR agent OR backtest)`
19. `(sebi OR nse) (ai OR algorithmic OR algo) trading retail 2026`
20. `("indian market" OR nifty) ("ai agent" OR agentic) (portfolio OR risk OR execution)`

## Tier 4 — author follow-ups

21. `from:shivanshco (claude OR dhan OR trading)` — new sessions after Day 5
22. `from:pranjalsoni_ (claude OR zerodha OR backtest)` — next run, fixed IP
23. `from:hb_stocks (nse OR data OR backtest)` — later steps in the NSE series
24. `to:shivanshco OR to:pranjalsoni_ (claude OR ai OR backtest)` — substantive replies from others
25. `@shivanshco OR @pranjalsoni_ (claude OR ai) -filter:replies` — quote-posts and commentary

## Vocabulary that Indian posters actually use

Include these when the English queries run dry: `Nifty`, `Bank Nifty`, `BankNifty`, `Sensex`, `F&O`, `options buying`, `expiry day`, `BTST`, `intraday`, `delivery`, `Zerodha Kite`, `Dhan`, `Upstox`, `Groww`, `Angel One`, `Fyers`, `Kotak Neo`, `ICICI Direct`, `NSE`, `BSE`, `SEBI`, `lot size`, `margin`, `brokerage`, `STT`, `DP charges`, `paper trade`, `backtest`, `forward test`, `algo`, `screener`, `corporate filings`.

## Operators cheat sheet

| Operator | Use |
|---|---|
| `"exact phrase"` | Force a phrase |
| `OR` | Alternatives, must be uppercase |
| `(a OR b)` | Grouping |
| `-word` / `-from:handle` | Exclude |
| `from:` / `to:` / `@handle` | Author, replies, mentions |
| `filter:links` / `filter:media` / `filter:replies` | Attachment and reply filters |
| `min_faves:50` / `min_retweets:10` | Quality floor |
| `since:2026-09-01` / `until:2026-11-23` | Date window |
| `lang:en` | Language |

## Sweep order

1. Tier 1 queries on **Latest**, last 60 days. Save only posts that pass the relevance test.
2. Open each promising thread; capture the whole thread, not just the bookmarked post.
3. Tier 2 for outcomes and incidents.
4. Tier 3 only when a post names a repo, dataset or broker tool.
5. Tier 4 at the end, so new follow-ups are not missed.
6. Log every query, date and result count in `../notes/search-log.md` so the next run does not repeat it.

---

## Second sweep — queries added 22 November 2026

These were run after the 25 above. Result counts and per-query notes are in [`notes/search-log.md`](notes/search-log.md). ✅ = produced findings saved in this folder; ⚪ = ran but produced nothing useful.

### Variants that worked

| Query | Result | Why it worked |
|---|---|---|
| `from:pranjalsoni_ claude since:2026-11-01 until:2026-11-08` | ✅ Found the five-day second live run (day 3, day 4, day 5, loss posts, limits post) | `from:` + one distinctive keyword beats a date-only window where the date operators are flaky |
| `("static ip" OR "circular 58") (algo OR trading) india` | ✅ NSE Circular 58/2026 cluster: practical guide, provider comment, news summary | New Indian regulatory vocabulary from the circular itself |
| `("NSE MCP" OR "nse mcp" OR "nseindia mcp")` | ⚪ 0 rendered posts in Latest on 22 Nov (topical phrase too new/rare in index) | The NSE MCP material came from the provider post found through `(mcp OR ...) (zerodha OR dhan OR nse ...)` instead |
| `("dhan mcp" OR "dhan skills")` | ⚪ 0 rendered posts in Latest | Use the Dhan/provider handles directly (`from:piyushchaudhry`, `from:kirubaakaran`) |
| `(zerodha OR dhan OR nse) (mcp OR "ai agent") ("session" OR "token" OR "login" OR "expired")` | ✅ Kite MCP session-expiry and token-handling posts, plus official Zerodha reply | Broker-quirk framing pulls practitioner complaints and vendor replies together |
| `("letting" OR "gave") (claude OR ai) (trade OR trading) ("real money" OR "real account")` | ⚪ Crypto/US AI journals; no Indian posts | Add `india` or a broker term next time |
| `(claude OR ai) (nifty OR banknifty) ("P&L" OR pnl OR loss OR profit) since:2026-09-01` | ⚪ Mostly market-news noise; one useful reply on static IP | P&L is under-posted; prefer `from:` authors |

### Ready-to-run variants for the next sweep

Copy these as-is into X Latest. Add `since:` only when the `from:`/keyword core is already narrow.

1. `from:pranjalsoni_ (day OR claude OR "real money")` — catch any day 6+/new run.
2. `from:hb_stocks (claude OR fundamental OR results OR sheet)` — Haseeb's NSE/Claude series follow-ups.
3. `from:openalgoHQ (agent OR freeze OR release)` — OpenAlgo release notes that affect NSE order handling.
4. `from:kirubaakaran (mcp OR dhan OR claude OR workflow)` — Dhan MCP workflows.
5. `from:piyushchaudhry (dhan OR mcp OR cloud)` — Dhan tooling launches.
6. `from:AKtrader1108 (nse OR mcp OR market)` — NSE MCP updates.
7. `("NSE MCP" OR "nse mcp" OR "mcp.nseindia") -filter:replies` — retry unquoted on Top as the launch ages.
8. `("dhan mcp" OR "dhan skills" OR "dhan cloud") -filter:replies` — retry unquoted on Top.
9. `("static ip" OR "circular 58/2026" OR "tech-savvy") (algo OR broker OR trading)` — new circular commentary and broker notices.
10. `(nse OR sebi) ("retail algo" OR "algo trading") (undertaking OR empanelment OR grievance)` — primary/legal follow-ups to Circular 58/2026.
11. `("fixed ip" OR "static ip" OR vps) (trading OR algo OR broker) india` — hosting/fixed-IP practice posts.
12. `("kite mcp" OR "dhan mcp") (session OR token OR login OR expired OR down)` — broker MCP reliability, the operational kill-shot for a 90-day run.
13. `("screener-mcp" OR "bazaar trader" OR "bazaar-trader")` — adoption reports and issues for the two downloaded repos.
14. `("claude" OR "ai") (nifty OR banknifty OR "indian market") ("total pnl" OR "after charges" OR "net pnl" OR "drawdown")` — real net-result posts, rare and high value.
15. `("day 1" OR "day 2" OR "day 3" OR "week 1") (claude OR ai OR gpt) (trade OR trading) (india OR nse OR nifty)` — find new public journey threads early.
16. `("AI agent" OR claude) (backtest OR "paper trading") (nifty OR banknifty OR dhan OR zerodha) filter:links` — repos and write-ups with a link.
17. `("nifty" OR "banknifty") ("token expired" OR "session expired" OR "auto square" OR "ip mismatch" OR "freeze limit")` — incident vocabulary for the reliability half of the score.
18. `from:zerodha OR from:AskZerodha (mcp OR api OR login OR session)` — official answers to broker-quirk questions.
19. `("SEBI" OR "NSE") (AI OR "algorithmic trading") (framework OR circular) since:2026-11-01` — regulatory changes before Day 1.
20. `@unhype_ai` or `from:<new author>` once a promising account is found — profile sweep of the new author's own timeline.

### Vocabulary that paid off this sweep

`NSE MCP`, `Dhan MCP`, `Dhan Skills`, `Dhan Cloud`, `DhanDev`, `Kite MCP`, `static IP`, `Circular 58/2026`, `tech-savvy retail`, `retail algo framework`, `empanelment`, `undertaking`, `grievance`, `screener-mcp`, `Bazaar Trader`, `honest fills`, `freeze limits`, `Muhurat`, `token expired`, `ip mismatch`, `auto square-off`, `paper trading`, `first print`, `tick size`, `bot_managed`, `reconciliation`, `kill switch`.

Note: `"NSE MCP"` and `"dhan mcp"` return 0 rendered posts on Latest as of 22 Nov 2026 even though the topics are live; the index lags the vocabulary. Prefer provider handles until the terms age in.
