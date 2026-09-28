{#
  O fato central: indicador x mês. Incremental: numa execução normal, só
  entram os meses cujo dado chegou ou mudou desde a última execução
  (carregado_em). Revisões da fonte reprocessam só o mês revisado.
  `dbt build --full-refresh` reconstrói tudo.
#}
{{
    config(
        materialized='incremental',
        unique_key='indicador_mes_id',
        incremental_strategy='delete+insert',
        on_schema_change='fail'
    )
}}

select
    indicador_id || '|' || to_char(mes, 'YYYY-MM') as indicador_mes_id,
    indicador_id,
    mes,
    valor,
    n_observacoes,
    carregado_em
from {{ ref('int_indicador_mensal') }}

{% if is_incremental() %}
where carregado_em > (select coalesce(max(carregado_em), '1900-01-01') from {{ this }})
{% endif %}
