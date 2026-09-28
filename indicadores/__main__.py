"""Linha de comando, para carga completa fora do Airflow (CI, publicação, testes).

python -m indicadores carregar --desde 2015-01-01 [--ate 2026-09-30] [--indicador selic_meta]
python -m indicadores site --saida build/site
"""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

from indicadores import catalogo, extracao, site


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="python -m indicadores")
    sub = parser.add_subparsers(dest="comando", required=True)

    p_carregar = sub.add_parser("carregar", help="extrai e carrega no warehouse")
    p_carregar.add_argument("--desde", type=date.fromisoformat, required=True)
    p_carregar.add_argument("--ate", type=date.fromisoformat, default=date.today())
    p_carregar.add_argument("--indicador", action="append", help="repita para mais de um")

    p_site = sub.add_parser("site", help="monta o site estático a partir dos marts")
    p_site.add_argument("--saida", type=Path, default=Path("build/site"))
    p_site.add_argument("--dbt-target", type=Path, default=Path("dbt/target"))

    args = parser.parse_args()
    if args.comando == "carregar":
        ids = args.indicador or [i.indicador_id for i in catalogo.carregar()]
        for indicador_id in ids:
            extracao.extrair_e_carregar(indicador_id, args.desde, args.ate)
    else:
        site.montar(args.saida, args.dbt_target)


if __name__ == "__main__":
    main()
