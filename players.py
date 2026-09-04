"""dlt resource: extract player profiles + season statistics from API-Football.

This is the E+L half of an ELT pipeline. It lands each /players response item
as close to its raw shape as dlt allows — no filtering, no derived metrics.
dlt auto-normalizes the nested JSON into related tables on load:

    players_raw               -- one row per player (bio fields, flattened
                                  from the "player" object: player__id,
                                  player__name, player__age, etc.)
    players_raw__statistics   -- one row per team/competition stint, linked
                                  back to players_raw via _dlt_parent_id

All cleaning (minutes filter, per-90 calculations) happens afterward, in SQL,
in transform/models/ (dbt) — not here.
"""

import dlt

from api_client import fetch_all_pages
from config import get_headers, load_config


@dlt.resource(
    name="players_raw",
    write_disposition="merge",
    # Preserve one row per player per season instead of overwriting previous
    # seasons when the same player ID appears again in a new year.
    primary_key=["player__id", "league__season"],
    columns={
        "dribbles__past": {"data_type": "bigint"},
        "games__number": {"data_type": "bigint"},
        "penalty__commited": {"data_type": "bigint"},
        "penalty__won": {"data_type": "bigint"},
        "league__id": {"data_type": "bigint"},
        "league__season": {"data_type": "bigint"},
    },
)
def players_resource(league_id: int, season: int):
    """Yield raw /players API items, tagged with season metadata for history."""
    config = load_config()
    headers = get_headers(config)

    for item in fetch_all_pages(
        "players",
        {"league": league_id, "season": season},
        headers=headers,
    ):
        item["league__id"] = league_id
        item["league__season"] = season
        yield item
