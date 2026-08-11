import json
from dataclasses import asdict
from pathlib import Path
import pandas as pd
from core.data import download
from core.features import add_features
from core.signals import make_signal, load_model
from core.positions import open_new_positions, update_open_positions
from core.paths import OUTPUT_DIR, WATCHLIST_SHORT

WATCHLIST = WATCHLIST_SHORT
OUTPUT = OUTPUT_DIR / "signals.csv"

SPARK_BARS = 20  # how many recent closes to keep for the sparkline chart


def run_scan(interval="15m", period="30d", min_confidence=80, manage_positions=True):
    with WATCHLIST.open() as f:
        groups = json.load(f)

    symbols = []
    for values in groups.values():
        symbols.extend(values)

    model = load_model()
    if model is None:
        print("No trained model found (models/market_ai_v2.pkl) — running on technicals only.")

    rows = []
    latest_prices = {}
    print("\n=== MARKET AI SCANNER ===")

    for symbol in symbols:
        try:
            df = add_features(download(symbol, period=period, interval=interval))
            if not df.empty:
                latest_prices[symbol] = float(df.iloc[-1]["Close"])
            signal = make_signal(symbol, df, timeframe=interval, min_confidence=min_confidence, model=model)
            d = asdict(signal)
            if signal.signal in ("BUY", "SELL"):
                spark = df["Close"].tail(SPARK_BARS).round(2).tolist() if not df.empty else []
                d["spark"] = json.dumps(spark)
                rows.append(d)
            print(f"{symbol}: {signal.signal} | {signal.confidence}%")
        except Exception as e:
            print(f"{symbol}: ERROR | {e}")

    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values("confidence", ascending=False)
    out.to_csv(OUTPUT, index=False)
    print(f"\nSaved {len(out)} actionable signals to {OUTPUT}")

    if manage_positions:
        closed = update_open_positions(latest_prices)
        opened = open_new_positions(out)
        if closed:
            print(f"Closed {closed} position(s).")
        if opened:
            print(f"Opened {opened} new paper position(s).")

    return out


if __name__ == "__main__":
    run_scan()
