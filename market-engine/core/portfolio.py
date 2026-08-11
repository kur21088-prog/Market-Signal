import pandas as pd

MAX_WEIGHT_PCT = 25.0   # cap any single holding for diversification
MIN_SCORE_TO_INCLUDE = 45.0  # HOLD or better only; AVOID names are excluded


def build_allocation(signals_df: pd.DataFrame) -> pd.DataFrame:
    """Turn long-term signals into a suggested target allocation.
    Favors higher trend_score and lower volatility ('steady growth' tilt),
    excludes AVOID-rated names, and caps any single position at MAX_WEIGHT_PCT."""
    cols = ["symbol", "weight_pct", "trend_score", "volatility", "rating"]
    if signals_df is None or signals_df.empty:
        return pd.DataFrame(columns=cols)

    eligible = signals_df[signals_df["trend_score"] >= MIN_SCORE_TO_INCLUDE].copy()
    if eligible.empty:
        return pd.DataFrame(columns=cols)

    # Steady-growth score: reward trend strength, penalize volatility.
    eligible["vol_safe"] = eligible["volatility"].clip(lower=1.0)
    eligible["raw_score"] = eligible["trend_score"] / eligible["vol_safe"]

    total = eligible["raw_score"].sum()
    eligible["weight_pct"] = eligible["raw_score"] / total * 100

    # A fixed 25% cap is mathematically infeasible with very few eligible
    # names (e.g. 3 names can't all stay under 25% and still sum to 100%).
    # Forcing it in that case dumps all the excess onto whichever name is
    # left uncapped, even if it's the weakest one. Instead, relax the cap
    # only as much as needed so it stays achievable for this many names.
    n = len(eligible)
    effective_cap = max(MAX_WEIGHT_PCT, 100.0 / n)

    # Cap and redistribute excess weight proportionally to uncapped names,
    # by their underlying raw_score share (not their evolving weight_pct),
    # so redistribution still favors stronger/lower-volatility names.
    for _ in range(10):
        over = eligible["weight_pct"] > effective_cap + 1e-9
        if not over.any():
            break
        excess = (eligible.loc[over, "weight_pct"] - effective_cap).sum()
        eligible.loc[over, "weight_pct"] = effective_cap
        under = ~over
        under_raw_total = eligible.loc[under, "raw_score"].sum()
        if under_raw_total > 0:
            eligible.loc[under, "weight_pct"] += (
                eligible.loc[under, "raw_score"] / under_raw_total * excess
            )

    eligible["weight_pct"] = eligible["weight_pct"].round(1)
    out = eligible.sort_values("weight_pct", ascending=False)
    return out[cols].reset_index(drop=True)
