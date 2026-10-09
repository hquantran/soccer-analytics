"""Cross-consumer contract and real MetricFlow SQL aggregation checks."""
import json
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

    def test_parsed_semantic_contract(self):
        manifest = json.loads((ROOT / 'target/manifest.json').read_text(encoding='utf-8'))
        models = {value['name']: value for value in manifest['semantic_models'].values()}
        measures = {m['name']: m for m in models['player_seasons']['measures']}
        metrics = {value['name']: value for value in manifest['metrics'].values()}
        for key, contract in CANONICAL_METRICS.items():
            params = metrics[key]['type_params']
            num_metric = params['numerator']['name']
            den_metric = params['denominator']['name']
            numerator = measures[metrics[num_metric]['type_params']['measure']['name']]
            denominator = measures[metrics[den_metric]['type_params']['measure']['name']]
            inputs = contract['numerator']
            expr = inputs if isinstance(inputs, str) else "(" + " + ".join(inputs) + ")"
            self.assertEqual(numerator['expr'], f"{expr} * {contract['scale']}")
            self.assertEqual(denominator['expr'], contract['denominator'])
            self.assertEqual(numerator['agg'], 'sum')
            self.assertEqual(denominator['agg'], 'sum')
            self.assertEqual(metrics[key]['type'], 'ratio')

    def test_power_bi_contract(self):
        dax = (ROOT / 'docs/power-bi-measures.dax').read_text()
        for contract in CANONICAL_METRICS.values():
            inputs = contract['numerator']
            inputs = [inputs] if isinstance(inputs, str) else inputs
            numerator = " + ".join(f"SUM(bi_player_seasons[{column}])" for column in inputs)
            if len(inputs) > 1:
                numerator = f"({numerator})"
            expression = (
                f"DIVIDE({contract['scale']} * {numerator}, "
                f"SUM(bi_player_seasons[{contract['denominator']}]))"
            )
            self.assertIn(expression, dax)


if __name__ == '__main__':
    unittest.main()
