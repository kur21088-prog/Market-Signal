from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from core.data import download
from core.features import add_features, FEATURE_COLUMNS

with open("data/watchlist.json") as f:
    groups = json.load(f)

# Keep first few symbols for a quick starter model.
symbols = (groups.get("stocks", [])[:5] + groups.get("crypto", [])[:4])

frames = []
for symbol in symbols:
    print(f"Building {symbol}...")
    df = add_features(download(symbol, period="1y", interval="1h"))
    if df.empty:
        continue
    df["future_close"] = df["Close"].shift(-3)
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

acc = accuracy_score(y_test, pred)
Path("models").mkdir(exist_ok=True)
joblib.dump(model, "models/market_ai_v2.pkl")

print(f"Out-of-time accuracy: {acc:.2%}")
print("Saved models/market_ai_v2.pkl")
