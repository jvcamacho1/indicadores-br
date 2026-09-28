{#
  Faixa plausível para um valor econômico. Não prova que o dado está
  certo, mas pega o erro grosseiro: vírgula decimal lida como milhar,
  unidade trocada, série errada no catálogo.
#}
{% test valor_entre(model, column_name, minimo, maximo) %}
select {{ column_name }}
from {{ model }}
where {{ column_name }} is not null
  and ({{ column_name }} < {{ minimo }} or {{ column_name }} > {{ maximo }})
{% endtest %}
