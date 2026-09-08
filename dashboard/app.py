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
pg.run()
