{#
  Por padrão o dbt prefixa o schema do target (analytics_staging). Aqui o
  nome configurado vale como está: staging, intermediate, marts.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}{{ target.schema }}{%- else -%}{{ custom_schema_name | trim }}{%- endif -%}
{%- endmacro %}
