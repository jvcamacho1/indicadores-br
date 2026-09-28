{#
  Juros real pela equação de Fisher: (1 + nominal) / (1 + inflação) - 1.
  A subtração simples (Selic - IPCA) superestima o juro real quando as
  taxas são altas, que é justamente o caso brasileiro.
#}
{% macro juros_real(nominal_pct, inflacao_pct) -%}
    round(((1 + {{ nominal_pct }} / 100.0) / (1 + {{ inflacao_pct }} / 100.0) - 1) * 100, 2)
{%- endmacro %}
