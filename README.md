# Soccer Scouting & Player Analytics Platform

## The Business Problem

Professional soccer clubs need to evaluate players across leagues, teams, and seasons when making scouting and recruitment decisions. The challenge is not simply having player statistics available. It is turning large amounts of raw performance data into a consistent dataset that allows analysts to quickly compare players, understand player profiles, and identify potential talent.

A typical scouting workflow can require analysts to collect data from different competitions, work with inconsistent statistics, account for differences in playing time, and manually compare players across positions and teams.

We built this project to make that process more systematic and data-driven.

### Business Question

> How can we turn large-scale soccer performance data into an analysis-ready scouting tool that helps analysts identify, compare, and discover players more efficiently?

---

## Our Solution

We built an end-to-end soccer analytics and scouting platform that automatically collects player statistics from **API-Football**, transforms the raw data into a structured analytical dataset, and delivers the results through an interactive **Streamlit** application.

The platform combines:

* Automated data collection and transformation
* Exploratory data analysis
* Standardized player performance metrics
* Player profiles and comparisons
* Player discovery through a recommendation system
* Interactive scouting dashboards

Instead of treating raw API data as the final product, we designed the workflow around the types of questions a scouting or analytics team would need to answer.

### What Users Can Do

The platform allows users to:

* Explore top-performing players
* View individual player profiles
* Compare players across performance metrics
* Analyze players across teams, leagues, and seasons
* Examine player distributions and performance patterns
* Discover players with similar performance profiles
* Use standardized per-90 statistics for more meaningful comparisons

---

# From Raw Data to Scouting Decisions

The project follows an end-to-end workflow:

```text
API-Football
     │
     ▼
Data Collection
     │
     ▼
dlt + DuckDB
     │
     ▼
Raw Player & Statistics Data
     │
     ▼
dbt Transformation
     │
     ▼
Analysis-Ready Player Features
     │
     ├───────────────┐
     ▼               ▼
Exploratory       Recommendation
Analysis          System
     │               │
     └───────┬───────┘
             ▼
        Streamlit
        Application
             │
             ▼
   Player Analysis & Scouting
```

---

# 1. Data Collection

We collected player and season statistics from **API-Football** across five major European leagues:

| League         | API-Football ID |
| -------------- | --------------: |
| Premier League |              39 |
| Ligue 1        |              61 |
| Bundesliga     |              78 |
| Serie A        |             135 |
| La Liga        |             140 |

The dataset covers seasons from **2020 through 2026**, resulting in:

* **5 leagues**
* **7 seasons**
* **35 league-season combinations**

The ingestion workflow was designed to handle the challenges of working with a paginated sports API, including:

* API pagination
* Request pacing
* Retry handling
* Load tracking
* Nested player statistics
* Incremental data loading

### Why This Matters

Automating collection makes it possible to build a repeatable scouting dataset instead of relying on manually downloaded or manually maintained statistics.

---

# 2. ELT Pipeline

The project uses an **ELT architecture** built with Python, `dlt`, DuckDB, and dbt.

### Extract & Load

The ingestion process retrieves player data from API-Football and loads the raw responses into DuckDB using `dlt`.

The raw data contains both player-level information and nested statistics associated with a player's team, league, and season.

This produces raw tables including:

* `players_raw`
* `players_raw__statistics`

The raw dataset contains:

* Player information
* Team
* League
* Season
* Games played
* Minutes
* Goals
* Assists
* Shots
* Passes
* Tackles
* Duels
* Dribbles
* Fouls
* Cards
* Penalties

### Transform

After loading the raw API data, dbt transforms it into an analysis-ready player dataset.

The transformation process includes:

* Converting height and weight into numeric values
* Converting ratings and pass accuracy into numeric fields
* Renaming API fields into more consistent analytical names
* Standardizing player positions
* Joining player profiles with performance statistics
* Filtering players with fewer than 300 minutes
* Creating player-season records
* Calculating standardized performance metrics

The **300-minute threshold** helps prevent players with very limited playing time from distorting performance comparisons.

---

# 3. Exploratory Data Analysis

Before using the data for player analysis and recommendations, we conducted exploratory data analysis to understand the composition and patterns of the player dataset.

The analysis examined:

### Players by Position

We examined the **number of players represented in each position** to understand the composition of the overall player pool.

This provides context for player comparisons and helps identify how the dataset is distributed across different positions.

### Minutes Played

We analyzed the distribution of minutes played to understand how playing time varies across the player pool.

### Missing Values

We examined missing values across features to identify fields that required attention during the transformation process.

### Goals vs. Total Shots

We compared total shots with goals, using player position as a dimension, to explore scoring patterns and identify unusual observations.

Together, these analyses helped us understand the player population and performance data before building the downstream scouting workflows.

---

# 4. Analysis-Ready Player Dataset

After transformation, the project produces a structured player-season dataset containing **12,731 analysis-ready records**.

Each record represents a player's performance for a specific:

* Player
* Team
* League
* Season

A player can therefore appear multiple times when they play across different seasons, teams, or competitions.

### Standardized Performance Metrics

To make comparisons more meaningful, we calculate several performance metrics on a per-90-minute basis:

| Metric          | Definition                         |
| --------------- | ---------------------------------- |
| Goals / 90      | Goals × 90 / Minutes               |
| Assists / 90    | Assists × 90 / Minutes             |
| Key Passes / 90 | Key Passes × 90 / Minutes          |
| Tackles / 90    | Total Tackles × 90 / Minutes       |
| Dribbles / 90   | Successful Dribbles × 90 / Minutes |

The analysis-ready dataset also includes information such as:

* Player position
* Team
* League
* Season
* Minutes
* Rating
* Pass accuracy
* Goals
* Assists
* Shots
* Tackles
* Dribbles
* Other performance statistics

### Why Per-90 Metrics?

Raw totals can favor players simply because they played more minutes.

Per-90 metrics provide a more consistent way to compare players with different amounts of playing time, making them more useful for player evaluation and discovery.

---

# 5. Player Analysis & Recommendation System

Beyond simply displaying statistics, the project includes a **player recommendation system** designed to support player discovery.

The recommendation workflow uses player performance characteristics to identify players with similar profiles.

This creates a more practical scouting workflow:

```text
Known Player
     │
     ▼
Analyze Performance Profile
     │
     ▼
Find Similar Player Profiles
     │
     ▼
Explore Recommended Players
     │
     ▼
Further Scouting / Evaluation
```

For example, instead of searching through thousands of players manually, an analyst can start with a player whose profile fits a particular role and use the recommendation system to discover other players with similar characteristics.

The recommendation system therefore extends the platform from **player reporting** into **player discovery**.

---

# 6. Streamlit Scouting Application

The analysis and recommendation workflows are delivered through an interactive Streamlit application.

The application is designed to make the underlying data easier to explore without requiring users to interact directly with the database or transformation pipeline.

### Top Players

Users can explore players based on their performance metrics and identify high-performing players within the available dataset.

### Player Profile

Users can examine an individual player's:

* Performance statistics
* Per-90 metrics
* Team
* League
* Season
* Position
* Playing time

### Player Comparison

Users can compare players across relevant performance metrics to better understand differences between player profiles.

### Player Discovery

The recommendation workflow allows users to move from a known player to other players with similar performance characteristics.

---

# 7. Business Impact

The project demonstrates how a large and complex sports dataset can be converted into a repeatable scouting and player analysis workflow.

### Scale

The platform processes data across:

* **5 major European leagues**
* **35 league-season combinations**
* **2020–2026 seasons**
* **26,132 raw player records**
* **27,412 raw player-statistic records**
* **12,731 analysis-ready player-season records**

### More Consistent Player Evaluation

Standardized player-season records and per-90 metrics make it easier to compare players across different levels of playing time, teams, leagues, and seasons.

### Faster Analysis Workflow

The automated pipeline creates a repeatable path from:

```text
Data Collection
      ↓
Data Transformation
      ↓
Feature Engineering
      ↓
Exploratory Analysis
      ↓
Player Recommendations
      ↓
Interactive Scouting
```

This reduces the amount of manual work required to move from raw player statistics to analysis.

### From Reporting to Discovery

The project goes beyond displaying player statistics. The recommendation system allows analysts to use existing player profiles as a starting point for discovering other players worth investigating.

---

# 8. Technology Stack

| Area            | Technologies                       |
| --------------- | ---------------------------------- |
| Data Source     | API-Football                       |
| Programming     | Python                             |
| Data Ingestion  | dlt                                |
| Data Warehouse  | DuckDB                             |
| Transformation  | dbt                                |
| Analysis        | Pandas, NumPy, Seaborn, Matplotlib |
| Application     | Streamlit                          |
| Version Control | Git / GitHub                       |

---

# 9. Project Architecture

```text
soccer-analytics/
│
├── config/
│   └── configuration files
│
├── ingestion/
│   ├── api_client.py
│   └── players.py
│
├── models/
│   ├── staging/
│   │   └── stg_players.sql
│   │
│   ├── dimensions/
│   ├── facts/
│   ├── marts/
│   │
│   └── bi/
│       └── bi_player_seasons.sql
│
├── dashboard/
│   └── Streamlit application
│
├── rec_system/
│   └── player recommendation workflow
│
├── tests/
│   └── data quality tests
│
├── data/
│   ├── warehouse/
│   │   └── api_sports.duckdb
│   │
│   └── exports/
│
├── dbt_project.yml
├── profiles.yml
└── run_players.py
```

---

# 10. Running the Project

## 1. Clone the Repository

```bash
git clone https://github.com/hquantran/soccer-analytics.git
cd soccer-analytics
```

## 2. Install Dependencies

Install the required Python and dbt dependencies according to the project environment.

## 3. Configure API Access

Add the required API-Football credentials to the project configuration.

## 4. Run the Data Pipeline

```bash
python run_players.py
```

This runs the player data ingestion process and loads the raw data into DuckDB.

## 5. Run dbt

Run the data quality tests:

```bash
dbt test
```

Then build the transformed models:

```bash
dbt run
```

## 6. Launch the Streamlit Application

```bash
streamlit run dashboard/app.py
```

The Streamlit application provides the interactive player analysis and scouting interface.

---

# 11. Team Contributions

This was a collaborative project where each team member focused on different parts of the analytics workflow.

### Ha Tran

**ELT Pipeline · Exploratory Data Analysis · Streamlit**

* Built the end-to-end ELT pipeline using Python, dlt, DuckDB, and dbt
* Built the data transformation workflow from raw API data to analysis-ready player features
* Conducted exploratory data analysis to understand player distributions and performance patterns
* Built the Streamlit application
* Optimized the application to run faster and provide a more responsive user experience

### Quan

**Recommendation System · BI Layer · Streamlit**

* Built the player recommendation system
* Built the BI/presentation layer for the analytical outputs
* Contributed to the Streamlit application

---

# 12. Key Takeaway

This project demonstrates how data engineering, analytics, and interactive applications can work together to solve a practical business problem.

Rather than building a dashboard around a static dataset, we built a repeatable pipeline that:

**collects data → structures it → analyzes it → identifies similar players → delivers insights through an interactive scouting application.**

The result is a scalable foundation for exploring player performance and supporting more efficient, data-driven soccer scouting and player discovery.

