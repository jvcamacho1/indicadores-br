-- As fontes, já padronizadas, numa tabela só.
select * from {{ ref('stg_bcb__observacoes') }}
union all
select * from {{ ref('stg_ibge__observacoes') }}
