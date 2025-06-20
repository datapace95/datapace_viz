import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

import sys
scripts_path = 'scripts/'
sys.path.insert(1, scripts_path)
from bigquery_to_df import bigquery_to_df

st.set_page_config(layout="wide")

st.title("Evolution du ratio puissance vs fréquence cadriaque")
with st.expander("détails sur le suivi") :
    st.write("Permet de suivre l'évolution de l'économie : pour une même fréquence cardiaque, on regarde si la puissance (mesurée en watts) augmente au cours du temps.")
    st.write("Critères des séances d'entrainements retenues pour ce suivi :")
    st.write("- séances sur home trainer avec comme titre 'HT EF' : permet d'enlever le bruit dû aux arrêts, environnements extérieurs, etc")
    st.write("- le titre 'HT EF' est saisi à la mano dans Strava, pour des séances d'endurance fondamentale, essentielement passée en zone 2 (donc pas d'intensité)")
    st.write("- séances durant à minima 45min")
    st.write("La mesure est ensuite effectuée entre la 10eme et la 45eme minute de la séance.")

if 'df_ratio' not in st.session_state :
    sql_ratio = f"""
                            SELECT
                            p_activity_id,
                            start_date_local,
                            start_date_local start_date_local_raw,
                            heartrate_avg,
                            watts_avg,
                            ROUND(watts_heartrate_ratio, 2) watts_heartrate_ratio
                            FROM `datapace-190495.tables.watts_heartrate_ratio_evol`
                            WHERE EXTRACT(YEAR FROM start_date_local) >= 2024
                            ORDER BY start_date_local
                        """
        
    df_ratio = bigquery_to_df(sql_ratio)

    st.session_state['df_ratio'] = df_ratio
else :
    df_ratio = st.session_state['df_ratio']

df_ratio['start_date_local'] = pd.to_datetime(df_ratio['start_date_local']).dt.date
df_ratio = df_ratio.sort_values("start_date_local")

# ==================================================
# FILTRES ==========================================
# ==================================================
with st.container(border=True) :
    st.subheader("Filtres")

    # Sélection du curseur de date
    min_date = df_ratio['start_date_local'].min()
    max_date = df_ratio['start_date_local'].max()

    # start_date, end_date = st.slider(
    #     "Sélectionner la plage de dates", 
    #     min_value=min_date, 
    #     max_value=max_date, 
    #     value=(min_date, max_date),
    #     format="YYYY-MM-DD",
    # )

    start_date = st.date_input("📅 date début", value=None, format="DD/MM/YYYY")
    if start_date is None :
        start_date = min_date
    end_date = st.date_input("📅 date fin", value=None, format="DD/MM/YYYY")
    if end_date is None :
        end_date = max_date

    # Filtrer le DataFrame selon la plage de dates
    df_ratio_filtered = df_ratio[
        (df_ratio['start_date_local'] >= start_date) & 
        (df_ratio['start_date_local'] <= end_date)
        ]
    
    # t_tot = df_ratio_filtered['time_sec'].sum() / 3600
    # nb_semaines = df_ratio_filtered['monday_date_of_week'].nunique()
    # nb_activites = df_ratio_filtered['p_activity_id'].nunique()
    # st.write(f"Temps total affiché (h) : {t_tot:.2f}")
    # st.write(f"temps moyen par semaine (h) : {(t_tot / nb_semaines):.2f}")
    # st.write(f"Nb activités : {nb_activites}")

with st.container(border=True) :
    if df_ratio_filtered.empty:
        st.warning("Aucune donnée disponible.")
    else:
        # Régression linéaire pour la courbe de tendance
        x_num = (df_ratio_filtered['start_date_local_raw'] - df_ratio_filtered['start_date_local_raw'].min()).dt.days.values
        y = df_ratio_filtered['watts_heartrate_ratio'].values

        coef = np.polyfit(x_num, y, 1)
        slope, intercept = coef
        trend = slope * x_num + intercept

        # Equation à afficher
        equation = f"y = {slope:.4f}x + {intercept:.2f}"

        # Graphique
        fig = go.Figure()

        # Courbe réelle avec markers
        fig.add_trace(go.Scatter(
            x=df_ratio_filtered['start_date_local'],
            y=df_ratio_filtered['watts_heartrate_ratio'],
            mode='lines+markers',
            name='Ratio (watts / bpm)',
            line=dict(color='blue'),
            marker=dict(size=6)
        ))

        # Courbe de tendance
        fig.add_trace(go.Scatter(
            x=df_ratio_filtered['start_date_local'],
            y=trend,
            mode='lines',
            name='Tendance linéaire',
            line=dict(color='orange', dash='dash')
        ))

        # Ajouter l'équation en annotation
        fig.add_annotation(
            x=df_ratio_filtered['start_date_local'].iloc[-1],
            y=trend[-1],
            text=equation,
            showarrow=False,
            font=dict(color='orange', size=12),
            xanchor="left"
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Watts / Fréquence cardiaque",
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=40, b=40),
            height=500,
            legend=dict(x=0.5, y=1.1, orientation="h", xanchor="center")
        )

        st.plotly_chart(fig, use_container_width=True)

with st.container(border=True):
    st.subheader("Estimation de la puissance à une date donnée (avec l'équation de la tendance)")

    if df_ratio_filtered.empty:
        st.info("Sélectionne une période contenant des données pour effectuer une estimation.")
    else:
        # Date cible pour l'estimation
        target_date = st.date_input("📅 Date cible pour l'estimation", value=max_date, format="DD/MM/YYYY")

        # Calcul du nombre de jours entre la date min et la date cible
        df_ratio_filtered['start_date_local_raw'] = pd.to_datetime(df_ratio['start_date_local_raw']).dt.tz_localize(None)
        x_target = (pd.to_datetime(target_date) - df_ratio_filtered['start_date_local_raw'].min()).days

        # Estimation du ratio (watts/bpm) à la date cible
        estimated_ratio = slope * x_target + intercept

        # Moyenne de la FC sur la période filtrée
        hr_avg = df_ratio_filtered['heartrate_avg'].mean()

        # Estimation de la puissance
        estimated_power = estimated_ratio * hr_avg

        st.markdown(f"**Ratio estimé (watts/bpm) avec l'équation :** {estimated_ratio:.2f}")
        st.markdown(f"**Fréquence cardiaque utilisée (moyenne période sélectionnée) :** {hr_avg:.0f} bpm")
        st.markdown(f"### ⚡ Puissance estimée (pour la FC ci-dessus): **{estimated_power:.0f} watts**")