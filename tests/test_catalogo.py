from pathlib import Path

import pytest

from indicadores import catalogo


def test_catalogo_carrega_os_seis_indicadores():
    ids = [i.indicador_id for i in catalogo.carregar()]
    assert ids == ["selic_meta", "ipca_mensal", "ipca_12m", "dolar_venda", "ibc_br", "desocupacao"]


def test_buscar_indicador_desconhecido():
    with pytest.raises(KeyError):
        catalogo.buscar("pib_da_lua")


def test_catalogo_recusa_id_repetido(tmp_path: Path):
    original = catalogo.CSV_PADRAO.read_text(encoding="utf-8").splitlines()
    csv = tmp_path / "c.csv"
    csv.write_text("\n".join([*original, original[1]]), encoding="utf-8")
    with pytest.raises(ValueError, match="repetido"):
        catalogo.carregar(csv)


def test_catalogo_recusa_agregacao_invalida(tmp_path: Path):
    original = catalogo.CSV_PADRAO.read_text(encoding="utf-8")
    csv = tmp_path / "c.csv"
    csv.write_text(original.replace(",diaria,ultimo,", ",diaria,mediana,"), encoding="utf-8")
    with pytest.raises(ValueError, match="agregação"):
        catalogo.carregar(csv)
