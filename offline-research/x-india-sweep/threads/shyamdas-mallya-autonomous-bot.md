# Shyamdas Mallya — fully autonomous NSE trading bot (Dhan + Zerodha)

Verbatim root post from [@ShyamdasMallya](https://x.com/ShyamdasMallya/status/2037000763495637307), posted 26 March 2026, plus the substantive replies captured with it. The author describes a fully autonomous Indian-market trading bot and says the series documents the bugs, P&L and pivots.

**Source:** [X post](https://x.com/ShyamdasMallya/status/2037000763495637307), copied 22 November 2026 from the signed-in X session and cross-checked against the teapawt mirror. Text verbatim.

**Author-reported:** all build details, capital amounts and bug counts are the author's own report. This sweep captured the root post only; the promised series of follow-ups (bugs, P&L, pivots) was not captured and is an open question.

## Root post

*26 March 2026 · [source](https://x.com/ShyamdasMallya/status/2037000763495637307) · [mirror](https://teapawt.net/ShyamdasMallya/status/2037000763495637307)*

> I built a fully autonomous stock trading bot for the Indian market. No human intervention during the trading day. It scans 565 NSE stocks every 2 minutes, picks trades, places real orders, monitors positions, and exits all on its own. 
>
> Here's the reality of building it. 
>
> The stack: FastAPI backend, Next.js dashboard, Dhan for equity trades, Zerodha for options. ₹91,000 live capital on equities. ₹1,64,000 on options. Built almost entirely using Claude Code $20+tax plan. Claude also runs as an in-process advisor, AI advising the AI mid-trade.
>  The goal: ₹1,000–2,800/day combined. Not glamorous. Disciplined compounding.
>
> What actually happened: 15+ production bugs. In live trading. With real money. 
>
> Every bug taught something the backtests never could. 
>
> The market didn't help either. US-Iran war escalation. India VIX 20+. BankNifty gap-up and gap-downs, swinging 600-1000 points intraday. We were debugging production code in wartime volatility. 
>
> What's interesting about Claude Code: the entire codebase was built conversationally. Describe the bug, get the fix. Describe the feature, get the implementation. Then argue with it when it's wrong. It's a genuinely different way to build. 
>
> This series documents all of it — the bugs, the P&L, the decisions, the pivots. No highlight reel. Just the actual build.
>
> Follow along if you're building something hard
>
> #AlgoTrading #ClaudeCode #NSE #BANKNIFTY #BuildInPublic #Python

## Replies visible on the post

- **@shahnawab** (Sep 17): Can you put more light on how you did it and the stats of Win and Loss? — [post](https://x.com/shahnawab/status/2100469888125182149)
- **@ShyamdasMallya** (Sep 17): Soon — [post](https://x.com/ShyamdasMallya/status/2100511944893698212)
- **@GrowthExe** (Sep 24): How did you pull live data from web? — [post](https://x.com/GrowthExe/status/2103119987724685812)
- **@ShyamdasMallya** (Sep 24): Dhan APIs, took 2 years sub. — [post](https://x.com/ShyamdasMallya/status/2103137755807338932)
- **@flytradr_guy** (May 13): genuinely solid build and the transparency is rare. the 15 production bugs with live capital is the part most people skip over but that is where the real learning happens. when you open source it, would love to see how the strategy logic compares to what we have built in flytradr.com  — [post](https://x.com/flytradr_guy/status/2054295399519969281)

## Notes

Commentary for Foolshot.

- **Stack.** FastAPI backend, Next.js dashboard, **Dhan for equity trades and Zerodha for options**, deployed as a fully autonomous loop: scan 565 NSE stocks every two minutes, pick trades, place real orders, monitor and exit without human intervention. This is the closest public match to Foolshot's Dhan-primary/Zerodha-fallback split, but the author runs both brokers live at once rather than as a fallback.
- **Capital.** ₹91,000 live on equities and ₹1,64,000 live on options, with a stated goal of ₹1,000–2,800/day combined. Those are author-reported amounts; no broker statement was posted.
- **"15+ production bugs. In live trading. With real money."** The author's central claim is that production bugs, not strategy, were the main thing the backtests could not prepare for. That matches the archived Shivansh and Pranjal incidents. Foolshot should treat a bug taxonomy and restart drill as part of the experiment design, not as an afterthought.
- **Market backdrop.** US–Iran war escalation, India VIX above 20, BankNifty gap-ups and gap-downs of 600–1,000 points. The author says they were "debugging production code in wartime volatility" — relevant to the 90-day experiment's assumption about a normal-volatility window.
- **Data access.** In a reply the author says live data comes from "Dhan APIs" and took a two-year subscription. Foolshot's Dhan data plan therefore needs to be confirmed for the experiment period, not assumed from a free tier.
- **Claude's role.** The codebase was built conversationally with Claude Code on a $20+tax plan, and Claude also runs "as an in-process advisor, AI advising the AI mid-trade". Two model calls per trade (adviser plus execution agent) is a capacity and failure-surface decision, not just a prompt choice.
- **No P&L in the captured post.** The reply asking for win/loss stats got "Soon". Do not treat this as evidence of profitability; it is evidence about what a live autonomous build looked like.

Raw capture: [`snapshots/posts/shyamdas-autonomous-indian-bot/`](../snapshots/posts/shyamdas-autonomous-indian-bot/), mirror text in [`snapshots/mirrors/`](../snapshots/mirrors/).
