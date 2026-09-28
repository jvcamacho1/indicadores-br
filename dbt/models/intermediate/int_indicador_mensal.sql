{#
  Tudo na mesma granularidade: um valor por indicador e mês.
  A regra de agregação vem do catálogo, porque depende do que a série mede:
    valor  -> a série já é mensal
    ultimo -> a meta Selic vigente no fim do mês
    media  -> o câmbio médio dos dias úteis
#}
with observacoes as (
    select
        o.indicador_id,
        date_trunc('month', o.data)::date as mes,
        o.data,
        o.valor,
        o.carregado_em,
        i.agregacao_mensal
    from {{ ref('int_observacoes') }} as o
    inner join {{ ref('stg_indicadores') }} as i using (indicador_id)
),

ordenadas as (
    select
        *,
        row_number() over (partition by indicador_id, mes order by data desc) as ordem_desc
    from observacoes
)

select
    indicador_id,
    mes,
    case max(agregacao_mensal)
        when 'media' then round(avg(valor), 4)
        else max(case when ordem_desc = 1 then valor end)
    end                   as valor,
    count(*)              as n_observacoes,
    max(carregado_em)     as carregado_em
from ordenadas
group by indicador_id, mes
