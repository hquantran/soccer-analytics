"""Top players overview page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.charts import build_metric_distribution
from dashboard.data import (
    build_peer_table,
    filter_frame,
    format_metric_value,
    format_season,
    load_filter_dimension_values,
    position_averages,
    top_players_table,
)
from dashboard.metrics_config import MetricSpec, metrics_for_position
from dashboard.ui import get_data, inject_theme_css, render_overview_sidebar

inject_theme_css()

st.title("Top players")
st.caption("Tactical leaderboards by position — filtered by minutes, league, and season.")

try:
    df = get_data()
    dims = load_filter_dimension_values()
except FileNotFoundError as exc:
    st.error(str(exc))
    st.stop()

df = df[df["position"] != "Goalkeeper"].copy()
applied = render_overview_sidebar(dims)

age_min, age_max = applied["age_range"]
position = applied["position"]
sort_key = applied["sort_key"]
sort_label = applied["sort_label"]
min_minutes = float(applied["min_minutes"])

filtered = filter_frame(
    df,
    leagues=applied["leagues"] or None,
    seasons=applied["seasons"] or None,
    teams=applied["teams"] or None,
    positions=[position],
    age_min=age_min,
    age_max=age_max,
)

if applied.get("seasons") and 2026 in applied["seasons"]:
    n_all = len(filtered)
    if n_all < 50:
        st.info(
            f"Season **{format_season(2026)}** is still early under the 300' staging filter "
            f"({n_all} rows). Try {format_season(2025)} for a fuller sample."
        )

peer_table = build_peer_table(filtered, position)
top = top_players_table(
    filtered,
    position,
    limit=5,
    sort_key=sort_key,
    min_minutes=min_minutes,
    defender_profile=applied.get("defender_profile"),
)
if top.empty:
    st.warning(
        f"No players match these filters with ≥ {min_minutes:.0f} minutes. "
        "Lower the minutes slider or widen leagues/seasons."
    )
    st.stop()

# Spec used for formatting the sort column
sort_spec = None
for block in metrics_for_position(position).values():
    for spec in block:
        if spec.key == sort_key:
            sort_spec = spec
            break
if sort_spec is None:
    sort_spec = MetricSpec(sort_key, sort_label, sort_key, None, 1.0, "{:.2f}")

profile_note = ""
if position == "Defender" and applied.get("defender_profile") not in (None, "All Defenders"):
    profile_note = f" · {applied['defender_profile']}"

st.markdown(
    f'<h3 class="section-title">Top 5 · {position}{profile_note} · {sort_label}</h3>',
    unsafe_allow_html=True,
)
st.caption(
    "API-Football has no xG / SCA / progressive passes — leaderboard uses the closest "
    "available rates (Goals/90, Shots/90, Key Passes/90, Passes/90, Duel Success %)."
)

display = top[
    [c for c in ["player_name", sort_key, "age", "minutes", "appearances", "teams", "leagues"] if c in top.columns]
].copy()
display.insert(0, "Rank", range(1, len(display) + 1))
display = display.rename(
    columns={
        "player_name": "Player",
        sort_key: sort_label,
        "age": "Age",
        "minutes": "Minutes",
        "appearances": "Apps",
        "teams": "Team(s)",
        "leagues": "League(s)",
    }
)
display[sort_label] = display[sort_label].map(lambda x: format_metric_value(x, sort_spec))
display["Minutes"] = display["Minutes"].map(lambda x: f"{x:.0f}")
display["Apps"] = display["Apps"].map(lambda x: f"{x:.0f}")
if "Age" in display.columns:
    display["Age"] = display["Age"].map(lambda x: f"{x:.0f}" if x == x else "—")

st.dataframe(display, width="stretch", hide_index=True)

# Position averages banner (replaces bottom rank cards)
avg_specs = [s for s in metrics_for_position(position)["primary"] if s.denominator is not None][:4]
eligible = peer_table[peer_table["minutes"] >= min_minutes] if "minutes" in peer_table.columns else peer_table
if position == "Defender" and applied.get("defender_profile") not in (None, "All Defenders"):
    # Mirror the same proxy split used for ranking
    if "key_passes_per90" in eligible.columns and eligible["key_passes_per90"].notna().any():
        median_kp = float(eligible["key_passes_per90"].median())
        if applied["defender_profile"] == "Full-Back profile":
            eligible = eligible[eligible["key_passes_per90"].fillna(0) >= median_kp]
        else:
            eligible = eligible[eligible["key_passes_per90"].fillna(0) < median_kp]

averages = position_averages(eligible, avg_specs)
st.markdown('<h3 class="section-title">Position averages</h3>', unsafe_allow_html=True)
st.caption(
    f"Means across {len(eligible)} {position.lower()}s with ≥ {min_minutes:.0f} minutes "
    "in the selected leagues / seasons."
)
banner_cols = st.columns(min(4, max(1, len(avg_specs))), gap="medium")
for i, spec in enumerate(avg_specs):
    with banner_cols[i % len(banner_cols)]:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">{spec.label}</div>
              <div class="metric-value">{format_metric_value(averages.get(spec.key), spec)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<h3 class="section-title">Metric distribution</h3>', unsafe_allow_html=True)
st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
st.plotly_chart(
    build_metric_distribution(
        eligible,
        sort_key,
        sort_label,
        highlight_ids=top["player_id"].tolist(),
    ),
    width="stretch",
    config={"displayModeBar": False},
)
st.markdown("</div>", unsafe_allow_html=True)
st.caption("Orange line = position mean. Diamonds mark the current Top 5.")
