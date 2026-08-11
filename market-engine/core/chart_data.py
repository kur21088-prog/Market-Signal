import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange, BollingerBands


def add_chart_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Adds a full indicator set for interactive charting. Unlike core/features.py
    and core/features_lt.py, this does NOT dropna the whole frame — a chart should
    still show early candles even before a slow-moving indicator (e.g. EMA200)
    has warmed up; Plotly just won't draw a line where the value is NaN."""
    if df.empty:
        return df

    df = df.copy()
    close, high, low = df["Close"], df["High"], df["Low"]

    df["ema9"] = EMAIndicator(close, window=9).ema_indicator()
    df["ema21"] = EMAIndicator(close, window=21).ema_indicator()
    df["ema50"] = EMAIndicator(close, window=50).ema_indicator()
    df["ema200"] = EMAIndicator(close, window=200).ema_indicator()

    df["rsi"] = RSIIndicator(close, window=14).rsi()

    macd = MACD(close)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    bb = BollingerBands(close, window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_mid"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()

    df["atr"] = AverageTrueRange(high, low, close, window=14).average_true_range()
    df["volume_avg"] = df["Volume"].rolling(20).mean()

    return df
