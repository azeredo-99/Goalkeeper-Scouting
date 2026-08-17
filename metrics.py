"""
gk_scouting.metrics
-------------------

Transforma eventos StatsBomb em métricas agregadas por guarda-redes.

Versão otimizada:
- evita apply(axis=1);
- reduz loops Python;
- usa groupby/vectorização;
- mantém a mesma API pública.
"""

import numpy as np
import pandas as pd


OWN_GOAL_X = 0.0
OWN_GOAL_Y = 40.0


def _distance_to_goal_series(
    x: pd.Series,
    y: pd.Series,
) -> pd.Series:
    """Distância vetorizada à baliza própria."""

    x_num = pd.to_numeric(
        x,
        errors="coerce",
    )

    y_num = pd.to_numeric(
        y,
        errors="coerce",
    )

    return np.hypot(
        x_num - OWN_GOAL_X,
        y_num - OWN_GOAL_Y,
    )


def compute_minutes_played(
    events: pd.DataFrame,
    gk_events: pd.DataFrame,
) -> pd.Series:
    """
    Estima minutos jogados.

    Em vez de criar uma linha por jogador/jogo através de um loop,
    faz um merge vetorizado entre gk_events e a duração máxima
    observada em cada partida.
    """

    if (
        events.empty
        or gk_events.empty
    ):
        return pd.Series(
            dtype=float,
            name="minutes",
        )

    max_minute_per_match = (
        events.groupby(
            "match_id",
            sort=False,
        )["minute"]
        .max()
    )

    player_match = (
        gk_events[
            [
                "player",
                "match_id",
            ]
        ]
        .dropna(
            subset=[
                "player",
                "match_id",
            ]
        )
        .drop_duplicates()
        .copy()
    )

    player_match["minutes"] = (
        player_match["match_id"]
        .map(max_minute_per_match)
        .fillna(90)
        .astype(float)
    )

    return (
        player_match
        .groupby(
            "player",
            sort=False,
        )["minutes"]
        .sum()
        .rename("minutes")
    )


def sweeper_keeper_metrics(
    gk_events: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas de sweeper-keeper sem apply."""

    if gk_events.empty:
        return pd.DataFrame(
            columns=[
                "sweeper_actions",
                "avg_distance_from_goal",
                "max_distance_from_goal",
            ]
        )

    sweeper = gk_events[
        gk_events["goalkeeper_type"]
        == "Keeper Sweeper"
    ].copy()

    if sweeper.empty:

        return pd.DataFrame(
            columns=[
                "sweeper_actions",
                "avg_distance_from_goal",
                "max_distance_from_goal",
            ]
        )

    sweeper["distance_from_goal"] = (
        _distance_to_goal_series(
            sweeper["x"],
            sweeper["y"],
        )
    )

    return (
        sweeper
        .groupby(
            "player",
            sort=False,
        )
        .agg(
            sweeper_actions=(
                "player",
                "size",
            ),
            avg_distance_from_goal=(
                "distance_from_goal",
                "mean",
            ),
            max_distance_from_goal=(
                "distance_from_goal",
                "max",
            ),
        )
    )


def shot_stopping_metrics(
    gk_events: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas de shot stopping."""

    if gk_events.empty:
        return pd.DataFrame(
            columns=[
                "shots_faced",
                "shots_saved",
                "goals_conceded",
                "save_pct",
            ]
        )

    type_series = gk_events[
        "goalkeeper_type"
    ]

    shots_faced = (
        type_series.eq(
            "Shot Faced"
        )
        .groupby(
            gk_events["player"],
            sort=False,
        )
        .sum()
    )

    shots_saved = (
        type_series.eq(
            "Shot Saved"
        )
        .groupby(
            gk_events["player"],
            sort=False,
        )
        .sum()
    )

    goals_conceded = (
        type_series.eq(
            "Goal Conceded"
        )
        .groupby(
            gk_events["player"],
            sort=False,
        )
        .sum()
    )

    df = pd.concat(
        [
            shots_faced.rename(
                "shots_faced"
            ),
            shots_saved.rename(
                "shots_saved"
            ),
            goals_conceded.rename(
                "goals_conceded"
            ),
        ],
        axis=1,
    ).fillna(0.0)

    df["save_pct"] = np.where(
        df["shots_faced"] > 0,
        (
            df["shots_saved"]
            / df["shots_faced"]
            * 100
        ),
        np.nan,
    )

    return df


def distribution_metrics(
    gk_passes: pd.DataFrame,
) -> pd.DataFrame:
    """Calcula métricas de distribuição sem loops."""

    if gk_passes.empty:
        return pd.DataFrame(
            columns=[
                "total_passes",
                "pass_success_pct",
                "avg_pass_length",
                "long_ball_pct",
            ]
        )

    df = gk_passes.copy()

    outcome = df[
        "pass_outcome"
    ]

    df["is_success"] = (
        outcome.isna()
    )

    df["is_long"] = (
        pd.to_numeric(
            df["pass_length"],
            errors="coerce",
        )
        > 40
    )

    return (
        df
        .groupby(
            "player",
            sort=False,
        )
        .agg(
            total_passes=(
                "player",
                "size",
            ),
            pass_success_pct=(
                "is_success",
                "mean",
            ),
            avg_pass_length=(
                "pass_length",
                "mean",
            ),
            long_ball_pct=(
                "is_long",
                "mean",
            ),
        )
        .assign(
            pass_success_pct=lambda frame:
                frame["pass_success_pct"] * 100,
            long_ball_pct=lambda frame:
                frame["long_ball_pct"] * 100,
        )
    )


def build_scouting_table(
    events: pd.DataFrame,
    gk_events: pd.DataFrame,
    gk_passes: pd.DataFrame,
) -> pd.DataFrame:
    """
    Junta todas as métricas numa única tabela por guarda-redes.
    """

    minutes = compute_minutes_played(
        events,
        gk_events,
    )

    sweeper = sweeper_keeper_metrics(
        gk_events,
    )

    shots = shot_stopping_metrics(
        gk_events,
    )

    dist = distribution_metrics(
        gk_passes,
    )

    table = pd.concat(
        [
            minutes,
            sweeper,
            shots,
            dist,
        ],
        axis=1,
    )

    table.index.name = "player"

    table["sweeper_actions_p90"] = np.where(
        table["minutes"] > 0,
        (
            table["sweeper_actions"]
            / table["minutes"]
            * 90
        ),
        np.nan,
    )

    table["shots_faced_p90"] = np.where(
        table["minutes"] > 0,
        (
            table["shots_faced"]
            / table["minutes"]
            * 90
        ),
        np.nan,
    )

    return table.sort_values(
        "minutes",
        ascending=False,
    )