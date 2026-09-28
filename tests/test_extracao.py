from datetime import date

import pytest

from indicadores import extracao


@pytest.mark.parametrize(
    ("inicio", "fim", "esperado"),
    [
        # execução agendada de @monthly: intervalo [1º do mês, 1º do mês seguinte)
        (date(2024, 5, 1), date(2024, 6, 1), (date(2024, 2, 1), date(2024, 5, 31))),
        # recuar atravessa a virada do ano
        (date(2024, 2, 1), date(2024, 3, 1), (date(2023, 11, 1), date(2024, 2, 29))),
        # execução manual no Airflow 3: intervalo vazio
        (date(2024, 5, 10), date(2024, 5, 10), (date(2024, 2, 1), date(2024, 5, 10))),
    ],
)
def test_janela_da_execucao(inicio, fim, esperado):
    assert extracao.janela_da_execucao(inicio, fim) == esperado
