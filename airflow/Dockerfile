FROM apache/airflow:2.9.3-python3.12

# Instalar dependências do sistema e UV
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    cp /root/.local/bin/uv /usr/local/bin/uv && \
    chmod +x /usr/local/bin/uv

# Copiar arquivos do projeto para instalar dependências
# Nota: o contexto do build é a raiz do projeto (via docker-compose)
WORKDIR /tmp/build

# Copiar pyproject.toml e uv.lock (se existir) da raiz do projeto
COPY --chown=root:root pyproject.toml uv.lock* ./

# Instalar dependências usando UV (apenas de produção, sem dev)
# Instalar como root para ter permissão de escrever em /usr/local
RUN uv pip install --system -e .

# Voltar para usuário airflow
USER airflow

# Voltar para /opt/airflow
WORKDIR /opt/airflow

# Configurar variáveis de ambiente do dbt
ENV DBT_PROFILES_DIR=/opt/airflow/.dbt \
    PYTHONPATH=/opt/airflow:/opt/airflow/dataflow

# Copiar DAGs e outros arquivos (opcional - normalmente via volume mount)
# COPY --chown=airflow:root airflow/dags /opt/airflow/dags
