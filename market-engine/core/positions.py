from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
from core.paths import OUTPUT_DIR

OPEN_FILE = OUTPUT_DIR / "open_positions.csv"
CLOSED_FILE = OUTPUT_DIR / "closed_positions.csv"

OPEN_COLUMNS = [
    "id", "symbol", "signal", "entry", "target1", "target2", "stop_loss",
    "confidence", "timeframe", "opened_at",
]
CLOSED_COLUMNS = OPEN_COLUMNS + ["closed_at", "exit_price", "exit_reason", "pnl_pct"]


def _load(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    try:
        df = pd.read_csv(path)
        if df.empty:
            return pd.DataFrame(columns=columns)
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=columns)


def _save(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def load_open_positions() -> pd.DataFrame:
    return _load(OPEN_FILE, OPEN_COLUMNS)


def load_closed_positions() -> pd.DataFrame:
    return _load(CLOSED_FILE, CLOSED_COLUMNS)


def open_new_positions(signals_df: pd.DataFrame) -> int:
    """Open a paper position for each actionable signal whose symbol doesn't
    already have an open position. Returns the number of positions opened."""
    if signals_df is None or signals_df.empty:
        return 0

    open_df = load_open_positions()
    already_open = set(open_df["symbol"]) if not open_df.empty else set()

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new_rows = []
    next_id = (int(open_df["id"].max()) + 1) if not open_df.empty else 1

    for _, row in signals_df.iterrows():
        if row["symbol"] in already_open:
            continue
        new_rows.append({
            "id": next_id,
            "symbol": row["symbol"],
            "signal": row["signal"],
            "entry": row["entry"],
            "target1": row["target1"],
            "target2": row["target2"],
            "stop_loss": row["stop_loss"],
            "confidence": row["confidence"],
            "timeframe": row["timeframe"],
            "opened_at": now,
        })
        next_id += 1
        already_open.add(row["symbol"])

    if not new_rows:
        return 0

    combined = pd.concat([open_df, pd.DataFrame(new_rows)], ignore_index=True)
    _save(combined, OPEN_FILE)
    return len(new_rows)


def _hit_check(pos, price):
    """Returns (exit_price, exit_reason) if the position's target or stop
    was hit at the given price, else (None, None)."""
    if pos["signal"] == "BUY":
        if price >= pos["target2"]:
            return pos["target2"], "target2_hit"
        if price <= pos["stop_loss"]:
            return pos["stop_loss"], "stop_hit"
    else:  # SELL
        if price <= pos["target2"]:
            return pos["target2"], "target2_hit"
        if price >= pos["stop_loss"]:
            return pos["stop_loss"], "stop_hit"
    return None, None


def update_open_positions(latest_prices: dict) -> int:
    """Check open positions against latest known prices. Close any that hit
    target2 or stop_loss, logging them to closed_positions.csv. Returns the
    number of positions closed."""
    open_df = load_open_positions()
    if open_df.empty:
        return 0

    closed_df = load_closed_positions()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    still_open_rows = []
    newly_closed_rows = []

    for _, pos in open_df.iterrows():
        price = latest_prices.get(pos["symbol"])
        if price is None:
            still_open_rows.append(pos)
            continue

        exit_price, exit_reason = _hit_check(pos, price)
        if exit_price is None:
            still_open_rows.append(pos)
            continue

        if pos["signal"] == "BUY":
            pnl_pct = (exit_price - pos["entry"]) / pos["entry"] * 100
        else:
            pnl_pct = (pos["entry"] - exit_price) / pos["entry"] * 100

        closed = pos.to_dict()
        closed.update({
            "closed_at": now,
            "exit_price": round(float(exit_price), 2),
            "exit_reason": exit_reason,
            "pnl_pct": round(float(pnl_pct), 2),
        })
        newly_closed_rows.append(closed)

    if not newly_closed_rows:
        return 0

    _save(pd.DataFrame(still_open_rows, columns=OPEN_COLUMNS), OPEN_FILE)
    combined_closed = pd.concat([closed_df, pd.DataFrame(newly_closed_rows)], ignore_index=True)
    _save(combined_closed, CLOSED_FILE)
    return len(newly_closed_rows)
