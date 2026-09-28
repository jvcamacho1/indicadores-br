from datetime import date
from decimal import Decimal

from indicadores import carga, extracao
from indicadores.modelos import Observacao


def _linhas(conn):
    with conn.cursor() as cur:
        cur.execute("select indicador_id, data, valor from raw.observacoes order by 1, 2")
        return cur.fetchall()


def test_upsert_e_idempotente(warehouse):
    obs = [Observacao(date(2024, 1, 1), Decimal("0.42")), Observacao(date(2024, 2, 1), Decimal("0.83"))]
    janela = (date(2024, 1, 1), date(2024, 2, 29))
    assert carga.gravar(warehouse, "ipca_mensal", "bcb", janela, obs) == {"recebidas": 2, "alteradas": 2}
    assert carga.gravar(warehouse, "ipca_mensal", "bcb", janela, obs) == {"recebidas": 2, "alteradas": 0}
    assert len(_linhas(warehouse)) == 2


def test_revisao_da_fonte_sobrescreve(warehouse):
    janela = (date(2024, 1, 1), date(2024, 1, 31))
    original = [Observacao(date(2024, 1, 1), Decimal("0.42"))]
    corrigido = [Observacao(date(2024, 1, 1), Decimal("0.44"))]
    carga.gravar(warehouse, "ipca_mensal", "bcb", janela, original)
    revisado = carga.gravar(warehouse, "ipca_mensal", "bcb", janela, corrigido)
    assert revisado["alteradas"] == 1
    assert _linhas(warehouse) == [("ipca_mensal", date(2024, 1, 1), Decimal("0.44"))]


def test_toda_execucao_fica_registrada(warehouse):
    carga.gravar(warehouse, "selic_meta", "bcb", (date(2024, 1, 1), date(2024, 1, 31)), [])
    with warehouse.cursor() as cur:
        cur.execute("select indicador_id, recebidas, alteradas from raw.cargas")
        assert cur.fetchall() == [("selic_meta", 0, 0)]


def test_extrair_e_carregar_ponta_a_ponta(warehouse, apis_locais):
    resultado = extracao.extrair_e_carregar("desocupacao", date(2024, 1, 1), date(2024, 12, 31))
    assert resultado == {"recebidas": 12, "alteradas": 12}
