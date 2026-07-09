"""Run the player statistics ingestion pipeline locally."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api_client import fetch_from_api, reset_requests_made
from config import get_headers, load_config
from constants import LEAGUE_IDS, SEASONS
from sources.fixtures import get_connection as get_fixtures_connection
from sources.player_statistics import (
    flatten_player_statistics,
    load_player_statistics,
    update_metadata,
)

ENDPOINT = "fixtures/players"


def get_fixture_ids(league_id: int, season: int, *, connection: Any) -> list[int]:
    result = connection.execute(
        """
        SELECT DISTINCT fixture_id
        FROM football.raw_fixtures
        WHERE league_id = ?
        AND league_season = ?
        AND status_short = 'FT'
        ORDER BY fixture_id
        """,
        [league_id, season],
    ).fetchall()
    return [row[0] for row in result]


def get_ingested_fixture_ids(*, connection: Any) -> set[int]:
    ingested = {
        row[0]
        for row in connection.execute(
            "SELECT DISTINCT fixture_id FROM football.raw_player_statistics"
        ).fetchall()
    }
    skipped = {
        row[0]
        for row in connection.execute(
            """
            SELECT DISTINCT entity_id
            FROM football.ingestion_metadata
            WHERE endpoint = ?
            AND status = 'skipped'
            """,
            [ENDPOINT],
        ).fetchall()
        if row[0] is not None
    }
    return ingested | skipped


def log_skipped_fixtures_bulk(fixture_ids: list[int], *, connection: Any) -> None:
    if not fixture_ids:
        return
    now = datetime.now(tz=timezone.utc)
    rows = [
        (ENDPOINT, fixture_id, now, 0, 0, "skipped", now, None)
        for fixture_id in fixture_ids
    ]
    connection.executemany(
        """
        INSERT INTO football.ingestion_metadata (
            endpoint, entity_id, last_ingested_at, rows_inserted,
            requests_used, status, created_at, started_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    connection.commit()


def main() -> None:
    config = load_config()
    headers = get_headers(config)
    connection = get_fixtures_connection()

    print("👤 Fetching player statistics...")
    current_endpoint = None
    current_entity_id = None
    started_at = None

    try:
        ingested_fixture_ids = get_ingested_fixture_ids(connection=connection)
        print(f"  Already ingested fixture IDs: {len(ingested_fixture_ids)}")

        fixture_rows = connection.execute(
            """
            SELECT DISTINCT league_id, league_season
            FROM football.raw_fixtures
            WHERE status_short = 'FT'
            ORDER BY league_id, league_season
            """
        ).fetchall()

        for league_id, season in fixture_rows:
            reset_requests_made()
            started_at = datetime.now(tz=timezone.utc)
            current_endpoint = f"{ENDPOINT}_{season}"
            current_entity_id = league_id

            all_fixture_ids = get_fixture_ids(league_id, season, connection=connection)
            new_fixture_ids = [fixture_id for fixture_id in all_fixture_ids if fixture_id not in ingested_fixture_ids]

            if not new_fixture_ids:
                print(f"  League {league_id} season {season} — no new fixtures, skipping")
                continue

            print(
                f"\n  Fetching player stats for league {league_id} season {season}: "
                f"{len(new_fixture_ids)} new fixture(s) of {len(all_fixture_ids)} total..."
            )

            all_stats: list[dict[str, Any]] = []
            total_rows = 0
            skipped_fixtures: list[int] = []
            failed_fixtures: list[int] = []

            for fixture_id in new_fixture_ids:
                try:
                    response = fetch_from_api(
                        ENDPOINT,
                        params={"fixture": fixture_id},
                        headers=headers,
                    )
                except requests.HTTPError as exc:
                    print(f"  ⚠️ Fixture {fixture_id} API error (will retry next run): {exc}")
                    failed_fixtures.append(fixture_id)
                    continue

                records = response.get("response", [])
                if not records:
                    skipped_fixtures.append(fixture_id)
                    continue

                for record in records:
                    team = record.get("team", {})
                    team_id = team.get("id")
                    team_name = team.get("name")
                    for player_record in record.get("players", []):
                        player = player_record.get("player", {})
                        statistics = player_record.get("statistics", [{}])[0]
                        all_stats.append(
                            flatten_player_statistics(
                                fixture_id,
                                team_id,
                                team_name,
                                player,
                                statistics,
                            )
                        )

                if len(all_stats) >= 100 * 44:
                    stat_rows = load_player_statistics(all_stats, connection=connection)
                    total_rows += stat_rows
                    ingested_fixture_ids.update(row["fixture_id"] for row in all_stats)
                    print(f"  ✅ Batch loaded {stat_rows} player stats")
                    all_stats = []

            if all_stats:
                stat_rows = load_player_statistics(all_stats, connection=connection)
                total_rows += stat_rows
                ingested_fixture_ids.update(row["fixture_id"] for row in all_stats)
                print(f"  ✅ Loaded {stat_rows} player stats")

            if skipped_fixtures:
                log_skipped_fixtures_bulk(skipped_fixtures, connection=connection)
                ingested_fixture_ids.update(skipped_fixtures)
                print(f"  ⏭️ Logged {len(skipped_fixtures)} fixtures with no API data (won't re-query)")

            if failed_fixtures:
                print(f"  ⚠️ {len(failed_fixtures)} fixture(s) failed due to API errors — will retry next run")

            update_metadata(
                f"{ENDPOINT}_{season}",
                total_rows,
                "success",
                league_id,
                started_at=started_at,
                connection=connection,
            )

        print("\n🎉 Player statistics ingestion complete!")

    except Exception as exc:
        if current_endpoint:
            update_metadata(
                current_endpoint,
                0,
                "failed",
                current_entity_id,
                started_at=started_at,
                connection=connection,
            )
        print(f"❌ Error: {exc}")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
