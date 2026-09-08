"""Export a sample of bi_player_seasons to Excel."""

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path

import duckdb

from ingestion.settings import PROJECT_ROOT

DEFAULT_DB = PROJECT_ROOT / "data" / "warehouse" / "api_sports.duckdb"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "exports" / "bi_player_seasons_sample.xlsx"


def export_sample(db_path: Path, output_path: Path, limit: int) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB file not found: {db_path}")

    with duckdb.connect(str(db_path)) as conn:
        table_name = "main.bi_player_seasons"
        try:
            conn.execute(f"SELECT 1 FROM {table_name} LIMIT 1").fetchone()
        except Exception as exc:  # pragma: no cover - user-facing error path
            raise RuntimeError(
                f"No dbt model table found at {table_name}. Run `dbt run` before exporting."
            ) from exc

        query = f"SELECT * FROM {table_name}"
        if limit and limit > 0:
            query = f"{query} LIMIT {limit}"

        df = conn.execute(query).df()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False)
    print(f"Sample exported to {output_path} ({len(df)} rows)")


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description="Export a sample of bi_player_seasons to Excel.")
    parser.add_argument("--db-path", default=str(DEFAULT_DB), help="Path to the DuckDB file.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output Excel file path.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Number of rows to include; 0 or negative exports all rows.",
    )
    return parser


if __name__ == "__main__":
    args = parse_args().parse_args()
    export_sample(Path(args.db_path), Path(args.output), args.limit)
