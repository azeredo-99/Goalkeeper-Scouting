"""
Goalkeeper Scouting — Frontend
--------------------------------

A lógica de dados/performance é mantida; em desenvolvimento:
- navegação;
- pesquisa;
- cards;
- hierarquia visual;
- comparação;
- semelhantes;
- responsividade;
- legibilidade.
"""

import html
import os
import unicodedata

import pandas as pd
import streamlit as st

import _bootstrap  # noqa: F401  (coloca src/ no sys.path)

from gk_scouting.data_loader import build_gk_events, build_gk_passes
from gk_scouting.metrics import build_scouting_table
from gk_scouting.market_data import get_goalkeepers
from gk_scouting.player_matching import (
    create_name_index,
    match_players,
)
from gk_scouting.visuals import plot_radar, plot_sweeper_map
from gk_scouting.similarity_engine import (
    STYLE_FEATURES,
    default_min_minutes,
    find_similar_goalkeepers,
    explain_similarity,
    normalise_dimension_weights,
)


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Goalkeeper Scouting",
    page_icon="🧤",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# FRONTEND THEME
# =========================================================

st.markdown(
    """
    <style>
        :root {
            --gk-navy: #0f172a;
            --gk-blue: #2563eb;
            --gk-blue-dark: #1d4ed8;
            --gk-bg: #f8fafc;
            --gk-panel: #ffffff;
            --gk-border: #e2e8f0;
            --gk-muted: #64748b;
            --gk-text: #0f172a;
            --gk-soft: #eff6ff;
            --gk-green: #16a34a;
        }

        .stApp {
            background:
                linear-gradient(
                    180deg,
                    #f8fafc 0%,
                    #ffffff 260px
                );
        }

        .block-container {
            max-width: 1500px;
            padding-top: 1.4rem;
            padding-bottom: 4rem;
        }

        /* Top navigation */
        div[data-testid="stRadio"] > div {
            gap: 0.45rem;
        }

        div[data-testid="stRadio"] label {
            background: #ffffff;
            border: 1px solid var(--gk-border);
            border-radius: 10px;
            padding: 0.45rem 0.85rem;
            transition: all 0.15s ease;
        }

        div[data-testid="stRadio"] label:hover {
            border-color: #bfdbfe;
            background: #f8fbff;
        }

        /* Native metrics */
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--gk-border);
            border-radius: 12px;
            padding: 0.9rem 1rem;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--gk-muted);
        }

        /* Input fields */
        div[data-baseweb="input"] > div {
            border-radius: 10px;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 9px;
            font-weight: 600;
        }

        /* Dataframe */
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--gk-border);
            border-radius: 12px;
            overflow: hidden;
        }

        /* Cards */
        .gk-hero {
            background: linear-gradient(
                135deg,
                #0f172a 0%,
                #1e293b 100%
            );
            color: #ffffff;
            border-radius: 18px;
            padding: 1.5rem 1.6rem;
            margin: 0.5rem 0 1rem 0;
            box-shadow:
                0 12px 30px rgba(15, 23, 42, 0.14);
        }

        .gk-hero-title {
            font-size: 1.7rem;
            font-weight: 800;
            line-height: 1.1;
            margin-bottom: 0.35rem;
        }

        .gk-hero-subtitle {
            color: #cbd5e1;
            font-size: 0.95rem;
        }

        .gk-section-title {
            font-size: 1.15rem;
            font-weight: 750;
            color: var(--gk-text);
            margin: 0.4rem 0 0.6rem 0;
        }

        .gk-section-note {
            color: var(--gk-muted);
            font-size: 0.88rem;
            margin-bottom: 0.9rem;
        }

        .gk-result {
            background: #ffffff;
            border: 1px solid var(--gk-border);
            border-radius: 11px;
            padding: 0.7rem 0.9rem;
            margin: 0.35rem 0;
        }

        .gk-result-name {
            font-weight: 700;
            color: var(--gk-text);
        }

        .gk-result-meta {
            color: var(--gk-muted);
            font-size: 0.82rem;
        }

        .gk-kpi-label {
            color: var(--gk-muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .gk-kpi-value {
            color: var(--gk-text);
            font-size: 1.45rem;
            font-weight: 800;
            margin-top: 0.15rem;
        }

        .gk-badge {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            background: var(--gk-soft);
            color: var(--gk-blue-dark);
            font-size: 0.75rem;
            font-weight: 700;
        }

        /* Reduce excessive vertical whitespace */
        hr {
            border-color: var(--gk-border);
            margin: 1rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def normalize_search_text(text):
    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        str(text).lower().strip(),
    )

    return "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )


def esc(value):
    """
    Escapa um valor antes de o interpolar em HTML.

    Nomes de jogadores e de clubes vem de um CSV externo que nao
    controlamos; sem escaping, qualquer marcacao nesses campos seria
    executada no browser (o Streamlit nao escapa dentro de
    `unsafe_allow_html=True`).
    """

    if value is None or pd.isna(value):
        return "N/A"

    return html.escape(str(value))


def format_market_value(value):
    if pd.isna(value):
        return "N/A"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "N/A"

    if value >= 1_000_000:
        millions = value / 1_000_000
        if millions >= 10:
            return f"€{millions:.0f}M"
        return f"€{millions:.1f}M"

    if value >= 1_000:
        return f"€{value / 1_000:.0f}K"

    return f"€{value:.0f}"


def calculate_age(date_of_birth):
    if pd.isna(date_of_birth):
        return None

    try:
        dob = pd.to_datetime(date_of_birth)
        today = pd.Timestamp.today()

        return (
            today.year
            - dob.year
            - (
                (today.month, today.day)
                < (dob.month, dob.day)
            )
        )
    except Exception:
        return None


def prepare_market_df(df):
    df = df.copy()

    if "normalized_name" not in df.columns:
        df["normalized_name"] = (
            df["name"]
            .fillna("")
            .map(normalize_search_text)
        )

    if "market_value_in_eur" in df.columns:
        df["market_value_in_eur"] = pd.to_numeric(
            df["market_value_in_eur"],
            errors="coerce",
        )

    return df


def search_market_players(
    market_df,
    query,
    limit=20,
):
    if market_df.empty:
        return market_df

    query = normalize_search_text(query)

    if not query:
        return market_df.head(0)

    starts = market_df[
        market_df["normalized_name"]
        .str.startswith(
            query,
            na=False,
        )
    ]

    contains = market_df[
        market_df["normalized_name"]
        .str.contains(
            query,
            regex=False,
            na=False,
        )
        &
        ~market_df["normalized_name"]
        .str.startswith(
            query,
            na=False,
        )
    ]

    starts = starts.sort_values(
        "market_value_in_eur",
        ascending=False,
        na_position="last",
    )

    contains = contains.sort_values(
        "market_value_in_eur",
        ascending=False,
        na_position="last",
    )

    return pd.concat(
        [starts, contains],
        ignore_index=True,
    ).head(limit)


def market_label(player):
    name = player.get(
        "name",
        "Nome desconhecido",
    )

    club = player.get(
        "current_club_name",
        "Clube desconhecido",
    )

    if pd.isna(club):
        club = "Clube desconhecido"

    value = format_market_value(
        player.get(
            "market_value_in_eur",
            None,
        )
    )

    return f"{name} · {club} · {value}"


def get_market_player(
    player_name,
    market_df,
):
    if not player_name or market_df.empty:
        return None

    normalized = normalize_search_text(
        player_name
    )

    matches = market_df[
        market_df["normalized_name"]
        == normalized
    ]

    if matches.empty:
        return None

    return matches.iloc[0]


def render_section_title(
    title,
    note=None,
):
    st.markdown(
        f"<div class='gk-section-title'>{title}</div>",
        unsafe_allow_html=True,
    )

    if note:
        st.markdown(
            f"<div class='gk-section-note'>{note}</div>",
            unsafe_allow_html=True,
        )


def render_player_card(
    player,
    market,
    performance=None,
):
    name = (
        performance
        if performance
        else market.get("name", "N/A")
    )

    club = market.get(
        "current_club_name",
        "N/A",
    )

    if pd.isna(club):
        club = "N/A"

    value = format_market_value(
        market.get(
            "market_value_in_eur"
        )
    )

    age = calculate_age(
        market.get(
            "date_of_birth"
        )
    )

    left, middle, right = st.columns(
        [2.2, 1.8, 1]
    )

    with left:
        st.markdown(
            f"<div class='gk-result-name'>🧤 {esc(name)}</div>"
            f"<div class='gk-result-meta'>🏟️ {esc(club)}</div>",
            unsafe_allow_html=True,
        )

    with middle:
        st.markdown(
            f"<div class='gk-kpi-label'>Valor de mercado</div>"
            f"<div class='gk-kpi-value'>{esc(value)}</div>",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            f"<div class='gk-kpi-label'>Idade</div>"
            f"<div class='gk-kpi-value'>"
            f"{esc(age)}"
            f"</div>",
            unsafe_allow_html=True,
        )


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data(show_spinner="A carregar dados de performance...")
def load_data():
    """
    Constroi a tabela de scouting e a base de mercado.

    Os eventos brutos (centenas de MB) sao apenas um passo intermedio:
    servem para construir `table` e nao voltam a ser usados pela aplicacao.
    Por isso NAO sao devolvidos nem mantidos em cache -- se o fossem,
    ficariam retidos em memoria durante todo o ciclo de vida do processo.
    """

    extended_path = "data/events_extended.pkl"
    fallback_path = "data/events_full_wc2022.pkl"

    if os.path.exists(extended_path):
        events_path = extended_path
    elif os.path.exists(fallback_path):
        events_path = fallback_path
    else:
        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )

    events = pd.read_pickle(
        events_path
    )

    gk_events = build_gk_events(events)
    gk_passes = build_gk_passes(events)

    table = build_scouting_table(
        events,
        gk_events,
        gk_passes,
    )

    # Libertar explicitamente os eventos brutos assim que a tabela esta
    # construida: nada na aplicacao os consome a partir daqui.
    del events, gk_events, gk_passes

    if "minutes" in table.columns:
        table = table[
            table["minutes"] >= 180
        ].copy()

    market_df = get_goalkeepers()
    market_df = create_name_index(market_df)
    market_df = prepare_market_df(market_df)

    return (
        table,
        market_df,
    )


(
    table,
    market_df,
) = load_data()


if market_df.empty:
    st.error(
        "Não foi possível carregar a base de mercado."
    )
    st.stop()


# Limiar de minutos sugerido, derivado da amostra realmente carregada.
# Um valor fixo nao serve: o percentil 25 e 286 minutos no Mundial 2022 e
# 190 no dataset multi-competicao.
suggested_min_minutes = default_min_minutes(
    table["minutes"]
    if "minutes" in table.columns
    else []
)


# =========================================================
# MATCH MAP
# =========================================================

@st.cache_data(show_spinner=False)
def build_performance_market_map(
    performance_names,
    _market_df,
):
    """
    `_market_df` leva prefixo `_` de proposito: sinaliza ao Streamlit que
    nao deve tentar gerar hash do DataFrame a cada rerun. E derivado de
    forma deterministica de `load_data()`, por isso `performance_names`
    e suficiente como chave de cache.
    """

    market_df = _market_df

    names = list(performance_names)

    if not names or market_df.empty:
        return {}

    matches = match_players(
        names,
        market_df,
    )

    market_lookup = {
        row["normalized_name"]: row
        for _, row in market_df.iterrows()
    }

    mapping = {}

    for _, row in matches.iterrows():

        statsbomb_name = row.get(
            "statsbomb_name"
        )

        transfermarkt_name = row.get(
            "transfermarkt_name"
        )

        if (
            not statsbomb_name
            or pd.isna(
                transfermarkt_name
            )
        ):
            continue

        normalized = normalize_search_text(
            transfermarkt_name
        )

        market_row = market_lookup.get(
            normalized
        )

        if market_row is not None:
            mapping[
                statsbomb_name
            ] = market_row

    return mapping


performance_market_map = (
    build_performance_market_map(
        tuple(table.index.tolist()),
        market_df,
    )
)


def market_for_performance(
    performance_name,
):
    return performance_market_map.get(
        performance_name
    )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="gk-hero">
        <div class="gk-hero-title">🧤 Goalkeeper Scouting</div>
        <div class="gk-hero-subtitle">
            Performance, mercado e análise de perfil de guarda-redes
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# NAVIGATION
# =========================================================

page = st.radio(
    "Área",
    [
        "👤 Perfil",
        "⚖️ Comparar",
        "🔎 Encontrar semelhantes",
    ],
    horizontal=True,
    label_visibility="collapsed",
    key="main_page",
)

st.divider()


# =========================================================
# PROFILE / GLOBAL SEARCH
# =========================================================

selected_market_player = None
selected_performance_player = None

if page in (
    "👤 Perfil",
    "⚖️ Comparar",
):

    render_section_title(
        "🔎 Procurar guarda-redes",
        "Escreve pelo menos parte do nome para procurar no mercado.",
    )

    search_query = st.text_input(
        "Pesquisar guarda-redes",
        placeholder=(
            "Ex.: Courtois, Diogo Costa, Donnarumma..."
        ),
        label_visibility="collapsed",
        key="global_search",
    )

    search_results = search_market_players(
        market_df,
        search_query,
        limit=12,
    )

    if not search_query.strip():

        st.info(
            "Pesquisa um guarda-redes para começar."
        )

    elif search_results.empty:

        st.warning(
            "Nenhum guarda-redes encontrado."
        )

    else:

        st.caption(
            f"{len(search_results)} resultado(s)"
        )

        options = [
            (
                market_label(player),
                player["name"],
            )
            for _, player
            in search_results.iterrows()
        ]

        selected_label = st.radio(
            "Resultados",
            [item[0] for item in options],
            horizontal=True,
            label_visibility="collapsed",
            key="global_player",
        )

        selected_market_name = dict(
            options
        ).get(
            selected_label
        )

        selected_market_player = (
            get_market_player(
                selected_market_name,
                market_df,
            )
        )

        if selected_market_name:

            normalized_selected = (
                normalize_search_text(
                    selected_market_name
                )
            )

            for (
                performance_name,
                market_row,
            ) in performance_market_map.items():

                if (
                    normalize_search_text(
                        market_row.get(
                            "name",
                            "",
                        )
                    )
                    == normalized_selected
                ):

                    selected_performance_player = (
                        performance_name
                    )

                    break

    st.divider()


# =========================================================
# PROFILE
# =========================================================

if page == "👤 Perfil":

    if selected_market_player is None:

        st.info(
            "Pesquisa um guarda-redes acima para abrir o perfil."
        )

    else:

        player = selected_market_player

        name = player.get(
            "name",
            "N/A",
        )

        club = player.get(
            "current_club_name",
            "N/A",
        )

        if pd.isna(club):
            club = "N/A"

        age = calculate_age(
            player.get(
                "date_of_birth"
            )
        )

        value = format_market_value(
            player.get(
                "market_value_in_eur"
            )
        )

        highest = format_market_value(
            player.get(
                "highest_market_value_in_eur"
            )
        )

        st.markdown(
            f"""
            <div class="gk-hero">
                <div class="gk-hero-title">🧤 {esc(name)}</div>
                <div class="gk-hero-subtitle">🏟️ {esc(club)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "🎂 Idade",
            f"{age} anos"
            if age is not None
            else "N/A",
        )

        c2.metric(
            "💰 Valor de mercado",
            value,
        )

        c3.metric(
            "📈 Maior valor",
            highest,
        )

        st.divider()

        render_section_title(
            "📊 Performance",
            "Métricas disponíveis na amostra StatsBomb.",
        )

        if (
            selected_performance_player is None
            or selected_performance_player
            not in table.index
        ):

            st.info(
                "Não existem dados de performance StatsBomb "
                "suficientes para este guarda-redes."
            )

        else:

            row = table.loc[
                selected_performance_player
            ]

            c1, c2, c3, c4 = st.columns(4)

            c1.metric(
                "⏱️ Minutos",
                f"{row['minutes']:.0f}",
            )

            c2.metric(
                "🥅 Defesas",
                f"{row['save_pct']:.1f}%",
            )

            c3.metric(
                "🧤 Sweeper /90",
                f"{row['sweeper_actions_p90']:.2f}",
            )

            c4.metric(
                "⚽ Passes certos",
                f"{row['pass_success_pct']:.1f}%",
            )


# =========================================================
# COMPARE
# =========================================================

elif page == "⚖️ Comparar":

    render_section_title(
        "⚖️ Comparar guarda-redes",
        "Compara performance e contexto de mercado de dois ou três jogadores.",
    )

    performance_market_options = [
        (
            market_label(market),
            performance_name,
        )
        for performance_name, market
        in performance_market_map.items()
    ]

    performance_market_options.sort(
        key=lambda item: item[0]
    )

    labels = [
        label
        for label, _ in performance_market_options
    ]

    mapping = dict(
        performance_market_options
    )

    if len(labels) < 2:

        st.warning(
            "São necessários pelo menos dois guarda-redes "
            "com dados de performance."
        )

    else:

        col1, col2 = st.columns(2)

        with col1:
            p1_label = st.selectbox(
                "Guarda-redes 1",
                labels,
                key="compare_1",
            )

        with col2:
            p2_label = st.selectbox(
                "Guarda-redes 2",
                labels,
                index=1 if len(labels) > 1 else 0,
                key="compare_2",
            )

        p3_label = st.selectbox(
            "Guarda-redes 3 (opcional)",
            ["(nenhum)"] + labels,
            key="compare_3",
        )

        selected_players = [
            mapping[p1_label],
            mapping[p2_label],
        ]

        if p3_label != "(nenhum)":
            selected_players.append(
                mapping[p3_label]
            )

        if len(set(selected_players)) != len(
            selected_players
        ):

            st.warning(
                "Escolhe guarda-redes diferentes."
            )

        else:

            st.divider()

            render_section_title(
                "👥 Jogadores selecionados",
            )

            cards = st.columns(
                len(selected_players)
            )

            for col, performance_name in zip(
                cards,
                selected_players,
            ):

                market = market_for_performance(
                    performance_name
                )

                with col:

                    if market is not None:
                        render_player_card(
                            performance_name,
                            market,
                            performance=performance_name,
                        )
                    else:
                        st.markdown(
                            f"**🧤 {performance_name}**"
                        )

            st.divider()

            render_section_title(
                "📊 Comparação estatística"
            )

            compare_metrics = [
                ("minutes", "Minutos"),
                ("save_pct", "Defesas (%)"),
                (
                    "pass_success_pct",
                    "Passes certos (%)",
                ),
                (
                    "avg_pass_length",
                    "Passe médio (m)",
                ),
                (
                    "long_ball_pct",
                    "Bola longa (%)",
                ),
                (
                    "sweeper_actions_p90",
                    "Saídas /90",
                ),
                (
                    "avg_distance_from_goal",
                    "Distância média",
                ),
            ]

            rows = []

            for metric, label in compare_metrics:

                if metric not in table.columns:
                    continue

                row = {
                    "Métrica": label,
                }

                for player in selected_players:

                    value = table.loc[
                        player,
                        metric,
                    ]

                    row[player] = (
                        round(
                            float(value),
                            2,
                        )
                        if not pd.isna(value)
                        else "N/A"
                    )

                rows.append(row)

            st.dataframe(
                pd.DataFrame(rows),
                width="stretch",
                hide_index=True,
            )

            st.button(
                "🕸️ Gerar radar comparativo",
                type="primary",
                key="generate_radar",
                on_click=None,
            )

            if st.session_state.get(
                "generate_radar",
                False,
            ):

                with st.spinner(
                    "A gerar radar..."
                ):

                    os.makedirs(
                        "output",
                        exist_ok=True,
                    )

                    path = (
                        "output/_tmp_radar_compare.png"
                    )

                    plot_radar(
                        table,
                        selected_players,
                        path,
                    )

                    st.image(
                        path,
                        width="stretch",
                    )


# =========================================================
# SIMILAR
# =========================================================

else:

    render_section_title(
        "🔎 Encontrar semelhantes",
        "Encontra perfis estatisticamente próximos e filtra por contexto de mercado.",
    )

    similar_search = st.text_input(
        "Pesquisar guarda-redes de referência",
        placeholder=(
            "Ex.: Donnarumma, Courtois, Diogo Costa..."
        ),
        label_visibility="collapsed",
        key="similar_reference_search",
    )

    normalized_similar_search = normalize_search_text(
        similar_search
    )

    if not normalized_similar_search:

        st.info(
            "Pesquisa pelo nome do guarda-redes que queres usar como referência."
        )

    else:

        similar_candidates = []

        for performance_name, market in (
            performance_market_map.items()
        ):

            market_name = normalize_search_text(
                market.get(
                    "name",
                    performance_name,
                )
            )

            if market_name.startswith(
                normalized_similar_search
            ):

                similar_candidates.append(
                    (
                        market_label(market),
                        performance_name,
                        market,
                    )
                )

        if not similar_candidates:

            for performance_name, market in (
                performance_market_map.items()
            ):

                market_name = normalize_search_text(
                    market.get(
                        "name",
                        performance_name,
                    )
                )

                if normalized_similar_search in market_name:

                    similar_candidates.append(
                        (
                            market_label(market),
                            performance_name,
                            market,
                        )
                    )

        similar_candidates = sorted(
            similar_candidates,
            key=lambda item: (
                -float(
                    item[2].get(
                        "market_value_in_eur",
                        0,
                    )
                    or 0
                )
            ),
        )[:20]

        if not similar_candidates:

            st.warning(
                "Nenhum guarda-redes encontrado para essa pesquisa."
            )

        else:

            st.caption(
                f"{len(similar_candidates)} resultado(s)"
            )

            similar_labels = [
                item[0]
                for item in similar_candidates
            ]

            similar_map = {
                item[0]: item[1]
                for item in similar_candidates
            }

            target_label = st.radio(
                "Resultados",
                similar_labels,
                index=0,
                label_visibility="collapsed",
                key="similar_reference_result",
            )

            target = similar_map[
                target_label
            ]

            target_market = market_for_performance(
                target
            )

            if target_market is not None:

                club = target_market.get(
                    "current_club_name",
                    "N/A",
                )

                if pd.isna(club):
                    club = "N/A"

                st.markdown(
                    f"""
                    <div class="gk-result">
                        <div class="gk-result-name">
                            🎯 {esc(target)}
                        </div>
                        <div class="gk-result-meta">
                            🏟️ {esc(club)} ·
                            💰 {esc(format_market_value(target_market.get("market_value_in_eur")))} ·
                            🎂 {esc(calculate_age(target_market.get("date_of_birth")))}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.divider()

            render_section_title(
                "⚖️ Perfil de scouting",
                "Define quanto cada dimensão deve pesar no perfil final.",
            )

            c1, c2, c3 = st.columns(3)

            with c1:
                w_shot = st.number_input(
                    "🥅 Shot Stopping",
                    min_value=0,
                    max_value=100,
                    value=30,
                    step=5,
                    key="w_shot",
                )

            with c2:
                w_distribution = st.number_input(
                    "⚽ Distribution",
                    min_value=0,
                    max_value=100,
                    value=35,
                    step=5,
                    key="w_distribution",
                )

            with c3:
                w_proactivity = st.number_input(
                    "🧤 Proactivity",
                    min_value=0,
                    max_value=100,
                    value=35,
                    step=5,
                    key="w_proactivity",
                )

            total = (
                w_shot
                + w_distribution
                + w_proactivity
            )

            # Os pesos sao sempre normalizados pela soma, por isso o que
            # conta e a proporcao entre dimensoes. Em vez de fingir que a
            # soma tem de dar 100, mostramos a proporcao efetivamente usada.
            if total <= 0:

                st.warning(
                    "Define pelo menos uma dimensão com peso maior que zero."
                )

            else:

                effective = normalise_dimension_weights(
                    {
                        "Shot Stopping": w_shot,
                        "Distribution": w_distribution,
                        "Proactivity": w_proactivity,
                    }
                )

                st.caption(
                    "Peso efetivamente aplicado: "
                    f"🥅 Shot Stopping {effective['Shot Stopping']:.0%} · "
                    f"⚽ Distribution {effective['Distribution']:.0%} · "
                    f"🧤 Proactivity {effective['Proactivity']:.0%}"
                )

            st.divider()

            render_section_title(
                "🎛️ Filtros"
            )

            c1, c2, c3, c4, c5 = st.columns(5)

            with c1:
                max_market_value = st.number_input(
                    "💰 Valor máximo (€M)",
                    min_value=0.0,
                    max_value=500.0,
                    value=50.0,
                    step=5.0,
                    help="0 = sem limite",
                    key="similar_max_market",
                )

            with c2:
                max_age = st.number_input(
                    "🎂 Idade máxima",
                    min_value=16,
                    max_value=45,
                    value=35,
                    step=1,
                    help="0 = sem limite",
                    key="similar_max_age",
                )

            with c3:
                min_similarity = st.number_input(
                    "🎯 Similaridade mínima (%)",
                    min_value=0,
                    max_value=100,
                    value=60,
                    step=5,
                    key="similar_minimum",
                )

            with c4:
                min_minutes = st.number_input(
                    "⏱️ Minutos mínimos",
                    min_value=90,
                    max_value=5000,
                    value=suggested_min_minutes,
                    step=90,
                    help=(
                        "Sugerido a partir da amostra carregada "
                        "(percentil 25, arredondado a jogos completos)."
                    ),
                    key="similar_minutes",
                )

            with c5:
                top_n = st.number_input(
                    "👥 Candidatos",
                    min_value=3,
                    max_value=20,
                    value=5,
                    step=1,
                    key="similar_top_n",
                )

            st.caption(
                "Valor máximo ou idade máxima = 0 significa sem limite."
            )

            run_similarity = st.button(
                "🔎 Procurar semelhantes",
                type="primary",
                disabled=(total <= 0),
                key="run_similarity",
            )

            if run_similarity:

                weights = {
                    "Shot Stopping": w_shot,
                    "Distribution": w_distribution,
                    "Proactivity": w_proactivity,
                }

                calculation_top_n = min(
                    max(
                        int(top_n) * 10,
                        50,
                    ),
                    500,
                )

                with st.spinner(
                    "A calcular perfis semelhantes..."
                ):

                    try:

                        sim = find_similar_goalkeepers(
                            table,
                            target,
                            top_n=calculation_top_n,
                            features=STYLE_FEATURES,
                            min_minutes=int(min_minutes),
                            dimension_weights=weights,
                        )

                    except Exception as exc:

                        st.error(
                            f"Não foi possível calcular os semelhantes: {exc}"
                        )

                        sim = pd.DataFrame()

                # Market filter
                if (
                    not sim.empty
                    and max_market_value > 0
                ):

                    max_value_eur = (
                        float(max_market_value)
                        * 1_000_000
                    )

                    allowed = []

                    for candidate in sim.index:

                        market = market_for_performance(
                            candidate
                        )

                        if market is None:
                            allowed.append(candidate)
                            continue

                        value = pd.to_numeric(
                            market.get(
                                "market_value_in_eur"
                            ),
                            errors="coerce",
                        )

                        if (
                            pd.isna(value)
                            or float(value) <= max_value_eur
                        ):

                            allowed.append(candidate)

                    sim = sim.loc[
                        sim.index.isin(
                            allowed
                        )
                    ].copy()

                # Age filter
                if (
                    not sim.empty
                    and int(max_age) > 0
                ):

                    allowed = []

                    for candidate in sim.index:

                        market = market_for_performance(
                            candidate
                        )

                        if market is None:
                            allowed.append(candidate)
                            continue

                        age = calculate_age(
                            market.get(
                                "date_of_birth"
                            )
                        )

                        if (
                            age is None
                            or age <= int(max_age)
                        ):
                            allowed.append(candidate)

                    sim = sim.loc[
                        sim.index.isin(
                            allowed
                        )
                    ].copy()

                # Minimum similarity
                if not sim.empty:

                    sim = sim[
                        sim["similarity_pct"]
                        >= float(
                            min_similarity
                        )
                    ].copy()

                if not sim.empty:
                    sim = sim.head(
                        int(top_n)
                    )

                st.divider()

                render_section_title(
                    "🎯 Resultados",
                    f"Perfis que cumprem os filtros definidos.",
                )

                if sim.empty:

                    st.info(
                        "Nenhum candidato atingiu todos os filtros selecionados."
                    )

                else:

                    def safe_metric(
                        candidate,
                        column,
                        decimals=1,
                    ):

                        if column not in sim.columns:
                            return "N/A"

                        value = sim.loc[
                            candidate,
                            column,
                        ]

                        if pd.isna(value):
                            return "N/A"

                        return round(
                            float(value),
                            decimals,
                        )

                    rows = []

                    for rank, candidate in enumerate(
                        sim.index,
                        start=1,
                    ):

                        market = market_for_performance(
                            candidate
                        )

                        if market is not None:

                            candidate_club = (
                                market.get(
                                    "current_club_name",
                                    "N/A",
                                )
                            )

                            if pd.isna(
                                candidate_club
                            ):
                                candidate_club = "N/A"

                            candidate_value = (
                                format_market_value(
                                    market.get(
                                        "market_value_in_eur"
                                    )
                                )
                            )

                            candidate_age = calculate_age(
                                market.get(
                                    "date_of_birth"
                                )
                            )

                        else:

                            candidate_club = "N/A"
                            candidate_value = "N/A"
                            candidate_age = None

                        rows.append(
                            {
                                "#": rank,
                                "Guarda-redes": candidate,
                                "Clube": candidate_club,
                                "Idade": (
                                    candidate_age
                                    if candidate_age is not None
                                    else "N/A"
                                ),
                                "Valor de mercado": candidate_value,
                                "Similaridade (%)": safe_metric(
                                    candidate,
                                    "similarity_pct",
                                    1,
                                ),
                                "Minutos": safe_metric(
                                    candidate,
                                    "minutes",
                                    0,
                                ),
                                "Defesas (%)": safe_metric(
                                    candidate,
                                    "save_pct",
                                    1,
                                ),
                                "Passes certos (%)": safe_metric(
                                    candidate,
                                    "pass_success_pct",
                                    1,
                                ),
                                "Passe médio (m)": safe_metric(
                                    candidate,
                                    "avg_pass_length",
                                    1,
                                ),
                                "Bola longa (%)": safe_metric(
                                    candidate,
                                    "long_ball_pct",
                                    1,
                                ),
                                "Saídas /90": safe_metric(
                                    candidate,
                                    "sweeper_actions_p90",
                                    2,
                                ),
                                "Distância média": safe_metric(
                                    candidate,
                                    "avg_distance_from_goal",
                                    1,
                                ),
                            }
                        )

                    st.dataframe(
                        pd.DataFrame(rows),
                        width="stretch",
                        hide_index=True,
                    )

                    render_section_title(
                        "🧠 Leitura de scouting"
                    )

                    for rank, candidate in enumerate(
                        sim.index,
                        start=1,
                    ):

                        score = float(
                            sim.loc[
                                candidate,
                                "similarity_pct",
                            ]
                        )

                        market = market_for_performance(
                            candidate
                        )

                        meta = ""

                        if market is not None:

                            candidate_club = market.get(
                                "current_club_name",
                                "N/A",
                            )

                            if pd.isna(
                                candidate_club
                            ):
                                candidate_club = "N/A"

                            meta = (
                                f" · {candidate_club} · "
                                f"{format_market_value(market.get('market_value_in_eur'))}"
                            )

                        st.markdown(
                            f"**{rank}. {candidate}** — "
                            f"{score:.1f}% de similaridade"
                            f"{meta}"
                        )

                        st.caption(
                            explain_similarity(
                                table,
                                target,
                                candidate,
                                features=STYLE_FEATURES,
                            )
                        )