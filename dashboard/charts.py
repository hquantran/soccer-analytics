"""Plotly chart builders for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.metrics_config import ScatterAxes, ScatterView

PLOT_BG = "#1C232B"
PAPER_BG = "#101417"
GRID = "#2A333C"
TEXT = "#E7D8C6"
MUTED = "#A89888"
ACCENT_A = "#C36A4A"
ACCENT_A_FILL = "rgba(195, 106, 74, 0.35)"
ACCENT_B = "#4A90A4"
ACCENT_B_FILL = "rgba(74, 144, 164, 0.30)"
PEER_DOT = "rgba(167, 152, 136, 0.35)"
HIGHLIGHT_RING = "#E7D8C6"


def _base_layout(**kwargs) -> dict:
    layout = {
        "paper_bgcolor": PAPER_BG,
        "plot_bgcolor": PLOT_BG,
        "font": dict(family="DM Sans, sans-serif", color=TEXT, size=13),
        "margin": dict(l=56, r=48, t=64, b=56),
    }
    layout.update(kwargs)
    return layout


@st.cache_data(show_spinner=False)
def build_radar_chart(labels: list[str], percentiles: list[float], player_name: str) -> go.Figure:
    if not labels or not percentiles:
        fig = go.Figure()
        fig.update_layout(
            **_base_layout(
                title=dict(text="Radar unavailable — not enough peer data", font=dict(size=14, color=MUTED)),
                height=520,
            )
        )
        return fig

    # Short angular labels reduce overlap / compression
    short = [lab.replace(" / 90", "/90").replace(" conversion", " conv.") for lab in labels]
    r = percentiles + [percentiles[0]]
    theta = short + [short[0]]
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=r,
            theta=theta,
            fill="toself",
            fillcolor=ACCENT_A_FILL,
            line=dict(color=ACCENT_A, width=2.5),
            marker=dict(size=7, color=ACCENT_A),
            name=player_name,
            customdata=labels + [labels[0]],
            hovertemplate="%{customdata}<br>Percentile: %{r:.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            title=dict(text="Position percentile profile", font=dict(size=16, color=TEXT)),
            height=580,
            showlegend=False,
            margin=dict(l=80, r=80, t=64, b=80),
            polar=dict(
                bgcolor=PLOT_BG,
                domain=dict(x=[0.08, 0.92], y=[0.08, 0.92]),
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[0, 25, 50, 75, 100],
                    gridcolor=GRID,
                    linecolor=GRID,
                    tickfont=dict(color=MUTED, size=10),
                ),
                angularaxis=dict(
                    gridcolor=GRID,
                    linecolor=GRID,
                    rotation=90,
                    direction="clockwise",
                    tickfont=dict(color=TEXT, size=11),
                ),
            ),
        )
    )
    return fig


@st.cache_data(show_spinner=False)
def build_comparison_radar(
    labels: list[str],
    values_a: list[float],
    values_b: list[float],
    name_a: str,
    name_b: str,
) -> go.Figure:
    fig = go.Figure()
    if not labels:
        fig.update_layout(**_base_layout(height=540, title=dict(text="Radar unavailable", font=dict(color=MUTED))))
        return fig

    theta_labels = [lab.replace(" / 90", "/90").replace(" conversion", " conv.") for lab in labels]
    theta = theta_labels + [theta_labels[0]]
    fig.add_trace(
        go.Scatterpolar(
            r=values_a + [values_a[0]],
            theta=theta,
            fill="toself",
            fillcolor=ACCENT_A_FILL,
            line=dict(color=ACCENT_A, width=2.5),
            name=name_a,
            customdata=labels + [labels[0]],
            hovertemplate="%{customdata}<br>" + name_a + " percentile: %{r:.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatterpolar(
            r=values_b + [values_b[0]],
            theta=theta,
            fill="toself",
            fillcolor=ACCENT_B_FILL,
            line=dict(color=ACCENT_B, width=2.5),
            name=name_b,
            customdata=labels + [labels[0]],
            hovertemplate="%{customdata}<br>" + name_b + " percentile: %{r:.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            title=dict(text=f"{name_a} vs {name_b} · positional percentiles", font=dict(size=16, color=TEXT)),
            height=600,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.08,
                font=dict(color=MUTED),
                bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=80, r=140, t=64, b=80),
            polar=dict(
                bgcolor=PLOT_BG,
                domain=dict(x=[0.05, 0.85], y=[0.08, 0.92]),
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickvals=[0, 25, 50, 75, 100],
                    ticksuffix="",
                    title=dict(text="Percentile", font=dict(size=11, color=MUTED)),
                    gridcolor=GRID,
                    linecolor=GRID,
                    tickfont=dict(color=MUTED, size=10),
                ),
                angularaxis=dict(
                    gridcolor=GRID,
                    linecolor=GRID,
                    rotation=90,
                    direction="clockwise",
                    tickfont=dict(color=TEXT, size=11),
                ),
            ),
        )
    )
    return fig


@st.cache_data(show_spinner=False)
def build_quadrant_scatter(
    peer_table: pd.DataFrame,
    axes: ScatterAxes,
    position: str,
    title: str | None = None,
    highlights: list[tuple[int, str, str]] | None = None,
    insight: str | None = None,
) -> go.Figure:
    """highlights: list of (player_id, display_name, color)."""
    fig = go.Figure()
    if peer_table.empty or axes.x_key not in peer_table.columns or axes.y_key not in peer_table.columns:
        fig.update_layout(
            **_base_layout(
                title=dict(
                    text="Scatter unavailable — missing axis data for this peer pool",
                    font=dict(size=14, color=MUTED),
                ),
                height=560,
            )
        )
        return fig

    plot_df = peer_table.dropna(subset=[axes.x_key, axes.y_key]).copy()
    if plot_df.empty:
        fig.update_layout(
            **_base_layout(
                title=dict(
                    text="Scatter unavailable — no peers with both axis metrics",
                    font=dict(size=14, color=MUTED),
                ),
                height=560,
            )
        )
        return fig

    # Sparse pools (few complete peers) look "broken"; still plot but flag in title.
    sparse = len(plot_df) < 8
    x_mean = float(plot_df[axes.x_key].mean())
    y_mean = float(plot_df[axes.y_key].mean())
    highlight_ids = {h[0] for h in (highlights or [])}
    others = plot_df[~plot_df["player_id"].isin(highlight_ids)]

    if not others.empty:
        fig.add_trace(
            go.Scatter(
                x=others[axes.x_key],
                y=others[axes.y_key],
                mode="markers",
                marker=dict(size=8, color=PEER_DOT, line=dict(width=0)),
                name=f"Other {position.lower()}s",
                hovertemplate="%{text}<br>"
                + axes.x_label
                + ": %{x:.2f}<br>"
                + axes.y_label
                + ": %{y:.2f}<extra></extra>",
                text=others["player_name"],
            )
        )

    missing_highlights: list[str] = []
    for player_id, label, color in highlights or []:
        selected = plot_df[plot_df["player_id"] == player_id]
        if selected.empty:
            missing_highlights.append(label)
            continue
        row = selected.iloc[0]
        fig.add_trace(
            go.Scattergl(
                x=[row[axes.x_key]],
                y=[row[axes.y_key]],
                mode="markers+text",
                marker=dict(size=18, color=color, line=dict(color=HIGHLIGHT_RING, width=1.5)),
                text=[label],
                textposition="top center",
                textfont=dict(color=TEXT, size=12, family="Space Grotesk, sans-serif"),
                name=label,
                hovertemplate="%{text}<br>"
                + axes.x_label
                + ": %{x:.2f}<br>"
                + axes.y_label
                + ": %{y:.2f}<extra></extra>",
            )
        )

    fig.add_vline(x=x_mean, line_dash="dot", line_color=MUTED, line_width=1.5)
    fig.add_hline(y=y_mean, line_dash="dot", line_color=MUTED, line_width=1.5)

    # Pad ranges so single/sparse points aren't stuck on the edge
    x_vals = plot_df[axes.x_key].astype(float)
    y_vals = plot_df[axes.y_key].astype(float)
    x_pad = max((x_vals.max() - x_vals.min()) * 0.08, abs(x_vals.mean()) * 0.05 + 0.05)
    y_pad = max((y_vals.max() - y_vals.min()) * 0.08, abs(y_vals.mean()) * 0.05 + 0.05)

    chart_title = title or f"{position} quadrant · {axes.x_label} vs {axes.y_label}"
    if sparse:
        chart_title = f"{chart_title} · limited peer sample ({len(plot_df)})"
    if missing_highlights:
        chart_title = f"{chart_title} · missing: {', '.join(missing_highlights)}"

    fig.update_layout(
        **_base_layout(
            title=dict(text=chart_title, font=dict(size=15, color=TEXT)),
            height=560,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
                font=dict(color=MUTED),
                bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=56, r=160, t=72, b=56),
            xaxis=dict(
                title=axes.x_label,
                range=[float(x_vals.min()) - x_pad, float(x_vals.max()) + x_pad],
                gridcolor=GRID,
                zeroline=False,
                color=MUTED,
                title_font=dict(color=TEXT),
            ),
            yaxis=dict(
                title=axes.y_label,
                range=[float(y_vals.min()) - y_pad, float(y_vals.max()) + y_pad],
                gridcolor=GRID,
                zeroline=False,
                color=MUTED,
                title_font=dict(color=TEXT),
            ),
        )
    )
    return fig


@st.cache_data(show_spinner=False)
def build_scatter_from_view(
    peer_table: pd.DataFrame,
    view: ScatterView,
    position: str,
    highlights: list[tuple[int, str, str]] | None = None,
) -> go.Figure:
    return build_quadrant_scatter(
        peer_table,
        view.axes,
        position,
        title=view.title,
        highlights=highlights,
        insight=view.insight,
    )


@st.cache_data(show_spinner=False)
def build_metric_distribution(
    peer_table: pd.DataFrame,
    metric_key: str,
    metric_label: str,
    highlight_ids: list[int] | None = None,
) -> go.Figure:
    """Histogram of a tactical metric for the filtered peer pool."""
    fig = go.Figure()
    if peer_table.empty or metric_key not in peer_table.columns:
        fig.update_layout(
            **_base_layout(
                title=dict(text="Distribution unavailable", font=dict(size=14, color=MUTED)),
                height=320,
            )
        )
        return fig

    series = peer_table[metric_key].dropna()
    if series.empty:
        fig.update_layout(**_base_layout(height=320))
        return fig

    fig.add_trace(
        go.Histogram(
            x=series,
            nbinsx=min(24, max(8, int(len(series) ** 0.5) * 2)),
            marker=dict(color="rgba(74, 144, 164, 0.55)", line=dict(width=0)),
            name=metric_label,
            hovertemplate=metric_label + ": %{x:.2f}<br>Players: %{y}<extra></extra>",
        )
    )
    mean_val = float(series.mean())
    fig.add_vline(x=mean_val, line_dash="dot", line_color=ACCENT_A, line_width=2)

    if highlight_ids:
        tops = peer_table[peer_table["player_id"].isin(highlight_ids)]
        if not tops.empty and metric_key in tops.columns:
            fig.add_trace(
                go.Scattergl(
                    x=tops[metric_key],
                    y=[0] * len(tops),
                    mode="markers",
                    marker=dict(size=11, color=ACCENT_A, symbol="diamond"),
                    name="Top 5",
                    hovertemplate="%{text}<br>" + metric_label + ": %{x:.2f}<extra></extra>",
                    text=tops["player_name"],
                )
            )

    fig.update_layout(
        **_base_layout(
            title=dict(text=f"{metric_label} · position distribution", font=dict(size=15, color=TEXT)),
            height=340,
            showlegend=False,
            margin=dict(l=48, r=24, t=56, b=48),
            xaxis=dict(title=metric_label, gridcolor=GRID, color=MUTED, title_font=dict(color=TEXT)),
            yaxis=dict(title="Players", gridcolor=GRID, color=MUTED, title_font=dict(color=TEXT)),
        )
    )
    return fig


@st.cache_data(show_spinner=False)
def build_season_trend_chart(trend_df: pd.DataFrame, player_name: str) -> go.Figure:
    """Dual-axis: minutes (bars/left) vs primary per-90 metric (line/right)."""
    fig = go.Figure()
    if trend_df.empty:
        fig.update_layout(
            **_base_layout(
                title=dict(text="Trend unavailable", font=dict(size=14, color=MUTED)),
                height=360,
            )
        )
        return fig

    primary_label = str(trend_df["primary_label"].iloc[0])
    fig.add_trace(
        go.Bar(
            x=trend_df["season_label"],
            y=trend_df["minutes"],
            name="Minutes",
            marker=dict(color="rgba(74, 144, 164, 0.55)", line=dict(width=0)),
            yaxis="y",
            hovertemplate="%{x}<br>Minutes: %{y:.0f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trend_df["season_label"],
            y=trend_df["primary_value"],
            name=primary_label,
            mode="lines+markers",
            line=dict(color=ACCENT_A, width=2.5),
            marker=dict(size=9, color=ACCENT_A),
            yaxis="y2",
            hovertemplate="%{x}<br>" + primary_label + ": %{y:.2f}<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            title=dict(text=f"{player_name} · season trajectory", font=dict(size=16, color=TEXT)),
            height=380,
            barmode="overlay",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(color=MUTED),
                bgcolor="rgba(0,0,0,0)",
            ),
            margin=dict(l=56, r=64, t=72, b=48),
            xaxis=dict(title="Season", gridcolor=GRID, color=MUTED, title_font=dict(color=TEXT)),
            yaxis=dict(
                title="Minutes",
                gridcolor=GRID,
                color=MUTED,
                title_font=dict(color=TEXT),
                zeroline=False,
            ),
            yaxis2=dict(
                title=primary_label,
                overlaying="y",
                side="right",
                gridcolor="rgba(0,0,0,0)",
                color=ACCENT_A,
                title_font=dict(color=ACCENT_A),
                zeroline=False,
            ),
        )
    )
    return fig
