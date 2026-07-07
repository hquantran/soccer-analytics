"""League metadata and season coverage source for dlt."""

from datetime import date, datetime, timezone
from typing import Optional

import dlt

from api_client import fetch_from_api

ENDPOINT = "leagues"


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _flatten_league(record: dict) -> dict:
    league = record.get("league", {})
    country = record.get("country", {})
    return {
        "league_id": league.get("id"),
        "league_name": league.get("name"),
        "league_type": league.get("type"),
        "league_logo_url": league.get("logo"),
        "country_name": country.get("name"),
        "country_code": country.get("code"),
        "country_flag_url": country.get("flag"),
        "ingested_at": datetime.now(tz=timezone.utc),
    }


def _flatten_league_season(league_id: int, season: dict) -> dict:
    coverage = season.get("coverage", {})
    fixtures = coverage.get("fixtures", {})
    return {
        "league_id": league_id,
        "season_year": season.get("year"),
        "season_start": _parse_date(season.get("start")),
        "season_end": _parse_date(season.get("end")),
        "is_current_season": season.get("current"),
        "coverage_fixtures_events": fixtures.get("events"),
        "coverage_fixtures_lineups": fixtures.get("lineups"),
        "coverage_standings": coverage.get("standings"),
        "coverage_players": coverage.get("players"),
        "coverage_top_scorers": coverage.get("top_scorers"),
        "coverage_injuries": coverage.get("injuries"),
        "coverage_predictions": coverage.get("predictions"),
        "coverage_odds": coverage.get("odds"),
        "ingested_at": datetime.now(tz=timezone.utc),
    }


@dlt.source(name="football_leagues")
def leagues_source(headers: dict, league_id: int, seasons: Optional[list[int]] = None):
    return [
        leagues_resource(league_id=league_id, headers=headers),
        league_seasons_resource(league_id=league_id, headers=headers, seasons=seasons),
    ]


@dlt.resource(name="raw_leagues", write_disposition="merge", primary_key="league_id")
def leagues_resource(league_id: int, *, headers: dict):
    """Yield league metadata for one league id."""
    state = dlt.current.resource_state()
    now = datetime.now(tz=timezone.utc)
    state_key = f"last_ingested_at_{league_id}"
    last_ingested_at = state.get(state_key)

    if last_ingested_at and (now - last_ingested_at).days < 365:
        print(f"  League {league_id} recently fetched — skipping")
        return

    print(f"🏆 Fetching league {league_id}...")
    response = fetch_from_api(ENDPOINT, params={"id": league_id}, headers=headers)
    records = response.get("response", [])

    for record in records:
        yield _flatten_league(record)

    state[state_key] = now


@dlt.resource(
    name="raw_league_seasons",
    write_disposition="merge",
    primary_key=["league_id", "season_year"],
)
def league_seasons_resource(
    league_id: int,
    *,
    headers: dict,
    seasons: Optional[list[int]] = None,
):
    """Yield league season coverage rows for one league id."""
    state = dlt.current.resource_state()
    now = datetime.now(tz=timezone.utc)
    state_key = f"last_ingested_at_{league_id}_seasons"
    last_ingested_at = state.get(state_key)

    if last_ingested_at and (now - last_ingested_at).days < 365:
        print(f"  League {league_id} seasons recently fetched — skipping")
        return

    print(f"📅 Fetching league {league_id} seasons...")
    response = fetch_from_api(ENDPOINT, params={"id": league_id}, headers=headers)
    records = response.get("response", [])

    for record in records:
        league_id_value = record.get("league", {}).get("id")
        for season in record.get("seasons", []):
            season_year = season.get("year")
            if seasons is not None and season_year not in seasons:
                continue
            yield _flatten_league_season(league_id_value, season)

    state[state_key] = now
