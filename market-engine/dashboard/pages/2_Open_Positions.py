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
from style import inject_base_css, page_header, section_header, metric_card, GREEN, RED

st.set_page_config(layout="wide")
inject_base_css()
st_autorefresh(interval=60000, key="positions_refresh")

page_header("📂 Paper Positions", "Auto-opened from actionable signals, auto-closed on target or stop.")


def load(path):
    p = Path(path)
    try:
        return pd.read_csv(p) if p.exists() else pd.DataFrame()
    except EmptyDataError:
        return pd.DataFrame()


open_df = load("data/open_positions.csv")
closed_df = load("data/closed_positions.csv")

win_rate = (closed_df["pnl_pct"] > 0).mean() * 100 if not closed_df.empty else 0
avg_pnl = closed_df["pnl_pct"].mean() if not closed_df.empty else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Open Positions", str(len(open_df)))
with c2:
    metric_card("Closed Trades", str(len(closed_df)))
with c3:
    metric_card("Win Rate", f"{win_rate:.1f}%", sub_color=GREEN if win_rate >= 50 else RED)
with c4:
    metric_card("Avg P&L", f"{avg_pnl:+.2f}%", sub_color=GREEN if avg_pnl >= 0 else RED)

section_header("🟡 Open")
if open_df.empty:
    st.info("No open paper positions yet. Positions open automatically from actionable BUY/SELL signals when you run a scan.")
else:
    st.dataframe(
        open_df.sort_values("opened_at", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol"),
            "signal": st.column_config.TextColumn("Signal"),
            "entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
            "target1": st.column_config.NumberColumn("Target 1", format="$%.2f"),
            "target2": st.column_config.NumberColumn("Target 2", format="$%.2f"),
            "stop_loss": st.column_config.NumberColumn("Stop", format="$%.2f"),
            "confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%.0f%%"),
        },
    )

section_header("✅ Closed")
if closed_df.empty:
    st.info("No closed positions yet.")
else:
    st.dataframe(
        closed_df.sort_values("closed_at", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol"),
            "signal": st.column_config.TextColumn("Signal"),
            "entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
            "exit_price": st.column_config.NumberColumn("Exit", format="$%.2f"),
            "pnl_pct": st.column_config.NumberColumn("P&L", format="%+.2f%%"),
            "exit_reason": st.column_config.TextColumn("Exit Reason"),
        },
    )

st.markdown(
    '<div class="disclaimer">Paper trading only — no real orders are placed.</div>',
    unsafe_allow_html=True,
)
