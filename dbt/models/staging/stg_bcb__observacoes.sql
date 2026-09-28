select
    indicador_id,
    data::date                as data,
    valor::numeric(18, 6)     as valor,
    carregado_em
from {{ source('raw', 'observacoes') }}
where fonte = 'bcb'
