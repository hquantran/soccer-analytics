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
            env = dict(os.environ, DBT_TARGET='dev', DUCKDB_PATH=str(database),
                       PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
            columns = ('minutes', 'goals', 'assists', 'passes_key', 'tackles_total',
                       'passes_total', 'passes_completed', 'duels_total', 'duels_won',
                       'dribbles_attempts', 'dribbles_success',
                       'shots_total', 'shots_on_target', 'fouls_committed', 'fouls_drawn')
            cases = [
                ([(90, 2, 1, 3, 4, 10, 8, 5, 3, 4, 2, 10, 4, 2, 3),
                  (810, 1, 2, 6, 8, 30, 27, 15, 9, 8, 6, 20, 8, 4, 6)],
                 dict(goals_per90=.3, assists_per90=.3, key_passes_per90=.9,
                      tackles_per90=1.2, pass_accuracy_pct=87.5, duel_success_pct=60,
                      dribble_attempts_per90=1.2, dribble_success_pct=800/12,
                        goal_involvements_per90=.6, successful_dribbles_per90=.8,
                        shot_accuracy_pct=40, goal_conversion_pct=10, fouls_per_tackle=.5,
                        shots_per90=3, passes_per90=4, fouls_drawn_per90=.9)),
                ([(0,) * len(columns)], {key: None for key in CANONICAL_METRICS}),
            ]
            for rows, expected in cases:
                frame = pd.DataFrame(rows, columns=columns)
                frame['player_id'] = 1
                frame['player_season_id'] = [f'stint_{i}' for i in range(len(frame))]
                frame['season_start_date'] = pd.to_datetime(['2020-01-01', '2021-01-01'][:len(rows)])
                excluded = frame.iloc[0].copy()
                excluded['player_id'] = 2
                excluded['player_season_id'] = 'excluded'
                excluded['goals'] = 999
                excluded['minutes'] = 90
                frame = pd.concat([frame, excluded.to_frame().T], ignore_index=True)
                frame[list(columns)] = frame[list(columns)].apply(pd.to_numeric)
                frame['player_id'] = pd.to_numeric(frame['player_id'])
                frame['season_start_date'] = pd.to_datetime(frame['season_start_date'])
                with duckdb.connect(str(database)) as conn:
                    conn.register('fixture', frame)
                    conn.execute('create or replace table main.fct_player_seasons as select * from fixture')
                output = Path(temporary) / 'result.csv'
                result = subprocess.run(
                    [str(mf), 'query', '--metrics', ','.join(CANONICAL_METRICS), '--group-by', 'player',
                     '--where', "{{ Dimension('player_season__stint_id') }} in ('stint_0', 'stint_1')", '--csv', str(output)],
                    cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8', timeout=90,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                result_frame = pd.read_csv(output)
                self.assertEqual(len(result_frame), 1)
                self.assertEqual(int(result_frame.iloc[0]['player']), 1)
                actual = result_frame.iloc[0]
                for key, value in expected.items():
                    if value is None:
                        self.assertTrue(pd.isna(actual[key]), key)
                    else:
                        self.assertAlmostEqual(float(actual[key]), value, places=9, msg=key)


if __name__ == '__main__':
    unittest.main()
