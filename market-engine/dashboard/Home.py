import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
_DASHBOARD = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_DASHBOARD))

import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError
from streamlit_autorefresh import st_autorefresh
from scanner import run_scan
from style import (
    inject_base_css, page_header, section_header, metric_card, beginner_tip,
    GREEN, RED, with_signal_labels, parse_spark_column,
)
from core.paths import OUTPUT_DIR

st.set_page_config(page_title="Market AI Engine", page_icon="📈", layout="wide")
inject_base_css()
st_autorefresh(interval=60000, key="home_refresh")

page_header("📈 Market AI Engine", "Paper-trading-first market scanner — short-term signals, long-term holds, and a steady-growth portfolio.")

beginner_tip("New here? Start with this", """
This page shows stocks and crypto with a strong signal <b>right now</b>.
<b>🟢 BUY</b> means the price looks likely to rise short-term. <b>🔴 SELL</b> means it looks likely to fall.
The confidence bar shows how strong the signal is — as a beginner, focus only on signals
<b>80% and above</b>, and treat lower ones as noise. Everything here uses pretend money
(paper trading) so you can practice without risk — check the <b>Paper Wallet</b> page to
see how your signals would actually perform in dollars.
""")

if st.button("▶️ Run Scan Now", type="primary"):
    with st.spinner("Scanning watchlist... this can take up to a minute."):
        try:
            run_scan()
            st.success("Scan complete.")
        except Exception as e:
            st.error(f"Scan failed: {e}")
    st.rerun()

signals_file = OUTPUT_DIR / "signals.csv"
try:
    df = pd.read_csv(signals_file) if signals_file.exists() else pd.DataFrame()
except EmptyDataError:
    df = pd.DataFrame()

buy_count = int((df["signal"] == "BUY").sum()) if not df.empty else 0
sell_count = int((df["signal"] == "SELL").sum()) if not df.empty else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Actionable Signals", str(len(df)))
with c2:
    metric_card("Buy Setups", str(buy_count), sub="↑ bullish" if buy_count else "", sub_color=GREEN)
with c3:
    metric_card("Sell Setups", str(sell_count), sub="↓ bearish" if sell_count else "", sub_color=RED)
with c4:
    metric_card("Auto-Refresh", "60 sec")

section_header("⭐ Top Opportunities")

if df.empty:
    st.info("No signals yet — press Run Scan Now above.")
else:
    show = df.sort_values("confidence", ascending=False).head(10)
    show = with_signal_labels(show, "signal")
    show = parse_spark_column(show, "spark")

    cols = ["symbol", "signal", "confidence", "entry", "target1", "target2", "stop_loss", "spark", "reason"]
    cols = [c for c in cols if c in show.columns]

    st.dataframe(
        show[cols],
        width="stretch",
        hide_index=True,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol"),
            "signal": st.column_config.TextColumn("Signal"),
            "confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%.0f%%"),
            "entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
            "target1": st.column_config.NumberColumn("Target 1", format="$%.2f"),
            "target2": st.column_config.NumberColumn("Target 2", format="$%.2f"),
            "stop_loss": st.column_config.NumberColumn("Stop", format="$%.2f"),
            "spark": st.column_config.LineChartColumn("Recent Price", width="small"),
            "reason": st.column_config.TextColumn("Why"),
        },
    )

st.markdown(
    '<div class="disclaimer">Research / paper trading first. Signals and model outputs are not guaranteed.</div>',
    unsafe_allow_html=True,
)
