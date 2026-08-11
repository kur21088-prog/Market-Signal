import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from core.data import download
from core.features import add_features, FEATURE_COLUMNS

with open("data/watchlist.json") as f:
    groups = json.load(f)

# Train on every symbol the scanner actually watches, not a subset,
# so the model has seen the same instruments it will be scoring.
symbols = [s for values in groups.values() for s in values]

FUTURE_BARS = 3  # how many candles ahead we're predicting up/down for

frames = []
for symbol in symbols:
    print(f"Building {symbol}...")
    df = add_features(download(symbol, period="1y", interval="1h"))
    if df.empty:
        print(f"  skipped (no data)")
        continue
    df["future_close"] = df["Close"].shift(-FUTURE_BARS)
    df["target"] = (df["future_close"] > df["Close"]).astype(int)
    df["symbol"] = symbol
    frames.append(df.dropna())

if not frames:
    raise SystemExit("No training data downloaded.")

data = pd.concat(frames).sort_index()
split = int(len(data) * 0.8)

train = data.iloc[:split]
test = data.iloc[split:]

X_train = train[FEATURE_COLUMNS]
y_train = train["target"]
X_test = test[FEATURE_COLUMNS]
y_test = test["target"]

model = RandomForestClassifier(
    n_estimators=400,
    max_depth=12,
    min_samples_leaf=5,
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)
pred = model.predict(X_test)

print("\n=== MODEL RESULTS ===")
print(f"Trained on {len(symbols)} symbols, {len(data)} total rows")
print(f"Out-of-time accuracy: {accuracy_score(y_test, pred):.2%}")
print(classification_report(y_test, pred, target_names=["DOWN", "UP"], digits=3))

Path("models").mkdir(exist_ok=True)
joblib.dump(model, "models/market_ai_v2.pkl")
print("Saved models/market_ai_v2.pkl")
