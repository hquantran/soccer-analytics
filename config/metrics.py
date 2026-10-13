"""Canonical rate contract shared with dbt; sum inputs before computing a rate."""
from pathlib import Path

import yaml

CANONICAL_METRICS = yaml.safe_load(
    (Path(__file__).resolve().parents[1] / 'dbt_project.yml').read_text(encoding='utf-8')
)['vars']['canonical_metrics']
