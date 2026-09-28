"""Imitação local das APIs do BCB (SGS) e do IBGE (SIDRA), com dados SINTÉTICOS.

Responde no mesmo formato das APIs reais, para que o pipeline inteiro
(extração, dbt, site) rode sem internet: nos testes, no CI e em quem quer
experimentar o projeto offline. Os números são inventados, mas coerentes
entre si. O IPCA de 12 meses, por exemplo, é o acumulado exato do mensal,
para que o teste de reconciliação do dbt passe.

    python tests/fake_api.py --porta 8765
    BCB_BASE_URL=http://127.0.0.1:8765 IBGE_BASE_URL=http://127.0.0.1:8765 python -m indicadores carregar ...
"""

from __future__ import annotations

import argparse
import json
import math
import re
import threading
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

INICIO = date(2014, 1, 1)


def _meses(ate: date):
    ate = min(ate, date.today())  # como a API real: nada publicado no futuro
    ano, mes = INICIO.year, INICIO.month
    while date(ano, mes, 1) <= ate:
        yield date(ano, mes, 1)
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def _t(d: date) -> int:
    return (d.year - INICIO.year) * 12 + d.month - INICIO.month


def ipca_mensal(d: date) -> float:
    return round(0.40 + 0.30 * math.sin(_t(d) / 5), 2)


def serie_mensal(codigo: str, ate: date) -> dict[date, float]:
    meses = list(_meses(ate))
    if codigo == "433":
        return {m: ipca_mensal(m) for m in meses}
    if codigo == "13522":
        saida = {}
        for i, m in enumerate(meses[11:], start=11):
            fator = math.prod(1 + ipca_mensal(x) / 100 for x in meses[i - 11 : i + 1])
            saida[m] = round((fator - 1) * 100, 2)
        return saida
    if codigo == "24364":
        return {m: round(135 + 8 * math.sin(_t(m) / 9) + _t(m) * 0.05, 2) for m in meses}
    if codigo == "6381:4099":
        return {m: round(10 + 3 * math.sin(_t(m) / 14), 1) for m in meses}
    raise KeyError(codigo)


def serie_diaria(codigo: str, ate: date) -> dict[date, float]:
    saida, d = {}, INICIO
    while d <= min(ate, date.today()):
        if d.weekday() < 5:
            t = (d - INICIO).days
            if codigo == "432":
                saida[d] = round((10 + 4 * math.sin(t / 400)) * 4) / 4
            elif codigo == "1":
                saida[d] = round(3 + 2.5 * t / 4700 + 0.15 * math.sin(t / 30), 4)
            else:
                raise KeyError(codigo)
        d += timedelta(days=1)
    return saida


DIARIAS = {"432", "1"}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silencioso
        pass

    def _json(self, status: int, corpo) -> None:
        dados = json.dumps(corpo).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):  # noqa: N802
        url = urlparse(self.path)
        if m := re.fullmatch(r"/dados/serie/bcdata\.sgs\.(\d+)/dados", url.path):
            return self._sgs(m.group(1), parse_qs(url.query))
        if m := re.fullmatch(r"/values/t/(\d+)/n1/all/v/(\d+)/p/(\d{6})-(\d{6})", url.path):
            return self._sidra(*m.groups())
        return self._json(404, {"erro": "rota desconhecida"})

    def _sgs(self, codigo: str, q: dict) -> None:
        ini = datetime.strptime(q["dataInicial"][0], "%d/%m/%Y").date()
        fim = datetime.strptime(q["dataFinal"][0], "%d/%m/%Y").date()
        serie = serie_diaria(codigo, fim) if codigo in DIARIAS else serie_mensal(codigo, fim)
        itens = [
            {"data": d.strftime("%d/%m/%Y"), "valor": f"{v}"}
            for d, v in sorted(serie.items())
            if ini <= d <= fim
        ]
        if not itens:
            return self._json(404, {"error": "Value(s) not found"})
        return self._json(200, itens)

    def _sidra(self, tabela: str, variavel: str, p_ini: str, p_fim: str) -> None:
        fim = date(int(p_fim[:4]), int(p_fim[4:]), 1)
        serie = serie_mensal(f"{tabela}:{variavel}", fim)
        cabecalho = {
            "NC": "Nível Territorial (Código)",
            "NN": "Nível Territorial",
            "MC": "Unidade de Medida (Código)",
            "MN": "Unidade de Medida",
            "V": "Valor",
            "D1C": "Brasil (Código)",
            "D1N": "Brasil",
            "D2C": "Variável (Código)",
            "D2N": "Variável",
            "D3C": "Trimestre Móvel (Código)",
            "D3N": "Trimestre Móvel",
        }
        linhas = [
            {
                "NC": "1",
                "NN": "Brasil",
                "MC": "2",
                "MN": "%",
                "V": f"{v}",
                "D1C": "1",
                "D1N": "Brasil",
                "D2C": variavel,
                "D2N": "Taxa de desocupação",
                "D3C": f"{m:%Y%m}",
                "D3N": f"{m:%m/%Y}",
            }
            for m, v in sorted(serie.items())
            if p_ini <= f"{m:%Y%m}" <= p_fim
        ]
        if not linhas:
            return self._json(400, "Período não disponível")
        return self._json(200, [cabecalho, *linhas])


def iniciar(porta: int = 0) -> ThreadingHTTPServer:
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--porta", type=int, default=8765)
    porta = parser.parse_args().porta
    print(f"API falsa (dados sintéticos) em http://127.0.0.1:{porta}")
    ThreadingHTTPServer(("127.0.0.1", porta), Handler).serve_forever()
