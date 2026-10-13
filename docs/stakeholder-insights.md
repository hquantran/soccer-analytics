# Recruitment Analytics: From Squad Questions to Player Review

**Business question: Where might a squad benefit from additional recruitment, and which players deserve a closer look?**

This case study uses six seasons of recorded player statistics, from 2020/21 to 2025/26, across five European leagues. The dataset contains 12,723 records covering 4,586 players. Each record represents a player at a team in a league and season. The 2026/27 season is excluded.

[View the full Power BI report](../Soccer_analytics.pdf)

## The recruitment problem

A high goal total does not explain whether a team has enough scoring options. A high scoring rate does not show whether a player can maintain it over several seasons. Recruitment analysis needs both the squad question and the evidence behind each candidate.

Power BI helps an analyst review teams, compare leagues, and identify players to investigate. Streamlit then provides detailed profiles, player comparisons, similar-player search, and AI-assisted explanations.

The project addresses a practical screening problem: deciding where to focus scouting effort without relying on raw totals or one impressive rate. It connects team-level questions with player evidence and detailed follow-up.

This is a portfolio case study. Its output is a shortlist for further review; no transfer outcome, time saving, or financial return has been measured.

## Main findings and decisions

| Finding | Decision it supports |
|---|---|
| Crystal Palace's top three scorers accounted for an average 64.6% of recorded goals each season in a separate annual analysis | Investigate scoring options outside the leading trio before deciding whether more attacking depth is needed |
| Bale leads the displayed scoring-rate ranking, but his evidence covers one season; Haaland and Mbappe have six seasons represented | Consider both scoring rate and the amount of playing-time evidence when prioritizing players |
| Bundesliga has the highest overall attacker scoring rate in the included sample | Compare candidates with relevant league and season peers rather than treating all raw rates as equivalent |

These findings support further investigation, not a transfer decision. The players in the ranking are examples of the screening method, not a shortlist matched to a particular club's budget or tactical needs.

## 1. Start with a squad question

![Team Attack: attacking trends and top-three scorers' share](images/powerbi/page-1.png)

*Report snapshot. Read team trends within the selected team and season range.*

The Team Attack page asks two useful questions: **how has attacking output changed, and how concentrated is scoring among a few players?** Goals and assists show recorded contributions. The separate shots chart helps investigate whether changes in goals came with changes in shooting volume.

Across the full six-season window, the three leading scorers contributed:

| Team | Top-three goals / recorded team goals | Share |
|---|---:|---:|
| Nottingham Forest | 91 / 176 | 51.7% |
| Leicester | 100 / 198 | 50.5% |
| Tottenham | 171 / 347 | 49.3% |

These figures describe the same three players across the whole window, not a new top three chosen each season. Teams also have different numbers of seasons represented, so the ranking alone is not a fair measure of squad weakness.

A separate annual check adds useful context: among teams with at least 30 recorded goals in each of the six seasons, Crystal Palace's top-three share averaged **64.6%**, exceeding 60% in five seasons. This annual average is an additional calculation, not the value shown by the multi-season chart.

**What this means:** repeated reliance on a few scorers gives the analyst a question about alternative scoring options. It can also reflect successful specialist finishers. It does not prove that another attacker is needed.

**Next action:** review a relevant single season, contributions outside the leading trio, and the available alternatives. Use video and role assessment to decide whether recruitment would address a real gap.

## 2. Understand who receives playing time

![Team Profiles: age-group minutes and passing-versus-creation scatter](images/powerbi/page-2.png)

The age chart shows the share of recorded minutes given to each age group. It can support questions about succession, experience, and opportunities for younger players. A younger or older squad is not automatically better.

As an additional historical check, PSG's under-25 minutes share increased from **36.3% in 2020/21 to 69.9% in 2025/26**, a change of 33.6 percentage points. This calculation uses each player's age on July 1 of the season-start year. It shows increased playing time for younger players. It does not explain whether they came through the academy or were recruited.

**Next action:** examine the players behind the change and the intervening seasons. Establish which roles might need support or succession planning before looking for candidates.

**Reading note:** the historical figures above use age at the start of each season. Grouping past minutes by current age answers a different question and should not be used to describe the current squad.

### A metric that needs further checking

The passing-accuracy input requires source validation. The scatter is excluded from the findings and should not support recruitment recommendations until the underlying data has been checked.

## 3. Separate high rates from sustained output

![League and Player Trends: player-season heatmap sorted by weighted rate](images/powerbi/page-3.png)

The updated heatmap ranks attackers by their **weighted goals per 90 across the selected seasons**. Each season column shows that season's rate. The Total column recalculates the rate from total goals and total minutes; it does not add the season rates or take their simple average.

The current ranking shows why playing time matters:

| Player | Recorded goals | Recorded minutes | Overall goals per 90 | Seasons represented |
|---|---:|---:|---:|---:|
| Gareth Bale | 11 | 921 | 1.075 | 1 |
| Jhon Duran | 12 | 1,131 | 0.955 | 2 |
| Erling Haaland | 161 | 15,356 | 0.944 | 6 |
| Kylian Mbappe | 167 | 15,923 | 0.944 | 6 |

Bale has a higher recorded rate, but Haaland and Mbappe have much more playing time across seasons. A short productive spell and sustained output deserve different levels of follow-up. Neither rate alone establishes the best candidate.

The updated report applies a **900-minute minimum to each player's total across the selected seasons**. Igamane's 428-minute record is therefore excluded. This improves the initial screen, but it is not a 900-minute minimum for every season.

For example, Duran has 1,131 recorded minutes overall, made up of 505 in 2023/24 and 626 in 2024/25. He passes the current total-minutes filter even though neither season reaches 900 minutes. His high rate warrants review, but the evidence is more limited than the six-season records.

**Next action:** use the current ranking to find players to investigate, then check their minutes in each season. If the question is sustained performance, apply the 900-minute requirement separately to each player-season and review how often the player meets the output criteria. Keep a separate route for emerging players with shorter histories. Blank cells do not mean zero goals.

A separate calculation illustrates this approach: Mbappe, Haaland, Lewandowski, Kane, and Guirassy each recorded at least 900 attacker minutes and at least 0.40 goals per 90 in all six seasons. These are examples of sustained output, not an affordable shortlist. The thresholds are screening choices, not proven predictors of future success.

## 4. Compare players in the right context

The league chart provides a reference for the selected position. Its saved 900-minute filter checks each league's combined minutes; it does not remove individual players with fewer than 900 minutes. Across the six-season attacker sample, the ranking is:

| League | Goals per 90 attacker-minutes |
|---|---:|
| Bundesliga | 0.372 |
| Ligue 1 | 0.341 |
| Premier League | 0.323 |
| Serie A | 0.321 |
| La Liga | 0.316 |

These are total attacker goals divided by total attacker minutes, multiplied by 90. They are not team goals per match or an average of individual player rates.

**What this means:** scoring rates differ across the included samples. This does not prove that one league is stronger or easier. The players covered, seasons selected, and playing-time distribution affect the result.

**Next action:** compare candidates with peers in the same position, season, and league. Use the wider league as the reference when assessing an individual candidate.

The interactive report uses goals per 90 for attackers, key passes per 90 for midfielders, and tackles per 90 for defenders. These describe different contributions, not a shared overall-quality score. More tackles can reflect more defensive work rather than better defending.

## 5. Move from screening to deeper investigation

Player-season links connect the report to Streamlit profiles for deeper review.

An analyst can then review season trends and position-specific metrics, compare the player with peers, compare two players directly, and find statistically similar alternatives. Similarity means similar recorded statistics; it does not establish equal ability or tactical fit.

Scouting signals highlight statistical patterns and their supporting evidence. AI-assisted explanations help describe those patterns in plain language and require analyst review.

## How this supports a recruitment review

Suppose a club wants to understand whether it needs another scoring option. Start by reviewing a relevant season's scoring concentration and the contribution of players outside the leading trio. Check squad age and existing alternatives before assuming a signing is the answer.

If additional scouting is justified, use the player matrix to identify productive attackers. Compare their rates with minutes and season history, then use league context and Streamlit profiles to assess supporting evidence. The review should end with candidates for video and role assessment, plus clear reasons for including them. This workflow does not claim that the example players are suitable replacements for any team in the report.

## Recommended next steps

1. **Define the squad question:** identify a scoring-depth or succession issue worth investigating.
2. **Check the context:** review the relevant team, season, age groups, and data coverage.
3. **Set player criteria:** choose the position and apply a meaningful player-season minutes threshold.
4. **Review repeated output:** distinguish a short productive spell from several strong seasons.
5. **Investigate candidates in Streamlit:** examine supporting metrics, peers, and alternatives.
6. **Recommend further scouting:** document candidates, reasons, and the questions specialist review must answer.

## Scope and limitations

- Findings use the recorded data for 2020/21 through 2025/26. Coverage varies by player and team; season labels do not guarantee complete records.
- The source excludes player stints below 300 minutes. Recorded team totals can therefore differ from official totals.
- Overall per-90 rates account for playing time. They do not measure consistency by themselves. The current matrix requires 900 total player minutes across the selected seasons, not 900 minutes in each season.
- Historical age findings use birth dates and July 1 of each season-start year. Missing birth dates are not included in the under-25 share but remain in total minutes.
- Annual scoring concentration and the sustained-output examples were calculated separately from the report's displayed multi-season rankings.
- The analysis does not establish affordability, tactical fit, medical status, or future performance. Scoring is not adjusted for penalties or expected goals.

## Intended outcome

A clear squad question, a set of candidates supported by evidence, and a plan for further scouting. The report helps decide **where to investigate next**, rather than making an automatic transfer recommendation.
