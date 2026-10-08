"""Execute the real semantic graph on synthetic facts, without provider data."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb
import pandas as pd

from config.metrics import CANONICAL_METRICS

ROOT = Path(__file__).resolve().parents[1]


class MetricFlowExecutionTests(unittest.TestCase):
    def test_multiseason_and_zero_denominators(self):
        folder = ROOT / 'data/migrations'
        folder.mkdir(parents=True, exist_ok=True)
        mf = Path(sys.executable).parent / ('mf.exe' if os.name == 'nt' else 'mf')
        with tempfile.TemporaryDirectory(dir=folder) as temporary:
            # Keep the catalog name used by the local semantic manifest.
            database = Path(temporary) / 'api_sports.duckdb'
            env = dict(os.environ, DBT_TARGET='dev', DUCKDB_PATH=str(database), PYTHONIOENCODING='utf-8')
            columns = ('minutes', 'goals', 'assists', 'passes_key', 'tackles_total',
                       'passes_total', 'passes_completed', 'duels_total', 'duels_won',
                       'dribbles_attempts', 'dribbles_success')
            cases = [
                ([(90, 2, 1, 3, 4, 10, 8, 5, 3, 4, 2),
                  (810, 1, 2, 6, 8, 30, 27, 15, 9, 8, 6)],
                 dict(goals_per90=.3, assists_per90=.3, key_passes_per90=.9,
                      tackles_per90=1.2, pass_accuracy_pct=87.5, duel_success_pct=60,
                      dribble_attempts_per90=1.2, dribble_success_pct=800/12)),
                ([(0,) * len(columns)], {key: None for key in CANONICAL_METRICS}),
            ]
            for rows, expected in cases:
                frame = pd.DataFrame(rows, columns=columns)
                frame['season_start_date'] = pd.to_datetime(['2020-01-01', '2021-01-01'][:len(rows)])
                with duckdb.connect(str(database)) as conn:
                    conn.register('fixture', frame)
                    conn.execute('create or replace table main.fct_player_seasons as select * from fixture')
                output = Path(temporary) / 'result.csv'
                result = subprocess.run(
                    [str(mf), 'query', '--metrics', ','.join(CANONICAL_METRICS), '--csv', str(output)],
                    cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', timeout=90,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                actual = pd.read_csv(output).iloc[0]
                for key, value in expected.items():
                    if value is None:
                        self.assertTrue(pd.isna(actual[key]), key)
                    else:
                        self.assertAlmostEqual(float(actual[key]), value, places=9, msg=key)


if __name__ == '__main__':
    unittest.main()
