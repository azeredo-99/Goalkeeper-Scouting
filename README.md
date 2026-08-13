# Algoritmo de Perfilagem de Guarda-Redes ⚽🧤

Projeto de **data scouting** focado na posição de guarda-redes, construído com dados
reais da [StatsBomb Open Data](https://github.com/statsbomb/open-data).

As métricas escolhidas não são só "defesas e golos sofridos" — tentam capturar
o que realmente distingue um guarda-redes moderno: **proatividade a sair da
baliza (sweeper-keeper)**, **qualidade de distribuição** e **eficácia a defender remates**.

## Porquê este projeto

A maioria dos clubes já tem scouts tradicionais que "veem" bem futebol. O que
falta é gente que saiba transformar milhares de eventos em dados legíveis e
comparáveis. Este projeto mostra exatamente isso: pega em dados brutos de
eventos (passe a passe, ação a ação) e devolve uma tabela e dois gráficos que
um Diretor Desportivo consegue interpretar em segundos.

## O que o projeto faz

1. **Carrega** eventos de jogos reais via `statsbombpy` (dados abertos do Mundial 2022).
2. **Isola** todas as ações de guarda-redes: saídas da baliza (*Keeper Sweeper*),
   defesas, golos sofridos, e a distribuição de bola (passes).
3. **Calcula métricas por 90 minutos**, para comparar jogadores com minutagens diferentes:
   - `sweeper_actions_p90` — nº de saídas da baliza por 90 min
   - `avg_distance_from_goal` — a que distância da própria baliza o guarda-redes atua
   - `save_pct` — eficácia de defesas
   - `pass_success_pct` / `long_ball_pct` — perfil de construção de jogo
4. **Visualiza**:
   - Um **radar comparativo** entre vários guarda-redes (`output/radar_comparativo.png`)
   - Um **mapa de campo** com as saídas da baliza de um jogador específico (`output/sweeper_map_*.png`)

## Como correr

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

A primeira vez que corres: demora ~3-5 min a descarregar os 64 jogos do Mundial 2022
(depois fica em cache local em `data/events_full_wc2022.pkl` e as próximas execuções são instantâneas).

Os resultados aparecem em `output/`:
- `scouting_table.csv` — métricas de todos os guarda-redes da competição
- `radar_comparativo.png`
- `sweeper_map_<jogador>.png`
- `similar_to_<jogador>.csv` — resultado do algoritmo de similaridade

### Versão interativa (Streamlit)

```bash
streamlit run streamlit_app.py
```

Abre uma app no browser com 3 separadores: perfil individual, comparação lado-a-lado,
e "encontrar guarda-redes parecidos" — a mesma lógica do `main.py`, mas explorável sem tocar em código.

## Estrutura do código

```
gk_scouting/
├── data_loader.py        # ligação à StatsBomb + limpeza de coordenadas
├── metrics.py             # cálculo das métricas de scouting (a lógica "de futebol")
├── visuals.py              # radar + mapa de campo 
├── similarity_engine.py    # "encontrar o novo X" — similaridade de cosseno entre perfis
├── main.py                 # pipeline em linha de comandos, ponto de entrada
├── streamlit_app.py        # versão interativa (dashboard no browser)
└── output/                 # tabela + gráficos gerados
```

## Exemplo de resultado (Mundial 2022 completo — 64 jogos, 34 guarda-redes com ≥180 min)

|   Guarda-redes    | Minutos | Ações Sweeper/90 | Distância média à baliza | Eficácia defesas | Eficácia passe |
|-------------------|---------|------------------|--------------------------|------------------|----------------|
| Emiliano Martínez |   739   |       0.5        |         13.5m            |       18.2%      |     66.1%      |
| Dominik Livaković |   725   |       0.2        |         10.2m            |		45.3%      |     82.9%	    |
| Manuel Neuer      |   293   |       1.2        |         25.2m            |		50.0%	   |     90.2%      |
| Alisson Becker    |   410   |       0.2        |         31.7m            |		25.0%      |     85.1%      |

### Exemplo do algoritmo de similaridade: "quem é parecido com o Neuer?"

|    Candidato    | Similaridade |
|-----------------|--------------|
| Unai Simón      |    94.5%     |
| Andries Noppert |    92.1%     | 
| Matthew Turner  |    87.5%     |
| Yann Sommer     |    82.3%     |

Isto confirma o que o olho treinado já esperaria: Neuer, Unai Simón e Noppert
são todos guarda-redes "líbero", muito proativos fora da área — o algoritmo
encontra esse padrão só a partir dos números, sem saber nada de futebol a priori.

## Próximos passos possíveis

- Cruzar com dados de mercado (idade, valor, contrato) para responder
  "quem é parecido E mais barato/mais jovem"
- Juntar mais competições/épocas (ex: ligas domésticas) para aumentar a amostra
- Adicionar zonas de distribuição (heatmap de para onde o guarda-redes lança a bola)

---
*Dados: [StatsBomb Open Data](https://github.com/statsbomb/open-data), disponíveis
gratuitamente para fins de investigação e desenvolvimento de portfólio.*
