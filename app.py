import streamlit as st


pages = {
    "": [
        st.Page("pages/home.py", title="Homepage", icon="🏠", default=True),
        st.Page("pages/split_by_zones.py", title="Suivi temps par zone", icon="⏱️"),
        st.Page("pages/heartrate_watts_ratio.py", title="Evolution ratio watts/fc", icon="⚡")
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()