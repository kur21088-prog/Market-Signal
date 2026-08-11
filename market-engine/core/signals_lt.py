from dataclasses import dataclass


@dataclass
class LongTermSignal:
    symbol: str
    rating: str          # "STRONG_HOLD", "HOLD", "AVOID", or "NO_DATA"
    trend_score: float   # 0-100
    volatility: float    # annualized %, lower = steadier
    price: float
    reason: str


def _trend_score(row):
    score = 0
    reasons = []

    if row["Close"] > row["ema200"]:
        score += 30
        reasons.append("above 200-day trend")
    else:
        reasons.append("below 200-day trend")

    if row["ema50"] > row["ema200"]:
        score += 25
        reasons.append("50/200 uptrend")

    if row["macd"] > row["macd_signal"]:
        score += 20
        reasons.append("MACD bullish")

    if 40 <= row["rsi"] <= 70:
        score += 15
        reasons.append("RSI healthy")
    elif row["rsi"] > 80:
        reasons.append("RSI overbought caution")

    if row["Close"] > row["ema50"]:
        score += 10
        reasons.append("price above 50-day")

    return score, reasons


def make_longterm_signal(symbol, df) -> LongTermSignal:
    if df.empty:
        return LongTermSignal(symbol, "NO_DATA", 0, 0, 0, "No data")

    row = df.iloc[-1]
    score, reasons = _trend_score(row)
    vol = float(row["volatility"])

    if score >= 70:
        rating = "STRONG_HOLD"
    elif score >= 45:
        rating = "HOLD"
    else:
        rating = "AVOID"

    return LongTermSignal(
        symbol=symbol,
        rating=rating,
        trend_score=round(float(score), 1),
        volatility=round(vol, 1),
        price=round(float(row["Close"]), 2),
        reason=", ".join(reasons),
    )
