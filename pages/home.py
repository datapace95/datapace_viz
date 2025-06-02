import streamlit as st
from PIL import Image

st.set_page_config(layout="wide")

st.title("DATAPACE - App de suivi d'entrainement")
st.write("Cette App a pour but de me fournir des informations d'entrainements que je ne peux pas avoir directement avec l'application Strava.")
st.write("Les différents suivis se trouvent dans les pages accessibles via le bandeau de gauche.")
st.write("")
st.subheader("Fonctionnement de l'app :")
st.write("- Les données utilisées sont celles provenant de l'API proposée par Strava")
st.write("- Elles sont récupérés par une succession de scripts Python hébergés dans un Cloud Run de GCP, qui s'occupent également de les pousser dans un Cloud Storage.")
st.write("- Ces scripts sont lancés quotidiennements par un Cloud Scheduler.")
st.write("- Les données sont ensuite requêtables via Big Query, dans lequel les data brutes sont accessibles via des EXTERNAL TABLES connectées au Cloud Storage.")
st.write("- Enfin les données finales visibles dans cette App sont transformées à partir de VIEWS modélisées via dbt.")
st.write("")
st.write("")

st.write("Ci-dessous un schema du fonctionnement :")
with st.container(border=True) :
    image = Image.open("pages/stack_schema.png")
    st.image(image)


st.write("lien vers le repo git de l'app : https://github.com/datapace95/datapace_viz")
st.write("lien vers le repo git de l'api comprenant les pipelines de donnnées : https://github.com/datapace95/datapace_viz")