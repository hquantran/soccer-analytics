-- Staging model for raw player statistics loaded by dlt.

with player as (
    select
        _dlt_id as player_row_id,
        player__id as player_id,
        player__name as name,
        player__age as age,
        player__nationality as nationality,
        regexp_replace(player__height, '[^0-9]', '', 'g')::int as height_cm,
        regexp_replace(player__weight, '[^0-9]', '', 'g')::int as weight_kg,
        player__injured as injured
    from {{ source('raw', 'players_raw') }}
),

stats as (
    select
        _dlt_parent_id as player_row_id,
        team__id as team_id,
        team__name as team_name,
        league__id as league_id,
        league__season as season,
        case
            when games__position = 'Forward' then 'Attacker'
            else games__position
        end as position,
        games__appearences as appearances,
        games__minutes as minutes,
        cast(games__rating as double) as rating,
        goals__total as goals,
        goals__assists as assists,
        shots__total as shots_total,
        shots__on as shots_on_target,
        passes__total as passes_total,
        passes__key as passes_key,
        cast(passes__accuracy as double) as passes_accuracy_pct,
        tackles__total as tackles_total,
        duels__total as duels_total,
        duels__won as duels_won,
        dribbles__attempts as dribbles_attempts,
        dribbles__success as dribbles_success,
        fouls__drawn as fouls_drawn,
        fouls__committed as fouls_committed,
        cards__yellow as cards_yellow,
        cards__red as cards_red
    from {{ source('raw', 'players_raw__statistics') }}
    where games__minutes >= 300
)

select
    {{ dbt_utils.generate_surrogate_key(['player_id', 'team_id', 'league_id', 'season']) }} as player_season_id,
    p.player_id,
    p.name,
    p.age,
    p.nationality,
    p.height_cm,
    p.weight_kg,
    p.injured,
    s.team_id,
    s.team_name,
    s.league_id,
    s.season,
    s.position,
    s.appearances,
    s.minutes,
    s.rating,
    s.goals,
    s.assists,
    s.shots_total,
    s.shots_on_target,
    s.passes_total,
    s.passes_key,
    s.passes_accuracy_pct,
    s.tackles_total,
    s.duels_total,
    s.duels_won,
    s.dribbles_attempts,
    s.dribbles_success,
    s.fouls_drawn,
    s.fouls_committed,
    s.cards_yellow,
    s.cards_red
from player p
inner join stats s using (player_row_id)
