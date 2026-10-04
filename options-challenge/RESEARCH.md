# Strategy Research — 2026-09-23

Goal: find an options strategy that is profitable **out of sample**, for a small Webull account.

## Data
- Webull 5-minute bars, regular hours, **Sep 2025 → Sep 2026** (262 full days) for SPY, QQQ, IWM,
  TSLA, NVDA, AMD, PLTR, META, AAPL, AMZN — about 206,000 bars.
- Webull daily bars **Dec 2021 → Sep 2026** for the same 10 tickers.
- No historical option prices are available, so options are priced with Black-Scholes:
  - same-day expiry: IV = 20-day *intraday* realised vol × premium; multi-day: 20-day close-to-close vol × premium
  - premium tested at **1.0×, 1.1×, 1.15×, 1.3×, 1.5×** so no conclusion depends on one guess
  - bid/ask cost on every leg, plus an opening IV premium and higher IV on gap days
- Every idea is judged on a **train period** (older data) and then a **test period** it never saw.
  Intraday: train Sep 2025–Apr 2026, test May–Sep 2026. Daily: train 2022–2024, test 2025–2026.

## Part 1 — Same-day (intraday) option buying: no edge found

| Test | Result |
|---|---|
| Direction screen, 50+ intraday signals (ORB 5/15/30, gaps, VWAP, prior-day levels, power hour, intraday momentum) | Only one held up: **stock gap + 15-min ORB in the gap direction** (+12–15 bps over 30–60 min in both periods) |
| That signal as long options / debit spreads, 162 variants | Loses after costs in the test period at every realistic cost level |
| 34,160 filter combinations × 4 entry types, selected on train | At 1.15× IV: 11 passed train, **0** profitable on test. At 1.0× IV (most favourable to buyers): 139 passed train, 1% profitable on test |
| Power hour (buy cheap options into the close) | Lost on every signal |

Conclusion: short-dated options are priced for moves about as big as the ones that actually happen,
so small directional edges from chart patterns are eaten by time decay and the bid/ask. The
"first 15 minutes / last 15 minutes" style of buying calls/puts **did not make money** in a year of data.

## Part 2 — Multi-day signals: one robust edge

RSI(2) mean reversion (Larry Connors), a published and widely-tested effect:

**Buy when RSI(2) < 10 and price > 200-day SMA; exit when close > 5-day SMA (max 5 days).**

| Underlying only | Train 2022–24 | Test 2025–26 |
|---|---|---|
| SPY | 25 trades, 80% win, +0.65% | 18 trades, 83% win, +0.86% |
| QQQ | 22, 73%, +1.01% | 18, 78%, +0.83% |
| IWM | 17, 59%, −0.24% | 21, 81%, +0.98% |
| ETFs, thresholds 5 to 30 | positive at every threshold | positive at every threshold |
| ETFs, no trend filter (incl. 2022 bear market) | 76% win, +0.77% | 84% win, +1.18% |

**Best option expression: bull put credit spread** (sell put just below price, buy put 1–5 dollars
lower, ~5 trading days to expiry, close at the signal exit):

| Spread | IV 1.1× train / test | IV 1.3× train / test | IV 1.5× train / test |
|---|---|---|---|
| $2 wide, 5 DTE (risk ≈ $118) | +15.5% / +19.2% per trade | +12.4% / +15.3% | +9.2% / +11.5% |
| $3 wide, 5 DTE (risk ≈ $180) | +16.8% / +21.1% | +14.7% / +18.2% | +12.4% / +15.3% |
| $5 wide, 5 DTE (risk ≈ $315) | +17.0% / +21.9% | +16.4% / +20.5% | +15.3% / +18.8% |
| $1 wide, 5 DTE (risk ≈ $60) | +9.9% / +12.1% | +5.2% / +6.4% | +0.8% / +1.1% |

Win rate 73–84%. Positive in both periods at every IV assumption (only the $1-wide spread goes
flat at 1.5×, because the bid/ask costs are large relative to a $1 width).

### Account simulation (Jan 2023 → Sep 2026, IV 1.3×, 5 DTE, risk 10% of equity per trade)

| Weekly deposit | Total deposited | Ending balance | Worst drawdown | 2023 | 2024 | 2025 | 2026 YTD |
|---|---|---|---|---|---|---|---|
| $25 | $4,951 | $18,077 | 19% | −$150 | +$2,715 | +$2,904 | +$7,707 |
| $50 | $9,801 | $30,633 | 22% | −$784 | +$3,700 | +$4,737 | +$13,278 |
| $100 | $19,501 | $76,461 | 17% | −$297 | +$10,792 | +$12,260 | +$34,405 |

**Warning from the same simulation:** with $101 and no deposits, the first trade (Jan 2023) lost $61
and the account could not afford another spread. At $100, one spread is ~60% of the account.
Risking 50% per trade produced 80–90% drawdowns. Size at **≤ 10–20% risk per trade**.

## Honest limitations
- Option prices are **modelled**, not real quotes. No put skew, no early assignment, fills assumed at
  the model's bid/ask. Real results will be worse than the tables.
- The signal fires ~2–3 times a month across the three ETFs; several can fire the same day
  (correlated risk).
- It is **not a same-day strategy**: positions are held 1–5 days.
- 2023 was flat-to-negative: expect losing stretches.
- Spreads need options approval for spreads on Webull (check the options level in the app).

## Files
- `research/lab.py`, `research/opt.py` — data loader, option model, trade simulator
- `research/study1_direction.py` … `study7_account.py` — each step above, reproducible
- `tools/rsi2_scan.py` — daily signal scanner

## Part 3 — Small-account version: RSI(2) with long calls under $100–150 (Options Level 2)

Webull requires Options Level 3 **and $2,000 equity** for spreads, so the put-spread strategy is not
available at $101. Tested instead: buy the nearest-money call that fits the budget on the same signal.
Added 10 cheaper ETFs with weekly options (XLF, EEM, XLE, KRE, XLU, XLI, SLV, GDX, TLT, HYG).
Script: `research/study8_small_calls.py`.

| Version (IV 1.3×) | Train 2022–24 | Test 2025–26 |
|---|---|---|
| Cheap ETFs, call ≤ $100, 10 DTE | 179 trades, 43% win, **−12.8%** per trade | 132 trades, 64% win, **+25.0%** |
| Cheap ETFs, call ≤ $100, 15 DTE | 179, 45%, **−9.2%** | 130, 65%, **+25.1%** |
| SPY/QQQ/IWM, call ≤ $100, 5 DTE | 17, 18%, **−47.3%** | 13, 69%, +66.8% |
| SPY/QQQ/IWM, call ≤ $150, 10 DTE | 24, 42%, +5.5% | 16, 81%, +60.0% |

**Result: fails.** Every affordable-call version lost money in 2022–24 and only worked in 2025–26,
when the bounce effect was unusually strong. Buying calls needs a bigger bounce than the average one,
so it only pays in strong years; the put spread wins on smaller bounces, which is why it held up in
both periods. The cheap ETFs also show a much weaker signal than SPY/QQQ in 2022–24.
No Level-2 (calls/puts only) version under $150 passed both periods.

## Part 4 — Backtest of the live bot's `auto` rules (2026-09-24)

Script: `research/study9_bot_auto.py`. Exact bot logic on 241 days of SPY+QQQ 5-min data (Oct 2025 → Sep 2026):
15-min opening range ± $0.05, completed-bar close beyond it, volume ≥ 1.5×, VWAP side, strong close, other ETF
confirming; same-day option ≤ $0.50; take-profit +80%, stop −35%, breakeven after +40%, flatten 14:50 CT,
max 2 trades/day.

| IV assumption | Train (Oct 25–Apr 26) | Test (May–Sep 26) |
|---|---|---|
| 1.0× (best case for buyers) | 234 trades, 12% win, **−$6.37/trade**, −$1,490 | 170, 13%, **−$5.88**, −$1,000 |
| 1.15× | 232, 9%, −$7.79, −$1,807 | 170, 13%, −$6.15, −$1,045 |
| 1.3× | 231, 9%, −$8.35, −$1,928 | 170, 9%, −$8.05, −$1,368 |

- Exits at 1.15×: 305 stops, 53 breakeven, only 44 take-profits.
- Robustness: favourable-first intrabar ordering (−$7.30 / −$6.21), no stop at all (−$12), hold to 14:50 (−$11) — all lose.
- The signal itself has a small real tilt (underlying +5.7 bps after 60 min, 59% in the right direction) but a
  $0.50 same-day option is far out of the money in the morning (delta ~0.1–0.15) and needs a much bigger move.
- 18 variations tested (each filter removed; entry cut-offs 10:30/12:00 CT; time stops; opening-range size filters;
  retest entries; $1.00 contracts; take-profit 50%/150%; stop 25%/50%; 1 trade/day). **None is profitable in both
  periods.** Best: entries only until 10:30 CT ≈ breakeven (−$1.64 / −$0.55 per trade at 1.15×), i.e. no edge.

**Conclusion: the `auto` rules lose about $6–8 per trade, ~$1,000 per six months at 2 trades/day — more than the
whole account. Do not run it live.** Paper mode only, as a logging/discipline tool, unless a future test finds a
version that is positive in both periods.
- Added 2026-09-25: filters using yesterday's levels / the gap also lose in both periods (IV 1.15, per trade):
  breakout must also clear prior-day high/low −$10.33 / −$5.80; only in gap direction −$9.28 / −$6.02;
  only against the gap (gap fade) −$6.59 / −$6.30.

## Part 5 — Prior-day volume profile (VAH / POC / VAL) setups (2026-09-26)

Script: `research/study10_volume_profile.py`. Prior-day profile from 5-min bars (checked against a 1-minute
profile: POC/VAH/VAL within $0.07). SPY, QQQ, IWM, 723 symbol-days, same option model and train/test split.

| Setup (IV 1.15×, $0.50 same-day option, level stops) | Train | Test |
|---|---|---|
| All four combined | 346 trades, 19% win, −$10.71/trade | 269, 18%, −$11.71 |
| A: open above VAH, VAH hold → call | 68, 29%, −$4.03 | 95, 27%, −$7.96 |
| B: open below VAL, VAL reject → put | 73, 23%, −$6.58 | 41, 24%, −$7.33 |
| C: back into value 30 min (80% rule) | 70, 47%, −$1.85 | 44, 36%, −$9.31 |
| D: open inside, break out of value | 158, 3%, −$18.40 | 108, 3%, −$17.46 |

- Best variants (60-min time stop, +50% option take-profit) cut the loss to −$1 to −$3/trade in train but
  −$3.50 to −$7 in test. Nearer-the-money contracts ($1.50, $3.00) lose more dollars. IV 1.0× does not rescue it.
- The underlying move after the signals is +3 bps (train) and −2 bps (test): no directional edge at all.

**Conclusion: prior-day volume profile levels do not give a same-day option edge in this data.** Together with
Parts 1 and 4, no rule-based same-day option-buying strategy has held up in both periods.

## Part 6 — September 2026 review: what worked this month (2026-09-29)

Data: SPY / QQQ / IWM 5-minute bars through 2026-09-29 (19 trading days in September). Daily bars for
09-24 to 09-29 were built from the 5-minute bars; the closes match Webull's.
Scripts: `research/study11_september.py` (regime and 11 strategies), `research/study11b_detail.py` (month by month).
Every rule is tested on September **and** on the 11 months before it (Oct 2025 – Aug 2026). A rule that only
works in one month of ~19 days is most likely luck.

### The month's market

| | SPY | QQQ | IWM |
|---|---|---|---|
| Aug 31 → Sep 29 | −0.1% | **+3.1%** | **−4.8%** |
| September range | 747.74 – 775.14 | 699.27 – 748.35 | 277.41 – 295.41 |

| Month (all 3 ETFs) | Avg day range | Up days | First 15-min direction held to close | Day's high/low set in first 30 min | VWAP crosses per day |
|---|---|---|---|---|---|
| Apr | 1.22% | 68% | 63% | 67% | 6.4 |
| May | 1.16% | 60% | 68% | 60% | 6.2 |
| Jun | 1.74% | 48% | 62% | 62% | 7.1 |
| Jul | 1.32% | 47% | 71% | 58% | 6.0 |
| Aug | 0.89% | 38% | 75% | 63% | 7.5 |
| **Sep** | **0.93%** | **39%** | **74%** | **61%** | **6.8** |

- Small days: the average range has been under 1% for two months, vs 1.2–1.7% in the spring. Cheap same-day
  options need a big move, and there have been few.
- More down days than up days, with tech (QQQ) and small caps (IWM) going opposite ways.
- The opening direction held to the close on about 3 of 4 days, but price still crossed VWAP ~7 times a day,
  so the path was choppy even when the direction was right.

### 11 intraday rules, same-day $0.50 option, Guardian exits

$/trade per 1 contract (IV ×1.15). "Und bps" is the underlying's move in the trade direction from entry to
14:50 CT (0.01% = 1 bp); it measures the signal alone, before any option cost.

| Rule | Sep n | Sep $/trade | Sep und bps | Prior n | Prior $/trade | Months positive (of 12) |
|---|---|---|---|---|---|---|
| Gap and go (gap > 0.3%, first 15 min confirms) | 14 | **+6.17** | +34 | 204 | −8.01 | 3 |
| Power hour break (14:00 CT) | 12 | −0.45 | −2 | 184 | −8.22 | 0 |
| RSI(14) 5-min extreme reversal | 20 | −1.09 | −8 | 209 | −9.15 | 0 |
| ORB 15-min breakout | 54 | −2.52 | +3 | 661 | −7.41 | 0 |
| Prior-day value plan (the 09-29 plan) | 56 | −3.23 | +8 | 646 | −8.62 | 0 |
| Trend day at 10:30 CT | 24 | −6.48 | +1 | 318 | −6.55 | 1 |
| ORB failed breakout (fade) | 25 | −7.00 | −1 | 315 | −7.29 | 1 |
| VWAP pullback in trend | 36 | −8.36 | −5 | 412 | −6.34 | 1 |
| EMA 9/21 cross + VWAP | 37 | −8.61 | −10 | 480 | −7.70 | 0 |
| Gap fade | 32 | −11.25 | −6 | 413 | −6.19 | 1 |
| Back into value → POC | 6 | −13.26 | −22 | 111 | −3.07 | 3 |

**One day made September's best numbers.** On 09-21 SPY and QQQ trended all day and gap-and-go and the ORB
breakout each made about +$81 per contract. Without 09-21, gap and go falls from +$6.17 to **−$6.52** per trade,
ORB from −$2.52 to −$5.73, and the value plan from −$3.23 to −$6.28.

**What the month says about indicators (underlying move, no option costs):**
- *Going with the move* (gap and go, ORB, value-area breakouts) was slightly right in September: +3 to +34 bps.
- *Fading the move* (gap fade, failed-breakout fade, back into value, RSI(14) extremes, VWAP pullbacks, EMA
  crosses) was wrong: −1 to −22 bps.
- Neither side was big enough to pay for a same-day option.

**Why the options lose even when the direction is right:** across all 4,269 simulated trades, the underlying
was in the trade's favour at 14:50 on 51% of them (a coin flip), and **85% of those right-direction trades
still lost money**: a normal dip hit the stop first, or time decay ate the option before the move came.

### Sensitivity (September / prior $/trade)

| Setting | ORB breakout | Value plan | Gap and go |
|---|---|---|---|
| Base: $0.50 same-day, IV ×1.15 | −2.52 / −7.41 | −3.23 / −8.62 | +6.17 / −8.01 |
| Cheaper model IV (×1.0) | +0.52 / −5.65 | +0.25 / −7.35 | +10.51 / −6.19 |
| $3.00 same-day (near the money) | +15.58 / −16.52 | +13.52 / −15.52 | +89.42 / −10.60 |
| $3.00, expires next day | −12.67 / −21.64 | −8.96 / −22.71 | +24.69 / −21.31 |
| $6.00, 5 days to expiry | −28.90 / −31.62 | −28.63 / −32.97 | −15.20 / −32.26 |

No setting is positive in both periods. Near-the-money contracts turn September green, but they lose about
twice as much per trade in the prior 11 months. Longer expiries lose more because the Guardian's $10–$20 stop
is tight for a $300–$600 contract.

### Your own trades (journal, 09-24 to 09-28, 30 trades)

| | Trades | Total | $/trade |
|---|---|---|---|
| Followed the rules / Guardian managed the exit | 5 | +$70.40 | +$14.08 |
| Partly followed | 10 | +$89.73 | +$8.97 |
| Broke the rules (no trigger, over the max, against the trend) | 15 | **−$133.92** | −$8.93 |

- 8 wins averaging +$27.88; 22 losses averaging −$8.95. The two best trades (+$117.88 and +$38.88) made
  the whole result; the other 28 trades lost **−$130.55** together.
- Every big winner came from a strong one-way move (09-25 open and 11:00 breakout, 09-28 10:48 and 11:24 calls) held
  until a trailing stop took it out. Hand exits within 1–2 minutes and trades 3+ of the day were where the
  money went.

### Multi-day RSI(2) (Part 2) in September — still the only rule that held up

Signal: RSI(2) < 10 with the price above its 200-day average; exit when the close is above the 5-day average
(max 5 days). Underlying return per trade:

| Entry | SPY | QQQ | IWM |
|---|---|---|---|
| 09-01 | +1.50% (2 days) | — | — |
| 09-10 | +0.85% (1 day) | +1.16% (5 days) | −0.53% (5 days) |

3 of 4 won in September; 11 of 14 won from June to September. **As of the 09-29 close, IWM is on a signal**
(RSI(2) 6.4, close 279.07 vs 200-day 274.71). SPY is close (RSI(2) 21.5). Part 2's backtest used the bull put
credit spread, which needs Options Level 3 and $2,000 of equity on Webull; Part 3 showed that buying calls on
this signal did not hold up in 2022–24.

### Conclusions for the restart

1. **No same-day option rule beat costs over the last 12 months**, including this month once 09-21 is removed.
   That matches Parts 1, 4 and 5. Treat 0DTE as a small, capped side bet, not the plan.
2. **In this market, trade with the move, never against it.** Continuation signals were right in September;
   fades were wrong. If you trade 0DTE: a gap-and-go or opening-range break in the first hour, in the trigger
   direction only.
3. **Let the Guardian hold the winners.** Your profit came from 2 trades held with a trailing stop; hand exits
   and extra trades gave it back. Keep the max of 2 trades a day and the lockout.
4. **Size by risk, not by account.** With a bigger account, keep each trade's stop loss at ≤ 2–5% of the balance
   (e.g. $1,000 → $20–$50 risk). Near-the-money contracts need a wider stop than the default $10–$20 clamp.
5. **The one edge that held across four years is multi-day RSI(2) with a put credit spread.** With $2,000+ and
   Options Level 3, that is the setup to trade (≤ 10% risk per spread, see Part 2). It fires ~2–3 times a month.
6. **Limits:** 19 days is a small sample; option prices are modelled, not real quotes; real fills are worse.

## Part 7 — Clint Awana's opening-range method, from his video (2026-09-29)

Source: "How to Trade the Opening Range", Clint Awana (@ClintOptions), YouTube, 2026-09-28, 44 min (the user
pasted the transcript). Script: `research/study12_clint_orb.py`.

### Notes: his method
- **Range:** high and low of the first 15 minutes, 9:30–9:45 ET (8:30–8:45 CT), on SPY and QQQ. The midpoint is
  usually near the open. Sit on your hands for those 15 minutes; most blown accounts come from FOMO trades in the
  first 5–10 minutes.
- **Range size matters:** compare it with the stock's normal daily range. Narrow ranges break more often and run
  further; a wide range (his example: 0.4% on SPY) rarely gives a clean break. Skip days with an oversized range.
- **Chart:** opening-range high/low, premarket high/low, standard (floor) pivots, VWAP, volume, RSI.
  Optional: ES/NQ futures levels, Mag-7 names (MSFT, TSLA, META, NVDA…) to confirm direction.
- **Entry:** a 5-minute candle **closes** outside the range, with **rising volume**, and **RSI trending the same
  way but not stretched** (not above 70 for calls or below 30 for puts). He wants **SPY and QQQ breaking the
  same way at the same time**. Flat VWAP/RSI/MACD or no volume = no pressure = skip.
- **Targets:** the next standard pivot, or the premarket high/low. Trim 20–30% of the position, then around 50%,
  leave a runner by +80%, but **never let a runner go red**. Take the first move and get out; don't hold all day.
- **Inside the range = no-man's land:** no trades. 0DTE calls and puts both bleed in the chop, faster later in the
  day. A pivot inside the range acts as a magnet on choppy days.
- **Retests** of the range edge after a break: possible, but under 50% in his experience. The first break is better.
- **Chasing** a break late is OK only if volume keeps coming, RSI still points the way, and there is room to the
  next pivot or premarket level.
- **Avoid:** monthly OPEX Fridays and FOMC days (price pins inside the range), CPI/PPI and 10 a.m. data days
  (oversized ranges), be careful on Mondays (weekend gaps).
- **His claim:** with every condition met it works "nine times out of 10".

### Backtest of his rules (SPY + QQQ, Oct 2025 – Sep 2026, same-day option)
Coded: range 9:30–9:45 ET; first 5-min close outside it before 11:30 ET; filters for volume (breakout candle above
the previous candle and above its 20-day average), RSI(14) (calls 50–70 and rising, puts 30–50 and falling),
SPY/QQQ agreement, narrow range (below the prior 10 days' median), no OPEX/FOMC days. His exit: next floor pivot
= take profit, a close back inside the range = out, otherwise out by 11:30 ET. Not coded: premarket levels (no
premarket bars in the data), Mag-7 check, trims/runners.

$/trade for 1 contract (IV ×1.15). "His $" = his exit; "Guardian $" = the Trade Guardian's trailing exits.

| Rules used | Period | Trades | Win | Und bps | His $ | Guardian $ |
|---|---|---|---|---|---|---|
| Plain break, $0.50 | Sep / prior | 37 / 425 | 30% / 29% | +4 / +0 | −0.39 / −5.46 | +1.34 / −7.88 |
| + volume | Sep / prior | 12 / 154 | 42% / 33% | +8 / +1 | +4.09 / −5.18 | +4.20 / −6.97 |
| + RSI | Sep / prior | 5 / 173 | 20% / 34% | +2 / +0 | −0.51 / −3.59 | +1.38 / −7.94 |
| volume + RSI | Sep / prior | 1 / 57 | — / 39% | — / +2 | — / −2.57 | — / −8.57 |
| **All his rules, $0.50** | prior (none in Sep) | 14 | 43% | +5 | −0.22 | −11.52 |
| All his rules, $1.00 | prior | 14 | 43% | +5 | +2.50 | −17.89 |
| All his rules, $2.00 | prior | 14 | 43% | +5 | +5.33 | −24.67 |

- **His filters help.** Volume and RSI cut the loss from −$5.46 to about −$2.60 per trade; with every rule it is
  about breakeven with a $0.50 contract and slightly positive with $1–2 contracts.
- **But all rules together fired only 14 times in 11 months** (none in September), and won **43%**, not 9 in 10.
  Positive Nov–Feb, negative every month it traded from April to August. 14 trades cannot prove an edge.
- **His exit beats the Guardian's for this setup** (take profit at the pivot, get out if the range fails):
  the Guardian's hold-and-trail gives the morning move back by the afternoon.
- The underlying move is small (+0 to +8 bps on average), so the option cost still decides most of the result.

## Part 8 — ICT concepts: fair value gaps, order blocks, liquidity sweeps (2026-10-04)

`research/study14_ict_search.py` searched 960 combinations: 4 setups (FVG retrace, order-block retest, momentum
at the displacement close, and liquidity sweep → market-structure shift → FVG retrace), 4 time windows, 4 bias
filters (none / VWAP side / 20-day trend / both), 5 targets (1R–3R, next liquidity) and 2 displacement sizes, on
SPY/QQQ/IWM 5-min bars. Configs were picked on TRAIN (Sep 2025 – Apr 2026) and then checked unchanged on TEST
(May – Sep 2026). Stop checked first, no fill on the signal candle, $0.01/share cost each way.

**What failed:** a plain FVG retrace (median −0.12R train / −0.06R test), order-block retests (too few fills,
none qualified), and momentum entries (positive on train, negative on test). Across all configs only 14% were
positive on test, and the top train configs mostly fell apart there.

**What survived: the sweep model.** Of the 24 sweep configs with enough trades, 24 were positive on train and 21 on test.
Requiring the MSS roughly doubles the edge, and without a sweep first the same MSS + FVG entry is exactly 0.00R.

**Correction made while drawing the chart examples.** The first version counted any candle that crossed a level and
closed on the far side as a "sweep", including plain breaks (open above, close below), and it allowed the sweep to
come after the displacement candle. `sweep="true"` now requires the candle to open and close on the same side with
only the wick through the level, at or before the displacement candle. This was a change made after seeing test
results, but it matches the textbook definition and it was also better on train (+0.31R → +0.51R).

`research/study14b_sweep_model.py`, rules:
1. Liquidity = prior-day high/low and the 9:30–9:45 ET (8:30–8:45 CT) range high/low.
2. Sweep: a 5-min candle opens and closes on the same side of a level, and only its wick goes through
   (a wick above means puts, a wick below means calls).
3. Within 6 candles (it can be the same candle), a big candle (body ≥ 1.25× the day's average range) closes past
   the last swing point and leaves an FVG.
4. Limit at the near edge of the FVG, good for 1 hour. Stop just past the day's furthest sweep wick on that side.
   Target 2R, **otherwise out after 1 hour** (picked on train option P&L).

| SPY/QQQ/IWM | Trades | Win (und.) | Avg R (t) | Option $/trade ($0.60) | Option win |
|---|---|---|---|---|---|
| Train | 32 | 66% | +0.51 (3.0) | +30.46 | 38% |
| Test | 17 | 71% | +0.61 (2.8) | +63.71 | 53% |
| $0.30 contract, all | 49 | | | +30.07 | 39% |

- All three ETFs are positive in R (QQQ is about flat in option $). Calls and puts both work, and 11 of the 12 months
  are positive in R (April loses).
- **The 7 stocks do not confirm it** (−0.22R on test, t −2.2), so treat it as an index-ETF effect at best.
- **It is lumpy.** The median option trade is −$7.82; winners pay 3–10× (still +$17/trade without the best 3).
  At $0.30 contracts: the max drawdown is −$87, the longest losing streak is 6, and the worst trade is −$25.
- **The Trade Guardian's exits ruin it** (+$4 train / −$7.63 test). Its tight option stop gets hit before the
  move. Use the chart stop, the 2R target and the 1-hour limit.
- **Caveats:** 49 trades (about 1 a week). About 1,150 configurations were tried, and the sweep definition was
  tightened after seeing results. Paper-trade it before risking money. Chart examples: the "Sweep Model Playbook"
  artifact.

## Part 9 — Published edges, and real implied volatility instead of the model (2026-10-04)

Data added: Cboe's VIX (1990–), VIX9D (2011–) and VIX1D (2022–) daily history in `data/*_cboe.csv`, downloaded
from cdn.cboe.com. These are the market's own implied vols, so option-selling and option-buying results no longer
rest only on lab.py's IV assumption.

**Published anomalies, checked on our data** (`research/study15_known_edges.py`):

| Effect (source) | Our data | Result |
|---|---|---|
| Intraday momentum into the close (Gao et al. 2018; Baltussen et al. 2021) | SPY/QQQ/IWM 5-min, 738 days | −1.2 bps, t −1.5: **gone** |
| …only on big-move days (the dealer-hedging version) | 249 days | ±1 bps, t < 0.7: **gone**; as a $0.40 0DTE trade, −$12 |
| Turn of the month (Lakonishok & Smidt 1988) | daily, Dec 2021 – Sep 2026 | same as other days: **gone** |
| Overnight vs daytime (Cliff et al. 2008) | daily | SPY equal; IWM's gain is all overnight. Not tradable with options |

**The bank/market-maker edge is selling options.** VIX was above the following month's realised SPY volatility on
84% of days since 2022 (19.2 vs 15.7 on average). For same-day options the gap is gone: VIX1D's variance
matched the realised 10:00–16:00 variance exactly (ratio 1.00), so 0DTE options are fairly priced on average.

**RSI(2) put spread, re-priced with real 9-day IV** (`research/study16_real_iv_spreads.py`; ATM IV = VIX9D × 0.85–1.05,
+1.5 vol points per 1% OTM of put skew, 1% half-spread per leg):

| SPY/QQQ/IWM, 5 DTE | Train (Oct 2022 – 2024) | Test (2025 – Sep 2026) |
|---|---|---|
| $5 wide, on the RSI(2) signal | 64 trades, 75–78% win, +$19–23 (+6–7% of risk) | 58 trades, 79–81% win, +$31–39 (+9–11%), t ≈ 2 |
| $2 wide, on the RSI(2) signal | about breakeven (costs eat a $2 width) | +$0–6 |
| $5 wide, every Monday, no signal | +$8–18, t < 1.6 | +$2–9, t < 0.7 |

Part 2's edge survives real IV, at about half the size the model gave. The signal does the work: selling every
week with no signal is close to breakeven after skew and costs. Risk is about $340 per $5 spread (worst trade −$370),
and it needs Options Level 3 plus $2,000 equity on Webull.

**Sweep model (Part 8) with VIX1D instead of the model IV** (`research/study14c_real_iv.py`). The model's 0DTE IV
(median 13.2% at 10:00 ET for SPY) was above the market's (8.7%), so the earlier option P&L was not flattered by
cheap pricing:

| SPY only, IV = VIX1D | Train | Test |
|---|---|---|
| $0.30 contract | 11 trades, +$50, 45% win | 8 trades, +$78, 50% win |
| $0.60 contract | +$66, 55% win | +$100, 50% win |

Still 19 SPY trades in 13 months: encouraging, not proven.
