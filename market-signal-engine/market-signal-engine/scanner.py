import json
from dataclasses import asdict
from pathlib import Path
import pandas as pd
from core.data import download
from core.features import add_features
from core.signals import make_signal

WATCHLIST = Path("data/watchlist.json")
OUTPUT = Path("data/signals.csv")

def run_scan(interval="15m", period="30d", min_confidence=80):
    with WATCHLIST.open() as f:
        groups = json.load(f)

    symbols = []
    for values in groups.values():
        symbols.extend(values)

    rows = []
    print("\n=== MARKET AI SCANNER ===")

    for symbol in symbols:
        try:
            df = add_features(download(symbol, period=period, interval=interval))
            signal = make_signal(symbol, df, timeframe=interval, min_confidence=min_confidence)
            d = asdict(signal)
            if signal.signal in ("BUY", "SELL"):
                rows.append(d)
            print(f"{symbol}: {signal.signal} | {signal.confidence}%")
        except Exception as e:
            print(f"{symbol}: ERROR | {e}")

    out = pd.DataFrame(rows)
    if not out.empty:
        out = out.sort_values("confidence", ascending=False)
    out.to_csv(OUTPUT, index=False)
    print(f"\nSaved {len(out)} actionable signals to {OUTPUT}")
    return out

if __name__ == "__main__":
    run_scan()
