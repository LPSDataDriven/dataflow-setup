# 🚀 Guia Completo de Implementação em Produção

## GitHub + Airflow + DBT Core + AWS (ECR, S3)

Este guia mostra como implementar um pipeline de dados completo usando:
- **GitHub** para versionamento
- **Airflow** com Docker para orquestração
- **DBT Core** para transformações
- **AWS ECR** para registry de containers (praticamente gratuito no free tier)
- **AWS S3** para artefatos/logs
- **Snowflake** como data warehouse

## 📋 Visão Geral da Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub Repo   │───▶│   GitHub Actions│───▶│   AWS ECR       │
│                 │    │   (CI/CD)       │    │   (Images)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   S3 Bucket     │◀───│   Airflow        │───▶│   DBT Core      │
│   (Artifacts)   │    │   (Local/EC2)    │    │   (Transform)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                          │
                                                          ▼
                                                  ┌─────────────────┐
                                                  │   Snowflake     │
                                                  │   (Data Lake)   │
                                                  └─────────────────┘
```

## 🔄 Fluxo Completo de Produção

### 1. **Desenvolvimento Local**
```bash
# Desenvolver DAGs e modelos DBT
git checkout -b feature/new-pipeline

# Testar localmente
docker-compose up -d
# Acessar: http://localhost:8080

# ... fazer mudanças ...
git add .
git commit -m "Add new DBT pipeline"
git push origin feature/new-pipeline
```

### 2. **Pull Request**
- GitHub Actions executa validações (pre-commit hooks)
- Testa DAGs e modelos DBT
- Valida sintaxe e conectividade

### 3. **Merge para Main/Develop**
- GitHub Actions faz build da imagem Docker
- Push da imagem para **AWS ECR** (praticamente gratuito no free tier)
- Upload de artefatos para S3 bucket

### 4. **Execução no Airflow**
- Airflow (local ou EC2) baixa imagem do ECR
- Scheduler executa DAGs conforme cron
- Tasks executam comandos DBT
- DBT conecta no Snowflake e executa SQL
- Logs são salvos localmente e no S3

## 🛠️ Implementação Passo a Passo

### Passo 1: Configurar AWS ECR

#### 1.1 Setup Inicial do ECR

```bash
# Configurar variáveis
export AWS_ACCOUNT_ID=123456789012  # Seu Account ID
export AWS_REGION=us-east-1
export ECR_REPO_NAME=dataflow-airflow

# Criar repositório ECR
./airflow/setup-ecr.sh
```

Isso cria um repositório ECR com:
- Scanning de vulnerabilidades habilitado
- Criptografia AES256
- Tags mutáveis

#### 1.2 Build e Push da Imagem

```bash
# Build e push para ECR
./airflow/build-ecr.sh v1.0.0

# Ou usar tag específica
./airflow/build-ecr.sh develop
./airflow/build-ecr.sh main
```

**Custos ECR** (para treinamento):
- **Storage**: Primeiros 500MB/mês = **GRATUITO** ✅
- **Data Transfer**: Primeiro 1GB/mês = **GRATUITO** ✅
- **Total estimado**: **$0.00/mês** ✅

Veja `ECR-COSTS-AND-ALTERNATIVES.md` para mais detalhes.

---

### Passo 2: Configurar Airflow Local (Desenvolvimento)

#### 2.1 Docker Compose

O arquivo `docker-compose.yml` já está configurado na raiz do projeto:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    # ... configuração ...

  airflow-init:
    build:
      context: .
      dockerfile: airflow/Dockerfile
    image: dataflow-airflow:latest
    # ... configuração ...

  airflow-scheduler:
    image: dataflow-airflow:latest
    command: ["airflow", "scheduler"]
    # ... configuração ...

  airflow-webserver:
    image: dataflow-airflow:latest
    command: ["airflow", "webserver"]
    ports:
      - "8080:8080"
    # ... configuração ...
```

#### 2.2 Dockerfile

O Dockerfile (`airflow/Dockerfile`) usa:
- **UV** para gerenciar dependências (mais rápido que pip)
- **pyproject.toml** para instalar dependências (não há mais `requirements.txt`)
- Imagem base: `apache/airflow:2.9.3-python3.12`

#### 2.3 Iniciar Ambiente Local

```bash
# Build da imagem local
docker-compose build

# Iniciar todos os serviços
docker-compose up -d

# Ver logs
docker-compose logs -f airflow-scheduler

# Acessar Airflow UI
open http://localhost:8080
# Usuário: admin
# Senha: admin
```

**Acesso**: `http://localhost:8080` (apenas local)

Veja `docker-compose.md` para explicação detalhada.

---

### Passo 3: Configurar Airflow com ECR (Demonstração/Compartilhamento)

Para ter um **link público** que outros usuários podem acessar:

#### 3.1 Opção: EC2 com IP Público 💰 **~$5-10/mês**

**Como funciona**:
- Instância EC2 roda Docker Compose
- Imagem do ECR é usada no EC2
- IP público do EC2 expõe porta 8080
- Link público disponível

**Configuração**:

```bash
# 1. Criar instância EC2 (t2.micro - elegível para free tier)
# 2. Conectar via SSH
ssh -i ~/.ssh/your-key.pem ec2-user@<IP-EC2>

# 3. Instalar Docker e Docker Compose
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Instalar AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 5. Configurar credenciais AWS
aws configure

# 6. Autenticar no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# 7. Clone o repositório
git clone <your-repo>
cd dataflow-setup

# 8. Atualizar docker-compose.yml para usar imagem do ECR
# Editar docker-compose.yml:
#   airflow-webserver:
#     image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/dataflow-airflow:latest
#     # (remover build: se tiver)

# 9. Iniciar
docker-compose up -d

# 10. Configurar Security Group para permitir porta 8080
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 8080 \
  --cidr 0.0.0.0/0  # ⚠️ Apenas para treinamento!

# 11. Acessar
http://<IP-PUBLICO-EC2>:8080
```

**Link específico com Elastic IP**:

```bash
# Alocar Elastic IP (IP fixo)
aws ec2 allocate-address --domain vpc

# Associar ao EC2
aws ec2 associate-address \
  --instance-id i-xxxxxxxxx \
  --allocation-id eipalloc-xxxxxxxxx

# Agora você tem um IP fixo
# Link: http://<ELASTIC-IP>:8080
```

**Segurança**:
- ⚠️ **Configure autenticação do Airflow** (usuário/senha já tem: admin/admin)
- ⚠️ **Use whitelist de IPs** quando possível (não permita 0.0.0.0/0 em produção)
- ✅ **Use SSH Tunnel** para acesso mais seguro (veja `AIRFLOW-UI-ACCESS.md`)

Veja `AIRFLOW-UI-ACCESS.md` para todas as opções de acesso e segurança.

---

### Passo 4: Configurar DBT para Produção

#### 4.1 Profiles para Produção

O arquivo `.dbt/profiles.yml` já está configurado na raiz:

```yaml
my_dbt_project:
  target: dev
  outputs:
    defaults: &snowflake_defaults
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      role: "{{ env_var('SNOWFLAKE_ROLE') }}"
      private_key_path: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PATH') }}"
      private_key_passphrase: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE') }}"
      # ...

    dev:
      <<: *snowflake_defaults
      schema: "{{ env_var('SNOWFLAKE_SCHEMA') }}"

    prod:
      <<: *snowflake_defaults
      database: "{{ env_var('SNOWFLAKE_DATABASE_PROD') }}"
      schema: prod
```

#### 4.2 Variáveis de Ambiente

Crie um arquivo `.env` na raiz:

```bash
# Snowflake
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_DATABASE_DEV=your_dev_database
SNOWFLAKE_DATABASE_PROD=your_prod_database
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_PRIVATE_KEY_PATH=/opt/airflow/.dbt/rsa_key.p8
SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase
SNOWFLAKE_QUERY_TAG=airflow_production

# AWS
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
```

---

### Passo 5: Configurar GitHub Actions (CI/CD)

#### 5.1 Secrets no GitHub

No seu repositório GitHub, vá para **Settings > Secrets and variables > Actions** e adicione:

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_ROLE=your-role
SNOWFLAKE_DATABASE_DEV=your-dev-database
SNOWFLAKE_DATABASE_PROD=your-prod-database
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_SCHEMA=your-schema
```

#### 5.2 Workflow de CI/CD

O arquivo `.github/workflows/lint_on_push.yml` já está configurado para:
- Executar pre-commit hooks
- Validar DAGs e modelos DBT

**Workflow de Deploy (exemplo)**:

```yaml
name: Build and Push to ECR

on:
  push:
    branches: [main, develop]

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Login to ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: dataflow-airflow
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -f airflow/Dockerfile -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
```

---

## 🚀 Executando o Pipeline

### 1. **Setup Inicial (Local)**

```bash
# Clone o repositório
git clone <your-repo>
cd dataflow-setup

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Inicie o Airflow local
docker-compose up -d

# Acesse o Airflow UI
open http://localhost:8080
# Usuário: admin
# Senha: admin
```

### 2. **Execução Manual**

```bash
# Execute DBT localmente
dbt build --target dev

# Ou via Airflow UI
# 1. Acesse http://localhost:8080
# 2. Encontre seu DAG
# 3. Clique em "Trigger DAG"
```

### 3. **Execução Automática**

Os DAGs executam automaticamente conforme o schedule definido nos DAGs.

---

## 📊 Monitoramento e Logs

### 1. **Logs do Airflow**
- **Web UI**: http://localhost:8080 (local) ou http://<IP-EC2>:8080 (EC2)
- **Logs locais**: `./logs/airflow/`
- **S3**: Logs podem ser enviados para S3 (configurar no Airflow)

### 2. **Logs do DBT**
- **Local**: `./logs/dbt/`
- **S3**: Configurar para enviar logs para S3

### 3. **Métricas**
- **Airflow**: Métricas disponíveis no UI
- **DBT**: Logs detalhados de execução
- **Snowflake**: Query history e performance

---

## 🔧 Troubleshooting

### 1. **DAGs não aparecem no Airflow**
```bash
# Verificar logs do scheduler
docker-compose logs airflow-scheduler

# Verificar sintaxe dos DAGs
python -m py_compile airflow/dags/*.py
```

### 2. **DBT não conecta no Snowflake**
```bash
# Testar conexão
dbt debug --target dev

# Verificar variáveis de ambiente
echo $SNOWFLAKE_ACCOUNT
```

### 3. **Erro ao autenticar no ECR**
```bash
# Autenticar manualmente
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Verificar credenciais
aws sts get-caller-identity
```

### 4. **Imagem do ECR não encontra pyproject.toml**
```bash
# Verificar se o build context está correto
# No docker-compose.yml, context deve ser "." (raiz do projeto)
# E o Dockerfile deve estar em airflow/Dockerfile
```

---

## 💰 Estimativa de Custos

### **Desenvolvimento Local (Docker Compose):**
- **Custo**: **$0.00** ✅
- **Acesso**: http://localhost:8080 (apenas local)

### **Demonstração/Compartilhamento (EC2):**
- **EC2 t2.micro**: **$0.00** (free tier) ou **~$7-10/mês** ✅
- **ECR**: **$0.00** (free tier cobre) ✅
- **S3**: **$0.00** (free tier cobre) ✅
- **Total**: **~$0-10/mês** ✅
- **Acesso**: http://<IP-EC2>:8080 (público)

### **Produção Escalável (ECS/EKS):**
- **ECS/EKS**: ~$50-200/mês (não recomendado para treinamento)
- **ALB**: ~$20/mês adicional

---

## 📚 Documentação Relacionada

- **`docker-compose.md`**: Explicação detalhada do docker-compose.yml
- **`airflow/README.md`**: Documentação completa da infraestrutura Airflow e ECR
- **`ECR-COSTS-AND-ALTERNATIVES.md`**: Custos e alternativas ao ECR
- **`AIRFLOW-UI-ACCESS.md`**: Todas as opções de acesso à UI do Airflow

---

## 🎯 Próximos Passos

1. ✅ **Configurar** AWS ECR (praticamente gratuito)
2. ✅ **Testar** pipeline completo localmente
3. ✅ **Deploy** para EC2 (se quiser link público)
4. ✅ **Configurar** CI/CD com GitHub Actions
5. ✅ **Documentar** processos específicos do seu time

---

**Nota**: Este guia foca em uma stack completa para treinamento com custos baixos (~$0-10/mês). ECR é praticamente gratuito no free tier, e EC2 pode ser gratuito (free tier) ou muito barato (~$7-10/mês). Para produção real com alta disponibilidade, considere ECS/EKS (custo mais alto).
