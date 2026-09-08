-- One row per league in the configured scope.

select *
from (
    values
        (39, 'Premier League'),
        (61, 'Ligue 1'),
        (78, 'Bundesliga'),
        (135, 'Serie A'),
        (140, 'La Liga')
) as leagues(league_id, league_name)
