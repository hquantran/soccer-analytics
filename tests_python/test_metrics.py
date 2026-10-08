"""Cross-consumer contract and real MetricFlow SQL aggregation checks."""
import json
import unittest
from pathlib import Path

import pandas as pd

from config.metrics import CANONICAL_METRICS
from dashboard.metrics_config import MetricSpec, compute_metric
from dashboard.recommender import ensure_recommender_features

ROOT = Path(__file__).resolve().parents[1]


class MetricContractTests(unittest.TestCase):
    def test_weighted_multiseason_and_zero(self):
        rows = pd.DataFrame([
            dict(minutes=90, goals=2, assists=1, passes_key=3, tackles_total=4,
                 passes_total=10, passes_completed=8, duels_total=5, duels_won=3,
                 dribbles_attempts=4, dribbles_success=2),
            dict(minutes=810, goals=1, assists=2, passes_key=6, tackles_total=8,
                 passes_total=30, passes_completed=27, duels_total=15, duels_won=9,
                 dribbles_attempts=8, dribbles_success=6),
        ])
        sums = rows.sum().to_dict()
        expected = dict(goals_per90=.3, assists_per90=.3, key_passes_per90=.9,
                        tackles_per90=1.2, pass_accuracy_pct=87.5, duel_success_pct=60,
                        dribble_attempts_per90=1.2, dribble_success_pct=800/12)
        for key, value in expected.items():
            spec = MetricSpec(key, key, 'unused')
            self.assertAlmostEqual(compute_metric(sums, spec), value)
            self.assertIsNone(compute_metric({col: 0 for col in sums}, spec))
        enriched = ensure_recommender_features(pd.DataFrame([sums]))
        self.assertAlmostEqual(enriched.iloc[0]['dribble_attempts_per90'], 1.2)
        self.assertAlmostEqual(enriched.iloc[0]['dribble_success_pct'], 800/12)
        self.assertNotIn('dribbles_per90', enriched.columns)
        self.assertNotAlmostEqual(rows.goals.mul(90).div(rows.minutes).mean(), .3)

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
            self.assertEqual(numerator['expr'], f"{contract['numerator']} * {contract['scale']}")
            self.assertEqual(denominator['expr'], contract['denominator'])
            self.assertEqual(numerator['agg'], 'sum')
            self.assertEqual(denominator['agg'], 'sum')
            self.assertEqual(metrics[key]['type'], 'ratio')

    def test_power_bi_contract(self):
        dax = (ROOT / 'docs/power-bi-measures.dax').read_text()
        for contract in CANONICAL_METRICS.values():
            expression = (
                f"DIVIDE({contract['scale']} * SUM(bi_player_seasons[{contract['numerator']}]), "
                f"SUM(bi_player_seasons[{contract['denominator']}]))"
            )
            self.assertIn(expression, dax)


if __name__ == '__main__':
    unittest.main()
