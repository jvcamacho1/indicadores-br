"""Cliente do SGS, o Sistema Gerenciador de Séries Temporais do Banco Central.

    GET /dados/serie/bcdata.sgs.{codigo}/dados?formato=json&dataInicial=dd/mm/aaaa&dataFinal=dd/mm/aaaa
    -> [{"data": "02/01/2024", "valor": "4.8526"}, ...]

O SGS limita a consulta de séries diárias a uma janela de 10 anos, então
janelas longas são quebradas em pedaços de até 5 anos. Um intervalo sem
dado responde 404, e isso não é erro: é uma lista vazia.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from decimal import Decimal

import requests

from indicadores.http import TIMEOUT
from indicadores.modelos import Observacao

ANOS_POR_JANELA = 5


def base_url() -> str:
    return os.environ.get("BCB_BASE_URL", "https://api.bcb.gov.br").rstrip("/")


def janelas(inicio: date, fim: date, anos: int = ANOS_POR_JANELA) -> Iterator[tuple[date, date]]:
    atual = inicio
    while atual <= fim:
        limite = date(atual.year + anos, atual.month, 1) - timedelta(days=1)
        yield atual, min(limite, fim)
        atual = min(limite, fim) + timedelta(days=1)


def buscar(codigo: str, inicio: date, fim: date, sessao: requests.Session) -> list[Observacao]:
    observacoes: list[Observacao] = []
    for ini, fi in janelas(inicio, fim):
        observacoes += _buscar_janela(codigo, ini, fi, sessao)
    return observacoes


def _buscar_janela(codigo: str, inicio: date, fim: date, sessao: requests.Session) -> list[Observacao]:
    resposta = sessao.get(
        f"{base_url()}/dados/serie/bcdata.sgs.{codigo}/dados",
        params={
            "formato": "json",
            "dataInicial": inicio.strftime("%d/%m/%Y"),
            "dataFinal": fim.strftime("%d/%m/%Y"),
        },
        timeout=TIMEOUT,
    )
    if resposta.status_code == 404:
        return []
    resposta.raise_for_status()
    corpo = resposta.json()
    if not isinstance(corpo, list):
        raise ValueError(f"SGS {codigo}: resposta inesperada: {str(corpo)[:200]}")
    return [
        Observacao(
            data=datetime.strptime(item["data"], "%d/%m/%Y").date(),
            valor=Decimal(item["valor"]),
        )
        for item in corpo
        if item.get("valor") not in (None, "")
    ]
