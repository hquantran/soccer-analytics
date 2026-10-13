-- Exercise the production macro with unequal season weights and zero denominators.
{% set metrics = var('canonical_metrics') %}
with inputs as (
    select 1 as player_id, 90 as minutes, 2 as goals, 1 as assists, 3 as passes_key,
           4 as tackles_total, 10 as passes_total, 8 as passes_completed,
           5 as duels_total, 3 as duels_won, 4 as dribbles_attempts, 2 as dribbles_success,
           10 as shots_total, 4 as shots_on_target, 2 as fouls_committed, 3 as fouls_drawn
    union all select 1, 810, 1, 2, 6, 8, 30, 27, 15, 9, 8, 6, 20, 8, 4, 6
    union all select 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
), actual as (
    select player_id,
    {% for name in metrics %}
        {{ canonical_rate(name, prefix='') }} as {{ name }}{% if not loop.last %},{% endif %}
    {% endfor %}
    from inputs group by player_id
)
select * from actual
where (player_id = 1 and (
    abs(goals_per90 - 0.3) > 0.000001
    or abs(assists_per90 - 0.3) > 0.000001
    or abs(key_passes_per90 - 0.9) > 0.000001
    or abs(tackles_per90 - 1.2) > 0.000001
    or abs(pass_accuracy_pct - 87.5) > 0.000001
    or abs(duel_success_pct - 60) > 0.000001
    or abs(dribble_attempts_per90 - 1.2) > 0.000001
    or abs(dribble_success_pct - (800.0 / 12)) > 0.000001
    or abs(goal_involvements_per90 - 0.6) > 0.000001
    or abs(successful_dribbles_per90 - 0.8) > 0.000001
    or abs(shot_accuracy_pct - 40) > 0.000001
    or abs(goal_conversion_pct - 10) > 0.000001
    or abs(fouls_per_tackle - 0.5) > 0.000001
    or abs(shots_per90 - 3) > 0.000001
    or abs(passes_per90 - 4) > 0.000001
    or abs(fouls_drawn_per90 - 0.9) > 0.000001
    {% for name in metrics %}or {{ name }} is null {% endfor %}
)) or (player_id = 2 and (
    {% for name in metrics %}{{ name }} is not null {% if not loop.last %} or {% endif %}{% endfor %}
))
