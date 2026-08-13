"""
Download de uma base de eventos grande e atualizada para o Goalkeeper Scouting.

O script consulta automaticamente o catálogo do StatsBomb Open Data e escolhe,
para cada competição, a época mais recente disponível. Assim não ficamos presos
a IDs antigas e, quando 2025/26 for publicada no Open Data, ela poderá ser usada
automaticamente.

Executar:
    python download_extended_data.py

Saída:
    data/events_extended.pkl
"""

from pathlib import Path

import pandas as pd
import requests

from data_loader import load_competition_events


COMPETITIONS_URL = (
    "https://raw.githubusercontent.com/statsbomb/open-data/"
    "master/data/competitions.json"
)

OUTPUT = Path("data/events_extended.pkl")

# Competições prioritárias para scouting de futebol masculino.
# O nome é usado para localizar a competição no catálogo atual.
PRIORITY_COMPETITIONS = [
    "Premier League",
    "La Liga",
    "Bundesliga",
    "Ligue 1",
    "Serie A",
    "Eredivisie",
    "Primeira Liga",
    "UEFA Champions League",
    "Europa League",
    "MLS",
    "World Cup",
    "European Championship",
    "Copa America",
]


# Competições que podem existir no catálogo mas que não são úteis
# para o objetivo principal deste projeto.
EXCLUDED_NAMES = {
    "women's super league",
    "fa women's super league",
}


def load_catalog():
    response = requests.get(
        COMPETITIONS_URL,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def competition_matches(row, wanted_name):
    name = str(row.get("competition_name", "")).strip().lower()
    wanted = wanted_name.lower()
    return name == wanted


def select_latest_competitions(catalog):
    """
    Seleciona a época mais recente disponível para cada competição.

    O catálogo do StatsBomb usa competition_id e season_id e não garante
    que a época mais recente seja a última linha do JSON, por isso usamos
    a data/final year quando disponível.
    """

    selected = []

    for wanted in PRIORITY_COMPETITIONS:
        candidates = [
            row
            for row in catalog
            if competition_matches(row, wanted)
            and str(row.get("competition_name", "")).strip().lower()
            not in EXCLUDED_NAMES
        ]

        if not candidates:
            continue

        def season_sort_key(row):
            season = row.get("season_name", "")
            text = str(season)
            numbers = []
            current = ""
            for char in text:
                if char.isdigit():
                    current += char
                elif current:
                    numbers.append(int(current))
                    current = ""
            if current:
                numbers.append(int(current))
            return max(numbers) if numbers else -1

        latest = max(
            candidates,
            key=season_sort_key,
        )

        selected.append(latest)

    return selected


def main():
    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("=" * 70)
    print("GOALKEEPER SCOUTING — BASE EXTENDIDA")
    print("=" * 70)
    print("A consultar catálogo atual do StatsBomb...")

    catalog = load_catalog()
    selected = select_latest_competitions(catalog)

    if not selected:
        raise RuntimeError(
            "Não foram encontradas competições compatíveis "
            "no catálogo do StatsBomb."
        )

    print("\nÉpocas mais recentes disponíveis encontradas:")

    for row in selected:
        print(
            f" - {row['competition_name']} | "
            f"{row['season_name']} | "
            f"competition_id={row['competition_id']} | "
            f"season_id={row['season_id']}"
        )

    datasets = []
    failed = []

    for i, row in enumerate(selected, start=1):
        competition_name = row["competition_name"]
        season_name = row["season_name"]

        print("\n" + "-" * 70)
        print(
            f"[{i}/{len(selected)}] "
            f"{competition_name} — {season_name}"
        )

        try:
            events = load_competition_events(
                competition_id=int(row["competition_id"]),
                season_id=int(row["season_id"]),
            )

            events["competition_id"] = int(row["competition_id"])
            events["season_id"] = int(row["season_id"])
            events["competition_name"] = competition_name
            events["season_name"] = season_name

            datasets.append(events)

            print(f"OK — {len(events):,} eventos")
            print(f"     {events['match_id'].nunique():,} jogos")

        except Exception as exc:
            print(f"ERRO — {exc}")
            failed.append(
                f"{competition_name} — {season_name}"
            )

    if not datasets:
        raise RuntimeError(
            "Não foi possível descarregar nenhuma competição."
        )

    all_events = pd.concat(
        datasets,
        ignore_index=True,
    )

    all_events.to_pickle(OUTPUT)

    goalkeeper_events = all_events[
        all_events["type"] == "Goal Keeper"
    ]

    print("\n" + "=" * 70)
    print("BASE CRIADA COM SUCESSO")
    print("=" * 70)
    print(f"Ficheiro: {OUTPUT}")
    print(f"Eventos: {len(all_events):,}")
    print(f"Jogos: {all_events['match_id'].nunique():,}")
    print(f"Eventos de GR: {len(goalkeeper_events):,}")

    print("\nPor competição:")

    summary = (
        all_events
        .groupby(["competition_name", "season_name"])
        .agg(
            jogos=("match_id", "nunique"),
            eventos=("match_id", "size"),
        )
        .sort_values("jogos", ascending=False)
    )

    print(summary.to_string())

    if failed:
        print("\nCompetições que falharam:")
        for name in failed:
            print(f" - {name}")


if __name__ == "__main__":
    main()
