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
    cached_peer_table,
    ensure_players_in_peer_table,
    format_age,
    load_filter_dimension_values,
    load_player_lookup,
    load_player_seasons_by_id,
    metric_percentile_map,
    percentile_scores,
)
from dashboard.metrics_config import radar_metric_specs, scatter_view_by_id, scatter_views_for_position
from dashboard.ui import inject_theme_css, render_compare_sidebar, render_metric_grid

inject_theme_css()

st.title("Player comparison")
st.caption("Same-position head-to-head: percentile radar (0–100) and dual-highlight scatter.")


def _player_header_card(profile: dict, name_class: str = "player-name compare") -> None:
    photo = profile.get("photo")
    age_txt = format_age(profile.get("age"))
    teams = ", ".join(profile.get("teams") or []) or "—"
    # Wider text column so long club names (e.g. Paris Saint Germain) can wrap cleanly
    left, right = st.columns([1, 4.2], gap="medium")
    with left:
        if photo:
            st.image(photo, width=120)
        else:
            st.caption("No photo")
    with right:
        st.markdown(
            f"""
            <div class="hero compare-hero">
              <p class="{name_class}" style="font-size:2.75rem !important;font-weight:700 !important;font-family:'Space Grotesk',sans-serif !important;margin:0 !important;line-height:1.15 !important;color:#E7D8C6 !important;">
                {profile['player_name']}
              </p>
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

profile_a = aggregate_player_rows(rows_a)
profile_b = aggregate_player_rows(rows_b)

if profile_a["position"] != profile_b["position"]:
    st.error(
        f"Players resolve to different majority positions "
        f"({profile_a['player_name']}: {profile_a['position']} vs "
        f"{profile_b['player_name']}: {profile_b['position']}). "
        "Pick players who share the same majority position, or narrow seasons."
    )
    st.stop()

position = profile_a["position"]
pos_rows_a = profile_a["rows"]
pos_rows_b = profile_b["rows"]

peer_table = cached_peer_table(
    position,
    seasons_t,
    leagues_t,
    float(age_min),
    float(age_max),
)
peer_table = ensure_players_in_peer_table(peer_table, [pos_rows_a, pos_rows_b], position)

pct_a = metric_percentile_map(peer_table, id_a, profile_a["metric_specs"]["primary"])
pct_b = metric_percentile_map(peer_table, id_b, profile_b["metric_specs"]["primary"])

c1, c2 = st.columns(2, gap="large")
with c1:
    _player_header_card(profile_a)
with c2:
    _player_header_card(profile_b)

st.markdown('<div style="height:1.15rem;"></div>', unsafe_allow_html=True)

m1, m2 = st.columns(2, gap="large")
with m1:
    render_metric_grid(
        profile_a["metric_specs"]["primary"],
        profile_a["metrics"]["primary"],
        percentiles=pct_a,
    )
with m2:
    render_metric_grid(
        profile_b["metric_specs"]["primary"],
        profile_b["metrics"]["primary"],
        percentiles=pct_b,
    )

if profile_a.get("position_info", {}).get("used_majority") or profile_b.get("position_info", {}).get("used_majority"):
    st.caption(
        "Position uses majority seasons played within the selected window; "
        "metrics only include rows at that position."
    )
if profile_a.get("used_bi_rates") and profile_b.get("used_bi_rates"):
    st.caption("Both players: single season/stint rates reuse BI-layer values.")
else:
    st.caption("Rates reuse BI when a player has one season/stint row; otherwise sum volume then recompute.")
st.caption("P## badges = percentile vs same-position peers in the selected filters.")

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
if len(shared_labels) < 3:
    st.caption("Radar needs at least three shared rate metrics — widen filters if axes are missing.")

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
