"""Read the scouting mart from the selected warehouse."""
from decimal import Decimal
import os
from pathlib import Path

import duckdb
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', override=False)
BACKEND = os.environ.get('SOCCER_BACKEND', 'databricks')
if BACKEND not in ('databricks', 'duckdb'):
    raise ValueError('SOCCER_BACKEND must be databricks or duckdb')


def query(sql, params=None):
    """Bind filter values as parameters; remote errors never fall back to local data."""
    namespace_prefix = 'main'
    if BACKEND == 'databricks':
        from scripts.migrate_history import namespace
        namespace_prefix = namespace()[2]
    sql = sql.replace('main.player_season_attributes', namespace_prefix + '.bi_player_seasons')
    if BACKEND == 'duckdb':
        path = os.environ.get('SOCCER_DUCKDB_PATH', str(ROOT / 'data/warehouse/api_sports.duckdb'))
        if not Path(path).exists():
            raise FileNotFoundError(f'DuckDB not found: {path}')
        with duckdb.connect(path, read_only=True) as connection:
            return connection.execute(sql, params or []).df()
    from scripts.migrate_history import remote_connection
    with remote_connection() as connection, connection.cursor() as cursor:
        cursor.execute(sql, params or [])
        frame = pd.DataFrame.from_records(cursor.fetchall(), columns=[c[0] for c in cursor.description])
    # Databricks DECIMAL display rates must support the app's NumPy/pandas calculations.
    for column in frame:
        sample = frame[column].dropna()
        if not sample.empty and isinstance(sample.iloc[0], Decimal):
            frame[column] = pd.to_numeric(frame[column], errors='raise').astype(float)
    return frame
