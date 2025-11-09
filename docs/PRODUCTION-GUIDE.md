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

## 🔄 Fluxo Completo de Produção (End-to-End)

Este fluxo garante que todas as alterações passem por validação, build automatizado e deploy na EC2.

### Visão Geral do Fluxo

```
┌─────────────────┐
│ 1. Desenvolvimento │
│    Local          │
│    (feature/*)    │
└────────┬──────────┘
         │ git push
         ▼
┌─────────────────┐
│ 2. Pull Request  │
│    → develop     │
│    (validação)   │
└────────┬──────────┘
         │ merge
         ▼
┌─────────────────┐
│ 3. Merge develop │
│    → GitHub      │
│    Actions       │
│    (build ECR)   │
└────────┬──────────┘
         │
         ▼
┌─────────────────┐
│ 4. ECR Registry  │
│    (imagem)      │
└────────┬──────────┘
         │
         ▼
┌─────────────────┐
│ 5. EC2 Update    │
│    (git pull +   │
│     docker pull) │
└─────────────────┘
```

### 1. **Desenvolvimento Local**

```bash
# 1. Criar branch de feature
git checkout -b feature/new-pipeline

# 2. Fazer alterações (DAGs, modelos DBT, etc.)
# Editar arquivos em:
# - airflow/dags/*.py
# - dbt/models/*.sql
# - pyproject.toml (dependências)

# 3. Testar localmente
docker-compose build
docker-compose up -d
# Acessar: http://localhost:8080

# 4. Validar código localmente (opcional, mas recomendado)
pre-commit run --all-files

# 5. Commit e push
git add .
git commit -m "Add new DBT pipeline"
git push origin feature/new-pipeline
```

**Importante**: As alterações locais **não** aparecem automaticamente na EC2. Elas precisam passar pelo fluxo completo.

### 2. **Pull Request para `develop`**

```bash
# 1. Criar PR no GitHub (feature/new-pipeline → develop)
# 2. GitHub Actions executa automaticamente:
#    - Validações (pre-commit hooks)
#    - Lint de código Python
#    - Lint de SQL (sqlfluff)
#    - Validação de sintaxe dos DAGs
```

**O que acontece**:
- ✅ Workflow `.github/workflows/lint_on_push.yml` executa
- ✅ Valida apenas arquivos modificados no PR
- ✅ Se passar, PR pode ser mergeado

### 3. **Merge para `develop` → Build Automático**

Quando você faz merge do PR para `develop`:

```bash
# 1. Merge PR no GitHub (feature/new-pipeline → develop)
# 2. GitHub Actions executa automaticamente:
#    - Workflow: .github/workflows/build-and-push-ecr.yml
#    - Build da imagem Docker
#    - Push para ECR com tag: develop
#    - Push também com tag: <SHA do commit>
```

**O que acontece**:
- ✅ Workflow `.github/workflows/build-and-push-ecr.yml` executa
- ✅ Build da imagem Docker usando `airflow/Dockerfile`
- ✅ Push para ECR: `679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:develop`
- ✅ Push também com SHA: `679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:<SHA>`

**Verificar o build**:
- Vá em **Actions** no GitHub → veja o workflow "Build and Push to ECR"
- Se falhar, veja os logs para identificar o problema

### 4. **Merge `develop` → `main` → Build para Produção**

Quando você faz merge de `develop` para `main`:

```bash
# 1. Merge develop → main no GitHub
# 2. GitHub Actions executa automaticamente:
#    - Build da imagem Docker
#    - Push para ECR com tags: main, latest, <SHA>
```

**O que acontece**:
- ✅ Build da imagem Docker
- ✅ Push para ECR: `679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:main`
- ✅ Push também: `679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:latest`
- ✅ Push com SHA: `679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:<SHA>`

### 5. **Atualizar EC2 com Código e Imagem**

**IMPORTANTE**: A EC2 precisa ser atualizada manualmente (ou via script automatizado) após o merge. O código e a imagem **não** são atualizados automaticamente.

#### 5.1 Atualizar Código na EC2

Na EC2, você precisa fazer `git pull` para pegar as alterações mais recentes:

```bash
# 1. Conectar na EC2
ssh -i ~/.ssh/airflow-ec2.pem ec2-user@<IP-EC2>

# 2. Ir para o diretório do projeto
cd ~/dataflow-setup

# 3. Verificar branch atual (deve ser main ou develop)
git branch

# 4. Atualizar código da branch
git pull origin main  # ou develop, dependendo do que você quer

# 5. Verificar se há alterações
git log --oneline -5
```

**Por que isso é necessário?**
- O `docker-compose.yml` monta volumes do filesystem da EC2
- Os DAGs em `airflow/dags/` vêm do código clonado na EC2
- Se o código não for atualizado, os DAGs antigos continuam rodando

#### 5.2 Atualizar Imagem Docker na EC2

Após atualizar o código, você precisa atualizar a imagem Docker do ECR:

```bash
# 1. Autenticar no ECR (se ainda não estiver autenticado)
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=679047180828
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 2. Fazer pull da nova imagem
docker-compose pull

# 3. Reiniciar os serviços com a nova imagem
docker-compose down
docker-compose up -d

# 4. Verificar se está usando a imagem correta
docker-compose images
```

**Alternativa: Usar `docker-compose.override.yml`**

Para garantir que sempre use a imagem do ECR, crie `docker-compose.override.yml` na EC2:

```bash
# Na EC2, dentro de ~/dataflow-setup
cat > docker-compose.override.yml <<'YAML'
services:
  airflow-init:
    image: 679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:main
    build:  # Remove build local

  airflow-scheduler:
    image: 679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:main

  airflow-webserver:
    image: 679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:main
YAML
```

**Nota**: O `docker-compose.override.yml` é um arquivo local (não commitado) que sobrescreve o `docker-compose.yml` na EC2.

#### 5.3 Script de Atualização Automática (Opcional)

Você pode criar um script na EC2 para automatizar a atualização:

```bash
# Na EC2, criar ~/dataflow-setup/update.sh
cat > ~/dataflow-setup/update.sh <<'SCRIPT'
#!/bin/bash
set -e

cd ~/dataflow-setup

echo "🔄 Atualizando código..."
git pull origin main

echo "🔐 Autenticando no ECR..."
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=679047180828
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "📦 Atualizando imagens Docker..."
docker-compose pull

echo "🔄 Reiniciando serviços..."
docker-compose down
docker-compose up -d

echo "✅ Atualização concluída!"
docker-compose ps
SCRIPT

chmod +x ~/dataflow-setup/update.sh
```

**Usar o script**:
```bash
~/dataflow-setup/update.sh
```

### 6. **Verificar Atualização na EC2**

```bash
# 1. Verificar versão do código
cd ~/dataflow-setup
git log --oneline -1

# 2. Verificar imagem Docker em uso
docker-compose images

# 3. Verificar logs do scheduler (deve mostrar DAGs atualizados)
docker-compose logs airflow-scheduler | tail -20

# 4. Acessar Airflow UI
# http://<IP-EC2>:8080
# Verificar se os DAGs atualizados aparecem
```

### Resumo do Fluxo Completo

| Etapa | Onde | Ação | Automático? |
|-------|------|------|-------------|
| 1. Desenvolvimento | Local | Editar código, testar localmente | ❌ Manual |
| 2. PR | GitHub | Criar PR (feature → develop) | ❌ Manual |
| 3. Validação | GitHub Actions | Lint e validações | ✅ Automático |
| 4. Merge develop | GitHub | Merge PR para develop | ❌ Manual |
| 5. Build develop | GitHub Actions | Build e push para ECR | ✅ Automático |
| 6. Merge main | GitHub | Merge develop → main | ❌ Manual |
| 7. Build main | GitHub Actions | Build e push para ECR (tag: main, latest) | ✅ Automático |
| 8. Atualizar EC2 | EC2 | `git pull` + `docker-compose pull` | ❌ Manual (ou script) |

**Dica**: Para automatizar a etapa 8, você pode configurar um cron job na EC2 ou usar AWS Systems Manager para executar o script de atualização periodicamente.

## 🛠️ Implementação Passo a Passo

### Passo 1: Configurar AWS ECR

#### 1.1 Setup Inicial do ECR

```bash
# Configurar variáveis
export AWS_ACCOUNT_ID=123456789012
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

# 8. Criar docker-compose.override.yml para usar imagem do ECR
# (Isso sobrescreve o build local e usa a imagem do ECR)
cat > docker-compose.override.yml <<'YAML'
services:
  airflow-init:
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/dataflow-airflow:main

  airflow-scheduler:
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/dataflow-airflow:main

  airflow-webserver:
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/dataflow-airflow:main
YAML

# 9. Fazer pull da imagem do ECR
docker-compose pull

# 10. Iniciar serviços
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

**Secrets obrigatórios para build ECR**:
```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_ACCOUNT_ID=123456789012
AWS_REGION=us-east-1
```

**Secrets opcionais (para outros workflows)**:
```
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_ROLE=your-role
SNOWFLAKE_DATABASE_DEV=your-dev-database
SNOWFLAKE_DATABASE_PROD=your-prod-database
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_SCHEMA=your-schema
```

**Como adicionar secrets**:
1. Vá em **Settings** do repositório
2. **Secrets and variables** → **Actions**
3. Clique em **New repository secret**
4. Adicione cada secret acima

#### 5.2 Workflows Configurados

O projeto já possui dois workflows configurados:

**1. `.github/workflows/lint_on_push.yml`** (Validação):
- ✅ Executa em PRs e pushes para `main`/`develop`
- ✅ Valida código com pre-commit hooks
- ✅ Lint de Python (black, isort, flake8)
- ✅ Lint de SQL (sqlfluff)
- ✅ Valida apenas arquivos modificados

**2. `.github/workflows/build-and-push-ecr.yml`** (Build e Deploy):
- ✅ Executa em push para `main` ou `develop`
- ✅ Build da imagem Docker usando `airflow/Dockerfile`
- ✅ Push para ECR com tags:
  - `develop` → tag: `develop` + `<SHA>`
  - `main` → tag: `main` + `latest` + `<SHA>`

**Como funciona o workflow de build**:

1. **Trigger**: Push para `main` ou `develop`
2. **Build**: Usa `airflow/Dockerfile` com contexto na raiz do projeto
3. **Tags**:
   - Branch `develop` → `dataflow-airflow:develop` + `dataflow-airflow:<SHA>`
   - Branch `main` → `dataflow-airflow:main` + `dataflow-airflow:latest` + `dataflow-airflow:<SHA>`
4. **Push**: Envia todas as tags para o ECR

**Verificar execução**:
- Vá em **Actions** no GitHub
- Veja o workflow "Build and Push to ECR"
- Clique na execução para ver logs detalhados

**Execução manual**:
- O workflow também pode ser executado manualmente via **Actions** → **Build and Push to ECR** → **Run workflow**

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

### 5. **Código na EC2 não está atualizado**
```bash
# Na EC2, verificar branch e atualizar código
cd ~/dataflow-setup
git branch  # Deve estar em main ou develop
git pull origin main  # Atualizar código

# Verificar se os DAGs foram atualizados
ls -la airflow/dags/

# Reiniciar serviços para carregar novos DAGs
docker-compose restart airflow-scheduler
```

### 6. **Imagem na EC2 não está atualizada**
```bash
# Na EC2, autenticar no ECR e fazer pull da nova imagem
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=679047180828
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Fazer pull da nova imagem
docker-compose pull

# Reiniciar serviços
docker-compose down
docker-compose up -d

# Verificar qual imagem está sendo usada
docker-compose images
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
