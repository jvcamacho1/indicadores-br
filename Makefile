# Atalhos. Rode `make` para ver a lista.
DESDE ?= 2015-01-01
ATE   ?= $(shell date +%Y-%m-01)
DC    = docker compose
EXEC  = $(DC) exec airflow
DBT   = $(EXEC) /home/airflow/dbt-venv/bin/dbt
DBT_ARGS = --project-dir /opt/projeto/dbt --profiles-dir /opt/projeto/dbt

.PHONY: help up down logs backfill carregar dbt docs site publicar ver test lint

help:  ## esta lista
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

.env:
	@echo "AIRFLOW_UID=$$(id -u)" > .env

up: .env  ## sobe Postgres + Airflow (http://localhost:8080)
	$(DC) up -d --build

down:  ## derruba os containers (os dados ficam no volume)
	$(DC) down

logs:  ## acompanha o log do Airflow
	$(DC) logs -f airflow

backfill:  ## backfill do DAG, de DESDE até ATE (padrão: 2015 até hoje)
	$(EXEC) airflow dags unpause indicadores_br
	$(EXEC) airflow backfill create --dag-id indicadores_br --from-date $(DESDE) --to-date $(ATE)

carregar:  ## carga completa sem Airflow (mais rápida que o backfill)
	$(EXEC) python -m indicadores carregar --desde $(DESDE)

dbt:  ## freshness + dbt build (modelos, testes e unit tests)
	$(DBT) source freshness $(DBT_ARGS)
	$(DBT) build $(DBT_ARGS)

docs:  ## documentação estática do dbt
	$(DBT) docs generate --static $(DBT_ARGS)

site: docs  ## monta o site em build/site
	$(EXEC) python -m indicadores site --saida /opt/projeto/build/site --dbt-target /opt/projeto/dbt/target

ver:  ## serve build/site em http://localhost:8000
	python3 -m http.server 8000 -d build/site

publicar:  ## publica build/site na branch gh-pages (GitHub Pages)
	scripts/publicar.sh build/site

test:  ## testes Python (sem Airflow, sem Postgres: os que precisam deles são pulados)
	python -m pytest

lint:
	ruff check . && ruff format --check .
