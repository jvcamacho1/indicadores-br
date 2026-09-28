FROM apache/airflow:3.3.2-python3.11

# O dbt fica num venv próprio: as dependências dele e as do Airflow brigam.
# A task do DAG chama /home/airflow/dbt-venv/bin/dbt diretamente.
COPY requirements-dbt.txt /tmp/requirements-dbt.txt
RUN python -m venv /home/airflow/dbt-venv \
 && /home/airflow/dbt-venv/bin/pip install --no-cache-dir -r /tmp/requirements-dbt.txt

# Extração: requests e psycopg2 já vêm na imagem, mas a versão fica declarada.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
