import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
_DASHBOARD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_DASHBOARD))

import json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.data import download
from core.chart_data import add_chart_indicators
from style import inject_base_css, page_header, section_header, GREEN, RED, BLUE, AMBER, MUTED

st.set_page_config(layout="wide")
inject_base_css()

page_header("📉 Charts", "Look up any stock, crypto, ETF, or futures symbol with indicators overlaid.")

TIMEFRAMES = {
    "Intraday · 15m (30 days)": ("15m", "30d"),
    "Hourly · 1h (1 year)": ("1h", "1y"),
    "Daily · 1d (2 years)": ("1d", "2y"),
    "Weekly · 1wk (5 years)": ("1wk", "5y"),
}


def load_watchlist_symbols():
    symbols = set()
    for path in ["data/watchlist.json", "data/watchlist_longterm.json"]:
        p = Path(path)
        if p.exists():
            try:
                groups = json.loads(p.read_text())
                for v in groups.values():
                    symbols.update(v)
            except Exception:
                pass
    return sorted(symbols)


quick_symbols = ["Custom..."] + load_watchlist_symbols()

top = st.columns([1.3, 1.6, 3.5])
with top[0]:
    quick_pick = st.selectbox("Quick pick", quick_symbols)
with top[1]:
    default_symbol = "" if quick_pick == "Custom..." else quick_pick
    symbol = st.text_input(
        "Or type any symbol (BTC-USD, GC=F, TSLA, etc.)",
        value=default_symbol or "AAPL",
    ).strip().upper()
with top[2]:
    timeframe_label = st.selectbox("Timeframe", list(TIMEFRAMES.keys()), index=2)
    interval, period = TIMEFRAMES[timeframe_label]

ind_cols = st.columns(6)
with ind_cols[0]:
    show_ema = st.checkbox("EMA 9/21/50", value=True)
with ind_cols[1]:
    show_ema200 = st.checkbox("EMA 200", value=False)
with ind_cols[2]:
    show_bb = st.checkbox("Bollinger Bands", value=False)
with ind_cols[3]:
    show_volume = st.checkbox("Volume", value=True)
with ind_cols[4]:
    show_rsi = st.checkbox("RSI", value=True)
with ind_cols[5]:
    show_macd = st.checkbox("MACD", value=True)

if not symbol:
    st.info("Enter a symbol above to load a chart.")
    st.stop()

with st.spinner(f"Loading {symbol}..."):
    try:
        raw = download(symbol, period=period, interval=interval)
    except Exception as e:
        st.error(f"Couldn't fetch {symbol}: {e}")
        st.stop()

if raw.empty:
    st.error(f"No data found for '{symbol}'. Check the symbol — Yahoo format examples: AAPL, BTC-USD, GC=F, EURUSD=X.")
    st.stop()

df = add_chart_indicators(raw)
last = df.iloc[-1]
prev = df.iloc[-2] if len(df) > 1 else last
change = float(last["Close"] - prev["Close"])
change_pct = (change / prev["Close"] * 100) if prev["Close"] else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{symbol}</div>
        <div class="metric-value">${last['Close']:,.2f}</div>
        <div class="metric-sub" style="color:{GREEN if change >= 0 else RED}">
            {'+' if change >= 0 else ''}{change:,.2f} ({change_pct:+.2f}%)
        </div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">RSI (14)</div>
        <div class="metric-value">{last['rsi']:.0f}</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Day Range</div>
        <div class="metric-value" style="font-size:20px;">${last['Low']:,.2f} – ${last['High']:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Volume</div>
        <div class="metric-value" style="font-size:20px;">{last['Volume']:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

# --- build dynamic subplot layout based on toggled indicators ---
row_specs = ["price"]
if show_volume:
    row_specs.append("volume")
if show_rsi:
    row_specs.append("rsi")
if show_macd:
    row_specs.append("macd")

heights = {"price": 0.55, "volume": 0.15, "rsi": 0.15, "macd": 0.15}
row_heights = [heights[r] for r in row_specs]
total = sum(row_heights)
row_heights = [h / total for h in row_heights]

fig = make_subplots(
    rows=len(row_specs), cols=1, shared_xaxes=True, vertical_spacing=0.03,
    row_heights=row_heights,
)
row_idx = {name: i + 1 for i, name in enumerate(row_specs)}

fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
    name=symbol, increasing_line_color=GREEN, decreasing_line_color=RED,
), row=row_idx["price"], col=1)

if show_ema:
    for col, color in [("ema9", AMBER), ("ema21", BLUE), ("ema50", "#B983FF")]:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], name=col.upper(), line=dict(width=1.3, color=color)),
                      row=row_idx["price"], col=1)
if show_ema200:
    fig.add_trace(go.Scatter(x=df.index, y=df["ema200"], name="EMA200", line=dict(width=1.3, color="#FF9F5A")),
                  row=row_idx["price"], col=1)
if show_bb:
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Upper", line=dict(width=1, color=MUTED, dash="dot")),
                  row=row_idx["price"], col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Lower", line=dict(width=1, color=MUTED, dash="dot"),
                             fill="tonexty", fillcolor="rgba(139,148,158,0.08)"),
                  row=row_idx["price"], col=1)

if show_volume:
    vol_colors = [GREEN if c >= o else RED for o, c in zip(df["Open"], df["Close"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=vol_colors, opacity=0.7),
                  row=row_idx["volume"], col=1)

if show_rsi:
    fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI", line=dict(width=1.3, color=BLUE)),
                  row=row_idx["rsi"], col=1)
    fig.add_hline(y=70, line_dash="dot", line_color=RED, opacity=0.5, row=row_idx["rsi"], col=1)
    fig.add_hline(y=30, line_dash="dot", line_color=GREEN, opacity=0.5, row=row_idx["rsi"], col=1)

if show_macd:
    hist_colors = [GREEN if v >= 0 else RED for v in df["macd_hist"].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df["macd_hist"], name="MACD Hist", marker_color=hist_colors, opacity=0.6),
                  row=row_idx["macd"], col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD", line=dict(width=1.3, color=AMBER)),
                  row=row_idx["macd"], col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Signal", line=dict(width=1.3, color=BLUE)),
                  row=row_idx["macd"], col=1)

fig.update_layout(
    height=650,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E6EDF3"),
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    margin=dict(t=10, b=10, l=10, r=10),
    hovermode="x unified",
)
fig.update_xaxes(gridcolor="#1C2229", showgrid=True)
fig.update_yaxes(gridcolor="#1C2229", showgrid=True)

st.plotly_chart(fig, width="stretch")

st.markdown(
    '<div class="disclaimer">Chart and indicators are for research only — not investment advice.</div>',
    unsafe_allow_html=True,
)
