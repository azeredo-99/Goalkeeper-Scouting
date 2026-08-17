# Goalkeeper Scouting 🧤⚽

> A data-driven football scouting platform focused on goalkeeper analysis,
> comparison and recruitment.

🚧 **Status: In Development**

---

## 🎯 About the Project

**Goalkeeper Scouting** is a personal data scouting project focused on
evaluating and comparing goalkeepers using performance and market data.

The project aims to go beyond traditional statistics such as saves and goals
conceded by analysing different aspects of a goalkeeper's profile, including:

- 🧤 **Shot Stopping**
- ⚽ **Distribution**
- 🧠 **Proactivity**

The platform allows users to define a scouting profile, search for similar
goalkeepers and compare players according to their statistical profiles and
market context.

---

## ✨ Features

### 🔎 Find Similar Goalkeepers

Select a goalkeeper and search for players with statistically similar
profiles.

The similarity engine compares multiple performance dimensions and ranks
potential candidates according to the selected scouting profile.

![Find Similar Goalkeepers](docs/screenshots/find_similar.png)

---

### ⚖️ Custom Scouting Profile

The scouting profile allows the user to define how important each dimension
should be in the final analysis.

- **Shot Stopping**
- **Distribution**
- **Proactivity**

The weights can be adjusted depending on the requirements of a specific
scouting context.

![Scouting Profile](docs/screenshots/profile.png)

---

### 🎯 Similarity Results

After defining the desired profile and filters, the platform returns the
goalkeepers that best match the selected criteria.

Users can filter candidates by:

- Maximum market value
- Maximum age
- Minimum similarity
- Minimum minutes played
- Number of candidates

The results also provide additional performance and market information for
each goalkeeper.

![Similarity Results](docs/screenshots/similar_results.png)

---

### 📊 Player Comparison

The platform allows users to compare goalkeeper profiles using their
performance metrics.

![Player Comparison](docs/screenshots/compare.png)

The comparison results are presented visually to make differences between
players easier to identify.

![Comparison Results](docs/screenshots/compare_results.png)

---

## 🧤 Performance Model

The project evaluates goalkeeper profiles across three main dimensions.

### Shot Stopping

Measures related to a goalkeeper's effectiveness when dealing with shots and
defensive situations.

### Distribution

Measures related to a goalkeeper's ability to contribute to build-up play and
progress the ball.

### Proactivity

Measures related to actions outside the goal line and the goalkeeper's
involvement in defensive space.

The importance of each dimension can be adjusted through the scouting profile.

---

## 🧠 Similarity Engine

The similarity engine is designed to identify goalkeepers with statistical
profiles close to a selected reference player.

The scouting workflow is:

```text
Select goalkeeper
       ↓
Define scouting profile
       ↓
Apply market & performance filters
       ↓
Analyse candidate profiles
       ↓
Calculate similarity
       ↓
Rank candidates
       ↓
Compare players