"""Load player statistics into DuckDB using local metadata-driven logic."""

from datetime import datetime, timezone

from api_client import fetch_all_pages, reset_requests_made
from config import get_api_settings, get_headers, load_config
from constants import LEAGUE_IDS, SEASONS
from sources.players import (
    flatten_player,
    get_connection,
    load_players,
    should_refetch,
    update_metadata,
)


def main() -> None:
    config = load_config()
    api_settings = get_api_settings(config)
    headers = get_headers(config)

    connection = get_connection()
    print("👤 Fetching players...")

    current_endpoint = None
    current_entity_id = None
    started_at = None

    try:
        for league_id in LEAGUE_IDS:
            for season in SEASONS:
                reset_requests_made()

                endpoint = f"players_{season}"
                if not should_refetch(endpoint, league_id, season, connection=connection):
                    print(
                        f"  League {league_id} season {season} recently fetched — skipping"
                    )
                    continue

                started_at = datetime.now(tz=timezone.utc)
                current_endpoint = endpoint
                current_entity_id = league_id
                print(f"\n  Fetching players for league {league_id} season {season}...")

                records = list(
                    fetch_all_pages(
                        "players",
                        {"league": league_id, "season": season},
                        headers=headers,
                        max_pages=api_settings.get("max_pages"),
                    )
                )

                if not records:
                    print("  No players found — skipping")
                    continue

                players = [flatten_player(record) for record in records]
                print(f"  Got {len(players)} players")

                player_rows = load_players(players, connection=connection)
                print(f"  ✅ Loaded {player_rows} new players")

                update_metadata(
                    endpoint,
                    player_rows,
                    "success",
                    league_id,
                    started_at=started_at,
                    connection=connection,
                )

        print("\n🎉 Players ingestion complete!")

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
        if "request limit" in str(exc).lower() or "quota" in str(exc).lower():
            print("⚠️ API daily request limit reached. Stopping pipeline.")
        else:
            print(f"❌ Error: {exc}")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
