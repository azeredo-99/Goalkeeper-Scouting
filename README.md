# Goalkeeper Scouting 🧤⚽

Plataforma de **data scouting especializada em guarda-redes**, criada para transformar
dados de performance e mercado em informação útil para recrutamento.

O projeto combina:

- dados de eventos da [StatsBomb Open Data](https://github.com/statsbomb/open-data);
- dados de mercado de jogadores;
- métricas específicas para guarda-redes;
- matching entre diferentes fontes de dados;
- análise de perfis;
- comparação entre jogadores;
- identificação de guarda-redes com estilos semelhantes.

O objetivo não é apenas mostrar estatísticas. É construir uma ferramenta capaz de
responder a perguntas reais de scouting, como:

> "Quem apresenta um perfil semelhante ao meu guarda-redes atual, mas é mais jovem
> e tem um valor de mercado inferior?"

---

## 🎯 O problema

Os clubes acumulam grandes quantidades de dados de performance, mas transformar
esses dados em informação útil para recrutamento continua a exigir bastante trabalho
manual.

Este projeto procura automatizar parte desse processo, criando uma camada de análise
específica para guarda-redes.

Em vez de olhar apenas para defesas e golos sofridos, o modelo procura capturar
dimensões que caracterizam diferentes estilos de guarda-redes:

- **Shot Stopping**
- **Distribution**
- **Proactivity / Sweeper-Keeper**

---

## 🚀 O que a plataforma faz

### 👤 Perfil individual

Para cada guarda-redes, a plataforma combina informação de mercado e performance.

#### Mercado

- idade;
- clube atual;
- valor de mercado;
- maior valor de mercado.

#### Performance

- minutos jogados;
- eficácia de defesas;
- eficácia de passe;
- comprimento médio do passe;
- percentagem de bola longa;
- ações de Sweeper-Keeper por 90;
- distância média à própria baliza.

---

### ⚖️ Comparar guarda-redes

Permite comparar dois ou três guarda-redes lado a lado.

A comparação inclui:

- contexto de mercado;
- idade;
- valor de mercado;
- minutos;
- shot stopping;
- distribuição;
- proatividade;
- restantes métricas disponíveis.

A plataforma pode também gerar um **radar comparativo** para visualizar rapidamente
as diferenças de perfil.

---

### 🔎 Encontrar semelhantes

O motor de similaridade procura guarda-redes com um perfil estatístico semelhante
ao jogador escolhido.

O utilizador pode controlar o perfil procurado através de pesos para:

- **Shot Stopping**
- **Distribution**
- **Proactivity**

Os pesos funcionam como um orçamento de **100%**, impedindo que a combinação das
dimensões ultrapasse esse valor.

Também podem ser aplicados filtros de recrutamento:

- valor máximo de mercado;
- idade máxima;
- similaridade mínima;
- minutos mínimos;
- número de candidatos.

Isto permite transformar a análise estatística numa pesquisa de recrutamento.

Exemplo:

> Encontrar guarda-redes semelhantes a Gianluigi Donnarumma, com pelo menos
> 60% de similaridade, menos de €20M de valor de mercado, com idade máxima de
> 28 anos e pelo menos 720 minutos analisados.

---

## 📊 Métricas

As principais métricas atualmente utilizadas incluem:

| Métrica técnica | Significado |
|---|---|
| `sweeper_actions_p90` | Ações de Sweeper-Keeper por 90 minutos |
| `avg_distance_from_goal` | Distância média à própria baliza |
| `save_pct` | Percentagem de remates defendidos |
| `shots_faced_p90` | Remates enfrentados por 90 minutos |
| `pass_success_pct` | Percentagem de passes certos |
| `avg_pass_length` | Comprimento médio do passe |
| `long_ball_pct` | Percentagem de passes longos |
| `minutes` | Minutos jogados |

As métricas são normalizadas para permitir comparações entre jogadores com diferentes
minutagens e perfis estatísticos.

---

## 🧠 Motor de similaridade

A similaridade é calculada sobre o **perfil de estilo de jogo**, e não sobre uma
avaliação absoluta da qualidade do guarda-redes.

O modelo considera seis características principais:

- ações de Sweeper-Keeper por 90;
- distância média à baliza;
- eficácia de defesas;
- eficácia de passe;
- comprimento médio do passe;
- percentagem de bola longa.

Estas características são agrupadas em três dimensões:

### Shot Stopping
- eficácia de defesas.

### Distribution
- eficácia de passe;
- comprimento médio do passe;
- percentagem de bola longa.

### Proactivity
- ações de Sweeper-Keeper;
- distância média à baliza.

O utilizador pode controlar o peso relativo destas dimensões.

> **Importante:** uma elevada similaridade significa que dois jogadores apresentam
> características estatísticas semelhantes. Não significa automaticamente que tenham
> a mesma qualidade ou valor desportivo.

---

## 🗂️ Dados

### Performance

A performance é baseada em eventos da **StatsBomb Open Data**.

O projeto suporta uma base alargada de competições e épocas disponíveis no dataset,
em vez de estar limitado a uma única competição.

### Mercado

Os dados de mercado incluem informação proveniente da base de jogadores utilizada
pelo projeto, incluindo:

- clube atual;
- data de nascimento;
- valor de mercado;
- maior valor de mercado.

A base é mantida localmente depois do primeiro carregamento, permitindo que a
aplicação seja executada sem depender de um download a cada arranque.

---

## 🔗 Matching entre fontes

StatsBomb e a base de mercado não utilizam necessariamente exatamente o mesmo nome
para um jogador.

Por isso existe uma camada específica de **player matching**, capaz de ligar
jogadores entre as duas fontes através de:

1. correspondência exata;
2. primeiro + último nome;
3. correspondência por tokens;
4. tratamento de nomes intermédios.

Exemplo:

```text
StatsBomb
Diogo Meireles Costa

Mercado
Diogo Costa

→ mesmo jogador
---
*Dados: [StatsBomb Open Data](https://github.com/statsbomb/open-data), disponíveis
gratuitamente para fins de investigação e desenvolvimento de portfólio.*
