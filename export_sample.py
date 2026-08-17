from __future__ import annotations

import re
from argparse import ArgumentParser
from pathlib import Path

import duckdb
import pandas as pd


SQL_REPLACEMENTS = {
    r"\{\{\s*source\('raw',\s*'players_raw'\)\s*\}\}": "soccer_analytics_data.players_raw",
    r"\{\{\s*source\('raw',\s*'players_raw__statistics'\)\s*\}\}": "soccer_analytics_data.players_raw__statistics",
}

FEATURES_SQL_REPLACEMENTS = {
    r"\{\{\s*ref\('stg_players'\)\s*\}\}": "sample_stg_players",
}


def normalize_sql(sql: str) -> str:
    for pattern, replacement in SQL_REPLACEMENTS.items():
        sql = re.sub(pattern, replacement, sql)
    return sql


def load_sql_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def export_sample(db_path: Path, output_path: Path, limit: int) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB file not found: {db_path}")

    stg_file = Path("models/staging/stg_players.sql")
    features_file = Path("models/marts/player_features.sql")
    if not stg_file.exists() or not features_file.exists():
        raise FileNotFoundError("Missing dbt model SQL files in models/staging or models/marts.")

    stg_sql = normalize_sql(load_sql_file(stg_file))
    features_sql = load_sql_file(features_file)
    for pattern, replacement in FEATURES_SQL_REPLACEMENTS.items():
        features_sql = re.sub(pattern, replacement, features_sql)

    with duckdb.connect(str(db_path)) as conn:
        conn.execute(f"CREATE OR REPLACE VIEW sample_stg_players AS {stg_sql}")
        conn.execute(f"CREATE OR REPLACE VIEW sample_player_features AS {features_sql}")
        query = f"SELECT * FROM sample_player_features LIMIT {limit}"
        df = conn.execute(query).df()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    print(f"Sample exported to {output_path} ({len(df)} rows)")


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Export a sample of transformed player features to Excel.")
    parser.add_argument("--db-path", default="api_sports.duckdb", help="Path to the DuckDB file.")
    parser.add_argument("--output", default="player_features_sample.xlsx", help="Output Excel file path.")
    parser.add_argument("--limit", type=int, default=20, help="Number of rows to include in the sample.")
    return parser


if __name__ == "__main__":
    args = parse_args().parse_args()
    export_sample(Path(args.db_path), Path(args.output), args.limit)
