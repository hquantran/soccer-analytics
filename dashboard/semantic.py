"""Execute MetricFlow in a subprocess, isolated from Streamlit's event loop."""
import os
import json
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading

import pandas as pd
import streamlit as st
import yaml

from config.metrics import CANONICAL_METRICS
from dashboard.metrics_config import ADDITIVE_COLS
from dashboard.warehouse import BACKEND, ROOT

_LOCK = threading.Lock()


def _environment():
    project = ROOT / 'target' / ('streamlit_' + BACKEND)
    environment = dict(os.environ, DBT_TARGET='databricks' if BACKEND == 'databricks' else 'dev',
                       PYTHONIOENCODING='utf-8', PYTHONUTF8='1',
                       DBT_PROFILES_DIR=str(ROOT),
                       SOCCER_DBT_TARGET_PATH=str(project / 'target'),
                       DBT_TARGET_PATH=str(project / 'target'),
                       SOCCER_DBT_PROJECT=str(project))
    environment['PYTHONPATH'] = str(ROOT) + os.pathsep + environment.get('PYTHONPATH', '')
    if BACKEND == 'duckdb':
        environment['DUCKDB_PATH'] = os.environ.get(
            'SOCCER_DUCKDB_PATH', str(ROOT / 'data/warehouse/api_sports.duckdb'))
    return environment


def _run(name, arguments, environment):
    executable = Path(sys.executable).parent / (name + '.exe' if os.name == 'nt' else name)
    if not executable.exists():
        raise RuntimeError(f'{name} is required in the Streamlit Python environment. Use .venv-analytics.')
    command = [str(executable), *arguments]
    if name == 'mf':
        # Build the potentially large filter inside Python, beyond Windows'
        # command-line length limit. The request is private and short-lived.
        with tempfile.TemporaryDirectory(dir=ROOT / 'data/migrations') as temporary:
            request = Path(temporary) / 'request.json'
            request.write_text(json.dumps(arguments), encoding='utf-8')
            command = [sys.executable, '-m', 'dashboard.semantic_worker', str(request)]
            result = subprocess.run(command, cwd=environment['SOCCER_DBT_PROJECT'], env=environment,
                                    capture_output=True, text=True, encoding='utf-8', timeout=180)
    else:
        result = subprocess.run(command, cwd=environment['SOCCER_DBT_PROJECT'], env=environment,
                                capture_output=True, text=True, encoding='utf-8', timeout=180)
    if result.returncode:
        details = result.stdout[-4000:] + '\n' + result.stderr[-2000:]
        token = environment.get('DATABRICKS_TOKEN')
        if token:
            details = details.replace(token, '[redacted]')
        raise RuntimeError(f'{name} failed: {details}')


def _prepare(environment):
    # This installed MetricFlow CLI loads target/semantic_manifest.json relative
    # to its project root. Give each backend its own project and manifest.
    project = Path(environment['SOCCER_DBT_PROJECT'])
    project.mkdir(parents=True, exist_ok=True)
    for name in ('packages.yml', 'package-lock.yml'):
        source = ROOT / name
        if source.exists():
            (project / name).write_text(source.read_text(encoding='utf-8'), encoding='utf-8')
    config = yaml.safe_load((ROOT / 'dbt_project.yml').read_text(encoding='utf-8'))
    config.update({'model-paths': [str(ROOT / 'models')], 'macro-paths': [str(ROOT / 'macros')],
                   'test-paths': [str(ROOT / 'tests')], 'packages-install-path': str(ROOT / 'dbt_packages')})
    project_config = project / 'dbt_project.yml'
    rendered = yaml.safe_dump(config, sort_keys=False)
    if not project_config.exists() or project_config.read_text(encoding='utf-8') != rendered:
        project_config.write_text(rendered, encoding='utf-8')
    manifest = Path(environment['SOCCER_DBT_TARGET_PATH']) / 'semantic_manifest.json'
    inputs = [project_config, ROOT / 'dbt_project.yml', ROOT / 'profiles.yml',
              ROOT / 'packages.yml',
              *ROOT.glob('models/**/*.yml'), *ROOT.glob('models/**/*.sql'),
              *ROOT.glob('macros/**/*.sql')]
    settings = {key: environment.get(key) for key in (
        'DUCKDB_PATH', 'DBT_TARGET', 'DATABRICKS_HOST', 'DATABRICKS_HTTP_PATH',
        'DATABRICKS_CATALOG', 'DATABRICKS_SCHEMA', 'DATABRICKS_TOKEN')}
    fingerprint = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    signature = project / 'connection.sha256'
    changed = not signature.exists() or signature.read_text(encoding='utf-8') != fingerprint
    if changed or not manifest.exists() or manifest.stat().st_mtime < max(path.stat().st_mtime for path in inputs):
        _run('dbt', ['parse', '--profiles-dir', str(ROOT)], environment)
        signature.write_text(fingerprint, encoding='utf-8')


@st.cache_data(ttl=300, show_spinner=False)
def rates_for_stints(stint_ids: tuple[str, ...], group_by: str = 'player') -> pd.DataFrame:
    """MetricFlow owns rate aggregation; the exact selected stints define the scope."""
    if group_by not in ('player', 'player_season__season'):
        raise ValueError('Unsupported semantic grouping')
    if not stint_ids:
        return pd.DataFrame(columns=[group_by, *CANONICAL_METRICS])
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+', value) for value in stint_ids):
        raise ValueError('Invalid stint ID')
    where = "{{ Dimension('player_season__stint_id') }} in (" + ','.join(
        "'" + value + "'" for value in stint_ids) + ')'
    environment = _environment()
    folder = ROOT / 'data/migrations'
    folder.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        _prepare(environment)
        with tempfile.TemporaryDirectory(dir=folder) as temporary:
            output = Path(temporary) / 'metrics.csv'
            metrics = [*CANONICAL_METRICS, *(column + '_additive' for column in ADDITIVE_COLS), 'rating_weighted']
            _run('mf', ['query', '--metrics', ','.join(metrics),
                        '--group-by', group_by, '--where', where, '--csv', str(output), '--quiet'], environment)
            return pd.read_csv(output).rename(columns={
                **{column + '_additive': column for column in ADDITIVE_COLS}, 'rating_weighted': 'rating'})


def query_rows(rows: pd.DataFrame, group_by: str = 'player') -> pd.DataFrame:
    ids = tuple(sorted(set(rows['player_season_id'].astype(str))))
    return rates_for_stints(ids, group_by)
