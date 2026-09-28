from datetime import date
from decimal import Decimal

from indicadores import bcb
from indicadores.http import sessao


def test_janelas_quebram_periodos_longos():
    janelas = list(bcb.janelas(date(2015, 1, 1), date(2026, 9, 27)))
    assert janelas[0] == (date(2015, 1, 1), date(2019, 12, 31))
    assert janelas[-1] == (date(2025, 1, 1), date(2026, 9, 27))
    # contíguas, sem buraco nem sobreposição
    for (_, fim), (inicio, _) in zip(janelas, janelas[1:], strict=False):
        assert (inicio - fim).days == 1


def test_janela_curta_e_uma_so():
    assert list(bcb.janelas(date(2026, 6, 1), date(2026, 8, 31))) == [(date(2026, 6, 1), date(2026, 8, 31))]


def test_buscar_serie_mensal(apis_locais):
    obs = bcb.buscar("433", date(2024, 1, 1), date(2024, 3, 31), sessao())
    assert [o.data for o in obs] == [date(2024, 1, 1), date(2024, 2, 1), date(2024, 3, 1)]
    assert all(isinstance(o.valor, Decimal) for o in obs)


def test_buscar_serie_diaria_atravessa_janelas(apis_locais):
    obs = bcb.buscar("432", date(2015, 1, 1), date(2021, 1, 10), sessao())
    datas = [o.data for o in obs]
    assert datas == sorted(set(datas))
    assert datas[0] == date(2015, 1, 1) and datas[-1] == date(2021, 1, 8)


def test_intervalo_sem_dado_e_lista_vazia(apis_locais):
    # a API falsa, como a real, responde 404 quando não há observação
    assert bcb.buscar("433", date(2024, 1, 2), date(2024, 1, 20), sessao()) == []


class _Resposta:
    status_code = 200

    def __init__(self, corpo):
        self._corpo = corpo

    def json(self):
        return self._corpo

    def raise_for_status(self):
        pass


class _Sessao:
    def __init__(self, corpo):
        self.corpo = corpo

    def get(self, *args, **kwargs):
        return _Resposta(self.corpo)


def test_valor_vazio_e_ignorado():
    corpo = [{"data": "01/02/2024", "valor": "0.83"}, {"data": "01/03/2024", "valor": ""}]
    obs = bcb.buscar("433", date(2024, 2, 1), date(2024, 3, 31), _Sessao(corpo))
    assert [(o.data, o.valor) for o in obs] == [(date(2024, 2, 1), Decimal("0.83"))]
