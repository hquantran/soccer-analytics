"""Single-player profile with position metrics, radar, trend, and scatter."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.charts import ACCENT_A, build_radar_chart, build_scatter_from_view, build_season_trend_chart
from dashboard.data import (
    aggregate_player_rows,
    build_peer_table,
    build_season_trend_frame,
    format_season,
    format_season_range,
    load_filter_dimension_values,
    load_peer_season_rows,
    load_player_lookup,
    load_player_seasons_by_id,
    metric_percentile_map,
    percentile_scores,
)
from dashboard.metrics_config import all_metric_specs, scatter_view_by_id, scatter_views_for_position
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

applied = render_profile_sidebar(lookup, dims)
if not applied or not applied.get("player_id"):
    st.info("Choose filters and a player in the sidebar to open a profile.")
    st.stop()

player_id = int(applied["player_id"])
seasons_t = tuple(applied["seasons"]) if applied["seasons"] else None
leagues_t = tuple(applied["leagues"]) if applied["leagues"] else None
teams_t = tuple(applied["teams"]) if applied["teams"] else None
age_min, age_max = applied["age_range"]
position = applied["position"]

# Exact player_id extraction — no name ILIKE / full-table scan in Python
player_rows = load_player_seasons_by_id(
    player_id,
    seasons=seasons_t,
    leagues=leagues_t,
    teams=teams_t,
)
if player_rows.empty:
    # Fall back to id-only if team/league filters exclude the selected stint
    player_rows = load_player_seasons_by_id(player_id, seasons=seasons_t)
if player_rows.empty:
    st.warning("Selected player has no rows for the applied season filters.")
    st.stop()

# Use the player's actual position from data when available
if "position" in player_rows.columns and not player_rows["position"].dropna().empty:
    position = str(player_rows["position"].dropna().iloc[-1])

peer_source = load_peer_season_rows(
    position,
    seasons=seasons_t,
    leagues=leagues_t,
    age_min=age_min,
    age_max=age_max,
)
peer_table = build_peer_table(peer_source, position)

profile = aggregate_player_rows(player_rows)
season_label = format_season_range(profile["seasons"])
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
          <div class="eyebrow">Soccer Analytics · Position profile</div>
          <p class="player-name">{profile['player_name']}</p>
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
    # No API rating — scouting header uses playing-time context only
    m1, m2, m3 = st.columns(3, gap="medium")
    m1.metric("Minutes", f"{profile['minutes']:.0f}")
    m2.metric("Appearances", f"{profile['appearances']:.0f}")
    age = profile.get("age")
    m3.metric("Age", f"{age:.0f}" if age is not None and age == age else "—")

st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
specs = profile["metric_specs"]
st.markdown(f'<h3 class="section-title">Primary metrics · {profile["position"]}</h3>', unsafe_allow_html=True)
render_metric_grid(specs["primary"], profile["metrics"]["primary"], percentiles=primary_pct)
st.caption("P## badges = percentile vs same-position peers in the selected seasons / leagues / age range.")

st.markdown('<h3 class="section-title">Secondary metrics</h3>', unsafe_allow_html=True)
render_metric_grid(specs["secondary"], profile["metrics"]["secondary"])

# Multi-season trajectory
st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
st.markdown('<h3 class="section-title">Season trajectory</h3>', unsafe_allow_html=True)
trend_df = build_season_trend_frame(player_rows, profile["position"])
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
radar_labels, radar_values = percentile_scores(peer_table, player_id, all_metric_specs(profile["position"]))
st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
st.plotly_chart(
    build_radar_chart(radar_labels, radar_values, profile["player_name"]),
    width="stretch",
    config={"displayModeBar": False},
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
st.markdown('<h3 class="section-title">Position scatter</h3>', unsafe_allow_html=True)
render_profile_scatter(peer_table, profile["position"], player_id, profile["player_name"], applied)

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
        if c in player_rows.columns
    ]
    display_rows = player_rows[show_cols].sort_values("season").copy()
    if "season" in display_rows.columns:
        display_rows["season"] = display_rows["season"].map(format_season)
    st.dataframe(display_rows, width="stretch", hide_index=True)
