import pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

FEATURE_COLUMNS_LT = [
    "Open", "High", "Low", "Close", "Volume",
    "ema20", "ema50", "ema200", "rsi",
    "macd", "macd_signal", "atr", "volume_avg", "volatility",
]


def add_features_lt(df: pd.DataFrame) -> pd.DataFrame:
    """Daily-bar features for long-term trend/hold analysis. Needs ~250+ rows
    (roughly 1y+ of daily bars) for the 200-day EMA and volatility window to
    warm up cleanly."""
    if df.empty:
        return df

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    df = df.copy()
    df["ema20"] = EMAIndicator(close, window=20).ema_indicator()
    df["ema50"] = EMAIndicator(close, window=50).ema_indicator()
    df["ema200"] = EMAIndicator(close, window=200).ema_indicator()
    df["rsi"] = RSIIndicator(close, window=14).rsi()

    macd = MACD(close)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    df["atr"] = AverageTrueRange(high, low, close, window=14).average_true_range()
    df["volume_avg"] = df["Volume"].rolling(50).mean()

    # Annualized volatility (%) from a 60-day rolling window of daily returns.
    # Used to favor steadier names in the portfolio allocation.
    daily_returns = close.pct_change()
    df["volatility"] = daily_returns.rolling(60).std() * (252 ** 0.5) * 100

    return df.dropna()
