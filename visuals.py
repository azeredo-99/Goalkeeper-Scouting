"""
gk_scouting.visuals
--------------------
Gera as duas peças visuais centrais do projeto:

1. plot_radar()   -> radar comparando 2-4 guarda-redes em várias métricas
2. plot_sweeper_map() -> mapa do campo com as ações de sweeper-keeper de um jogador

"""

import numpy as np
import matplotlib.pyplot as plt
from mplsoccer import Pitch

BG = "#0f172a"
PANEL = "#1e293b"
GRID = "#334155"
TEXT = "#e2e8f0"
ACCENT = ["#22c55e", "#f59e0b", "#38bdf8", "#f472b6"]

# métricas usadas no radar + se "mais alto é melhor" (True) ou "mais baixo é melhor" (False)
RADAR_METRICS = {
    "save_pct": ("Eficácia defesas (%)", True),
    "sweeper_actions_p90": ("Ações Sweeper /90", True),
    "avg_distance_from_goal": ("Distância média à baliza", True),
    "pass_success_pct": ("Eficácia de passe (%)", True),
    "long_ball_pct": ("% Bola longa", True),
}


def _normalize(table, metric):
    """Normaliza uma coluna para 0-100 com base no min/max de TODOS os guarda-redes da tabela."""
    col = table[metric].astype(float)
    lo, hi = col.min(), col.max()
    if hi == lo:
        return col * 0 + 50
    return (col - lo) / (hi - lo) * 100


def plot_radar(table, players, out_path):
    """
    Desenha um radar comparando `players` (lista de nomes, devem existir no índice de `table`)
    nas métricas definidas em RADAR_METRICS. Guarda o gráfico em `out_path`.
    """
    metrics = list(RADAR_METRICS.keys())
    labels = [RADAR_METRICS[m][0] for m in metrics]
    n = len(metrics)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PANEL)

    for i, player in enumerate(players):
        if player not in table.index:
            continue
        values = [_normalize(table, m)[player] for m in metrics]
        values += values[:1]
        color = ACCENT[i % len(ACCENT)]
        ax.plot(angles, values, color=color, linewidth=2, label=player)
        ax.fill(angles, values, color=color, alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, color=TEXT, fontsize=10)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels([])
    ax.spines["polar"].set_color(GRID)
    ax.grid(color=GRID, alpha=0.5)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    plt.title(
        "Perfil Comparativo de Guarda-Redes\n(percentil dentro da amostra analisada)",
        color=TEXT, fontsize=13, pad=30,
    )
    legend = ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.15),
                        facecolor=PANEL, edgecolor="none", labelcolor=TEXT)
    fig.savefig(out_path, facecolor=BG, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_sweeper_map(gk_events, player, out_path):
    """
    Desenha o campo com todas as ações de 'Keeper Sweeper' (saídas da baliza)
    de um guarda-redes, coloridas por resultado (Claim / Clear / Punch / Success...).
    """
    df = gk_events[(gk_events["player"] == player) & (gk_events["goalkeeper_type"] == "Keeper Sweeper")]

    pitch = Pitch(pitch_type="statsbomb", pitch_color=BG, line_color=GRID, half=False)
    fig, ax = pitch.draw(figsize=(10, 7))
    fig.set_facecolor(BG)

    outcomes = df["goalkeeper_outcome"].fillna("Outro")
    unique_outcomes = outcomes.unique()
    colors = {o: ACCENT[i % len(ACCENT)] for i, o in enumerate(unique_outcomes)}

    for outcome in unique_outcomes:
        sub = df[outcomes == outcome]
        pitch.scatter(sub["x"], sub["y"], ax=ax, s=220, color=colors[outcome],
                       edgecolors="white", linewidth=1, label=outcome, zorder=3)

    # linha de referência: área grande (18 jardas)
    ax.legend(facecolor=PANEL, edgecolor="none", labelcolor=TEXT, loc="upper right")
    plt.title(f"Ações de Sweeper-Keeper — {player}", color=TEXT, fontsize=14, pad=10)
    fig.savefig(out_path, facecolor=BG, dpi=150, bbox_inches="tight")
    plt.close(fig)
