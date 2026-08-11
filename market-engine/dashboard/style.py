import streamlit as st
import pandas as pd

GREEN = "#00D26A"
RED = "#FF5C5C"
BLUE = "#4FA3FF"
AMBER = "#F2C94C"
MUTED = "#8B949E"
CARD = "#141A21"
BORDER = "#242C36"
TEXT = "#E6EDF3"

SIGNAL_LABEL = {
    "BUY": "🟢 BUY",
    "SELL": "🔴 SELL",
    "WAIT": "⚪ WAIT",
    "STRONG_HOLD": "🟢 STRONG HOLD",
    "HOLD": "🔵 HOLD",
    "AVOID": "🔴 AVOID",
    "NO_DATA": "⚪ NO DATA",
}


def inject_base_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, sans-serif;
    }}

    .block-container {{
        padding-top: 2rem;
        max-width: 1300px;
    }}

    .metric-card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 18px 20px;
        height: 100%;
    }}
    .metric-label {{
        color: {MUTED};
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }}
    .metric-value {{
        color: {TEXT};
        font-size: 30px;
        font-weight: 800;
        line-height: 1.1;
    }}
    .metric-sub {{
        font-size: 13px;
        font-weight: 600;
        margin-top: 6px;
    }}

    .page-header {{
        font-size: 32px;
        font-weight: 800;
        color: {TEXT};
        margin-bottom: 0;
    }}
    .page-sub {{
        color: {MUTED};
        font-size: 15px;
        margin-bottom: 22px;
    }}
    .section-header {{
        font-size: 18px;
        font-weight: 700;
        color: {TEXT};
        margin: 28px 0 10px 0;
    }}

    div[data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid {BORDER};
    }}

    div[data-testid="stButton"] button {{
        border-radius: 10px;
        font-weight: 700;
        padding: 0.5rem 1.4rem;
    }}

    .disclaimer {{
        color: {MUTED};
        font-size: 12.5px;
        border-top: 1px solid {BORDER};
        padding-top: 14px;
        margin-top: 30px;
    }}
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = ""):
    st.markdown(f'<div class="page-header">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-sub">{subtitle}</div>', unsafe_allow_html=True)


def section_header(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, sub: str = "", sub_color: str = MUTED):
    sub_html = f'<div class="metric-sub" style="color:{sub_color}">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def pnl_color(value: float) -> str:
    return GREEN if value >= 0 else RED


def with_signal_labels(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Return a copy with a human/emoji-friendly display column.
    Leaves the original column untouched for filtering/sorting elsewhere."""
    out = df.copy()
    out[column] = out[column].map(lambda v: SIGNAL_LABEL.get(v, v))
    return out


def parse_spark_column(df: pd.DataFrame, column: str = "spark") -> pd.DataFrame:
    """Decode the JSON-encoded price-history column written by scanner.py /
    longterm.py back into plain Python lists for LineChartColumn."""
    import json
    out = df.copy()
    if column in out.columns:
        out[column] = out[column].apply(
            lambda v: json.loads(v) if isinstance(v, str) and v else []
        )
    return out
