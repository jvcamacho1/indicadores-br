"""Sessão HTTP com retry para 429 e 5xx.

É a primeira linha de defesa contra instabilidade das APIs públicas. A
segunda são os retries da task no Airflow, com backoff exponencial.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

TIMEOUT = 60


def sessao() -> requests.Session:
    retry = Retry(
        total=4,
        backoff_factor=2,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        respect_retry_after_header=True,
    )
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = "indicadores-br (+https://github.com/jvcamacho1/indicadores-br)"
    return s
