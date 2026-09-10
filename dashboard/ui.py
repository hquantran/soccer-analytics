"""Shared Streamlit UI helpers: theme CSS, filter bar, search suggestions."""

from __future__ import annotations

import streamlit as st

from dashboard.data import (
    filter_frame,
    format_season,
    load_player_seasons,
    top_player_matches,
)


def inject_theme_css() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');

          :root {
            --bg: #101417;
            --card: #1C232B;
            --card-border: #2A333C;
            --text: #E7D8C6;
            --muted: #A89888;
            --accent: #C36A4A;
          }

          .stApp {
            background: var(--bg);
            color: var(--text);
            font-family: 'DM Sans', sans-serif;
          }
          [data-testid="stSidebar"] {
            background: #0E1216;
            border-right: 1px solid var(--card-border);
          }
          .block-container {
            padding-top: 1.2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
          }
          h1, h2, h3, .player-name {
            font-family: 'Space Grotesk', sans-serif;
            letter-spacing: -0.02em;
            color: var(--text) !important;
          }
          .stCaption, [data-testid="stCaptionContainer"] {
            color: var(--muted) !important;
          }
          div[data-testid="stMetric"] {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 0.85rem 1rem;
          }
          div[data-testid="stMetric"] label { color: var(--muted) !important; }
          div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: var(--text) !important;
            font-family: 'Space Grotesk', sans-serif;
          }
          .filter-bar {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 1rem 1.1rem 0.85rem 1.1rem;
            margin: 0.4rem 0 1.4rem 0;
          }
          .hero {
            background: linear-gradient(135deg, #151A1F 0%, #1C232B 45%, #3A2A24 100%);
            color: var(--text);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 1.45rem 1.6rem;
            margin-bottom: 1.35rem !important;
          }
          .hero .eyebrow {
            text-transform: uppercase;
            font-size: 0.72rem;
            color: var(--muted);
            letter-spacing: 0.1em;
            margin-bottom: 0.35rem;
          }
          /* Streamlit resets <p> font-size — force hero names large */
          .hero .player-name,
          .hero p.player-name,
          div.hero p {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 2.75rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            line-height: 1.15 !important;
            color: var(--text) !important;
            letter-spacing: -0.02em !important;
          }
          .meta,
          .hero .meta,
          .hero div.meta {
            color: var(--muted) !important;
            margin-top: 0.5rem !important;
            font-size: 0.98rem !important;
            font-weight: 400 !important;
            line-height: 1.45 !important;
            overflow-wrap: anywhere;
            word-break: break-word;
          }
          .hero.compare-hero {
            min-height: 7.5rem;
            padding: 1.25rem 1.35rem;
            margin-bottom: 1.35rem !important;
          }
          .compare-header-gap {
            height: 0.35rem;
            margin-bottom: 0.85rem;
          }
          /* Keep multiselect chips readable instead of truncating mid-label */
          [data-baseweb="tag"] {
            max-width: 100% !important;
          }
          [data-baseweb="tag"] span {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: unset !important;
          }
          [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
            max-height: none !important;
            flex-wrap: wrap !important;
          }
          .metric-card {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 0.95rem 1rem 1rem 1rem;
            height: 100%;
            min-height: 6.75rem;
            margin-bottom: 0.55rem;
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
          }
          .metric-label {
            font-size: 0.76rem;
            color: var(--muted);
            margin-bottom: 0.45rem;
            min-height: 2.4em;
            line-height: 1.2;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 0.45rem;
          }
          .metric-label > span:first-child {
            flex: 1;
            min-width: 0;
          }
          .metric-value {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.45rem;
            font-weight: 700;
            color: var(--text);
            margin-top: auto;
            line-height: 1.1;
          }
          .pct-badge {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            padding: 0.15rem 0.45rem;
            border-radius: 999px;
            border: 1px solid var(--card-border);
            color: var(--muted);
            background: #151A1F;
            white-space: nowrap;
          }
          .pct-badge.high {
            color: #E7D8C6;
            border-color: #C36A4A;
            background: rgba(195, 106, 74, 0.22);
          }
          .pct-badge.mid {
            color: #E7D8C6;
            border-color: #4A90A4;
            background: rgba(74, 144, 164, 0.18);
          }
          .section-title {
            margin: 1.75rem 0 0.85rem 0;
            color: var(--text);
            font-size: 1.2rem;
          }
          .chart-panel {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 0.75rem 0.85rem 0.55rem 0.85rem;
            margin: 0.35rem 0 1.1rem 0;
          }
          .insight {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.45;
            margin: 0 0 1.4rem 0;
          }
          .viz-spacer { height: 1.25rem; }
          .suggest-box {
            background: #151A1F;
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 0.35rem;
            margin-top: 0.35rem;
            max-height: 220px;
            overflow-y: auto;
          }
          [data-testid="stExpander"] {
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 12px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_data():
    return load_player_seasons()


def default_filters(df) -> dict:
    leagues = sorted(df["league_name"].dropna().unique().tolist())
    seasons = sorted(df["season"].dropna().unique().tolist())
    positions = sorted(p for p in df["position"].dropna().unique().tolist() if p != "Goalkeeper")
    ages = df["age"].dropna()
    age_lo = int(ages.min()) if not ages.empty else 16
    age_hi = int(ages.max()) if not ages.empty else 40
    return {
        "leagues": leagues,
        "seasons": seasons,  # Select All by default
        "position": "Midfielder" if "Midfielder" in positions else (positions[0] if positions else None),
        "teams": [],
        "age_range": (age_lo, age_hi),
        "player_id": None,
        "player_name": None,
        "compare_player_id": None,
        "compare_player_name": None,
        "scatter_view_id": None,
    }


def _selection_caption(label: str, values: list, *, empty: str = "All") -> None:
    """Show the full selected filter list (multiselect chips often truncate)."""
    if not values:
        st.caption(f"{label}: {empty}")
        return
    shown = ", ".join(str(v) for v in values)
    st.caption(f"{label}: {shown}")


def _render_season_filter(prefix: str, seasons_all: list[int]) -> list[int]:
    """
    Single vs multi season toggle shared by all sidebars.
    Single → selectbox (latest default). Multi → multiselect (all selected).
    """
    season_labels = [format_season(s) for s in seasons_all]
    label_to_season = {format_season(s): int(s) for s in seasons_all}
    latest_label = season_labels[-1] if season_labels else None

    mode = st.radio(
        "Season mode",
        options=["Single season", "Multi season"],
        horizontal=True,
        key=f"{prefix}_season_mode_v2",
        help="Single season uses one BI season row path; multi aggregates volume across seasons.",
    )

    if mode == "Single season":
        if not season_labels:
            st.caption("Seasons: None")
            return []
        default_idx = season_labels.index(latest_label) if latest_label in season_labels else 0
        pick = st.selectbox(
            "Season",
            season_labels,
            index=default_idx,
            key=f"{prefix}_season_single",
            help="API season year = season start (e.g. 2022/2023).",
        )
        seasons = [label_to_season[pick]]
        _selection_caption("Season", [pick], empty="None")
        return seasons

    season_pick = st.multiselect(
        "Season",
        season_labels,
        default=season_labels,
        key=f"{prefix}_seasons_multi",
        help="API season year = season start (e.g. 2022/2023). Default: all seasons.",
    )
    seasons = [label_to_season[s] for s in season_pick]
    _selection_caption("Seasons", season_pick, empty="None")
    return seasons


def render_metric_grid(specs, values: dict, percentiles: dict | None = None) -> None:
    if not specs:
        return
    # Prefer even rows so values line up across compare columns
    n_cols = 3 if len(specs) >= 5 else min(4, len(specs))
    cols = st.columns(n_cols, gap="medium")
    for i, spec in enumerate(specs):
        with cols[i % n_cols]:
            from dashboard.data import format_metric_value

            display = format_metric_value(values.get(spec.key), spec)
            badge = ""
            if percentiles and spec.key in percentiles:
                pct = int(percentiles[spec.key])
                tier = "high" if pct >= 75 else ("mid" if pct >= 50 else "")
                badge = f'<span class="pct-badge {tier}">P{pct}</span>'
            st.markdown(
                f"""
                <div class="metric-card">
                  <div class="metric-label"><span>{spec.label}</span>{badge}</div>
                  <div class="metric-value">{display}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def _default_position(positions_all: list[str]) -> str:
    if "Midfielder" in positions_all:
        return "Midfielder"
    return positions_all[0] if positions_all else "Midfielder"


def _scope_player_lookup(lookup, *, position: str | None, leagues, age_range, teams):
    scoped = lookup.copy()
    if position:
        scoped = scoped[scoped["position"] == position]
    age = scoped["age"]
    scoped = scoped[age.isna() | ((age >= age_range[0]) & (age <= age_range[1]))]
    if leagues:
        scoped = scoped[scoped["league_name"].isin(leagues)]
    if teams:
        scoped = scoped[scoped["team_name"].isin(teams)]
    return scoped.sort_values("player_name").reset_index(drop=True)


def _searchable_player_select(scoped, *, state_key: str, label: str) -> tuple[int | None, str | None]:
    """Search first, then serialize only a small player candidate list."""
    query = (st.text_input(
        f"Find {label.lower()}",
        key=f"{state_key}_search",
        placeholder="Type a player name",
    ) or "").strip().lower()
    candidates = scoped
    if query:
        candidates = candidates[candidates["player_name"].str.lower().str.contains(query, regex=False, na=False)]
    candidates = candidates.head(75)
    if candidates.empty:
        st.caption("No matching players.")
        return None, None

    id_to_label = {
        int(row.player_id): f"{row.player_name} · {row.team_name}"
        for row in candidates.itertuples(index=False)
    }
    options = list(id_to_label)
    selection_key = f"{state_key}_id"
    if st.session_state.get(selection_key) not in options:
        st.session_state[selection_key] = options[0]
    player_id = st.selectbox(
        label,
        options=options,
        format_func=lambda pid: id_to_label[pid],
        key=selection_key,
    )
    player_name = str(candidates.loc[candidates["player_id"] == player_id, "player_name"].iloc[0])
    return int(player_id), player_name


def render_profile_sidebar(lookup, dims: dict) -> dict | None:
    """Sidebar with player select first, then filter controls."""
    leagues_all = dims["leagues"]
    seasons_all = dims["seasons"]
    positions_all = dims["positions"]
    age_lo, age_hi = dims["age_min"], dims["age_max"]
    default_pos = _default_position(positions_all)

    with st.sidebar:
        # Scope from prior filter widget state so Player can sit at the top.
        # Position is advanced-only and does not gate the player list (profile uses the player's recorded position).
        leagues_pre = st.session_state.get("profile_sb_leagues", leagues_all)
        age_pre = st.session_state.get("profile_sb_age", (age_lo, age_hi))
        teams_pre = st.session_state.get("profile_sb_teams", [])

        scoped = _scope_player_lookup(
            lookup,
            position=None,
            leagues=leagues_pre,
            age_range=age_pre,
            teams=teams_pre,
        )

        st.markdown("### Player")
        name_q = (st.text_input("Filter by name", key="profile_sb_name_q", placeholder="Type to narrow list…") or "").strip()
        if name_q and not scoped.empty:
            scoped = scoped[scoped["player_name"].str.contains(name_q, case=False, na=False)]

        if scoped.empty:
            st.warning("No players match the filters below.")
            player_id = None
            player_name = None
        else:
            id_to_label = {
                int(r.player_id): f"{r.player_name} · {r.team_name}"
                for r in scoped.itertuples(index=False)
            }
            options = list(id_to_label.keys())
            # Drop stale selection if filters removed that player.
            if st.session_state.get("profile_sb_player_id") not in options:
                st.session_state["profile_sb_player_id"] = options[0]
            player_id = st.selectbox(
                "Select player",
                options=options,
                format_func=lambda pid: id_to_label[pid],
                key="profile_sb_player_id",
            )
            player_name = str(scoped.loc[scoped["player_id"] == player_id, "player_name"].iloc[0])

        st.markdown("### Filters")
        leagues = st.multiselect(
            "League",
            leagues_all,
            default=leagues_all,
            key="profile_sb_leagues",
        )
        _selection_caption("Leagues", leagues, empty="None")
        seasons = _render_season_filter("profile_sb", seasons_all)

        with st.expander("Advanced filters", expanded=False):
            position = st.selectbox(
                "Peer position override",
                positions_all,
                index=positions_all.index(default_pos) if default_pos in positions_all else 0,
                key="profile_sb_position",
                help="Only used if the player's BI rows lack a position. Charts normally use the player's recorded position.",
            )
            age_range = st.slider(
                "Age range",
                min_value=age_lo,
                max_value=age_hi,
                value=(age_lo, age_hi),
                key="profile_sb_age",
            )
            team_pool = _scope_player_lookup(
                lookup,
                position=None,
                leagues=leagues,
                age_range=age_range,
                teams=[],
            )
            teams_all = sorted(team_pool["team_name"].dropna().unique().tolist())
            teams = st.multiselect("Team", teams_all, default=[], key="profile_sb_teams")
            _selection_caption("Teams", teams, empty="All teams")

        if player_id is None:
            return None

        return {
            "leagues": leagues,
            "seasons": seasons,
            "position": position,
            "teams": teams,
            "age_range": age_range,
            "player_id": int(player_id),
            "player_name": player_name,
            "scatter_view_id": st.session_state.get("filters_profile", {}).get("scatter_view_id"),
        }


def render_overview_sidebar(dims: dict) -> dict:
    """Sidebar filters for Top Players, including mandatory min-minutes."""
    from dashboard.metrics_config import DEFENDER_SUBPOSITIONS, TOP_SORT_OPTIONS

    leagues_all = dims["leagues"]
    seasons_all = dims["seasons"]
    positions_all = dims["positions"]
    age_lo, age_hi = dims["age_min"], dims["age_max"]
    teams_all = dims["teams"]

    with st.sidebar:
        st.markdown("### Filters")
        leagues = st.multiselect(
            "League",
            leagues_all,
            default=leagues_all,
            key="overview_sb_leagues",
        )
        _selection_caption("Leagues", leagues, empty="None")
        seasons = _render_season_filter("overview_sb", seasons_all)
        position = st.selectbox(
            "Position",
            positions_all,
            index=positions_all.index("Midfielder") if "Midfielder" in positions_all else 0,
            key="overview_sb_position",
        )
        age_range = st.slider(
            "Age range",
            min_value=age_lo,
            max_value=age_hi,
            value=(age_lo, age_hi),
            key="overview_sb_age",
        )
        teams = st.multiselect("Team", teams_all, default=[], key="overview_sb_teams")
        _selection_caption("Teams", teams, empty="All teams")
        min_minutes = st.slider(
            "Minimum minutes played",
            min_value=300,
            max_value=4000,
            value=900,
            step=50,
            key="overview_sb_min_minutes",
            help="Filters out small-sample outliers before ranking.",
        )

        defender_profile = "All Defenders"
        if position == "Defender":
            defender_profile = st.selectbox(
                "Sub-position",
                DEFENDER_SUBPOSITIONS,
                key="overview_sb_defender_profile",
                help="Proxy split: Full-Back = above-median key passes/90 among defenders; Center-Back = below.",
            )

        sort_opts = TOP_SORT_OPTIONS.get(position, TOP_SORT_OPTIONS["Midfielder"])
        sort_labels = [label for _, label in sort_opts]
        sort_choice = st.selectbox("Sort by", sort_labels, key="overview_sb_sort")
        sort_key = next(key for key, label in sort_opts if label == sort_choice)

    return {
        "leagues": leagues,
        "seasons": seasons,
        "position": position,
        "teams": teams,
        "age_range": age_range,
        "min_minutes": min_minutes,
        "sort_key": sort_key,
        "sort_label": sort_choice,
        "defender_profile": defender_profile,
    }


def render_compare_sidebar(lookup, dims: dict) -> dict | None:
    """Sidebar with Player A/B first, then filter controls."""
    leagues_all = dims["leagues"]
    seasons_all = dims["seasons"]
    positions_all = dims["positions"]
    age_lo, age_hi = dims["age_min"], dims["age_max"]
    default_pos = _default_position(positions_all)

    with st.sidebar:
        position_pre = st.session_state.get("compare_sb_position", default_pos)
        leagues_pre = st.session_state.get("compare_sb_leagues", leagues_all)
        age_pre = st.session_state.get("compare_sb_age", (age_lo, age_hi))
        teams_pre = st.session_state.get("compare_sb_teams", [])

        scoped = _scope_player_lookup(
            lookup,
            position=position_pre,
            leagues=leagues_pre,
            age_range=age_pre,
            teams=teams_pre,
        )

        st.markdown("### Players")
        name_q = (st.text_input("Filter by name", key="compare_sb_name_q", placeholder="Type to narrow list…") or "").strip()
        if name_q and not scoped.empty:
            scoped = scoped[scoped["player_name"].str.contains(name_q, case=False, na=False)]

        if scoped.empty:
            st.warning("No players match the filters below.")
            id_a = id_b = None
            name_a = name_b = None
        else:
            id_to_label = {
                int(r.player_id): f"{r.player_name} · {r.team_name}"
                for r in scoped.itertuples(index=False)
            }
            options = list(id_to_label.keys())
            if st.session_state.get("compare_sb_player_a_id") not in options:
                st.session_state["compare_sb_player_a_id"] = options[0]
            if st.session_state.get("compare_sb_player_b_id") not in options:
                st.session_state["compare_sb_player_b_id"] = options[min(1, len(options) - 1)]

            id_a = st.selectbox(
                "Player A",
                options=options,
                format_func=lambda pid: id_to_label[pid],
                key="compare_sb_player_a_id",
            )
            id_b = st.selectbox(
                "Player B",
                options=options,
                format_func=lambda pid: id_to_label[pid],
                key="compare_sb_player_b_id",
            )
            name_a = str(scoped.loc[scoped["player_id"] == id_a, "player_name"].iloc[0])
            name_b = str(scoped.loc[scoped["player_id"] == id_b, "player_name"].iloc[0])

        st.markdown("### Filters")
        leagues = st.multiselect(
            "League",
            leagues_all,
            default=leagues_all,
            key="compare_sb_leagues",
        )
        _selection_caption("Leagues", leagues, empty="None")
        seasons = _render_season_filter("compare_sb", seasons_all)

        with st.expander("Advanced filters", expanded=False):
            position = st.selectbox(
                "Position",
                positions_all,
                index=positions_all.index(default_pos) if default_pos in positions_all else 0,
                key="compare_sb_position",
            )
            age_range = st.slider(
                "Age range",
                min_value=age_lo,
                max_value=age_hi,
                value=(age_lo, age_hi),
                key="compare_sb_age",
            )
            team_pool = _scope_player_lookup(
                lookup,
                position=position,
                leagues=leagues,
                age_range=age_range,
                teams=[],
            )
            teams_all = sorted(team_pool["team_name"].dropna().unique().tolist())
            teams = st.multiselect("Team", teams_all, default=[], key="compare_sb_teams")
            _selection_caption("Teams", teams, empty="All teams")

        if id_a is None or id_b is None:
            return None
        if id_a == id_b:
            st.warning("Choose two different players.")
            return None

        return {
            "leagues": leagues,
            "seasons": seasons,
            "position": position,
            "teams": teams,
            "age_range": age_range,
            "player_id": int(id_a),
            "player_name": name_a,
            "compare_player_id": int(id_b),
            "compare_player_name": name_b,
            "scatter_view_id": st.session_state.get("filters_compare", {}).get("scatter_view_id"),
        }


def _player_suggest_list(
    search_base,
    query: str,
    state_key: str,
    label: str,
) -> tuple[int | None, str | None]:
    """One search box + one-click suggestion buttons (on_click avoids remount races)."""
    from st_keyup import st_keyup

    id_key = f"{state_key}_id"
    name_key = f"{state_key}_name"
    ver_key = f"{state_key}_ver"

    selected_id = st.session_state.get(id_key)
    selected_name = st.session_state.get(name_key)
    version = int(st.session_state.get(ver_key, 0))

    # Locked selection — edit the name to search again.
    if selected_id is not None and selected_name:
        edit_key = f"{state_key}_edit_{version}"
        if edit_key not in st.session_state:
            st.session_state[edit_key] = selected_name
        edited = (st.text_input(label, key=edit_key) or "").strip()
        if edited != selected_name:
            st.session_state.pop(id_key, None)
            st.session_state.pop(name_key, None)
            next_ver = version + 1
            st.session_state[ver_key] = next_ver
            st.session_state[f"{state_key}_q_{next_ver}"] = edited
            st.rerun()
        st.caption("Edit the name above to search again.")
        return int(selected_id), str(selected_name)

    widget_key = f"{state_key}_q_{version}"
    if widget_key not in st.session_state:
        st.session_state[widget_key] = ""

    st_keyup(
        label,
        key=widget_key,
        placeholder="Type a name, then click a match…",
        debounce=200,
    )
    query_val = (st.session_state.get(widget_key) or "").strip()

    matches = top_player_matches(search_base, query_val, limit=5)
    if query_val and not matches.empty:
        st.markdown('<div class="suggest-box">', unsafe_allow_html=True)
        for row in matches.itertuples(index=False):
            pid = int(row.player_id)
            name = str(row.player_name)
            team = getattr(row, "team_name", None)
            btn_label = f"{name} · {team}" if team else name

            def _select(pid=pid, name=name, id_key=id_key, name_key=name_key, ver_key=ver_key, version=version):
                st.session_state[id_key] = pid
                st.session_state[name_key] = name
                st.session_state[ver_key] = version + 1

            st.button(
                btn_label,
                key=f"{state_key}_btn_{version}_{pid}",
                on_click=_select,
                width="stretch",
            )
        st.markdown("</div>", unsafe_allow_html=True)
    elif query_val:
        st.caption("No matching players.")
    else:
        st.caption("Matches appear as you type — click one to select.")

    return None, None


def render_filter_bar(
    df,
    *,
    mode: str = "profile",
    applied_key: str = "applied_filters",
) -> dict | None:
    """
    Horizontal filter bar with Apply.
    mode: profile | overview | compare
    Returns applied filters dict, or None if not yet applied.
    """
    if applied_key not in st.session_state:
        st.session_state[applied_key] = default_filters(df)

    applied = st.session_state[applied_key]
    leagues_all = sorted(df["league_name"].dropna().unique().tolist())
    seasons_all = sorted(df["season"].dropna().unique().tolist())
    positions_all = sorted(p for p in df["position"].dropna().unique().tolist() if p != "Goalkeeper")
    ages = df["age"].dropna()
    age_lo = int(ages.min()) if not ages.empty else 16
    age_hi = int(ages.max()) if not ages.empty else 40

    if f"{applied_key}_age" not in st.session_state:
        st.session_state[f"{applied_key}_age"] = tuple(applied.get("age_range", (age_lo, age_hi)))

    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    st.markdown("##### Filters")

    c1, c2, c3, c4 = st.columns([1.2, 1.1, 1.0, 1.3], gap="medium")
    with c1:
        draft_leagues = st.multiselect(
            "League",
            leagues_all,
            default=applied.get("leagues") or leagues_all,
            key=f"{applied_key}_leagues",
        )
    with c2:
        season_labels = [format_season(s) for s in seasons_all]
        label_to_season = {format_season(s): int(s) for s in seasons_all}
        default_years = applied.get("seasons") or (seasons_all[-1:] if seasons_all else [])
        default_labels = [format_season(s) for s in default_years if format_season(s) in label_to_season]
        draft_season_labels = st.multiselect(
            "Season",
            season_labels,
            default=default_labels,
            key=f"{applied_key}_season_labels",
            help="API season year = season start (e.g. 2022/2023).",
        )
        draft_seasons = [label_to_season[label] for label in draft_season_labels]
    with c3:
        pos_default = applied.get("position") if applied.get("position") in positions_all else positions_all[0]
        draft_position = st.selectbox(
            "Position",
            positions_all,
            index=positions_all.index(pos_default),
            key=f"{applied_key}_position",
        )
    with c4:
        draft_age = st.slider(
            "Age range",
            min_value=age_lo,
            max_value=age_hi,
            key=f"{applied_key}_age",
        )

    team_pool = filter_frame(
        df,
        leagues=draft_leagues or None,
        seasons=draft_seasons or None,
        positions=[draft_position],
        age_min=draft_age[0],
        age_max=draft_age[1],
    )
    teams_all = sorted(team_pool["team_name"].dropna().unique().tolist())
    kept_teams = [t for t in (applied.get("teams") or []) if t in teams_all]

    if mode == "overview":
        t1, t2 = st.columns([2.5, 0.8], gap="medium")
        with t1:
            draft_teams = st.multiselect(
                "Team",
                teams_all,
                default=kept_teams,
                key=f"{applied_key}_teams",
            )
            player_id = player_name = None
            compare_id = compare_name = None
        with t2:
            st.write("")
            st.write("")
            apply_clicked = st.button("Apply filters", type="primary", width="stretch", key=f"{applied_key}_apply")
    elif mode == "compare":
        t1, t2, t3, t4 = st.columns([1.1, 1.3, 1.3, 0.7], gap="medium")
        with t1:
            draft_teams = st.multiselect(
                "Team",
                teams_all,
                default=kept_teams,
                key=f"{applied_key}_teams",
            )
        search_base = filter_frame(
            df,
            leagues=draft_leagues or None,
            seasons=draft_seasons or None,
            teams=draft_teams or None,
            positions=[draft_position],
            age_min=draft_age[0],
            age_max=draft_age[1],
        )
        with t2:
            player_id, player_name = _player_suggest_list(search_base, "", f"{applied_key}_p1", "Player A")
        with t3:
            player_id_b, player_name_b = _player_suggest_list(search_base, "", f"{applied_key}_p2", "Player B")
            compare_id, compare_name = player_id_b, player_name_b
        with t4:
            st.write("")
            st.write("")
            apply_clicked = st.button("Apply filters", type="primary", width="stretch", key=f"{applied_key}_apply")
    else:
        # profile
        t1, t2, t3 = st.columns([1.2, 1.8, 0.8], gap="medium")
        with t1:
            draft_teams = st.multiselect(
                "Team",
                teams_all,
                default=kept_teams,
                key=f"{applied_key}_teams",
            )
        search_base = filter_frame(
            df,
            leagues=draft_leagues or None,
            seasons=draft_seasons or None,
            teams=draft_teams or None,
            positions=[draft_position],
            age_min=draft_age[0],
            age_max=draft_age[1],
        )
        with t2:
            player_id, player_name = _player_suggest_list(search_base, "", f"{applied_key}_p1", "Search player")
            compare_id = compare_name = None
        with t3:
            st.write("")
            st.write("")
            apply_clicked = st.button("Apply filters", type="primary", width="stretch", key=f"{applied_key}_apply")

    st.markdown("</div>", unsafe_allow_html=True)

    if apply_clicked:
        if mode == "profile" and not player_id:
            st.warning("Pick a player from the suggestions, then Apply.")
            return None
        if mode == "compare" and (not player_id or not compare_id):
            st.warning("Pick Player A and Player B from the suggestions, then Apply.")
            return None
        if mode == "compare" and player_id == compare_id:
            st.warning("Choose two different players.")
            return None

        st.session_state[applied_key] = {
            "leagues": draft_leagues,
            "seasons": draft_seasons,
            "position": draft_position,
            "teams": draft_teams,
            "age_range": draft_age,
            "player_id": player_id,
            "player_name": player_name,
            "compare_player_id": compare_id,
            "compare_player_name": compare_name,
            "scatter_view_id": applied.get("scatter_view_id"),
        }
        st.rerun()

    applied = st.session_state[applied_key]
    if mode == "overview":
        return applied
    if mode == "profile" and applied.get("player_id"):
        return applied
    if mode == "compare" and applied.get("player_id") and applied.get("compare_player_id"):
        return applied
    return None
