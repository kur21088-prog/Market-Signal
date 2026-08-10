import yfinance as yf
import pandas as pd

def download(symbol: str, period="30d", interval="15m") -> pd.DataFrame:
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)
    if df is None or df.empty:
        return pd.DataFrame()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    needed = ["Open", "High", "Low", "Close", "Volume"]
    if not all(c in df.columns for c in needed):
        return pd.DataFrame()

    return df[needed].dropna().copy()
