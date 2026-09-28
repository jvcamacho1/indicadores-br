select
    indicador_id,
    fonte,
    codigo_fonte,
    nome,
    nome_en,
    unidade,
    periodicidade,
    agregacao_mensal,
    descricao,
    descricao_en
from {{ ref('indicadores') }}
