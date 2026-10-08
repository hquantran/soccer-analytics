-- Compare the serving rates to independent additive fact inputs.
select b.player_season_id
from {{ ref('bi_player_seasons') }} b
join {{ ref('fct_player_seasons') }} f using (player_season_id)
where
{% for name in var('canonical_metrics') %}
    (b.{{ name }} is null and {{ canonical_rate(name, aggregate=false) }} is not null)
    or (b.{{ name }} is not null and {{ canonical_rate(name, aggregate=false) }} is null)
    or abs(b.{{ name }} - round({{ canonical_rate(name, aggregate=false) }}, 3)) > 0.000001
    {% if not loop.last %}or{% endif %}
{% endfor %}
