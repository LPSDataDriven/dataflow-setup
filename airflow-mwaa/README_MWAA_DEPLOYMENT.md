# Guia de Deployment para AWS MWAA

Este guia te ajudará a integrar seu projeto com o AWS MWAA (Managed Workflows for Apache Airflow).

## 📋 Pré-requisitos

### 1. Configuração na AWS (já feita por você)
- ✅ Amazon MWAA Environment criado
- ✅ CloudFormation/Stacks configurados
- ✅ S3 bucket para código do Airflow
- ✅ VPC e subnets configuradas
- ✅ Security Groups configurados

### 2. Estrutura de Arquivos Necessária

```
airflow-mwaa/
├── dags/                          # DAGs do Airflow
│   ├── dbt_main_pipeline_mwaa.py
│   └── full_main_pipeline_mwaa.py
├── plugins/                       # Plugins customizados (opcional)
├── requirements/                  # Dependências Python
│   └── requirements.txt
└── README_MWAA_DEPLOYMENT.md     # Este arquivo
```

## 🚀 Processo de Deployment

### Passo 1: Preparar o S3 Bucket

1. **Criar estrutura no S3:**
```bash
aws s3 mb s3://lpsdata-airflow-1

# Criar estrutura de diretórios
aws s3api put-object --bucket lpsdata-airflow-1 --key dags/
aws s3api put-object --bucket lpsdata-airflow-1 --key plugins/
aws s3api put-object --bucket lpsdata-airflow-1 --key requirements/
```

### Passo 2: Upload dos Arquivos

```bash
# Upload dos DAGs
aws s3 sync ./dags/ s3://lpsdata-airflow-1/dags/

# Upload dos requirements
aws s3 cp ./requirements/requirements.txt s3://lpsdata-airflow-1/requirements/requirements.txt

# Upload dos plugins (se houver)
aws s3 sync ./plugins/ s3://lpsdata-airflow-1/plugins/
```

### Passo 3: Configurar Variáveis do Airflow

No console do MWAA, vá para **Airflow UI** e configure as seguintes variáveis:

#### Variáveis Obrigatórias:
```json
{
  "dbt_project_dir": "/opt/airflow/dbt_project",
  "dbt_profiles_dir": "/opt/airflow/.dbt",
  "dbt_target": "dev"
}
```

#### Como configurar:
1. Acesse o Airflow UI do MWAA
2. Vá em **Admin** → **Variables**
3. Clique em **+** para adicionar nova variável
4. Adicione cada variável com sua chave e valor

### Passo 4: Configurar Secrets (Recomendado)

Para credenciais sensíveis, use AWS Secrets Manager:

#### 1. Criar secret no AWS Secrets Manager:
```bash
aws secretsmanager create-secret \
    --name "airflow/dbt/snowflake" \
    --description "Snowflake credentials for DBT" \
    --secret-string '{
        "account": "your_account",
        "user": "your_user",
        "password": "your_password",
        "warehouse": "your_warehouse",
        "database": "your_database",
        "schema": "your_schema"
    }'
```

#### 2. Atualizar DAGs para usar secrets:
```python
from airflow.providers.amazon.aws.secrets.secrets_manager import SecretsManagerBackend

# No seu DAG
secrets_backend = SecretsManagerBackend()
snowflake_creds = secrets_backend.get_conn_uri("airflow/dbt/snowflake")
```

## 🔧 Configurações Específicas do MWAA

### 1. Configuração do Environment

No console do MWAA, certifique-se de que:

- **Airflow Version**: 2.8.1 ou superior
- **Python Version**: 3.11
- **Requirements File**: `requirements/requirements.txt`
- **DAGs Folder**: `dags/`
- **Plugins Folder**: `plugins/`

### 2. Configuração de Rede

- **VPC**: Use a mesma VPC onde está seu MWAA
- **Subnets**: Pelo menos 2 subnets privadas em AZs diferentes
- **Security Groups**: Permitir tráfego HTTPS (443) e SSH (22) se necessário

### 3. Configuração de IAM

O MWAA precisa das seguintes permissões:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::lpsdata-airflow-1",
                "arn:aws:s3:::lpsdata-airflow-1/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:*:*:secret:airflow/*"
            ]
        }
    ]
}
```

## 📁 Estrutura de Arquivos no S3

```
lpsdata-airflow-1/
├── dags/
│   ├── dbt_main_pipeline_mwaa.py
│   └── full_main_pipeline_mwaa.py
├── plugins/
│   └── (plugins customizados se houver)
├── requirements/
│   └── requirements.txt
└── (outros arquivos se necessário)
```

## 🔄 Processo de Atualização

### Para atualizar DAGs:
```bash
# Upload apenas dos DAGs modificados
aws s3 sync ./dags/ s3://lpsdata-airflow-1/dags/ --delete
```

### Para atualizar requirements:
```bash
# Upload do requirements.txt
aws s3 cp ./requirements/requirements.txt s3://lpsdata-airflow-1/requirements/requirements.txt
```

**⚠️ Importante**: Após atualizar requirements, o MWAA precisa ser reiniciado para instalar as novas dependências.

## 🐛 Troubleshooting

### Problemas Comuns:

1. **DAGs não aparecem no UI:**
   - Verifique se os arquivos estão no S3
   - Verifique se não há erros de sintaxe nos DAGs
   - Verifique os logs do MWAA

2. **Erro de dependências:**
   - Verifique o requirements.txt
   - Reinicie o environment do MWAA

3. **Erro de conectividade:**
   - Verifique as configurações de VPC
   - Verifique os Security Groups
   - Verifique as rotas de rede

### Logs do MWAA:
- **Task Logs**: Airflow UI → DAG → Task → Logs
- **Scheduler Logs**: CloudWatch Logs → `/aws/mwaa/ENVIRONMENT_NAME/scheduler`
- **Webserver Logs**: CloudWatch Logs → `/aws/mwaa/ENVIRONMENT_NAME/webserver`

## 📊 Monitoramento

### CloudWatch Metrics:
- `SchedulerHeartbeat`
- `DAGProcessingTime`
- `TaskInstanceDuration`

### Alertas Recomendados:
- Falha de DAGs críticos
- Tempo de execução excessivo
- Falhas de conectividade

## 💰 Otimização de Custos

1. **Use schedule apropriado**: Evite execuções desnecessárias
2. **Configure auto-scaling**: Para workloads variáveis
3. **Use instâncias menores**: Para desenvolvimento
4. **Monitore logs**: Para identificar problemas de performance

## 🔐 Segurança

1. **Use Secrets Manager**: Para credenciais sensíveis
2. **Configure VPC**: Para isolamento de rede
3. **Use IAM roles**: Com princípio de menor privilégio
4. **Habilite logging**: Para auditoria

## 📞 Próximos Passos

1. **Teste local**: Execute os DAGs localmente primeiro
2. **Deploy gradual**: Comece com um DAG simples
3. **Monitore**: Acompanhe logs e métricas
4. **Otimize**: Ajuste configurações baseado no uso

---

**Nota**: Este guia assume que você já tem o MWAA Environment configurado. Se precisar de ajuda com a configuração inicial, consulte a documentação oficial da AWS.
