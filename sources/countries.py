import dlt
from datetime import datetime, timezone
from typing import Optional

from api_client import fetch_from_api

ENDPOINT = "countries"

@dlt.source(name="football_countries")
def countries_source(headers: dict, country_name: Optional[str] = None):
    return countries_resource(headers=headers, country_name=country_name)

@dlt.resource(name="raw_countries", write_disposition="append", primary_key="country_name")
def countries_resource(headers: dict, country_name: Optional[str] = None):
    print("🌍 Fetching countries...")
    
    state = dlt.current.resource_state()
    state_key = country_name or "__all__"
    if state.get(state_key, False):
        print(f"  Countries already ingested for query {state_key} — skipping")
        return

    params = {}
    if country_name:
        params["name"] = country_name

    response = fetch_from_api(ENDPOINT, params=params, headers=headers)
    records = response.get("response", [])
    print(f"  Got {len(records)} countries from API")

    for record in records:
        yield {
            "country_name": record.get("name"),
            "country_code": record.get("code"),
            "country_flag_url": record.get("flag"),
            "ingested_at": datetime.now(tz=timezone.utc),
        }
        
    state[state_key] = True