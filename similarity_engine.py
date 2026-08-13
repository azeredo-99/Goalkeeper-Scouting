"""
gk_scouting.similarity_engine
-------------------------------
O projeto de scouting que realmente interessa a um Diretor Desportivo:
"o meu guarda-redes titular vai ser vendido — quem é parecido com ele
e mais barato/mais novo?"

Aqui não temos preços nem idades (a StatsBomb Open Data não os inclui),
mas o motor de similaridade é o mesmo que usarias com dados de mercado
reais (TransferMarkt, Wyscout) — troca-se só a origem dos dados.

Método: normaliza as métricas (z-score) e usa distância de cosseno
para encontrar os guarda-redes com o "perfil de jogo" mais parecido.
"""

import numpy as np
import pandas as pd
from numpy.linalg import norm

# Métricas que definem o "estilo" de um guarda-redes (não incluímos minutos,
# nem contagens absolutas, para não penalizar quem jogou menos jogos)
STYLE_FEATURES = [
    "sweeper_actions_p90",
    "avg_distance_from_goal",
    "save_pct",
    "pass_success_pct",
    "avg_pass_length",
    "long_ball_pct",
]


def _zscore(table: pd.DataFrame, features) -> pd.DataFrame:
    sub = table[features].astype(float)
    return (sub - sub.mean()) / sub.std(ddof=0)


def find_similar_goalkeepers(table: pd.DataFrame, target_player: str, top_n: int = 5,
                              features=None, min_minutes: int = 180) -> pd.DataFrame:
    """
    Devolve os `top_n` guarda-redes com o perfil de jogo mais parecido
    ao `target_player`, por similaridade de cosseno sobre as métricas
    normalizadas em STYLE_FEATURES.

    Útil para o caso de uso "o meu titular vai sair, quem é parecido e
    mais barato/mais jovem" — aqui identificamos o "parecido"; o "mais
    barato/mais jovem" cruza-se depois com dados de mercado (idade, valor).
    """
    features = features or STYLE_FEATURES
    pool = table[table["minutes"] >= min_minutes].dropna(subset=features)

    if target_player not in pool.index:
        raise ValueError(f"'{target_player}' não está na tabela (ou não tem minutos suficientes).")

    z = _zscore(pool, features)
    target_vec = z.loc[target_player].values

    similarities = {}
    for player, row in z.iterrows():
        if player == target_player:
            continue
        vec = row.values
        denom = norm(target_vec) * norm(vec)
        sim = float(np.dot(target_vec, vec) / denom) if denom != 0 else 0.0
        similarities[player] = sim

    result = pd.Series(similarities, name="similarity").sort_values(ascending=False).head(top_n)
    result_df = result.to_frame()
    result_df["similarity_pct"] = (result_df["similarity"] + 1) / 2 * 100  # de [-1,1] para [0,100]

    # junta as métricas originais para dar contexto ao scout
    return result_df.join(pool[features + ["minutes"]])


def explain_similarity(table: pd.DataFrame, target_player: str, candidate: str, features=None) -> str:
    """
    Gera uma frase curta em português explicando ONDE o candidato se parece
    (ou difere) do alvo — o "toque humano" que transforma números em scouting.
    """
    features = features or STYLE_FEATURES
    z = _zscore(table, features)
    diffs = (z.loc[candidate] - z.loc[target_player]).sort_values()

    closest = diffs.abs().idxmin()
    furthest = diffs.abs().idxmax()

    label_map = {
        "sweeper_actions_p90": "proatividade a sair da baliza",
        "avg_distance_from_goal": "distância a que atua da baliza",
        "save_pct": "eficácia de defesas",
        "pass_success_pct": "eficácia de passe",
        "avg_pass_length": "comprimento médio de passe",
        "long_ball_pct": "tendência para bola longa",
    }

    direction = "acima" if diffs[furthest] > 0 else "abaixo"
    return (
        f"{candidate} é muito parecido com {target_player} em {label_map.get(closest, closest)}, "
        f"mas fica {direction} da média em {label_map.get(furthest, furthest)}."
    )
