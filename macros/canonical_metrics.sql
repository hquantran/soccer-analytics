{% macro canonical_numerator(name, prefix='') -%}
    {%- set numerator = var('canonical_metrics')[name].numerator -%}
    {%- if numerator is string -%}
        {{- prefix ~ numerator -}}
    {%- else -%}
        ({{ prefix }}{{ numerator | join(' + ' ~ prefix) }})
    {%- endif -%}
{%- endmacro %}

{% macro canonical_rate(name, prefix='f.', aggregate=true) %}
    {% set metric = var('canonical_metrics')[name] %}
    {% set numerator = canonical_numerator(name, prefix) %}
    {% set denominator = prefix ~ metric.denominator %}
    {% if aggregate %}
        {% set numerator = 'sum(' ~ numerator ~ ')' %}
        {% set denominator = 'sum(' ~ denominator ~ ')' %}
    {% endif %}
    ({{ metric.scale }}.0 * {{ numerator }} / nullif({{ denominator }}, 0))
{% endmacro %}
