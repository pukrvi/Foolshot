# Data, tools, and strategy posts

## Haseeb Badar · NSE data workflow · 14 November

The bookmark is a reply labeled Step 1. His instructions were to open NSE’s equity archives, pick the symbol-level price, volume and delivery series, and export one year as CSV. He also pointed to historical Nifty 50 data for index comparisons. The individual post opened in X. Its parent and the indicated reply did not load in the views available for this collection. [Bookmarked reply](https://x.com/hb_stocks/status/2121551250361835664) · [Illustration](https://x.com/hb_stocks/status/2121551250361835664/photo/1) · [NSE archives](https://betanseapi.nseindia.com/resources/historical-reports-capital-market-daily-monthly-archives)

## AI / Tech · Claude Trading Skills · 18 November

@chatgptricks credited tradermonty for a collection of workflows covering market and chart research, stock screens, historical strategy tests, and portfolio review. The source repository and its skill files are included in the resource folder. One reader asked whether the journal could import broker fills. A second emphasized commission and slippage when interpreting backtests. No author answers appeared in the visible reply stream. [Post](https://x.com/chatgptricks/status/2123002615000936824) · [Import question](https://x.com/_HelloPurple_/status/2123327528760983741) · [Cost comment](https://x.com/0xSpeter/status/2123024205650575734) · [Repository](https://github.com/tradermonty/claude-trading-skills)

## bodila · LEAPS benchmark · 15 November

The post discussed a benchmark where long inputs exposed gaps between recalling one fact, tracking state changes, and learning patterns. It highlighted a market dataset, a simulated order book, and prediction from social posts. Proposed design choices included keeping position and order state in code, compressing numeric inputs, asking narrow questions, logging token use, retesting model changes, and comparing against a simple baseline and a no-trade outcome. The original LEAPS paper is included. Its 12 datasets and 30 evaluated models support the benchmark framing. The post’s claimed 99% trading-agent failure rate is not a finding established by the benchmark. [Post](https://x.com/51bodila/status/2121779229729677816) · [Post mirror](https://nitter.cf/51bodila/status/2121779229729677816) · [Paper](https://arxiv.org/abs/2610.25919)

## bodila · Ten-repository roundup · 16 November

The list starts with data and analysis, then covers backtesting, agent evaluation, and execution examples. All ten named projects have a local source copy. The roundup quotes the author’s longer six-agent desk guide, which has its own offline notes. Visible comments included one endorsement of NautilusTrader for backtest/live code parity, Freqtrade for dry runs, OpenBB for data, and GS Quant for volatility tooling. [Post and comments](https://x.com/51bodila/status/2122076270942892034) · [Offline resource index](../resources/INDEX.md) · [Guide notes](../articles/bodila-six-agent-desk.md)

## ludoonchart · BTC moving-average replay · 21 November

The author reported a paper replay on 720 daily Kraken Bitcoin bars. The rule used a 20/50-day simple moving-average crossover with both long and short positions. Signals were computed at the close, filled at the next open, and charged five basis points per side. The author reported +33.1% for the rule versus −32.4% for holding, 31.6% maximum drawdown versus 53.1%, and eight winners across 18 closed trades. Only 32 of 192 combinations ended above zero. He attributed part of the selected rule’s result to short exposure during a falling market. Exact test dates and the replay code were not supplied in the post. [Post](https://x.com/ludoonchart/status/2123898954211553534)

**Author reply.** He clarified that GS Quant and J.P. Morgan Python Training were learning references. His separate backtester produced the figures. Both references are saved, and the quoted paper-terminal guide has its own notes. [Author reply](https://x.com/ludoonchart/status/2123902987877625918) · [Guide notes](../articles/ludoonchart-paper-terminal.md)
