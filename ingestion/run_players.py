"""Extract + clean player statistics for MVP_LEAGUE_IDS x SEASONS into DuckDB.

Run from the project root with the venv activated:

    python -m ingestion.run_players

Or use the root shim:

    python run_players.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import dlt
import duckdb

from config.constants import MVP_LEAGUE_IDS, SEASONS
from ingestion.players import players_resource
from ingestion.settings import PROJECT_ROOT

DB_PATH = PROJECT_ROOT / "data" / "warehouse" / "api_sports.duckdb"


def reset_pipeline_state() -> None:
    """Fully clear dlt + DuckDB state before a clean schema rebuild."""
    pipeline_root = Path.home() / ".dlt" / "pipelines" / "soccer_analytics"
    if pipeline_root.exists():
        shutil.rmtree(pipeline_root)

    if DB_PATH.exists():
        DB_PATH.unlink()

    if (Path.home() / ".dlt" / "pipelines").exists():
        for stale in (Path.home() / ".dlt" / "pipelines").glob("soccer_analytics*"):
            if stale.exists():
                shutil.rmtree(stale)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))
    try:
        conn.execute("DROP SCHEMA IF EXISTS soccer_analytics_data_staging CASCADE")
        conn.execute("DROP SCHEMA IF EXISTS soccer_analytics_data CASCADE")
        conn.execute("DROP VIEW IF EXISTS main.sample_stg_players")
        conn.execute("DROP VIEW IF EXISTS main.stg_players")
        conn.execute("DROP TABLE IF EXISTS main.dim_players")
        conn.execute("DROP TABLE IF EXISTS main.dim_teams")
        conn.execute("DROP TABLE IF EXISTS main.dim_leagues")
        conn.execute("DROP TABLE IF EXISTS main.fct_player_seasons")
        conn.execute("DROP TABLE IF EXISTS main.bi_player_seasons")
        conn.execute("DROP TABLE IF EXISTS main.player_features")
    finally:
        conn.close()


def main() -> None:
    db_exists = DB_PATH.exists()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not db_exists:
        print("Database not found. Loading fresh data from API...")
        pipeline = dlt.pipeline(
            pipeline_name="soccer_analytics",
            destination=dlt.destinations.duckdb(str(DB_PATH)),
            dataset_name="soccer_analytics_data",
        )

        for league_id in MVP_LEAGUE_IDS:
            for season in SEASONS:
                print(f"Loading league={league_id} season={season}...")
                load_info = pipeline.run(players_resource(league_id, season))
                print(load_info)
    else:
        print(f"Database already exists at {DB_PATH}. Skipping API load and exporting current data only.")

    active_dbt = Path(sys.executable).parent / "Scripts" / "dbt.exe"
    if sys.version_info >= (3, 14):
        compatible_dbt = next(
            (
                path
                for path in Path(sys.executable).parent.parent.glob(
                    "Python3*/Scripts/dbt.exe"
                )
                if path.parent.parent != Path(sys.executable).parent
            ),
            None,
        )
        dbt_executable = str(compatible_dbt) if compatible_dbt else shutil.which("dbt")
    else:
        dbt_executable = str(active_dbt) if active_dbt.exists() else shutil.which("dbt")
    if not dbt_executable:
        raise RuntimeError("dbt executable not found. Install dbt-duckdb in the active Python environment.")
    dbt_cmd = [
        dbt_executable,
        "run",
        "--project-dir",
        str(PROJECT_ROOT),
        "--profiles-dir",
        str(PROJECT_ROOT),
    ]
    print(f"Running dbt transform: {' '.join(dbt_cmd)}")
    subprocess.run(dbt_cmd, cwd=PROJECT_ROOT, check=True)
    print("dbt models and data/exports complete.")


if __name__ == "__main__":
    main()
