# Como Acessar a UI do Airflow

## Importante: ECR vs Execução de Containers

**ECR (Elastic Container Registry)** é **apenas um registry** (armazém de imagens Docker). Ele **NÃO executa containers**.

Para acessar a **UI do Airflow**, você precisa:
1. ✅ **Ter a imagem no ECR** (feito via `build-ecr.sh`)
2. ✅ **Executar os containers** em algum lugar (local, EC2, ECS, EKS)
3. ✅ **Expor a porta 8080** para acesso

## Opções de Acesso à UI

### Opção 1: Local (Docker Compose) ⭐ **RECOMENDADO PARA TREINAMENTO**

**Custo**: **$0.00** ✅

**Como funciona**:
- Imagens do ECR são baixadas para seu computador
- Docker Compose roda containers localmente
- Acesso via `http://localhost:8080` (apenas no seu computador)

**Acesso**:
- ✅ **Link**: `http://localhost:8080`
- ❌ **Link público**: Não disponível (apenas local)
- ✅ **Usuários**: Apenas quem tem acesso ao seu computador

**Configuração**:
```bash
# O docker-compose.yml atual está configurado para build local
# (usa 'build:' com context: . e dockerfile: airflow/Dockerfile)

# 1. Build da imagem local
docker-compose build

# 2. Iniciar serviços
docker-compose up -d

# 3. Acessar
open http://localhost:8080
```

**Nota**: Se quiser usar imagem do ECR localmente (em vez de build local), você precisaria:
1. Autenticar no ECR
2. Criar um `docker-compose.override.yml` para sobrescrever e usar a imagem do ECR
3. Veja [docs/EC2-AIRFLOW-ECR-SETUP.md](EC2-AIRFLOW-ECR-SETUP.md) para exemplo completo

**Vantagens**:
- ✅ Grátis
- ✅ Fácil setup
- ✅ Bom para desenvolvimento/treinamento

**Desvantagens**:
- ❌ Apenas local (não compartilhável)
- ❌ Requer máquina sempre ligada

---

### Opção 2: EC2 com Docker Compose 💰 **BAIXO CUSTO + LINK PÚBLICO**

**Custo**: ~**$5-10/mês** (t2.micro/small com free tier)

**Como funciona**:
- Instância EC2 roda Docker Compose
- Imagem do ECR é usada no EC2
- IP público do EC2 expõe porta 8080
- Link público disponível

**Acesso**:
- ✅ **Link público**: `http://<IP-PUBLICO-EC2>:8080`
- ✅ **Link específico**: Pode configurar domínio (ex: `airflow.training.com`)
- ✅ **Usuários**: Qualquer um com o link pode acessar (⚠️ segurança)

**Configuração**:
```bash
# 1. Criar instância EC2 (t2.micro - elegível para free tier)
# 2. Instalar Docker e Docker Compose
# 3. Autenticar no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# 4. Pull da imagem do ECR
docker pull ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/dataflow-airflow:latest

# 5. Usar docker-compose com imagem do ECR
docker-compose up -d

# 6. Configurar Security Group para permitir porta 8080
# 7. Acessar via IP público: http://<IP>:8080
```

**Configurar Security Group**:
```bash
# Permitir acesso HTTP (porta 8080)
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 8080 \
  --cidr 0.0.0.0/0  # ⚠️ Acesso público (use com cuidado!)
```

**Link específico com domínio**:
```bash
# Opção 1: Route 53 (se tiver domínio)
# Criar registro A apontando para IP do EC2

# Opção 2: Elastic IP (IP fixo)
aws ec2 allocate-address --domain vpc
aws ec2 associate-address --instance-id i-xxxxxxxxx --allocation-id eipalloc-xxxxxxxxx

# Agora você tem um IP fixo: http://<ELASTIC-IP>:8080
```

**Vantagens**:
- ✅ Link público disponível
- ✅ Baixo custo (~$5-10/mês, ou free tier)
- ✅ Usa ECR (aprende stack AWS)

**Desvantagens**:
- ⚠️ Custo (mas baixo)
- ⚠️ Precisa configurar segurança adequadamente

**Segurança**:
- ⚠️ **NÃO exponha sem autenticação** em produção
- ✅ Use **AWS VPN** ou **SSH Tunnel** para acesso seguro
- ✅ Configure **Basic Auth** no Airflow ou use **ALB** com autenticação

---

### Opção 3: EC2 com SSH Tunnel 🔒 **SEGURO + GRATUITO**

**Custo**: **$0.00** (se usar free tier) ou ~$5-10/mês

**Como funciona**:
- EC2 roda Airflow **sem expor porta 8080 publicamente**
- Você cria um **tunnel SSH** do seu computador para o EC2
- Acesso via `http://localhost:8080` (túnel seguro)

**Acesso**:
- ✅ **Link local**: `http://localhost:8080` (via túnel)
- ❌ **Link público**: Não disponível (mais seguro)
- ✅ **Usuários**: Apenas quem tem chave SSH

**Configuração**:
```bash
# 1. Criar instância EC2
# 2. Instalar Docker e rodar Airflow (porta 8080 apenas interno)

# 3. Criar túnel SSH (do seu computador)
ssh -i ~/.ssh/your-key.pem -L 8080:localhost:8080 ec2-user@<IP-EC2>

# 4. Em outra janela, acessar
open http://localhost:8080
```

**Vantagens**:
- ✅ **Seguro** (sem exposição pública)
- ✅ Gratuito (free tier)
- ✅ Usa ECR (aprende stack AWS)

**Desvantagens**:
- ❌ Apenas acesso local (via túnel)
- ⚠️ Requer chave SSH

---

### Opção 4: ECS Fargate + ALB 💰💰💰 **PRODUÇÃO (CUSTO ALTO)**

**Custo**: ~**$50-200/mês**

**Como funciona**:
- ECS Fargate roda containers do ECR
- Application Load Balancer (ALB) expõe a UI
- Link público com domínio

**Acesso**:
- ✅ **Link público**: `https://airflow.example.com`
- ✅ **HTTPS**: Suportado via ALB
- ✅ **Autenticação**: Integrada no ALB

**Vantagens**:
- ✅ Alta disponibilidade
- ✅ Escalável
- ✅ Produção-ready

**Desvantagens**:
- ❌ **Custo alto** (~$50-200/mês)
- ❌ Complexo de configurar

**Para treinamento**: ❌ **NÃO recomendado** (custo alto)

---

## Recomendação para Treinamento

### **Estratégia Híbrida** ⭐

1. **Desenvolvimento**: Local (Docker Compose) → `http://localhost:8080` → **$0**
2. **Demonstração/Compartilhamento**: EC2 com IP público → `http://<IP>:8080` → **~$5-10/mês**
3. **Treinamento em equipe**: EC2 com SSH Tunnel → Acesso seguro → **~$5-10/mês**

### Configuração Recomendada para EC2 (Demonstração)

```bash
# 1. Criar instância EC2 t2.micro (free tier elegível)
# 2. Instalar Docker e Docker Compose
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Autenticar no ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# 4. Configurar docker-compose.yml para usar imagem do ECR
# Editar docker-compose.yml:
#   airflow-webserver:
#     image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/dataflow-airflow:latest
#     ports:
#       - "8080:8080"

# 5. Iniciar
docker-compose up -d

# 6. Configurar Security Group
# Permitir porta 8080 de 0.0.0.0/0 (⚠️ apenas para treinamento!)

# 7. Acessar
http://<IP-PUBLICO-EC2>:8080
```

### Link Específico com Elastic IP

Para ter um **link fixo** que não muda:

```bash
# 1. Alocar Elastic IP
aws ec2 allocate-address --domain vpc

# 2. Associar ao EC2
aws ec2 associate-address \
  --instance-id i-xxxxxxxxx \
  --allocation-id eipalloc-xxxxxxxxx

# 3. Agora você tem um IP fixo
# Link: http://<ELASTIC-IP>:8080

# 4. (Opcional) Configurar Route 53 para domínio
# Se tiver domínio: airflow.training.com → <ELASTIC-IP>
```

---

## Segurança para Acesso Público

### ⚠️ **IMPORTANTE**: Não exponha Airflow sem proteção!

**Riscos**:
- ❌ Qualquer um pode acessar seus dados
- ❌ Pode executar DAGs sem autorização
- ❌ Exposição de credenciais/secrets

**Proteções**:
1. **Autenticação do Airflow** (usuário/senha) ✅ Já tem (admin/admin)
2. **IP Whitelist** no Security Group (só permitir IPs conhecidos)
3. **AWS VPN** ou **SSH Tunnel** (acesso via túnel)
4. **ALB com autenticação** (para produção)

**Exemplo: Whitelist de IP**:
```bash
# Permitir apenas IPs específicos
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxxxxxx \
  --protocol tcp \
  --port 8080 \
  --cidr <SEU-IP>/32  # Apenas seu IP
```

---

## Resumo

| Opção | Custo | Link Público | Segurança | Para Treinamento |
|-------|-------|--------------|-----------|------------------|
| **Local** | $0 | ❌ | ✅ | ⭐⭐ Melhor |
| **EC2 Público** | ~$5-10/mês | ✅ | ⚠️ | ⭐⭐⭐ Ideal |
| **EC2 SSH Tunnel** | ~$5-10/mês | ❌ | ✅✅ | ⭐⭐ Bom |
| **ECS + ALB** | ~$50-200/mês | ✅ | ✅✅ | ❌ Caro demais |

**Para seu projeto de treinamento**: Use **EC2 com IP público** para demonstrar, mas configure **autenticação do Airflow** e **whitelist de IPs** quando possível.
