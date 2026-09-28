"""Cliente da API do SIDRA, o banco de tabelas do IBGE.

    GET /values/t/{tabela}/n1/all/v/{variavel}/p/{aaaamm}-{aaaamm}
    -> [ {cabeçalho}, {"V": "6.8", "D3C": "202407", ...}, ... ]

A primeira linha é o cabeçalho: diz o que cada chave significa. A coluna
do período é achada por ele, e não por posição, porque a ordem das
dimensões muda de tabela para tabela. Valores como "..." e "-" são o jeito
do SIDRA dizer que não há dado.
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal, InvalidOperation

import requests

from indicadores.http import TIMEOUT
from indicadores.modelos import Observacao

PALAVRAS_DE_PERIODO = ("mês", "trimestre", "ano", "período")


def base_url() -> str:
    return os.environ.get("IBGE_BASE_URL", "https://apisidra.ibge.gov.br").rstrip("/")


def buscar(codigo: str, inicio: date, fim: date, sessao: requests.Session) -> list[Observacao]:
    """`codigo` é "tabela:variável", como em "6381:4099"."""
    tabela, variavel = codigo.split(":")
    resposta = sessao.get(
        f"{base_url()}/values/t/{tabela}/n1/all/v/{variavel}/p/{inicio:%Y%m}-{fim:%Y%m}",
        timeout=TIMEOUT,
    )
    if resposta.status_code in (400, 404) and "per" in resposta.text.lower():
        return []  # nenhum período publicado no intervalo
    resposta.raise_for_status()
    return interpretar(resposta.json())


def interpretar(corpo: list[dict[str, str]]) -> list[Observacao]:
    if not corpo:
        return []
    cabecalho, *linhas = corpo
    chave = _chave_do_periodo(cabecalho)
    observacoes = []
    for linha in linhas:
        valor = _decimal(linha.get("V", ""))
        if valor is None:
            continue
        codigo = linha[chave]
        observacoes.append(Observacao(data=date(int(codigo[:4]), int(codigo[4:6]), 1), valor=valor))
    return observacoes


def _chave_do_periodo(cabecalho: dict[str, str]) -> str:
    for chave, nome in cabecalho.items():
        nome = nome.lower()
        if chave.endswith("C") and "(código)" in nome and any(p in nome for p in PALAVRAS_DE_PERIODO):
            return chave
    raise ValueError(f"SIDRA: coluna de período não encontrada em {cabecalho}")


def _decimal(texto: str) -> Decimal | None:
    try:
        return Decimal(texto)
    except InvalidOperation:
        return None
