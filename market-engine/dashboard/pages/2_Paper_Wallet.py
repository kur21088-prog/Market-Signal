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
from style import inject_base_css, page_header, section_header, metric_card, beginner_tip, GREEN, RED
from core import wallet as wallet_module
from core import positions as positions_module
from core.data import download

st.set_page_config(layout="wide")
inject_base_css()
st_autorefresh(interval=60000, key="wallet_refresh")

page_header("💼 Paper Wallet", "Practice investing with pretend money and track your real dollar profit and loss.")

beginner_tip("What is this?", """
This is a pretend trading account — no real money involved. Every time the
scanner finds a strong short-term signal, it automatically "invests" a set
amount here (default $500) so you can see how it would have gone. Green
numbers mean you'd be up, red means you'd be down. This is the best way to
learn how these signals actually perform before ever risking real money.
""")

w = wallet_module.load_wallet()

with st.expander("⚙️ Wallet settings"):
    c1, c2 = st.columns(2)
    with c1:
        new_balance = st.number_input("Starting balance ($)", min_value=100.0, value=float(w["starting_balance"]), step=500.0)
    with c2:
        new_per_trade = st.number_input("Amount to invest per signal ($)", min_value=10.0, value=float(w["per_trade"]), step=50.0)

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Save settings"):
            wallet_module.configure_wallet(new_balance, new_per_trade)
            st.success("Settings saved. This only changes future trades, not your current cash or history.")
            st.rerun()
    with b2:
        if st.button("🔄 Reset wallet (clears all history)", type="secondary"):
            st.session_state["confirm_reset"] = True

    if st.session_state.get("confirm_reset"):
        st.warning("This clears every open and closed paper position and resets your cash. This cannot be undone.")
        rc1, rc2 = st.columns(2)
        with rc1:
            if st.button("Yes, reset everything"):
                positions_module.reset_all(new_balance, new_per_trade)
                st.session_state["confirm_reset"] = False
                st.success("Wallet reset.")
                st.rerun()
        with rc2:
            if st.button("Cancel"):
                st.session_state["confirm_reset"] = False
                st.rerun()


def load(path):
    p = Path(path)
    try:
        return pd.read_csv(p) if p.exists() else pd.DataFrame()
    except EmptyDataError:
        return pd.DataFrame()


open_df = load(positions_module.OPEN_FILE)
closed_df = load(positions_module.CLOSED_FILE)

# --- fetch current prices for open positions to compute unrealized $ P/L ---
current_prices = {}
if not open_df.empty:
    with st.spinner("Checking current prices..."):
        for sym in open_df["symbol"].unique():
            try:
                df = download(sym, period="2d", interval="15m")
                if not df.empty:
                    current_prices[sym] = float(df.iloc[-1]["Close"])
            except Exception:
                pass

if not open_df.empty:
    open_df["invested_usd"] = pd.to_numeric(open_df["invested_usd"], errors="coerce").fillna(w["per_trade"])
    open_df["shares"] = pd.to_numeric(open_df["shares"], errors="coerce")
    open_df["shares"] = open_df.apply(
        lambda r: r["shares"] if pd.notna(r["shares"]) else (r["invested_usd"] / r["entry"] if r["entry"] else 0),
        axis=1,
    )
    open_df["current_price"] = open_df["symbol"].map(current_prices)
    open_df["unrealized_usd"] = open_df.apply(
        lambda r: (r["shares"] * (r["current_price"] - r["entry"]) if r["signal"] == "BUY"
                   else r["shares"] * (r["entry"] - r["current_price"]))
        if pd.notna(r["current_price"]) else 0.0,
        axis=1,
    )
    invested_total = open_df["invested_usd"].sum()
    unrealized_total = open_df["unrealized_usd"].sum()
else:
    invested_total = 0.0
    unrealized_total = 0.0

realized_total = pd.to_numeric(closed_df["pnl_usd"], errors="coerce").sum() if not closed_df.empty and "pnl_usd" in closed_df.columns else 0.0
win_rate = (pd.to_numeric(closed_df["pnl_usd"], errors="coerce") > 0).mean() * 100 if not closed_df.empty else 0

total_value = w["cash"] + invested_total + unrealized_total
total_return = total_value - w["starting_balance"]
total_return_pct = (total_return / w["starting_balance"] * 100) if w["starting_balance"] else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Total Portfolio Value", f"${total_value:,.2f}",
                sub=f"{'+' if total_return >= 0 else ''}{total_return:,.2f} ({total_return_pct:+.1f}%) all-time",
                sub_color=GREEN if total_return >= 0 else RED)
with c2:
    metric_card("Cash Available", f"${w['cash']:,.2f}")
with c3:
    metric_card("Invested (open)", f"${invested_total:,.2f}",
                sub=f"{'+' if unrealized_total >= 0 else ''}{unrealized_total:,.2f} unrealized",
                sub_color=GREEN if unrealized_total >= 0 else RED)
with c4:
    metric_card("Win Rate (closed)", f"{win_rate:.0f}%", sub=f"{len(closed_df)} trades closed" if not closed_df.empty else "")

section_header("🟡 Open Positions")
if open_df.empty:
    st.info("No open paper positions yet. They open automatically from strong signals on the Live Scanner page.")
else:
    show_cols = ["symbol", "signal", "entry", "current_price", "invested_usd", "unrealized_usd", "confidence"]
    show_cols = [c for c in show_cols if c in open_df.columns]
    st.dataframe(
        open_df[show_cols].sort_values("unrealized_usd", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol"),
            "signal": st.column_config.TextColumn("Signal"),
            "entry": st.column_config.NumberColumn("Entry Price", format="$%.2f"),
            "current_price": st.column_config.NumberColumn("Current Price", format="$%.2f"),
            "invested_usd": st.column_config.NumberColumn("Invested", format="$%.2f"),
            "unrealized_usd": st.column_config.NumberColumn("Unrealized P/L", format="$%+.2f"),
            "confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=100, format="%.0f%%"),
        },
    )

section_header("✅ Closed Positions")
if closed_df.empty:
    st.info("No closed positions yet.")
else:
    show_cols = ["symbol", "signal", "entry", "exit_price", "invested_usd", "pnl_usd", "pnl_pct", "exit_reason"]
    show_cols = [c for c in show_cols if c in closed_df.columns]
    st.dataframe(
        closed_df[show_cols].sort_values("pnl_usd", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "symbol": st.column_config.TextColumn("Symbol"),
            "signal": st.column_config.TextColumn("Signal"),
            "entry": st.column_config.NumberColumn("Entry", format="$%.2f"),
            "exit_price": st.column_config.NumberColumn("Exit", format="$%.2f"),
            "invested_usd": st.column_config.NumberColumn("Invested", format="$%.2f"),
            "pnl_usd": st.column_config.NumberColumn("P/L ($)", format="$%+.2f"),
            "pnl_pct": st.column_config.NumberColumn("P/L (%)", format="%+.2f%%"),
            "exit_reason": st.column_config.TextColumn("Exit Reason"),
        },
    )

st.markdown(
    '<div class="disclaimer">Paper trading only — this is pretend money. No real orders are ever placed.</div>',
    unsafe_allow_html=True,
)
