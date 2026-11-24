# ludoonchart’s self-improving paper terminal

The November 2026 guide describes a Claude Code project that proposes and filters trade rules. The walkthrough uses Kronos for forecasts, DSPy for prompt tuning, and mem0 for prior failures. It also references RD-Agent, GS Quant, magic-trace, and daily_stock_analysis. Their source trees are included in the resource index. [Original X post](https://x.com/ludoonchart/status/2120258414542573669) · [Full article mirror](https://teapaw.org/ludoonchart/article/2120258414542573669) · [Resource index](../resources/INDEX.md)

## Walkthrough by section

1. Write ground rules and a plan for a paper-only project. Keep test data locked and require actual script outputs.
2. Fetch OHLCV bars from Kraken and split them by date into train, validation, and final test windows.
3. Backtest moving-average crossovers, z-score mean reversion, and Kronos forecasts as competing rule families. Trigger at a bar close and fill at the next open. Include two basis points each way in this article’s example.
4. Apply a separate gate before recording a candidate as passed. The demo requires positive train and validation returns, a gap of at most two percentage points, validation drawdown of at most 1.5%, and two or more validation trades. The test window stays locked at this point.
5. Record the exact cause of rejection and its figures in mem0. Read earlier failures before proposing the next batch.
6. Use DSPy to tune the proposal prompt on train and validation, with a 20-trial cap. Compare changes on both windows and flag gains limited to training.
7. Show the data windows, strategy scores, gate decisions, paper results, veto reasons and stop control in a dashboard.
8. Repeat candidate generation, backtesting, gating, journaling and prompt tuning.
9. Rerun on longer history, check timing sensitivity, and decide whether a final holdout run is warranted.

## Reported run and replies

The walkthrough reports 560 five-minute ETH/USD bars from Kraken for 7–9 November. It generated 18 candidates, none passed, and the terminal remained in paper mode. A reader reported that EMA and z-score candidates did not earn enough to cover costs in their check. The BTC moving-average replay from 21 November is a separate demonstration with different data and fees. [Guide discussion](https://teapaw.org/ludoonchart/status/2120258414542573669) · [BTC replay](https://x.com/ludoonchart/status/2123898954211553534)
