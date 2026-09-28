-- O Postgres do compose guarda duas coisas: os metadados do Airflow (banco
-- "airflow", criado pela imagem) e o warehouse, criado aqui.
create user warehouse with password 'warehouse';
create database warehouse owner warehouse;
