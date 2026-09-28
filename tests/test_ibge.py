from datetime import date
from decimal import Decimal

import pytest

from indicadores import ibge
from indicadores.http import sessao


def test_interpretar_acha_o_periodo_pelo_cabecalho():
    # período na D1, e não na D3 como na tabela 6381: a ordem não importa
    corpo = [
        {"V": "Valor", "D1C": "Mês (Código)", "D1N": "Mês", "D2C": "Brasil (Código)"},
        {"V": "7.8", "D1C": "202405", "D1N": "maio 2024", "D2C": "1"},
        {"V": "...", "D1C": "202406", "D1N": "junho 2024", "D2C": "1"},
        {"V": "-", "D1C": "202407", "D1N": "julho 2024", "D2C": "1"},
    ]
    obs = ibge.interpretar(corpo)
    assert [(o.data, o.valor) for o in obs] == [(date(2024, 5, 1), Decimal("7.8"))]


def test_interpretar_sem_coluna_de_periodo_falha():
    with pytest.raises(ValueError, match="período"):
        ibge.interpretar([{"V": "Valor", "D1C": "Brasil (Código)"}, {"V": "1", "D1C": "1"}])


def test_interpretar_corpo_vazio():
    assert ibge.interpretar([]) == []


def test_buscar_na_api(apis_locais):
    obs = ibge.buscar("6381:4099", date(2024, 1, 1), date(2024, 6, 30), sessao())
    assert [o.data.month for o in obs] == [1, 2, 3, 4, 5, 6]


def test_periodo_sem_dado_e_lista_vazia(apis_locais):
    assert ibge.buscar("6381:4099", date(2099, 1, 1), date(2099, 3, 31), sessao()) == []
