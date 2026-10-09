# Six Seasons of European Football

## Scoring dependence, sustained player output, and youth participation

Prepared October 9, 2026. Scope: **season-start years 2020–2025 (2020/21–2025/26)**. **2026 is excluded from every calculation.**

This analysis looks beyond single-season rankings to identify recurring scoring concentration, sustained individual output, and changes in youth participation across five European leagues. Power BI provides the overview; linked Streamlit profiles support further scouting.

Figures were calculated from the local DuckDB fact and dimension tables, not extracted from the PBIX cache. Refresh the report and match the filters before presenting them. Season labels and similar sample sizes do not guarantee complete source coverage.

## 1. Scoring concentration is a recurring pattern

**Stakeholder message:** Crystal Palace's leading three scorers account for an average of 64.6% of recorded goals across six seasons. Their share exceeds 60% in five seasons, making scoring depth a useful follow-up question.

| Team | Seasons evaluated | Mean annual top-three share | Seasons with share ≥60% |
|---|---:|---:|---:|
| Crystal Palace | 6 | 64.6% | 5 |
| Tottenham | 6 | 63.3% | 3 |
| Aston Villa | 6 | 61.6% | 3 |
| Lyon | 6 | 61.2% | 4 |
| Osasuna | 6 | 61.0% | 3 |

These are the five highest mean shares among clubs with at least 30 recorded goals in each of the six seasons. All positions are included. Top scorers are selected separately for each team-season; player ID breaks ties. Each season receives equal weight in the average.

**Implication:** Examine alternative scoring contributors and cover for leading scorers. Concentration can also reflect effective specialists; it is not automatically a weakness or evidence of injury risk.

**Report caution:** Selecting all six seasons in the existing Top 3 Goal Share measure identifies three players across the whole window. It does not produce this mean annual share. Reproduce this table by calculating each season's share first, then averaging the six results.

## 2. League context matters, and rankings change

**Stakeholder message:** Bundesliga attackers lead the included sample in four of six seasons, but Ligue 1 leads in 2025/26. A single aggregate ranking hides that variation.

| Season | Bundesliga | Premier League | Ligue 1 | La Liga | Serie A |
|---|---:|---:|---:|---:|---:|
| 2020/21 | 0.371 | 0.310 | 0.333 | 0.318 | **0.391** |
| 2021/22 | **0.378** | 0.303 | 0.349 | 0.306 | 0.358 |
| 2022/23 | **0.366** | 0.327 | 0.358 | 0.308 | 0.314 |
| 2023/24 | **0.396** | 0.358 | 0.317 | 0.329 | 0.307 |
| 2024/25 | **0.395** | 0.339 | 0.330 | 0.300 | 0.292 |
| 2025/26 | 0.329 | 0.293 | **0.355** | 0.339 | 0.273 |

Values: goals per 90 attacker-minutes, calculated as `90 × sum(goals) / sum(minutes)`. Position is Attacker; no additional 900-minute filter applies. Bold indicates the season's highest rate.

**Implication:** Benchmark recruits against same-position league peers. These numbers do not rank league strength or represent goals per match. Validate coverage before attributing changes to football conditions.

## 3. Sustained output distinguishes players from isolated peaks

**Stakeholder message:** Haaland, Mbappé, Lewandowski, Kane, and Guirassy each meet our chosen scoring threshold in all six qualified seasons in this snapshot.

| Player | Qualified seasons | Seasons ≥0.40 goals/90 | Lowest qualified-season rate | Weighted rate across qualified seasons |
|---|---:|---:|---:|---:|
| Erling Haaland | 6 | 6 | 0.722 | 0.944 |
| Kylian Mbappé | 6 | 6 | 0.831 | 0.944 |
| Robert Lewandowski | 6 | 6 | 0.620 | 0.927 |
| Harry Kane | 6 | 6 | 0.473 | 0.872 |
| Serhou Guirassy | 6 | 6 | 0.510 | 0.727 |

Qualification: at least 900 attacker minutes per player-season, summed across included stints. Candidates need at least four qualified seasons; ranking uses strong-season count, then the unrounded weighted rate. The five shown all qualify in six seasons. The 0.40 threshold is an analytical choice.

**Implication:** Prioritize repeated substantial-minute output for further scouting. Penalties, expected goals, and tactical roles are not controlled here; this is sustained scoring rather than proof of overall quality or future performance.

**Small-sample example:** Lookman records 0.675, 0.521, and 0.597 goals/90 in 2022/23–2024/25 with at least 900 minutes each. His 2025/26 record is 0.579 over 622 minutes, so that cell must be excluded from the qualified heatmap.

## 4. Youth participation changed substantially

**Stakeholder message:** Several clubs show large increases in the share of recorded minutes assigned to players under 25 between the first and last seasons of the window.

| Team | Under-25 share, 2020/21 | Under-25 share, 2025/26 | Change (percentage points) |
|---|---:|---:|---:|
| Strasbourg | 29.7% | 95.1% | +65.4 |
| Parma | 22.2% | 67.2% | +45.0 |
| Paris Saint Germain | 36.3% | 69.9% | +33.6 |
| Genoa | 15.2% | 47.9% | +32.7 |
| Lazio | 6.9% | 34.5% | +27.6 |

These are the five largest endpoint increases among teams represented in both endpoint seasons. They do not imply a steady annual increase or continuous participation in the covered leagues.

Age is measured on July 1 of each season-start year. All positions are included. Missing birth dates remain in total minutes but are not counted as under 25. Changes are calculated before rounding.

**Implication:** Investigate changing recruitment and development profiles. Youth minutes do not prove academy production: young signings and academy graduates cannot be distinguished here.

**Validate before highlighting:** Strasbourg's 95.1% is extreme; check included players, birth dates, and coverage. Select explicit seasons in the dynamic-age chart: grouping historical minutes by age today cannot reproduce this analysis.

## 5. Passing accuracy needs validation before stakeholder conclusions

The model estimates completed passes as `round(passes_total × passes_accuracy_pct / 100)`, assuming the provider field is a percentage. The resulting 2024/25 estimates include 44.1% for Paris Saint Germain and 12.2% for Manchester United. These warrant investigation.

Verify raw field meaning, missingness, and numerator/denominator coverage against source records. Do not use the scatter's accuracy axis to claim passing quality until validated.

## Suggested presentation script

“We examined six season labels across five European leagues, excluding 2026. Crystal Palace shows recurring scoring concentration, several attackers sustain our scoring threshold across six qualified seasons, and youth participation changes substantially at some clubs. League scoring-rate rankings also vary over time, reinforcing the importance of context in recruitment. These findings prioritize further scouting rather than establish tactical causes.”

## Coverage and checks

| Season | Included stints | Distinct players |
|---|---:|---:|
| 2020/21 | 2,096 | 2,082 |
| 2021/22 | 2,141 | 2,119 |
| 2022/23 | 2,191 | 2,061 |
| 2023/24 | 2,076 | 2,027 |
| 2024/25 | 2,116 | 2,022 |
| 2025/26 | 2,103 | 2,069 |

The source excludes stints below 300 minutes. Recorded team totals may differ from official totals. Similar row counts do not prove completeness, including for 2025/26.

Before sharing: refresh Power BI, match the documented filters, enforce the heatmap's 900-minute qualification, prevent player selections from narrowing league comparisons, retain Unknown age groups, and show selected seasons and positions alongside visuals.
