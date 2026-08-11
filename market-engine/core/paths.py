import os
from pathlib import Path

# Where generated outputs (signals, open/closed positions, long-term signals,
# portfolio allocation) get written. Locally this defaults to ./data so
# everything just works out of the box. On Railway (or any host where you
# want results to survive a redeploy), set the OUTPUT_DIR env var to a
# mounted Volume path, e.g. /app/state, and mount a Volume there.
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "data"))

# Where the trained ML model is saved/loaded from. Same idea — point this
# at the persistent volume in production so a redeploy doesn't wipe out
# a model you spent time training.
MODELS_DIR = Path(os.environ.get("MODELS_DIR", "models"))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Watchlists are git-tracked inputs, not generated outputs — always read
# from the repo's data/ folder regardless of OUTPUT_DIR, so editing them
# in git and pushing always takes effect.
WATCHLIST_SHORT = Path("data/watchlist.json")
WATCHLIST_LONG = Path("data/watchlist_longterm.json")
