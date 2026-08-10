import streamlit as st
import pandas as pd
from pathlib import Path
from pandas.errors import EmptyDataError
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Market AI Engine", page_icon="📈", layout="wide")
st_autorefresh(interval=60000, key="home_refresh")

st.title("📈 Market AI Engine")
st.caption("Paper-trading-first market scanner")

signals_file = Path("data/signals.csv")

try:
    df = pd.read_csv(signals_file) if signals_file.exists() else pd.DataFrame()
except EmptyDataError:
    df = pd.DataFrame()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Actionable signals", len(df))
c2.metric("BUY", int((df["signal"] == "BUY").sum()) if not df.empty else 0)
c3.metric("SELL", int((df["signal"] == "SELL").sum()) if not df.empty else 0)
c4.metric("Refresh", "60 sec")

st.divider()
st.subheader("⭐ Top Opportunities")

if df.empty:
    st.info("Run: python scripts/run_scan.py")
else:
    show = df.sort_values("confidence", ascending=False).head(10)
    st.dataframe(show, use_container_width=True, hide_index=True)

st.warning("Research / paper trading first. Signals and model outputs are not guaranteed.")
