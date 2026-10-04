"""Shared Streamlit presentation for rules-based findings and AI scouting notes."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard.gemini_scout import (
    ask_custom_scout_question as ask_ai_question,
    explain_all_findings_with_gemini as explain_all_flags_with_ai,
    explain_finding_with_gemini as explain_finding_with_ai,
    init_gemini as is_ai_configured,
    summarize_profile_and_charts_with_gemini as summarize_with_ai,
)
from dashboard.scout_engine import Finding, ScoutEngine


def _finite_number(value) -> float | None:
    try:
        if pd.isna(value):
            return None
        number = float(value)
        return number if pd.notna(number) else None
    except (TypeError, ValueError):
        return None


def build_scatter_chart_context(peer_table: pd.DataFrame, profiles: list[dict], view) -> dict:
    """Describe the selected scatter plot using its plotted values and cohort ranges."""
    axes = {}
    for axis_name, key, label in (
        ("x", view.axes.x_key, view.axes.x_label),
        ("y", view.axes.y_key, view.axes.y_label),
    ):
        values = pd.to_numeric(peer_table.get(key, pd.Series(dtype=float)), errors="coerce").dropna()
        selected = {}
        for profile in profiles:
            player_row = peer_table[peer_table["player_id"].astype(str) == str(profile["player_id"])]
            value = _finite_number(player_row.iloc[0].get(key)) if not player_row.empty else None
            selected[profile["player_name"]] = value
        axes[axis_name] = {
            "metric": label,
            "key": key,
            "selected_player_values": selected,
            "peer_count_with_value": int(values.size),
            "peer_min": _finite_number(values.min()) if not values.empty else None,
            "peer_25th_percentile": _finite_number(values.quantile(0.25)) if not values.empty else None,
            "peer_median": _finite_number(values.median()) if not values.empty else None,
            "peer_75th_percentile": _finite_number(values.quantile(0.75)) if not values.empty else None,
            "peer_max": _finite_number(values.max()) if not values.empty else None,
        }
    return {
        "chart": view.title,
        "interpretation_note": view.insight,
        "ideal_quadrant": view.ideal_quadrant,
        "position": profiles[0]["position"] if profiles else None,
        "axes": axes,
    }


def _profile_summary(profile: dict, peer_table: pd.DataFrame) -> dict:
    metric_summaries = []
    player_rows = peer_table[peer_table["player_id"].astype(str) == str(profile["player_id"])]
    player_index = player_rows.index[0] if not player_rows.empty else None

    for block, specs in profile["metric_specs"].items():
        for spec in specs:
            value = _finite_number(profile["metrics"][block].get(spec.key))
            peer_values = pd.to_numeric(peer_table.get(spec.key, pd.Series(dtype=float)), errors="coerce").dropna()
            percentile = None
            if player_index is not None and spec.key in peer_table:
                ranked = pd.to_numeric(peer_table[spec.key], errors="coerce").rank(
                    pct=True, ascending=spec.higher_is_better, method="average"
                ) * 100
                percentile = _finite_number(ranked.loc[player_index])
            metric_summaries.append(
                {
                    "category": block,
                    "metric": spec.label,
                    "key": spec.key,
                    "value": value,
                    "peer_percentile": round(percentile, 1) if percentile is not None else None,
                    "peer_median": _finite_number(peer_values.median()) if not peer_values.empty else None,
                    "higher_is_better": spec.higher_is_better,
                }
            )

    return {
        "player": profile["player_name"],
        "position": profile["position"],
        "age": _finite_number(profile.get("age")),
        "nationality": profile.get("nationality"),
        "teams": profile.get("teams", []),
        "leagues": profile.get("leagues", []),
        "seasons": profile.get("seasons", []),
        "minutes": _finite_number(profile.get("minutes")),
        "appearances": _finite_number(profile.get("appearances")),
        "rating": _finite_number(profile.get("rating")),
        "peer_cohort_size": int(len(peer_table)),
        "metrics": metric_summaries,
    }


def _render_ai_report(report: dict) -> None:
    """Display model output as a concise, scannable stakeholder briefing."""
    summary = report.get("executive_summary")
    if summary:
        st.success(str(summary))

    takeaways = report.get("key_takeaways") or []
    if takeaways:
        st.markdown("##### Key takeaways")
        for takeaway in takeaways:
            st.markdown(f"- {takeaway}")

    assessments = report.get("player_assessments") or []
    if assessments:
        st.markdown("##### Player-by-player assessment")
        for assessment in assessments:
            st.markdown(f"**{assessment.get('player', 'Player')}**")
            strengths = assessment.get("strengths") or []
            tradeoffs = assessment.get("tradeoffs") or []
            if strengths:
                st.markdown("Strengths: " + " · ".join(str(item) for item in strengths))
            if tradeoffs:
                st.markdown("Trade-offs / uncertainties: " + " · ".join(str(item) for item in tradeoffs))

    metric_rows = report.get("metric_interpretations") or []
    if metric_rows:
        st.markdown("##### Metric interpretation")
        st.dataframe(pd.DataFrame(metric_rows), width="stretch", hide_index=True)

    chart_rows = report.get("chart_reading") or []
    if chart_rows:
        st.markdown("##### Chart reading")
        for chart in chart_rows:
            st.markdown(f"**{chart.get('chart', 'Chart')}** — {chart.get('interpretation', '')}")

    considerations = report.get("decision_considerations") or []
    if considerations:
        st.markdown("##### Decision considerations")
        for item in considerations:
            st.markdown(f"- {item}")

    recommendation = report.get("recommendation")
    if recommendation:
        st.info(f"**Evidence-based guidance:** {recommendation}")

    limitations = report.get("limitations") or []
    if limitations:
        st.markdown("##### Limitations")
        for item in limitations:
            st.markdown(f"- {item}")

    next_steps = report.get("recommended_next_steps") or []
    if next_steps:
        st.markdown("##### Recommended next steps")
        for item in next_steps:
            st.markdown(f"- {item}")


def render_scout_analysis(
    profiles: list[dict],
    peer_table: pd.DataFrame,
    *,
    key_prefix: str,
    chart_context: dict | None = None,
    comparison_mode: bool = False,
) -> None:
    """Render findings for one profile or a same-position player comparison."""
    st.markdown('<div class="viz-spacer"></div>', unsafe_allow_html=True)
    st.markdown('<h3 class="section-title">Scout analysis</h3>', unsafe_allow_html=True)
    st.caption(
        "Rule-based flags compare each player with the same-position peer cohort "
        "used by this page; they complement rather than replace the metrics above."
    )

    engine = ScoutEngine(peer_table)
    results: list[tuple[dict, list[Finding]]] = [
        (profile, engine.analyze_player(profile["player_id"])) for profile in profiles
    ]
    all_entries = [
        {
            "player": profile["player_name"],
            "position": profile["position"],
            "finding": finding.to_dict(),
        }
        for profile, findings in results
        for finding in findings
    ]
    ai_ready = is_ai_configured()

    tabs = st.tabs(
        [f"{profile['player_name']} · findings" for profile, _ in results]
        if len(results) > 1
        else ["Findings"]
    )
    for tab, (profile, findings) in zip(tabs, results):
        with tab:
            if not findings:
                st.success("No configured scouting flags were triggered for this player.")
                continue
            for index, finding in enumerate(findings):
                with st.expander(f"{finding.severity} · {finding.metric} · {finding.finding_type}"):
                    st.write(finding.evidence)
                    st.caption(f"Rule: {finding.reason}")
                    current, benchmark, percentile = st.columns(3)
                    current.metric("Current", f"{finding.current_value:.2f}")
                    benchmark.metric("Peer median", f"{finding.peer_benchmark:.2f}")
                    percentile.metric("Peer percentile", f"{finding.percentile:.0f}th")
                    st.caption(
                        f"Performance confidence: {finding.confidence} · "
                        f"Sample: {finding.sample_size:.0f} minutes"
                    )
                    if ai_ready and st.button(
                        "Explain this flag in detail with AI",
                        key=f"{key_prefix}_explain_{profile['player_id']}_{index}",
                    ):
                        with st.spinner("AI is reviewing the evidence…"):
                            explanation = explain_finding_with_ai(
                                finding.to_dict(), profile["player_name"], profile["position"]
                            )
                        _render_ai_report(explanation)

    st.markdown("#### AI Profile & Chart Analyst")
    if not ai_ready:
        st.info(
            "AI assistance is not configured yet. Add your provider API key to "
            "the local .streamlit/secrets.toml file (or the matching environment variable) "
            "and restart the app. Rule-based findings remain available."
        )
        return

    st.caption(
        "AI receives the selected profile, peer-relative metrics, plotted chart values, "
        "and flags—not chart screenshots or the full player dataset."
    )
    profile_context = [_profile_summary(profile, peer_table) for profile in profiles]
    if st.button("Summarize profile and charts", key=f"{key_prefix}_summarize_profile"):
        with st.spinner("AI is summarizing the profile and charts…"):
            summary = summarize_with_ai(
                profile_context,
                chart_context or {},
                all_entries,
            )
        _render_ai_report(summary)

    player_context = " vs ".join(profile["player_name"] for profile in profiles)
    if all_entries and st.button("Explain all flags in detail", key=f"{key_prefix}_explain_all"):
        with st.spinner("AI is preparing a detailed scouting explanation…"):
            explanation = explain_all_flags_with_ai(all_entries, player_context)
        _render_ai_report(explanation)

    if comparison_mode:
        st.markdown("##### Decision-support question")
        question_label = "What decision are you weighing?"
        question_placeholder = (
            "Compare these players for a starting role. Prioritize the profile and charts, "
            "explain the trade-offs, and tell me what further evidence I need."
        )
        submit_label = "Ask AI to support this decision"
    else:
        question_label = "Ask about the profile, charts, or flags"
        question_placeholder = "Summarize the radar and explain the season trend."
        submit_label = "Ask AI"
    with st.form(f"{key_prefix}_ai_question_form"):
        question = st.text_input(
            question_label,
            placeholder=question_placeholder,
            key=f"{key_prefix}_ai_question",
        )
        submitted = st.form_submit_button(submit_label)
    if submitted:
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("AI is reviewing the findings…"):
                answer = ask_ai_question(
                    profile_context,
                    chart_context or {},
                    all_entries,
                    player_context,
                    profiles[0]["position"],
                    question.strip(),
                )
            _render_ai_report(answer)
