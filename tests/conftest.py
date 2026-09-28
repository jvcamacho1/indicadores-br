from __future__ import annotations

import pytest

from tests import fake_api

BANCO_DE_TESTE = "indicadores_teste"


@pytest.fixture(scope="session")
def api_falsa():
    servidor = fake_api.iniciar(0)
    yield f"http://127.0.0.1:{servidor.server_port}"
    servidor.shutdown()


@pytest.fixture
def apis_locais(api_falsa, monkeypatch):
    monkeypatch.setenv("BCB_BASE_URL", api_falsa)
    monkeypatch.setenv("IBGE_BASE_URL", api_falsa)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    return api_falsa


@pytest.fixture
def warehouse(monkeypatch):
    """Um banco descartável no Postgres do ambiente, ou skip se não houver Postgres.

    Nunca o banco configurado em WAREHOUSE_DB: os testes apagam e recriam
    o banco que usam.
    """
    psycopg2 = pytest.importorskip("psycopg2")
    from indicadores import carga

    try:
        admin = carga.conectar()
    except psycopg2.OperationalError:
        pytest.skip("sem Postgres (defina WAREHOUSE_HOST/PORT)")
    admin.autocommit = True
    with admin.cursor() as cur:
        cur.execute(f"drop database if exists {BANCO_DE_TESTE}")
        cur.execute(f"create database {BANCO_DE_TESTE}")
    monkeypatch.setenv("WAREHOUSE_DB", BANCO_DE_TESTE)
    conn = carga.conectar()
    carga.preparar(conn)
    yield conn
    conn.close()
    with admin.cursor() as cur:
        cur.execute(f"drop database if exists {BANCO_DE_TESTE}")
    admin.close()
