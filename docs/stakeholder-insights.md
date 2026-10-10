# From Scoring Gaps to a Focused Scouting Shortlist

## A recruitment screening case study across six seasons

Prepared October 9, 2026. Scope: **season-start years 2020–2025 (2020/21–2025/26)**. **2026 is excluded from every calculation.**

This analysis looks beyond single-season rankings to identify recurring scoring concentration, sustained individual output, and changes in youth participation across five European leagues. Power BI provides the overview; linked Streamlit profiles support further scouting.

## Business problem

A hypothetical football club is preparing its next recruitment review. The sporting director needs to decide which roles deserve more scouting and which players warrant detailed evaluation. Raw goal totals favor players with more minutes, one strong season can dominate attention, and reviewing profiles individually makes broad comparisons difficult.

**The decision: Where should the club focus its scouting effort to broaden scoring contributions and identify players with sustained, role-relevant output?**

This is a portfolio case study, not a commissioned engagement. No actual club adoption, recruitment savings, or transfer outcomes are claimed.

## How the solution supports that decision

| Decision stage | What the project provides | Practical output |
|---|---|---|
| Diagnose the need | Team scoring concentration and output trends | A scoring-depth question or role to investigate |
| Establish context | Position-specific league rates and historical age participation | A relevant comparison group |
| Screen candidates | Player-season heatmap with a 900-minute qualification | Players with repeated output and sufficient exposure |
| Investigate alternatives | Linked Streamlit profiles, peer comparisons, and similarity search | A narrower list for video and domain review |
| Explain the evidence | Calculated findings with optional AI-assisted explanations | A reviewable scouting brief |

**Intended value:** Make screening more consistent and shorten the path from an aggregate finding to player-level evidence. Affordability and tactical suitability remain outside the model: fees, wages, contracts, match context, and several advanced performance measures are unavailable.

## Executive takeaways and recommended actions

| Finding | Why it matters | Recommended next step |
|---|---|---|
| Crystal Palace's annual top-three share exceeds 60% in five seasons | Scoring concentration recurs rather than appearing in just one season | Examine contributors outside the leading trio before deciding whether broader attacking support is needed |
| Several forwards sustain the scoring criterion across six qualified seasons | Repeated substantial-minute output is more informative than one high-rate cell | Apply the same screen to the wider pool, then review candidates in Streamlit and video |
| Bundesliga leads attacker scoring rates in four seasons, but the leader changes | Raw rates sit within different league and season contexts | Show a candidate's league benchmark and previous seasons alongside their latest rate |
| PSG's under-25 minutes share rises by 33.6 percentage points between endpoints | Playing-time participation changes substantially | Inspect the players and intervening seasons before inferring a recruitment or development strategy |
| Estimated passing accuracy produces questionable values | An uncertain metric could misdirect a recommendation | Validate the raw field before making passing-quality claims |

These findings prioritize investigation. They do not demonstrate causal dependence on scorers, league strength, academy success, or future player performance. Established stars below illustrate the screening method; they are not presumed affordable recruitment targets.

Figures were calculated from the local DuckDB fact and dimension tables, not extracted from the PBIX cache. Refresh the report and match the filters before presenting them. Season labels and similar sample sizes do not guarantee complete source coverage.

The saved PBIX contains three pages: **Team Attack**, **Team Profiles**, and **League & Player Trends**. Goals/assists and shots are now separate visuals. The player matrix and league chart use a position-dependent metric. The age chart uses the dynamic `Minutes by Display Age` measure: its interpretation depends on whether a season filter is active.

The analysis window contains **12,723 player stints and 4,586 distinct players**. Stints are player/team/league/season combinations, not necessarily one row per player-season.

## What the current multi-season scoring chart actually shows

**Stakeholder message:** “Some clubs' recorded scoring across the selected window is concentrated in the same three players. This measures continuity of scoring contributions, rather than each season's reliance on its leading trio.”

| Team | Recorded goals, 2020–2025 window | Goals from the window's top three players | Share |
|---|---:|---:|---:|
| Nottingham Forest | 176 | 91 | 51.7% |
| Leicester | 198 | 100 | 50.5% |
| Tottenham | 347 | 171 | 49.3% |
| West Ham | 282 | 134 | 47.5% |
| Osasuna | 245 | 115 | 46.9% |

These are the five highest shares among teams with at least 150 recorded goals in the selected window. All positions are included. This ranking does not require six seasons of coverage for every club; promotion, relegation, and missing coverage can change each club's exposure. Apply an explicit 2020–2025 filter to reproduce it in Power BI.

**Implication:** Review whether leading scorers represent persistent contributors or a short period of concentrated output. For year-by-year depth, use the annual calculation below instead. Neither calculation establishes a causal dependency on those players.

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

## Match each claim to its visual

| Report visual | Safe interpretation | Required selection or qualification |
|---|---|---|
| Top-three goal-share chart | Share contributed by three players within the selected window | Explicit season range; annual averages need a separate calculation |
| Goals/assists and shots trends | Recorded output changes, not automatically changes in efficiency | Same team and coverage window; conversion is needed to assess efficiency |
| Dynamic age chart | Historical age groups when seasons are filtered; current-age groups otherwise | Select seasons for historical youth-participation findings |
| Passing/creation scatter | Exploratory comparison of estimated accuracy and key-pass rate | Validate passing field before interpreting accuracy |
| Player-season matrix | Position-specific output over time | ≥900 minutes per player-season; goals, key passes, or tackles are different constructs |
| League rate chart | Position-specific weighted rate among included stints | One position; player slicer must not narrow the benchmark |

The midfielder and defender views describe creation and tackling activity, respectively. They should not be labelled overall performance or defensive quality without additional evidence. Blank qualified cells represent unavailable or insufficient-minute observations, not zero performance.

## Suggested presentation script

“We examined six season labels across five European leagues, excluding 2026. Crystal Palace shows recurring scoring concentration, several attackers sustain our scoring threshold across six qualified seasons, and youth participation changes substantially at some clubs. League scoring-rate rankings also vary over time, reinforcing the importance of context in recruitment. These findings prioritize further scouting rather than establish tactical causes.”

## Coverage and checks

### Intended business impact and how to test it

The business outcome has not yet been measured. Evaluate the workflow by asking analysts to complete the same screening task with their existing process and this project, comparing:

- Time to produce a shortlist with documented evidence.
- Proportion of candidates meeting the requested position, season, and minutes criteria.
- Recommendations accepted for further review by a football domain expert.
- Reproducibility of findings from the documented filters.

These are proposed success measures, not achieved results. The current demonstrated scope is a connected analysis workflow covering **12,723 recorded stints and 4,586 players**, with explicit metric definitions and qualification rules.

### Data coverage

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
