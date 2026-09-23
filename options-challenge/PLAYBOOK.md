# $100 Same-Day Options Challenge — Playbook

Account: Webull Individual Margin (…6965). Starting balance **$101.30** (2026-09-23).
Deposits added weekly. Goal: grow the account as much as possible **without blowing it up**.

Claude does the analysis and builds each order; the user approves every order in the
Webull app and sets the stop-loss there (the Webull connection only supports limit orders,
not stop orders).

---

## 1. Trading windows

| Window (ET)   | Setup                        | Notes |
|---------------|------------------------------|-------|
| 9:00 – 9:25   | Pre-market scan              | Levels, bias, pick 1–2 tickers, get the chain screenshot |
| 9:30 – 9:35   | **Do not trade**             | Spreads are widest, IV is inflated, fake-outs are common |
| 9:35 – 9:50   | **Setup A: Opening Range Breakout** | Main trade of the day |
| by 10:15      | Hard exit for Setup A        | Get out if it hasn't worked by then |
| 15:15 – 15:25 | Afternoon scan               | Trend of the day, gamma pin strike |
| 15:30 – 15:50 | **Setup B: Power Hour Push** | Only on trend days, smaller size |
| by 15:55      | Hard exit, everything closed | **Never hold a same-day option into the close** |

Maximum **2 trades per day**, one in each window.

---

## 2. Tickers

- **Core (daily expirations, tightest spreads):** SPY, QQQ, IWM
- **Movers (weekly expirations):** big-volume stocks with cheap, liquid chains, picked each
  morning from pre-market gainers/losers and most-active lists (e.g. TSLA, NVDA, AMD, PLTR,
  SOFI, MARA, etc.). Only traded when a news or earnings catalyst is driving volume.

A ticker is only tradable if its option passes the contract filter in §5.

---

## 2b. Full pre-trade checklist (every trade is scored on all of these)

| Area | What Claude checks | Source |
|------|--------------------|--------|
| **News / catalysts** | Overnight headlines, macro calendar (CPI, FOMC, jobs, Fed speakers, Treasury yields), earnings, analyst moves, geopolitical risk | Web search |
| **Trend** | EMA 9 / 21 / 50 alignment, price vs VWAP, daily + 15-min + 5-min direction | Webull bars → `tools/indicators.py` |
| **Momentum** | RSI 14 (avoid buying calls > 75 / puts < 25), MACD cross and histogram direction | `tools/indicators.py` |
| **Volatility** | ATR 14 (sets realistic targets), Bollinger width (squeeze → breakout) | `tools/indicators.py` |
| **Volume** | Relative volume of the trigger bar, large-order money flow, capital inflow/outflow | Webull bars, footprint, capital flow |
| **Structure** | Swing highs/lows, HH+HL / LH+LL, break of structure, opening range, prior-day levels | `tools/indicators.py` |
| **Options positioning** | Net gamma exposure (positive = choppy/pinning, negative = trending), gamma flip, call wall, put wall, max-OI pin, put/call volume, strikes where volume is building | Option chain → `tools/gex.py` |
| **Contract** | Delta, premium, spread, volume, IV | Option chain → `tools/gex.py` |

A trade needs **news not against it**, **trend + structure agreeing**, **volume confirming**,
and **gamma not blocking it**. Momentum and volatility adjust the target and size.

---

## 3. Setup A — Opening Range Breakout (9:35 – 9:50)

**Pre-market (9:00–9:25)**
1. Mark: prior day high / low / close, pre-market high / low, gap % from prior close.
2. Bias: gap up and holding above the pre-market midpoint = calls; gap down and holding
   below = puts; flat = wait for the break.
3. From the chain screenshot: the strikes with the largest open interest (they act as
   magnets and walls) and where call vs put volume is building.

**Opening range** = high and low of the first 5-minute candle (9:30–9:35).

**Entry: all of these must be true**
- [ ] A 5-minute candle (or two 1-minute candles in a row) **closes** outside the opening range
- [ ] Breakout candle volume ≥ **1.5×** the average of the prior bars
- [ ] Price is on the right side of **VWAP** (above for calls, below for puts)
- [ ] Direction agrees with the pre-market bias, or the break is strong enough to override it
- [ ] Large-order money flow agrees with the direction
- [ ] No big open-interest wall within ~0.3% in the direction of the trade
- [ ] Reward-to-risk ≥ **2:1** (distance to next level ÷ distance back inside the range)

**Exit**
- Stop: price closes back inside the opening range, **or** the option is down **25%**
- Target: next level (prior day high/low, pre-market high/low, open-interest strike),
  or **+50%** on the option
- Once up +30%, raise the stop to breakeven
- Time stop: **10:15 ET**, win or lose

---

## 4. Setup B — Power Hour Push (15:30 – 15:50)

Only on a **trend day**: price has stayed on one side of VWAP most of the afternoon and
kept making higher highs (or lower lows).

**Entry**
- [ ] The afternoon's consolidation (roughly 14:30–15:25) breaks in the trend direction,
      with a 5-minute close and volume ≥ 1.5× average
- [ ] The trade moves **toward** the largest same-day open-interest strike (the "pin"), not away from it
- [ ] Premium ≤ **$0.30** (these options lose value very fast; small size only)

**Exit**
- Stop: back inside the consolidation, or option down **30%**
- Target: the pin strike or **+50–100%**
- **Hard exit at 15:50–15:55.** Nothing is held into the close.

---

## 5. Contract filter

| Item             | Rule |
|------------------|------|
| Expiration       | Same day for SPY/QQQ/IWM; nearest weekly for stocks |
| Delta            | 0.30 – 0.50 (at the money or slightly out) |
| Premium          | Setup A: $0.25 – $0.80 · Setup B: ≤ $0.30 |
| Bid/ask spread   | ≤ $0.05, or ≤ 10% of premium |
| Volume today     | ≥ 500 contracts on that strike |
| Order type       | **Limit only**, at the mid price or 1 cent above; never chase more than 3 cents |

---

## 6. Risk rules

| Rule | Limit |
|------|-------|
| Risk per trade | ≤ **25%** of account (stop × premium × 100) |
| Max daily loss | **30%** of the account at the start of the day, or 2 losing trades, then done for the day |
| Circuit breaker | Account drops **40%** below its high-water mark → stop, review the journal, reset rules |
| Deposits | Added at the start of the week only, never mid-day to "win it back" |
| News days | No trades on CPI, FOMC or jobs report mornings until 30 min after the release |

**Position sizing**

```
contracts = floor( (account × 0.25) / (premium × 100 × stop%) )
            capped so total cost ≤ 80% of account, minimum 1
```

Until the account passes about **$300**, that's **1 contract** per trade.

---

## 7. Daily workflow with Claude

1. **9:00 ET** — message "scan". Claude pulls pre-market data (gainers/losers, most active,
   SPY/QQQ/IWM bars, money flow) and returns levels, bias and the 1–2 best tickers.
2. **9:15 ET** — send a screenshot of the same-day option chain around the current price
   (strike, bid, ask, volume, open interest, IV, delta). Claude picks the strike and
   writes a **conditional trade card** in advance:
   *"If SPY 5-min closes above X on volume > Y, buy 1 SPY [strike]C at limit ≤ $Z;
   stop X−a / −25%; target T."*
3. **9:35 ET** — when the trigger hits, say **"go"**. Claude sends the limit order to Webull,
   you approve it in the app, then immediately set the stop in the app.
4. **15:15 ET** — same process for Setup B.
5. **After the close** — Claude logs the trade in `JOURNAL.md`.

Speed matters at the open: pre-staging the trade card means the only thing left at 9:35
is "trigger hit? → go". If the move has already run more than halfway to the target
before the order is placed, **skip it**.
