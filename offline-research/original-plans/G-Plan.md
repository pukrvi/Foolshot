I want to run a experiment using AI, Claude Code or Codex. The idea is that for three months I want to give these AI tools access to a MCP from either Dhan or Zerodha. Put up ₹1,00,000 in my trading account and let it trade basically on itself. Couple of things is, okay, I'll provide it some basic skills and GitHub repos that other people have built obviously before starting. It can create its own framework. Number two is it should be self-learning and make correction in its own strategy and harness. So maybe let's create a custom harness for itself inside Claude Code. I want to have a target given to it in terms of percentage, let's say 10% every week. So yeah, this is what I want to set up. Now before we draft, I want to draft a basically a project dossier of what we want to do. You can ask me clarifying question in this chat regarding things. If you want, you can ask me interactively using a UI where you give me a bunch of options, etc. as well. What I'm thinking is, or what I don't know is, I again, I'm a AI tinkerer and not from finance background. So let's say I have decided to do this, how I should run it, what maybe some tools or skills do you need, think needed. And even before that, like let's decide on some basics like what should it be doing? Should it be doing day trading, options trading, future trading? How much tax is on everything? How should I allocate my money? Again, charges, fees to get maximum profit and all of that. So let's start thinking. You brainstorm with me and then we'll figure out a specification.

---

Running an autonomous AI trading experiment with ₹1,00,000 over 3 months is a great engineering project.Since you are coming at this from an AI builder angle rather than finance, locking down the market mechanics,fee traps, and 2026 Indian rules first will stop your agent from burning capital on avoidable mistakes.

## 1. Reality Check on the "10% Every Week" Target
Before picking a broker or strategy, the goal you give the AI matters more than almost anything else.

- **The compounding math:** 10% every week for 12 weeks turns ₹1,00,000 into roughly ₹3,14,000 (+214% in 3 months). Over a full year, that is over 14,000%. Even top quantitative hedge funds rarely sustain 30-40% a year.
- **The AI reward-hacking risk:** If you prompt Claude Code or Codex to chase 10% every week, it will quickly learn that normal stock moves cannot hit that number. It will start forcing trades, taking maximum leverage, or buying risky out-of-the-money options, which usually leads to blowing up the account.
- **A better objective function:** Optimize for **risk-adjusted return** (consistent wins with small losses) under hard risk caps, such as stopping all trading for the day if down 2%, or pausing the experiment if total capital drops by 15%. For a v1 autonomous system, beating Nifty 50 or making **2-4% per month** after taxes and fees is a strong result.

## 2. Which Trading Style Fits ₹1,00,000 and an AI Agent?
Not every market segment works with a ₹1,00,000 balance or with LLM latency. Here is how the four main options compare in India as of late 2026:

| **Segment** | **Fit for ₹1L** | **Brokerage (Zerodha / Dhan)** | **STT & Key Charges** | **Income Tax Treatment** | **Fit for LLM Agent** |
| --- | --- | --- | --- | --- | --- |
| **Equity Delivery / Swing**(hold 2+ days) | **Best.** Easy to split across 4-6 stocks | **₹0** | 0.1% STT on buy and sell | Flat **20% STCG** (held under 1 year) | **High.** Matches AI strengths (news, fundamentals, daily charts) |
| **Equity Intraday**(same day) | **Good.** Up to ~5x leverage possible | ₹20 or 0.03% per order (whichever is lower) | 0.025% STT on sell side | **Tax slab**(Speculative business income, ITR-3) | **Medium.** Only works at low frequency (1-3 trades/day) |
| **Options Buying** | **Tight.** Buying works; selling needs ₹1.2L+ per lot | Flat ₹20 per order (₹40 round trip) | **0.15% STT**on sell premium (raised Apr 2026) | **Tax slab** (Non-speculative business income, ITR-3) | **Low.** Fast decay, high noise, over 90% of retail traders lose money |
| **Futures** | **Not viable.**Minimum lot margins are ₹1.2L-₹2L+ | ₹20 or 0.03% per order | 0.05% STT on sell side (raised Apr 2026) | **Tax slab** (Non-speculative business income, ITR-3) | **Not viable** at ₹1L capital |
**Key finance takeaways for your setup:**

- **The fee trap on ₹1,00,000:** If the AI takes a ₹10,000 intraday or options trade, paying ₹40 in round-trip brokerage plus STT, exchange fees, and 18% GST costs roughly ₹50 per trade. That is **0.5% friction** just to enter and exit. If the AI overtrades (say 5 trades a day), fees alone will eat ₹5,000+ a month.
- **Tax filing simplicity:** Intraday and F&O trading classify you as a business trader, which requires filing **ITR-3**, tracking turnover, and potentially paying advance tax. Speculative intraday losses also cannot offset other business income. Equity delivery/swing trading stays cleanly under capital gains (ITR-2) with zero brokerage.
- **Best starting point:** **Equity Swing Trading** (holding positions for 2-15 days), or a hybrid where 80% is swing trading and 20% is low-frequency intraday.

## 3. Zerodha vs. Dhan MCP and 2026 SEBI Rules
Both brokers now have official MCP servers, so you do not have to build a wrapper from scratch.

| **Feature** | **Zerodha Kite MCP** | **Dhan MCP** |
| --- | --- | --- |
| **Official MCP Endpoint** | Hosted at `mcp.kite.trade/mcp`, plus an open-source Go server on GitHub you can self-host | Hosted at `mcp.dhan.co/mcp` with built-in Claude Code and Codex setup docs |
| **Order & Portfolio API** | Free (Personal tier) | Free |
| **Live & Historical Data** | **₹500/month** (can be offset via Developer Credits if you pay ₹500+ in brokerage) | **₹499/month + GST** (Pro depth is ₹999/month) |
| **Standout Feature for AI** | Open-source Go MCP code lets you fork, audit, and restrict tools locally | Native **Super Orders** (entry + stop-loss + target in one call) and an official **Agent Skills** pack |
**Mandatory SEBI Algo Rules to Plan Around (Effective April 1, 2026):**

- **Whitelisted Static IP:** Under SEBI's retail algo framework active since April 1, 2026, direct API order placement requires registering a static IP with your broker (you can only change it once per week). If you run locally from home broadband with a dynamic IP, you will either need a static IP from your ISP or route orders through a cheap cloud VPS (AWS/GCP) with a fixed IP.
- **Daily 2FA Login:** Broker access tokens expire every 24 hours and require manual two-factor authentication each morning. Your harness cannot run 100% unattended for 90 days; you will need a 30-second morning auth routine before 9:15 AM IST.
- **Order Rate Limit:** Self-built personal algos staying under **10 orders per second** do not need formal exchange strategy registration, which is plenty for an LLM-driven system.

## 4. Designing the "Self-Learning" Architecture Safely
Giving Claude Code direct, unfiltered access to `place_order` is the fastest way to lose money to a bug or hallucination. The cleanest pattern is to split the system into **two layers**:

- **Layer 1: Deterministic Guardrails and Execution (Python)**

- A hard-coded risk engine sits between the AI and the broker API/MCP. The AI is **never allowed to edit this file**.
- It enforces hard limits: max capital per stock (e.g., ₹20,000), max open positions (e.g., 5), mandatory stop-loss on every entry, max daily loss kill switch (e.g., ₹2,000), and a whitelist of liquid NSE stocks (like Nifty 200) so the AI never buys illiquid penny stocks.
- Price monitoring and stop-loss triggers run in lightweight Python code (or broker-side GTT / Super Orders), not via continuous LLM polling.
- **Layer 2: The Self-Learning Brain (Claude Code / Codex Harness)**

- **Pre-market routine (8:45 AM):** Pulls overnight news, index trend, and open positions to write a structured daily plan.
- **Scheduled decision windows:** Runs at fixed checkpoints (for example, 9:30 AM, 1:00 PM, and 3:05 PM for swing trading) instead of reacting to every 1-minute candle.
- **Trade journal:** Every trade logs the entry thesis, indicators, news catalyst, and invalidation level into a local SQLite database or Markdown journal.
- **Weekend self-correction loop:** Every Saturday, Claude Code audits the week's winning and losing trades, checks what broke (bad entries, early exits, high fees), proposes updates to its strategy scripts or skills in a git branch, and runs a quick backtest on historical candles before you approve merging the update for Monday.

## 5. Starter Skills and Tools to Assemble
Before letting the agent build its own harness, giving it these 5 building blocks will save weeks of trial and error:

- **Broker MCP + Market Data Skill:** Connects to Dhan or Zerodha for portfolio state, historical OHLCV candles, and margin checks.
- **Risk & Position Sizing Skill:** Calculates exact share quantity based on stop-loss distance and max rupee risk per trade (for example, risking 1% or ₹1,000 per trade).
- **Backtesting Skill:** Wraps a Python library like `backtesting.py` or `vectorbt` so the AI can prove a strategy change works on past NSE data before going live.
- **News & Corporate Actions Skill:** Checks upcoming earnings dates, dividends, splits, and NSE announcements so the AI does not accidentally hold into a binary earnings shock.
- **Post-Mortem & Git Versioning Skill:** Forces the AI to tag every strategy tweak with a version number so you can trace which version actually made money.
To draft a clean, concrete **Project Dossier and Technical Specification**, pick your preferences below (or upload any rough notes or repo links you already have in mind).

---

I think swing in India just takes too much taxation of around 20%, so let's say I am but I am not willing to experiment with more money as well, and we need to have stop losses and overall mechanism to save us from doing, basically getting in loss again and again. What I will do is, let's say we can also have a mechanism where every day it makes profit, that profit gets taken out of there and it always should have just 1 lakh rupees to trade every day. Yeah, if it does some losses, then we will have to do take into account to either top it up or maybe let it make that money and yeah, somehow put it back. So yeah, that was one thing just came to my mind. Yeah, I don't want to do equity swing and delivery. Those are brokerage is zero. I don't know if it is the best option. I am thinking something in between intraday and options or a mix of both. Also, I want you to research, do a deep research on the internet on people who might have done it and based on their experience and how it has went for them or you also try again, do your own research and try to do some informed decision and yeah, let's keep having discussions.

---

Before locking in intraday or options, there are three things from the actual data (taxes, real-world AI trading results, and Indian settlement rules) that will save you a lot of frustration and money.

## 1. Quick Tax Catch: Swing Is Often Cheaper Than Intraday and Options
It feels like 20% tax on equity swing trading is high, but intraday and options are usually taxed **more**, not less, depending on your total income.

- **Equity Swing / Delivery:** Flat **20%** Short-Term Capital Gains tax, zero brokerage on Zerodha/Dhan, and a simple ITR-2 filing.
- **Intraday Equity and Options:** Treated as **business income** and taxed at your **income tax slab rate (up to 30% plus cess)**. If your salary or other income already puts you in the 20% or 30% slab, every rupee your bot makes in intraday or options gets taxed at that top slab rate.
- **The Extra Paperwork:** Trading intraday or F&O even once forces you to file **ITR-3**. Intraday losses are "speculative" and can only offset future intraday profits (for up to 4 years), whereas F&O losses can offset other business income (for up to 8 years), but neither can offset your regular salary. One upside: under ITR-3, you can deduct genuine trading expenses like API subscriptions, VPS hosting, and internet bills if you keep invoices.
If your main reason for skipping swing was tax, it is worth double-checking your tax slab. If you want intraday/options simply because you want faster feedback loops for the AI to learn every day, that makes total sense as an experiment.

## 2. What Real-World AI Trading Experiments Show (2025-2026 Research)
Several public benchmarks and real-money tests have tried letting LLMs like Claude, GPT, and Gemini trade on their own. The results are remarkably consistent:

- **Nof1 Alpha Arena (Real Money Benchmark):** Six top models were each given $10,000 of real money to trade live markets. Only 2 out of 6 finished in profit (Qwen at +22.3% and DeepSeek at +4.9%), while the four US models lost between 30% and 59% of their capital. One huge lesson stood out: **overtrading killed returns**. Gemini placed 238 trades and lost heavily to fees and bad churn, while Claude Sonnet placed only 38 trades and preserved far more capital. Nof1's own research note concluded that current LLMs struggle with raw live market prediction because market patterns constantly shift.
- **Multi-Season Public Arenas (44 Models, 2,527 Trades):** A September 2026 review of six full AI trading seasons found that only **42.6%** of model-seasons ended in profit (worse than a coin flip), and whichever model won one season rarely stayed on top in the next. The models gave sensible, logical explanations for their trades, yet still lost money when making live directional calls.
- **ACM Survey of 47 LLM Trading Systems (October 2026):** Researchers audited 47 AI trading papers and live setups. Their main finding is the blueprint you should copy: **LLMs fail when acting as live click-traders, but they add real value UPSTREAM of the trade**. Putting the LLM in charge of reading news, writing and improving quantitative Python strategies, running backtests, and reviewing past mistakes worked much better than asking the LLM to stare at live candles and pick entries. Strict hard-coded risk controls were the biggest factor in preventing blowups.
- **Indian Market Reality (SEBI Studies & Local API Issues):**

- SEBI's August 2026 report on FY26 derivatives showed **87.7%** of individual F&O traders lost money (average loss of ₹1.17 lakh), and options accounted for **92%** of total retail losses. Worse, traders with portfolios under ₹1 lakh accounted for **70%** of all losses.
- Meanwhile, **99%** of institutional and prop-desk profits in Indian F&O came from ultra-fast algo entities. Over standard internet APIs, Indian algo users on Dhan and Zerodha regularly report execution slippage, unfilled limit orders during sudden spikes, and occasional order sync bugs.
- In **Equity Intraday**, SEBI found that **7 out of 10** individual traders lose money. That is still tough, though noticeably less punishing than options.

## 3. Your "Daily Profit Sweep" Idea: Smart Concept, Important Technical Catch
Locking daily profits so the bot only ever trades with a fixed ₹1,00,000 is actually a great risk-control idea. In trading, this stops an agent from getting overconfident after a lucky week, sizing up, and losing everything in one bad session.
However, there are two practical catches in India:

- **T+1 Settlement Rule:** You cannot withdraw intraday or options profit on the same evening. Under SEBI's T+1 settlement cycle, Monday's profit settles on Tuesday and can only be withdrawn after Tuesday evening. Losses, on the other hand, are deducted immediately on Monday. Also, neither Zerodha nor Dhan lets an API automatically transfer cash to your bank account for security reasons.
- **The Clean Workaround (Virtual Capital Cap):** Enforce the ₹1,00,000 cap in your Python risk engine (`MAX_CAPITAL = 100000`). Even if the broker account grows to ₹1,08,000, the code ignores the extra ₹8,000 when calculating trade sizes. Then, once a week (say Friday evening), you manually withdraw anything above ₹1,00,000 to your bank.
- **Do Not Auto-Top-Up Losses:** If the account drops from ₹1,00,000 to ₹90,000, avoid topping it back up to ₹1,00,000. Topping up hides real drawdowns and quietly turns a ₹1,00,000 experiment into a ₹1,50,000+ loss. Instead, force the bot to trade smaller with the remaining ₹90,000, and set a hard "pull the plug" floor (for example, stop the experiment if capital drops to ₹80,000).

## 4. Intraday vs. Options vs. a Mix: What Makes the Most Sense?
If you want daily action and fast learning loops without doing swing trading, here is how intraday equity and options stack up for an AI harness:

| **Factor** | **Equity Intraday (Cash Stocks)** | **Index Options Buying** |
| --- | --- | --- |
| **How Price Moves** | Clean, linear (stock goes up 1%, you make 1%) | Non-linear (time decay eats value every minute even if price stays flat) |
| **STT & Cost Drag** | Lower (0.025% STT on sell side) | High (**0.15%** STT on sell side in 2026) |
| **AI / Latency Tolerance** | Medium (a 5-second delay on a Nifty 50 stock is survivable) | Very low (options can jump 10-20% in seconds during volatility) |
| **Risk of Sudden Blowup** | Low if using strict stop-loss and 1x-2x leverage | Very high (a bad news candle can blow past your stop-loss) |
| **Best Use for ₹1,00,000** | **Best starting sandbox** for testing a self-learning AI harness | Only worth testing as a small Phase 2 add-on once the core harness works |

## 5. The Best Architecture Based on Research
Combining the research above with your goal of a self-learning Claude Code / Codex harness, the strongest setup is a **Two-Speed System**:

- **During Market Hours (9:15 AM to 3:15 PM): Pure Deterministic Python**

- Claude Code does **not** directly call `place_order` on live 1-minute candles.
- Instead, a lightweight Python script executes the currently active strategy rules via Dhan/Zerodha API, automatically attaches broker-side stop-losses and targets on every trade, caps trades at 2 to 3 per day, and triggers an automatic kill switch if daily loss hits ₹1,500 to ₹2,000 (1.5% to 2%).
- **Before and After Market Hours: Claude Code / Codex as the Self-Learning Brain**

- **8:30 AM (Pre-Market):** Checks overnight news, global cues, and earnings announcements to pick a clean watchlist of 5 to 10 liquid NSE stocks (or flags "high-risk day, reduce size").
- **4:00 PM (Post-Market Review):** Downloads the day's exact fills, slippage, brokerage, and PnL. Logs why each trade won or lost.
- **Weekly Evolution Loop (Weekend):** Claude Code reviews the week's trade journal, identifies failure patterns (for example, getting stopped out in the first 15 minutes of market open), writes an updated Python strategy in a new git branch, backtests it on the last 6 months of NSE intraday data, and presents a plain-English report for you to approve before Monday.

## Where Should We Go Next in Our Brainstorm?
To narrow down the exact spec before we draft the Project Dossier, let's align on two big design choices:
1. **Instrument plan:** Do you like starting Month 1 purely on **Equity Intraday** (liquid Nifty 100 stocks) to battle-test the stop-losses, API sync, and self-learning loop, and only unlocking a small **Options** sleeve in Month 2 if the system behaves reliably? Or do you want both live from Day 1?
2. **LLM role:** Are you on board with the **Two-Speed architecture** (Python executes live with hard stop-losses, Claude Code / Codex researches, codes, backtests, and updates the strategy daily/weekly), or were you specifically excited about testing an LLM making live intraday calls through MCP in real time?

---

So, I will be doing this from my account. Like my annual income is 4 lakh rupees, so I don't think it will be taxable up to 12 lakhs or something. You can check that one. Let's say if my annual income is 4 lakhs, then I don't think the basically trade swinging options work because I'm in a free tax lab, so none of these things will be taxable.

You actually caught a huge tax detail that flips the math completely in favor of intraday and options for your situation.
At a **₹4 lakh annual income**, **intraday and options profits are completely tax-free** for you up to a high limit, while **equity swing trading actually gets taxed at 20%**.

## 1. How the ₹12 Lakh Tax-Free Rule Works (FY 2026-27)
Under the New Tax Regime for FY 2026-27, there are two separate tax-free layers, and they treat trading styles differently:

- **Basic Exemption Limit (₹4 lakh):** The first ₹4 lakh of your income is taxed at 0%.
- **Section 87A Rebate (up to ₹12 lakh):** If your total taxable income is ₹12 lakh or less, you get a rebate of up to ₹60,000 that brings your final tax bill down to **₹0**.
- **The Critical Catch:** The Section 87A rebate **only covers normal slab-rate income** (like salary, freelance income, and trading business income). It **does not apply to special-rate capital gains**, such as equity swing profits taxed at 20%.

## 2. Tax Comparison at Your ₹4 Lakh Income
Assuming your regular taxable income is ₹4 lakh under the New Tax Regime:

| **Trading Style** | **Income Type** | **Tax You Pay on Trading Profits** | **ITR Form Needed** |
| --- | --- | --- | --- |
| **Equity Intraday** | Speculative Business Income | **₹0** (until total income crosses ₹12 lakh) | ITR-3 |
| **Options Trading (F&O)** | Non-Speculative Business Income | **₹0** (until total income crosses ₹12 lakh) | ITR-3 |
| **Equity Swing (under 1 year)** | Short-Term Capital Gains | **20% + 4% cess** from rupee one above your ₹4L basic limit | ITR-2 |

- **One small note if your ₹4 lakh is salary:** Salaried individuals get a ₹75,000 standard deduction under the New Tax Regime. That drops your taxable salary to ₹3.25 lakh, leaving ₹75,000 of basic exemption space before the 20% swing tax starts. Even then, intraday and options give you a much bigger tax-free runway (up to ₹8.75 lakh in trading profit).

## 3. Three Practical Rules You Still Need to Watch
Even with ₹0 income tax on intraday and options, three real-world rules still apply:

- **You still have to file ITR-3:** If your total income crosses ₹4 lakh (or if your bot ends in a loss and you want to carry that loss forward to future years), you must file **ITR-3** before the due date. Do not file ITR-1 or ITR-2 if you trade intraday or F&O.
- **No surprise CA tax audit:** Because broker trades are 100% digital, a tax audit is generally only triggered if your trading turnover crosses **₹10 crore** (assuming you have not opted out of presumptive taxation under Section 44AD in the last 5 years). Trading turnover is calculated as the sum of absolute profits plus absolute losses, not total trade value, so a ₹1 lakh account stays nowhere near ₹10 crore.
- **Brokerage and STT still leave your account daily:** Zero income tax does not stop transaction charges. Every trade still pays brokerage, GST, exchange charges, and STT. Remember that STT on selling options was raised to **0.15%** from April 1, 2026, which makes overtrading options expensive for a ₹1 lakh balance.

## 4. What This Means for Your Experiment Design
With taxes out of the way, **skipping swing trading and focusing on Intraday Equity and Options makes complete sense** for your account.
Now our decision is purely about **engineering and survival**, not taxes. Before we draft the Project Dossier, let's lock in two choices:
- **Choice 1: Pure Intraday first, or Intraday + Options together?**

- **Option A (Safer rollout):** Run Month 1 on **Equity Intraday** only (top liquid Nifty 100 stocks) so the AI learns clean price moves and proves its stop-losses work, then unlock a small **Options** budget in Month 2.
- **Option B (Mix from Day 1):** Split your ₹1,00,000 cap right away, for example ₹70,000 for Equity Intraday and ₹30,000 for Index Options buying, with strict trade limits on both.
- **Choice 2: How should Claude Code / Codex control trades?**

- **Two-Speed Setup (Recommended by research):** A hard-coded Python script executes live entries, stop-losses, and the daily loss kill switch during market hours (9:15 AM to 3:15 PM), while Claude Code or Codex runs before market open, after market close, and on weekends to analyze trades, refine the strategy code, and backtest updates.
- **Direct Live MCP Agent:** Claude Code or Codex actively checks the market via Dhan or Zerodha MCP every 15 to 30 minutes during live hours and triggers orders through a safety-checked wrapper.