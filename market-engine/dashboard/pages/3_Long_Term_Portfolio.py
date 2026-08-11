import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError
from longterm import run_longterm_scan

st.set_page_config(layout="wide")
st.title("🌳 Long-Term Hold & Portfolio")
st.caption("Daily-bar trend signals (weeks-to-months hold) on a separate, more conservative watchlist.")

if st.button("▶️ Run Long-Term Scan Now", type="primary"):
    with st.spinner("Scanning long-term watchlist... this can take a minute."):
        try:
            run_longterm_scan()
            st.success("Scan complete.")
        except Exception as e:
            st.error(f"Scan failed: {e}")
    st.rerun()


def load(path):
    p = Path(path)
    try:
        return pd.read_csv(p) if p.exists() else pd.DataFrame()
    except EmptyDataError:
        return pd.DataFrame()


signals_df = load("data/longterm_signals.csv")
alloc_df = load("data/portfolio_allocation.csv")

st.divider()
st.subheader("📊 Steady-Growth Portfolio Allocation")
if alloc_df.empty:
    st.info("No allocation yet — press Run Long-Term Scan Now above.")
else:
    c1, c2 = st.columns([2, 3])
    with c1:
        st.dataframe(alloc_df, use_container_width=True, hide_index=True)
    with c2:
        st.bar_chart(alloc_df.set_index("symbol")["weight_pct"])
    st.caption(
        "Weighted toward stronger trend and lower volatility, capped at 25% per "
        "position for diversification. This is a suggested target allocation, "
        "not a guarantee of returns."
    )

st.divider()
st.subheader("📋 All Long-Term Signals")
if signals_df.empty:
    st.info("No long-term signals yet.")
else:
    rating_order = {"STRONG_HOLD": 0, "HOLD": 1, "AVOID": 2, "NO_DATA": 3}
    signals_df["_sort"] = signals_df["rating"].map(rating_order).fillna(4)
    show = signals_df.sort_values(["_sort", "trend_score"], ascending=[True, False]).drop(columns="_sort")
    st.dataframe(show, use_container_width=True, hide_index=True)

st.warning("Not investment advice. This is a research/paper-trading tool — no real trades are placed.")
