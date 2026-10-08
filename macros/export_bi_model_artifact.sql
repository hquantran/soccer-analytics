{% macro export_bi_model_artifact(format) %}
    {% if target.type == 'duckdb' %}
        {% set destination = "data/exports/" ~ this.identifier ~ "." ~ format %}
        {% if format == 'parquet' %}
            {{ return("COPY (SELECT * FROM " ~ (this | string) ~ ") TO '" ~ destination ~ "' (FORMAT PARQUET, COMPRESSION ZSTD);") }}
        {% else %}
            {{ return("COPY (SELECT * FROM " ~ (this | string) ~ ") TO '" ~ destination ~ "' (HEADER, DELIMITER ',');") }}
        {% endif %}
    {% else %}
        {{ return('select 1;') }}
    {% endif %}
{% endmacro %}