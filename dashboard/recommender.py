"""Cosine-similarity player recommender for the Streamlit dashboard.

Works for both single-season and multi-season Profile filters because it
consumes `peer_table`: one aggregated row per `player_id` over the same
season/league/age window (rates recomputed from summed volume).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from dashboard.metrics_config import MetricSpec

# Explicit canonical attempts and success metrics; similarity rankings may change.
RECOMMENDER_SPECS: list[MetricSpec] = [
    MetricSpec("goals_per90", "Goals / 90", "goals", "minutes", 90.0),
    MetricSpec("assists_per90", "Assists / 90", "assists", "minutes", 90.0),
    MetricSpec("key_passes_per90", "Key passes / 90", "passes_key", "minutes", 90.0),
    MetricSpec("tackles_per90", "Tackles / 90", "tackles_total", "minutes", 90.0),
    MetricSpec("dribble_attempts_per90", "Dribble attempts / 90", "dribbles_attempts", "minutes", 90.0),
    MetricSpec("shot_accuracy_pct", "Shot accuracy %", "shots_on_target", "shots_total", 100.0),
    MetricSpec("goal_conversion_pct", "Conversion %", "goals", "shots_total", 100.0),
    MetricSpec("dribble_success_pct", "Dribble success %", "dribbles_success", "dribbles_attempts", 100.0),
    MetricSpec("duel_success_pct", "Duel win %", "duels_won", "duels_total", 100.0),
    MetricSpec("fouls_per_tackle", "Fouls / tackle", "fouls_committed", "tackles_total", 1.0, higher_is_better=False),
]

FEATURE_COLS = [spec.key for spec in RECOMMENDER_SPECS]
DEFAULT_MIN_MINUTES = 500.0


def _metric_series_from_sums(sums_df: pd.DataFrame, spec: MetricSpec) -> pd.Series:
    if spec.numerator not in sums_df.columns:
        return pd.Series(np.nan, index=sums_df.index, dtype="float64")
    num = pd.to_numeric(sums_df[spec.numerator], errors="coerce")
    if spec.denominator is None:
        return num.astype("float64")
    if spec.denominator not in sums_df.columns:
        return pd.Series(np.nan, index=sums_df.index, dtype="float64")
    den = pd.to_numeric(sums_df[spec.denominator], errors="coerce")
    return (num * float(spec.scale) / den.where(den != 0)).astype("float64")


def ensure_recommender_features(peer_table: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with all recommender rate columns computed from additive sums."""
    if peer_table.empty:
        return peer_table.copy()

    out = peer_table.copy()
    for spec in RECOMMENDER_SPECS:
        # Always recompute from summed volume so single- and multi-season match
        out[spec.key] = _metric_series_from_sums(out, spec)
    return out


def recommend_similar_players(
    peer_table: pd.DataFrame,
    player_id: int,
    *,
    top_n: int = 8,
    min_minutes: float = DEFAULT_MIN_MINUTES,
) -> pd.DataFrame:
    """
    Rank same-position peers by cosine similarity on standardized rate features.

    `peer_table` must already be one row per player_id (as from `build_peer_table`).
    The query `player_id` is always excluded — so the same attacker never appears
    again via a different season (multi-season aggregation already collapses seasons;
    single-season still drops other rows for that id).
    """
    if peer_table.empty:
        return pd.DataFrame()

    enriched = ensure_recommender_features(peer_table)
    if "minutes" not in enriched.columns:
        return pd.DataFrame()

    pool = enriched.loc[enriched["minutes"] >= float(min_minutes)].copy()
    if pool.empty or int(player_id) not in set(pool["player_id"].astype(int)):
        # Query player may be under the minutes floor — still allow them as query
        query_rows = enriched.loc[enriched["player_id"].astype(int) == int(player_id)]
        if query_rows.empty:
            return pd.DataFrame()
        pool = pd.concat([pool, query_rows], ignore_index=True).drop_duplicates(
            subset=["player_id"], keep="first"
        )

    # One row per player (safety); exclude the query player from candidates
    pool = pool.drop_duplicates(subset=["player_id"], keep="first")
    query = pool.loc[pool["player_id"].astype(int) == int(player_id)]
    if query.empty:
        return pd.DataFrame()

    candidates = pool.loc[pool["player_id"].astype(int) != int(player_id)].copy()
    if candidates.empty:
        return pd.DataFrame()

    X_all = pool[FEATURE_COLS].astype("float64")
    X_all = X_all.fillna(X_all.median(numeric_only=True)).fillna(0.0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_all)
    scaled = pd.DataFrame(X_scaled, index=pool.index, columns=FEATURE_COLS)

    q_vec = scaled.loc[query.index]
    c_mat = scaled.loc[candidates.index]
    sims = cosine_similarity(q_vec, c_mat)[0]

    out = candidates.copy()
    out["similarity"] = sims
    out = out.sort_values("similarity", ascending=False).head(int(top_n)).reset_index(drop=True)

    display_cols = [
        c
        for c in [
            "player_id",
            "player_name",
            "position",
            "teams",
            "leagues",
            "minutes",
            "age",
            "similarity",
            *FEATURE_COLS,
        ]
        if c in out.columns
    ]
    return out[display_cols]
