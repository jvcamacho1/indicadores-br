"""Carga idempotente no schema `raw` do warehouse.

Chave natural (indicador_id, data) com upsert: rodar a mesma janela duas
vezes não duplica nada, e uma revisão da fonte sobrescreve o valor antigo.
`carregado_em` só muda quando o valor muda, e é o que o modelo incremental
do dbt usa para saber o que reprocessar.

`alteradas` conta as linhas novas e as que mudaram de valor; numa carga
repetida da mesma janela, é zero.

Cada execução também deixa uma linha em `raw.cargas`. É por ela que o
`dbt source freshness` sabe se o pipeline parou de rodar.
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from datetime import date

import psycopg2
from psycopg2.extensions import connection
from psycopg2.extras import execute_values

from indicadores.modelos import Observacao

DDL = """
create schema if not exists raw;

create table if not exists raw.observacoes (
    indicador_id text        not null,
    fonte        text        not null,
    data         date        not null,
    valor        numeric     not null,
    carregado_em timestamptz not null default now(),
    primary key (indicador_id, data)
);

create table if not exists raw.cargas (
    id            bigserial   primary key,
    indicador_id  text        not null,
    janela_inicio date        not null,
    janela_fim    date        not null,
    recebidas     integer     not null,
    alteradas     integer     not null,
    executado_em  timestamptz not null default now()
);
"""

UPSERT = """
insert into raw.observacoes (indicador_id, fonte, data, valor)
values %s
on conflict (indicador_id, data) do update
    set valor = excluded.valor, carregado_em = now()
    where raw.observacoes.valor is distinct from excluded.valor
returning 1
"""


def conectar() -> connection:
    return psycopg2.connect(
        host=os.environ.get("WAREHOUSE_HOST", "localhost"),
        port=int(os.environ.get("WAREHOUSE_PORT", "5432")),
        user=os.environ.get("WAREHOUSE_USER", "warehouse"),
        password=os.environ.get("WAREHOUSE_PASSWORD", "warehouse"),
        dbname=os.environ.get("WAREHOUSE_DB", "warehouse"),
    )


def preparar(conn: connection) -> None:
    with conn, conn.cursor() as cur:
        cur.execute(DDL)


def gravar(
    conn: connection,
    indicador_id: str,
    fonte: str,
    janela: tuple[date, date],
    observacoes: Iterable[Observacao],
) -> dict[str, int]:
    linhas = [(indicador_id, fonte, o.data, o.valor) for o in observacoes]
    with conn, conn.cursor() as cur:
        alteradas = 0
        if linhas:
            alteradas = len(execute_values(cur, UPSERT, linhas, fetch=True))
        cur.execute(
            "insert into raw.cargas (indicador_id, janela_inicio, janela_fim, recebidas, alteradas)"
            " values (%s, %s, %s, %s, %s)",
            (indicador_id, janela[0], janela[1], len(linhas), alteradas),
        )
    return {"recebidas": len(linhas), "alteradas": alteradas}
