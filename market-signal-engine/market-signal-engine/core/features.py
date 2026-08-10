import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

FEATURE_COLUMNS = [
    "Open","High","Low","Close","Volume",
    "ema9","ema21","ema50","rsi",
    "macd","macd_signal","atr","volume_avg"
]

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    df = df.copy()
    df["ema9"] = EMAIndicator(close, window=9).ema_indicator()
    df["ema21"] = EMAIndicator(close, window=21).ema_indicator()
    df["ema50"] = EMAIndicator(close, window=50).ema_indicator()
    df["rsi"] = RSIIndicator(close, window=14).rsi()

    macd = MACD(close)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    df["atr"] = AverageTrueRange(high, low, close, window=14).average_true_range()
    df["volume_avg"] = df["Volume"].rolling(20).mean()

    return df.dropna()
