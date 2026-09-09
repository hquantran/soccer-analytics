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
from dashboard.ui import inject_theme_css, render_metric_grid, render_profile_sidebar

inject_theme_css()

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
    if profile.get("used_bi_rates"):
        st.caption("Rates for this single season/stint reuse BI-layer values.")
    else:
        st.caption("Rates recomputed from summed volume across the selected seasons/stints.")

st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
specs = profile["metric_specs"]
st.markdown(f'<h3 class="section-title">Primary metrics · {profile["position"]}</h3>', unsafe_allow_html=True)
render_metric_grid(specs["primary"], profile["metrics"]["primary"], percentiles=primary_pct)
st.caption("P## badges = percentile vs same-position peers in the selected seasons / leagues / age range.")

st.markdown('<h3 class="section-title">Secondary metrics</h3>', unsafe_allow_html=True)
render_metric_grid(specs["secondary"], profile["metrics"]["secondary"])

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

views = scatter_views_for_position(profile["position"])
view_labels = {v.id: v.title for v in views}
default_view = applied.get("scatter_view_id") if applied.get("scatter_view_id") in view_labels else views[0].id
view_id = st.selectbox(
    "Scatter view",
    options=list(view_labels.keys()),
    format_func=lambda vid: view_labels[vid],
    index=list(view_labels.keys()).index(default_view),
)
view = scatter_view_by_id(profile["position"], view_id)
st.session_state.setdefault("filters_profile", {})
st.session_state["filters_profile"]["scatter_view_id"] = view_id

st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
st.plotly_chart(
    build_scatter_from_view(
        peer_table,
        view,
        profile["position"],
        highlights=[(player_id, profile["player_name"], ACCENT_A)],
    ),
    width="stretch",
    config={"displayModeBar": False},
)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown(f'<p class="insight">{view.insight}</p>', unsafe_allow_html=True)

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
