import streamlit as st


pages = {
    "": [
        st.Page("pages/home.py", title="Homepage", icon="🏠", default=True),
        st.Page("pages/split_by_zones.py", title="Check temps par zone", icon="🤖"),
        st.Page("pages/heartrate_watts_ratio.py", title="Evolution ratio watts/fc", icon="💼"),
        # st.Page("studies.py", title="Etudes", icon="🎓"),
        # st.Page("skills.py", title="Compétences", icon="🔧"),
        # st.Page("hobbies.py", title="Hobbies", icon="🚴"),
        # st.Page("perso_project.py", title="Projet perso", icon="🧑🏽"),
        # st.Page("why_streamlit.py", title="Pourquoi ce CV sur Streamlit ?", icon="❓")
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()