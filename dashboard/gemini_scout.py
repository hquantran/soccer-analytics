"""Gemini explanations for deterministic scouting findings."""

from __future__ import annotations

import json
import os
from typing import Any

import streamlit as st
from google import genai
from google.genai import types


def _gemini_settings() -> tuple[str | None, str]:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL")
    try:
        api_key = api_key or st.secrets.get("GEMINI_API_KEY")
        model = model or st.secrets.get("GEMINI_MODEL")
    except (AttributeError, FileNotFoundError):
        pass
    return api_key or None, model or "gemini-2.5-flash"


def init_gemini() -> bool:
    """Return whether an API key is configured without exposing its value."""
    api_key, _ = _gemini_settings()
    return bool(api_key)


def _generate(prompt: str) -> dict[str, Any]:
    api_key, model_name = _gemini_settings()
    if not api_key:
        return {"executive_summary": "Gemini API key is not configured. Rule-based evidence is shown above."}
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        text = response.text or ""
        try:
            report = json.loads(text)
            if isinstance(report, dict):
                return report
        except json.JSONDecodeError:
            pass
        return {"executive_summary": text or "Gemini returned an empty explanation."}
    except Exception as exc:  # SDK/network errors should not interrupt the dashboard.
        return {
            "executive_summary": (
                f"Gemini explanation unavailable ({type(exc).__name__}). "
                "Refer to the rule-based evidence above."
            )
        }


_REPORT_FORMAT = """
Return a valid JSON object only, with these keys:
{
  "executive_summary": "2-4 plain-language sentences",
  "key_takeaways": ["concise stakeholder takeaway"],
  "player_assessments": [
    {"player": "name", "strengths": ["evidence-led strength"],
     "tradeoffs": ["uncertainty or development area"]}
  ],
  "metric_interpretations": [
    {"metric": "metric label", "interpretation": "what the supplied values mean"}
  ],
  "chart_reading": [
    {"chart": "chart name", "interpretation": "what supplied plotted values show"}
  ],
  "decision_considerations": ["factor to consider; do not overstate evidence"],
  "limitations": ["important data limitation"],
  "recommended_next_steps": ["practical next check"],
  "recommendation": "cautious evidence-based guidance; state if evidence is insufficient"
}
Use empty arrays when a section has no relevant evidence. Do not use Markdown fences.
"""


@st.cache_data(ttl=3600, show_spinner=False)
def explain_finding_with_gemini(finding_dict: dict[str, Any], player_name: str, position: str) -> dict[str, Any]:
    """Give a detailed interpretation of every field in one finding."""
    prompt = f"""
You are an objective football scouting analyst. Explain the finding thoroughly,
not just why the rule fired. Use only the supplied facts and do not recalculate
or add statistics that are absent from the data.
Player: {player_name} ({position})
Structured finding:
{json.dumps(finding_dict, indent=2, default=str)}

Use these labeled sections:
1. Plain-language takeaway.
2. Why it was flagged: describe the rule and supplied trigger reason.
3. What each number means: current value, peer median, percentile, minutes,
   severity, and confidence; compare them without inventing a formula.
4. What the evidence supports versus what it cannot establish, especially any
   small-sample uncertainty. Severity is the rule's alert level, not a medical
   or disciplinary risk. Confidence describes confidence in the performance
   interpretation, not whether the deterministic rule executed correctly.
5. Practical next checks for a scout (data/video/context) and key limitations.
Be specific, clear, and appropriately cautious. Do not use outside player
knowledge, assert causation, or infer missing metrics such as xG.
"""
    prompt += _REPORT_FORMAT
    return _generate(prompt)


@st.cache_data(ttl=3600, show_spinner=False)
def explain_all_findings_with_gemini(findings: list[dict[str, Any]], context: str) -> dict[str, Any]:
    """Explain the complete set of displayed findings, including their interaction."""
    prompt = f"""
You are an objective football scouting analyst. Explain the complete scouting
summary for this context: {context}

Structured findings:
{json.dumps(findings, indent=2, default=str)}

Write a useful report with these sections:
1. Overall assessment: summarize the combined picture without making a signing
   recommendation unsupported by the data.
2. Finding-by-finding explanation: why each rule fired; what its current value,
   peer median, percentile, severity, confidence, and minutes indicate.
3. How the findings fit together: distinguish reinforcing signals from tensions;
   if there is only one finding or no meaningful interaction, say so.
4. Uncertainty and limitations: explain sample-size caveats and what the fields
   cannot tell us. Do not treat severity as injury/disciplinary risk or confidence
   as certainty that a player will repeat the performance.
5. Next scouting steps: specific data or video evidence to collect.

Use only the structured findings above. Do not invent calculations, statistics,
causes, player history, or missing metrics. If information is absent, say so.
"""
    prompt += _REPORT_FORMAT
    return _generate(prompt)


@st.cache_data(ttl=3600, show_spinner=False)
def summarize_profile_and_charts_with_gemini(
    profiles: list[dict[str, Any]], chart_context: dict[str, Any], findings: list[dict[str, Any]]
) -> dict[str, Any]:
    """Summarize profile metrics and the underlying values shown in charts."""
    prompt = f"""
You are an objective football scouting analyst. The following context contains
selected player profiles, peer-relative metric summaries, plotted chart data,
and any deterministic scouting flags.

Profiles and metrics:
{json.dumps(profiles, indent=2, default=str)}

Chart data:
{json.dumps(chart_context, indent=2, default=str)}

Rule-based flags:
{json.dumps(findings, indent=2, default=str)}

Write a clear, detailed report with these sections:
1. Executive summary of each player and the most notable evidence.
2. Profile metrics: explain the raw values, peer medians and peer percentiles;
   preserve the higher-is-better direction supplied for each metric.
3. Chart reading: explain season trajectory (minutes bars and the position's
   primary rate line), radar axes (0-100 peer percentiles), and scatter axes,
   selected-player values, peer distributions, and ideal quadrant when supplied.
   For comparisons, contrast the players only on metrics present in the data.
4. Scouting flags: explain their rule triggers and how they relate to the profile
   and charts; clearly distinguish strong rates from small samples.
5. What the evidence cannot show and useful follow-up checks.

The chart input is structured plotted values, not an image. Do not claim to see
visual details that are not represented in the data. Use only supplied facts;
do not invent stats, causal explanations, player history, or missing metrics.
Flag severity is an alert level, not medical/disciplinary risk. Confidence is
about the performance interpretation, not the correctness of rule execution.
"""
    prompt += _REPORT_FORMAT
    return _generate(prompt)


@st.cache_data(ttl=3600, show_spinner=False)
def ask_custom_scout_question(
    profile_context: list[dict[str, Any]],
    chart_context: dict[str, Any],
    finding_dicts: list[dict[str, Any]],
    player_name: str,
    position: str,
    user_question: str,
) -> dict[str, Any]:
    """Answer a profile or player comparison question as a structured report."""
    prompt = f"""
You are an objective football scouting analyst.
Player or comparison: {player_name} ({position})
Profile metrics:
{json.dumps(profile_context, indent=2, default=str)}
Chart data:
{json.dumps(chart_context, indent=2, default=str)}
Findings:
{json.dumps(finding_dicts, indent=2, default=str)}
Question: {user_question}

Interpret the chart data and profile metrics when relevant. Keep each player's
metrics and findings associated with that player. Answer using only the supplied
context; state when evidence is insufficient. Do not invent statistics, image
details, or outside facts.
If the question asks which player to choose, assess each option against the
supplied criteria; if criteria are absent, state the trade-offs and ask what
matters most rather than declaring a universal winner. Make any conclusion
conditional on role, minutes/sample, and missing context.
"""
    prompt += _REPORT_FORMAT
    return _generate(prompt)
