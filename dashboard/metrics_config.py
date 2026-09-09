"""Position-specific metric and scatter definitions for the Streamlit dashboard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    numerator: str
    denominator: str | None = None
    scale: float = 1.0
    format: str = "{:.2f}"
    higher_is_better: bool = True


@dataclass(frozen=True)
class ScatterAxes:
    x_key: str
    x_label: str
    x_numerator: str
    x_denominator: str | None
    x_scale: float
    y_key: str
    y_label: str
    y_numerator: str
    y_denominator: str | None
    y_scale: float


@dataclass(frozen=True)
class ScatterView:
    id: str
    title: str
    insight: str
    axes: ScatterAxes
    # For defender fouls chart, ideal is high x / low y
    ideal_quadrant: str = "top-right"  # or "bottom-right"


ADDITIVE_COLS = [
    "minutes",
    "appearances",
    "goals",
    "assists",
    "shots_total",
    "shots_on_target",
    "passes_total",
    "passes_completed",
    "passes_key",
    "tackles_total",
    "duels_total",
    "duels_won",
    "dribbles_attempts",
    "dribbles_success",
    "fouls_drawn",
    "fouls_committed",
]

# BI season-grain rates that match MetricSpec formulas exactly.
# Do NOT include bi.dribbles_per90 — BI uses dribbles_success, UI uses attempts.
BI_RATE_KEYS = frozenset(
    {
        "goals_per90",
        "assists_per90",
        "goal_involvements_per90",
        "key_passes_per90",
        "tackles_per90",
        "shot_accuracy_pct",
        "goal_conversion_pct",
        "pass_accuracy_pct",
        "dribble_success_pct",
        "duel_success_pct",
        "fouls_per_tackle",
    }
)


POSITION_METRICS: dict[str, dict[str, list[MetricSpec]]] = {
    "Attacker": {
        "primary": [
            MetricSpec("goals_per90", "Goals / 90", "goals", "minutes", 90.0),
            MetricSpec("goal_involvements_per90", "G+A / 90", "goals", "minutes", 90.0),
            MetricSpec("goal_conversion_pct", "Conversion %", "goals", "shots_total", 100.0, "{:.1f}%"),
            MetricSpec("shot_accuracy_pct", "Shot accuracy %", "shots_on_target", "shots_total", 100.0, "{:.1f}%"),
            MetricSpec("shots_per90", "Shots / 90", "shots_total", "minutes", 90.0),
            MetricSpec("assists_per90", "Assists / 90", "assists", "minutes", 90.0),
        ],
        "secondary": [
            MetricSpec("dribble_success_pct", "Dribble success %", "dribbles_success", "dribbles_attempts", 100.0, "{:.1f}%"),
            MetricSpec("fouls_drawn_per90", "Fouls drawn / 90", "fouls_drawn", "minutes", 90.0),
        ],
    },
    "Midfielder": {
        "primary": [
            MetricSpec("key_passes_per90", "Key passes / 90", "passes_key", "minutes", 90.0),
            MetricSpec("goal_involvements_per90", "G+A / 90", "goals", "minutes", 90.0),
            MetricSpec("passes_per90", "Passes / 90", "passes_total", "minutes", 90.0),
            MetricSpec("pass_accuracy_pct", "Pass accuracy %", "passes_completed", "passes_total", 100.0, "{:.1f}%"),
            MetricSpec("duel_success_pct", "Duel win %", "duels_won", "duels_total", 100.0, "{:.1f}%"),
            MetricSpec("tackles_per90", "Tackles / 90", "tackles_total", "minutes", 90.0),
        ],
        "secondary": [
            MetricSpec("dribble_success_pct", "Dribble success %", "dribbles_success", "dribbles_attempts", 100.0, "{:.1f}%"),
            MetricSpec("assists_per90", "Assists / 90", "assists", "minutes", 90.0),
        ],
    },
    "Defender": {
        "primary": [
            MetricSpec("duel_success_pct", "Duel win %", "duels_won", "duels_total", 100.0, "{:.1f}%"),
            MetricSpec("tackles_per90", "Tackles / 90", "tackles_total", "minutes", 90.0),
            MetricSpec(
                "fouls_per_tackle",
                "Fouls / tackle",
                "fouls_committed",
                "tackles_total",
                1.0,
                "{:.2f}",
                higher_is_better=False,
            ),
            MetricSpec("pass_accuracy_pct", "Pass accuracy %", "passes_completed", "passes_total", 100.0, "{:.1f}%"),
            MetricSpec("key_passes_per90", "Key passes / 90", "passes_key", "minutes", 90.0),
            MetricSpec("dribbles_per90", "Dribbles / 90", "dribbles_attempts", "minutes", 90.0),
        ],
        "secondary": [
            MetricSpec("dribble_success_pct", "Dribble success %", "dribbles_success", "dribbles_attempts", 100.0, "{:.1f}%"),
        ],
    },
}



# Primary output metric used on the multi-season trend chart (right Y-axis).
POSITION_TREND_METRIC: dict[str, str] = {
    "Attacker": "goals_per90",
    "Midfielder": "key_passes_per90",
    "Defender": "tackles_per90",
}


POSITION_SCATTER_VIEWS: dict[str, list[ScatterView]] = {
    "Attacker": [
        ScatterView(
            id="shot_volume_vs_clinicality",
            title="Shot Volume vs Clinicality",
            insight=(
                "Separates volume shooters from clinical finishers. "
                "Top-right = high-volume, elite-converting forwards."
            ),
            axes=ScatterAxes(
                "shots_total",
                "Total shots",
                "shots_total",
                None,
                1.0,
                "goal_conversion_pct",
                "Goal conversion %",
                "goals",
                "shots_total",
                100.0,
            ),
        ),
        ScatterView(
            id="dribble_volume_vs_efficiency",
            title="1v1 Volume vs Dribble Efficiency",
            insight=(
                "Evaluates winger threat. Top-right = elite ball-carriers; "
                "bottom-right = high take-ons but frequent turnovers."
            ),
            axes=ScatterAxes(
                "dribbles_attempts",
                "Dribble attempts",
                "dribbles_attempts",
                None,
                1.0,
                "dribble_success_pct",
                "Dribble success %",
                "dribbles_success",
                "dribbles_attempts",
                100.0,
            ),
        ),
    ],
    "Midfielder": [
        ScatterView(
            id="buildup_vs_creation",
            title="Build-up Volume vs Chance Creation",
            insight=(
                "Deep-lying recyclers sit high-pass / low key-pass; "
                "top-right = tempo controllers who also unlock defenses."
            ),
            axes=ScatterAxes(
                "passes_total",
                "Total passes",
                "passes_total",
                None,
                1.0,
                "key_passes_per90",
                "Key passes / 90",
                "passes_key",
                "minutes",
                90.0,
            ),
        ),
        ScatterView(
            id="defensive_activity_vs_dominance",
            title="Defensive Activity vs Physical Dominance",
            insight=(
                "For holding / box-to-box mids. Top-right = high-workrate, "
                "physically dominant ball-winners."
            ),
            axes=ScatterAxes(
                "tackles_total",
                "Total tackles",
                "tackles_total",
                None,
                1.0,
                "duel_success_pct",
                "Duel success %",
                "duels_won",
                "duels_total",
                100.0,
            ),
        ),
    ],
    "Defender": [
        ScatterView(
            id="engagement_vs_duel_dominance",
            title="Defensive Engagement vs Duel Dominance",
            insight=(
                "Center-backs under pressure. Top-right = brick-wall defenders "
                "who win a high share of many contested duels."
            ),
            axes=ScatterAxes(
                "duels_total",
                "Total duels",
                "duels_total",
                None,
                1.0,
                "duel_success_pct",
                "Duel success %",
                "duels_won",
                "duels_total",
                100.0,
            ),
        ),
        ScatterView(
            id="tackle_volume_vs_discipline",
            title="Defensive Volume vs Discipline / Efficiency",
            insight=(
                "Bottom-right is ideal: high tackle volume with low fouls per tackle — "
                "clean, high-IQ defenders."
            ),
            axes=ScatterAxes(
                "tackles_total",
                "Total tackles",
                "tackles_total",
                None,
                1.0,
                "fouls_per_tackle",
                "Fouls per tackle",
                "fouls_committed",
                "tackles_total",
                1.0,
            ),
            ideal_quadrant="bottom-right",
        ),
    ],
}


def metrics_for_position(position: str) -> dict[str, list[MetricSpec]]:
    return POSITION_METRICS.get(position, POSITION_METRICS["Midfielder"])


def scatter_views_for_position(position: str) -> list[ScatterView]:
    return POSITION_SCATTER_VIEWS.get(position, POSITION_SCATTER_VIEWS["Midfielder"])


def scatter_view_by_id(position: str, view_id: str) -> ScatterView:
    views = scatter_views_for_position(position)
    for view in views:
        if view.id == view_id:
            return view
    return views[0]


def all_metric_specs(position: str) -> list[MetricSpec]:
    blocks = metrics_for_position(position)
    return list(blocks.get("primary", [])) + list(blocks.get("secondary", []))


def radar_metric_specs(position: str) -> list[MetricSpec]:
    """Up to 6 rate/% axes for radar (no volume totals)."""
    rates = [spec for spec in metrics_for_position(position).get("primary", []) if spec.denominator is not None]
    return rates[:6]


# Leaderboard sort options. Labels prefer scouting language; keys map to available API fields
# (API-Football has no xG, SCA, or progressive passes).
TOP_SORT_OPTIONS: dict[str, list[tuple[str, str]]] = {
    "Attacker": [
        ("goals_per90", "Goals / 90"),
        ("goal_involvements_per90", "G+A / 90"),
        ("shots_per90", "Shots / 90"),
        ("goal_conversion_pct", "Conversion %"),
    ],
    "Midfielder": [
        ("key_passes_per90", "Key Passes / 90"),
        ("goal_involvements_per90", "G+A / 90"),
        ("passes_per90", "Passes / 90"),
        ("duel_success_pct", "Duel Win %"),
    ],
    "Defender": [
        ("duel_success_pct", "Duel Win %"),
        ("tackles_per90", "Tackles / 90"),
        ("key_passes_per90", "Key Passes / 90"),
    ],
}

DEFENDER_SUBPOSITIONS = ["All Defenders", "Center-Back profile", "Full-Back profile"]


def trend_metric_for_position(position: str) -> MetricSpec:
    key = POSITION_TREND_METRIC.get(position, "key_passes_per90")
    for spec in all_metric_specs(position):
        if spec.key == key:
            return spec
    return metrics_for_position(position)["primary"][0]


def compute_metric(row_sums: dict[str, float], spec: MetricSpec) -> float | None:
    if spec.key == "goal_involvements_per90":
        goals = row_sums.get("goals")
        assists = row_sums.get("assists")
        if goals is None and assists is None:
            return None
        num = float(goals or 0) + float(assists or 0)
        den = row_sums.get("minutes")
        if den is None or den == 0:
            return None
        return num * 90.0 / float(den)

    num = row_sums.get(spec.numerator)
    if num is None:
        return None
    if spec.denominator is None:
        return float(num)
    den = row_sums.get(spec.denominator)
    if den is None or den == 0:
        return None
    return float(num) * spec.scale / float(den)


def compute_xy(row_sums: dict[str, float], axes: ScatterAxes) -> tuple[float | None, float | None]:
    x_spec = MetricSpec(axes.x_key, axes.x_label, axes.x_numerator, axes.x_denominator, axes.x_scale)
    y_spec = MetricSpec(axes.y_key, axes.y_label, axes.y_numerator, axes.y_denominator, axes.y_scale)
    return compute_metric(row_sums, x_spec), compute_metric(row_sums, y_spec)


def all_scatter_metric_keys(position: str) -> set[str]:
    keys: set[str] = set()
    for view in scatter_views_for_position(position):
        keys.add(view.axes.x_key)
        keys.add(view.axes.y_key)
    return keys
