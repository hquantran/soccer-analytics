"""Load and aggregate bi_player_seasons for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

from dashboard.metrics_config import (
    ADDITIVE_COLS,
    BI_RATE_KEYS,
    MetricSpec,
    all_metric_specs,
    all_scatter_metric_keys,
    compute_metric,
    compute_xy,
    metrics_for_position,
    scatter_views_for_position,
    trend_metric_for_position,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "warehouse" / "api_sports.duckdb"
PARQUET_PATH = PROJECT_ROOT / "data" / "exports" / "bi_player_seasons.parquet"


def format_season(year: int | float | str) -> str:
    """API season start year → football season label (2022 → 2022/2023)."""
    y = int(year)
    return f"{y}/{y + 1}"


def format_season_range(seasons: list[int] | list[float]) -> str:
    """One or many seasons as display text."""
    if not seasons:
        return "—"
    years = sorted(int(s) for s in seasons)
    if len(years) == 1:
        return format_season(years[0])
    return f"{format_season(years[0])}–{format_season(years[-1])} ({len(years)} seasons)"


def format_age(age) -> str:
    """Safe age display — handles None, NaN, and pandas NA."""
    if age is None:
        return "—"
    try:
        if pd.isna(age):
            return "—"
    except (TypeError, ValueError):
        return "—"
    try:
        return f"{float(age):.0f}"
    except (TypeError, ValueError):
        return "—"


def _connect() -> duckdb.DuckDBPyConnection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"DuckDB not found at {DB_PATH}. Run dbt to build models.")
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data(show_spinner=False)
def load_player_lookup() -> pd.DataFrame:
    """
    Lightweight one-row-per-player index for selectbox search.
    Uses latest season stint for team / position / age / league.
    """
    sql = """
        select
            player_id,
            player_name,
            team_name,
            position,
            age,
            league_name,
            season
        from main.bi_player_seasons
        where position != 'Goalkeeper'
        qualify row_number() over (
            partition by player_id
            order by season desc, minutes desc nulls last
        ) = 1
        order by player_name
    """
    with _connect() as conn:
        return conn.execute(sql).df()


@st.cache_data(show_spinner=False)
def load_filter_dimension_values() -> dict:
    """Distinct filter values from bi_player_seasons (small result)."""
    sql = """
        select
            list(distinct league_name order by league_name) as leagues,
            list(distinct season order by season) as seasons,
            list(distinct position order by position) as positions,
            list(distinct team_name order by team_name) as teams,
            min(age) as age_min,
            max(age) as age_max
        from main.bi_player_seasons
        where position != 'Goalkeeper'
    """
    with _connect() as conn:
        row = conn.execute(sql).fetchone()
    leagues = [x for x in (row[0] or []) if x]
    seasons = [int(x) for x in (row[1] or [])]
    positions = [x for x in (row[2] or []) if x and x != "Goalkeeper"]
    teams = [x for x in (row[3] or []) if x]
    age_min = int(row[4]) if row[4] is not None else 16
    age_max = int(row[5]) if row[5] is not None else 40
    return {
        "leagues": leagues,
        "seasons": seasons,
        "positions": positions,
        "teams": teams,
        "age_min": age_min,
        "age_max": age_max,
    }


@st.cache_data(show_spinner=False)
def load_player_seasons_by_id(
    player_id: int,
    seasons: tuple[int, ...] | None = None,
    leagues: tuple[str, ...] | None = None,
    teams: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Exact player_id lookup into bi_player_seasons (no name ILIKE)."""
    clauses = ["player_id = ?", "position != 'Goalkeeper'"]
    params: list = [int(player_id)]

    if seasons:
        placeholders = ", ".join(["?"] * len(seasons))
        clauses.append(f"season in ({placeholders})")
        params.extend(int(s) for s in seasons)
    if leagues:
        placeholders = ", ".join(["?"] * len(leagues))
        clauses.append(f"league_name in ({placeholders})")
        params.extend(leagues)
    if teams:
        placeholders = ", ".join(["?"] * len(teams))
        clauses.append(f"team_name in ({placeholders})")
        params.extend(teams)

    sql = (
        f"select * from main.bi_player_seasons "
        f"where {' and '.join(clauses)} "
        f"order by season, team_name"
    )
    with _connect() as conn:
        return conn.execute(sql, params).df()


@st.cache_data(show_spinner=False)
def load_peer_season_rows(
    position: str,
    seasons: tuple[int, ...] | None = None,
    leagues: tuple[str, ...] | None = None,
    teams: tuple[str, ...] | None = None,
    age_min: float | None = None,
    age_max: float | None = None,
) -> pd.DataFrame:
    """Peer pool for percentiles / radar / scatter — filtered in DuckDB."""
    clauses = ["position = ?"]
    params: list = [position]

    if seasons:
        placeholders = ", ".join(["?"] * len(seasons))
        clauses.append(f"season in ({placeholders})")
        params.extend(int(s) for s in seasons)
    if leagues:
        placeholders = ", ".join(["?"] * len(leagues))
        clauses.append(f"league_name in ({placeholders})")
        params.extend(leagues)
    if teams:
        placeholders = ", ".join(["?"] * len(teams))
        clauses.append(f"team_name in ({placeholders})")
        params.extend(teams)
    if age_min is not None:
        clauses.append("age >= ?")
        params.append(float(age_min))
    if age_max is not None:
        clauses.append("age <= ?")
        params.append(float(age_max))

    sql = f"select * from main.bi_player_seasons where {' and '.join(clauses)}"
    with _connect() as conn:
        return conn.execute(sql, params).df()


def load_player_seasons() -> pd.DataFrame:
    """Prefer DuckDB table; fall back to parquet export."""
    if DB_PATH.exists():
        with duckdb.connect(str(DB_PATH), read_only=True) as conn:
            try:
                return conn.execute("select * from main.bi_player_seasons").df()
            except duckdb.Error:
                pass
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH)
    raise FileNotFoundError(
        "No bi_player_seasons data found. Run `dbt run` to build main.bi_player_seasons "
        f"or generate {PARQUET_PATH.name}."
    )


def filter_frame(
    df: pd.DataFrame,
    *,
    leagues: list[str] | None = None,
    seasons: list[int] | None = None,
    teams: list[str] | None = None,
    positions: list[str] | None = None,
    player_query: str | None = None,
    age_min: float | None = None,
    age_max: float | None = None,
) -> pd.DataFrame:
    out = df
    if "position" in out.columns:
        out = out[out["position"] != "Goalkeeper"]
    if leagues:
        out = out[out["league_name"].isin(leagues)]
    if seasons:
        out = out[out["season"].isin(seasons)]
    if teams:
        out = out[out["team_name"].isin(teams)]
    if positions:
        out = out[out["position"].isin(positions)]
    if age_min is not None and "age" in out.columns:
        out = out[out["age"].fillna(0) >= age_min]
    if age_max is not None and "age" in out.columns:
        out = out[out["age"].fillna(99) <= age_max]
    if player_query:
        q = player_query.strip().lower()
        if q:
            out = out[out["player_name"].fillna("").str.lower().str.contains(q, regex=False)]
    return out


def top_player_matches(df: pd.DataFrame, query: str, limit: int = 5) -> pd.DataFrame:
    """Return up to `limit` unique players matching the name query (with team for disambiguation)."""
    cols = ["player_id", "player_name"]
    if "team_name" in df.columns:
        cols.append("team_name")
    if not query or not query.strip():
        return pd.DataFrame(columns=cols)
    q = query.strip().lower()
    matched = df[df["player_name"].fillna("").str.lower().str.contains(q, regex=False)]
    if matched.empty:
        return matched[cols].iloc[0:0]
    return (
        matched[cols]
        .drop_duplicates(subset=["player_id"])
        .sort_values("player_name")
        .head(limit)
        .reset_index(drop=True)
    )


def _row_sums(rows: pd.DataFrame) -> dict[str, float]:
    return {col: float(rows[col].fillna(0).sum()) for col in ADDITIVE_COLS if col in rows.columns}


def _metric_from_rows(rows: pd.DataFrame, spec: MetricSpec) -> float | None:
    """
    Single BI row: reuse precomputed season rates when formulas match.
    Multi-row (multi-season or multi-stint): sum additives, then recompute.
    """
    if len(rows) == 1 and spec.key in BI_RATE_KEYS and spec.key in rows.columns:
        raw = rows.iloc[0][spec.key]
        if pd.notna(raw):
            return float(raw)
    return compute_metric(_row_sums(rows), spec)


def resolve_majority_position(rows: pd.DataFrame) -> tuple[str, pd.DataFrame, dict]:
    """
    Pick the position the player spent the most seasons in (within `rows`).

    Tie-break: more minutes, then most recent season. Returns
    (position, rows_filtered_to_that_position, info_dict).
    Single-season / single-position inputs pass through unchanged.
    """
    if rows.empty:
        raise ValueError("No rows to resolve position")

    usable = rows[rows["position"].notna() & (rows["position"] != "Goalkeeper")].copy()
    if usable.empty:
        raise ValueError("No non-GK position rows")

    # Distinct seasons played at each position
    season_counts = usable.groupby("position")["season"].nunique()
    minutes = usable.groupby("position")["minutes"].sum() if "minutes" in usable.columns else season_counts * 0
    latest = usable.groupby("position")["season"].max()

    rank = pd.DataFrame(
        {
            "seasons": season_counts,
            "minutes": minutes,
            "latest": latest,
        }
    ).sort_values(["seasons", "minutes", "latest"], ascending=[False, False, False])

    position = str(rank.index[0])
    filtered = usable[usable["position"] == position].copy()
    info = {
        "position": position,
        "season_counts": {str(k): int(v) for k, v in season_counts.items()},
        "used_majority": int(season_counts.max()) < int(usable["season"].nunique())
        or usable["position"].nunique() > 1,
    }
    return position, filtered, info


def aggregate_player_rows(rows: pd.DataFrame) -> dict:
    """Collapse one or more season rows for a player into identity + metrics.

    Uses majority-position seasons when the player switched positions across
    the selected window; metrics/specs match that position only.
    """
    if rows.empty:
        raise ValueError("No rows to aggregate")

    position, pos_rows, pos_info = resolve_majority_position(rows)
    first = pos_rows.sort_values("season").iloc[-1]
    sums = _row_sums(pos_rows)

    if "rating" in pos_rows.columns and sums.get("minutes", 0) > 0:
        rating = float((pos_rows["rating"].fillna(0) * pos_rows["minutes"].fillna(0)).sum() / sums["minutes"])
    else:
        rating = float(first.get("rating") or 0)

    seasons = sorted(pos_rows["season"].dropna().unique().tolist())
    teams = sorted(pos_rows["team_name"].dropna().unique().tolist())
    leagues = sorted(pos_rows["league_name"].dropna().unique().tolist())

    metric_blocks = metrics_for_position(position)
    computed: dict[str, dict[str, float | None]] = {}
    for block_name, specs in metric_blocks.items():
        computed[block_name] = {spec.key: _metric_from_rows(pos_rows, spec) for spec in specs}

    return {
        "player_id": int(first["player_id"]),
        "player_name": first["player_name"],
        "photo": first.get("photo"),
        "position": position,
        "position_info": pos_info,
        "nationality": first.get("nationality"),
        "age": first.get("age"),
        "rating": rating,
        "seasons": seasons,
        "teams": teams,
        "leagues": leagues,
        "minutes": sums.get("minutes", 0.0),
        "appearances": sums.get("appearances", 0.0),
        "metrics": computed,
        "metric_specs": metric_blocks,
        "sums": sums,
        "used_bi_rates": len(pos_rows) == 1,
        "rows": pos_rows,
    }


def build_peer_table(df: pd.DataFrame, position: str) -> pd.DataFrame:
    """One aggregated row per player with position metrics and all scatter axes.

    Always sum additive columns then recompute rates (correct for 1+ rows and
    matches BI season-grain formulas). Vectorized for dashboard performance.
    """
    peers = df[df["position"] == position]
    if peers.empty:
        return pd.DataFrame()

    additive = [c for c in ADDITIVE_COLS if c in peers.columns]
    grouped = peers.groupby("player_id", sort=False)
    sums = grouped[additive].sum().reset_index()

    # Latest stint for display identity (name / age)
    latest_idx = peers.groupby("player_id", sort=False)["season"].idxmax()
    identity = peers.loc[latest_idx, ["player_id", "player_name", "age"]].reset_index(drop=True)

    teams = (
        grouped["team_name"]
        .agg(lambda s: ", ".join(sorted({str(x) for x in s.dropna()})))
        .rename("teams")
        .reset_index()
    )
    leagues = (
        grouped["league_name"]
        .agg(lambda s: ", ".join(sorted({str(x) for x in s.dropna()})))
        .rename("leagues")
        .reset_index()
    )

    out = identity.merge(sums, on="player_id").merge(teams, on="player_id").merge(leagues, on="player_id")
    out["position"] = position

    if "rating" in peers.columns and "minutes" in peers.columns:
        weighted = peers.assign(
            _rw=peers["rating"].fillna(0) * peers["minutes"].fillna(0),
            _mins=peers["minutes"].fillna(0),
        )
        rating = weighted.groupby("player_id", sort=False).agg(_rw=("_rw", "sum"), _mins=("_mins", "sum"))
        rating["rating"] = rating["_rw"] / rating["_mins"].replace(0, pd.NA)
        out = out.merge(rating[["rating"]].reset_index(), on="player_id", how="left")
    else:
        out["rating"] = None

    specs = all_metric_specs(position)
    scatter_specs: list[MetricSpec] = []
    seen_keys = {s.key for s in specs}
    for view in scatter_views_for_position(position):
        for key, label, num, den, scale in (
            (view.axes.x_key, view.axes.x_label, view.axes.x_numerator, view.axes.x_denominator, view.axes.x_scale),
            (view.axes.y_key, view.axes.y_label, view.axes.y_numerator, view.axes.y_denominator, view.axes.y_scale),
        ):
            if key not in seen_keys:
                scatter_specs.append(MetricSpec(key, label, num, den, scale))
                seen_keys.add(key)

    for spec in list(specs) + scatter_specs:
        out[spec.key] = _metric_series_from_sums(out, spec)

    for key in all_scatter_metric_keys(position):
        if key not in out.columns:
            out[key] = None

    return out.reset_index(drop=True)


def _metric_series_from_sums(sums_df: pd.DataFrame, spec: MetricSpec) -> pd.Series:
    """Vectorized MetricSpec over a frame of summed additive columns."""
    if spec.key == "goal_involvements_per90":
        goals = pd.to_numeric(sums_df.get("goals"), errors="coerce").fillna(0)
        assists = pd.to_numeric(sums_df.get("assists"), errors="coerce").fillna(0)
        minutes = pd.to_numeric(sums_df.get("minutes"), errors="coerce")
        return ((goals + assists) * 90.0 / minutes.where(minutes != 0)).astype("float64")

    if spec.numerator not in sums_df.columns:
        return pd.Series(float("nan"), index=sums_df.index, dtype="float64")
    num = pd.to_numeric(sums_df[spec.numerator], errors="coerce")
    if spec.denominator is None:
        return num.astype("float64")
    if spec.denominator not in sums_df.columns:
        return pd.Series(float("nan"), index=sums_df.index, dtype="float64")
    den = pd.to_numeric(sums_df[spec.denominator], errors="coerce")
    result = num * float(spec.scale) / den.where(den != 0)
    return result.astype("float64")


@st.cache_data(show_spinner=False)
def cached_peer_table(
    position: str,
    seasons: tuple[int, ...] | None,
    leagues: tuple[str, ...] | None,
    age_min: float | None,
    age_max: float | None,
    min_minutes: float = 0.0,
    teams: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Cached peer aggregation for dashboard pages."""
    peer_source = load_peer_season_rows(
        position,
        seasons=seasons,
        leagues=leagues,
        teams=teams,
        age_min=age_min,
        age_max=age_max,
    )
    peers = build_peer_table(peer_source, position)
    if peers.empty:
        return peers
    if min_minutes and "minutes" in peers.columns:
        peers = peers[peers["minutes"] >= float(min_minutes)].reset_index(drop=True)
    return peers


def ensure_players_in_peer_table(
    peer_table: pd.DataFrame,
    player_frames: list[pd.DataFrame],
    position: str,
) -> pd.DataFrame:
    """
    Guarantee selected players appear in the peer pool (needed for radar/scatter
    highlights when age/league filters exclude their lookup stint).
    """
    if not player_frames:
        return peer_table

    extra = pd.concat([f for f in player_frames if f is not None and not f.empty], ignore_index=True)
    if extra.empty:
        return peer_table

    extra = extra[extra["position"] == position]
    if extra.empty:
        return peer_table

    extra_peers = build_peer_table(extra, position)
    if extra_peers.empty:
        return peer_table
    if peer_table.empty:
        return extra_peers.reset_index(drop=True)

    missing = ~extra_peers["player_id"].isin(peer_table["player_id"])
    if not missing.any():
        return peer_table
    return pd.concat([peer_table, extra_peers.loc[missing]], ignore_index=True)


def top_players_table(
    df: pd.DataFrame,
    position: str,
    limit: int = 5,
    *,
    sort_key: str = "goals_per90",
    min_minutes: float = 0.0,
    defender_profile: str | None = None,
) -> pd.DataFrame:
    """Top N players ranked by a tactical metric (DESC), with optional min minutes."""
    # Accept either raw season rows or an already-aggregated peer table.
    if "player_id" in df.columns and sort_key in df.columns and "minutes" in df.columns and df["player_id"].is_unique:
        peers = df.copy()
    else:
        peers = build_peer_table(df, position)
    if peers.empty:
        return peers
    if min_minutes and "minutes" in peers.columns:
        peers = peers[peers["minutes"] >= float(min_minutes)]
    if peers.empty:
        return peers

    # Defender sub-position proxy (API has no CB/FB): full-backs lean creative on the ball.
    if position == "Defender" and defender_profile and defender_profile != "All Defenders":
        if "key_passes_per90" in peers.columns and peers["key_passes_per90"].notna().any():
            median_kp = float(peers["key_passes_per90"].median())
            if defender_profile == "Full-Back profile":
                peers = peers[peers["key_passes_per90"].fillna(0) >= median_kp]
            elif defender_profile == "Center-Back profile":
                peers = peers[peers["key_passes_per90"].fillna(0) < median_kp]

    if sort_key not in peers.columns:
        sort_key = next((c for c in peers.columns if c.endswith("_per90") or c.endswith("_pct")), "minutes")
    peers = peers.dropna(subset=[sort_key])
    if peers.empty:
        return peers
    return peers.sort_values(sort_key, ascending=False).head(limit).reset_index(drop=True)


def position_averages(peer_table: pd.DataFrame, specs: list[MetricSpec]) -> dict[str, float | None]:
    """Mean of selected metrics across the peer table (league/position scope)."""
    out: dict[str, float | None] = {}
    if peer_table.empty:
        return out
    for spec in specs:
        if spec.key not in peer_table.columns:
            out[spec.key] = None
            continue
        series = peer_table[spec.key].dropna()
        out[spec.key] = float(series.mean()) if not series.empty else None
    if "minutes" in peer_table.columns:
        out["minutes"] = float(peer_table["minutes"].mean())
    return out


def percentile_scores(
    peer_table: pd.DataFrame,
    player_id: int,
    specs: list[MetricSpec],
) -> tuple[list[str], list[float]]:
    """Return radar labels and 0–100 percentile scores for the selected player."""
    labels: list[str] = []
    values: list[float] = []
    if peer_table.empty:
        return labels, values

    player_mask = peer_table["player_id"] == player_id
    if not player_mask.any():
        return labels, values

    for spec in specs:
        if spec.key not in peer_table.columns:
            continue
        series = peer_table[spec.key]
        if series.dropna().empty:
            continue
        ranks = series.rank(pct=True, ascending=spec.higher_is_better, method="average") * 100
        player_pct = ranks.loc[player_mask]
        if player_pct.empty or pd.isna(player_pct.iloc[0]):
            continue
        labels.append(spec.label)
        values.append(round(float(player_pct.iloc[0]), 1))

    return labels, values


def metric_percentile_map(
    peer_table: pd.DataFrame,
    player_id: int,
    specs: list[MetricSpec],
) -> dict[str, float]:
    """Map metric key → 0–100 peer percentile for badge display."""
    out: dict[str, float] = {}
    if peer_table.empty:
        return out
    player_mask = peer_table["player_id"] == player_id
    if not player_mask.any():
        return out
    for spec in specs:
        if spec.key not in peer_table.columns:
            continue
        series = peer_table[spec.key]
        if series.dropna().empty:
            continue
        ranks = series.rank(pct=True, ascending=spec.higher_is_better, method="average") * 100
        player_pct = ranks.loc[player_mask]
        if player_pct.empty or pd.isna(player_pct.iloc[0]):
            continue
        out[spec.key] = round(float(player_pct.iloc[0]), 0)
    return out


def build_season_trend_frame(player_rows: pd.DataFrame, position: str) -> pd.DataFrame:
    """One row per season for dual-axis trend chart."""
    if player_rows.empty:
        return pd.DataFrame(columns=["season", "season_label", "minutes", "primary_value", "primary_label"])

    primary = trend_metric_for_position(position)
    records: list[dict] = []
    for season, rows in player_rows.groupby("season"):
        sums = _row_sums(rows)
        records.append(
            {
                "season": int(season),
                "season_label": format_season(season),
                "minutes": sums.get("minutes", 0.0),
                "primary_value": _metric_from_rows(rows, primary),
                "primary_label": primary.label,
                "primary_key": primary.key,
            }
        )
    return pd.DataFrame.from_records(records).sort_values("season").reset_index(drop=True)


def format_metric_value(value: float | None, spec: MetricSpec) -> str:
    if value is None:
        return "—"
    try:
        return spec.format.format(value)
    except (ValueError, TypeError):
        return str(value)
