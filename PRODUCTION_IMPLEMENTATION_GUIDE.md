# 🚀 Guia Completo de Implementação em Produção

## GitHub + AWS MWAA + DBT Core

Este guia te mostra como implementar um pipeline de dados completo em produção usando GitHub para versionamento, AWS MWAA para orquestração e DBT Core para transformações.

## 📋 Visão Geral da Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│   GitHub Actions│───▶│   S3 Bucket     │
│                 │    │   (CI/CD)       │    │   (MWAA)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Snowflake     │◀───│   DBT Core      │◀───│   AWS MWAA      │
│   (Data Lake)   │    │   (Transform)   │    │   (Orchestrate) │
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
- Upload para S3 bucket do MWAA
- MWAA detecta novos DAGs

### 4. **Execução no MWAA**
- Scheduler executa DAGs conforme cron
- Tasks executam comandos DBT
- DBT conecta no Snowflake e executa SQL
- Logs são salvos no CloudWatch

## 🛠️ Implementação Passo a Passo

### Passo 1: Configurar GitHub Repository

#### 1.1 Estrutura do Repositório
```
your-data-pipeline/
├── .github/workflows/          # CI/CD pipelines
│   └── deploy-mwaa.yml
├── airflow-mwaa/              # Código do Airflow
│   ├── dags/                  # DAGs
│   ├── requirements/          # Dependências Python
│   └── plugins/               # Plugins customizados
├── my_dbt_project/            # Projeto DBT
│   ├── models/                # Modelos DBT
│   ├── tests/                 # Testes DBT
│   ├── macros/                # Macros DBT
│   └── dbt_project.yml        # Configuração DBT
├── .dbt/                      # Profiles DBT
│   └── profiles.yml           # Configuração de conexões
├── scripts/                   # Scripts utilitários
└── docs/                      # Documentação
```

#### 1.2 Configurar Secrets no GitHub
Vá em **Settings** → **Secrets and variables** → **Actions** e adicione:

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
SNOWFLAKE_ACCOUNT=your_account.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
```

### Passo 2: Configurar AWS MWAA

#### 2.1 Criar S3 Bucket
```bash
# Criar bucket
aws s3 mb s3://lpsdata-airflow-1

# Criar estrutura de diretórios
aws s3api put-object --bucket lpsdata-airflow-1 --key dags/
aws s3api put-object --bucket lpsdata-airflow-1 --key plugins/
aws s3api put-object --bucket lpsdata-airflow-1 --key requirements/
aws s3api put-object --bucket lpsdata-airflow-1 --key dbt_project/
aws s3api put-object --bucket lpsdata-airflow-1 --key .dbt/
```

#### 2.2 Configurar MWAA Environment
No console AWS MWAA:

1. **Environment Name**: `lpsdata-mwaa-prod`
2. **Airflow Version**: `2.8.1`
3. **Python Version**: `3.11`
4. **Requirements File**: `requirements/requirements.txt`
5. **DAGs Folder**: `dags/`
6. **Plugins Folder**: `plugins/`

#### 2.3 Configurar VPC e Security Groups
- **VPC**: Use VPC existente ou crie nova
- **Subnets**: Pelo menos 2 subnets privadas
- **Security Groups**: Permitir HTTPS (443) e SSH (22)

### Passo 3: Configurar DBT

#### 3.1 Estrutura do Projeto DBT
```yaml
# my_dbt_project/dbt_project.yml
name: 'lpsdata_pipeline'
version: '1.0.0'
config-version: 2

profile: 'lpsdata'

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  lpsdata_pipeline:
    staging:
      +materialized: view
    marts:
      +materialized: table
```

#### 3.2 Configurar Profiles
```yaml
# .dbt/profiles.yml
lpsdata:
  target: prod
  outputs:
    prod:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      warehouse: "{{ env_var('SNOWFLAKE_WAREHOUSE') }}"
      database: "{{ env_var('SNOWFLAKE_DATABASE') }}"
      schema: "{{ env_var('SNOWFLAKE_SCHEMA') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE', 'ACCOUNTADMIN') }}"
      threads: 4
      client_session_keep_alive: False
      query_tag: "dbt_mwaa_production"
```

### Passo 4: Configurar CI/CD

#### 4.1 GitHub Actions Workflow
O arquivo `.github/workflows/deploy-mwaa.yml` já foi criado e inclui:

- **Validação**: Testa DAGs e DBT
- **Deploy**: Upload para S3
- **Integração**: Atualiza MWAA
- **Testes**: Valida deployment

#### 4.2 Configurar Branch Protection
1. Vá em **Settings** → **Branches**
2. Adicione regra para `main`:
   - Require pull request reviews
   - Require status checks to pass
   - Require branches to be up to date

### Passo 5: Configurar Monitoramento

#### 5.1 CloudWatch Alarms
```bash
# Alarm para falhas de DAG
aws cloudwatch put-metric-alarm \
  --alarm-name "MWAA-DAG-Failures" \
  --alarm-description "Alarm when DAGs fail" \
  --metric-name "DAGProcessingTime" \
  --namespace "AWS/MWAA" \
  --statistic "Average" \
  --period 300 \
  --threshold 1 \
  --comparison-operator "GreaterThanThreshold"
```

#### 5.2 SNS Notifications
```bash
# Criar tópico SNS
aws sns create-topic --name "mwaa-alerts"

# Criar subscription
aws sns subscribe \
  --topic-arn "arn:aws:sns:us-east-1:123456789012:mwaa-alerts" \
  --protocol "email" \
  --notification-endpoint "your-email@example.com"
```

## 🔧 Como Funciona na Prática

### Cenário: Pipeline Diário de Dados

#### 1. **Desenvolvimento**
```bash
# Desenvolver novo modelo DBT
cd my_dbt_project/models/marts/
# Criar arquivo user_analytics.sql
# Fazer commit e push
```

#### 2. **CI/CD**
- GitHub Actions detecta mudanças
- Valida sintaxe do DBT
- Testa conectividade
- Faz deploy para S3

#### 3. **Execução no MWAA**
```python
# DAG executa automaticamente às 6h UTC
@task
def run_dbt_build():
    # Executa: dbt build --target prod
    # Conecta no Snowflake
    # Executa SQL dos modelos
    # Salva resultados
```

#### 4. **Monitoramento**
- Logs no CloudWatch
- Métricas de performance
- Alertas por email
- Dashboard no Airflow UI

## 📊 Exemplo de Pipeline Completo

### DAG de Produção
```python
# airflow-mwaa/dags/daily_data_pipeline.py
with DAG(
    dag_id="daily_data_pipeline",
    schedule="0 6 * * *",  # Diário às 6h UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["production", "daily"],
) as dag:

    # Task 1: Validar ambiente
    validate = validate_environment()

    # Task 2: Executar DBT
    dbt_build = run_dbt_build()

    # Task 3: Enviar notificação
    notify = send_success_notification()

    validate >> dbt_build >> notify
```

### Modelo DBT
```sql
-- my_dbt_project/models/marts/user_analytics.sql
{{ config(materialized='table') }}

with user_events as (
    select * from {{ ref('staging_user_events') }}
),

user_metrics as (
    select
        user_id,
        count(*) as total_events,
        count(distinct event_date) as active_days,
        max(event_date) as last_activity
    from user_events
    group by user_id
)

select * from user_metrics
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. **DAGs não aparecem no MWAA**
```bash
# Verificar S3
aws s3 ls s3://lpsdata-airflow-1/dags/

# Verificar logs do MWAA
aws logs describe-log-groups --log-group-name-prefix "/aws/mwaa"
```

#### 2. **Erro de conectividade DBT**
```bash
# Verificar profiles
dbt debug --profiles-dir .dbt

# Testar conexão
dbt run --profiles-dir .dbt --target prod
```

#### 3. **Falha no CI/CD**
```bash
# Verificar logs do GitHub Actions
# Verificar secrets configurados
# Verificar permissões AWS
```

## 📈 Otimizações de Produção

### 1. **Performance**
- Use `dbt build` em vez de `dbt run` + `dbt test`
- Configure materializações apropriadas
- Use incremental models para dados grandes

### 2. **Custos**
- Configure schedule otimizado
- Use instâncias menores para desenvolvimento
- Monitore uso de recursos

### 3. **Segurança**
- Use Secrets Manager para credenciais
- Configure IAM roles com menor privilégio
- Habilite logging e auditoria

## 🎯 Próximos Passos

1. **Implementar**: Seguir este guia passo a passo
2. **Testar**: Executar pipeline de teste
3. **Monitorar**: Configurar alertas e dashboards
4. **Otimizar**: Ajustar baseado no uso real
5. **Escalar**: Adicionar mais pipelines conforme necessário

## 📞 Suporte

Se tiver dúvidas ou problemas:
1. Verifique os logs no CloudWatch
2. Consulte a documentação do MWAA
3. Teste localmente primeiro
4. Use o ambiente de desenvolvimento para debugging

---

**🎉 Parabéns!** Você agora tem um pipeline de dados completo em produção usando as melhores práticas da indústria!
