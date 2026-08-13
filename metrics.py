"""
gk_scouting.metrics
--------------------
Transforma eventos individuais em métricas agregadas por guarda-redes,
prontas para comparar jogadores (radar chart, tabela, ranking).

Todas as métricas são normalizadas por 90 minutos onde faz sentido,
para poderes comparar guarda-redes com números de minutos diferentes.
"""

import numpy as np
import pandas as pd

# Coordenadas StatsBomb: campo 120 x 80. A baliza própria fica perto de x=0.
OWN_GOAL_X = 0
OWN_GOAL_Y = 40


def _distance_to_goal(x, y):
    if pd.isna(x) or pd.isna(y):
        return np.nan
    return float(np.hypot(x - OWN_GOAL_X, y - OWN_GOAL_Y))


def compute_minutes_played(events: pd.DataFrame, gk_events: pd.DataFrame) -> pd.Series:
    """Estima os minutos jogados por cada guarda-redes com base no último evento do jogo em que participou."""
    max_minute_per_match = events.groupby("match_id")["minute"].max()
    rows = []
    for (player, match_id), grp in gk_events.groupby(["player", "match_id"]):
        rows.append({"player": player, "minutes": max_minute_per_match.get(match_id, 90)})
    df = pd.DataFrame(rows)
    return df.groupby("player")["minutes"].sum()


def sweeper_keeper_metrics(gk_events: pd.DataFrame) -> pd.DataFrame:
    """
    Métricas de 'Sweeper Keeper': quão proativo é o guarda-redes a sair
    da área para intercetar / limpar bolas em profundidade.
    """
    sweeper = gk_events[gk_events["goalkeeper_type"] == "Keeper Sweeper"].copy()
    sweeper["distance_from_goal"] = sweeper.apply(lambda r: _distance_to_goal(r["x"], r["y"]), axis=1)

    agg = sweeper.groupby("player").agg(
        sweeper_actions=("player", "count"),
        avg_distance_from_goal=("distance_from_goal", "mean"),
        max_distance_from_goal=("distance_from_goal", "max"),
    )
    return agg


def shot_stopping_metrics(gk_events: pd.DataFrame) -> pd.DataFrame:
    """
    Métricas clássicas de defesa de remates: remates enfrentados, defesas,
    golos sofridos e % de defesas.
    """
    shots_faced = gk_events[gk_events["goalkeeper_type"] == "Shot Faced"].groupby("player").size()
    saves = gk_events[gk_events["goalkeeper_type"] == "Shot Saved"].groupby("player").size()
    goals_conceded = gk_events[gk_events["goalkeeper_type"] == "Goal Conceded"].groupby("player").size()

    df = pd.DataFrame({
        "shots_faced": shots_faced,
        "shots_saved": saves,
        "goals_conceded": goals_conceded,
    }).fillna(0)

    df["save_pct"] = np.where(df["shots_faced"] > 0, df["shots_saved"] / df["shots_faced"] * 100, np.nan)
    return df


def distribution_metrics(gk_passes: pd.DataFrame) -> pd.DataFrame:
    """
    Métricas de construção de jogo: nº de passes, % de sucesso,
    comprimento médio e % de passes longos (>40 jardas StatsBomb).
    """
    df = gk_passes.copy()
    df["is_success"] = df["pass_outcome"].isna()  # NaN em pass_outcome = passe completado
    df["is_long"] = df["pass_length"] > 40

    agg = df.groupby("player").agg(
        total_passes=("player", "count"),
        pass_success_pct=("is_success", lambda s: s.mean() * 100),
        avg_pass_length=("pass_length", "mean"),
        long_ball_pct=("is_long", lambda s: s.mean() * 100),
    )
    return agg


def build_scouting_table(events: pd.DataFrame, gk_events: pd.DataFrame, gk_passes: pd.DataFrame) -> pd.DataFrame:
    """
    Junta todas as métricas numa única tabela por guarda-redes:
    minutos, sweeper-keeper, shot-stopping e distribuição.
    Esta é a tabela "mestra" para scouting e para gerar os radares.
    """
    minutes = compute_minutes_played(events, gk_events)
    sweeper = sweeper_keeper_metrics(gk_events)
    shots = shot_stopping_metrics(gk_events)
    dist = distribution_metrics(gk_passes)

    table = pd.concat([minutes.rename("minutes"), sweeper, shots, dist], axis=1)

    # normalizar ações por 90 minutos para permitir comparação justa
    table["sweeper_actions_p90"] = table["sweeper_actions"] / table["minutes"] * 90
    table["shots_faced_p90"] = table["shots_faced"] / table["minutes"] * 90

    return table.sort_values("minutes", ascending=False)
