"""Shared metric and Power BI formula contract checks."""
import unittest
from pathlib import Path

import pandas as pd

from config.metrics import CANONICAL_METRICS
from dashboard.metrics_config import MetricSpec
from dashboard.recommender import ensure_recommender_features

ROOT = Path(__file__).resolve().parents[1]


class MetricContractTests(unittest.TestCase):
    def test_recommender_preserves_semantic_metrics(self):
        from dashboard.recommender import FEATURE_COLS
        frame = pd.DataFrame([{key: 0.123 for key in FEATURE_COLS}])
        frame['goals'] = 999
        frame['minutes'] = 1
        enriched = ensure_recommender_features(frame)
        pd.testing.assert_frame_equal(frame, enriched)
        self.assertEqual(MetricSpec('goal_involvements_per90', 'G+A').numerator, ('goals', 'assists'))
        with self.assertRaises(ValueError):
            ensure_recommender_features(frame.drop(columns=['goals_per90']))

    def test_power_bi_contract(self):
        dax = (ROOT / 'powerbi/measures.dax').read_text(encoding='utf-8')
        for contract in CANONICAL_METRICS.values():
            inputs = contract['numerator']
            inputs = [inputs] if isinstance(inputs, str) else inputs
            numerator = " + ".join(f"SUM(fct_player_seasons[{column}])" for column in inputs)
            if len(inputs) > 1:
                numerator = f"({numerator})"
            expression = (
                f"DIVIDE({contract['scale']} * {numerator}, "
                f"SUM(fct_player_seasons[{contract['denominator']}]))"
            )
            self.assertIn(expression, dax)


if __name__ == '__main__':
    unittest.main()
