"""Extract + clean player statistics for MVP_LEAGUE_IDS x SEASONS into DuckDB.

Run from the project root with the venv activated:

    python -m pipelines.run_players

To expand scope later, add league IDs to constants.MVP_LEAGUE_IDS (or point
this at constants.LEAGUE_IDS once you're ready for the full backlog) and
re-run — dlt's merge write disposition means re-running is safe and won't
duplicate rows.
"""

import dlt
from pathlib import Path

import duckdb

from constants import MVP_LEAGUE_IDS, SEASONS
from players import players_resource


DB_PATH = Path("api_sports.duckdb")
RAW_CSV_PATH = Path("players_raw.csv")
FEATURES_CSV_PATH = Path("player_features.csv")


def export_players_csv(db_path: Path, csv_path: Path, query: str) -> None:
    if not db_path.exists():
        print(f"Database file {db_path} not found. Skipping CSV export.")
        return

    conn = duckdb.connect(str(db_path))
    try:
        conn.execute(
            f"COPY ({query}) TO '{csv_path}' (HEADER, DELIMITER ',');"
        )
        print(f"Exported to {csv_path}")
    finally:
        conn.close()


def transform_data(db_path: Path) -> None:
    if not db_path.exists():
        print(f"Database file {db_path} not found. Skipping transform.")
        return

    conn = duckdb.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE OR REPLACE TABLE soccer_analytics_data.stg_players AS
            WITH player AS (
                SELECT
                    _dlt_id AS player_row_id,
                    player__id AS player_id,
                    player__name AS name,
                    player__age AS age,
                    player__nationality AS nationality,
                    player__height AS height_cm,
                    player__weight AS weight_kg,
                    player__injured AS injured
                FROM soccer_analytics_data.players_raw
            ),
            stats AS (
                SELECT
                    _dlt_parent_id AS player_row_id,
                    team__id AS team_id,
                    team__name AS team_name,
                    league__id AS league_id,
                    league__season AS season,
                    games__position AS position,
                    games__appearences AS appearances,
                    games__minutes AS minutes,
                    CAST(games__rating AS DOUBLE) AS rating,
                    goals__total AS goals,
                    goals__assists AS assists,
                    shots__total AS shots_total,
                    shots__on AS shots_on_target,
                    passes__total AS passes_total,
                    passes__key AS passes_key,
                    CAST(passes__accuracy AS DOUBLE) AS passes_accuracy_pct,
                    tackles__total AS tackles_total,
                    duels__total AS duels_total,
                    duels__won AS duels_won,
                    dribbles__attempts AS dribbles_attempts,
                    dribbles__success AS dribbles_success,
                    fouls__drawn AS fouls_drawn,
                    fouls__committed AS fouls_committed,
                    cards__yellow AS cards_yellow,
                    cards__red AS cards_red
                FROM soccer_analytics_data.players_raw__statistics
                WHERE games__minutes >= 300
            )
            SELECT
                p.player_id,
                p.name,
                p.age,
                p.nationality,
                p.height_cm,
                p.weight_kg,
                p.injured,
                s.team_id,
                s.team_name,
                s.league_id,
                s.season,
                s.position,
                s.appearances,
                s.minutes,
                s.rating,
                s.goals,
                s.assists,
                s.shots_total,
                s.shots_on_target,
                s.passes_total,
                s.passes_key,
                s.passes_accuracy_pct,
                s.tackles_total,
                s.duels_total,
                s.duels_won,
                s.dribbles_attempts,
                s.dribbles_success,
                s.fouls_drawn,
                s.fouls_committed,
                s.cards_yellow,
                s.cards_red
            FROM player p
            INNER JOIN stats s USING (player_row_id)
            """
        )

        conn.execute(
            """
            CREATE OR REPLACE TABLE soccer_analytics_data.player_features AS
            SELECT
                player_id,
                name,
                age,
                nationality,
                team_id,
                team_name,
                league_id,
                season,
                position,
                minutes,
                rating,
                round(goals * 90.0 / minutes, 3) AS goals_per90,
                round(assists * 90.0 / minutes, 3) AS assists_per90,
                round(passes_key * 90.0 / minutes, 3) AS key_passes_per90,
                round(tackles_total * 90.0 / minutes, 3) AS tackles_per90,
                round(dribbles_success * 90.0 / minutes, 3) AS dribbles_per90,
                passes_accuracy_pct
            FROM soccer_analytics_data.stg_players
            """
        )
        conn.commit()
        print("Transformed raw data into soccer_analytics_data.stg_players and player_features")
    finally:
        conn.close()


def main() -> None:
    pipeline = dlt.pipeline(
        pipeline_name="soccer_analytics",
        destination=dlt.destinations.duckdb(str(DB_PATH)),
        dataset_name="soccer_analytics_data",
    )

    for league_id in MVP_LEAGUE_IDS:
        for season in SEASONS:
            print(f"Loading league={league_id} season={season}...")
            load_info = pipeline.run(players_resource(league_id, season))
            print(load_info)

    export_players_csv(DB_PATH, RAW_CSV_PATH, "SELECT * FROM soccer_analytics_data.players_raw")
    transform_data(DB_PATH)
    export_players_csv(DB_PATH, FEATURES_CSV_PATH, "SELECT * FROM soccer_analytics_data.player_features")


if __name__ == "__main__":
    main()
