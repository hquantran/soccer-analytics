# Soccer analytics ELT pipeline

This project loads player data from the API-Football API into DuckDB via dlt, then applies dbt staging and mart SQL logic.

## Security note

The API-Football key currently in `config.toml` was exposed outside the repo at some point. Even though the file is gitignored, it should be rotated immediately in the API-Football dashboard and replaced in the local config file. Do not commit secrets to the repository.

## Main flow

1. `run_players.py` loads the API data into the `soccer_analytics_data` schema in DuckDB.
2. `dbt run` builds the `stg_players` and `player_features` models.
3. `export_sample.py` exports a sample of the final `player_features` table to Excel.

The configured target leagues are the Premier League, Ligue 1, Bundesliga, Serie A,
and La Liga. The loader is configured for seasons 2020 through 2026 and has no
pagination limit, so it fetches every page returned by the API. It also stops
when the API reports only five requests remaining, protecting the end of the
daily quota. Adjust `quota_reserve` in `config.toml` if needed.

## Typical commands

```bash
python run_players.py
dbt test --project-dir . --profiles-dir .
python export_sample.py --limit 20
```

Use Python 3.13 for dbt in this project. On Windows, run the commands from the
project root with the same environment that contains `dbt-duckdb`. The load makes
35 API league-season requests and respects the configured six-second pause between
requests, so the initial run takes several minutes and may consume API quota.
