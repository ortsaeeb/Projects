# Options Bot — Setup & Use

Runs on **your own computer** (Windows/Mac) using Webull's official OpenAPI.
It sees live option bid/ask, places and cancels orders by itself, and manages exits
(take-profit, stop, breakeven trail, end-of-day flatten).

## 1. One-time setup
1. Install Python 3.11+ from python.org (Windows: tick "Add Python to PATH").
2. Get this folder onto your computer:
   `git clone https://github.com/ortsaeeb/projects.git` then `cd projects/options-challenge/bot`
   (branch `claude/webull-options-trading-oyic74`: `git checkout claude/webull-options-trading-oyic74`)
3. Install the Webull SDK: `pip install webull-openapi-python-sdk`
4. Copy `config.example.json` to `config.json` and fill in **app_key, app_secret, account_id**
   (from Webull's OpenAPI / developer page). `config.json` is git-ignored — **never share it or commit it.**
5. First run: `python bot.py check`
   Webull may ask you to approve a 2-factor prompt in the app; the token is saved in `conf/`.
   This prints your balance, a SPY quote and one SPY option quote. If anything errors, send the
   error text (NOT your keys) so it can be fixed.

## 2. Paper mode (default — no real orders)
```
python bot.py chain SPY --type C                 # today's calls near the money, live bid/ask
python bot.py watch QQQ --call-above 742.7 --put-below 740.2 --auto
python bot.py rsi2                               # daily RSI(2) scan (run ~2:45 PM CT)
```
Paper fills use real quotes. Results go to `logs/`.

## 3. Live mode
Both are required, on purpose:
- `"mode": "live"` in `config.json`
- `--live` on the command line
```
python bot.py --live auto        # (backtest: loses money, see RESEARCH.md part 4) start by 8:30 CT: sets its own levels from the 8:30-8:45 range on SPY+QQQ,
                                 # trades confirmed breakouts (volume, VWAP, strong close, other ETF agrees) until 2:30 CT
python bot.py --live watch QQQ --call-above 742.7 --put-below 740.2 --auto
python bot.py --live manage SPY260924C00769000 --entry 0.58     # protect a position you bought yourself
```

## 3a. Order test
`guard` does this by itself: once the market is open it places and cancels a $0.01 test order and prints
`ORDER TEST PASSED`, and after your first trade it prints `STOP ORDER CONFIRMED`. To run it on its own:
```
python bot.py --live testorder
```
Places a **$0.01 buy** on an at-the-money SPY call (it cannot fill) and cancels it. If you hold an option, it also
places and cancels a **$0.01 stop-limit sell** on it (don't run it while the guard is running). Ends with
`RESULT: orders work` — or the exact Webull error to send over.

## 3b. Trade Guardian (recommended way to use the bot)
You pick the trades in the Webull app; the Guardian manages every exit.
```
python bot.py --live guard      # real stop orders
python bot.py guard             # dry run: reads your real positions, only simulates the orders
```
- Any option you buy gets a real **stop-limit sell order in Webull within ~5 seconds**, placed so the trade
  sits **30% under your entry**, with the loss kept between **$10 and $20** per trade (`risk_pct`, `risk_min`,
  `risk_max`). Contracts above ~$0.67 hit the $20 cap, so their stop gets tighter; the log warns under 20% room.
  It stays at Webull even if your PC shuts off.
- The stop only moves up: **breakeven at +40%**, **locks +30% at +80%**, **locks +90% at +150%**, then trails
  **25% under the highest bid**.
- **Selling by hand:** Webull won't let you sell while the Guardian's stop holds the contracts. Either
  **edit the Guardian's stop** in Orders into a Limit order at the bid, or **cancel it and sell** — the Guardian
  waits 1 minute before putting a stop back, and cleans up once the position is gone.
- If the stop is cancelled and you still hold the option after 1 minute, the stop goes back on.
- Only one Guardian window can run at a time (a second one refuses to start).
- A `KILL` file left over from a previous day is deleted at startup; today's `KILL` file sells everything.
- Early-close days (day after Thanksgiving, Christmas Eve): same-day options are closed at 11:50 CT.
- If Webull can't be reached, the log says so once (then every 5 minutes); stops already placed stay active.
- Same-day options are sold at `flatten_time_ct` (2:50 PM CT), with a warning at 2:30.
- Warns when one trade is more than 30% of the account.
- Heads-up in the log when the day's loss reaches $20 (`warn_loss`); trading continues.
- Warnings on a new trade (never blocks): midday 10:30–1:30 CT, re-entry within 10 min of a loss, trade #4+ of
  the day, same-day strike more than 0.35% out of the money. Turn off with `"warnings": false`.
- Optional lockout (off by default): after 2 losses or −$25 in a day, any new position is sold right away.

Change any of these by adding a `"guard"` block to `config.json`, for example:
```json
"guard": { "risk_pct": 0.30, "risk_min": 10, "risk_max": 20, "warn_loss": 20 }
```
- Run **only one** of `guard`, `auto`, `buy`, `watch --auto` or `manage` at a time: they each place their own
  exit orders and would fight over the same contracts.
- Stops are **DAY orders**. For an option you hold overnight, start `guard` again the next morning.
- `python bot.py check` prints your option positions the way the guard reads them; check it once.
- Every 5 minutes the log shows `GUARD alive — ...` with each position's stop, so you can see it's running.

Moving the stop up needs the bot running; the resting stop order protects you either way.
If Webull rejects the stop order type, the log says so and the Guardian watches the stop itself instead
(that fallback only works while the bot runs).

## 4. Safety limits (config.json → "risk")
| Setting | Default | Meaning |
|---|---|---|
| max_cost_per_trade | $50 | never buys a contract costing more |
| max_trades_per_day | 2 | stops entering after this many |
| max_daily_loss | $40 | stops entering after this much realized loss |
| take_profit_pct | 0.80 | take-profit limit at +80% |
| stop_loss_pct | 0.35 | exit at −35% |
| flatten_time_ct | 14:50 | sells anything still open at 2:50 PM CT |

After a +40% move the stop automatically rises to breakeven.
**Kill switch:** create an empty file named `KILL` in this folder — the bot stops entering and exits open trades.

## 5. Important
- The bot enforces discipline; it does **not** create an edge. The backtests (RESEARCH.md) found no
  reliable edge in same-day breakout trading. Expect losing days.
- The first live trades should be watched. If an automatic exit fails, the log says
  "SELL MANUALLY IN WEBULL".
- Response fields from Webull were coded defensively; `python bot.py check` confirms they parse correctly.
