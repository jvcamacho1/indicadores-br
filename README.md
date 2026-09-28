# indicadores-br

**ELT de indicadores econômicos do Brasil com Airflow + dbt.** Selic, IPCA,
juros real, dólar, IBC-Br e desemprego, direto das APIs públicas do Banco
Central (SGS) e do IBGE (SIDRA), modelados em camadas e publicados como um
painel estático.

**Painel:** https://jvcamacho1.github.io/indicadores-br/ ·
**Documentação e linhagem (dbt docs):** https://jvcamacho1.github.io/indicadores-br/dbt-docs/

> *EN: An ELT pipeline for Brazilian economic indicators (Central Bank and
> IBGE public APIs), orchestrated by Airflow, modeled with dbt on Postgres,
> and published as a static dashboard. Everything runs locally with Docker;
> only the static result is online.*

## Arquitetura

```
 APIs públicas             Local (docker compose)                                      Online
┌──────────────┐   ┌───────────────────────────────────────────────────────────┐   ┌──────────────────┐
│ BCB · SGS    │──▶│ Airflow (DAG mensal, catchup)                             │   │ GitHub Pages     │
│ IBGE · SIDRA │   │   extrair_e_carregar[6] ─▶ Postgres raw (upsert)          │   │  painel          │
└──────────────┘   │   so_a_execucao_mais_recente                              │──▶│  dbt docs        │
                   │   dbt: source freshness ─▶ build (staging ▶ marts, testes) │   │ (branch gh-pages)│
                   │   dbt docs ─▶ montar_site ─▶ build/site                    │   └──────────────────┘
                   └───────────────────────────────────────────────────────────┘
```

Só o resultado estático fica online, e o painel mostra a data da última
atualização. Para ele não depender de uma máquina ligada, um workflow do
GitHub Actions (`publicar.yml`) refaz a extração e o dbt uma vez por mês e
republica. O Airflow continua sendo o orquestrador do projeto; o workflow só
mantém a vitrine atualizada.

## O que o projeto demonstra

| Tema | Onde |
|---|---|
| **Orquestração** com retries, backoff exponencial, `catchup` e backfill | `dags/indicadores_br.py` |
| **Dynamic task mapping**: uma task por indicador do catálogo | `extrair_e_carregar.expand(...)` |
| **Janela com recuo** de 3 meses: pega dado atrasado (IPCA) e revisões | `indicadores/extracao.py` |
| **Backfill que só carrega**: transformar e publicar é da execução mais recente (`LatestOnlyOperator`) | DAG |
| **Carga idempotente**: upsert por (indicador, data), log de execuções | `indicadores/carga.py` |
| **Catálogo como dado**: indicador novo é uma linha no seed | `dbt/seeds/indicadores.csv` |
| **Modelagem em camadas**: staging por fonte → intermediate mensal → marts | `dbt/models/` |
| **Fato incremental** (`delete+insert` por `carregado_em`) | `fct_indicador_mensal` |
| **Testes de dados**: chaves, relacionamentos, faixas plausíveis, freshness | `_marts.yml`, `_sources.yml` |
| **Reconciliação entre séries**: IPCA 12m publicado × acumulado do mensal | `tests/assert_ipca_12m_reconcilia_com_mensal.sql` |
| **Unit tests do dbt**: juros real pela equação de Fisher | `_marts.yml` |
| **dbt e Airflow em ambientes separados** (as dependências brigam) | `docker/airflow.Dockerfile` |
| **CI**: lint, pytest, pipeline completo contra uma API falsa, import do DAG | `.github/workflows/ci.yml` |

## Os dados

| Indicador | Fonte | Série | Agregação mensal |
|---|---|---|---|
| Selic (meta) | BCB · SGS | 432 | último valor do mês |
| IPCA (variação mensal) | BCB · SGS | 433 | valor do mês |
| IPCA acumulado em 12 meses | BCB · SGS | 13522 | valor do mês |
| Dólar comercial (venda) | BCB · SGS | 1 | média dos dias úteis |
| IBC-Br (dessazonalizado) | BCB · SGS | 24364 | valor do mês |
| Taxa de desocupação | IBGE · SIDRA | tabela 6381, variável 4099 | trimestre móvel terminado no mês |

## Modelo

```
raw.observacoes, raw.cargas          (extração)
  └─ staging.stg_bcb__observacoes, stg_ibge__observacoes, stg_indicadores (seed)
       └─ intermediate.int_observacoes ─▶ int_indicador_mensal     (granularidade: indicador × mês)
            └─ marts.fct_indicador_mensal  (incremental)
               marts.dim_indicador, marts.dim_calendario
               marts.mart_painel_mensal    (um mês por linha; juros real, IPCA 12m recalculado, IBC-Br 12m)
```

## Como rodar

Pré-requisitos: Docker e `make`.

```bash
make up          # Postgres + Airflow em http://localhost:8080
make backfill    # DAG de 2015 até hoje (ou: make carregar, sem Airflow, mais rápido)
make dbt         # freshness + dbt build
make site        # dbt docs + build/site
make ver         # abre o site em http://localhost:8000
make publicar    # envia build/site para a branch gh-pages
```

No Airflow, ative o DAG `indicadores_br`: a execução mais recente extrai,
roda o dbt e monta o site sozinha.

### Sem internet ou sem Docker

`tests/fake_api.py` imita as duas APIs com dados **sintéticos**, no mesmo
formato das reais. É o que o CI usa para rodar o pipeline inteiro sem depender
do governo estar no ar:

```bash
pip install -r requirements-dev.txt -r requirements-dbt.txt
python tests/fake_api.py &                        # http://127.0.0.1:8765
export BCB_BASE_URL=http://127.0.0.1:8765 IBGE_BASE_URL=http://127.0.0.1:8765 DADOS_SINTETICOS=1
export WAREHOUSE_HOST=localhost WAREHOUSE_USER=... WAREHOUSE_PASSWORD=... WAREHOUSE_DB=...
python -m indicadores carregar --desde 2015-01-01
(cd dbt && dbt build --profiles-dir . && dbt docs generate --static --profiles-dir .)
python -m indicadores site
```

Um site montado com dados sintéticos traz uma faixa de aviso, e o
`scripts/publicar.sh` se recusa a publicá-lo.

## Backlog

Melhorias planejadas, para aprender dbt e Airflow na prática:
[`docs/backlog.md`](docs/backlog.md).

## Estrutura

```
dags/                 DAG do Airflow
indicadores/          extração e carga (clientes do SGS e do SIDRA, upsert, CLI, montagem do site)
dbt/                  projeto dbt: seeds, staging, intermediate, marts, testes, macros
site/                 painel estático (HTML, CSS, JS com Chart.js), PT/EN
tests/                pytest + API falsa
docker/               imagem do Airflow (com o dbt num venv próprio) e init do warehouse
scripts/publicar.sh   publica build/site na gh-pages
docs/backlog.md       backlog de melhorias
```

---

Feito por **José Camacho** · [Portfólio](https://jvcamacho1.github.io) ·
[LinkedIn](https://www.linkedin.com/in/jvcamacho/)
