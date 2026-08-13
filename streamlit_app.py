"""
App Streamlit — Scouting de Guarda-Redes
------------------------------------------
Interface interativa sobre o mesmo pipeline: escolhe um guarda-redes,
vê o perfil dele, compara com outro, ou pede "encontra-me um parecido".

Corre com:
    streamlit run streamlit_app.py
"""

import pandas as pd
import streamlit as st

from data_loader import build_gk_events, build_gk_passes
from metrics import build_scouting_table
from visuals import plot_radar, plot_sweeper_map
from similarity_engine import find_similar_goalkeepers, explain_similarity

st.set_page_config(page_title="Scouting de Guarda-Redes", page_icon="🧤", layout="wide")


@st.cache_data
def load_data():
    events = pd.read_pickle("data/events_full_wc2022.pkl")
    gk_events = build_gk_events(events)
    gk_passes = build_gk_passes(events)
    table = build_scouting_table(events, gk_events, gk_passes)
    table = table[table["minutes"] >= 180]  # amostra mínima para robustez
    return events, gk_events, gk_passes, table


st.title("🧤 Algoritmo de Perfilagem de Guarda-Redes")
st.caption("Dados: StatsBomb Open Data · Mundial 2022 · 34 guarda-redes com ≥180 min jogados")

events, gk_events, gk_passes, table = load_data()

tab1, tab2, tab3 = st.tabs(["📊 Perfil individual", "⚖️ Comparar", "🔎 Encontrar parecidos"])

with tab1:
    player = st.selectbox("Escolhe um guarda-redes", table.index.sort_values())
    row = table.loc[player]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Minutos jogados", f"{row['minutes']:.0f}")
    c2.metric("Eficácia de defesas", f"{row['save_pct']:.1f}%")
    c3.metric("Ações Sweeper /90", f"{row['sweeper_actions_p90']:.2f}")
    c4.metric("Eficácia de passe", f"{row['pass_success_pct']:.1f}%")

    st.subheader("Mapa de saídas da baliza (Sweeper-Keeper)")
    fig_path = f"output/_tmp_sweeper_{player.replace(' ', '_')}.png"
    plot_sweeper_map(gk_events, player, fig_path)
    st.image(fig_path)

with tab2:
    col1, col2 = st.columns(2)
    p1 = col1.selectbox("Guarda-redes 1", table.index.sort_values(), key="p1")
    p2 = col2.selectbox("Guarda-redes 2", table.index.sort_values(), index=1, key="p2")
    p3 = st.selectbox("Guarda-redes 3 (opcional)", ["(nenhum)"] + list(table.index.sort_values()), key="p3")

    players = [p1, p2] + ([p3] if p3 != "(nenhum)" else [])
    fig_path = "output/_tmp_radar_compare.png"
    plot_radar(table, players, fig_path)
    st.image(fig_path)

with tab3:
    target = st.selectbox("Encontrar guarda-redes parecidos com...", table.index.sort_values())
    top_n = st.slider("Quantos candidatos mostrar?", 3, 10, 5)

    sim = find_similar_goalkeepers(table, target, top_n=top_n)
    st.dataframe(sim[["similarity_pct", "sweeper_actions_p90", "avg_distance_from_goal",
                       "save_pct", "pass_success_pct", "minutes"]].round(1))

    st.subheader("Leitura de scouting")
    for candidate in sim.index:
        st.write("•", explain_similarity(table, target, candidate))
