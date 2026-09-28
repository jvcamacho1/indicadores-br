"""O catálogo de indicadores.

A fonte da verdade é o seed do dbt (`dbt/seeds/indicadores.csv`): a mesma
tabela vira `dim_indicador` no warehouse e diz à extração o que buscar.
Indicador novo entra por uma linha no CSV, sem mexer em código.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

CSV_PADRAO = Path(__file__).resolve().parent.parent / "dbt" / "seeds" / "indicadores.csv"
FONTES = {"bcb", "ibge"}
AGREGACOES = {"valor", "ultimo", "media"}


@dataclass(frozen=True)
class Indicador:
    indicador_id: str
    fonte: str
    codigo_fonte: str
    nome: str
    unidade: str
    periodicidade: str
    agregacao_mensal: str


def carregar(caminho: Path = CSV_PADRAO) -> list[Indicador]:
    with caminho.open(encoding="utf-8", newline="") as f:
        linhas = list(csv.DictReader(f))
    indicadores = [
        Indicador(
            indicador_id=linha["indicador_id"],
            fonte=linha["fonte"],
            codigo_fonte=linha["codigo_fonte"],
            nome=linha["nome"],
            unidade=linha["unidade"],
            periodicidade=linha["periodicidade"],
            agregacao_mensal=linha["agregacao_mensal"],
        )
        for linha in linhas
    ]
    _validar(indicadores)
    return indicadores


def buscar(indicador_id: str, caminho: Path = CSV_PADRAO) -> Indicador:
    for indicador in carregar(caminho):
        if indicador.indicador_id == indicador_id:
            return indicador
    raise KeyError(f"indicador desconhecido: {indicador_id}")


def _validar(indicadores: list[Indicador]) -> None:
    ids = [i.indicador_id for i in indicadores]
    if len(ids) != len(set(ids)):
        raise ValueError("indicador_id repetido no catálogo")
    for i in indicadores:
        if i.fonte not in FONTES:
            raise ValueError(f"{i.indicador_id}: fonte inválida {i.fonte!r}")
        if i.agregacao_mensal not in AGREGACOES:
            raise ValueError(f"{i.indicador_id}: agregação inválida {i.agregacao_mensal!r}")
