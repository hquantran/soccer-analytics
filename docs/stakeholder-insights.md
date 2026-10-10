# Recruitment Analytics: From Squad Needs to Player Screening



**Analysis window:** 2020/21?2025/26; season-start year 2026 excluded. The local snapshot contains 12,723 player?team?league?season stints across five European leagues and 4,586 players.

[View the Power BI report PDF](../Soccer_analytics.pdf)

## Business Question

**Where might a squad benefit from additional recruitment, and which players warrant further evaluation?**

A recruitment team must first establish a need, then assess candidates against that need. Raw scoring totals favor players with more minutes, a standout season can conceal inconsistent output, and the same rate can mean different things across positions and competitions.

This project supports that initial investigation. Power BI provides team-level signals, league comparisons, and player-season screening. Streamlit provides deeper profiles, peer comparisons, similar-player search, and AI-assisted explanations. Together, they help an analyst assemble candidates and questions for further scouting; they do not determine who a club should sign.

This is a hypothetical recruitment case study, not evidence of a completed club engagement or measured recruitment impact.

## 1. Identify Potential Squad Needs

![Team Attack report: scoring concentration and attacking trends](images/powerbi/page-1.png)

*Saved report snapshot. Its selections differ from the independently calculated annual comparisons below.*

Scoring concentration provides a starting question: **how much does a team rely on its leading contributors, and what happens beyond them?** Goals, assists, and shots across seasons help an analyst investigate whether a change reflects attacking volume, finishing, or personnel.

Among clubs with at least 30 recorded goals in each of the six seasons, Crystal Palace's leading three scorers accounted for a **mean annual share of 64.6%**, exceeding 60% in five seasons. Tottenham's mean was 63.3%, and Aston Villa's was 61.6%.

Repeated concentration warrants investigation, but it does not establish a squad weakness. A team may successfully concentrate chances among specialist finishers. Before suggesting recruitment, review the most relevant season, contributions outside the leading trio, and the roles of existing alternatives. Availability and tactical evidence are needed to determine whether additional depth would address a real problem.

**Next step:** define a specific question, such as whether the squad has sufficient alternative scoring options, before screening additional attackers.

The report's top-three measure ranks contributors over the selected window. The annual figures above instead identify each season's leading three separately and average the six shares equally. These are different analyses; selecting several seasons in the chart does not reproduce the mean annual statistic.

## 2. Understand Squad Context

![Team Profiles report: minutes by age group and exploratory passing analysis](images/powerbi/page-2.png)

*The age visual has historical and current-age modes. Passing accuracy is not cleared for recruitment recommendations.*

Playing-time allocation helps frame the squad question. A high share of minutes for younger players may prompt discussion about experience and support; a low share may prompt questions about succession. Neither pattern is inherently preferable.

Using age on July 1 of each season-start year, PSG's under-25 share of recorded minutes increased from **36.3% in 2020/21 to 69.9% in 2025/26**, a rise of 33.6 percentage points. This establishes an endpoint change in participation. It does not prove a deliberate youth-development strategy, distinguish academy players from young signings, or show that the change was steady.

**Next step:** inspect the players driving the change and the intervening seasons, then consider their roles alongside the original squad question. Use explicit season selections for historical age analysis. With no season selected, current-age mode groups historical minutes by age today; it does not describe the current squad.

### Validation before recommendation

The passing-versus-chance-creation scatter could help explore team style, but its passing input requires validation. The current calculation estimates completed passes from a provider field treated as a percentage. It produces suspicious 2024/25 team values, including **44.1% for PSG and 12.2% for Manchester United**.

Confirm the source field's meaning and missing-data coverage before using this metric. Until then, defer passing-quality conclusions and exclude this scatter from stakeholder recommendations. Detecting an implausible result is a reason to investigate the calculation, not to explain it as football behavior.

## 3. Screen Players for Sustained Performance

![League and Player Trends report: player-season heatmap and league comparison](images/powerbi/page-3.png)

*The PDF shows an attacker selection. The interactive report changes the output metric by position; the PDF is a static snapshot.*

Once the squad question is defined, the player-season heatmap helps distinguish repeated output from isolated high rates. A minimum-minute requirement reduces the weight placed on a few productive appearances, although it cannot eliminate performance uncertainty.

For an illustrative attacker screen, qualify each player-season at **900 attacker minutes**, require at least four qualified seasons, and count seasons with at least **0.40 goals per 90**. The following players meet the scoring threshold in all six qualified seasons:

| Player | Qualified seasons | Seasons at ?0.40 goals/90 | Lowest qualified-season rate |
|---|---:|---:|---:|
| Kylian Mbapp? | 6 | 6 | 0.831 |
| Erling Haaland | 6 | 6 | 0.722 |
| Robert Lewandowski | 6 | 6 | 0.620 |
| Harry Kane | 6 | 6 | 0.473 |
| Serhou Guirassy | 6 | 6 | 0.510 |

These established forwards demonstrate the screening method; they are not a budget-qualified shortlist. The thresholds are analytical choices, not validated predictors of transfer success. A four-season requirement also excludes emerging players, who need a separate development-focused review.

**Next step:** apply role-appropriate criteria to the relevant candidate pool, retain minutes alongside rates, and inspect season-to-season changes. A blank qualified cell can indicate insufficient minutes or absent data; it must not be read as zero performance.

The heatmap supports this review, but the four-season qualification and strong-season counts above were calculated separately from the local data. They should not be described as an automated feature of the saved report.

## 4. Put Performance in Context

A candidate's rate needs a relevant comparison group. The report uses goals per 90 for attackers, key passes per 90 for midfielders, and tackles per 90 for defenders. These measure different contributions; they are not interchangeable overall-performance scores. Higher tackle volume, for example, may reflect greater defensive workload rather than better defending.

Among included attackers, Bundesliga had the highest aggregate scoring rate in **four of six seasons**. The leader changed from Serie A in 2020/21 (0.391 goals per 90 attacker-minutes) to Bundesliga in 2021/22?2024/25, then Ligue 1 in 2025/26 (0.355).

This variation supports using season-specific context. It does not establish league strength, ease of scoring, or a transfer adjustment factor. Coverage and the mix of included players also affect the comparison.

**Next step:** compare a candidate with same-position peers in the relevant season and league, then inspect supporting metrics. Keep a league benchmark independent of an individual player selection when the purpose is to compare that player with the wider population.

## 5. Investigate Shortlisted Players

Power BI identifies a statistical question; Streamlit helps investigate the player behind it. Player-season hyperlinks can carry the selected player, season, and league selections into the profile. The current local setup requires Streamlit to be running on the viewer's machine.

In Streamlit, an analyst can:

- Review position-specific output, season trends, peer percentiles, and supporting charts.
- Compare two players in the same resolved position under a consistent filter window.
- Find statistically similar players to expand the pool of alternatives. Similarity describes a statistical profile, not equal ability or tactical fit.
- Examine rule-based scouting signals and the evidence that triggered them.
- Request Gemini explanations grounded in supplied metrics, chart context, and scouting signals when configured. Explanations remain subject to analyst verification.

**Next step:** record why each candidate merits video or specialist review, which evidence supports that judgment, and what remains unknown. The application helps organize investigation; it does not supply contract, medical, affordability, or complete tactical assessments.

## Recommended Recruitment Workflow

1. **Define the question:** select a team and relevant season; investigate a scoring-depth or succession signal.
2. **Establish context:** review attacking trends and age-based participation before assuming recruitment is the answer.
3. **Set screening criteria:** choose the position, output metrics, minimum minutes, and appropriate history requirement.
4. **Benchmark fairly:** compare candidates within relevant season, league, and position groups.
5. **Investigate in Streamlit:** review profiles, peers, comparisons, statistical alternatives, and supporting explanations.
6. **Recommend further scouting:** document candidates, evidence, uncertainties, and the questions video, tactical, medical, and financial review must resolve.

## What the Analysis Can and Cannot Tell Us

The analysis can identify recurring statistical patterns, compare recorded output on consistent definitions, and provide evidence for prioritizing further review.

It cannot establish that a team needs a transfer, that a player will reproduce performance elsewhere, or that a statistically similar player is a suitable replacement. Scoring concentration, youth participation, and league averages are investigative signals rather than causal explanations. Goals are not adjusted for penalties or expected goals in this case study.

No recruitment outcome, adoption, time saving, or financial return has been measured. Any future evaluation should assess the quality and reproducibility of the shortlist and its usefulness to expert reviewers.

## Analytical Notes

- **Evidence source:** numerical findings were recalculated from the local DuckDB snapshot. The PDF and inspected PBIX visual structure establish presentation, not numerical parity with the embedded Power BI model. Match filters and refresh data before reproducing findings.
- **Coverage and grain:** one fact row represents a player?team?league?season stint. Staging excludes stints below 300 minutes. Recorded team goals therefore may differ from official totals; season labels alone do not establish completeness.
- **Screening threshold:** 900 minutes qualifies aggregated player-seasons at the selected position, not entire leagues. A visual-level league total filter does not implement player qualification. Streamlit similarity search has a separate default 500-minute candidate floor; align filters before comparing outputs.
- **Rate definitions:** per-90 rates use `90 ? sum(events) / sum(minutes)`. Percentage rates divide summed numerators by summed denominators. Do not average stored player rates. Multi-season rates are weighted by their denominators.
- **Age:** historical findings use birth dates and a July 1 reference date, not the fact model's January 1 season key. Missing birth dates remain in total minutes but do not enter the under-25 numerator.
- **Consumers:** Power BI imports dimensional facts and dimensions; Streamlit reads the scouting mart, which excludes goalkeepers. Shared metric definitions support consistent formulas. Optional MetricFlow work is not required by either application.
- **Scope:** the briefing covers season-start years 2020?2025. It does not claim that every season or player has complete provider coverage. Passing accuracy remains withheld pending validation.

## Intended Outcome

An **evidence-backed shortlist and a clear set of questions for further scouting**, tied to an explicitly investigated squad need. The value is a traceable path from team-level signal to candidate review, with human judgment at each decision.

