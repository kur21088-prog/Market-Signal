import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
_DASHBOARD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_DASHBOARD))

import streamlit as st
import pandas as pd
from pandas.errors import EmptyDataError
from streamlit_autorefresh import st_autorefresh
from scanner import run_scan
from style import inject_base_css, page_header, section_header, beginner_tip, GREEN, RED, parse_spark_column
from core.paths import OUTPUT_DIR

st.set_page_config(layout="wide")
inject_base_css()
st_autorefresh(interval=60000, key="scanner_refresh")

page_header("📡 Live Market Scanner", "Short-term BUY/SELL setups from the 15-minute scan.")

beginner_tip("How to read a signal", """
<b>Entry</b> is the suggested price to buy (or sell) at. <b>Target 1</b> and
<b>Target 2</b> are price levels where it may make sense to take profit —
Target 1 first, Target 2 if it keeps moving your way. <b>Stop</b> is your exit
if the trade goes against you — this limits how much you could lose. A simple
rule for beginners: only act on signals with <b>80%+ confidence</b>, and never
risk more than you're prepared to lose. This scanner already opens a pretend
position for you automatically — see the <b>Paper Wallet</b> page to track it.
""")

if st.button("▶️ Run Scan Now", type="primary"):
    with st.spinner("Scanning watchlist... this can take up to a minute."):
        try:
            run_scan()
            st.success("Scan complete.")
        except Exception as e:
            st.error(f"Scan failed: {e}")
    st.rerun()

file = OUTPUT_DIR / "signals.csv"
try:
    df = pd.read_csv(file) if file.exists() else pd.DataFrame()
except EmptyDataError:
    df = pd.DataFrame()

if df.empty:
    st.info("No actionable signals right now. Press Run Scan Now above.")
else:
    df = parse_spark_column(df, "spark")
    buy = df[df["signal"] == "BUY"].sort_values("confidence", ascending=False)
    sell = df[df["signal"] == "SELL"].sort_values("confidence", ascending=False)

    col_config = {
        "symbol": st.column_config.TextColumn("Symbol"),
        "confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%.0f%%"),
        "entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
        "target1": st.column_config.NumberColumn("Target 1", format="$%.2f"),
        "target2": st.column_config.NumberColumn("Target 2", format="$%.2f"),
        "stop_loss": st.column_config.NumberColumn("Stop", format="$%.2f"),
        "spark": st.column_config.LineChartColumn("Recent Price", width="small"),
        "reason": st.column_config.TextColumn("Why"),
    }
    cols = ["symbol", "confidence", "entry", "target1", "target2", "stop_loss", "spark", "reason"]
    cols = [c for c in cols if c in df.columns]

    left, right = st.columns(2)

    with left:
        section_header(f"🟢 BUY Watchlist ({len(buy)})")
        if buy.empty:
            st.caption("No BUY setups right now.")
        else:
            st.dataframe(buy[cols].head(10), width="stretch", hide_index=True, column_config=col_config)

    with right:
        section_header(f"🔴 SELL Watchlist ({len(sell)})")
        if sell.empty:
            st.caption("No SELL setups right now.")
        else:
            st.dataframe(sell[cols].head(10), width="stretch", hide_index=True, column_config=col_config)

st.markdown(
    '<div class="disclaimer">Research / paper trading first. Signals and model outputs are not guaranteed.</div>',
    unsafe_allow_html=True,
)
