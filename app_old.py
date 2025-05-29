import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import sys
scripts_path = 'scripts/'
sys.path.insert(1, scripts_path)
from bigquery_to_df import bigquery_to_df

st.set_page_config(layout="wide")

st.title("Analyse répartition par zone d'effort")
st.write("L'entrainement en endurance fondamentale (zone 1 + zone 2) devrait représenter entre 75% et 85% du temps passé pour une progression optimale (et une réduction du risque de blessure).")
st.write("")

if 'df_weekly_stats' not in st.session_state :
    sql_weekly_stats = f"""
                            SELECT
                            monday_date_of_week
                            , ratio_time_zone_ef
                            , time_hour
                            , nb_activities
                            FROM `datapace-190495.tables.weekly_stats`
                        """
        
    df_weekly_stats = bigquery_to_df(sql_weekly_stats)
    df_weekly_stats['monday_date_of_week'] = pd.to_datetime(df_weekly_stats['monday_date_of_week']).dt.date

    st.session_state['df_weekly_stats'] = df_weekly_stats

if 'df_weekly_stats' in st.session_state :

    df_weekly_stats = st.session_state['df_weekly_stats']

    # ==================================================
    # FILTRES ==========================================
    # ==================================================
    with st.container(border=True) :
        st.subheader("Filtres")

        # Sélection du curseur de date
        min_date = df_weekly_stats['start_date_local'].min()
        max_date = df_weekly_stats['start_date_local'].max()

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
        df_filtered = df_weekly_stats[
            (df_weekly_stats['start_date_local'] >= start_date) & 
            (df_weekly_stats['start_date_local'] <= end_date)
        ]

    
    col11, col12 = st.columns([1,3])

    # ==================================================
    # Tableau repartition par zone
    # ==================================================
    with col11 :
        with st.container(border=True) :

            # 2. Afficher un tableau avec zone_num et SUM(nb_rows)
            st.subheader("Répartition par zone")


            df_summary = df_filtered.groupby('zone_num').agg({'time_sec': 'sum'}).reset_index()

            total_time_sec = df_summary['time_sec'].sum()
            hour = int(int(total_time_sec) / 3600)
            minuts = int(((total_time_sec / 3600) * 1.0 - int((total_time_sec/3600)) *1.0) * 60)
            st.write(f"temps total (heure) : {str(hour)} heures et {str(minuts)} minutes")

            df_summary['repartition (%)'] = ((df_summary['time_sec'] * 1.0) / (total_time_sec * 1.0)) * 100
            df_summary['répartition cumulée (%)'] = df_summary['repartition (%)'].cumsum()

            df_summary['repartition (%)'] = df_summary['repartition (%)'].round(0)
            df_summary['répartition cumulée (%)'] = df_summary['répartition cumulée (%)'].round(0)
            df_summary['temps (h)'] = df_summary['time_sec'] / 3600
            df_summary['temps (h)'] = df_summary['temps (h)'].round(1)
            df_summary['zone'] = df_summary['zone_num']

            df_summary = df_summary[['zone', 'temps (h)', 'repartition (%)', 'répartition cumulée (%)']]

            st.dataframe(df_summary, hide_index=True)

            show_zone = st.checkbox("afficher tes zones")
            if show_zone :
                zone_query = f"""
                    SELECT
                    data_type as type,
                    zone_num as zone,
                    min,
                    max
                    FROM `tables.STRAVA_ZONES`
                    WHERE p_athlete_id = {st.session_state['strava_api_infos']['athlete_id'][0]}
                    ORDER BY data_type, zone_num                    
                    """
                df_zones = bigquery_to_df(zone_query)
                st.dataframe(df_zones)

    # ==================================================
    # GRAPHES
    # ==================================================
    with col12 :
        with st.container(border=True) :
            st.subheader("Répartition du temps passé en EF (zone 1 + zone 2), et temps total par semaine")

            df_agg = df_filtered.groupby('monday_date_of_week').apply(
                lambda x: pd.Series({
                    'ratio_time_zone_ef': x.loc[x['zone_num'] <= 2, 'time_sec'].sum() / x['time_sec'].sum(),
                    'tot_time_hour': x['time_sec'].sum() / 3600
                })
            ).reset_index()

            df_agg['tot_time_hour'] = df_agg['tot_time_hour'].round(1)
            df_agg['ratio_time_zone_ef'] = df_agg['ratio_time_zone_ef'].round(2)
            df_agg['monday_date_of_week'] = pd.to_datetime(df_agg['monday_date_of_week'])
            df_agg['objectif_min'] = 0.75
            df_agg['objectif_max'] = 0.85

            # # Création du graphique avec Plotly Express
            # fig = px.line(
            #     df_agg,
            #     x='monday_date_of_week',
            #     y='ratio_time_sec',
            #     title='% zone 2',
            #     labels={'monday_date_of_week': 'By week', 'ratio_time_sec': '% zone 2'}
            # )

            # # Personnalisation des traces et du style
            # fig.update_traces(marker=dict(color='#1f77b4', size=6), line=dict(color='#1f77b4', width=2))

            # # Ajouter la ligne de l'objectif en tant que nouvelle série
            # fig.add_scatter(
            #     x=df_agg['monday_date_of_week'],
            #     y=df_agg['objectif_min'],
            #     mode='lines',
            #     name='Objectif min',
            #     line=dict(color="red", width=1, dash="dash")  # Style de la ligne (rouge, pointillé)
            # )
            # # Ajouter la ligne de l'objectif en tant que nouvelle série
            # fig.add_scatter(
            #     x=df_agg['monday_date_of_week'],
            #     y=df_agg['objectif_max'],
            #     mode='lines',
            #     name='Objectif max',
            #     line=dict(color="red", width=1, dash="dash")  # Style de la ligne (rouge, pointillé)
            # )

            # # Configuration des axes avec uniquement les valeurs de 'monday_date_of_week' comme ticks
            # fig.update_layout(
            #     xaxis=dict(
            #         tickvals=df_agg['monday_date_of_week'],  # Utiliser uniquement les dates présentes dans df_ragg
            #         tickformat="%Y-%m-%d",
            #         title_font=dict(size=12),
            #         tickangle=45,
            #         tickfont=dict(size=10)
            #     ),
            #     yaxis=dict(
            #         title='% zone 2',
            #         title_font=dict(size=12),
            #         tickfont=dict(size=10)
            #     ),
            #     title={'x': 0.5, 'xanchor': 'center', 'font': {'size': 16, 'color': '#333'}},
            #     plot_bgcolor='rgba(0,0,0,0)',
            #     margin=dict(l=40, r=40, t=40, b=40)
            # )

            # # Afficher le graphique dans Streamlit
            # st.plotly_chart(fig)


            fig = go.Figure()

            # Trace pour le ratio de temps en zone 2
            fig.add_trace(
                go.Scatter(
                    x=df_agg['monday_date_of_week'],
                    y=df_agg['ratio_time_zone_ef'],
                    mode='lines+markers',
                    name='% temps passé en endurance fondamentale (zone 1 + zone 2)',
                    line=dict(color='#1f77b4', width=2)
                )
            )

            # Trace pour la ligne d'objectif min
            fig.add_trace(
                go.Scatter(
                    x=df_agg['monday_date_of_week'],
                    y=df_agg['objectif_min'],
                    mode='lines',
                    name='objectif min',
                    line=dict(color='#1f77b4', width=1, dash="dash")
                )
            )

            # Trace pour la ligne d'objectif min
            fig.add_trace(
                go.Scatter(
                    x=df_agg['monday_date_of_week'],
                    y=df_agg['objectif_max'],
                    mode='lines',
                    name='objectif max',
                    line=dict(color='#1f77b4', width=1, dash="dash")
                )
            )

            # Nouvelle trace pour la somme de `time_sec`, affichée sur un axe secondaire
            fig.add_trace(
                go.Scatter(
                    x=df_agg['monday_date_of_week'],
                    y=df_agg['tot_time_hour'],
                    mode='lines+markers',
                    name='temps total (heure)',
                    line=dict(color="green", width=2, dash="dot"),
                    yaxis="y2"  # Associer cette série à l'axe secondaire
                )
            )

            # Mise en page pour ajouter l'axe secondaire
            fig.update_layout(
                title='',
                xaxis=dict(
                    tickvals=df_agg['monday_date_of_week'],
                    tickformat="%Y-%m-%d",
                    title='semaine (date du lundi)',
                    tickangle=45
                ),
                yaxis=dict(
                    title='% temps passé en EF',
                    titlefont=dict(color="#1f77b4")
                ),
                yaxis2=dict(
                    title='heure',
                    titlefont=dict(color="green"),
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.5, y=1.1, orientation="h", xanchor="center"),
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=40, r=40, t=40, b=40)
            )

            # Afficher le graphique dans Streamlit
            st.plotly_chart(fig)