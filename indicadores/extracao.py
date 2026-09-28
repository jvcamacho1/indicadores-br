"""Busca um indicador numa janela e grava no warehouse. É o que cada task do DAG executa."""

from __future__ import annotations

import logging
from datetime import date, timedelta

from indicadores import bcb, carga, catalogo, ibge
from indicadores.http import sessao

log = logging.getLogger(__name__)

CLIENTES = {"bcb": bcb.buscar, "ibge": ibge.buscar}
MESES_PARA_TRAS = 3


def janela_da_execucao(inicio: date, fim_exclusivo: date) -> tuple[date, date]:
    """A janela de uma execução do DAG: o intervalo agendado, recuado MESES_PARA_TRAS meses.

    Recuar é o que pega o dado que chega atrasado (o IPCA de um mês sai no
    seguinte) e as revisões. Numa execução manual o Airflow 3 dá um
    intervalo vazio (início = fim); aí a janela são os meses anteriores.
    """
    ano, mes = inicio.year, inicio.month - MESES_PARA_TRAS
    while mes < 1:
        ano, mes = ano - 1, mes + 12
    return date(ano, mes, 1), max(fim_exclusivo, inicio + timedelta(days=1)) - timedelta(days=1)


def extrair_e_carregar(indicador_id: str, inicio: date, fim: date) -> dict[str, int]:
    indicador = catalogo.buscar(indicador_id)
    observacoes = CLIENTES[indicador.fonte](indicador.codigo_fonte, inicio, fim, sessao())
    conn = carga.conectar()
    try:
        carga.preparar(conn)
        resultado = carga.gravar(conn, indicador_id, indicador.fonte, (inicio, fim), observacoes)
    finally:
        conn.close()
    log.info("%s %s..%s: %s", indicador_id, inicio, fim, resultado)
    return resultado
