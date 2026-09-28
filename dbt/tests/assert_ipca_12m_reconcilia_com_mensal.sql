{#
  Reconciliação entre duas séries da mesma fonte: o IPCA de 12 meses que o
  BC publica (série 13522) tem que bater com o acumulado das 12 variações
  mensais (série 433). Diferença acima de 0,05 p.p. é sinal de mês
  faltando, série trocada ou revisão não carregada.
#}
select mes, ipca_12m, ipca_12m_calculado
from {{ ref('mart_painel_mensal') }}
where ipca_12m is not null
  and ipca_12m_calculado is not null
  and abs(ipca_12m - ipca_12m_calculado) > 0.05
