{{ config(materialized='table') }}

-- 2020-01-01 through 2026-12-31. Pure SQL generation also compiles offline.
select
{% if target.type == 'databricks' %}
    date_add(cast('2020-01-01' as date), cast(generated_number - 1 as int))
{% else %}
    cast('2020-01-01' as date) + cast(generated_number - 1 as int)
{% endif %}
    as date_day
from ({{ dbt_utils.generate_series(upper_bound=2557) }}) as spine
