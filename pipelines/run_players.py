"""Load player statistics into DuckDB via dlt."""

import dlt

from config import get_api_settings, get_headers, load_config
from sources.players import players


def main() -> None:
    config = load_config()
    api_settings = get_api_settings(config)
    query = config.get("query", {})

    team = int(query["team"])
    season = int(query["season"])
    headers = get_headers(config)

    pipeline = dlt.pipeline(
        pipeline_name="api_sports",
        destination="duckdb",
        dataset_name="football",
    )

    info = pipeline.run(
        players(
            team=team,
            season=season,
            headers=headers,
            max_pages=api_settings.get("max_pages"),
        )
    )
    print(info)


if __name__ == "__main__":
    main()
