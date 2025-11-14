#!/bin/bash
set -e

# Inicializar banco de dados (não falha se já estiver inicializado)
airflow db init || true

# Criar usuário admin (não falha se já existir)
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin || true
