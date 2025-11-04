# Infraestrutura Airflow com Docker e AWS ECR

Esta pasta contém a configuração para rodar Airflow localmente com Docker ou usando imagens do AWS ECR em produção.

## Estrutura

```
airflow/
├── Dockerfile           # Imagem Docker usando UV e pyproject.toml
├── build-ecr.sh         # Script para build e push para ECR
├── setup-ecr.sh         # Script para criar repositório ECR
├── dags/                # DAGs do Airflow
└── README.md            # Este arquivo
```

## Configuração

### Dependências

As dependências são gerenciadas através do `pyproject.toml` na raiz do projeto, não há mais `requirements.txt` separado. Isso garante:

- ✅ **Consistência**: Mesmas dependências local e produção
- ✅ **Versionamento**: Controle centralizado de versões
- ✅ **UV**: Instalação rápida e eficiente

### Dockerfile

O Dockerfile usa:
- Imagem base oficial do Airflow: `apache/airflow:2.9.3-python3.12`
- **UV** para gerenciar dependências (mais rápido que pip)
- `pyproject.toml` para instalar dependências (apenas produção, sem dev)

## Uso Local (Docker Compose)

### Iniciar ambiente local

```bash
# Build da imagem local
docker-compose build

# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f airflow-scheduler

# Parar serviços
docker-compose down
```

### Acessar Airflow

- **Web UI**: http://localhost:8080
- **Usuário**: `admin`
- **Senha**: `admin`

### Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com:

```bash
# Snowflake
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_DATABASE_DEV=your_dev_database
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_PRIVATE_KEY_PATH=/opt/airflow/.dbt/rsa_key.p8
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase
SNOWFLAKE_QUERY_TAG=airflow_local

# AWS (opcional para local)
AWS_REGION=us-east-1
```

## Uso com AWS ECR (Produção)

### O que é ECR?

**Amazon Elastic Container Registry (ECR)** é um serviço de registro de containers Docker gerenciado pela AWS. É como um "Docker Hub privado" na AWS.

**Vantagens:**
- 🔒 **Segurança**: Imagens privadas, integrado com IAM
- ⚡ **Performance**: Mais rápido que Docker Hub público
- 💰 **Custo**: Geralmente mais barato para grandes volumes
- 🔗 **Integração**: Fácil integração com ECS, EKS, Lambda, etc.

### Setup Inicial (primeira vez)

#### 1. Configurar credenciais AWS

```bash
# Instalar AWS CLI (se não tiver)
# https://aws.amazon.com/cli/

# Configurar credenciais
aws configure

# Ou usar variáveis de ambiente
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

#### 2. Obter AWS Account ID

```bash
# Opção 1: Via AWS CLI
aws sts get-caller-identity --query Account --output text

# Opção 2: Via console AWS (canto superior direito)
# Anote o Account ID exibido
```

#### 3. Criar repositório ECR

```bash
# Configurar variáveis
export AWS_ACCOUNT_ID=123456789012  # Seu Account ID
export AWS_REGION=us-east-1
export ECR_REPO_NAME=dataflow-airflow  # Nome do repositório

# Criar repositório
./airflow/setup-ecr.sh
```

Isso cria um repositório ECR com:
- Scanning de vulnerabilidades habilitado
- Criptografia AES256
- Tags mutáveis (permite atualizar tags)

### Build e Push para ECR

```bash
# Configurar Account ID (se ainda não configurou)
export AWS_ACCOUNT_ID=123456789012

# Build e push com tag específica
./airflow/build-ecr.sh v1.0.0

# Ou usar tag padrão "latest"
./airflow/build-ecr.sh

# Ou tag por commit/branch
./airflow/build-ecr.sh $(git rev-parse --short HEAD)
./airflow/build-ecr.sh develop
./airflow/build-ecr.sh main
```

O script:
1. 🔨 Faz build da imagem Docker
2. 🔐 Autentica no ECR
3. 📤 Faz push da imagem

### Usar imagem do ECR

#### Opção 1: Docker Compose (para testes)

Atualize `docker-compose.yml`:

```yaml
services:
  airflow-scheduler:
    # Comentado: build local
    # build:
    #   context: .
    #   dockerfile: airflow/Dockerfile

    # Usando imagem do ECR
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/dataflow-airflow:latest
    # ... resto da configuração
```

```bash
# Autenticar no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Usar docker-compose normalmente
docker-compose pull
docker-compose up -d
```

#### Opção 2: ECS/EKS (Produção)

No task definition ECS ou deployment EKS, use:

```json
{
  "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:latest",
  ...
}
```

Certifique-se de que a task/role tenha permissões para:
- `ecr:GetAuthorizationToken`
- `ecr:BatchGetImage`
- `ecr:GetDownloadUrlForLayer`

### Atualizar Imagem em Produção

```bash
# 1. Build e push nova versão
./airflow/build-ecr.sh v1.1.0

# 2. Atualizar task/service no ECS/EKS
# Para ECS: force new deployment
aws ecs update-service --cluster your-cluster --service your-service --force-new-deployment

# Para EKS: atualizar deployment
kubectl set image deployment/airflow-scheduler \
  scheduler=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/dataflow-airflow:v1.1.0
```

## Estratégias de Tags

### Recomendado

```bash
# Versão semântica
./airflow/build-ecr.sh v1.0.0

# Branch (desenvolvimento)
./airflow/build-ecr.sh develop

# Commit SHA (reproduzível)
./airflow/build-ecr.sh $(git rev-parse --short HEAD)

# Latest (última versão)
./airflow/build-ecr.sh latest
```

## Troubleshooting

### Erro: "repository does not exist"

```bash
# Criar repositório
./airflow/setup-ecr.sh
```

### Erro: "unauthorized"

```bash
# Autenticar no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com
```

### Erro: "build failed" - UV não encontrado

Verifique se o Dockerfile está copiando `pyproject.toml` corretamente. O contexto do build deve ser a **raiz do projeto**, não a pasta `airflow/`.

## Próximos Passos

- [ ] Configurar CI/CD para build automático no push
- [ ] Adicionar tags de versão baseadas em Git tags
- [ ] Configurar scanning automático de vulnerabilidades
- [ ] Adicionar multi-stage build para reduzir tamanho da imagem
