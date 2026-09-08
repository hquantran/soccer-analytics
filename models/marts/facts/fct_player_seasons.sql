-- Additive player-season facts. Use these columns for correct multi-season
-- rollups in Streamlit: sum(numerator) / sum(denominator).

select
    player_season_id,
    player_id,
    team_id,
    league_id,
    season,
    position,
    injured,
    rating,
    appearances,
    minutes,
    coalesce(goals, 0) as goals,
    coalesce(assists, 0) as assists,
    coalesce(shots_total, 0) as shots_total,
    coalesce(shots_on_target, 0) as shots_on_target,
    coalesce(passes_total, 0) as passes_total,
    round(coalesce(passes_total, 0) * passes_accuracy_pct / 100.0) as passes_completed,
    coalesce(passes_key, 0) as passes_key,
    coalesce(tackles_total, 0) as tackles_total,
    coalesce(duels_total, 0) as duels_total,
    coalesce(duels_won, 0) as duels_won,
    coalesce(dribbles_attempts, 0) as dribbles_attempts,
    coalesce(dribbles_success, 0) as dribbles_success,
    coalesce(fouls_drawn, 0) as fouls_drawn,
    coalesce(fouls_committed, 0) as fouls_committed,
    coalesce(cards_yellow, 0) as cards_yellow,
    coalesce(cards_red, 0) as cards_red
from {{ ref('stg_players') }}
