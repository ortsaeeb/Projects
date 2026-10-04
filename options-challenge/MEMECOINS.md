# Memecoins — can we be profitable? (2026-10-04)

Short answer: **not reliably, and not on Webull's fees.** Memecoin profits come in rare manias (2021, 2024); the rest
of the time almost everything bleeds. New launches are mostly traps. The only rule that made money since 2022 needed
exchange fees near 0.1%, still fell 60% along the way, and was carried by the 2024 mania.

## 1. Who actually makes money

| Fact | Source |
|---|---|
| 98.6% of 7M+ pump.fun tokens (Jan 2024 – Mar 2025) collapsed into pump-and-dumps; only 97,000 kept > $1,000 of liquidity | [Solidus Labs](https://www.soliduslabs.com/reports/solana-rug-pulls-pump-dumps-crypto-compliance) |
| 93% of 388,000 Raydium pools showed soft-rug-pull behaviour | same |
| 82.8% of memecoins that gained > 100% showed artificial-growth manipulation (wash trading, liquidity-pool inflation) before the dump; 34,988 tokens on 4 chains | [arXiv 2507.01963](https://arxiv.org/abs/2507.01963) |
| Of 13.4M pump.fun wallets, 0.04% made $10,000+; 88% lost money or made under $100 (Jan 2025) | [Mitrade / Dune](https://www.mitrade.com/insights/news/live-news/article-3-565219-20250111) |
| Share of pump.fun wallets in profit: 30.1% in Jun 2025, up to 73.3% in Apr 2026, but realised P&L only (bag holders who never sold are left out), and 65% of winners made $1–$500 | [CoinGecko](https://www.coingecko.com/research/publications/pump-fun-traders-are-making-a-comeback) |

The steady winners are the platform (fees), coin creators and insiders (bundled supply, early sells), and sniper bots
that buy in the first seconds. Ordinary buyers mostly supply the exit liquidity.

## 2. The memecoins big enough to list (Binance daily data, `research/study21_memecoins.py`)

Of the 16 memecoins listed since 2021, 15 are down 43–98% from their listing price, every one fell 91–99% at its
worst, and in 2025 they lost 64–92% (DOGE −64%, PEPE −79%, BONK −75%, WIF −85%, TRUMP −90%). These are the
*survivors*; the coins that died before listing aren't even in the data.

## 3. Rules tested (long only, equal weight, signal at the close, Webull's 1% spread each way)

| Rule | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 YTD | Since 2022 |
|---|---|---|---|---|---|---|---|
| Buy & hold every coin | +1,594% | −55% | +12% | +156% | −80% | −11% | **−77%** |
| Hold the basket only while it's above its 50-day average | +656% | −70% | 0% | +87% | −2% | −10% | −50% |
| Per coin: buy a 20-day high, sell a 10-day low | +1,471% | −42% | +1% | +137% | −13% | −23% | −9% |
| Per coin: above its 50-day average and BTC above its 50-day | +553% | −36% | +26% | +91% | −27% | −13% | −2% |

Also tested: 20/100-day averages, 7/14/30-day momentum, BTC-only filters, top-3 weekly momentum, buying −20% days:
all lost in 2025–26.

**Fees decide it.** At 0.1% per side (big-exchange fees) instead of Webull's 1%, the same rules since 2022: basket trend
+28%, per-coin breakout +65%, per-coin trend + BTC **+134%**, with worst drops of −46% to −71%, mostly earned in
2024. At Webull's ~2% round trip, the frequent in-and-out of a trend rule eats the whole edge.

## 4. If you still want to play

- Never touch new launches (pump.fun, Telegram calls, "next 100x"); assume any coin under a month old is a trap.
- Only listed majors, with money you can lose entirely, sized as a lottery ticket (not the options account).
- Decide with a fixed rule, e.g. hold only while the coin is above its 50-day average and BTC is too; sell when it
  isn't. Check once a day, never chase a candle.
- Webull's spread makes this roughly break-even at best; a low-fee exchange is the only way the rule paid.
- Scams: never connect a wallet to a link from a DM, airdrop, or "claim" page; no "recovery" services.

Data: `tools/fetch_crypto.py` (Binance public API), `data/crypto/*_1d.csv`.
