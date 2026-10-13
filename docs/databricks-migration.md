# Databricks warehouse and reporting architecture

## Current architecture

Historical API data is preserved in DuckDB and migrated to managed Databricks
Delta tables. dbt builds staging views, a player-season fact, player/team/league
dimensions, and the `bi_player_seasons` scouting mart.

- **Power BI:** imports facts and dimensions from Databricks. Its semantic model
  defines relationships, DAX measures, formats and report-facing fields.
- **Streamlit:** reads the scouting mart from Databricks or the local DuckDB source.
- **Shared formulas:** `dbt_project.yml` supplies the 16 rate definitions used by
  dbt SQL, Python rollups and generated Power BI DAX.

There is no separate MetricFlow query path. Power BI does not need one to provide
semantic modeling. Neither dashboard relies on a hosted dbt Semantic Layer.

The saved private Databricks comparison reports no discrepancies across model
counts, fact totals, sampled records and player rollups. Direct raw-table counts
confirmed 26,132 parent rows and 27,412 statistics rows. These are related records,
not 53,544 unique players. Re-run validation after changing data or transformations.

## Preserve and transfer history

Do **not** rerun `run_players.py` to migrate history. The lowest useful persisted
data is `soccer_analytics_data.players_raw` and `players_raw__statistics` in
`data/warehouse/api_sports.duckdb`. Their `_dlt_id` / `_dlt_parent_id` relationship
is needed by staging. dlt state and intermediate staging schemas are not needed.

```powershell
python -m pip install -r requirements.txt
dbt deps --profiles-dir .
python -m scripts.migrate_history prepare
```

Use Python 3.11 (the project `.python-version` and validated runtime). The existing
Python 3.14 environment emits Pydantic v1 compatibility warnings. For a locked
environment, run `uv sync --locked --python 3.11`
and use `uv run` before each Python and dbt command. In the migration validation
session an isolated `.venv-analytics` was used to preserve the existing environment.
`prepare` opens the existing warehouse read-only, exports both complete raw tables
to compressed Parquet, verifies row counts, computes checksums, and captures a
private pre-migration baseline. Existing exports are never overwritten. To take a
new snapshot, pass `--out data/migrations/another-snapshot` to every migration
command. The original source remains intact. No migration data is committed.

## Connect the private workspace

Copy `.env.example` to ignored `.env` and fill in the workspace host (no URL scheme),
SQL warehouse HTTP path, token, catalog, curated schema and raw schema. Never paste
the token in Git, screenshots or chat. The host is in the workspace URL; open
**SQL Warehouses → your warehouse → Connection details** for its HTTP path. Use
**Settings → Developer → Access tokens** if workspace policy permits PATs.
The current loader supports PAT authentication. If PATs are unavailable, a supported
OAuth flow must be configured before loading; do not invent a token.

Keep `DBT_TARGET=dev` until ready. dbt does not automatically load `.env`; load it
into the current process before calling dbt. For example:

```powershell
python -m dotenv -f .env run -- dbt debug --profiles-dir . --target databricks
python -m scripts.migrate_history load
python -m dotenv -f .env run -- dbt build --profiles-dir . --target databricks
python -m scripts.migrate_history compare-databricks
```

The loader
uses the workspace Files API to upload to a private Unity Catalog managed volume,
then creates managed raw **Delta** tables using Parquet CTAS. It verifies remote
row counts and refuses to overwrite existing tables or volume files. The account
must permit schema, volume and table creation in the selected catalog. On a partial
load, inspect existing tables and checksums before resuming; do not delete data
blindly. Set up a fresh raw schema for a deliberate retry.

Remote dbt table materializations use Delta; staging stays a view. Source catalog
and schema are environment-controlled. Local filesystem export hooks execute only
on DuckDB. Credentials are read from environment variables, never SQL or code.

`compare-databricks` checks all five curated model row counts, distinct players,
leagues, seasons, additive totals, 20 deterministically selected fact records, and
every player's multi-season additive totals. These cover the original eight metrics; the expanded formula checks cover
all 16 shared rates. dbt also tests serving rate parity.
Differences fail the command and produce an ignored private JSON report for
investigation. Expected changes are only the added explicit dribble-attempt rate
and recommender feature semantics; existing successful-dribble legacy rates remain.

## Grain and metric definitions

The fact grain is player, team, league and season. Staging retains stints with
at least 300 minutes. The scouting mart excludes goalkeepers. Multi-stint and
multi-season rates divide summed inputs rather than averaging stored rates.
Zero denominators return null. Attempted and successful dribbles are separate metrics.

`passes_completed` is estimated from the provider field interpreted as a percentage.
Passing accuracy requires source validation and is withheld from stakeholder
recommendations. Formula parity does not establish source accuracy.

Birth dates are available in `dim_players`. Historical age can be calculated at
July 1 of each season-start year; the fact's January 1 season key is not that
age reference date.

## Validation

```powershell
dbt parse --profiles-dir . --target dev
dbt build --profiles-dir . --target dev
python -m unittest discover -s tests_python -v
python -m scripts.migrate_history compare-local
python -m dotenv -f .env run -- dbt build --profiles-dir . --target databricks
python -m scripts.migrate_history compare-databricks
```

dbt tests check keys, relationships, scope, ranges and rate parity. Python tests
check shared formulas, generated DAX and weighted rollups. The migration comparison
checks local/cloud counts and values. No MetricFlow installation or tests are required.

## Power BI and Streamlit

Follow the [Power BI connection guide](../powerbi/README.md). The generator creates
TMDL imports, relationships and DAX from shared formulas. Use the starter only for
a blank report; applying it over a customized model can replace custom work.
The generator does not design report pages. The separately created report is
summarized in the [stakeholder briefing](stakeholder-insights.md).

Streamlit reads `bi_player_seasons` directly. Set `SOCCER_BACKEND=databricks` or
`duckdb` in ignored `.env` and restart. Queries are parameterized, results are cached,
and remote errors do not silently fall back to local data.

## Private data

Keep credentials, databases, raw exports, migration snapshots and imported Power BI
datasets private. A PBIX contains imported data. Git ignore rules do not remove
files already committed to history. Review provider rights before sharing exports
or report screenshots.
