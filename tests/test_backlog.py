"""O backlog segue as próprias convenções (docs/backlog.md, seção "Como usar")."""

import re
from pathlib import Path

BACKLOG = Path(__file__).resolve().parent.parent / "docs" / "backlog.md"
STATUS = {"TODO", "FEITO", "PARCIAL", "BLOQUEADO"}
PRIORIDADES = {"P0", "P1", "P2", "P3"}
ESFORCOS = {"S", "M", "L"}
AREAS = {"dbt", "Airflow", "Ambos"}


def _texto() -> str:
    return BACKLOG.read_text(encoding="utf-8")


def _linhas_da_tabela() -> list[list[str]]:
    linhas = []
    for linha in _texto().splitlines():
        if re.match(r"^\|\s*(✅\s*)?IND-\d{3}\s*\|", linha):
            linhas.append([c.strip() for c in linha.strip().strip("|").split("|")])
    return linhas


def _id(celula: str) -> str:
    return celula.replace("✅", "").strip()


def test_a_tabela_tem_tarefas():
    assert len(_linhas_da_tabela()) >= 10


def test_toda_linha_tem_sete_colunas():
    for linha in _linhas_da_tabela():
        assert len(linha) == 7, linha


def test_nenhum_id_repetido():
    ids = [_id(linha[0]) for linha in _linhas_da_tabela()]
    assert len(ids) == len(set(ids))


def test_vocabulario_de_status_e_escalas():
    for id_, _tarefa, area, _nivel, prioridade, esforco, status in _linhas_da_tabela():
        assert status in STATUS, (id_, status)
        assert prioridade in PRIORIDADES, (id_, prioridade)
        assert esforco in ESFORCOS, (id_, esforco)
        assert area in AREAS, (id_, area)


def test_concluida_leva_check_e_so_ela():
    for linha in _linhas_da_tabela():
        tem_check = "✅" in linha[0]
        assert tem_check == (linha[6] == "FEITO"), linha[0]


def test_toda_tarefa_tem_secao_e_toda_secao_tem_tarefa():
    na_tabela = {_id(linha[0]) for linha in _linhas_da_tabela()}
    secoes = set(re.findall(r"^### (IND-\d{3}) — ", _texto(), flags=re.M))
    assert na_tabela == secoes


def test_toda_secao_tem_objetivo_e_criterio_de_aceite():
    blocos = re.split(r"^### ", _texto(), flags=re.M)[1:]
    for bloco in blocos:
        id_ = bloco.split(" ", 1)[0]
        assert "**Objetivo:**" in bloco, id_
        assert "**Critério de aceite:**" in bloco, id_
