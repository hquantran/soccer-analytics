"""Compare two players in the same position."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.charts import ACCENT_A, ACCENT_B, build_comparison_radar, build_scatter_from_view
from dashboard.data import (
    aggregate_player_rows,
    build_peer_table,
    load_filter_dimension_values,
    load_peer_season_rows,
    load_player_lookup,
    load_player_seasons_by_id,
    percentile_scores,
)
from dashboard.metrics_config import radar_metric_specs, scatter_view_by_id, scatter_views_for_position
from dashboard.ui import inject_theme_css, render_compare_sidebar, render_metric_grid

inject_theme_css()

st.title("Player comparison")
st.caption("Same-position head-to-head: percentile radar (0–100) and dual-highlight scatter.")


def _player_header_card(profile: dict, accent_hex: str, eyebrow: str) -> None:
    photo = profile.get("photo")
    age = profile.get("age")
    age_txt = f"{age:.0f}" if age is not None and age == age else "—"
    teams = ", ".join(profile.get("teams") or []) or "—"
    left, right = st.columns([1, 3], gap="medium")
    with left:
        if photo:
            st.image(photo, width=120)
        else:
            st.caption("No photo")
    with right:
        st.markdown(
            f"""
            <div class="hero" style="margin-bottom:0;">
              <div class="eyebrow" style="color:{accent_hex};">{eyebrow}</div>
              <p class="player-name">{profile['player_name']}</p>
              <div class="meta">
                <strong>{profile['position']}</strong>
                · {teams}
                · Age {age_txt}
                · {profile['minutes']:.0f} minutes
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


try:
    lookup = load_player_lookup()
    dims = load_filter_dimension_values()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

applied = render_compare_sidebar(lookup, dims)
if not applied:
    st.info("Choose filters and two different players in the sidebar.")
    st.stop()

age_min, age_max = applied["age_range"]
position = applied["position"]
seasons_t = tuple(applied["seasons"]) if applied["seasons"] else None
leagues_t = tuple(applied["leagues"]) if applied["leagues"] else None
teams_t = tuple(applied["teams"]) if applied["teams"] else None

id_a = int(applied["player_id"])
id_b = int(applied["compare_player_id"])

rows_a = load_player_seasons_by_id(id_a, seasons=seasons_t, leagues=leagues_t, teams=teams_t)
rows_b = load_player_seasons_by_id(id_b, seasons=seasons_t, leagues=leagues_t, teams=teams_t)
if rows_a.empty:
    rows_a = load_player_seasons_by_id(id_a, seasons=seasons_t)
if rows_b.empty:
    rows_b = load_player_seasons_by_id(id_b, seasons=seasons_t)
if rows_a.empty or rows_b.empty:
    st.warning("One or both players are missing under the applied filters.")
    st.stop()

if rows_a.iloc[0]["position"] != rows_b.iloc[0]["position"]:
    st.error("Players must share the same position. Adjust filters and re-select.")
    st.stop()

position = str(rows_a.iloc[0]["position"])
peer_source = load_peer_season_rows(
    position,
    seasons=seasons_t,
    leagues=leagues_t,
    age_min=age_min,
    age_max=age_max,
)
peer_table = build_peer_table(peer_source, position)

profile_a = aggregate_player_rows(rows_a)
profile_b = aggregate_player_rows(rows_b)

c1, c2 = st.columns(2, gap="large")
with c1:
    _player_header_card(profile_a, "#C36A4A", "Player A")
    render_metric_grid(profile_a["metric_specs"]["primary"], profile_a["metrics"]["primary"])
with c2:
    _player_header_card(profile_b, "#4A90A4", "Player B")
    render_metric_grid(profile_b["metric_specs"]["primary"], profile_b["metrics"]["primary"])

radar_specs = radar_metric_specs(position)
labels_a, values_a = percentile_scores(peer_table, id_a, radar_specs)
labels_b, values_b = percentile_scores(peer_table, id_b, radar_specs)

label_to_a = dict(zip(labels_a, values_a))
label_to_b = dict(zip(labels_b, values_b))
shared_labels = [lab for lab in labels_a if lab in label_to_b]
aligned_a = [label_to_a[lab] for lab in shared_labels]
aligned_b = [label_to_b[lab] for lab in shared_labels]

st.markdown('<h3 class="section-title">Stacked percentile radar</h3>', unsafe_allow_html=True)
st.caption("Each axis is a 0–100 positional percentile vs peers in the selected filters. Raw totals are excluded.")
st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
st.plotly_chart(
    build_comparison_radar(
        shared_labels,
        aligned_a,
        aligned_b,
        profile_a["player_name"],
        profile_b["player_name"],
    ),
    width="stretch",
    config={"displayModeBar": False},
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<h3 class="section-title">Position scatter</h3>', unsafe_allow_html=True)
views = scatter_views_for_position(position)
view_labels = {v.id: v.title for v in views}
default_view = applied.get("scatter_view_id") if applied.get("scatter_view_id") in view_labels else views[0].id
view_id = st.selectbox(
    "Scatter view",
    options=list(view_labels.keys()),
    format_func=lambda vid: view_labels[vid],
    index=list(view_labels.keys()).index(default_view),
)
view = scatter_view_by_id(position, view_id)
st.session_state.setdefault("filters_compare", {})
st.session_state["filters_compare"]["scatter_view_id"] = view_id

st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
st.plotly_chart(
    build_scatter_from_view(
        peer_table,
        view,
        position,
        highlights=[
            (id_a, profile_a["player_name"], ACCENT_A),
            (id_b, profile_b["player_name"], ACCENT_B),
        ],
    ),
    width="stretch",
    config={"displayModeBar": False},
)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown(f'<p class="insight">{view.insight}</p>', unsafe_allow_html=True)
