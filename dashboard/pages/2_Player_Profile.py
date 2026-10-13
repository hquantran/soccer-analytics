"""Single-player profile with position metrics, radar, trend, and scatter."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.charts import ACCENT_A, build_radar_chart, build_scatter_from_view, build_season_trend_chart
from dashboard.data import (
    aggregate_player_rows,
    build_season_trend_frame,
    cached_peer_table,
    ensure_players_in_peer_table,
    format_age,
    format_season,
    format_season_range,
    load_filter_dimension_values,
    load_player_lookup,
    load_player_seasons_by_id,
    metric_percentile_map,
    percentile_scores,
)
from dashboard.metrics_config import radar_metric_specs, scatter_view_by_id, scatter_views_for_position
from dashboard.recommender import DEFAULT_MIN_MINUTES, recommend_similar_players
from dashboard.scout_ui import build_scatter_chart_context, render_scout_analysis
from dashboard.ui import inject_theme_css, render_metric_grid, render_profile_sidebar

inject_theme_css()


@st.fragment
def render_profile_scatter(peer_table, position: str, player_id: int, player_name: str, applied: dict) -> None:
    views = scatter_views_for_position(position)
    view_labels = {view.id: view.title for view in views}
    default_view = applied.get("scatter_view_id") if applied.get("scatter_view_id") in view_labels else views[0].id
    view_id = st.selectbox(
        "Scatter view",
        options=list(view_labels.keys()),
        format_func=lambda value: view_labels[value],
        index=list(view_labels.keys()).index(default_view),
        key="profile_scatter_view",
    )
    view = scatter_view_by_id(position, view_id)
    st.session_state.setdefault("filters_profile", {})
    st.session_state["filters_profile"]["scatter_view_id"] = view_id

    st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
    st.plotly_chart(
        build_scatter_from_view(
            peer_table,
            view,
            position,
            highlights=[(player_id, player_name, ACCENT_A)],
        ),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(f'<p class="insight">{view.insight}</p>', unsafe_allow_html=True)

st.title("Player profile")
st.caption("Position-aware scouting metrics, season trends, peer percentiles, and tactical scatters.")

try:
    lookup = load_player_lookup()
    dims = load_filter_dimension_values()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

link = st.session_state.pop("profile_link_pending", None)
if link is not None:
    try:
        linked_player = int(link[0])
        linked_season = int(link[1]) if link[1] is not None else None
        linked_leagues = link[2] if len(link) > 2 else ()
        if isinstance(linked_leagues, str):
            linked_leagues = (linked_leagues,)
        if any(league not in dims["leagues"] for league in linked_leagues):
            raise ValueError("League not found in the scouting data.")
        if linked_player not in set(lookup["player_id"].astype(int)):
            raise ValueError("Player not found in the scouting data.")
        if linked_season is not None and linked_season not in dims["seasons"]:
            raise ValueError("Season not found in the scouting data.")
    except (TypeError, ValueError):
        st.error("This profile link has an invalid or unavailable player, season, or league.")
        st.stop()
    st.session_state.update({
        "profile_sb_player_id": linked_player,
        "profile_sb_name_q": "",
        "profile_sb_leagues": list(dict.fromkeys(linked_leagues)) if linked_leagues else dims["leagues"],
        "profile_sb_teams": [],
        "profile_sb_age": (dims["age_min"], dims["age_max"]),
    })
    if linked_season is not None:
        st.session_state["profile_sb_season_mode_v2"] = "Single season"
        st.session_state["profile_sb_season_single"] = format_season(linked_season)
    else:
        st.session_state["profile_sb_season_mode_v2"] = "Multi season"
        st.session_state["profile_sb_seasons_multi"] = [format_season(s) for s in dims["seasons"]]

applied = render_profile_sidebar(lookup, dims)
if not applied or not applied.get("player_id"):
    st.info("Choose filters and a player in the sidebar to open a profile.")
    st.stop()

player_id = int(applied["player_id"])
seasons_t = tuple(applied["seasons"]) if applied["seasons"] else None
leagues_t = tuple(applied["leagues"]) if applied["leagues"] else None
teams_t = tuple(applied["teams"]) if applied["teams"] else None
age_min, age_max = applied["age_range"]

# Exact player_id extraction — no name ILIKE / full-table scan in Python
player_rows = load_player_seasons_by_id(
    player_id,
    seasons=seasons_t,
    leagues=leagues_t,
    teams=teams_t,
)
if player_rows.empty:
    st.warning("Selected player has no rows for the applied season, league, and team filters.")
    st.stop()

profile = aggregate_player_rows(player_rows)
position = profile["position"]
pos_rows = profile["rows"]
season_label = format_season_range(profile["seasons"])

peer_table = cached_peer_table(
    position,
    seasons_t,
    leagues_t,
    float(age_min),
    float(age_max),
)
peer_table = ensure_players_in_peer_table(peer_table, [pos_rows], position)
primary_pct = metric_percentile_map(peer_table, player_id, profile["metric_specs"]["primary"])

left, right = st.columns([1, 4], gap="large")
with left:
    if profile.get("photo"):
        st.image(profile["photo"], width="stretch")
    else:
        st.info("No photo")
with right:
    st.markdown(
        f"""
        <div class="hero">
          <p class="player-name" style="font-size:2.75rem !important;font-weight:700 !important;font-family:'Space Grotesk',sans-serif !important;margin:0 !important;line-height:1.15 !important;color:#E7D8C6 !important;">
            {profile['player_name']}
          </p>
          <div class="meta">
            <strong>{profile['position']}</strong>
            · {", ".join(profile["leagues"])}
            · {", ".join(profile["teams"])}
            · {season_label}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div style="height:0.55rem;"></div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3, gap="medium")
    m1.metric("Minutes", f"{profile['minutes']:.0f}")
    m2.metric("Appearances", f"{profile['appearances']:.0f}")
    m3.metric("Age", format_age(profile.get("age")))
    if profile.get("position_info", {}).get("used_majority"):
        counts = profile["position_info"].get("season_counts", {})
        breakdown = ", ".join(f"{pos}: {n} season{'s' if n != 1 else ''}" for pos, n in counts.items())
        st.caption(
            f"Position resolved by majority seasons played → **{position}** ({breakdown}). "
            "Metrics use only rows at that position."
        )
    if profile.get("metric_source") == "scouting_mart":
        st.caption("Metrics use scouting-mart values for one stint and weighted totals for multiple stints.")
    else:
        st.caption("Metrics use scouting-mart values for one stint and weighted totals for multiple stints.")

st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
specs = profile["metric_specs"]
st.markdown(f'<h3 class="section-title">Primary metrics · {profile["position"]}</h3>', unsafe_allow_html=True)
render_metric_grid(specs["primary"], profile["metrics"]["primary"], percentiles=primary_pct)
st.caption("P## badges = percentile vs same-position peers in the selected seasons / leagues / age range.")

st.markdown('<h3 class="section-title">Secondary metrics</h3>', unsafe_allow_html=True)
render_metric_grid(specs["secondary"], profile["metrics"]["secondary"])

# Similar players — same sidebar season window; one vector per player_id
st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
st.markdown('<h3 class="section-title">Similar players</h3>', unsafe_allow_html=True)
season_mode = "single season" if len(profile["seasons"]) == 1 else "multi-season window"
st.caption(
    f"Cosine similarity on standardized rate features vs same-position peers in the "
    f"selected **{season_mode}**. One profile per player (same player never repeats). "
    f"Candidates need ≥ {DEFAULT_MIN_MINUTES:.0f} minutes in the window."
)
similar = recommend_similar_players(
    peer_table,
    player_id,
    top_n=8,
    min_minutes=DEFAULT_MIN_MINUTES,
)
if similar.empty:
    st.info("Not enough same-position peers to recommend similar players. Widen filters or lower minutes.")
else:
    show = similar[
        [c for c in ["player_name", "teams", "leagues", "minutes", "age", "similarity"] if c in similar.columns]
    ].copy()
    show = show.rename(
        columns={
            "player_name": "Player",
            "teams": "Team(s)",
            "leagues": "League(s)",
            "minutes": "Minutes",
            "age": "Age",
            "similarity": "Similarity",
        }
    )
    show["Minutes"] = show["Minutes"].round(0).astype(int)
    show["Similarity"] = show["Similarity"].map(lambda x: f"{x:.3f}")
    if "Age" in show.columns:
        show["Age"] = show["Age"].map(lambda x: "" if pd.isna(x) else f"{x:.0f}")
    st.dataframe(show, width="stretch", hide_index=True)

# Multi-season trajectory (majority-position rows only)
st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
st.markdown('<h3 class="section-title">Season trajectory</h3>', unsafe_allow_html=True)
trend_df = build_season_trend_frame(pos_rows, profile["position"])
st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
st.plotly_chart(
    build_season_trend_chart(trend_df, profile["player_name"]),
    width="stretch",
    config={"displayModeBar": False},
)
st.markdown("</div>", unsafe_allow_html=True)
if len(trend_df) < 2:
    st.caption("Select multiple seasons in the sidebar to compare volume vs output over time.")

st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
st.markdown('<h3 class="section-title">Radar · peer percentiles</h3>', unsafe_allow_html=True)
radar_labels, radar_values = percentile_scores(peer_table, player_id, radar_metric_specs(profile["position"]))
st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
st.plotly_chart(
    build_radar_chart(radar_labels, radar_values, profile["player_name"]),
    width="stretch",
    config={"displayModeBar": False},
)
st.markdown("</div>", unsafe_allow_html=True)
if len(radar_labels) < 3:
    st.caption("Radar needs at least three rate metrics with peer coverage — widen filters if axes are missing.")

st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
st.markdown('<h3 class="section-title">Position scatter</h3>', unsafe_allow_html=True)
render_profile_scatter(peer_table, profile["position"], player_id, profile["player_name"], applied)

active_scatter = scatter_view_by_id(
    profile["position"], st.session_state.get("profile_scatter_view", "")
)
chart_context = {
    "season_trajectory": trend_df[
        ["season_label", "minutes", "primary_label", "primary_value"]
    ].to_dict(orient="records"),
    "radar_percentiles": [
        {"metric": label, "peer_percentile": value}
        for label, value in zip(radar_labels, radar_values)
    ],
    "scatter": build_scatter_chart_context(peer_table, [profile], active_scatter),
}
render_scout_analysis(
    [profile],
    peer_table,
    key_prefix="profile_scout",
    chart_context=chart_context,
)

with st.expander("Underlying season rows"):
    show_cols = [
        c
        for c in [
            "season",
            "league_name",
            "team_name",
            "position",
            "minutes",
            "age",
            "goals",
            "assists",
            "shots_total",
            "passes_total",
            "tackles_total",
        ]
        if c in pos_rows.columns
    ]
    display_rows = pos_rows[show_cols].sort_values("season").copy()
    if "season" in display_rows.columns:
        display_rows["season"] = display_rows["season"].map(format_season)
    st.dataframe(display_rows, width="stretch", hide_index=True)
