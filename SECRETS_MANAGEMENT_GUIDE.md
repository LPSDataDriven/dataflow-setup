# 🔐 Guia Completo de Gerenciamento de Secrets

## 📋 Resumo: O que vai onde

| Ambiente | Onde ficam as credenciais | Como acessar | Quando usar |
|----------|---------------------------|--------------|-------------|
| **Local (Docker)** | `.env` | `os.getenv()` | Desenvolvimento |
| **GitHub Actions** | GitHub Secrets | `${{ secrets.NOME }}` | CI/CD |
| **Produção (ECS/EKS)** | AWS Secrets Manager | `SecretsManagerBackend()` | Produção |
| **Airflow UI** | Airflow Variables | `Variable.get()` | Configurações |

## 🏠 1. Ambiente Local (Docker) - MANTER .env

### ✅ **SIM, mantenha o `.env` para desenvolvimento local!**

```bash
# .env (local)
SNOWFLAKE_ACCOUNT=your_account.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_ROLE=ACCOUNTADMIN
```

### Como usar no código local:
```python
# airflow/dags/local_dag.py
import os
from dotenv import load_dotenv

load_dotenv()  # Carrega o .env

snowflake_account = os.getenv("SNOWFLAKE_ACCOUNT")
snowflake_user = os.getenv("SNOWFLAKE_USER")
```

### Docker Compose (já configurado):
```yaml
# docker-compose.yml
services:
  airflow-webserver:
    volumes:
      - ./.env:/opt/airflow/.env:ro  # ✅ Já está configurado
```

## ☁️ 2. GitHub Actions - GitHub Secrets

### Configurar secrets no GitHub:
1. Vá em **Repository** → **Settings** → **Secrets and variables** → **Actions**
2. Clique em **New repository secret**
3. Adicione cada secret:

```bash
# GitHub Secrets (Repository Settings → Secrets and variables → Actions)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
SNOWFLAKE_ACCOUNT=your_account.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema
```

### Como usar no GitHub Actions:
```yaml
# .github/workflows/deploy.yml
- name: Deploy to S3
  env:
    SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
    SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_USER }}
    SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_PASSWORD }}
  run: |
    # Upload arquivos para S3
    # Criar profiles.yml com as credenciais
```

## 🏢 3. Produção (ECS/EKS) - AWS Secrets Manager

### Criar secret no AWS Secrets Manager:
```bash
# Criar secret
aws secretsmanager create-secret \
    --name "airflow/snowflake/credentials" \
    --description "Snowflake credentials for production" \
    --secret-string '{
        "account": "your_account.snowflakecomputing.com",
        "user": "your_username",
        "password": "your_password",
        "warehouse": "your_warehouse",
        "database": "your_database",
        "schema": "your_schema",
        "role": "ACCOUNTADMIN"
    }'
```

### Como usar em produção:
```python
# airflow-local/dags/production_dag.py
from airflow.providers.amazon.aws.secrets.secrets_manager import SecretsManagerBackend

secrets_backend = SecretsManagerBackend()
snowflake_creds = secrets_backend.get_conn_uri("airflow/snowflake/credentials")
```

## 🎛️ 4. Airflow UI - Airflow Variables

### Configurar variáveis no Airflow UI:
1. Acesse o **Airflow UI** local
2. Vá em **Admin** → **Variables**
3. Clique em **+** para adicionar nova variável
4. Adicione cada variável:

```bash
# Airflow Variables (Admin → Variables)
dbt_project_dir: /opt/airflow/dbt_project
dbt_profiles_dir: /opt/airflow/.dbt
dbt_target: prod
snowflake_account: your_account.snowflakecomputing.com
snowflake_warehouse: your_warehouse
snowflake_database: your_database
snowflake_schema: your_schema
```

### Como usar:
```python
from airflow.models import Variable

project_dir = Variable.get("dbt_project_dir")
target = Variable.get("dbt_target")
```

## 🔄 Fluxo Prático: Como Funciona

### **Desenvolvimento Local:**
```python
# 1. Você desenvolve localmente
# 2. Usa .env para credenciais
# 3. Testa com Docker
# 4. Faz commit para GitHub
```

### **CI/CD (GitHub Actions):**
```yaml
# 1. GitHub Actions executa
# 2. Usa GitHub Secrets para credenciais
# 3. Faz upload para S3
# 4. Atualiza Airflow local
```

### **Produção (ECS/EKS):**
```python
# 1. Airflow em produção executa DAGs
# 2. Usa AWS Secrets Manager para credenciais
# 3. Usa Airflow Variables para configurações
# 4. Executa DBT no Snowflake
```

## 🛠️ Implementação Prática

### Exemplo de DAG que funciona em todos os ambientes:

```python
import os
from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from airflow.exceptions import AirflowException

# Tentar importar SecretsManagerBackend (disponível em produção)
try:
    from airflow.providers.amazon.aws.secrets.secrets_manager import SecretsManagerBackend
    SECRETS_MANAGER_AVAILABLE = True
except ImportError:
    SECRETS_MANAGER_AVAILABLE = False

@task
def get_snowflake_credentials(**context):
    """
    Obtém credenciais do Snowflake da fonte apropriada
    """
    credentials = {}

    # Prioridade 1: AWS Secrets Manager (produção)
    if SECRETS_MANAGER_AVAILABLE:
        try:
            secrets_backend = SecretsManagerBackend()
            secret_name = "airflow/snowflake/credentials"
            secret_value = secrets_backend.get_conn_uri(secret_name)

            if secret_value:
                # Parse do secret
                parts = secret_value.split(":")
                if len(parts) >= 6:
                    credentials = {
                        "account": parts[0],
                        "user": parts[1],
                        "password": parts[2],
                        "warehouse": parts[3],
                        "database": parts[4],
                        "schema": parts[5]
                    }
                    return credentials
        except Exception as e:
            print(f"Erro ao acessar Secrets Manager: {str(e)}")

    # Prioridade 2: Airflow Variables (configuração)
    try:
        account = Variable.get("snowflake_account", default_var=None)
        user = Variable.get("snowflake_user", default_var=None)
        password = Variable.get("snowflake_password", default_var=None)
        warehouse = Variable.get("snowflake_warehouse", default_var=None)
        database = Variable.get("snowflake_database", default_var=None)
        schema = Variable.get("snowflake_schema", default_var=None)

        if all([account, user, password, warehouse, database, schema]):
            credentials = {
                "account": account,
                "user": user,
                "password": password,
                "warehouse": warehouse,
                "database": database,
                "schema": schema
            }
            return credentials
    except Exception as e:
        print(f"Erro ao acessar Airflow Variables: {str(e)}")

    # Prioridade 3: Variáveis de ambiente (desenvolvimento)
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA")

    if all([account, user, password, warehouse, database, schema]):
        credentials = {
            "account": account,
            "user": user,
            "password": password,
            "warehouse": warehouse,
            "database": database,
            "schema": schema
        }
        return credentials

    # Se nenhuma fonte funcionou
    raise AirflowException("Não foi possível obter credenciais do Snowflake")
```

## 📋 Checklist de Configuração

### ✅ **Desenvolvimento Local:**
- [ ] Arquivo `.env` configurado
- [ ] Docker Compose montando `.env`
- [ ] Código usando `os.getenv()`

### ✅ **GitHub Actions:**
- [ ] Secrets configurados no GitHub
- [ ] Workflow usando `${{ secrets.NOME }}`
- [ ] Upload para S3 funcionando

### ✅ **Produção (ECS/EKS):**
- [ ] Secret criado no Secrets Manager
- [ ] Airflow Variables configuradas
- [ ] DAGs usando `SecretsManagerBackend()`

## 🚨 Segurança

### **Boas Práticas:**
1. **Nunca** commite credenciais no código
2. **Use** `.env` localmente (já no `.gitignore`)
3. **Use** GitHub Secrets para CI/CD
4. **Use** AWS Secrets Manager para produção
5. **Rotacione** credenciais regularmente

### **O que NÃO fazer:**
```python
# ❌ NUNCA faça isso
SNOWFLAKE_PASSWORD = "minha_senha_secreta"  # Hardcoded

# ❌ NUNCA faça isso
print(f"Password: {password}")  # Log de senha
```

### **O que fazer:**
```python
# ✅ Faça isso
password = os.getenv("SNOWFLAKE_PASSWORD")  # Variável de ambiente

# ✅ Faça isso
print(f"Password: {'*' * len(password)}")  # Mascarar senha
```

## 🎯 Próximos Passos

1. **Mantenha** o `.env` para desenvolvimento local
2. **Configure** GitHub Secrets para CI/CD
3. **Crie** secret no AWS Secrets Manager
4. **Configure** Airflow Variables no Airflow local
5. **Teste** em cada ambiente

## ❓ Dúvidas Frequentes

### **P: Preciso configurar tudo de uma vez?**
**R:** Não! Comece com o `.env` local, depois configure conforme for precisando.

### **P: Posso usar só o `.env` em produção?**
**R:** Não é recomendado. Use AWS Secrets Manager para produção.

### **P: Como sei qual fonte está sendo usada?**
**R:** Execute o DAG `credentials_example` que criei para verificar.

### **P: E se uma fonte falhar?**
**R:** O código tem fallback automático para a próxima fonte.

---

**🎉 Agora você entende exatamente onde cada coisa fica!** Mantenha o `.env` local e configure os outros conforme for precisando.
