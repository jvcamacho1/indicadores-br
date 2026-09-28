"""O DAG importa e tem a forma esperada. Só roda onde o Airflow está instalado."""

from pathlib import Path

import pytest

pytest.importorskip("airflow")

from airflow.dag_processing.dagbag import DagBag  # noqa: E402

DAGS = Path(__file__).resolve().parent.parent / "dags"


@pytest.fixture(scope="module")
def dag():
    bag = DagBag(dag_folder=str(DAGS))
    assert bag.import_errors == {}
    return bag.get_dag("indicadores_br")


def test_tasks_e_ordem(dag):
    assert set(dag.task_ids) == {
        "listar_indicadores",
        "extrair_e_carregar",
        "so_a_execucao_mais_recente",
        "dbt_freshness_e_build",
        "dbt_docs",
        "montar_site",
    }
    assert dag.get_task("so_a_execucao_mais_recente").upstream_task_ids == {"extrair_e_carregar"}
    assert dag.get_task("montar_site").upstream_task_ids == {"dbt_docs"}


def test_agenda_e_retries(dag):
    assert dag.catchup is True
    assert dag.get_task("extrair_e_carregar").retries == 3
