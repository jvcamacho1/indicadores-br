# Backlog de estudo: dbt e Airflow

Melhorias para o `indicadores-br`, pensadas para aprender dbt e Airflow
implementando. Cada tarefa traz só o **conceito** (termo para pesquisar), o
**objetivo** e o **critério de aceite**. O caminho até lá é seu.

## Como usar

**Status.** Vocabulário fechado: `TODO`, `FEITO`, `PARCIAL`, `BLOQUEADO`.
Ao concluir, troque o status e ponha ✅ ao lado do ID, na primeira coluna.

**Escalas.** Prioridade `P0` a `P3`. Esforço `S` (uma tarde), `M` (alguns
dias), `L` (uma semana ou mais).

**IDs não se reaproveitam.** Tarefa abandonada fica `BLOQUEADO` com o motivo
na seção dela, e o ID não volta a ser usado.

**Ordem sugerida.** Os níveis são uma trilha: o nível 1 faz você rodar e
entender o que existe; o 2 cobre o que se usa no dia a dia; o 3 é
arquitetura. Dentro de um nível, a ordem é livre.

**Uma tarefa, um PR.** Cada tarefa termina com o CI verde e, quando mudar o
que o site mostra, com o painel republicado (`make publicar` ou o workflow
`publicar.yml`).

`tests/test_backlog.py` confere estas convenções: seção para todo ID da
tabela, status e escalas dentro do vocabulário, nenhum ID repetido.

## Tarefas

| ID | Tarefa | Área | Nível | Prioridade | Esforço | Status |
|---|---|---|---|---|---|---|
| IND-001 | Rodar o pipeline completo localmente | Ambos | 1 | P0 | S | TODO |
| IND-002 | Documentar todas as colunas das fontes e dos marts | dbt | 1 | P1 | S | TODO |
| IND-003 | Teste unitário das regras de agregação mensal | dbt | 1 | P1 | S | TODO |
| IND-004 | Connection do Airflow para o warehouse | Airflow | 1 | P1 | M | TODO |
| IND-005 | Pool para as chamadas às APIs públicas | Airflow | 1 | P2 | S | TODO |
| IND-010 | Pacotes do dbt (`dbt_utils`) | dbt | 2 | P1 | S | TODO |
| IND-011 | Novo indicador só pelo catálogo, com pivot gerado por Jinja | dbt | 2 | P1 | M | TODO |
| IND-012 | Macro genérica de acumulado em 12 meses | dbt | 2 | P2 | S | TODO |
| IND-013 | Exposure do painel na linhagem | dbt | 2 | P2 | S | TODO |
| IND-014 | Severidade de testes e `store_failures` | dbt | 2 | P2 | S | TODO |
| IND-015 | Params no DAG e disparo com configuração | Airflow | 2 | P1 | S | TODO |
| IND-016 | Pular o dbt quando nada mudou | Airflow | 2 | P1 | M | TODO |
| IND-017 | Callback de falha | Airflow | 2 | P2 | S | TODO |
| IND-018 | Lint do SQL com sqlfluff no CI | dbt | 2 | P3 | S | TODO |
| IND-020 | Snapshot das revisões de valores | dbt | 3 | P1 | M | TODO |
| IND-021 | Contratos de modelo nos marts | dbt | 3 | P2 | S | TODO |
| IND-022 | Incremental com `merge` e janela configurável | dbt | 3 | P2 | M | TODO |
| IND-023 | Assets: extração e transformação em DAGs separados | Airflow | 3 | P1 | M | TODO |
| IND-024 | dbt como TaskGroup com Astronomer Cosmos | Ambos | 3 | P2 | M | TODO |
| IND-025 | Hook e operador próprios para o SGS | Airflow | 3 | P2 | L | TODO |
| IND-026 | Sensor deferrable para a publicação do IPCA | Airflow | 3 | P3 | M | TODO |
| IND-027 | Teste do DAG ponta a ponta no CI | Ambos | 3 | P2 | M | TODO |
| IND-028 | Slim CI do dbt com `state:modified` e `--defer` | dbt | 3 | P3 | L | TODO |
| IND-029 | Página de qualidade de dados no painel | Ambos | 3 | P3 | M | TODO |

## Nível 1: rodar e entender

### IND-001 — Rodar o pipeline completo localmente

**Conceito:** Docker Compose, Airflow standalone, backfill.

**Objetivo:** subir o ambiente da sua máquina e executar o caminho inteiro
com os dados reais: backfill desde 2015, dbt, docs e site.

**Critério de aceite:**
- `make up`, `make backfill`, `make dbt` e `make site` rodam sem erro.
- O Grid do DAG `indicadores_br` mostra as execuções mensais desde 2015-01,
  com `dbt_freshness_e_build` pulada em todas, menos na mais recente.
- O README ganha uma screenshot desse Grid e o tempo total do backfill.
- Todo ajuste que o `docker-compose.yml` ou o Makefile precisarem para rodar
  entra no mesmo PR.

### IND-002 — Documentar todas as colunas das fontes e dos marts

**Conceito:** dbt docs, `description`, doc blocks (`{% docs %}`).

**Objetivo:** que o dbt docs publicado explique cada coluna, das fontes em
`raw` até `mart_painel_mensal`, sem precisar ler o SQL.

**Critério de aceite:**
- Toda coluna de `_sources.yml` e de `_marts.yml` tem `description`.
- As descrições longas (regra de agregação, equação de Fisher, trimestre
  móvel) moram em doc blocks num arquivo `.md` e são referenciadas com
  `doc()`.
- Em `/dbt-docs/`, nenhuma coluna dos marts aparece sem descrição.

### IND-003 — Teste unitário das regras de agregação mensal

**Conceito:** dbt unit tests.

**Objetivo:** provar com dados de entrada controlados que
`int_indicador_mensal` aplica as três regras do catálogo: `media` para o
dólar, `ultimo` para a Selic e `valor` para as séries mensais.

**Critério de aceite:**
- Um unit test por regra, com pelo menos duas observações no mesmo mês nos
  casos `media` e `ultimo`.
- Mudar a regra do dólar para `ultimo` no seed faz um desses testes falhar.
- `dbt build` passa no CI.

### IND-004 — Connection do Airflow para o warehouse

**Conceito:** Airflow Connections, `PostgresHook`,
`apache-airflow-providers-postgres`.

**Objetivo:** a carga dentro do Airflow pega as credenciais de uma
Connection `warehouse`, e não mais de variáveis de ambiente soltas.

**Critério de aceite:**
- Existe a Connection `warehouse`, definida no `docker-compose.yml` (sem
  segredo novo no Git) e visível em *Admin → Connections*.
- As tasks do DAG usam a Connection; a CLI (`python -m indicadores`) e o CI
  continuam funcionando sem Airflow.
- Os testes de `indicadores/carga.py` continuam passando.

### IND-005 — Pool para as chamadas às APIs públicas

**Conceito:** Airflow Pools.

**Objetivo:** limitar quantas tasks falam com as APIs do governo ao mesmo
tempo, inclusive durante o backfill com várias execuções em paralelo.

**Critério de aceite:**
- Existe um pool `apis_governo` com 2 slots, criado de forma reprodutível
  (comando no Makefile ou na inicialização, e não clicando na UI).
- As tasks `extrair_e_carregar` usam o pool.
- Durante o backfill, *Admin → Pools* nunca mostra mais de 2 slots ocupados.

## Nível 2: recursos do dia a dia

### IND-010 — Pacotes do dbt (`dbt_utils`)

**Conceito:** `packages.yml`, `dbt deps`, dbt_utils.

**Objetivo:** usar um pacote da comunidade no lugar de lógica escrita à mão
onde fizer sentido.

**Critério de aceite:**
- `dbt_utils` declarado em `packages.yml`, com versão fixada.
- `fct_indicador_mensal` testa a unicidade de `(indicador_id, mes)` com
  `unique_combination_of_columns`.
- `dbt deps` roda no CI, no `publicar.yml` e na imagem ou no DAG do Airflow,
  e `dbt_packages/` continua fora do Git.

### IND-011 — Novo indicador só pelo catálogo, com pivot gerado por Jinja

**Conceito:** Jinja no dbt, `run_query`, macros que geram SQL.

**Objetivo:** hoje, um indicador novo exige editar o `mart_painel_mensal` à
mão (uma linha `max(case when ...)` por indicador). A meta é que uma linha
no seed baste.

**Critério de aceite:**
- O IGP-M (SGS 189, variação mensal) entra no pipeline apenas com uma linha
  nova em `dbt/seeds/indicadores.csv`.
- O `mart_painel_mensal` gera as colunas de indicador a partir do catálogo;
  não sobra nenhum `indicador_id` escrito no SQL do pivot.
- As colunas de hoje continuam com os mesmos nomes (o painel não quebra), e
  `igpm_mensal` aparece no mart.
- A API falsa (`tests/fake_api.py`) serve a série 189, e o CI passa.

### IND-012 — Macro genérica de acumulado em 12 meses

**Conceito:** macros do dbt, window functions.

**Objetivo:** a conta de acumulado em 12 meses que hoje existe só para o IPCA
(`exp(sum(ln(...)))` no `mart_painel_mensal`) vira uma macro reaproveitável.

**Critério de aceite:**
- Macro `acumulado_12m(coluna)` em `dbt/macros/`, documentada.
- O mart usa a macro para `ipca_12m_calculado` e para o novo `igpm_12m`
  (depende da IND-011).
- Um unit test cobre a macro com 12 meses conhecidos, e o teste de
  reconciliação do IPCA continua passando.

### IND-013 — Exposure do painel na linhagem

**Conceito:** dbt exposures.

**Objetivo:** mostrar no dbt docs quem consome os marts: o painel publicado.

**Critério de aceite:**
- Uma exposure do tipo `dashboard`, com URL, dono e dependência de
  `mart_painel_mensal` e `dim_indicador`.
- No grafo de linhagem do `/dbt-docs/`, a exposure aparece depois dos marts.

### IND-014 — Severidade de testes e `store_failures`

**Conceito:** `severity`, `warn_if`, `error_if`, `store_failures`.

**Objetivo:** separar "avisar" de "parar o pipeline" e conseguir inspecionar
as linhas que reprovaram um teste.

**Critério de aceite:**
- O teste de reconciliação do IPCA avisa com 1 ou 2 meses fora da tolerância
  e só falha a partir de 3.
- Os testes de faixa (`valor_entre`) guardam as falhas numa tabela
  consultável.
- Registrar no PR o experimento: forçar um valor fora da faixa no `raw`,
  rodar `dbt build`, consultar a tabela de falhas e desfazer.

### IND-015 — Params no DAG e disparo com configuração

**Conceito:** DAG `params`, trigger com configuração.

**Objetivo:** reprocessar um indicador ou uma janela maior sem editar
código.

**Critério de aceite:**
- O DAG aceita `params` para a lista de indicadores (padrão: todos) e para
  os meses de recuo (padrão: 3).
- Disparar pela UI com `{"indicadores": ["ipca_mensal"], "meses_para_tras": 24}`
  gera uma única task mapeada, e `raw.cargas` registra a janela de 24 meses.
- As execuções agendadas continuam usando os padrões.

### IND-016 — Pular o dbt quando nada mudou

**Conceito:** XCom, `ShortCircuitOperator` (ou `@task.short_circuit`).

**Objetivo:** cada `extrair_e_carregar` já devolve `{"recebidas", "alteradas"}`.
Se nenhuma carga alterou linhas, dbt, docs e site não precisam rodar.

**Critério de aceite:**
- Uma task soma as `alteradas` de todas as cargas mapeadas e pula o resto
  do DAG quando a soma é zero.
- Rodar a mesma execução duas vezes seguidas: a primeira roda o dbt, a
  segunda aparece com o dbt como `skipped` no Grid.
- Uma execução manual com um param `forcar=true` roda o dbt mesmo sem
  mudança.

### IND-017 — Callback de falha

**Conceito:** `on_failure_callback`, contexto da task.

**Objetivo:** descobrir que o pipeline falhou sem precisar abrir a UI.

**Critério de aceite:**
- Toda task do DAG tem um callback de falha que registra DAG, task, data
  lógica, tentativa e link do log (num arquivo, num webhook ou num e-mail,
  à sua escolha).
- Registrar no PR a falha provocada: apontar `BCB_BASE_URL` para um
  endereço inválido e mostrar o registro que o callback produziu depois das
  retentativas.

### IND-018 — Lint do SQL com sqlfluff no CI

**Conceito:** sqlfluff, templater `dbt`.

**Objetivo:** estilo de SQL consistente e verificado automaticamente, como
o ruff já faz com o Python.

**Critério de aceite:**
- `.sqlfluff` configurado para Postgres com o templater do dbt.
- Um job novo no `ci.yml` roda `sqlfluff lint dbt/models`.
- Todos os modelos atuais passam, corrigidos ou com as regras
  desligadas explicitamente e o motivo em comentário.

## Nível 3: arquitetura

### IND-020 — Snapshot das revisões de valores

**Conceito:** dbt snapshots (SCD tipo 2), estratégia `check`.

**Objetivo:** hoje, quando o BC ou o IBGE revisam um número, o upsert
sobrescreve o valor antigo e a história se perde. A meta é guardar cada
versão.

**Critério de aceite:**
- Um snapshot de `raw.observacoes` com chave `(indicador_id, data)`, que
  detecta mudança em `valor`.
- Um mart `mart_revisoes` com, por indicador: quantas observações já foram
  revisadas, a maior revisão absoluta e a data da última revisão.
- Registrar no PR o experimento: alterar um valor no `raw`, rodar
  `dbt snapshot` e mostrar as duas versões com `dbt_valid_from` e
  `dbt_valid_to`.

### IND-021 — Contratos de modelo nos marts

**Conceito:** model contracts (`contract: enforced`), constraints.

**Objetivo:** o formato dos marts vira uma promessa: mudar tipo ou nome de
coluna quebra o build, e não o painel em produção.

**Critério de aceite:**
- Os quatro marts têm contrato imposto, com `data_type` em todas as colunas.
- `fct_indicador_mensal` e `dim_indicador` declaram suas chaves como
  `constraints`.
- Registrar no PR a falha provocada: renomear uma coluna do mart e mostrar o
  `dbt build` falhando por causa do contrato.

### IND-022 — Incremental com `merge` e janela configurável

**Conceito:** estratégias incrementais (`merge`, `delete+insert`),
`is_incremental()`, `var()`.

**Objetivo:** entender as estratégias incrementais comparando as duas no
mesmo modelo.

**Critério de aceite:**
- `fct_indicador_mensal` passa a usar `merge`.
- Uma `var('meses_reprocessar')` (padrão 0) força reprocessar os últimos N
  meses, além do filtro por `carregado_em`.
- Registrar no PR a diferença de SQL gerado entre as duas estratégias
  (`target/run/...`) e o resultado idêntico de
  `dbt build --full-refresh` contra uma execução incremental.

### IND-023 — Assets: extração e transformação em DAGs separados

**Conceito:** Airflow Assets, agendamento por dados.

**Objetivo:** separar quem produz o dado de quem o consome. A extração
publica um Asset, e a transformação roda quando ele é atualizado, e não num
horário.

**Critério de aceite:**
- DAG `indicadores_extracao` (mensal, com catchup) declara que atualiza um
  Asset do `raw`.
- DAG `indicadores_transformacao`, agendado por esse Asset, roda dbt, docs
  e site.
- O backfill da extração não dispara uma transformação por mês de
  histórico: a escolha fica justificada no PR.
- A view de Assets da UI mostra o vínculo entre os dois DAGs, e os testes de
  DAG cobrem os dois.

### IND-024 — dbt como TaskGroup com Astronomer Cosmos

**Conceito:** astronomer-cosmos, `DbtTaskGroup`.

**Objetivo:** ver cada modelo e cada teste do dbt como uma task do Airflow,
com retry e log próprios, no lugar de um `dbt build` monolítico.

**Critério de aceite:**
- O `BashOperator` `dbt_freshness_e_build` é substituído por um TaskGroup do
  Cosmos que usa o venv do dbt da imagem.
- O Grid mostra uma task por modelo, com os testes do modelo em seguida.
- Uma falha de teste num mart não impede os modelos que não dependem dele.

### IND-025 — Hook e operador próprios para o SGS

**Conceito:** custom hooks, custom operators, templating (`template_fields`).

**Objetivo:** empacotar o acesso ao SGS no padrão do Airflow, reaproveitável
por qualquer DAG.

**Critério de aceite:**
- `SgsHook` com a URL base vinda de uma Connection `bcb_sgs` e o retry
  HTTP de `indicadores/http.py`.
- `SgsToPostgresOperator(codigo, indicador_id, ...)`, com as datas da
  janela como campos templatizáveis.
- Testes unitários do hook e do operador contra a API falsa.
- O DAG usa o operador para as séries do BCB, e o comportamento do pipeline
  não muda.

### IND-026 — Sensor deferrable para a publicação do IPCA

**Conceito:** sensors, `mode="reschedule"`, deferrable operators e
triggers.

**Objetivo:** o IPCA sai por volta do dia 10. Em vez de rodar e não achar o
dado, a transformação espera ele existir.

**Critério de aceite:**
- Um sensor verifica se o IPCA do mês de referência já está no SGS.
- O sensor não ocupa um worker enquanto espera (deferrable ou reschedule),
  com `timeout` e `poke_interval` justificados no PR.
- Quando o dado não sai dentro do prazo, a execução termina num estado claro
  (falha ou skip), e o motivo aparece no log.

### IND-027 — Teste do DAG ponta a ponta no CI

**Conceito:** `dag.test()`, testes de integração.

**Objetivo:** hoje o CI só confere que o DAG importa. A meta é executá-lo de
verdade: extração contra a API falsa, dbt e site.

**Critério de aceite:**
- Um job no `ci.yml` sobe Postgres e a API falsa, instala Airflow e dbt em
  ambientes separados e roda o DAG com `dag.test()`.
- O teste confere o estado final de todas as tasks e que `build/site/data.json`
  existe com `sintetico: true`.
- O job leva menos de 10 minutos.

### IND-028 — Slim CI do dbt com `state:modified` e `--defer`

**Conceito:** dbt state, `manifest.json`, `--select state:modified+`,
`--defer`.

**Objetivo:** num PR, rodar e testar só os modelos que mudaram e os que
dependem deles, aproveitando o resto da última execução de produção.

**Critério de aceite:**
- O `publicar.yml` guarda o `manifest.json` de cada publicação como
  artefato.
- Um job de PR baixa esse manifest e roda
  `dbt build --select state:modified+ --defer --state ...`.
- Um PR que muda só `dim_calendario` executa `dim_calendario` e o que vem
  depois, e não o staging.

### IND-029 — Página de qualidade de dados no painel

**Conceito:** artefatos do dbt (`run_results.json`), observabilidade de dados.

**Objetivo:** mostrar no site a saúde do pipeline, e não só o resultado.

**Critério de aceite:**
- `montar_site` lê o `run_results.json` da última execução e grava um
  `qualidade.json`.
- Uma página ou seção "Qualidade" lista, em PT e EN: testes que passaram e
  falharam, horário da execução, freshness de `raw.cargas` e o último mês
  de cada indicador.
- A página funciona com os dados sintéticos do CI e com os reais.
