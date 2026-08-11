import json
from pathlib import Path
from dataclasses import asdict
import pandas as pd
from core.data import download
from core.features_lt import add_features_lt
from core.signals_lt import make_longterm_signal
from core.portfolio import build_allocation

WATCHLIST = Path("data/watchlist_longterm.json")
SIGNALS_OUT = Path("data/longterm_signals.csv")
ALLOC_OUT = Path("data/portfolio_allocation.csv")

SPARK_BARS = 30  # how many recent daily closes to keep for the sparkline chart


def run_longterm_scan(period="2y", interval="1d"):
    with WATCHLIST.open() as f:
        groups = json.load(f)
    symbols = [s for values in groups.values() for s in values]

    rows = []
    print("\n=== LONG-TERM HOLD SCAN ===")
    for symbol in symbols:
        try:
            df = add_features_lt(download(symbol, period=period, interval=interval))
            sig = make_longterm_signal(symbol, df)
            d = asdict(sig)
            spark = df["Close"].tail(SPARK_BARS).round(2).tolist() if not df.empty else []
            d["spark"] = json.dumps(spark)
            rows.append(d)
            print(f"{symbol}: {sig.rating} | trend {sig.trend_score} | vol {sig.volatility}%")
        except Exception as e:
            print(f"{symbol}: ERROR | {e}")

    signals_df = pd.DataFrame(rows)
    signals_df.to_csv(SIGNALS_OUT, index=False)

    allocation_df = build_allocation(signals_df)
    allocation_df.to_csv(ALLOC_OUT, index=False)

    print(f"\nSaved {len(signals_df)} long-term signals to {SIGNALS_OUT}")
    print(f"Saved {len(allocation_df)} portfolio allocation rows to {ALLOC_OUT}")
    return signals_df, allocation_df


if __name__ == "__main__":
    run_longterm_scan()
