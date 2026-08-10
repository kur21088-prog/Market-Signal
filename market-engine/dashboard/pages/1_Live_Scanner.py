import streamlit as st
import pandas as pd
from pathlib import Path
from pandas.errors import EmptyDataError
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st_autorefresh(interval=60000, key="scanner_refresh")
st.title("📡 Live Market Scanner")

file = Path("data/signals.csv")
try:
    df = pd.read_csv(file) if file.exists() else pd.DataFrame()
except EmptyDataError:
    df = pd.DataFrame()

if df.empty:
    st.info("No actionable signals right now.")
else:
    buy = df[df["signal"] == "BUY"].sort_values("confidence", ascending=False)
    sell = df[df["signal"] == "SELL"].sort_values("confidence", ascending=False)

    left, right = st.columns(2)

    with left:
        st.subheader("🟢 BUY Watchlist")
        st.dataframe(buy.head(10), use_container_width=True, hide_index=True)

    with right:
        st.subheader("🔴 SELL Watchlist")
        st.dataframe(sell.head(10), use_container_width=True, hide_index=True)
