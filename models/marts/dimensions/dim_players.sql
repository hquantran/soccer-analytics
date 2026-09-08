-- One row per player (attributes from the most recent season stint).

select
    player_id,
    name,
    nationality,
    photo,
    height_cm,
    weight_kg,
    age
from {{ ref('stg_players') }}
qualify row_number() over (
    partition by player_id
    order by season desc, team_id, league_id
) = 1
