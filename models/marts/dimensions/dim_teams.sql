-- One row per team.

select
    team_id,
    max(team_name) as team_name
from {{ ref('stg_players') }}
group by team_id
