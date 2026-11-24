# Search log — second X sweep (India, 22 November 2026)

Session: **22 November 2026, ~16:50–18:00 IST**, Safari signed in as `@unhype.ai`, X search tab. Every row is a query actually typed into X search and captured. Tier 1–2 queries from [`../QUERIES.md`](../QUERIES.md) are all present with a result count; new variants added during the sweep are logged too.

**What "result count" means.** X's search UI does not expose a total result count in this layout. The number below is the count of **unique posts rendered and captured** on the Latest tab after loading the page and pressing PageDown 3–6 times. It is a page-capture count, not the number of matching posts in X's index. Queries with `0` rendered no posts (either a genuine empty result or the rate-limit panel — the `Err` column distinguishes).

| # | Query (exact string) | Tab | Posts captured | Err page | What it yielded / saved |
|---|---|---|---|---|---|
| 1 | `(claude OR chatgpt OR "ai agent" OR llm) (nifty OR banknifty OR sensex OR "indian market" OR "indian stock") (trade OR trading OR trader) -filter:replies` | Latest | 14 | no | Tier 1. Surfaced the 20 Nov NSE static-IP circular posts (@subuonelifee) plus industry chatter. Nothing saved directly; R1 later sourced from the dedicated queries. |
| 2 | `(zerodha OR dhan OR upstox OR groww OR angelone OR fyers OR kotakneo) (claude OR chatgpt OR mcp OR "ai agent")` | Latest | 10 | no | Tier 1. Dhan Cloud/API and Zerodha AI posts; @YashGup74155629 DhanDev Hyderabad and @kortexagent Zerodha AI-usage stats. Dhan post saved (Q5+). |
| 3 | `("ai trading" OR "agentic trading" OR "claude trading" OR "ai trader") india` | Latest | 16 | no | Tier 1. Mostly listicles and product promos. One research post on models "remembering" the market (@rajanraju26) noted in learning R32. |
| 4 | `(nifty OR banknifty) (claude OR chatgpt OR "ai agent") (backtest OR strategy OR pnl OR "paper trading" OR "live trading")` | Latest | 12 | no | Tier 1. Archived Pranjal post again; @talktovardhan indicator-stacking critique (R31); @PairSync desk promo. |
| 5 | `(mcp OR "model context protocol") (zerodha OR dhan OR nse OR nifty OR "indian broker")` | Latest | 12 | no | Tier 1. Strong: NSE official MCP server (@AKtrader1108), Dhan Cloud (@YashGup74155629), @boardyai filings-pipeline comment. NSE MCP and Dhan items saved and captured. |
| 6 | `(claude code OR codex OR cursor OR "gemini cli") (nifty OR banknifty OR "indian market") trading` | Latest | 13 | no | Tier 1. @Aashish10_03 "Bazaar Trader" 11 Claude skills (repo saved, R?); @Tenshiwrf low value. |
| 7 | `("₹1 lakh" OR "1 lakh" OR "100000" OR "one lakh") (claude OR ai OR agent) trading` | Latest | 12 | no | Tier 2. 12 posts, none passing the India+AI filter; no saves. |
| 8 | `(claude OR ai) (intraday OR "options buying" OR expiry OR "option selling") nifty` | Latest | 15 | no | Tier 2. 15 posts, none passing the India+AI filter; no saves. |
| 9 | `("paper trading" OR "live trading") (claude OR gpt OR gemini OR grok OR deepseek) (india OR nse OR nifty)` | Latest | 12 | no | Tier 2. @ShyamdasMallya autonomous bot (saved verbatim), @dharmikgohil_ ₹1L paper thread (saved verbatim), @sks_dev tool post. |
| 10 | `(nifty OR banknifty) ("stopped out" OR "square off" OR "auto square" OR "token expired" OR "ip whitelist")` | Latest | 9 | no | Tier 2. 9 posts; the incidents returned were market news, not AI/broker incidents. No saves. |
| 11 | `("trading bot" OR "algo trading") (india OR nse) (ai OR llm OR agent) -filter:replies` | Latest | 5 | no | Tier 2. @subuonelifee circular summary; @MartinDaya3 AI NSE bot review request (no public result). |
| 12 | `(backtest OR "walk forward" OR "out of sample") (nifty OR banknifty OR "indian options") (claude OR llm OR agent)` | Latest | 5 | no | Tier 2. @PairSync only; no saves. |
| 13 | `(backtest OR "walk forward" OR "out of sample") (nifty OR banknifty OR "indian options") (claude OR llm OR agent)` | Latest | 14 | no | Tier 2. @Suhas__ashok 3-year Indian trader/AI post, @jiyani02 Claude broker-data session, @EnumulaKartik ML portfolio build. @Suhas post captured for learning. |
| 14 | `min_faves:40 (claude OR chatgpt OR "ai agent") (nifty OR banknifty OR "indian market")` | Latest | 13 | no | Tier 2. min_faves filter mostly returned large-account noise; @talktovardhan critique (R31). |
| 15 | `(nsepython OR "jugaad-data" OR "nse data" OR openalgo OR "indian broker api" OR "kite connect") (ai OR llm OR agent OR claude)` | Latest | 12 | no | Tier 3. NSE MCP, OpenAlgo research-agent release, @ankit_mehta OpenAlgo preview, @QuantplayHQ. OpenAlgo release and Quantplay captured. |
| 16 | `("dhan mcp" OR "kite mcp" OR "zerodha mcp" OR "upstox mcp" OR "groww mcp")` | Latest | 16 | no | Tier 3. Every MCP provider route: Kite MCP session complaints, Dhan MCP launch, screener NSE MCP, Kite MCP read-only patterns. @vishal__bulbule, @piyushchaudhry, @DeepankarBhade, @nixxin captured. |
| 17 | `("trading agent" OR "multi-agent") (india OR nse OR nifty OR "indian market")` | Latest | 12 | no | Tier 3. Mostly job ads and generic multi-agent posts; no saves. |
| 18 | `(github.com) (nifty OR banknifty OR zerodha OR dhan OR nse) (claude OR llm OR agent OR backtest)` | Latest | 10 | no | Tier 3. screener-mcp (@Logesh11667187), OpenAlgo release, OpenTerminalUI (@HitheshKaranth), @tom_doerr skill post. All captured and reviewed. |
| 19 | `(sebi OR nse) (ai OR algorithmic OR algo) trading retail 2026` | Latest | 13 | no | Tier 3. NSE static-IP circular cluster: @algotradingdesk, @DevMagg, @SyedSibetHassan. Captured; R1 sourced here plus Q32. |
| 20 | `("indian market" OR nifty) ("ai agent" OR agentic) (portfolio OR risk OR execution)` | Latest | 12 | no | Tier 3. Generic market commentary; no saves. |
| 21 | `from:shivanshco (claude OR dhan OR trading)` | Latest | 20 | no | Tier 4. Shivansh follow-ups: Dhan position posts, new Meta-ads posts (non-trading). No new trading sessions after Day 5; confirms the series ended. |
| 22 | `from:pranjalsoni_ (claude OR zerodha OR backtest)` | Latest | 13 | no | Tier 4. CRITICAL: second live run found — day 3/4/5, 3-green-days, loss posts, limits post. All captured verbatim in threads/pranjalsoni-second-run.md. |
| 23 | `from:hb_stocks (nse OR data OR backtest)` | Latest | 13 | no | Tier 4. Haseeb's new Claude fundamental-analyst series (18-19 Nov), NSE data Sheets follow-ups. Captured; R35, R38. |
| 24 | `to:shivanshco OR to:pranjalsoni_ (claude OR ai OR backtest)` | Latest | 20 | no | Tier 4. Replies to Shivansh/Pranjal mostly noise (meta-ads thread); no new trading replies. |
| 25 | `@shivanshco OR @pranjalsoni_ (claude OR ai) -filter:replies` | Latest | 27 | no | Tier 4. Mentions mostly noise; @gohil_revin asked Pranjal what happened after day 5 (unanswered), user's own @unhype_ai reply to Shivansh about the meta-ads thread. |
| 26 | `from:pranjalsoni_ since:2026-11-01 until:2026-11-10` | Latest | 17 | no | New variant. Date-filtered Pranjal timeline: filter was not strict (returned 9-10 Nov unrelated posts first); useful only to show the timeline volume. No saves. |
| 27 | `from:pranjalsoni_ claude since:2026-11-01 until:2026-11-08` | Latest | 8 | no | New variant. `from:pranjalsoni_ claude` — the effective query for the second run; returned the day 3/4/5 posts directly. Used as the basis for the verbatim file. |
| 28 | `("NSE MCP" OR "nse mcp" OR "nseindia mcp")` | Latest | 0 | no | New variant. Retry of `"NSE MCP"` after a rate-limit page: search returns zero rendered posts (X shows no results for the quoted phrase in this session). |
| 29 | `("dhan mcp" OR "dhan skills")` | Latest | 0 | no | New variant. `"dhan mcp"` also returns zero rendered posts in Latest; the Dhan MCP material came from the provider handles found in Q16/Q5. |
| 30 | `("letting" OR "gave") (claude OR ai) (trade OR trading) ("real money" OR "real account")` | Latest | 8 | no | New variant. "letting/gave AI trade real money" — returns crypto/US AI journals (AvemaHQ, Grok Bot promos), outside Indian scope; no saves. |
| 31 | `(claude OR ai) (nifty OR banknifty) ("P&L" OR pnl OR loss OR profit) since:2026-09-01` | Latest | 12 | no | New variant. Static-IP commentary: @thesanjay15, @REDBOXINDIA, @abhip_me, @kirubaakaran. Captured for regulatory detail and the grievance-waiver critique. |
| 32 | `("static ip" OR "circular 58") (algo OR trading) india` | Latest | 11 | no | New variant. Static-IP practical guides and news: @abhip_me how-to, @REDBOXINDIA summary, @Alphaalgo7 explainer, @kirubaakaran provider comment, @Truvosofficial IP/CGNAT report. Captured. |
| 33 | `(zerodha OR dhan OR nse) (mcp OR "ai agent") ("session" OR "token" OR "login" OR "expired")` | Latest | 10 | no | New variant. Broker session quirks: @nixxin Zerodha MCP expiry, @zerodha official token reply, @aiwithme0001 auth failure, @DeepankarBhade session question. Captured for R7-R9. |

## Tier totals

- Tier 1 — core discovery: 6 queries, 77 posts captured.
- Tier 2 — evidence and outcomes: 8 queries, 85 posts captured.
- Tier 3 — repos, data and tooling: 6 queries, 75 posts captured.
- Tier 4 — author follow-ups: 5 queries, 93 posts captured.
- New variants added during this sweep (22 Nov 2026): 8 queries, 66 posts captured.

## Operational notes for the next run

- **The blocker described in the handoff did not repeat.** X search answered on the first navigation of the session. Two queries (28 and 29) hit a "Something went wrong. Try reloading." panel on their first attempt; the same URLs retried later returned normally (0 results). No long wait was needed. The usual shape — retry once, then wait 10–15 minutes — is still the right first response.
- **Date operators are weaker than they look.** `since:`/`until:` on Latest did not strictly filter: Q26 `from:pranjalsoni_ since:2026-11-01 until:2026-11-10` returned 9–10 November non-trading posts and did not reach the trading posts within six screens; Q27 with an extra keyword (`claude`) found them immediately. Add a keyword to `from:` queries instead of relying on date windows.
- **`from:<handle> <keyword>` is the highest-yield pattern.** Q27 and Q22 produced the entire second Pranjal run. Q23 produced Haseeb's new series. Q21 confirmed Shivansh had stopped posting trading updates and had moved to Meta ads.
- **Provider handles beat topical queries for tool discovery.** NSE MCP, Dhan MCP/Cloud and OpenAlgo material came from provider/practitioner handles (@AKtrader1108, @piyushchaudhry, @kirubaakaran, @openalgoHQ) found through Q5/Q16/Q18, not from `"NSE MCP"` (Q28, 0 posts) or `"dhan mcp"` (Q29, 0 posts).
- **Quote-heavy queries return quote-post noise.** Q25 (`@shivanshco OR @pranjalsoni_ ...`) returned 27 posts, mostly reactions to unrelated posts by those handles. Prefer `from:` for author coverage.
- **The phrase searches that worked:** `static ip` + `circular 58` (Q31/Q32) for the regulatory cluster; `claude` inside a `from:` query; `NSE MCP` only as a free-text phrase in a broader query. The Indian-vocabulary terms that paid off this sweep: `NSE MCP`, `Dhan MCP`, `Dhan Cloud`, `static IP`, `circular 58/2026`, `Kite MCP`, `screener-mcp`, `Bazaar Trader`, `DhanDev`.
- **Top tab** was probed once with `claude nifty trading` and returned two high-engagement posts (the archived Pranjal week and the Mohak Ailani recommendation record). Top is good for established threads; Latest is required for the follow-up runs that matter here. Tiers were run on Latest as specified.

## Capture method (what worked this session)

- **AppleScript can set a tab URL and read titles**; `do JavaScript` is still disabled ("Allow JavaScript from Apple Events" off). `System Events` keystrokes are **denied** in this session ("osascript is not allowed to send keystrokes"), so the handoff's clipboard script (`tools/xgrab.sh`) no longer works as written.
- **Working path:** AppleScript sets the X URL in tab 8; the **CUA plugin** (accessibility tree) reads the rendered page. The AX tree exposes every post's full text, numeric status ID, author, timestamp and reply/like/view counts, which the clipboard path does not. Cmd+A/Cmd+C is still available through CUA's app-level keyboard when a clipboard copy is wanted.
- **Long posts:** the AX article label is truncated for long-form posts; the full text is obtained from the teapawt mirror page for that post ID (saved under [`../snapshots/mirrors/`](../snapshots/mirrors/)). X's own page splits long text across several AX nodes, so the label + mirror pair is the reliable verbatim source.
- **Screenshots:** CUA window screenshots failed with `WINDOW_CHANGED`; `screencapture -x -o` from the shell works and was used for visual checks. Clipboard was backed up to `/tmp/clip-backup2.txt` before the session and restored afterwards.

## Saved artifacts from this sweep

- `../snapshots/search/q01.txt` … `q33.txt` plus `.json` for q13–q33: raw page text per query, header records query, URL, tab, error flag and count.
- `../snapshots/posts/<topic>/tree.txt`, `thread.txt`, `posts.json`: per-post AX capture and extracted article list.
- `../snapshots/mirrors/<handle>-<id>.txt`: full-text mirror copy for long posts.
- `../snapshots/_all-search-posts.json` and `../snapshots/_fulltexts.json`: aggregated candidate and full-text indexes for later re-use.

Reproduce a search: `https://x.com/search?q=<url-encoded query>&src=typed_query&f=live` in a signed-in browser, then scroll the article list and capture the AX tree (see the Capture method section).
