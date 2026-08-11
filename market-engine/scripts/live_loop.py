import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import time
import logging
from scanner import run_scan
from longterm import run_longterm_scan

logging.basicConfig(level=logging.INFO, format="%(asctime)s [live-loop] %(message)s")
log = logging.getLogger("live_loop")

SHORT_TERM_INTERVAL_SEC = 15 * 60      # short-term scan cadence
LONG_TERM_INTERVAL_SEC = 24 * 60 * 60  # long-term scan cadence


def safe_run(fn, name):
    try:
        log.info(f"running {name}...")
        fn()
        log.info(f"{name} complete")
    except Exception as e:
        log.error(f"{name} failed: {e}")


def main():
    log.info("live loop starting")
    last_long_term = 0.0

    while True:
        cycle_start = time.time()

        safe_run(run_scan, "short-term scan")

        if cycle_start - last_long_term >= LONG_TERM_INTERVAL_SEC:
            safe_run(run_longterm_scan, "long-term scan")
            last_long_term = cycle_start

        elapsed = time.time() - cycle_start
        sleep_for = max(0.0, SHORT_TERM_INTERVAL_SEC - elapsed)
        log.info(f"sleeping {sleep_for:.0f}s until next short-term scan")
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
