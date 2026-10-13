"""Fast scouting-mart rollups using the shared metric contract."""
import pandas as pd

from config.metrics import CANONICAL_METRICS
from dashboard.metrics_config import ADDITIVE_COLS


def query_rows(rows: pd.DataFrame, group_by: str = 'player') -> pd.DataFrame:
    if group_by not in ('player', 'player_season__season'):
        raise ValueError('Unsupported scouting grouping')
    key = 'player_id' if group_by == 'player' else 'season'
    if rows.empty:
        return pd.DataFrame(columns=[group_by, *ADDITIVE_COLS, *CANONICAL_METRICS, 'rating'])
    grouped = rows.groupby(key, sort=False)
    totals = grouped[ADDITIVE_COLS].sum(min_count=1)
    weighted = rows.assign(_rating_minutes=rows.rating.fillna(0) * rows.minutes)
    totals['rating'] = weighted.groupby(key)._rating_minutes.sum() / totals.minutes.where(totals.minutes != 0)
    for name, contract in CANONICAL_METRICS.items():
        inputs = contract['numerator']
        columns = [inputs] if isinstance(inputs, str) else inputs
        numerator = totals[columns].sum(axis=1, min_count=1)
        denominator = totals[contract['denominator']]
        totals[name] = numerator * contract['scale'] / denominator.where(denominator != 0)
        # Stored rates are valid only when the group contains exactly one stint.
        if name in rows:
            singles = grouped.size().eq(1)
            stored = grouped[name].first()
            totals.loc[singles, name] = stored.loc[singles]
    return totals.rename_axis(group_by).reset_index()
