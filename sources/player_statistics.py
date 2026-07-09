"""Local DuckDB player statistics ingestion helpers."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import duckdb

from api_client import get_requests_made

DB_PATH = Path(__file__).resolve().parents[1] / "api_sports.duckdb"
SCHEMA_NAME = "football"


def get_connection() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(DB_PATH))
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}")
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.ingestion_metadata (
            endpoint TEXT,
            entity_id BIGINT,
            last_ingested_at TIMESTAMP,
            rows_inserted BIGINT,
            requests_used BIGINT,
            status TEXT,
            created_at TIMESTAMP,
            started_at TIMESTAMP
        )
        """
    )
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.raw_player_statistics (
            fixture_id BIGINT,
            team_id BIGINT,
            team_name TEXT,
            player_id BIGINT,
            player_name TEXT,
            minutes_played BIGINT,
            jersey_number BIGINT,
            position TEXT,
            rating TEXT,
            is_captain BOOLEAN,
            is_substitute BOOLEAN,
            offsides BIGINT,
            shots_total BIGINT,
            shots_on_target BIGINT,
            goals_scored BIGINT,
            goals_conceded BIGINT,
            assists BIGINT,
            saves BIGINT,
            passes_total BIGINT,
            passes_key BIGINT,
            pass_accuracy TEXT,
            tackles_total BIGINT,
            blocks BIGINT,
            interceptions BIGINT,
            duels_total BIGINT,
            duels_won BIGINT,
            dribbles_attempted BIGINT,
            dribbles_success BIGINT,
            dribbles_past BIGINT,
            fouls_drawn BIGINT,
            fouls_committed BIGINT,
            yellow_cards BIGINT,
            red_cards BIGINT,
            penalty_won BIGINT,
            penalty_committed BIGINT,
            penalty_scored BIGINT,
            penalty_missed BIGINT,
            penalty_saved BIGINT,
            ingested_at TIMESTAMP
        )
        """
    )
    return conn


def flatten_player_statistics(
    fixture_id: int,
    team_id: int,
    team_name: str,
    player: dict[str, Any],
    stats: dict[str, Any],
) -> dict[str, Any]:
    games = stats.get("games", {})
    shots = stats.get("shots", {})
    goals = stats.get("goals", {})
    passes = stats.get("passes", {})
    tackles = stats.get("tackles", {})
    duels = stats.get("duels", {})
    dribbles = stats.get("dribbles", {})
    fouls = stats.get("fouls", {})
    cards = stats.get("cards", {})
    penalty = stats.get("penalty", {})

    return {
        "fixture_id": fixture_id,
        "team_id": team_id,
        "team_name": team_name,
        "player_id": player.get("id"),
        "player_name": player.get("name"),
        "minutes_played": games.get("minutes"),
        "jersey_number": games.get("number"),
        "position": games.get("position"),
        "rating": str(games.get("rating")) if games.get("rating") else None,
        "is_captain": games.get("captain"),
        "is_substitute": games.get("substitute"),
        "offsides": stats.get("offsides"),
        "shots_total": shots.get("total"),
        "shots_on_target": shots.get("on"),
        "goals_scored": goals.get("total"),
        "goals_conceded": goals.get("conceded"),
        "assists": goals.get("assists"),
        "saves": goals.get("saves"),
        "passes_total": passes.get("total"),
        "passes_key": passes.get("key"),
        "pass_accuracy": str(passes.get("accuracy")) if passes.get("accuracy") else None,
        "tackles_total": tackles.get("total"),
        "blocks": tackles.get("blocks"),
        "interceptions": tackles.get("interceptions"),
        "duels_total": duels.get("total"),
        "duels_won": duels.get("won"),
        "dribbles_attempted": dribbles.get("attempts"),
        "dribbles_success": dribbles.get("success"),
        "dribbles_past": dribbles.get("past"),
        "fouls_drawn": fouls.get("drawn"),
        "fouls_committed": fouls.get("committed"),
        "yellow_cards": cards.get("yellow"),
        "red_cards": cards.get("red"),
        "penalty_won": penalty.get("won"),
        "penalty_committed": penalty.get("commited"),
        "penalty_scored": penalty.get("scored"),
        "penalty_missed": penalty.get("missed"),
        "penalty_saved": penalty.get("saved"),
        "ingested_at": datetime.now(tz=timezone.utc),
    }


def load_player_statistics(
    stats: list[dict[str, Any]],
    *,
    connection: Optional[duckdb.DuckDBPyConnection] = None,
) -> int:
    if not stats:
        return 0

    conn = connection or get_connection()
    rows = [
        (
            row.get("fixture_id"),
            row.get("team_id"),
            row.get("team_name"),
            row.get("player_id"),
            row.get("player_name"),
            row.get("minutes_played"),
            row.get("jersey_number"),
            row.get("position"),
            row.get("rating"),
            row.get("is_captain"),
            row.get("is_substitute"),
            row.get("offsides"),
            row.get("shots_total"),
            row.get("shots_on_target"),
            row.get("goals_scored"),
            row.get("goals_conceded"),
            row.get("assists"),
            row.get("saves"),
            row.get("passes_total"),
            row.get("passes_key"),
            row.get("pass_accuracy"),
            row.get("tackles_total"),
            row.get("blocks"),
            row.get("interceptions"),
            row.get("duels_total"),
            row.get("duels_won"),
            row.get("dribbles_attempted"),
            row.get("dribbles_success"),
            row.get("dribbles_past"),
            row.get("fouls_drawn"),
            row.get("fouls_committed"),
            row.get("yellow_cards"),
            row.get("red_cards"),
            row.get("penalty_won"),
            row.get("penalty_committed"),
            row.get("penalty_scored"),
            row.get("penalty_missed"),
            row.get("penalty_saved"),
            row.get("ingested_at"),
        )
        for row in stats
    ]

    conn.executemany(
        f"""
        INSERT OR REPLACE INTO {SCHEMA_NAME}.raw_player_statistics (
            fixture_id, team_id, team_name, player_id, player_name, minutes_played,
            jersey_number, position, rating, is_captain, is_substitute, offsides,
            shots_total, shots_on_target, goals_scored, goals_conceded, assists,
            saves, passes_total, passes_key, pass_accuracy, tackles_total, blocks,
            interceptions, duels_total, duels_won, dribbles_attempted,
            dribbles_success, dribbles_past, fouls_drawn, fouls_committed,
            yellow_cards, red_cards, penalty_won, penalty_committed,
            penalty_scored, penalty_missed, penalty_saved, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def update_metadata(
    endpoint: str,
    rows_inserted: int,
    status: str,
    entity_id: Optional[int] = None,
    *,
    started_at: Optional[datetime] = None,
    connection: Optional[duckdb.DuckDBPyConnection] = None,
) -> None:
    conn = connection or get_connection()
    now = datetime.now(tz=timezone.utc)
    conn.execute(
        f"""
        INSERT INTO {SCHEMA_NAME}.ingestion_metadata (
            endpoint, entity_id, last_ingested_at, rows_inserted,
            requests_used, status, created_at, started_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            endpoint,
            entity_id,
            now,
            rows_inserted,
            get_requests_made(),
            status,
            now,
            started_at,
        ],
    )
    conn.commit()
