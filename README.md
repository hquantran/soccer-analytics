# Soccer analytics ELT pipeline

This project extracts player and season-statistics data from the API-Football API,
lands the response in DuckDB with `dlt`, transforms it with dbt, and exports
analysis-ready player features. It is an **ELT** pipeline:

1. **Extract and load:** Python requests the API and `dlt` writes the response in
	 its raw, nested shape to DuckDB.
2. **Transform:** dbt reads the raw tables, cleans and joins them, filters out
	 low-minute rows, and calculates per-90 metrics.
3. **Export:** Python writes CSV and Excel extracts from the loaded or transformed
	 relations.

## Important security note

Never commit an API key. The local `config.toml` contains a credential and must
remain ignored. Rotate the key in the API-Football dashboard if it has ever been
shared or exposed, then put the replacement only in the local file. Use
`config.example.toml` as the safe template.

## End-to-end flow

```text
API-Football /players endpoint
				|
				v
api_client.py  (HTTP, pagination, retries, pacing, quota protection)
				|
				v
players.py + dlt
				|
				v
api_sports.duckdb
				|
				+--> soccer_analytics_data_staging (temporary latest load package)
				|
				+--> soccer_analytics_data (merged historical raw data)
					players_raw                  one row per player response item
					players_raw__statistics      one row per player/team/competition stint
				|
				|  sources.yml tells dbt where these two tables are
				v
models/staging/stg_players.sql (view in main)
	join player profile to statistics
	clean height/weight and position
	keep rows with at least 300 minutes
				|
				v
models/marts/player_features.sql (table in main)
	calculate goals, assists, key passes, tackles, and dribbles per 90
				|
				+--> player_features.csv
				+--> export_sample.py --> player_features_sample.xlsx
```

The configured scope is five leagues and seasons 2020 through 2026 inclusive:

| League | API-Football ID |
| --- | ---: |
| Premier League | 39 |
| Ligue 1 | 61 |
| Bundesliga | 78 |
| Serie A | 135 |
| La Liga | 140 |

That is 35 league-season combinations. Pagination is unlimited unless
`max_pages` is added to the `[api]` section. Requests are paced by
`safe_pause_seconds`, retried up to `max_retries` times, and stop before the
remaining daily quota reaches `quota_reserve`.

## Project files

### Python ingestion and export

| File | Purpose |
| --- | --- |
| `api_client.py` | Low-level HTTP client. Builds request URLs, sends GET requests, retries HTTP 429 and 5xx responses, checks API errors, tracks request counts, reads rate-limit headers, pauses between calls, and yields every paginated response item. |
| `config.py` | Loads local TOML settings, validates that a real API key exists, creates the API header, and supplies defaults for request pacing, retries, pagination, and quota protection. |
| `config.example.toml` | Safe configuration template. Copy it to `config.toml`, then add the real key locally. |
| `config.toml` | Local runtime configuration. It is secret-bearing and should not be committed. |
| `constants.py` | Defines the five league IDs and the inclusive season list used by the loader. |
| `players.py` | Defines the `dlt` resource. It calls the API client and adds the requested league and season to each raw response item. It intentionally does not clean or calculate metrics. |
| `run_players.py` | Main orchestrator. It optionally loads the API, exports raw CSV, runs dbt, and exports the final feature CSV. It uses `api_sports.duckdb`. If that file already exists, it skips API ingestion and only reruns dbt and exports. |
| `export_sample.py` | Command-line Excel exporter for `main.player_features`. It can export all rows or a limited sample. |
| `requirements.txt` | Python dependencies: dbt core and DuckDB adapter, `dlt` with DuckDB support, HTTP requests, and certificates. |

### dbt project files

| File | Purpose |
| --- | --- |
| `dbt_project.yml` | Names the dbt project and declares that staging models are views while mart models are physical tables. |
| `profiles.yml` | Points dbt at `api_sports.duckdb` and the `main` schema. This is why raw data is in `soccer_analytics_data` but dbt models are in `main`. |
| `packages.yml` | Requests the `dbt-labs/dbt_utils` package, used for the surrogate key and combination uniqueness test. |
| `package-lock.yml` | Pins the resolved dbt package version and checksum. |
| `sources.yml` | Gives dbt the logical source name `raw` for the two `dlt` tables in `soccer_analytics_data`. `{{ source('raw', ...) }}` in SQL resolves through this file. |
| `models/staging/stg_players.sql` | Joins player profile rows to statistics using `_dlt_id` and `_dlt_parent_id`, normalizes names and units, renames API fields, maps `Forward` to `Attacker`, and keeps only rows with at least 300 minutes. It is a view. |
| `models/marts/player_features.sql` | Selects the useful analysis columns from `stg_players` and computes per-90 metrics as `metric * 90 / minutes`. It is a table. |
| `models/schema.yml` | Documents model columns and declares dbt data-quality tests such as not-null, unique, accepted league IDs, valid season/minute/rating ranges, and non-negative counting statistics. |
| `tests/generic/is_between.sql` | Reusable dbt test that returns values below a minimum or above a maximum. |
| `tests/generic/non_negative.sql` | Reusable dbt test that returns negative non-null values. |
| `tests/stg_players_scope.sql` | Singular dbt test that fails if a staging row is outside the configured league or season scope. |
| `tests/player_features_metrics.sql` | Singular dbt test that fails if a final feature row has fewer than 300 minutes or a negative per-90 metric. |
| `models/` | SQL model definitions. dbt compiles them into `target/` and materializes them in DuckDB. |
| `dbt_packages/dbt_utils/` | Installed third-party dbt macros and tests. It is dependency output, not project-owned business logic. |
| `target/` | Generated dbt artifacts: manifest, compiled SQL, run results, graph metadata, and intermediate files. It can be regenerated. |
| `logs/` | Generated dbt logs. |

### Data files

| File | Purpose |
| --- | --- |
| `api_sports.duckdb` | Active DuckDB warehouse used by both `run_players.py` and dbt. |
| `soccer_analytics.duckdb` | An older/unused DuckDB file. In the current workspace it has no project tables; use `api_sports.duckdb`. |
| `players_raw.csv` | CSV export of `soccer_analytics_data.players_raw`, created by `run_players.py` before dbt runs. |
| `player_features.csv` | CSV export of `main.player_features`, created by `run_players.py` after dbt runs. |
| `tmp_player_features.csv` | Temporary or manually generated feature extract; it is not used by the pipeline code. |

## DuckDB tables and views

The active file is `api_sports.duckdb`. A DuckDB file contains schemas, and a
schema groups relations. The project uses `soccer_analytics_data` for `dlt` raw
data and `main` for dbt models.

### Raw source relations: `soccer_analytics_data`

#### `players_raw` (26,132 rows)

This is the player-profile side of the API response. It contains fields such as
`player__id`, `player__name`, age, nationality, height, weight, injury status,
birth details, and the requested `league__id` and `league__season`. The double
underscore names come from `dlt` flattening nested JSON. `_dlt_id` is the row ID
used to connect this table to its child statistics rows; `_dlt_load_id` identifies
the load batch.

#### `players_raw__statistics` (27,412 rows)

This is the child table created when `dlt` normalizes the API's nested
`statistics` array. A row represents a player's stint for a team and
competition in a season. It contains team, league, games, goals, shots, passes,
tackles, duels, dribbles, fouls, cards, and penalty fields. `_dlt_parent_id`
points back to the parent `_dlt_id` in `players_raw`; `_dlt_list_idx` records the
position in the original array.

The raw tables are intentionally wide and close to the API shape. They are not
the tables to use for analysis because values still have API names and types,
and they include low-minute rows and fields that the feature model does not need.

### What `dlt` cleans, and what it does not

It is important to separate **structural normalization** from **analytical
cleaning**. `dlt` does the first one. dbt does the second one.

`dlt` performs these loading tasks:

- Sends the records produced by `players.py` to DuckDB.
- Flattens nested JSON keys. For example, `player.id` becomes `player__id` and
	`games.minutes` becomes `games__minutes`.
- Splits the nested `statistics` array into the child table
	`players_raw__statistics`.
- Adds `_dlt_id`, `_dlt_parent_id`, `_dlt_load_id`, and related metadata so rows
	can be connected and load batches can be tracked.
- Merges records from the different league-season requests into the final raw
	tables according to the resource's configured keys.

`dlt` does **not** decide whether the data is useful for analysis. It does not
apply the 300-minute threshold, calculate per-90 rates, rename fields into the
project's preferred vocabulary, or guarantee that API values are in the final
numeric format. Raw values can therefore look like this:

| Raw value | Why it is still raw |
| --- | --- |
| `player__height = '173'` | Height arrived as text and still has the API field name. |
| `games__rating = '6.79'` | Rating is stored as text in the source relation. |
| `games__position = 'Forward'` | The project later standardizes this label to `Attacker`. |
| `passes__accuracy = NULL` | The API did not provide a value for that record; `dlt` preserves the null. |
| `games__minutes = 209` | The row is valid source data but is excluded from the analytical layer because it is below 300 minutes. |

The cleanup happens in `models/staging/stg_players.sql`. That model:

- Converts height and weight text to integer centimeters and kilograms.
- Casts rating and pass accuracy to numeric types.
- Renames fields such as `games__appearences` to `appearances`.
- Changes `Forward` to `Attacker`.
- Joins player profile rows to their statistics rows.
- Keeps only statistics rows where `games__minutes >= 300`.

The next model, `models/marts/player_features.sql`, calculates goals, assists,
key passes, tackles, and successful dribbles per 90 minutes. Therefore, raw
tables are not broken or unfinished; they preserve the source faithfully so the
transformation logic can be inspected, changed, and rerun.

#### `_dlt_loads`, `_dlt_pipeline_state`, and `_dlt_version`

These are `dlt` bookkeeping tables. They record load metadata, pipeline state,
and the `dlt` schema version. They support ingestion and schema evolution; they
are not analytical datasets.

### Transient dlt relations: `soccer_analytics_data_staging`

This schema contains temporary `dlt` copies used while a load package is being
prepared and merged. It currently has `players_raw` and
`players_raw__statistics` staging tables plus `_dlt_version`. In this workspace,
each staging table has 511 rows because the latest load was the 2026 La Liga
request, which returned 511 player records. That does **not** mean the pipeline
only loaded 511 players: the merged final tables contain 26,132 player rows and
27,412 statistics rows across all 35 league-season loads.

The staging rows are raw source rows, not failed cleaning attempts. They are a
load buffer or recent package snapshot. `dlt` may keep the latest staging
relations after a successful load, and their contents can change or disappear
on a later load. dbt does not read this schema; `sources.yml` points to the
merged `soccer_analytics_data` schema instead.

To inspect the difference directly:

```sql
select count(*) from soccer_analytics_data_staging.players_raw;
-- Current result: 511

select count(*) from soccer_analytics_data.players_raw;
-- Current result: 26,132
```

### dbt relations: `main`

#### `stg_players` (12,731 rows, view)

This is the cleaned relational layer. It joins `players_raw` to
`players_raw__statistics` with:

```sql
players_raw._dlt_id = players_raw__statistics._dlt_parent_id
```

It converts height and weight text into integers, casts rating and pass
accuracy to numeric values, renames API fields, normalizes the position label,
and filters `games__minutes >= 300`. `player_season_id` is a surrogate key based
on player, team, league, and season. Because it is a view, its results are
computed from the raw tables when queried.

#### `player_features` (12,731 rows, table)

This is the analysis-ready mart. It keeps identity, team, league, season,
position, minutes, rating, pass accuracy, and five per-90 measures:

| Column | Formula |
| --- | --- |
| `goals_per90` | `goals * 90 / minutes` |
| `assists_per90` | `assists * 90 / minutes` |
| `key_passes_per90` | `passes_key * 90 / minutes` |
| `tackles_per90` | `tackles_total * 90 / minutes` |
| `dribbles_per90` | `dribbles_success * 90 / minutes` |

The `minutes >= 300` filter in staging prevents division by zero and keeps the
feature set focused on players with a meaningful amount of playing time.

## How the joins and names work

The API response is nested. `dlt` flattens nested keys by joining parent and
child names with `__`, so `player.id` becomes `player__id` and a nested statistic
such as `games.minutes` becomes `games__minutes`.

The relationship is not a join on the public player ID alone. The reliable
`dlt` relationship is:

```text
players_raw._dlt_id
				^
				|
players_raw__statistics._dlt_parent_id
```

The public `player__id` identifies the player, while the combination of player,
team, league, and season identifies the analytical player-season record. A
player can therefore have multiple rows across seasons, leagues, or teams.

## Running the project

Run these commands from the project root with the project virtual environment
activated. Python 3.13 is the recommended environment for dbt in this project.

```bash
# First run: fetch API data, build models, and write CSV files
python run_players.py

# Validate the configured dbt tests
dbt test --project-dir . --profiles-dir .

# Export an Excel sample from the final mart
python export_sample.py --limit 20
```

On later runs, `run_players.py` sees the existing `api_sports.duckdb` and skips
the API load. It still runs dbt and refreshes the CSV exports. To intentionally
rebuild from the API, remove the active database and the matching `dlt` pipeline
state, then run the script again. `run_players.py` contains the reset helper,
but it is not called automatically.

Useful DuckDB checks from Python are:

```python
import duckdb

with duckdb.connect("api_sports.duckdb", read_only=True) as conn:
		print(conn.sql("SHOW TABLES").df())
		print(conn.sql("SELECT * FROM main.player_features LIMIT 5").df())
```

## Generated output and troubleshooting

`dbt run` creates or replaces the `main.stg_players` view and
`main.player_features` table. `dbt test` runs the tests in `models/schema.yml`
and the SQL files under `tests/`. A failing test returns the offending rows in a
generated relation under the dbt test schema and reports the failure in the
terminal.

## Parquet exports and Power BI

The dbt project has a post-hook that runs after each model succeeds:

```text
output/{{ model.name }}.parquet
```

The current outputs are:

| File | Contents |
| --- | --- |
| `output/stg_players.parquet` | Cleaned and joined staging rows. Useful for troubleshooting or detailed analysis. |
| `output/player_features.parquet` | Final analysis-ready mart. This is the recommended Power BI source. |

The Parquet files are generated from the DuckDB relations after dbt builds them,
so they contain the same rows and columns as `main.stg_players` and
`main.player_features`. They are generated artifacts, are ignored by Git, and
are replaced on the next successful `dbt run`.

For Power BI Desktop, connect to the final file using **Get Data > Parquet** and
select `output/player_features.parquet`. Build reports from this file rather
than the staging export unless you specifically need the lower-level columns.
After refreshing the pipeline, run `dbt run` again and refresh the Power BI
dataset to read the updated file.

This is a good approach for a local project or a small scheduled workflow:
Parquet is columnar, preserves types better than CSV, is compact, and is fast
for Power BI to read. It also keeps Power BI separate from the raw API and the
transformation logic.

The main limitation is refresh location. A local path works in Power BI Desktop,
but Power BI Service cannot normally refresh a file that exists only on your
computer. For published dashboards, copy the Parquet output to a supported
shared location such as OneDrive/SharePoint, Azure Blob Storage, Azure Data
Lake, or another organization-approved data store, then connect Power BI to
that shared location. Alternatively, configure an on-premises gateway if the
file must remain on a local or network machine.

The complete local workflow is:

```bash
python run_players.py
# or, when the raw DuckDB data already exists:
dbt run --project-dir . --profiles-dir .
```

Then refresh Power BI from `output/player_features.parquet`. Do not edit the
Parquet file manually; change the source or dbt model and regenerate it.

Common points of confusion:

- `players_raw` is not the final player table. It is a flattened API parent
	table; its statistics are in `players_raw__statistics`.
- `soccer_analytics_data` is the raw source schema. `main` is where dbt models
	are materialized.
- `soccer_analytics_data_staging` is a temporary `dlt` load area. It is not the
	complete historical dataset and it is not where cleaning happens.
- `stg_players` is a view, while `player_features` is a table.
- `player_features.csv` is an export and is not the source dbt reads.
- `soccer_analytics.duckdb` is not the configured target. The configured target
	is `api_sports.duckdb` in `profiles.yml`.
- If a raw schema change causes a `dlt` schema-evolution error, inspect the
	existing pipeline state under the user's `.dlt/pipelines` directory and use a
	deliberate clean rebuild rather than deleting files at random.
