-- Streamlit-ready wide table at player-season grain.
-- Rates use sum(numerator) / sum(denominator) so the same formulas stay correct
-- if this grain is later rolled up. At one row per season, sum() == the row value.
-- For multi-season Streamlit views, prefer aggregating additive columns in Python
-- the same way — never average these rate columns.

select
    f.player_season_id,
    f.player_id,
    p.name as player_name,
    p.nationality,
    p.photo,
    p.height_cm,
    p.weight_kg,
    p.age,
    f.team_id,
    t.team_name,
    f.league_id,
    l.league_name,
    f.season,
    f.position,
    f.injured,
    max(f.rating) as rating,
    sum(f.appearances) as appearances,
    sum(f.minutes) as minutes,

    -- ---------------------------------------------------------------------
    -- Additive volume inputs (sum these in Streamlit for multi-season views)
    -- Attackers: shots_total (primary), assists, fouls_drawn (secondary)
    -- Midfielders: passes_total (primary)
    -- Defenders: dribbles_attempts (secondary — attacking fullbacks)
    -- ---------------------------------------------------------------------
    sum(f.goals) as goals,
    sum(f.assists) as assists,
    sum(f.shots_total) as shots_total,
    sum(f.shots_on_target) as shots_on_target,
    sum(f.passes_total) as passes_total,
    sum(f.passes_completed) as passes_completed,
    sum(f.passes_key) as passes_key,
    sum(f.tackles_total) as tackles_total,
    sum(f.duels_total) as duels_total,
    sum(f.duels_won) as duels_won,
    sum(f.dribbles_attempts) as dribbles_attempts,
    sum(f.dribbles_success) as dribbles_success,
    sum(f.fouls_drawn) as fouls_drawn,
    sum(f.fouls_committed) as fouls_committed,
    sum(f.cards_yellow) as cards_yellow,
    sum(f.cards_red) as cards_red,

    -- ---------------------------------------------------------------------
    -- Per 90 metrics  (sum(stat) * 90 / sum(minutes))
    -- goals_per90:          Attackers (ST, Winger) — primary
    -- key_passes_per90:     Midfielders (CM, CAM, CDM) — primary
    -- tackles_per90:        Defenders (CB, LB, RB) — primary;
    --                       Midfielders (CDM) — secondary
    -- assists_per90 / dribbles_per90 / goal_involvements_per90: supporting
    -- ---------------------------------------------------------------------
    round(sum(f.goals) * 90.0 / nullif(sum(f.minutes), 0), 3) as goals_per90,
    round(sum(f.assists) * 90.0 / nullif(sum(f.minutes), 0), 3) as assists_per90,
    round(sum(f.goals + f.assists) * 90.0 / nullif(sum(f.minutes), 0), 3) as goal_involvements_per90,
    round(sum(f.passes_key) * 90.0 / nullif(sum(f.minutes), 0), 3) as key_passes_per90,
    round(sum(f.tackles_total) * 90.0 / nullif(sum(f.minutes), 0), 3) as tackles_per90,
    round(sum(f.dribbles_success) * 90.0 / nullif(sum(f.minutes), 0), 3) as dribbles_per90,

    -- ---------------------------------------------------------------------
    -- Division / efficiency metrics  (sum(num) / sum(den))
    -- shot_accuracy_pct:    Attackers — primary
    -- goal_conversion_pct:  Attackers — primary
    -- pass_accuracy_pct:    Midfielders — primary;
    --                       Defenders (ball-playing CBs) — secondary
    -- dribble_success_pct:  Attackers (wingers) — secondary;
    --                       Midfielders (press resistance) — secondary
    -- duel_success_pct:     Defenders — primary;
    --                       Midfielders — secondary
    -- fouls_per_tackle:     Defenders — primary (tackle efficiency / discipline;
    --                       lower = cleaner)
    -- ---------------------------------------------------------------------
    round(100.0 * sum(f.shots_on_target) / nullif(sum(f.shots_total), 0), 3) as shot_accuracy_pct,
    round(100.0 * sum(f.goals) / nullif(sum(f.shots_total), 0), 3) as goal_conversion_pct,
    round(100.0 * sum(f.passes_completed) / nullif(sum(f.passes_total), 0), 3) as pass_accuracy_pct,
    round(100.0 * sum(f.dribbles_success) / nullif(sum(f.dribbles_attempts), 0), 3) as dribble_success_pct,
    round(100.0 * sum(f.duels_won) / nullif(sum(f.duels_total), 0), 3) as duel_success_pct,
    round(sum(f.fouls_committed) * 1.0 / nullif(sum(f.tackles_total), 0), 3) as fouls_per_tackle
from {{ ref('fct_player_seasons') }} f
inner join {{ ref('dim_players') }} p using (player_id)
inner join {{ ref('dim_teams') }} t using (team_id)
inner join {{ ref('dim_leagues') }} l using (league_id)
where f.position != 'Goalkeeper'
group by
    f.player_season_id,
    f.player_id,
    p.name,
    p.nationality,
    p.photo,
    p.height_cm,
    p.weight_kg,
    p.age,
    f.team_id,
    t.team_name,
    f.league_id,
    l.league_name,
    f.season,
    f.position,
    f.injured
