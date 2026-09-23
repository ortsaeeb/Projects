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
