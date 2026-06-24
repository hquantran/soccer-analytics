"""Load country metadata into DuckDB via dlt."""

import dlt

from config import get_headers, load_config
from sources.countries import countries_source


def main() -> None:
    config = load_config()
    headers = get_headers(config)

    pipeline = dlt.pipeline(
        pipeline_name="api_sports",
        destination="duckdb",
        dataset_name="football",
    )

    info = pipeline.run(
        countries_source(headers=headers)
    )
    print(info)


if __name__ == "__main__":
    main()
