# Guia de Setup: Airflow no EC2 usando imagem do ECR

Este guia padroniza como subir o Airflow em uma instância EC2 usando a imagem Docker que você já publicou no AWS ECR.

## Visão geral (em termos simples)

- Você já construiu uma imagem Docker do Airflow com tudo que o projeto precisa e a publicou no ECR.
- A EC2 será apenas uma máquina Linux na nuvem que vai: (1) instalar Docker/Compose, (2) baixar a imagem do ECR, (3) rodar os containers com o `docker-compose.yml` deste repositório.
- O `docker-compose.yml` do projeto descreve os serviços (Postgres, Airflow Scheduler, Airflow Webserver, tarefa de init) e seus volumes/variáveis. Na EC2, iremos usá‑lo praticamente como está, apenas apontando a imagem para a do ECR (em vez de construir localmente).

Resultado: você acessa a UI do Airflow na porta 8080 da EC2; o Scheduler agenda e executa DAGs; o dbt roda dentro do container do Airflow e se conecta ao Snowflake.

## O que exatamente está rodando e onde?

- Airflow (webserver, scheduler e a tarefa one‑shot de init) roda em containers Docker dentro da EC2.
- Postgres (banco do Airflow) também roda como container.
- O código de DAGs (`airflow/dags/`), o projeto dbt (`dbt/`) e o `profiles.yml` (em `.dbt/`) são montados como volumes do host (diretórios no disco da EC2) para dentro dos containers.
- O dbt executa DENTRO do container do Airflow e se conecta ao Snowflake via rede pública, usando as credenciais/env vars.

## Pré‑requisitos

- Conta AWS com permissões para EC2 e ECR.
- Chave SSH (.pem) para acessar a EC2.
- Repositório ECR com a imagem publicada, por exemplo:
  - `679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:latest`
- Security Group permitindo:
  - SSH (TCP 22) – idealmente somente do seu IP.
  - Airflow UI (TCP 8080) – seu IP, IPs selecionados ou público (0.0.0.0/0) apenas para demonstração.
- Opcional: Elastic IP para link fixo.

## Passo a passo (console AWS + terminal)

### 1) Criar a EC2 (no Console AWS)

- Região: us‑east‑1 (ou a que você estiver usando no ECR)
- AMI: Amazon Linux 2023 (x86_64)
- Tipo: t3.small (2 GiB RAM) – recomendado para demos; t3.micro funciona mas pode ficar apertado
- Key pair: crie/seleciona uma chave (.pem)
- Rede:
  - VPC: default
  - Subnet: pública
  - Auto‑assign public IP: Enable
- Security Group (novo):
  - SSH (TCP 22) → Source: "My IP" (recomendado)
  - Custom TCP (8080) → Source:
    - A) 0.0.0.0/0 (público; simples mas menos seguro), ou
    - B) Um IP por usuário (ex.: 203.0.113.10/32), ou
    - C) Não criar 8080 e usar túnel SSH (mais seguro)
- Armazenamento: 10–20 GiB gp3
- (Opcional) IAM Role: anexe uma role com política "AmazonEC2ContainerRegistryReadOnly" – evita precisar de `docker login` no ECR.
- Launch.

### 2) Conectar via SSH

```bash
ssh -i ~/.ssh/sua-chave.pem ec2-user@<IP_PUBLICO_EC2>
ssh -i /home/leopfs/205/.keys/airflow-ec2.pem ec2-user@35.175.248.11

```

### 3) Instalar Docker, Compose e AWS CLI

```bash
sudo dnf update -y
sudo dnf install -y docker git awscli
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
newgrp docker

# Docker Compose (binário standalone v2)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose version
```

### 4) Login no ECR (se a instância NÃO tiver IAM Role com leitura no ECR)

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=679047180828
aws ecr get-login-password --region $AWS_REGION \
| docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
```

### 5) Trazer o repositório e preparar diretórios

```bash
git clone <SEU_REPO_GIT> dataflow-setup
cd dataflow-setup

# Diretórios que serão montados como volumes
mkdir -p airflow/dags logs plugins dbt .dbt dataflow

# Permissões amigáveis no host
sudo chown -R ec2-user:ec2-user airflow/dags logs plugins dbt .dbt dataflow
chmod -R u+rwX,g+rwX airflow/dags logs plugins dbt .dbt dataflow
```

### 6) Usar a imagem do ECR no Compose

O `docker-compose.yml` do projeto já define os serviços e volumes. Localmente você construiu a imagem com `build:`. Na EC2, queremos usar a imagem pronta do ECR.

Você pode fazer isso sem editar o arquivo principal criando um override:

```bash
cat > docker-compose.override.yml <<'YAML'
services:
  airflow-init:
    image: 679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:latest
  airflow-scheduler:
    image: 679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:latest
  airflow-webserver:
    image: 679047180828.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:latest
YAML
```

O Docker Compose automaticamente mescla `docker-compose.yml` + `docker-compose.override.yml` na subida.

### 7) Subir os serviços

```bash
docker-compose pull             # garante a imagem do ECR
docker-compose up -d

# Verificar
docker-compose ps
```

### 8) Acessar a UI do Airflow

- Garanta no Security Group a regra TCP 8080 (ver seção pré‑requisitos)
- Abra: `http://<IP_PUBLICO_EC2>:8080`
- Usuário: `admin`, Senha: `admin`
- Se necessário, (re)crie o usuário:

```bash
docker-compose exec airflow-webserver airflow users create \
  --username admin --firstname Admin --lastname User --role Admin \
  --email admin@example.com --password admin
```

## Perguntas frequentes (FAQ)

### O que a EC2 precisa ter para funcionar?
- Docker e Docker Compose instalados e ativos
- Acesso ao ECR (via IAM Role ou `docker login`)
- Security Group com SSH (22) e UI do Airflow (8080) conforme sua política
- Diretórios montados (dags, logs, plugins, dbt, .dbt, dataflow) existentes no host

### A EC2 usa o `docker-compose.yml` do projeto?
Sim. Ele é a fonte da verdade da orquestração local/EC2: define containers, variáveis e volumes. Na EC2, adicionamos um `docker-compose.override.yml` para apontar a imagem para o ECR em vez de construir localmente. Nada muda na lógica dos serviços.

### Onde o dbt roda?
Dentro do container do Airflow (scheduler/webserver, conforme sua DAG). O container possui as dependências instaladas (via `pyproject.toml`/UV). Ele usa os arquivos do projeto `dbt/` montados e o `profiles.yml` em `.dbt/` para conectar no Snowflake.

### Preciso deixar a EC2 ligada para agendamento diário?
Sim, se o Scheduler do Airflow estiver na EC2, ela precisa estar executando. Para custo baixo, use instância pequena (t3.small) e desligue quando não precisar. Para manter 24/7, o custo permanece baixo em t3.small; t3.micro é ainda mais barato.

### Preciso de Elastic IP?
Não é obrigatório. Mas se deseja um link estável/publicável, associe um Elastic IP (gratuito enquanto associado a uma instância em execução). Sem Elastic IP, o IP público pode mudar após Stop/Start.

### É seguro abrir 8080 para o mundo (0.0.0.0/0)?
Para laboratório/demonstração, funciona; para segurança, prefira:
- Restringir por IP (um `/32` por usuário), ou
- Não expor 8080 e usar túnel SSH (`ssh -L 8080:localhost:8080 ec2-user@IP`)

### Logs e permissões
Se o webserver falhar com `Permission denied` em `/opt/airflow/logs`, garanta que os diretórios mapeados existem e estão com permissão de escrita do host:

```bash
sudo chown -R ec2-user:ec2-user logs airflow/dags plugins dbt .dbt dataflow
chmod -R u+rwX,g+rwX logs airflow/dags plugins dbt .dbt dataflow
```

### Como parar/atualizar?

```bash
# Parar
docker-compose down

# Atualizar imagem do ECR e reler
docker-compose pull
docker-compose up -d --force-recreate
```

## Troubleshooting rápido

- UI não abre: ver `docker-compose ps`, `docker-compose logs --tail=200 airflow-webserver`, Security Group 8080.
- `airflow-init` em Exited: é esperado (tarefa one‑shot). Se necessário, rode `docker-compose run --rm airflow-init`.
- Erro de permissão em logs: veja seção "Logs e permissões".
- ECR não autentica: verifique `aws sts get-caller-identity`, IAM Role ou `docker login` com `aws ecr get-login-password`.

## Resumo

- EC2 é o host; Docker/Compose orquestram containers; a imagem vem do ECR; o compose do projeto define a topologia.
- Você ganha um ambiente de demonstração/treinamento muito próximo de produção, com baixo custo e link público opcional.
