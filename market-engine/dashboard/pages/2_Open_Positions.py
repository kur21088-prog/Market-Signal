import streamlit as st
import pandas as pd
from pathlib import Path
from pandas.errors import EmptyDataError
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide")
st_autorefresh(interval=60000, key="positions_refresh")
st.title("📂 Paper Positions")


def load(path):
    p = Path(path)
    try:
        return pd.read_csv(p) if p.exists() else pd.DataFrame()
    except EmptyDataError:
        return pd.DataFrame()


open_df = load("data/open_positions.csv")
closed_df = load("data/closed_positions.csv")

st.subheader("🟡 Open")
if open_df.empty:
    st.info("No open paper positions yet. Positions open automatically from actionable BUY/SELL signals when you run a scan.")
else:
    st.dataframe(open_df.sort_values("opened_at", ascending=False), use_container_width=True, hide_index=True)

st.divider()
st.subheader("✅ Closed")
if closed_df.empty:
    st.info("No closed positions yet.")
else:
    c1, c2, c3 = st.columns(3)
    win_rate = (closed_df["pnl_pct"] > 0).mean() * 100
    c1.metric("Closed trades", len(closed_df))
    c2.metric("Win rate", f"{win_rate:.1f}%")
    c3.metric("Avg P&L", f"{closed_df['pnl_pct'].mean():.2f}%")
    st.dataframe(closed_df.sort_values("closed_at", ascending=False), use_container_width=True, hide_index=True)

st.warning("Paper trading only — no real orders are placed.")
