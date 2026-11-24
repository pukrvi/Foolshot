# Shivansh Mehendiratta’s Dhan experiment

Source notes from @shivanshco, 27 October to 4 November 2026. The figures below are the author’s reports. Dhan P&L posts are linked from the original threads.

| Session | Date | Gross reported | Net reported | Source |
| --- | --- | --- | --- | --- |
| Day 1 | 27 Oct | — | +₹4,400 | [X](https://x.com/shivanshco/status/2115064439972249723) · [Thread mirror](https://teapawt.net/shivanshco/status/2115064439972249723) |
| Day 2 | 28 Oct | +₹11,000 | ~+₹9,500 | [X](https://x.com/shivanshco/status/2115359943004217707) · [Thread mirror](https://teapawt.net/shivanshco/status/2115359943004217707) |
| Day 3 | 29 Oct | +₹11,500 | ~+₹11,200 | [X](https://x.com/shivanshco/status/2115709430558019896) · [Thread mirror](https://teapawt.net/shivanshco/status/2115709430558019896) |
| Day 4 | 30 Oct | +₹10,400 | ~+₹8,500 | [X](https://x.com/shivanshco/status/2116088713952583757) · [Thread mirror](https://teapawt.net/shivanshco/status/2116088713952583757) |
| Day 5 | 4 Nov | −₹3,100 | ~−₹5,000 | [X](https://x.com/shivanshco/status/2117925681967595543) · [Thread mirror](https://teapawt.org/shivanshco/status/2117925681967595543) |

## Day 1

1. He funded ₹1 lakh, offered Dhan or Zerodha, and said Claude chose Dhan for its API. The API plan cost ₹499 per month. The stated target was ₹10,000 per day.
2. He shared his trading style and gave Claude discretion to research and execute when the market opened.
3. Claude backtested overnight. A broker token problem blocked roughly half the session. He supplied a fresh token after waking.
4. The author described at-the-money option buying based on price action and range breakouts, with stops, targets, and intended 20% position sizing. The first trade made about ₹3,500. The second hit its stop. He said Claude adjusted for overly tight trailing stops.
5. The account reportedly reached about ₹9,500 intraday profit before giving some back. He ended around 2:45 p.m. on expiry day, with roughly ₹4,400 after charges.

**Replies.** Nakul Bhardwaj recommended OpenAlgo. Shivansh said he might try it. @SSManambrakat questioned the stated 20% sizing based on apparent premium exposure. Shivansh distinguished day trading and scalping from research that would use corporate filings. He also pointed to avoiding revenge trades as one positive. The thread links days 2, 3, and 4. [Thread and replies](https://teapawt.net/shivanshco/status/2115064439972249723)

## Day 2

1. Claude preferred to skip a non-expiry day. The author told it to trade because Sensex expiry was one day away.
2. An IP/token mismatch delayed the start until about 11:30 a.m. Dhan’s interface showed a five-day wait before another primary-IP reset. He considered using a static IP.
3. The bot sized larger from its first trade and exited some positions early. He attributed much of the day’s result to a Sensex 73300 put bought on a downside break at 13:23 and exited at 13:25.

**Author replies.** He clarified that Dhan had grouped three trades with quantities of 140, 120, and 120. He described roughly ₹45,000 in position size. He confirmed the trades were option buys, said he had made few setup changes, and estimated using about 10–20% of the Fable allowance on Claude Max. [Sizing](https://x.com/shivanshco/status/2115446764975387129) · [Option buying](https://x.com/shivanshco/status/2115370882667553260) · [Model usage](https://x.com/shivanshco/status/2115445225653141767)

## Day 3

1. He prompted Claude to search for stronger ideas overnight. Claude reportedly tested hundreds of thousands of 15-minute breakout variations and picked an expiry-specific rule set from 108 expiry sessions over two years. He questioned whether that sample meant much.
2. Connectivity held. A false breakout at 09:40 cost ₹4,327. The next trade, at 10:07 on the same 73500 call, returned ₹15,591 over 19 minutes.
3. He reported about ₹25,000 cumulative profit and considered skipping the next session without a suitable two-days-to-expiry strategy.
4. After readers including Pranjal asked for broker evidence, he posted a Dhan P&L link. He said he did not think he could generate links for prior days. In another branch, he asked a paper trader about their Sensex scalping setup. That commenter reported testing gamma spikes and losing back part of the gain on a short. [Thread and replies](https://teapawt.net/shivanshco/status/2115709430558019896)

## Day 4

1. Friday and two-days-to-expiry research explored patterns, stop, target and sizing grids, entry filters, and gradient-boosting models. He said the research did not produce a strong candidate.
2. The system still ran short-hold 15-minute breakout scalps. He said trailing exits left some of the day’s larger moves uncaptured. Roughly 13 trades cost about ₹2,000 in taxes and fees.
3. The author put four-day cumulative net profit near ₹33,500 and considered increasing expiry-day capital. He linked that idea to the perceived expiry edge and high VIX.
4. He shared a Dhan P&L link. In replies, he said he generally used Opus 5.5 for coding and had yet to compare its trading results with Fable. He also explained that Day 1 served as a thread index. A commenter reported a separate Opus paper experiment with losses on both option buying and an iron fly. [Thread and replies](https://teapawt.net/shivanshco/status/2116088713952583757)

## Day 5

1. A move and unfinished Mac mini setup kept him out of the prior two sessions. He resumed after midday once Wi-Fi was installed. [Bookmarked author reply](https://x.com/shivanshco/status/2117925684979122509)
2. He blamed tight trailing and repeated stop-outs for a rough session. Fifteen trades in roughly two and a half hours hit the trade-count cap before the daily loss cap. [Author reply](https://x.com/shivanshco/status/2117925687143411886)
3. He described the non-expiry rules as growing into a collection of weakly supported conditions. He raised the possibility of overfitting and said he had asked Claude to trade anyway. [Author reply](https://x.com/shivanshco/status/2117925689550942670)
4. He felt less personal stress and self-blame than when trading manually. [Author reply](https://x.com/shivanshco/status/2117927752540327960)
5. He reported roughly ₹28,500 cumulative net over five sessions, discussed adding another ₹1 lakh for expiry sessions, and posted Dhan P&L. Those were plans as described on that date. [Totals](https://x.com/shivanshco/status/2117927794177126504) · [P&L post](https://x.com/shivanshco/status/2117927979678605406)
6. In replies, he said he expected losing days and characterized avoiding an account liquidation day as important. @SSManambrakat reported a separate paper/live experiment using five years of one-minute Nifty data. They said expiry-afternoon momentum was the only consistently positive direction in their tests. Gap fades, first-hour trend, and pre-event straddles were weak after costs. They also estimated ₹3,000–₹5,000 of charges and slippage for 15 round trips. @webiyo suggested Ebitta’s stock screener. [Discussion](https://teapawt.org/shivanshco/status/2117925681967595543)

## Bookmark text supplied by Puneet

> I let fable 5.1 trade nifty weekly options on a 1L account and asked it to make me 10k a day
>
> Today was day 1 🧵

> Day 2 of letting fable 5.1 trade my 1L account
>
> +11k gross, ~9.5k after charges 🧵

> Day 4 of letting fable 5.1 trade my 1L account
>
> +10.4k gross, ~8.5k after charges 🧵

> Didn't trade monday and the juicy nifty expiry cause i moved places and didnt have the mac mini setup
>
> Even today started after ~12pm the moment after i had the wifi installation done lol
