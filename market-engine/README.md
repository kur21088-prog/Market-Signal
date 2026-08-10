# Market Signal Engine

Paper-trading-first market scanner for stocks, crypto, ETFs, and metals.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/run_scan.py
streamlit run dashboard/Home.py
```

## What it does

- Scans the symbols in `data/watchlist.json`
- Produces BUY / SELL / WAIT signals
- Uses EMA, RSI, MACD, ATR, and volume
- Supports optional ML probability after you train a model
- Writes current signals to `data/signals.csv`
- Shows signals in a Streamlit dashboard

## Important

This project is for research and paper trading first. Backtests and ML accuracy do not guarantee future profit.
