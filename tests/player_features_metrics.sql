select *
from {{ ref('player_features') }}
where minutes < 300
   or goals_per90 < 0
   or assists_per90 < 0
   or key_passes_per90 < 0
   or tackles_per90 < 0
   or dribbles_per90 < 0