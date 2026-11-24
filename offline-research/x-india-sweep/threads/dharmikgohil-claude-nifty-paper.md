# Dharmik Gohil — Claude paper-trading ₹1,00,000 on NIFTY options

Verbatim thread from [@dharmikgohil_](https://x.com/dharmikgohil_/status/2062025929514426803), posted 3 June 2026. The author describes a one-day paper-trading session in which Claude Opus 4.8 was given ₹1,00,000, NIFTY options, live market data and a Zerodha account.

**Source:** [X thread](https://x.com/dharmikgohil_/status/2062025929514426803), copied 22 November 2026 from the signed-in X session. Text is verbatim, including the author's line breaks and punctuation. Each post in the thread has its own numeric ID.

**Author-reported:** this is the author's account of a paper-trading exercise. It is not a live-money result and no broker statement or P&L link was posted. The author does not state the final account balance after the last trade.

| # | Date shown on X | Link |
|---|---|---|
| 1 | 3 June 2026 (thread root) | [2062025929514426803](https://x.com/dharmikgohil_/status/2062025929514426803) |
| 2 | Jun 3 | [2062025932806955181](https://x.com/dharmikgohil_/status/2062025932806955181) |
| 3 | Jun 3 | [2062025935403266353](https://x.com/dharmikgohil_/status/2062025935403266353) |
| 4 | Jun 3 | [2062025937722765793](https://x.com/dharmikgohil_/status/2062025937722765793) |
| 5 | Jun 3 | [2062025940100915688](https://x.com/dharmikgohil_/status/2062025940100915688) |
| 6 | Jun 3 | [2062025942541984111](https://x.com/dharmikgohil_/status/2062025942541984111) |
| 7 | Jun 3 | [2062025945234682295](https://x.com/dharmikgohil_/status/2062025945234682295) |

---

## Post 1

*3 June 2026 · [source](https://x.com/dharmikgohil_/status/2062025929514426803)*

> So yesterday I gave Claude Opus 4.8 ₹1,00,000 for paper-trading and told it to trade NIFTY options from 9:15 AM to 3:30 PM.
>
> With some trading skills!
>
> and just access to live market data and a Zerodha account.
>
> What happened next perfectly explains why most traders lose money.

## Post 2

*Jun 3 · [source](https://x.com/dharmikgohil_/status/2062025932806955181)*

> The AI's first trade was terrible.
>
> It saw momentum.
> Jumped in.
> Got stopped out.
> −₹9,204.
> Account down 9%.
>
> If you've traded before, you know what usually comes next:
>
> "Need to make it back."
>
> The AI did something different.
>
> Nothing.

## Post 3

*Jun 3 · [source](https://x.com/dharmikgohil_/status/2062025935403266353)*

> For the next 90 minutes it just watched.
>
> No averaging.
> No revenge trade.
> No random entries because the market was moving.
> Then it found a setup it actually liked.
> Not the breakout.
>
> The retest after the breakout.
>
> One trade.
>
> +₹10,403.
>
> The entire loss recovered.

## Post 4

*Jun 3 · [source](https://x.com/dharmikgohil_/status/2062025937722765793)*

> At that point the experiment was proving something interesting.
>
> The AI wasn't making money because it was smart.
>
> It was making money because it was patient.
>
> Then I ruined it.
>
> I told it:
>
> "Trade more."

## Post 5

*Jun 3 · [source](https://x.com/dharmikgohil_/status/2062025940100915688)*

> Within minutes it started behaving exactly like a human trader.
>
> A quick scalp.
>
> A forced entry.
>
> A trade that looked good for 30 seconds.
>
> A fake breakout.
>
> Small losses everywhere.
>
> Nothing catastrophic.
>
> Just death by activity.

## Post 6

*Jun 3 · [source](https://x.com/dharmikgohil_/status/2062025942541984111)*

> By afternoon all the profits from the good trade were gone.
>
> Not because the market changed.
>
> Not because the strategy failed.
>
> Because it stopped waiting.

## Post 7

*Jun 3 · [source](https://x.com/dharmikgohil_/status/2062025945234682295)*

> Then I gave it one final instruction:
>
> "Either win big or lose it all."
>
> 13 minutes before expiry it bought a lottery-ticket option.
>
> Risk: ₹4,550
>
> Potential upside: ridiculous.
>
> The kind of trade every trader secretly dreams about.
>
> The option expired at zero.

## Notes

Commentary for Foolshot.

- **Result as reported.** First trade stopped out for −₹9,204 (account "down 9%"). After a 90-minute pause the AI took one retest trade for +₹10,403 and recovered the loss. The author then instructed it to "trade more" and reports the profits went back to zero through small forced trades. A final instruction to "either win big or lose it all" produced a lottery-ticket option bought 13 minutes before expiry, risking ₹4,550, which expired at zero.
- **The lesson the author draws** is about patience versus forced activity: the AI made money while it waited and lost it when told to trade. For Foolshot this is an argument for a deterministic trade-count or no-trade gate that a chat instruction cannot widen, and for logging the instruction that preceded each order.
- **Paper-only.** The exercise is explicitly paper-trading; it says nothing about slippage, fills, brokerage or margin in live NIFTY options. Foolshot's replay needs the bazaar-trader honest-fill method (first print after signal, ₹0.50 option slippage, full NSE charges) before this behaviour can be scored.
- **Option-buying lottery tickets.** Risking ₹4,550 on a 13-minutes-to-expiry option is the kind of trade the archived Pranjal audit found to be negative after costs. Foolshot's sizing and stop rules should make this trade impossible by construction (minimum time-to-expiry, maximum premium at risk, deterministic loss cap).
- **Dating.** The thread is from 3 June 2026, five months before the November sweep window; it is included because it is one of the cleanest public descriptions of model behaviour under a human instruction change, not because it is current evidence about the November market.

Raw capture: [`snapshots/posts/dharmikgohil-claude-1L-paper/`](../snapshots/posts/dharmikgohil-claude-1L-paper/).
