import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
_DASHBOARD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_DASHBOARD))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pandas.errors import EmptyDataError
from longterm import run_longterm_scan
from style import (
    inject_base_css, page_header, section_header, metric_card,
    GREEN, RED, BLUE, AMBER, with_signal_labels, parse_spark_column,
)
from core.paths import OUTPUT_DIR

st.set_page_config(layout="wide")
inject_base_css()

page_header("🌳 Long-Term Hold & Portfolio", "Daily-bar trend signals (weeks-to-months hold) on a separate, more conservative watchlist.")

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


signals_df = load(OUTPUT_DIR / "longterm_signals.csv")
alloc_df = load(OUTPUT_DIR / "portfolio_allocation.csv")

strong = int((signals_df["rating"] == "STRONG_HOLD").sum()) if not signals_df.empty else 0
hold = int((signals_df["rating"] == "HOLD").sum()) if not signals_df.empty else 0
avoid = int((signals_df["rating"] == "AVOID").sum()) if not signals_df.empty else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Strong Holds", str(strong), sub_color=GREEN)
with c2:
    metric_card("Holds", str(hold), sub_color=BLUE)
with c3:
    metric_card("Avoid", str(avoid), sub_color=RED)
with c4:
    metric_card("Portfolio Positions", str(len(alloc_df)))

section_header("📊 Steady-Growth Portfolio Allocation")
if alloc_df.empty:
    st.info("No allocation yet — press Run Long-Term Scan Now above.")
else:
    left, right = st.columns([3, 2])

    with left:
        st.dataframe(
            alloc_df,
            width="stretch",
            hide_index=True,
            column_config={
                "symbol": st.column_config.TextColumn("Symbol"),
                "weight_pct": st.column_config.ProgressColumn("Target Weight", min_value=0, max_value=alloc_df["weight_pct"].max(), format="%.1f%%"),
                "trend_score": st.column_config.ProgressColumn("Trend Score", min_value=0, max_value=100, format="%.0f"),
                "volatility": st.column_config.NumberColumn("Volatility (ann.)", format="%.1f%%"),
                "rating": st.column_config.TextColumn("Rating"),
            },
        )

    with right:
        colors = [GREEN, BLUE, AMBER, "#7C5CFF", "#2FD9C8", "#FF9F5A", "#5AC8FA", "#B983FF"]
        fig = go.Figure(data=[go.Pie(
            labels=alloc_df["symbol"],
            values=alloc_df["weight_pct"],
            hole=0.62,
            marker=dict(colors=colors * (len(alloc_df) // len(colors) + 1), line=dict(color="#0B0F14", width=2)),
            textinfo="label+percent",
            textfont=dict(color="#E6EDF3", size=12),
        )])
        fig.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
        )
        st.plotly_chart(fig, width="stretch")

    st.caption(
        "Weighted toward stronger trend and lower volatility, capped per position for "
        "diversification. This is a suggested target allocation, not a guarantee of returns."
    )

section_header("📋 All Long-Term Signals")
if signals_df.empty:
    st.info("No long-term signals yet.")
else:
    rating_order = {"STRONG_HOLD": 0, "HOLD": 1, "AVOID": 2, "NO_DATA": 3}
    signals_df["_sort"] = signals_df["rating"].map(rating_order).fillna(4)
    show = signals_df.sort_values(["_sort", "trend_score"], ascending=[True, False]).drop(columns="_sort")
    show = with_signal_labels(show, "rating")
    show = parse_spark_column(show, "spark")

    cols = ["symbol", "rating", "trend_score", "volatility", "price", "spark", "reason"]
    cols = [c for c in cols if c in show.columns]

    st.dataframe(
        show[cols],
        width="stretch",
        hide_index=True,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol"),
            "rating": st.column_config.TextColumn("Rating"),
            "trend_score": st.column_config.ProgressColumn("Trend Score", min_value=0, max_value=100, format="%.0f"),
            "volatility": st.column_config.NumberColumn("Volatility (ann.)", format="%.1f%%"),
            "price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "spark": st.column_config.LineChartColumn("30-Day Trend", width="small"),
            "reason": st.column_config.TextColumn("Why"),
        },
    )

st.markdown(
    '<div class="disclaimer">Not investment advice. This is a research/paper-trading tool — no real trades are placed.</div>',
    unsafe_allow_html=True,
)
