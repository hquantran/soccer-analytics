# Private Databricks migration

The repository supplies a migration path, not evidence that a remote deployment has
already succeeded. Local validation is recorded below; remote execution and parity
must pass before describing the Databricks migration as complete.

## Validation completed locally (2026-10-08)

- Python 3.11.17; locked dbt Core 1.12.5, dbt-duckdb 1.11.0,
  dbt-databricks 1.12.6, dbt-metricflow 0.15.0.
- DuckDB parse, compile and build: 7 models and all 74 data tests passed.
- MetricFlow semantic and warehouse validation: zero errors or warnings.
- All eight MetricFlow totals matched independent additive SQL calculations.
- Four Python tests passed, including real MetricFlow execution on weighted
  multi-season fixtures and zero-denominator fixtures, parsed semantic contract
  checks, recommender consistency and DAX contract checks.
- Local baseline parity passed for all model counts, fact totals, representative
  records and every player's multi-season additive rollup.
- Streamlit entry point and all three pages passed application smoke tests.
- Databricks parse and offline compile passed; remote build, upload, Delta storage
  inspection and remote parity remain unverified until account access is configured.

These results establish local correctness and adapter SQL rendering. They do not
prove a completed Databricks deployment or an executed Power BI report.

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
and use `uv run` before each Python, dbt and mf command. In the migration validation
session an isolated `.venv-analytics` was used to preserve the existing environment.
On Windows set `$env:PYTHONIOENCODING='utf-8'` and `$env:PYTHONUTF8='1'` before
running `mf`; its Unicode status messages and player names in CSV exports otherwise
fail with cp1252 defaults.

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
into the current process before calling dbt or MetricFlow. For example:

```powershell
python -m dotenv -f .env run -- dbt debug --profiles-dir . --target databricks
python -m scripts.migrate_history load
python -m dotenv -f .env run -- dbt build --profiles-dir . --target databricks
python -m dotenv -f .env run -- mf validate-configs
python -m scripts.migrate_history compare-databricks
```

Set `DBT_TARGET=databricks` in `.env` for the MetricFlow command above. The loader
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

## Grain and metric semantics

`fct_player_seasons` has one row per **player, team, league, season stint** with
at least 300 minutes. A transferred player can have multiple stints in a season.
The surrogate key and four-column uniqueness tests enforce that grain. Facts
include goalkeepers; `bi_player_seasons` intentionally serves only outfield players.
Players use latest available attributes, teams and leagues have one row each.
Age is the current calendar-year difference, preserving the original DuckDB logic;
it is not historical age at season start.

The semantic graph defines player/team/league entities, categorical season,
position, nationality and identity dimensions, and additive measures. An artificial
January 1 date represents the integer season for MetricFlow. It is a season label,
**not a match date**; monthly/daily football performance cannot be inferred from it.
The daily time spine covers 2020–2026 and must be extended with the source scope.

`dbt_project.yml → vars.canonical_metrics` is the shared numerator/denominator/scale
contract. dbt macros render BI rates; semantic measures render scaled additive
numerators from those variables; Python `MetricSpec` reads the same contract for
arbitrary local filter-window rollups. Tests check the parsed semantic graph agrees.
Downstream arbitrary windows still sum additive columns locally; Streamlit does
not call MetricFlow. Display rates are rounded to three decimals; semantic rates
are unrounded.

| Metric | Aggregation |
|---|---|
| goals_per90 | 90 × SUM(goals) / SUM(minutes) |
| assists_per90 | 90 × SUM(assists) / SUM(minutes) |
| key_passes_per90 | 90 × SUM(passes_key) / SUM(minutes) |
| tackles_per90 | 90 × SUM(tackles_total) / SUM(minutes) |
| pass_accuracy_pct | 100 × SUM(passes_completed) / SUM(passes_total) |
| duel_success_pct | 100 × SUM(duels_won) / SUM(duels_total) |
| dribble_attempts_per90 | 90 × SUM(dribbles_attempts) / SUM(minutes) |
| dribble_success_pct | 100 × SUM(dribbles_success) / SUM(dribbles_attempts) |

Zero denominators return NULL / Python `None`, not zero or infinity. Never average
precomputed rates. Missing event totals preserve the existing fact-layer zero
imputation. `passes_completed` is an **estimate**, rounded from attempted passes
and the provider's reported pass percentage. Missing pass percentages leave this
estimate null; the current denominator includes those attempts. This preserves the
existing definition but can understate accuracy when coverage is incomplete.
This limitation should be stated when discussing the metric.

The BI column `successful_dribbles_per90` explicitly means successful dribbles
per 90; it replaces the ambiguous `dribbles_per90` name. Dashboard, recommender and notebook code use
`dribble_attempts_per90` and `dribble_success_pct`. Similarity rankings can change
because attempts replace successes in the dribble volume feature. The UI layout
and Gemini integration are unchanged.

## Local and semantic validation

```powershell
dbt parse --profiles-dir . --target dev
dbt compile --profiles-dir . --target dev
dbt build --profiles-dir . --target dev
mf validate-configs
mf query --metrics goals_per90,dribble_attempts_per90 --group-by player,player__player_name
python -m unittest discover -s tests_python -v
python -m scripts.migrate_history compare-local
dbt parse --profiles-dir . --target databricks --target-path target/databricks
dbt compile --profiles-dir . --target databricks --target-path target/databricks --no-introspect --no-populate-cache
```

Use `DBT_TARGET=dev` for local MetricFlow and regenerate the default `target` artifacts
after switching targets. Databricks offline compilation checks adapter rendering;
it cannot prove warehouse execution. Runtime build, remote semantic validation,
and parity are required with account access. The open-source `dbt-metricflow` CLI
provides `mf`; no paid hosted semantic endpoint is needed.

## Power BI and private Streamlit

Power BI Desktop uses the Azure Databricks connector (also for Databricks on other
clouds): provide workspace host and SQL warehouse HTTP path, authenticate, then
select `<catalog>.<curated_schema>.bi_player_seasons`. Use Import for this small
dataset unless DirectQuery is required. Import stores private data in the PBIX;
keep that file private. Do not publish a dataset or report publicly.

Power BI does not automatically consume the MetricFlow YAML. For filter-aware
rates use the supplied [DAX measures](power-bi-measures.dax) over the exposed additive
columns; these mirror the canonical contract. dbt parity tests and Python contract
tests govern the definitions. Power BI Desktop is required to create and validate
an actual report; no fabricated PBIX is included.

Streamlit queries **MetricFlow for metric values** on the Databricks SQL
warehouse. Profile attributes and filter choices come directly from the fact and
dimension tables. The application does not read the BI table or Parquet exports.
Set `SOCCER_BACKEND=databricks` in the ignored `.env` and launch:

```powershell
.\.venv-analytics\Scripts\streamlit.exe run dashboard/app.py
```

The app loads `.env` automatically. Attribute queries bind filter values as SQL
parameters. Exact selected stint IDs scope semantic queries, preserving season,
league, team, age and majority-position filters. MetricFlow computes the rates,
additive totals and minutes-weighted rating; charts, percentiles and similarity
scores remain dashboard responsibilities. An entirely missing completed-pass total
produces a null accuracy instead of an artificial zero.

Results are cached in memory for five minutes. MetricFlow runs in a subprocess
with a separate generated project and manifest under ignored
`target/streamlit_<backend>`. Query requests and CSV results are temporary files
under ignored `data/migrations`, deleted after use. Large filters are loaded by a
Python worker to avoid Windows' command-line length limit. Cold queries include
MetricFlow startup time; the SQL warehouse must be available. There is no silent
local fallback after a remote error. Restart after changing connection settings.

`SOCCER_BACKEND` selects both the dashboard attribute source and its MetricFlow
target. `DBT_TARGET` still selects the target for manual dbt/MetricFlow commands.
Use the Python 3.11 `.venv-analytics` environment, which contains `dbt` and `mf`.
For local semantic queries, set `SOCCER_BACKEND=duckdb`; optional
`SOCCER_DUCKDB_PATH` selects the database. The historical DuckDB database remains
intact. BI models and `scripts.export_databricks_consumer.py` remain optional for
other consumers and are not required by Streamlit.

## Private data policy

Underlying sports data belongs to a third-party provider and is intentionally
excluded from source control. Databases, CSV/Parquet exports, migration snapshots,
tokens, `.env`, private configuration and Streamlit secrets are ignored. Notebook
outputs were cleared because they contained player records. Ignore patterns do not
remove data from past Git commits: existing repository history must be reviewed
before public redistribution. Do not commit freshly executed notebook outputs.

References: [open-source MetricFlow](https://github.com/dbt-labs/metricflow),
[MetricFlow commands](https://docs.getdbt.com/docs/build/metricflow-commands),
[Databricks Free Edition](https://docs.databricks.com/aws/en/getting-started/free-edition).
[Power BI connector](https://learn.microsoft.com/en-us/power-query/connectors/databricks-azure).

## Shared metric definitions

`dbt_project.yml` defines the inputs and scales for all 16 rates. BI SQL uses
`canonical_rate`, semantic measures render the same numerator, and Streamlit
requests the resulting metric names through MetricFlow. Its display metadata
reads the same contract through `config/metrics.py`. Change the formula there
when updating an existing metric, then rebuild dbt models and restart Streamlit.
The optional BI table is still built by dbt SQL. Streamlit uses grouped semantic
queries directly and does not recalculate rates in Python. Rates are calculated
after summing additive inputs, with null results for zero denominators.

Goal involvements use the combined numerator `[goals, assists]`. Successful
dribbles per 90 remain distinct from attempts per 90 and dribble success percent.
