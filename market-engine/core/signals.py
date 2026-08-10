from dataclasses import dataclass
from pathlib import Path
import joblib
import pandas as pd
from core.features import FEATURE_COLUMNS

MODEL_PATH = Path("models/market_ai_v2.pkl")


@dataclass
class Signal:
    symbol: str
    signal: str
    confidence: float
    entry: float | None
    target1: float | None
    target2: float | None
    stop_loss: float | None
    reason: str
    timeframe: str
    ml_probability: float | None = None


def load_model():
    """Load the ML model once. Returns None if no model has been trained yet."""
    if not MODEL_PATH.exists():
        return None
    try:
        return joblib.load(MODEL_PATH)
    except Exception:
        return None


def _technical_scores(row):
    buy = sell = 0
    buy_reasons, sell_reasons = [], []

    if row["ema9"] > row["ema21"]:
        buy += 20; buy_reasons.append("short trend up")
    else:
        sell += 20; sell_reasons.append("short trend down")

    if row["Close"] > row["ema50"]:
        buy += 20; buy_reasons.append("price above trend")
    else:
        sell += 20; sell_reasons.append("price below trend")

    if row["rsi"] > 55:
        buy += 20; buy_reasons.append("RSI bullish")
    elif row["rsi"] < 45:
        sell += 20; sell_reasons.append("RSI bearish")

    if row["macd"] > row["macd_signal"]:
        buy += 20; buy_reasons.append("MACD bullish")
    else:
        sell += 20; sell_reasons.append("MACD bearish")

    if row["Volume"] > row["volume_avg"]:
        buy += 10
        sell += 10

    return buy, sell, buy_reasons, sell_reasons


def _ml_probability(row, model):
    if model is None:
        return None
    try:
        X = pd.DataFrame([row])[FEATURE_COLUMNS]
        return float(model.predict_proba(X)[0][1] * 100)
    except Exception:
        return None


def make_signal(symbol, df, timeframe="15m", min_confidence=80, model=None):
    if df.empty:
        return Signal(symbol, "WAIT", 0, None, None, None, None, "No data", timeframe)

    row = df.iloc[-1]
    buy, sell, buy_reasons, sell_reasons = _technical_scores(row)
    ml_up = _ml_probability(row, model)

    tech_signal = "BUY" if buy > sell else "SELL"
    tech_score = max(buy, sell)

    # Blend ML if available. ML probability is directional:
    # for SELL, use probability of DOWN = 100 - probability of UP.
    directional_ml = None
    if ml_up is not None:
        directional_ml = ml_up if tech_signal == "BUY" else 100 - ml_up
        confidence = 0.7 * tech_score + 0.3 * directional_ml
    else:
        confidence = tech_score

    if confidence < min_confidence:
        return Signal(symbol, "WAIT", round(confidence, 1), None, None, None, None,
                      "Setup below confidence threshold", timeframe,
                      round(ml_up, 1) if ml_up is not None else None)

    entry = float(row["Close"])
    atr = float(row["atr"])

    if tech_signal == "BUY":
        target2 = entry + atr * 1.5
        stop = entry - atr * 0.9
        target1 = entry + (target2 - entry) * 0.5
        reason = ", ".join(buy_reasons)
    else:
        target2 = entry - atr * 1.5
        stop = entry + atr * 0.9
        target1 = entry - (entry - target2) * 0.5
        reason = ", ".join(sell_reasons)

    return Signal(
        symbol=symbol,
        signal=tech_signal,
        confidence=round(confidence, 1),
        entry=round(entry, 2),
        target1=round(target1, 2),
        target2=round(target2, 2),
        stop_loss=round(stop, 2),
        reason=reason,
        timeframe=timeframe,
        ml_probability=round(ml_up, 1) if ml_up is not None else None,
    )
