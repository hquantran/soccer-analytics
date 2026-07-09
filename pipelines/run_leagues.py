"""Run the league ingestion pipeline."""

import sys
from pathlib import Path

import dlt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_headers, load_config
from constants import LEAGUE_IDS, SEASONS
from sources.leagues import leagues_source


def main() -> None:
    config = load_config()
    headers = get_headers(config)

    pipeline = dlt.pipeline(
        pipeline_name="api_sports",
        destination="duckdb",
        dataset_name="football",
    )

    for league_id in LEAGUE_IDS:
        try:
            info = pipeline.run(
                leagues_source(headers=headers, league_id=league_id, seasons=SEASONS)
            )
            print(info)
        except Exception as exc:
            if "request limit" in str(exc).lower() or "quota" in str(exc).lower():
                print("⚠️ API daily request limit reached. Stopping pipeline.")
                break
            raise


if __name__ == "__main__":
    main()
