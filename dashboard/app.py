"""Soccer Analytics dashboard entrypoint.

Run from the project root:

    streamlit run dashboard/app.py
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Soccer Analytics",
    page_icon=":soccer:",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = Path(__file__).resolve().parent / "pages"

top = st.Page(PAGES / "1_Top_Players.py", title="Top Players", default=True)
profile = st.Page(PAGES / "2_Player_Profile.py", title="Player Profile")
compare = st.Page(PAGES / "3_Compare.py", title="Compare")

pg = st.navigation([top, profile, compare])
link_player = st.query_params.get("player_id")
link_season = st.query_params.get("season")
link_league = tuple(st.query_params.get_all("league"))
link_key = (link_player, link_season, link_league)
if link_player is not None and st.session_state.get("profile_link_seen") != link_key:
    st.session_state["profile_link_seen"] = link_key
    st.session_state["profile_link_pending"] = link_key
    if pg != profile:
        st.switch_page(profile)
pg.run()
