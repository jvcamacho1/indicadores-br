{#
  A tabela que o painel lê: um mês por linha, um indicador por coluna,
  mais as métricas derivadas.
#}
with fatos as (
    select
        c.mes,
        max(case when f.indicador_id = 'selic_meta'  then f.valor end) as selic_meta,
        max(case when f.indicador_id = 'ipca_mensal' then f.valor end) as ipca_mensal,
        max(case when f.indicador_id = 'ipca_12m'    then f.valor end) as ipca_12m,
        max(case when f.indicador_id = 'dolar_venda' then f.valor end) as dolar_venda,
        max(case when f.indicador_id = 'ibc_br'      then f.valor end) as ibc_br,
        max(case when f.indicador_id = 'desocupacao' then f.valor end) as desocupacao
    from {{ ref('dim_calendario') }} as c
    left join {{ ref('fct_indicador_mensal') }} as f using (mes)
    group by c.mes
),

com_janelas as (
    select
        *,
        -- produto das 12 últimas variações: exp(soma dos logaritmos)
        exp(sum(ln(1 + ipca_mensal / 100.0)) over ultimos_12) as fator_12m,
        count(ipca_mensal) over ultimos_12                       as meses_com_ipca,
        lag(ibc_br, 12) over (order by mes)                      as ibc_br_ano_anterior
    from fatos
    window ultimos_12 as (order by mes rows between 11 preceding and current row)
)

select
    mes,
    selic_meta,
    ipca_mensal,
    ipca_12m,
    case when meses_com_ipca = 12 then round((fator_12m - 1) * 100, 2) end as ipca_12m_calculado,
    {{ juros_real('selic_meta', 'ipca_12m') }}                           as juros_real,
    dolar_venda,
    ibc_br,
    round((ibc_br / nullif(ibc_br_ano_anterior, 0) - 1) * 100, 2)        as ibc_br_var_12m,
    desocupacao
from com_janelas
