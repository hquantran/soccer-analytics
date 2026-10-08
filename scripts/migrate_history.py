"""Prepare existing dlt history, load it into Delta, and compare dbt outputs.

No API ingestion. All datasets/reports remain under ignored data/migrations.
Run from the repository root: python -m scripts.migrate_history --help
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/warehouse/api_sports.duckdb'
OUT = ROOT / 'data/migrations'
RAW_TABLES = ('players_raw', 'players_raw__statistics')
MODELS = ('dim_players', 'dim_teams', 'dim_leagues', 'fct_player_seasons', 'bi_player_seasons')
TOTALS = ('minutes', 'goals', 'assists', 'passes_total', 'passes_completed', 'passes_key',
          'tackles_total', 'duels_total', 'duels_won', 'dribbles_attempts', 'dribbles_success')


def identifier(value: str) -> str:
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value):
        raise ValueError(f'Invalid SQL identifier: {value!r}')
    return f'`{value}`'


def local_snapshot(conn) -> dict:
    result = {}
    for model in MODELS:
        result[model] = conn.execute(f'select count(*) from main.{model}').fetchone()[0]
    result['fact_summary'] = list(conn.execute(
        'select count(*), count(distinct player_id), count(distinct league_id), '
        'count(distinct season), ' + ', '.join(f'sum({c})' for c in TOTALS) +
        ' from main.fct_player_seasons').fetchone())
    columns = 'player_season_id, player_id, team_id, league_id, season, ' + ', '.join(TOTALS)
    result['samples'] = [list(row) for row in conn.execute(
        f'select {columns} from main.fct_player_seasons order by player_season_id limit 20'
    ).fetchall()]
    result['player_rollups'] = [list(row) for row in conn.execute(
        'select player_id, count(distinct season), ' + ', '.join(f'sum({c})' for c in TOTALS) +
        ' from main.fct_player_seasons group by player_id order by player_id'
    ).fetchall()]
    return result


def prepare(db: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db), read_only=True) as conn:
        manifest = {'source': str(db.resolve()), 'raw_tables': {}}
        for table in RAW_TABLES:
            destination = out / f'{table}.parquet'
            if destination.exists():
                raise FileExistsError(f'{destination} exists; choose a new --out directory')
            path_sql = str(destination.resolve()).replace('\\', '/').replace("'", "''")
            conn.execute(f"COPY soccer_analytics_data.{table} TO '{path_sql}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            source_count = conn.execute(f'select count(*) from soccer_analytics_data.{table}').fetchone()[0]
            transferred = conn.execute('select count(*) from read_parquet(?)', [str(destination)]).fetchone()[0]
            if source_count != transferred:
                raise AssertionError(f'Export row count mismatch: {table}')
            manifest['raw_tables'][table] = {
                'rows': source_count, 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                'columns': [row[0] for row in conn.execute(f'describe soccer_analytics_data.{table}').fetchall()],
            }
        snapshot = local_snapshot(conn)
        (out / 'baseline.json').write_text(json.dumps(snapshot, indent=2), encoding='utf-8')
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Prepared two verified Parquet exports and private baseline; source database unchanged.')


def remote_connection():
    from databricks import sql
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env', override=False)
    required = ('DATABRICKS_HOST', 'DATABRICKS_HTTP_PATH', 'DATABRICKS_TOKEN')
    missing = [key for key in required if not os.environ.get(key)]
    if missing:
        raise ValueError('Set private .env values: ' + ', '.join(missing))
    return sql.connect(server_hostname=os.environ['DATABRICKS_HOST'].removeprefix('https://').rstrip('/'),
                       http_path=os.environ['DATABRICKS_HTTP_PATH'], access_token=os.environ['DATABRICKS_TOKEN'])


def namespace(raw=False):
    catalog = os.environ.get('DATABRICKS_CATALOG', 'workspace')
    schema = os.environ.get('DATABRICKS_RAW_SCHEMA' if raw else 'DATABRICKS_SCHEMA',
                            'soccer_analytics_data' if raw else 'soccer_analytics')
    return catalog, schema, f'{identifier(catalog)}.{identifier(schema)}'


def load(out: Path):
    """Upload through the private workspace Files API, then CTAS managed Delta tables.

    Refuses existing tables: migration must not silently replace remote source data.
    """
    from databricks.sdk import WorkspaceClient
    manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
    with remote_connection() as conn:
        catalog, schema, ns = namespace(raw=True)
        with conn.cursor() as cursor:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {ns}')
            cursor.execute(f'CREATE VOLUME IF NOT EXISTS {ns}.history_transfer')
            client = WorkspaceClient(host='https://' + os.environ['DATABRICKS_HOST'].removeprefix('https://').rstrip('/'),
                                     token=os.environ['DATABRICKS_TOKEN'])
            for table in RAW_TABLES:
                cursor.execute(f'SHOW TABLES IN {ns} LIKE \'{table}\'')
                if cursor.fetchall():
                    raise FileExistsError(f'{table} already exists; verify it rather than overwriting')
                local = out / f'{table}.parquet'
                if hashlib.sha256(local.read_bytes()).hexdigest() != manifest['raw_tables'][table]['sha256']:
                    raise AssertionError(f'Parquet checksum changed: {table}')
                remote = f'/Volumes/{catalog}/{schema}/history_transfer/{table}.parquet'
                with local.open('rb') as stream:
                    client.files.upload(remote, stream, overwrite=False)
                cursor.execute(f"CREATE TABLE {ns}.{identifier(table)} USING DELTA AS SELECT * FROM parquet.`{remote}`")
                cursor.execute(f'SELECT count(*) FROM {ns}.{identifier(table)}')
                if cursor.fetchone()[0] != manifest['raw_tables'][table]['rows']:
                    raise AssertionError(f'Delta row count mismatch: {table}')
    print('Private raw Delta tables loaded and row counts verified. Run dbt build --target databricks next.')


def compare(out: Path, db: Path, remote: bool):
    expected = json.loads((out / 'baseline.json').read_text(encoding='utf-8'))
    if not remote:
        with duckdb.connect(str(db), read_only=True) as conn:
            actual = local_snapshot(conn)
    else:
        actual = {}
        with remote_connection() as conn, conn.cursor() as cursor:
            _, _, ns = namespace()
            for model in MODELS:
                cursor.execute(f'SELECT count(*) FROM {ns}.{identifier(model)}')
                actual[model] = cursor.fetchone()[0]
            cursor.execute('SELECT count(*), count(distinct player_id), count(distinct league_id), '
                           'count(distinct season), ' + ', '.join(f'sum({c})' for c in TOTALS) +
                           f' FROM {ns}.fct_player_seasons')
            actual['fact_summary'] = list(cursor.fetchone())
            cursor.execute('SELECT player_season_id, player_id, team_id, league_id, season, ' +
                           ', '.join(TOTALS) + f' FROM {ns}.fct_player_seasons ORDER BY player_season_id LIMIT 20')
            actual['samples'] = [list(row) for row in cursor.fetchall()]
            cursor.execute('SELECT player_id, count(distinct season), ' +
                           ', '.join(f'sum({c})' for c in TOTALS) +
                           f' FROM {ns}.fct_player_seasons GROUP BY player_id ORDER BY player_id')
            actual['player_rollups'] = [list(row) for row in cursor.fetchall()]
    def same(a, b):
        if isinstance(a, list) and isinstance(b, list):
            return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-8)
        return a == b
    discrepancies = [key for key in expected if not same(expected[key], actual.get(key))]
    (out / ('databricks_comparison.json' if remote else 'local_comparison.json')).write_text(
        json.dumps({'passed': not discrepancies, 'discrepancies': discrepancies, 'actual': actual},
                   indent=2, default=float), encoding='utf-8')
    if discrepancies:
        raise AssertionError('Parity failed: ' + ', '.join(discrepancies))
    print('Parity passed: model counts, fact totals, samples, and every player multi-season additive rollup.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'load', 'compare-local', 'compare-databricks'))
    parser.add_argument('--db', type=Path, default=DB)
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare(args.db, args.out)
    elif args.action == 'load':
        load(args.out)
    else:
        compare(args.out, args.db, args.action == 'compare-databricks')


if __name__ == '__main__':
    main()
