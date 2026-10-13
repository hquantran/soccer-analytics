"""Deterministic scouting findings built from the semantic dashboard results."""

from dataclasses import asdict, dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass
class Finding:
    finding_type: str
    severity: str
    metric: str
    current_value: float
    previous_value: Optional[float]
    peer_benchmark: float
    percentile: float
    sample_size: float
    evidence: str
    reason: str
    confidence: str
    gemini_explanation: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class ScoutEngine:
    """Analyze one aggregated player row against same-position peers."""

    MIN_MINUTES_THRESHOLD = 900
    ELITE_METRICS = {
        "goals_per90": "Goals / 90",
        "goal_involvements_per90": "Goal involvements / 90",
        "key_passes_per90": "Key passes / 90",
        "tackles_per90": "Tackles / 90",
        "duel_success_pct": "Duel win %",
        "pass_accuracy_pct": "Pass accuracy %",
        "dribble_success_pct": "Dribble success %",
    }

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    @staticmethod
    def _number(row: pd.Series, column: str, default: float = 0.0) -> float:
        value = pd.to_numeric(row.get(column, default), errors="coerce")
        return float(value) if pd.notna(value) and np.isfinite(value) else default

    @staticmethod
    def _percentile(values: pd.Series, value: float) -> float:
        numeric = pd.to_numeric(values, errors="coerce").dropna()
        if numeric.empty:
            return 50.0
        return float((numeric < value).mean() * 100)

    def analyze_player(self, player_id: int | str, season: str | None = None) -> list[Finding]:
        """Return explainable rule findings for a player in ``self.df``.

        ``season`` remains for backwards compatibility; the dashboard passes an
        already aggregated, one-row-per-player table, so it is not required.
        """
        del season
        if "player_id" not in self.df.columns:
            return []

        matched = self.df[self.df["player_id"].astype(str) == str(player_id)]
        if matched.empty:
            return []
        player = matched.iloc[0]
        position = player.get("position")
        peers = self.df[self.df["position"] == position] if position is not None else self.df
        if peers.empty:
            peers = matched

        minutes = self._number(player, "minutes")
        findings: list[Finding] = []

        if minutes < self.MIN_MINUTES_THRESHOLD:
            peer_minutes = pd.to_numeric(peers.get("minutes", pd.Series(dtype=float)), errors="coerce")
            findings.append(
                Finding(
                    finding_type="sample_size_warning",
                    severity="HIGH" if minutes < 450 else "MEDIUM",
                    metric="Minutes",
                    current_value=minutes,
                    previous_value=None,
                    peer_benchmark=float(peer_minutes.median()) if peer_minutes.notna().any() else 0.0,
                    percentile=self._percentile(peer_minutes, minutes),
                    sample_size=minutes,
                    evidence=f"Player has accumulated {minutes:.0f} minutes in the selected data window.",
                    reason="Below the 900-minute stability threshold; rate metrics may be volatile.",
                    confidence="LOW",
                )
            )

        # The source currently has goals and shots, but no non-penalty goals or xG.
        if "goals_per90" in peers.columns and "shots_per90" in peers.columns:
            goals_90 = self._number(player, "goals_per90")
            shots_90 = self._number(player, "shots_per90")
            shot_percentile = self._percentile(peers["shots_per90"], shots_90)
            if goals_90 > 0.4 and shot_percentile < 50:
                findings.append(
                    Finding(
                        finding_type="high_output_low_volume",
                        severity="HIGH" if minutes < self.MIN_MINUTES_THRESHOLD else "MEDIUM",
                        metric="Goals / 90",
                        current_value=goals_90,
                        previous_value=None,
                        peer_benchmark=float(pd.to_numeric(peers["goals_per90"], errors="coerce").median()),
                        percentile=self._percentile(peers["goals_per90"], goals_90),
                        sample_size=minutes,
                        evidence=(
                            f"Goals / 90 is {goals_90:.2f}; shots / 90 is {shots_90:.2f} "
                            f"({shot_percentile:.0f}th positional percentile)."
                        ),
                        reason="Scoring output is high relative to shot volume; investigate conversion sustainability.",
                        confidence="HIGH" if minutes >= self.MIN_MINUTES_THRESHOLD else "LOW",
                    )
                )

        for column, label in self.ELITE_METRICS.items():
            if column not in player.index or column not in peers.columns:
                continue
            value = self._number(player, column, default=float("nan"))
            peer_values = pd.to_numeric(peers[column], errors="coerce").dropna()
            if not np.isfinite(value) or peer_values.empty:
                continue
            percentile = self._percentile(peer_values, value)
            if percentile >= 90:
                findings.append(
                    Finding(
                        finding_type="elite_strength",
                        severity="INFO",
                        metric=label,
                        current_value=value,
                        previous_value=None,
                        peer_benchmark=float(peer_values.median()),
                        percentile=percentile,
                        sample_size=minutes,
                        evidence=f"Ranks at the {percentile:.0f}th percentile among same-position peers for {label}.",
                        reason="Metric is at or above the 90th positional percentile in this data window.",
                        confidence="HIGH" if minutes >= self.MIN_MINUTES_THRESHOLD else "LOW",
                    )
                )

        return findings
