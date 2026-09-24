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
python bot.py --live watch QQQ --call-above 742.7 --put-below 740.2 --auto
python bot.py --live manage SPY260924C00769000 --entry 0.58     # protect a position you bought yourself
```

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
