-- Um mês por linha, do primeiro ao último mês com dado.
with limites as (
    select min(mes) as primeiro, max(mes) as ultimo
    from {{ ref('int_indicador_mensal') }}
)

select
    mes::date                          as mes,
    extract(year from mes)::int        as ano,
    extract(month from mes)::int       as mes_do_ano,
    extract(quarter from mes)::int     as trimestre,
    to_char(mes, 'YYYY-MM')            as mes_iso
from limites,
    generate_series(primeiro, ultimo, interval '1 month') as mes
