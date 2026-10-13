{% macro age_in_years(date_expression) %}
    {{ return(adapter.dispatch('age_in_years', 'soccer_analytics')(date_expression)) }}
{% endmacro %}

{% macro default__age_in_years(date_expression) %}
    date_diff('year', cast({{ date_expression }} as date), current_date)
{% endmacro %}

{% macro databricks__age_in_years(date_expression) %}
    year(current_date()) - year(cast({{ date_expression }} as date))
{% endmacro %}

{% macro regex_matches(expression, pattern) %}
    {{ return(adapter.dispatch('regex_matches', 'soccer_analytics')(expression, pattern)) }}
{% endmacro %}

{% macro default__regex_matches(expression, pattern) %}
    regexp_matches({{ expression }}, '{{ pattern }}')
{% endmacro %}

{% macro databricks__regex_matches(expression, pattern) %}
    regexp_like({{ expression }}, '{{ pattern }}')
{% endmacro %}

{% macro regex_replace_all(expression, pattern, replacement) %}
    {{ return(adapter.dispatch('regex_replace_all', 'soccer_analytics')(expression, pattern, replacement)) }}
{% endmacro %}

{% macro default__regex_replace_all(expression, pattern, replacement) %}
    regexp_replace({{ expression }}, '{{ pattern }}', '{{ replacement }}', 'g')
{% endmacro %}

{% macro databricks__regex_replace_all(expression, pattern, replacement) %}
    regexp_replace({{ expression }}, '{{ pattern }}', '{{ replacement }}')
{% endmacro %}
