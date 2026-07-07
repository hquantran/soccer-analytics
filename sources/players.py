"""Local DuckDB player ingestion helpers."""

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
        CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.raw_players (
            player_id BIGINT,
            player_name TEXT,
            firstname TEXT,
            lastname TEXT,
            age BIGINT,
            birth_date DATE,
            birth_place TEXT,
            birth_country TEXT,
            nationality TEXT,
            height TEXT,
            weight TEXT,
            photo_url TEXT,
            ingested_at TIMESTAMP
        )
        """
    )
    return conn


def should_refetch(endpoint: str, league_id: int, season: int, *, connection: Optional[duckdb.DuckDBPyConnection] = None) -> bool:
    conn = connection or get_connection()
    if conn is not None and connection is None:
        conn.close()
    endpoint_name = f"{endpoint}_{season}"
    try:
        result = conn.execute(
            f"""
            SELECT last_ingested_at
            FROM {SCHEMA_NAME}.ingestion_metadata
            WHERE endpoint = ?
            AND entity_id = ?
            AND status IN ('success', 'skipped')
            ORDER BY last_ingested_at DESC
            LIMIT 1
            """,
            [endpoint_name, league_id],
        ).fetchone()
    except Exception:
        return True

    if not result or not result[0]:
        return True

    last_ingested = result[0]
    if last_ingested.tzinfo is None:
        last_ingested = last_ingested.replace(tzinfo=timezone.utc)

    days_since = (datetime.now(tz=timezone.utc) - last_ingested).days
    return days_since >= 365


def flatten_player(record: dict[str, Any]) -> dict[str, Any]:
    player = record.get("player", {})
    birth = player.get("birth", {})
    birth_date_str = birth.get("date")
    birth_date = None
    if birth_date_str:
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except Exception:
            birth_date = None

    return {
        "player_id": player.get("id"),
        "player_name": player.get("name"),
        "firstname": player.get("firstname"),
        "lastname": player.get("lastname"),
        "age": player.get("age"),
        "birth_date": birth_date,
        "birth_place": birth.get("place"),
        "birth_country": birth.get("country"),
        "nationality": player.get("nationality"),
        "height": player.get("height"),
        "weight": player.get("weight"),
        "photo_url": player.get("photo"),
        "ingested_at": datetime.now(tz=timezone.utc),
    }


def load_players(players: list[dict[str, Any]], *, connection: Optional[duckdb.DuckDBPyConnection] = None) -> int:
    if not players:
        return 0

    conn = connection or get_connection()
    existing_ids = {
        row[0]
        for row in conn.execute(f"SELECT player_id FROM {SCHEMA_NAME}.raw_players").fetchall()
    }

    new_players = [
        player for player in players if player.get("player_id") and player.get("player_id") not in existing_ids
    ]
    if not new_players:
        print("  No new players to load")
        return 0

    columns = [
        "player_id",
        "player_name",
        "firstname",
        "lastname",
        "age",
        "birth_date",
        "birth_place",
        "birth_country",
        "nationality",
        "height",
        "weight",
        "photo_url",
        "ingested_at",
    ]
    values = [tuple(player.get(column) for column in columns) for player in new_players]
    conn.executemany(
        f"""
        INSERT INTO {SCHEMA_NAME}.raw_players (
            player_id, player_name, firstname, lastname, age, birth_date,
            birth_place, birth_country, nationality, height, weight,
            photo_url, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )
    return len(new_players)


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
