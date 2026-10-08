"""Refresh an ignored private Streamlit cache after successful remote parity."""
import json
from pathlib import Path

import duckdb
import pandas as pd

from scripts.migrate_history import OUT, ROOT, namespace, remote_connection


def main():
    report = OUT / 'databricks_comparison.json'
    if not report.exists() or not json.loads(report.read_text())['passed']:
        raise RuntimeError('Run compare-databricks successfully before refreshing the consumer cache.')
    with remote_connection() as conn, conn.cursor() as cursor:
        _, _, ns = namespace()
        cursor.execute(f'SELECT * FROM {ns}.bi_player_seasons')
        frame = pd.DataFrame.from_records(cursor.fetchall(), columns=[c[0] for c in cursor.description])
    # Separate cache: never replace the historical warehouse.
    database = ROOT / 'data/warehouse/databricks_consumer.duckdb'
    export = ROOT / 'data/exports/databricks_bi_player_seasons.parquet'
    with duckdb.connect(str(database)) as local:
        local.register('remote_frame', frame)
        local.execute('CREATE OR REPLACE TABLE main.bi_player_seasons AS SELECT * FROM remote_frame')
    frame.to_parquet(export, index=False)
    print('Private Databricks consumer cache refreshed. Set both SOCCER_* paths before launching Streamlit.')


if __name__ == '__main__':
    main()
