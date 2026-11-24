# Historical market data

This store supports read-only research preparations. The registered experiment is Monday, 23 November 2026, with an exclusive cutoff at 2026-11-23 00:00:00 IST (22 November 18:30 UTC). The earlier daily signal used 22 November 23:59:59 IST. That earlier timestamp can be supplied with `--cutoff 2026-11-22T23:59:59+05:30` when reproducing that experiment.

Two read paths are deliberately separate:

- **Strict evidence** uses only rows with a verified publication timestamp. Every daily archive row loaded so far has `availability=unknown`, so strict queries currently return only the small set of dated macro/news records. This is the replay-safe path.
- **Research inspection** returns the latest stored source rows regardless of availability and marks them `not_point_in_time`. Use it to study, chart, backtest and validate the dataset; never pass it to a replay packet.

## Loaded coverage (measured 2026-11-24)

| Dataset | Window | Rows | Sessions | Source |
|---|---|---:|---:|---|
| `equity_daily` | 2023-11-23 → 2026-11-20 | 1,794,652 | 743 | TejHQ NSE parquet |
| `equity_daily` (outcome only) | 2026-11-23 | 3,755 | 1 | NSE CM archive, excluded from history |
| `equity_daily` (inferred) | 2026-11-19/20 | 2 | 2 | saved RELIANCE preparation |
| `equity_delivery` | 2023-11-23 → 2026-11-20 | 1,595,125 | 743 | TejHQ NSE parquet |
| `corporate_actions` | 2023-11-23 → 2026-11-20 | 6,586 | 638 ex-dates | TejHQ NSE parquet |
| `listings` | intervals to 2026-11-23 | 3,592 | — | TejHQ symbol history |
| `derivatives_daily` | 2025-11-24 → 2026-11-20 | 9,906,015 | 247 | NSE F&O UDiFF bhavcopy |
| `indices` | 2023-11-23 → 2026-11-20 | 100,518 | 743 | NSE index close archive |
| `macro` | 2021-11-22 → 2026-11-20 | 2,513 | 1,259 | Federal Reserve H.10, EIA |
| `news` | 2026-11-22 | 1 | 1 | Economic Times metadata |
| `economic_events` | 2026-11-06 | 1 | 1 | BLS release metadata |

`derivatives_daily` contains 9,747,614 option rows and 158,401 futures rows across 243 underlyings, including expired contracts. The largest underlyings are NIFTY (437,379 rows), NIFTYNXT50 (266,713), BANKNIFTY (253,986), MIDCPNIFTY (203,701) and FINNIFTY (126,375). `indices` carries 175 index series, including Nifty 50, Nifty Bank, Nifty 500, sector indices and India VIX.

The database is `market.sqlite3` (about 11 GB) with 1,014 verified raw source hashes. Raw archive bytes occupy about 320 MB and are content-addressed under `raw/`.

## Reproduction commands

Run these from the market-data code worktree. Point `market_root` at the original checkout's Git-ignored directory. Use a private umask.

```sh
umask 077
market_repo=/Users/vishmac/Documents/GitHub/Foolshot
market_root="$market_repo/data/private/market-data"
intake="$market_repo/data/private/monday-20261123-intake"
uv venv --python 3.12
uv pip sync requirements.lock
export PYTHONPATH=src

# 3 years of NSE cash daily, delivery, actions and symbol history
.venv/bin/python -m foolshot.market_equity --root "$market_root" --tejhq-dir "$market_root/sources/tejhq"

# 1 year of every NSE F&O contract, options and futures, including expired series
.venv/bin/python -m foolshot.market_nse_archive --root "$market_root" --kind fo \
  --start 2025-11-24 --end 2026-11-22 --delay 1.2 \
  --report "$market_root/reports/options-daily-20261124.json"

# 3 years of index closes, including India VIX and sector indices
.venv/bin/python -m foolshot.market_nse_archive --root "$market_root" --kind indices \
  --start 2023-11-23 --end 2026-11-22 --delay 1.2 \
  --report "$market_root/reports/index-daily-20261124.json"

# Context, Monday outcome, validation and evidence packet
.venv/bin/python -m foolshot.market_fx --root "$market_root"
.venv/bin/python -m foolshot.market_equity "$intake/nse-alt.zip" --root "$market_root" --outcome-only \
  --source "NSE official CM bhavcopy (existing intake copy)" \
  --url https://archives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20261123_F_0000.csv.zip
.venv/bin/python -m foolshot.market_derivatives --root "$market_root"
.venv/bin/python -m foolshot.market_validate --root "$market_root" \
  --output "$market_root/reports/coverage-20261123.json"
.venv/bin/python -m foolshot.market_evidence --root "$market_root" packet \
  --output "$market_root/reports/pre-session-20261123.json" \
  --preparation "$market_root/reports/preparation-20261123.json"
.venv/bin/python -m unittest discover -s tests -v
```

The NSE archive collector is resumable and idempotent:

- Every completed HTTP response is checkpointed by URL hash in `checkpoints/`; a rerun reuses the verified blob without a request. `--refresh` re-fetches and retains both hashes.
- Each daily file becomes one receipt keyed by dataset, source, URL and raw SHA-256. Re-importing an unchanged file adds zero rows.
- `--download-only` and `--import-only` split acquisition from normalization. Per-object failures are recorded in the report and do not stop the remaining sessions.
- The session list is derived from the already imported cash history, so exchange holidays are not guessed. Both archive runs report zero missing sessions against that reference.

## Queries

Strict, cutoff-enforced evidence:

```sh
.venv/bin/python -m foolshot.market_evidence --root "$market_root" --symbol USDINR query macro --limit 5
```

Research inspection, including rows whose publication time is unknown:

```sh
.venv/bin/python -m foolshot.market_evidence --root "$market_root" --symbol NIFTY query derivatives_daily --limit 5 --all-availability
.venv/bin/python -m foolshot.market_evidence --root "$market_root" --symbol NIFTY chain --session 2026-11-20 --limit 20
.venv/bin/python -m foolshot.market_evidence --root "$market_root" --symbol NIFTY chain --session 2026-11-20 --expiry 2026-11-26 --limit 200
.venv/bin/python -m foolshot.market_evidence --root "$market_root" --symbol "Nifty 50" query indices --limit 5 --all-availability
```

Python helpers:

- `market_store.observations(root, dataset, cutoff, ...)` — strict, version-resolved evidence.
- `market_evidence.research_observations(root, dataset, ...)` — latest source rows, marked `not_point_in_time`.
- `market_evidence.research_chain(root, symbol, session, expiry=None, limit=500)` — end-of-day option chain from stored contract rows.
- `market_evidence.end_of_day_chain(...)` — strict chain; empty while archive availability stays unknown.
- `market_evidence.completed_sessions`, `price_volume_trend`, `relative_strength`, `equity_breadth`, `observed_universe`, `listed_universe`.

## Storage and data dictionary

- `raw/<sha-prefix>/<sha>` stores the original bytes by SHA-256. `checkpoints/` records acquisition, HTTP status, ETag/Last-Modified and content hashes for resumable sources. `sources/` holds provider-native Parquet files staged for local import.
- `market.sqlite3` holds normalized observations and source receipts. A receipt identifies the source, URL, immutable raw SHA, acquisition UTC, byte and row counts, and the outcome-only flag.
- Each observation has a stable record key within its source and dataset. It stores date, symbol, original offset-bearing event and availability timestamps, normalized UTC instants, availability classification and rationale, and dataset-specific values.
- Equity observations keep the provider's unadjusted OHLC and previous close, quantities and turnover. The NSE UDiFF adapter preserves integer paise and reports delivery separately. Symbol intervals in a derived snapshot do not establish official listing or delisting dates.
- `derivatives_daily` values: `contract_id`, `symbol`, `expiry`, `strike`, `option_type` (`CE`/`PE`; absent on futures), `instrument_type` (`IDO`/`IDF`/`STO`/`STF`), `contract_name`, unadjusted `open`/`high`/`low`/`close`, `last_price`, `previous_close`, `settlement`, `underlying_price`, `volume`, `turnover_rupees`, `trades`, `open_interest`, `oi_change`, `lot_size`. The record key is `<FinInstrmId>|<session>`.
- `indices` values: `open`, `high`, `low`, `close`, `points_change`, `change_pct`, `volume`, `turnover_crore`, `pe`, `pb`, `div_yield`. Dividend-point series can carry a close without OHLC.
- Contracts, candles, actual trades, quotes, and snapshots are separate datasets. The chain helper assembles eligible daily contracts and identifies the result as end-of-day. Each provider export is responsible for contract IDs, quote sizes, minute bar boundaries and native units.
- The strict reader filters by release eligibility before choosing the latest version for each logical record and provider. Conflicting values at the same latest timestamp are excluded. Outcome-only files never enter preparation. Dated versions already available at the cutoff remain eligible when later corrections are present.

## Validation results

`reports/coverage-20261123.json` records the run:

- SQLite integrity `ok`; 1,014 raw hashes verified; no receipt count mismatches.
- No missing sessions for equity, delivery, derivatives or indices against the 743-session cash reference.
- 108 of 9,906,015 derivatives rows carry a source OHLC exception, all stock futures whose reported close falls just outside the reported high/low (for example 1213.40 close against a 1213.60 low). They are preserved unadjusted and reported, not silently corrected.
- 4 of 100,518 index rows show the same source inconsistency for `Nifty50 USD`; no parsing defect was found.
- No duplicate natural keys; every derivative batch is keyed by contract id and session. Re-importing unchanged archives adds zero rows.
- Untestable without additional sources: official segment calendar, exchange listing/delisting dates, intraday completeness, historical contract/lot masters, and independent provider parity.

`reports/archive-publication-times.json` records the HTTP `Last-Modified` value captured with each of the 990 archive downloads. All 247 F&O files and all 743 index files report a modification time before the 2026-11-23 cutoff (F&O files around 19:20 IST on the session date, index files around 23:20 IST). These are server object-modification times, not verified first-publication receipts, so the observations remain `availability=unknown`. The report gives the owner the evidence needed to decide whether to accept them as inferred availability for a research replay; the strict path will keep excluding them until that decision is recorded.

## Sources and gaps

TejHQ permits private personal research and local storage under its published data terms. The code license does not license the underlying data, exchange terms remain applicable, and republishing raw files is restricted. [TejHQ data terms](https://tejhq.dev/data-terms)

The NSE daily F&O and index archives are public exchange objects. NSE's website terms restrict systematic collection and redistribution, and its research-data policy distinguishes free daily reports from chargeable voluminous history. This collector fetches only the reviewed daily objects at a polite rate, keeps them local for private research, and records source URLs and hashes. No subscription, trial, credential or order operation is involved. [NSE terms](https://betanseapi.nseindia.com/static/nse-terms-of-use) · [NSE research data list](https://www.nse.in/static/research/initiatives-data-for-research)

Daily archives do not expose a per-file publication timestamp, so the rows remain `unknown` availability and cannot pass the strict replay filter. Closing that gap needs dated publication receipts or an authorized provider with historical timestamps, not a parser change.

Still missing from the original request:

- One year of one-minute OHLCV for Nifty 50 constituents, Nifty, Bank Nifty and expired options.
- Genuine historical bid/ask quotes, displayed sizes and intraday option-chain snapshots.
- Historical contract specifications and lot-size change masters.
- Three years of derivatives daily (the current acquisition is the requested one-year options scope).
- Official exchange calendars and verified listing/delisting records.

The Federal Reserve H.10 releases are public-domain board data and publish at 16:15 New York time. The 23 November release is retained as a later version and excluded from the packet. The contemporaneous WPSR artifact records WTI and its source header. Only metadata was retained for the saved Economic Times news item. [Federal Reserve terms](https://www.federalreserve.gov/disclaimer.htm) · [H.10 release schedule](https://www.federalreserve.gov/data/releaseschedule.htm) · [EIA policy](https://www.eia.gov/about/copyrights_reuse.php)
