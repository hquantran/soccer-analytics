-- Feature model computing per-90 player metrics from the staging player data.

select
    player_id,
    name,
    age,
    nationality,
    team_id,
    team_name,
    league_id,
    season,
    position,
    minutes,
    rating,
    round(goals * 90.0 / minutes, 3) as goals_per90,
    round(assists * 90.0 / minutes, 3) as assists_per90,
    round(passes_key * 90.0 / minutes, 3) as key_passes_per90,
    round(tackles_total * 90.0 / minutes, 3) as tackles_per90,
    round(dribbles_success * 90.0 / minutes, 3) as dribbles_per90,
    passes_accuracy_pct
from {{ ref('stg_players') }}
