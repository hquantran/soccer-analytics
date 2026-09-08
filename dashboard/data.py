"""Load and aggregate bi_player_seasons for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

from dashboard.metrics_config import (
    ADDITIVE_COLS,
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

# Keep the dashboard payload narrow. Rates are recomputed for multi-season
# views, while the stored rates provide the single-row fast path.
DASHBOARD_COLUMNS = [
    "player_season_id",
    "player_id",
    "player_name",
    "nationality",
    "photo",
    "age",
    "team_id",
    "team_name",
    "league_id",
    "league_name",
    "season",
    "position",
    "injured",
    "rating",
    *ADDITIVE_COLS,
    "goals_per90",
    "assists_per90",
    "goal_involvements_per90",
    "key_passes_per90",
    "tackles_per90",
    "dribbles_per90",
    "shot_accuracy_pct",
    "goal_conversion_pct",
    "pass_accuracy_pct",
    "dribble_success_pct",
    "duel_success_pct",
    "fouls_per_tackle",
]


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
    if age_min is not None:
        clauses.append("age >= ?")
        params.append(float(age_min))
    if age_max is not None:
        clauses.append("age <= ?")
        params.append(float(age_max))

    sql = f"select * from main.bi_player_seasons where {' and '.join(clauses)}"
    with _connect() as conn:
        return conn.execute(sql, params).df()


@st.cache_data(show_spinner=False)
def load_player_seasons() -> pd.DataFrame:
    """Load the dashboard payload from the columnar export."""
    if PARQUET_PATH.exists():
        return pd.read_parquet(PARQUET_PATH, columns=DASHBOARD_COLUMNS)
    if DB_PATH.exists():
        with duckdb.connect(str(DB_PATH), read_only=True) as conn:
            try:
                columns = ", ".join(f'"{column}"' for column in DASHBOARD_COLUMNS)
                return conn.execute(f"select {columns} from main.bi_player_seasons").df()
            except duckdb.Error:
                pass
    raise FileNotFoundError(
        "No bi_player_seasons data found. Run `dbt run` to build main.bi_player_seasons "
        f"or generate {PARQUET_PATH.name}."
    )


@st.cache_data(show_spinner=False)
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


@st.cache_data(show_spinner=False)
def aggregate_player_rows(rows: pd.DataFrame) -> dict:
    """Collapse one or more season rows for a player into identity + recomputed metrics."""
    if rows.empty:
        raise ValueError("No rows to aggregate")

    first = rows.iloc[0]
    position = first["position"]
    sums = _row_sums(rows)

    if "rating" in rows.columns and sums.get("minutes", 0) > 0:
        rating = float((rows["rating"].fillna(0) * rows["minutes"].fillna(0)).sum() / sums["minutes"])
    else:
        rating = float(first.get("rating") or 0)

    seasons = sorted(rows["season"].dropna().unique().tolist())
    teams = sorted(rows["team_name"].dropna().unique().tolist())
    leagues = sorted(rows["league_name"].dropna().unique().tolist())

    metric_blocks = metrics_for_position(position)
    computed: dict[str, dict[str, float | None]] = {}
    for block_name, specs in metric_blocks.items():
        computed[block_name] = {
            spec.key: (
                float(first[spec.key])
                if len(rows) == 1 and spec.key in rows.columns and pd.notna(first[spec.key])
                else compute_metric(sums, spec)
            )
            for spec in specs
        }

    return {
        "player_id": int(first["player_id"]),
        "player_name": first["player_name"],
        "photo": first.get("photo"),
        "position": position,
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
    }


@st.cache_data(show_spinner=False)
def build_peer_table(df: pd.DataFrame, position: str) -> pd.DataFrame:
    """One aggregated row per player with position metrics and all scatter axes."""
    peers = df[df["position"] == position]
    if peers.empty:
        return pd.DataFrame()

    specs = all_metric_specs(position)
    scatter_keys = all_scatter_metric_keys(position)
    records: list[dict] = []

    for player_id, rows in peers.groupby("player_id", sort=False):
        first = rows.iloc[0]
        sums = _row_sums(rows)
        record: dict = {
            "player_id": int(player_id),
            "player_name": first["player_name"],
            "position": position,
            "rating": float(
                (rows["rating"].fillna(0) * rows["minutes"].fillna(0)).sum() / sums["minutes"]
            )
            if sums.get("minutes", 0) > 0
            else float(first.get("rating") or 0),
            "age": float(rows["age"].dropna().iloc[-1]) if rows["age"].notna().any() else None,
            "minutes": sums.get("minutes", 0.0),
            "appearances": sums.get("appearances", 0.0),
            "teams": ", ".join(sorted(rows["team_name"].dropna().unique().tolist())),
            "leagues": ", ".join(sorted(rows["league_name"].dropna().unique().tolist())),
        }
        for spec in specs:
            if len(rows) == 1 and spec.key in rows.columns and pd.notna(first[spec.key]):
                record[spec.key] = float(first[spec.key])
            else:
                record[spec.key] = compute_metric(sums, spec)
        for view in scatter_views_for_position(position):
            x_val, y_val = compute_xy(sums, view.axes)
            record[view.axes.x_key] = x_val
            record[view.axes.y_key] = y_val
        for key in scatter_keys:
            record.setdefault(key, None)
        records.append(record)

    return pd.DataFrame.from_records(records)


@st.cache_data(show_spinner=False)
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


@st.cache_data(show_spinner=False)
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


@st.cache_data(show_spinner=False)
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


@st.cache_data(show_spinner=False)
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


@st.cache_data(show_spinner=False)
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
                "primary_value": compute_metric(sums, primary),
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
