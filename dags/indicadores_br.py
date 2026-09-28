"""
### indicadores_br

ELT mensal dos indicadores econômicos do BCB (SGS) e do IBGE (SIDRA).

1. **extrair_e_carregar**: uma task por indicador do catálogo (dynamic task
   mapping). Busca a janela da execução mais 3 meses para trás, porque o
   IPCA sai no mês seguinte e as séries são revisadas, e grava com upsert
   em `raw.observacoes`.
2. **so_a_execucao_mais_recente**: no backfill, as execuções antigas só
   carregam dados. Transformar e publicar é trabalho da execução mais recente.
3. **dbt_freshness_e_build**: `dbt source freshness` e `dbt build` (modelos, testes
   de dados e testes unitários).
4. **dbt_docs**: documentação estática, com a linhagem.
5. **montar_site**: exporta os marts para `data.json` e monta o site em `build/site`.

Backfill desde 2015: `make backfill` (ou `airflow backfill create ...`).
"""

from __future__ import annotations

import os
from datetime import timedelta

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.latest_only import LatestOnlyOperator
from airflow.sdk import dag, get_current_context, task

PROJETO = os.environ.get("PROJETO_DIR", "/opt/projeto")
DBT = os.environ.get("DBT_BIN", "dbt")
DBT_ARGS = f"--project-dir {PROJETO}/dbt --profiles-dir {PROJETO}/dbt"


@dag(
    dag_id="indicadores_br",
    schedule="@monthly",
    start_date=pendulum.datetime(2015, 1, 1, tz="UTC"),
    catchup=True,
    max_active_runs=3,
    doc_md=__doc__,
    tags=["elt", "bcb", "ibge", "dbt"],
    default_args={
        "owner": "jose.camacho",
        "retries": 3,
        "retry_delay": timedelta(minutes=1),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=20),
    },
)
def indicadores_br():
    @task
    def listar_indicadores() -> list[str]:
        from indicadores import catalogo

        return [i.indicador_id for i in catalogo.carregar()]

    @task(max_active_tis_per_dagrun=3)
    def extrair_e_carregar(indicador_id: str) -> dict[str, int]:
        from indicadores import extracao

        contexto = get_current_context()
        inicio, fim = extracao.janela_da_execucao(
            contexto["data_interval_start"].date(), contexto["data_interval_end"].date()
        )
        return extracao.extrair_e_carregar(indicador_id, inicio, fim)

    @task
    def montar_site() -> str:
        from pathlib import Path

        from indicadores import site

        return str(site.montar(Path(PROJETO) / "build" / "site", Path(PROJETO) / "dbt" / "target"))

    cargas = extrair_e_carregar.expand(indicador_id=listar_indicadores())
    mais_recente = LatestOnlyOperator(task_id="so_a_execucao_mais_recente")
    dbt_build = BashOperator(
        task_id="dbt_freshness_e_build",
        bash_command=f"{DBT} source freshness {DBT_ARGS} && {DBT} build {DBT_ARGS}",
    )
    dbt_docs = BashOperator(
        task_id="dbt_docs",
        bash_command=f"{DBT} docs generate --static {DBT_ARGS}",
    )

    cargas >> mais_recente >> dbt_build >> dbt_docs >> montar_site()


indicadores_br()
