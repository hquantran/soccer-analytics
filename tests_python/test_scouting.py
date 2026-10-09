import unittest

import pandas as pd

from dashboard.metrics_config import ADDITIVE_COLS
from dashboard.scouting import query_rows
from scripts.generate_power_bi_model import generate, dax_rate
from config.metrics import CANONICAL_METRICS


class ScoutingTests(unittest.TestCase):
    def test_weighted_rollup_and_stored_single_stint(self):
        rows = pd.DataFrame([{**dict.fromkeys(ADDITIVE_COLS, 0), 'player_id': 1,
                              'season': 2023, 'minutes': 900, 'goals': 10, 'rating': 8,
                              'passes_completed': None, 'passes_total': 100, 'goals_per90': 1.0},
                             {**dict.fromkeys(ADDITIVE_COLS, 0), 'player_id': 1,
                              'season': 2024, 'minutes': 1800, 'goals': 5, 'rating': 7,
                              'passes_completed': None, 'passes_total': 200, 'goals_per90': .25}])
        combined = query_rows(rows).iloc[0]
        self.assertEqual(combined.goals_per90, .5)
        self.assertAlmostEqual(combined.rating, 22 / 3)
        self.assertTrue(pd.isna(combined.pass_accuracy_pct))
        self.assertTrue(pd.isna(combined.fouls_per_tackle))
        seasons = query_rows(rows, 'player_season__season')
        self.assertEqual(seasons.goals_per90.tolist(), [1, .25])

    def test_power_bi_generated_contract(self):
        model = generate()
        for contract in CANONICAL_METRICS.values():
            self.assertIn(dax_rate(contract), model)
        self.assertEqual(model.count('crossFilteringBehavior: oneDirection'), 4)
        self.assertNotIn('DATABRICKS_TOKEN', model)


if __name__ == '__main__':
    unittest.main()
