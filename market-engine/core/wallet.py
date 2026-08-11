import json
from core.paths import OUTPUT_DIR

WALLET_FILE = OUTPUT_DIR / "wallet.json"
DEFAULT_STARTING_BALANCE = 10000.0
DEFAULT_PER_TRADE = 500.0


def load_wallet() -> dict:
    if not WALLET_FILE.exists():
        wallet = {
            "starting_balance": DEFAULT_STARTING_BALANCE,
            "cash": DEFAULT_STARTING_BALANCE,
            "per_trade": DEFAULT_PER_TRADE,
        }
        save_wallet(wallet)
        return wallet
    try:
        return json.loads(WALLET_FILE.read_text())
    except Exception:
        wallet = {
            "starting_balance": DEFAULT_STARTING_BALANCE,
            "cash": DEFAULT_STARTING_BALANCE,
            "per_trade": DEFAULT_PER_TRADE,
        }
        save_wallet(wallet)
        return wallet


def save_wallet(wallet: dict):
    WALLET_FILE.parent.mkdir(parents=True, exist_ok=True)
    WALLET_FILE.write_text(json.dumps(wallet))


def deduct_cash(amount: float) -> dict:
    wallet = load_wallet()
    wallet["cash"] = max(0.0, wallet["cash"] - amount)
    save_wallet(wallet)
    return wallet


def add_cash(amount: float) -> dict:
    wallet = load_wallet()
    wallet["cash"] = wallet["cash"] + amount
    save_wallet(wallet)
    return wallet


def configure_wallet(starting_balance: float, per_trade: float) -> dict:
    """Updates settings only — does not touch existing positions or reset cash.
    Use reset_wallet() for a full restart."""
    wallet = load_wallet()
    wallet["starting_balance"] = starting_balance
    wallet["per_trade"] = per_trade
    save_wallet(wallet)
    return wallet


def reset_wallet(starting_balance: float = None, per_trade: float = None) -> dict:
    """Full restart: cash goes back to starting_balance. Callers should also
    clear open/closed positions to avoid an inconsistent ledger — see
    core.positions.reset_all()."""
    wallet = load_wallet()
    if starting_balance is not None:
        wallet["starting_balance"] = starting_balance
    if per_trade is not None:
        wallet["per_trade"] = per_trade
    wallet["cash"] = wallet["starting_balance"]
    save_wallet(wallet)
    return wallet
