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

## Deploying to Railway (live 24/7)

This runs as a single Railway service: the Streamlit dashboard plus a background
loop that scans every 15 minutes (short-term) and once a day (long-term) — even
when nobody has the dashboard open.

1. Push this repo to GitHub, then in Railway: **New Project → Deploy from GitHub repo**.
2. Railway auto-detects Python and reads `railway.json` for the start command (or
   `Procfile` as a fallback) — no manual config needed there.
3. **Add a Volume** so scan results, paper positions, and the trained model
   survive redeploys: in the service, right-click the canvas or use ⌘K →
   **New Volume**, mount it at `/app/state`.
4. **Set environment variables** on the service:
   - `OUTPUT_DIR` = `/app/state`
   - `MODELS_DIR` = `/app/state/models`
5. Deploy. Railway gives you a public URL — that's your live dashboard.

Notes:
- Watchlists (`data/watchlist.json`, `data/watchlist_longterm.json`) are
  git-tracked and always read from the repo, not the volume — edit them
  locally and `git push` to update the scan universe.
- If you skip the Volume/env vars, the app still runs fine, it just starts
  from empty signals/positions/model on every redeploy.
- To retrain the model on Railway with the persisted volume, use the
  Railway CLI (`railway run python scripts/build_model.py`) or a one-off
  Railway shell, since it's not part of the automatic loop.

## Important

This project is for research and paper trading first. Backtests and ML accuracy do not guarantee future profit.
