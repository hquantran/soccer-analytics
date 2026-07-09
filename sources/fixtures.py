"""Local DuckDB fixtures ingestion helpers."""

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
        CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.raw_fixtures (
            fixture_id BIGINT,
            referee TEXT,
            timezone TEXT,
            match_date TIMESTAMP,
            match_timestamp BIGINT,
            first_period_start BIGINT,
            second_period_start BIGINT,
            venue_id BIGINT,
            venue_name TEXT,
            venue_city TEXT,
            status_long TEXT,
            status_short TEXT,
            elapsed_minutes BIGINT,
            extra_time BIGINT,
            league_id BIGINT,
            league_name TEXT,
            league_country TEXT,
            league_season BIGINT,
            league_round TEXT,
            home_team_id BIGINT,
            home_team_name TEXT,
            home_team_winner BOOLEAN,
            away_team_id BIGINT,
            away_team_name TEXT,
            away_team_winner BOOLEAN,
            ingested_at TIMESTAMP
        )
        """
    )
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.raw_fixture_scores (
            fixture_id BIGINT,
            halftime_home BIGINT,
            halftime_away BIGINT,
            fulltime_home BIGINT,
            fulltime_away BIGINT,
            extratime_home BIGINT,
            extratime_away BIGINT,
            penalty_home BIGINT,
            penalty_away BIGINT,
            ingested_at TIMESTAMP
        )
        """
    )
    return conn


def _parse_ts(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


def flatten_fixture(record: dict[str, Any]) -> dict[str, Any]:
    fixture = record.get("fixture", {})
    periods = fixture.get("periods", {})
    venue = fixture.get("venue", {})
    status = fixture.get("status", {})
    league = record.get("league", {})
    teams = record.get("teams", {})
    home = teams.get("home", {})
    away = teams.get("away", {})
    return {
        "fixture_id": fixture.get("id"),
        "referee": fixture.get("referee"),
        "timezone": fixture.get("timezone"),
        "match_date": _parse_ts(fixture.get("date")),
        "match_timestamp": fixture.get("timestamp"),
        "first_period_start": periods.get("first"),
        "second_period_start": periods.get("second"),
        "venue_id": venue.get("id"),
        "venue_name": venue.get("name"),
        "venue_city": venue.get("city"),
        "status_long": status.get("long"),
        "status_short": status.get("short"),
        "elapsed_minutes": status.get("elapsed"),
        "extra_time": status.get("extra"),
        "league_id": league.get("id"),
        "league_name": league.get("name"),
        "league_country": league.get("country"),
        "league_season": league.get("season"),
        "league_round": league.get("round"),
        "home_team_id": home.get("id"),
        "home_team_name": home.get("name"),
        "home_team_winner": home.get("winner"),
        "away_team_id": away.get("id"),
        "away_team_name": away.get("name"),
        "away_team_winner": away.get("winner"),
        "ingested_at": datetime.now(tz=timezone.utc),
    }


def flatten_fixture_score(fixture_id: int, record: dict[str, Any]) -> dict[str, Any]:
    score = record.get("score", {})
    halftime = score.get("halftime", {})
    fulltime = score.get("fulltime", {})
    extratime = score.get("extratime", {})
    penalty = score.get("penalty", {})
    return {
        "fixture_id": fixture_id,
        "halftime_home": halftime.get("home"),
        "halftime_away": halftime.get("away"),
        "fulltime_home": fulltime.get("home"),
        "fulltime_away": fulltime.get("away"),
        "extratime_home": extratime.get("home"),
        "extratime_away": extratime.get("away"),
        "penalty_home": penalty.get("home"),
        "penalty_away": penalty.get("away"),
        "ingested_at": datetime.now(tz=timezone.utc),
    }


def should_refetch_fixtures(league_id: int, season: int, *, connection: Optional[duckdb.DuckDBPyConnection] = None) -> bool:
    conn = connection or get_connection()
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
            [f"fixtures_{season}", league_id],
        ).fetchone()
    except Exception:
        return True

    if not result or not result[0]:
        return True

    last_ingested = result[0]
    if last_ingested.tzinfo is None:
        last_ingested = last_ingested.replace(tzinfo=timezone.utc)

    current_year = datetime.now().year
    days_since = (datetime.now(tz=timezone.utc) - last_ingested).days
    if season >= current_year - 1:
        return days_since >= 1

    stale_fixture = conn.execute(
        f"""
        SELECT 1
        FROM {SCHEMA_NAME}.raw_fixtures
        WHERE league_id = ?
        AND league_season = ?
        AND status_short IN ('NS', 'TBD')
        AND match_date < CURRENT_TIMESTAMP
        LIMIT 1
        """,
        [league_id, season],
    ).fetchone()
    return stale_fixture is not None


def load_fixtures(fixtures: list[dict[str, Any]], *, connection: Optional[duckdb.DuckDBPyConnection] = None) -> int:
    if not fixtures:
        return 0

    conn = connection or get_connection()
    rows = [
        (
            fixture.get("fixture_id"),
            fixture.get("referee"),
            fixture.get("timezone"),
            fixture.get("match_date"),
            fixture.get("match_timestamp"),
            fixture.get("first_period_start"),
            fixture.get("second_period_start"),
            fixture.get("venue_id"),
            fixture.get("venue_name"),
            fixture.get("venue_city"),
            fixture.get("status_long"),
            fixture.get("status_short"),
            fixture.get("elapsed_minutes"),
            fixture.get("extra_time"),
            fixture.get("league_id"),
            fixture.get("league_name"),
            fixture.get("league_country"),
            fixture.get("league_season"),
            fixture.get("league_round"),
            fixture.get("home_team_id"),
            fixture.get("home_team_name"),
            fixture.get("home_team_winner"),
            fixture.get("away_team_id"),
            fixture.get("away_team_name"),
            fixture.get("away_team_winner"),
            fixture.get("ingested_at"),
        )
        for fixture in fixtures
        if fixture.get("fixture_id") is not None
    ]
    conn.executemany(
        f"""
        INSERT INTO {SCHEMA_NAME}.raw_fixtures (
            fixture_id, referee, timezone, match_date, match_timestamp,
            first_period_start, second_period_start, venue_id, venue_name,
            venue_city, status_long, status_short, elapsed_minutes, extra_time,
            league_id, league_name, league_country, league_season, league_round,
            home_team_id, home_team_name, home_team_winner, away_team_id,
            away_team_name, away_team_winner, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def load_fixture_scores(scores: list[dict[str, Any]], *, connection: Optional[duckdb.DuckDBPyConnection] = None) -> int:
    if not scores:
        return 0

    valid_scores = [score for score in scores if score.get("fixture_id")]
    if not valid_scores:
        return 0

    conn = connection or get_connection()
    fixture_ids = [score.get("fixture_id") for score in valid_scores if score.get("fixture_id") is not None]
    if fixture_ids:
        conn.execute(
            f"DELETE FROM {SCHEMA_NAME}.raw_fixture_scores WHERE fixture_id IN ({', '.join('?' for _ in fixture_ids)})",
            fixture_ids,
        )

    rows = [
        (
            score.get("fixture_id"),
            score.get("halftime_home"),
            score.get("halftime_away"),
            score.get("fulltime_home"),
            score.get("fulltime_away"),
            score.get("extratime_home"),
            score.get("extratime_away"),
            score.get("penalty_home"),
            score.get("penalty_away"),
            score.get("ingested_at"),
        )
        for score in valid_scores
    ]
    conn.executemany(
        f"""
        INSERT INTO {SCHEMA_NAME}.raw_fixture_scores (
            fixture_id, halftime_home, halftime_away, fulltime_home,
            fulltime_away, extratime_home, extratime_away, penalty_home,
            penalty_away, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    return len(valid_scores)


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
