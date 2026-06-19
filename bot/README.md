# BIST Paper-Trading Bot

A cloud-automated paper-trading bot (virtual money, no broker) for Borsa Istanbul.
It runs on a schedule via GitHub Actions, scores stocks with a multi-factor model,
rebalances a virtual portfolio, and writes an explainable end-of-day report.

## How it works

Every run (hourly during BIST hours):
1. **Scores** each stock in the watchlist on 7 factors — momentum, trend, value
   (earnings yield), quality (ROE), low volatility, RSI, debt/equity — each turned
   into a cross-sectional z-score and combined into a weighted composite.
2. **Rebalances** to the top 3 by composite score: sells dropouts, buys new entrants,
   holds survivors.
3. **Logs** every trade with a plain-language reason (which data drove which inference).
4. **Reports**: regenerates a daily Markdown briefing under `durum/raporlar/`.
5. **Persists** state by committing `durum/` back to the repo.

## Files

| File | Role |
|------|------|
| `strateji.py` | Multi-factor scoring (reuses the project's `veri_katmani.py`) |
| `cuzdan.py` | Virtual wallet: JSON persistence, trade log, daily value history |
| `bot.py` | One trading cycle (run by the Action) |
| `gunsonu.py` | End-of-day report generator |
| `durum/` | Bot state (wallet, trades, reports) — written by the bot |

## Setup (GitHub Actions)

1. Push these files to the repo.
2. **Settings → Actions → General → Workflow permissions → "Read and write permissions"**
   (so the bot can commit its state).
3. **Actions** tab → run the workflow once manually (**Run workflow**) to test.
4. After that it runs automatically on the schedule in `.github/workflows/bot.yml`.

Cron is in UTC; `0 7-15 * * 1-5` maps to 10:00–18:00 Istanbul (UTC+3, no DST), Mon–Fri.

## Notes

- **Paper trading only.** Virtual balance, no real orders, no broker. Not investment advice.
- Banks and holdings are excluded from the watchlist (non-standard financial statements).
- GitHub's scheduled runs are best-effort and may be delayed a few minutes.
- Scheduled workflows pause after ~60 days of repo inactivity (any commit re-enables them).
