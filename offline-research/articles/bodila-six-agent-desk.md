# bodila’s six-agent paper-trading desk

The October 2026 guide describes a U.S. stock workflow run by six GrokBot roles. It was quoted in the LEAPS post and the ten-repository roundup. The author's Jane Street comparison is their framing. The article describes an independent desk setup. [Original X post](https://x.com/51bodila/status/2110409939600462238) · [Full article mirror](https://nitter.cf/51bodila/article/2110409939600462238)

| Role | Responsibility described |
| --- | --- |
| Scout | Scans SEC filings and other public sources. Records candidates and why others were excluded. |
| Analyst | Produces a fair-value card per candidate and documents price, rationale and risks. |
| Quant | Writes and tests rules in a versioned directory. Sets aside a holdout and documents test results. |
| Skeptic | Challenges candidates and audits code and tests independently. Checks for leakage, changed tests and repeated holdout use. |
| Risk | Turns accepted candidates into paper-order tickets. Rejects tickets that fail code-level limits and sends tickets for human approval. |
| Journal | Records fills, misses, rejected tickets and vetoes. Compares observed performance against the backtest and flags decay. |

## Strategy example in the guide

The proposal looks for publicly filed Form 4 open-market purchases of at least $100,000 by high-ranking executives at liquid U.S. stocks. It filters out likely compensation batches and sets a $20 million average daily dollar-volume floor. The historical test uses the next open after public filing, a stop two ATRs below entry, and a five-session exit. The proposed order ticket uses a day limit at 0.5% above the previous close. The article distinguishes testing the authors’ filters from first checking the source study’s result. It flags survivorship bias from yfinance and calls for counting missing prices. [SEC dataset](https://www.sec.gov/dera/data/form-345) · [Event study](https://blog.quantinsti.com/sec-form-4-insider-trading-python-event-study/)

## Workflow and replies

The written sequence is market scan, valuation, independent review, risk check, manual approval, and journal review. The example uses paper Alpaca and suggests position count, position size, and daily-loss caps in a separate config. There are pause and kill files in the design. Its review compares actual versus simulated results and asks whether the Skeptic’s vetoes helped.

The author replied that they had run the system since Opus 5.5 released. They also said the article explains an optional Jev integration. Readers asked who handles disagreements overnight and suggested giving the veto agent an independent data snapshot. A commenter named the open-source bt library as another backtest option. [X post and replies](https://x.com/51bodila/status/2110409939600462238) · [Reply mirror](https://nitter.cf/51bodila/status/2110409939600462238)
