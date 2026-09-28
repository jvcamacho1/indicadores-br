"""Monta o site estático a partir dos marts.

Lê `marts.mart_painel_mensal` e `marts.dim_indicador`, grava `data.json`
ao lado dos arquivos de `site/` e copia a documentação estática do dbt.
O resultado é uma pasta que qualquer servidor de arquivos serve, e é o que
vai para a branch gh-pages.

Com DADOS_SINTETICOS=1 (CI e testes com a API falsa), o site mostra uma
faixa avisando que os números são inventados.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from indicadores import carga

log = logging.getLogger(__name__)

RAIZ = Path(__file__).resolve().parent.parent
FONTE_DO_SITE = RAIZ / "site"

COLUNAS = [
    "selic_meta",
    "ipca_mensal",
    "ipca_12m",
    "ipca_12m_calculado",
    "juros_real",
    "dolar_venda",
    "ibc_br",
    "ibc_br_var_12m",
    "desocupacao",
]


def _numero(valor):
    return float(valor) if isinstance(valor, Decimal) else valor


def exportar() -> dict:
    conn = carga.conectar()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"select to_char(mes, 'YYYY-MM'), {', '.join(COLUNAS)}"
                " from marts.mart_painel_mensal order by mes"
            )
            meses = [
                {"mes": linha[0], **{c: _numero(v) for c, v in zip(COLUNAS, linha[1:], strict=True)}}
                for linha in cur.fetchall()
            ]
            cur.execute(
                "select indicador_id, fonte, codigo_fonte, nome, nome_en, unidade,"
                " descricao, descricao_en from marts.dim_indicador order by indicador_id"
            )
            nomes = [d.name for d in cur.description]
            indicadores = [dict(zip(nomes, linha, strict=True)) for linha in cur.fetchall()]
            cur.execute(
                "select f.indicador_id, to_char(max(f.mes), 'YYYY-MM')"
                " from marts.fct_indicador_mensal f group by f.indicador_id"
            )
            ultimo_mes = dict(cur.fetchall())
    finally:
        conn.close()
    for i in indicadores:
        i["ultimo_mes"] = ultimo_mes.get(i["indicador_id"])
    return {
        "gerado_em": datetime.now(UTC).isoformat(timespec="seconds"),
        "sintetico": os.environ.get("DADOS_SINTETICOS") == "1",
        "indicadores": indicadores,
        "meses": meses,
    }


def montar(saida: Path, dbt_target: Path) -> Path:
    if saida.exists():
        shutil.rmtree(saida)
    shutil.copytree(FONTE_DO_SITE, saida)
    dados = exportar()
    (saida / "data.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    docs = dbt_target / "static_index.html"
    if docs.exists():
        (saida / "dbt-docs").mkdir()
        shutil.copy(docs, saida / "dbt-docs" / "index.html")
    else:
        log.warning("sem %s: rode `dbt docs generate --static` antes", docs)
    (saida / ".nojekyll").touch()
    log.info("site montado em %s (%d meses)", saida, len(dados["meses"]))
    return saida
