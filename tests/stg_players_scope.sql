select *
from {{ ref('stg_players') }}
where league_id not in (39, 61, 78, 135, 140)
   or season not between 2020 and 2026