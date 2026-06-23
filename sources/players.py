"""Player statistics source for dlt."""

from typing import Optional

import dlt

from api_client import fetch_all_pages


@dlt.resource(name="players", write_disposition="replace")
def players(
    team: int,
    season: int,
    *,
    headers: dict,
    max_pages: Optional[int] = None,
):
    """Yield player records (with nested statistics) for one team and season."""
    params = {"team": team, "season": season}
    yield from fetch_all_pages(
        "players",
        params,
        headers=headers,
        max_pages=max_pages,
    )
