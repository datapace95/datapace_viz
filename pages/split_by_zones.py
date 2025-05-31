import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import sys
scripts_path = 'scripts/'
sys.path.insert(1, scripts_path)
from bigquery_to_df import bigquery_to_df

st.set_page_config(layout="wide")

st.title("Check du temps passé par zone d'intensité")
st.write("Il est conseillé de passer entre 75% et 85% du temps d'entrainement en zone 1 + zone 2 (endurance fondamentale), pour développer la capacité aérobie (et réduire le risque de blessure).")

if 'df_activity_zone' not in st.session_state :
    sql_activity_zone = f"""
                            SELECT 
                            p_activity_id,
                            start_date_local,
                            monday_date_of_week,
                            zone_num,
                            nb_rows,
                            time_sec
                            FROM `datapace-190495.tables.activity_zone_stats`
                            WHERE zone_num IS NOT NULL
                            AND EXTRACT(YEAR FROM start_date_local) >= 2024
                            ORDER BY start_date_local DESC, p_activity_id, zone_num
                        """
        
    df_activity_zone = bigquery_to_df(sql_activity_zone)
    df_activity_zone['monday_date_of_week'] = pd.to_datetime(df_activity_zone['monday_date_of_week']).dt.date
    df_activity_zone['start_date_local'] = pd.to_datetime(df_activity_zone['start_date_local']).dt.date

    st.session_state['df_activity_zone'] = df_activity_zone
else :
    df_activity_zone = st.session_state['df_activity_zone']


c1, c2 = st.columns([1,2])

with c1 :

    # ==================================================
    # FILTRES ==========================================
    # ==================================================
    with st.container(border=True) :
        st.subheader("Filtres")

        # Sélection du curseur de date
        min_date = df_activity_zone['start_date_local'].min()
        max_date = df_activity_zone['start_date_local'].max()

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
        df_activity_zone_filtered = df_activity_zone[
            (df_activity_zone['start_date_local'] >= start_date) & 
            (df_activity_zone['start_date_local'] <= end_date)
            ]
        
        t_tot = df_activity_zone_filtered['time_sec'].sum() / 3600
        nb_semaines = df_activity_zone_filtered['monday_date_of_week'].nunique()
        nb_activites = df_activity_zone_filtered['p_activity_id'].nunique()
        st.write(f"Temps total affiché (h) : {t_tot:.2f}")
        st.write(f"temps moyen par semaine (h) : {(t_tot / nb_semaines):.2f}")
        st.write(f"Nb activités : {nb_activites}")

with c2 :
    # ==================================================
    # TABLEAU PAR ZONE =================================
    # ==================================================
    df_zone = (
        df_activity_zone_filtered.groupby("zone_num", as_index=False)
        .agg(total_time_sec=("time_sec", "sum"))
        .sort_values("zone_num")
        )

    df_zone["total_time_hr"] = df_zone["total_time_sec"] / 3600
    df_zone["%"] = 100 * df_zone["total_time_sec"] / df_zone["total_time_sec"].sum()
    df_zone["%_cumul"] = df_zone["%"].cumsum()

    with st.container(border=True) :
        st.subheader("Répartition par zone d'intensité")
        st.dataframe(df_zone[["zone_num", "total_time_hr", "%", "%_cumul"]].style.format({
                        "total_time_hr": "{:.2f}",
                        "%": "{:.1f}%",
                        "%_cumul": "{:.1f}%"
                        }),
                    column_config={
                        'zone_num' : 'zone',
                        'total_time_hr' : 'temps (h)',
                        '%_cumul' : '% cumul'
                    },
                    hide_index=True
            )


# ==================================================
# GRAPHE PAR SEMAINE ===============================
# ==================================================
with st.container(border=True) :
    st.subheader("Répartition du temps passé en Endurance Fondamentale (zone 1 + zone 2), et temps total par semaine")

    if df_activity_zone.empty:
        st.warning("Pas de donnée disponible.")
    else:
        # Agrégation par semaine
        df_agg = df_activity_zone_filtered.groupby('monday_date_of_week').apply(
            lambda x: pd.Series({
                'ratio_time_zone_ef': x.loc[x['zone_num'] <= 2, 'time_sec'].sum() / x['time_sec'].sum(),
                'tot_time_hour': x['time_sec'].sum() / 3600
            })
        ).reset_index()

        # Nettoyage / mise en forme
        df_agg['tot_time_hour'] = df_agg['tot_time_hour'].round(1)
        df_agg['ratio_time_zone_ef'] = df_agg['ratio_time_zone_ef'].round(2)
        df_agg['objectif_min'] = 0.75
        df_agg['objectif_max'] = 0.85

        # Création du graphique
        fig = go.Figure()

        # Ratio temps en EF (zones 1 + 2)
        fig.add_trace(
            go.Scatter(
                x=df_agg['monday_date_of_week'],
                y=df_agg['ratio_time_zone_ef'],
                mode='lines+markers',
                name='% temps passé en endurance fondamentale (zone 1 + zone 2)',
                line=dict(color='#1f77b4', width=2)
            )
        )

        # Objectif min
        fig.add_trace(
            go.Scatter(
                x=df_agg['monday_date_of_week'],
                y=df_agg['objectif_min'],
                mode='lines',
                name='objectif min',
                line=dict(color='#1f77b4', width=1, dash="dash")
            )
        )

        # Objectif max
        fig.add_trace(
            go.Scatter(
                x=df_agg['monday_date_of_week'],
                y=df_agg['objectif_max'],
                mode='lines',
                name='objectif max',
                line=dict(color='#1f77b4', width=1, dash="dash")
            )
        )

        # Temps total hebdo (axe secondaire)
        fig.add_trace(
            go.Scatter(
                x=df_agg['monday_date_of_week'],
                y=df_agg['tot_time_hour'],
                mode='lines+markers',
                name='temps total (heure)',
                line=dict(color="green", width=2, dash="dot"),
                yaxis="y2"
            )
        )

        # Layout
        fig.update_layout(
            xaxis=dict(
                title='Semaine (date premier jour semaine)',
                tickangle=45,
                tickformat="%Y-%m-%d"
            ),
            yaxis=dict(
                title='% temps passé en EF',
                titlefont=dict(color="#1f77b4"),
                tickformat=".0%",
            ),
            yaxis2=dict(
                title='Temps total (h)',
                titlefont=dict(color="green"),
                overlaying='y',
                side='right'
            ),
            legend=dict(x=0.5, y=1.1, orientation="h", xanchor="center"),
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=40, b=40),
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)
