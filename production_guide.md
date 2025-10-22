# 🚀 Guia Completo de Implementação em Produção

## GitHub + Airflow Local + DBT Core

Este guia te mostra como implementar um pipeline de dados completo em produção usando GitHub para versionamento, Airflow local com Docker para orquestração e DBT Core para transformações.

## 📋 Visão Geral da Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│   GitHub Actions│───▶│   S3 Bucket     │
│                 │    │   (CI/CD)       │    │   (Artifacts)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Snowflake     │◀───│   DBT Core      │◀───│   Airflow Local │
│   (Data Lake)   │    │   (Transform)   │    │   (Docker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔄 Fluxo Completo de Produção

### 1. **Desenvolvimento Local**
```bash
# Desenvolver DAGs e modelos DBT
git checkout -b feature/new-pipeline
# ... fazer mudanças ...
git add .
git commit -m "Add new DBT pipeline"
git push origin feature/new-pipeline
```

### 2. **Pull Request**
- GitHub Actions executa validações
- Testa DAGs e modelos DBT
- Valida sintaxe e conectividade

### 3. **Merge para Main**
- GitHub Actions faz deploy automático
- Upload para S3 bucket (artifacts)
- Airflow local detecta novos DAGs

### 4. **Execução no Airflow Local**
- Scheduler executa DAGs conforme cron
- Tasks executam comandos DBT
- DBT conecta no Snowflake e executa SQL
- Logs são salvos localmente e no S3

## 🛠️ Implementação Passo a Passo

### Passo 1: Configurar GitHub Actions

#### 1.1 Criar Secrets no GitHub
No seu repositório GitHub, vá para **Settings > Secrets and variables > Actions** e adicione:

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_DATABASE_DEV=your-dev-database
SNOWFLAKE_DATABASE_PROD=your-prod-database
SNOWFLAKE_SCHEMA=your-schema
SNOWFLAKE_ROLE=your-role
```

#### 1.2 Configurar Workflow
O arquivo `.github/workflows/test-cicd.yml` já foi criado e inclui:
- **Validação**: Testa secrets e conectividade
- **Testes**: Valida DAGs e modelos DBT
- **Deploy**: Upload para S3

### Passo 2: Configurar Airflow Local

#### 2.1 Docker Compose
Crie um `docker-compose.yml` na raiz do projeto:

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    volumes:
      - postgres_db_volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5
    restart: always

  airflow-webserver:
    build: ./airflow-local
    command: webserver
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      postgres:
        condition: service_healthy

  airflow-scheduler:
    build: ./airflow-local
    command: scheduler
    healthcheck:
      test: ["CMD-SHELL", 'airflow jobs check --job-type SchedulerJob --hostname "$${HOSTNAME}"']
      interval: 10s
      timeout: 10s
      retries: 5
    restart: always
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  postgres_db_volume:
```

#### 2.2 Dockerfile para Airflow
Crie `airflow-local/Dockerfile`:

```dockerfile
FROM apache/airflow:2.8.1-python3.11

USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY requirements/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY dags/ /opt/airflow/dags/
COPY .dbt/ /opt/airflow/.dbt/
COPY dbt/ /opt/airflow/dbt/
```

### Passo 3: Configurar DBT para Produção

#### 3.1 Profiles para Produção
Atualize `.dbt/profiles.yml`:

```yaml
dataflow_setup:
  target: prod
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE_DEV') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      schema: "{{ env_var('SNOWFLAKE_SCHEMA') }}"
      authenticator: password
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      client_session_keep_alive: true
      query_tag: "dbt_local_development"

    prod:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE_PROD') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      schema: "{{ env_var('SNOWFLAKE_SCHEMA') }}"
      authenticator: password
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      client_session_keep_alive: true
      query_tag: "dbt_local_production"
```

### Passo 4: Configurar Monitoramento

#### 4.1 CloudWatch Alarms (Opcional)
Para monitorar execuções via S3:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "DBT-Pipeline-Failures" \
  --alarm-description "Alert when DBT pipeline fails" \
  --metric-name "FailedExecutions" \
  --namespace "Custom/DBT" \
  --statistic "Sum" \
  --period 300 \
  --threshold 1 \
  --comparison-operator "GreaterThanOrEqualToThreshold" \
  --evaluation-periods 1
```

#### 4.2 Notificações SNS
```bash
aws sns create-topic --name "dbt-alerts"

aws sns subscribe \
  --topic-arn "arn:aws:sns:us-east-1:123456789012:dbt-alerts" \
  --protocol "email" \
  --notification-endpoint "your-email@example.com"
```

## 🚀 Executando o Pipeline

### 1. **Setup Inicial**
```bash
# Clone o repositório
git clone <your-repo>
cd dataflow-setup

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Inicie o Airflow
docker-compose up -d

# Acesse o Airflow UI
open http://localhost:8080
```

### 2. **Execução Manual**
```bash
# Execute DBT localmente
dbt build --target prod

# Ou via Airflow UI
# 1. Acesse http://localhost:8080
# 2. Encontre seu DAG
# 3. Clique em "Trigger DAG"
```

### 3. **Execução Automática**
Os DAGs executam automaticamente conforme o schedule definido.

## 📊 Monitoramento e Logs

### 1. **Logs do Airflow**
- **Web UI**: http://localhost:8080
- **Logs locais**: `./logs/airflow/`
- **S3**: Logs são enviados para S3 automaticamente

### 2. **Logs do DBT**
- **Local**: `./logs/dbt/`
- **S3**: `s3://your-bucket/dbt-logs/`

### 3. **Métricas**
- **Airflow**: Métricas disponíveis no UI
- **DBT**: Logs detalhados de execução
- **Snowflake**: Query history e performance

## 🔧 Troubleshooting

### 1. **DAGs não aparecem no Airflow**
```bash
# Verificar logs do scheduler
docker-compose logs airflow-scheduler

# Verificar sintaxe dos DAGs
python -m py_compile airflow-local/dags/*.py
```

### 2. **DBT não conecta no Snowflake**
```bash
# Testar conexão
dbt debug --target prod

# Verificar variáveis de ambiente
echo $SNOWFLAKE_ACCOUNT
```

### 3. **Erro de permissões AWS**
```bash
# Verificar credenciais
aws sts get-caller-identity

# Testar acesso ao S3
aws s3 ls s3://your-bucket
```

## 💰 Estimativa de Custos

### **Execução Local (Docker):**
- **Custo**: $0 (apenas recursos locais)
- **Vantagens**: Controle total, sem custos de cloud
- **Desvantagens**: Requer máquina sempre ligada

### **Para Produção Escalável:**
- **AWS ECS/EKS**: ~$50-200/mês (dependendo do uso)
- **Google Cloud Run**: ~$30-100/mês
- **Azure Container Instances**: ~$40-150/mês

## 🎯 Próximos Passos

1. **Configurar** Airflow local com Docker
2. **Testar** pipeline completo
3. **Implementar** monitoramento
4. **Documentar** processos
5. **Treinar** equipe

---

**Nota**: Este guia foca em execução local para reduzir custos. Para ambientes de produção com alta disponibilidade, considere migrar para soluções gerenciadas como ECS, EKS ou outras plataformas de container.
