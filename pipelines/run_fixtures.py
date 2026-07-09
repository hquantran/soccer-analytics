"""Run the fixtures ingestion pipeline locally."""

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
from sources.fixtures import (
    flatten_fixture,
    flatten_fixture_score,
    get_connection,
    load_fixture_scores,
    load_fixtures,
    should_refetch_fixtures,
    update_metadata,
)

ENDPOINT = "fixtures"


def main() -> None:
    config = load_config()
    headers = get_headers(config)
    connection = get_connection()

    print("🏟️ Fetching fixtures...")
    current_endpoint = None
    current_entity_id = None
    started_at = None

    try:
        for league_id in LEAGUE_IDS:
            for season in SEASONS:
                reset_requests_made()
                if not should_refetch_fixtures(league_id, season, connection=connection):
                    print(
                        f"  League {league_id} season {season} recently fetched — skipping"
                    )
                    continue

                started_at = datetime.now(tz=timezone.utc)
                current_endpoint = f"{ENDPOINT}_{season}"
                current_entity_id = league_id
                print(f"\n  Fetching fixtures for league {league_id} season {season}...")

                try:
                    response = fetch_from_api(
                        ENDPOINT,
                        params={"league": league_id, "season": season},
                        headers=headers,
                    )
                except requests.HTTPError as exc:
                    print(f"  ⚠️ API error for league {league_id} season {season}: {exc}")
                    update_metadata(
                        f"{ENDPOINT}_{season}",
                        0,
                        "failed",
                        league_id,
                        started_at=started_at,
                        connection=connection,
                    )
                    continue

                records = response.get("response", [])
                if not records:
                    print("  No fixtures found — skipping")
                    continue

                fixtures = [flatten_fixture(record) for record in records]
                scores = [flatten_fixture_score(record.get("fixture", {}).get("id"), record) for record in records]
                fixture_rows = load_fixtures(fixtures, connection=connection)
                score_rows = load_fixture_scores(scores, connection=connection)
                print(f"  ✅ Loaded {fixture_rows} fixtures")
                print(f"  ✅ Loaded {score_rows} fixture scores")
                update_metadata(
                    f"{ENDPOINT}_{season}",
                    fixture_rows + score_rows,
                    "success",
                    league_id,
                    started_at=started_at,
                    connection=connection,
                )

        print("\n🎉 Fixtures ingestion complete!")

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
