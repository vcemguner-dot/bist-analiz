# BIST Equity Analysis Toolkit

A Python toolkit for fundamental analysis, portfolio tracking, and strategy backtesting of Borsa İstanbul (BIST) stocks, with an interactive Streamlit dashboard.

Built as a hands-on equity-research project: it pulls real market and financial-statement data, computes the metrics a buy-side analyst actually uses, and runs an honest, cost-aware backtest.

## Features

- **Fundamental ratios** — margins, ROE, ROA, current ratio, debt/equity across recent fiscal years, computed directly from reported financial statements.
- **USD-based DCF** — interactive discounted-cash-flow valuation built on USD free cash flow (avoids the lira-inflation problem), with adjustable growth, WACC, and terminal-growth assumptions.
- **Portfolio tracker** — positions, P&L, allocation, and a 1-year benchmark comparison against the BIST 100 (alpha).
- **Backtest engine** — SMA-crossover strategy vs buy-and-hold, with look-ahead protection, transaction costs, and max-drawdown.

## Architecture

A shared data layer feeds three independent modules, all surfaced through one Streamlit UI:

```
            ┌────────────── Streamlit UI (app.py) ──────────────┐
            │   Ratios   │     DCF     │  Portfolio │  Backtest  │
            └──────┬───────────┬────────────┬────────────┬───────┘
                   ▼           ▼            ▼            ▼
          degerleme.py   degerleme.py   portfoy.py   backtest.py
                   └───────────┴────────────┴────────────┘
                                   ▼
                          veri_katmani.py  (data layer)
                  yfinance (prices)  +  isyatirimhisse (financials)
```

## Tech stack

Python · Streamlit · pandas · matplotlib · yfinance · isyatirimhisse

## Setup

```bash
# 1. (optional) create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run the app
streamlit run app.py
```

The app opens in your browser. Type any BIST ticker (e.g. `BIMAS`, `ASELS`, `THYAO`) in the sidebar.

## Project structure

| File | Role |
|------|------|
| `veri_katmani.py` | Data layer — fetches prices and financials, builds USD FCF |
| `degerleme.py` | Valuation — financial ratios and the DCF function |
| `portfoy.py` | Portfolio tracking and benchmark comparison |
| `backtest.py` | SMA-crossover backtest engine |
| `app.py` | Streamlit dashboard |

## Data sources

- **Prices:** Yahoo Finance via `yfinance` (BIST tickers use the `.IS` suffix).
- **Financial statements:** İş Yatırım via `isyatirimhisse`, which provides far more complete fundamentals for Turkish companies than Yahoo.

Both libraries read public websites and are not official APIs — they can break if those sites change, and request rates should be kept gentle. Suitable for personal research, not production trading.

## Disclaimer

For educational and personal-research use only. Not investment advice.
