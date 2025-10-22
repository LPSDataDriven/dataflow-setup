# 🚀 Guia de Configuração AWS para Airflow Local

## 📋 Credenciais Necessárias

### 1. **Credenciais AWS (Obrigatórias)**

Você precisa de:
- **AWS Access Key ID**
- **AWS Secret Access Key**
- **Região AWS** (ex: us-east-1)

**Como obter:**
1. Acesse o AWS Console → IAM → Users
2. Selecione seu usuário → Security credentials
3. Clique em "Create access key"
4. Escolha "Application running outside AWS"
5. Copie as credenciais geradas

### 2. **Configurações S3**

- **S3 Bucket Name**: Nome do bucket para armazenar artifacts e logs

### 3. **Credenciais Snowflake (Opcional)**

- **Account**: Seu account Snowflake
- **User/Password**: Credenciais de acesso
- **Warehouse/Database/Schema**: Configurações do ambiente

## 🔧 Como Configurar

### Passo 1: Criar arquivo .env

```bash
# Copie o arquivo de exemplo
cp env.example .env

# Edite com suas credenciais
nano .env
```

### Passo 2: Preencher credenciais essenciais

```bash
# Mínimo necessário para testar
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=lpsdata-airflow-1
```

### Passo 3: Credenciais Snowflake (se usando)

```bash
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=your-warehouse
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=your-schema
SNOWFLAKE_ROLE=your-role
```

## 🧪 Como Testar

### 1. **Teste de Conexão AWS**
```bash
# Execute o script de teste
python aws/test_aws_connection.py
```

### 2. **Verificações Automáticas**
O script testa:
- ✅ **Credenciais AWS**: Se estão válidas
- ✅ **Bucket S3**: Se existe e é acessível
- ✅ **Docker**: Se está disponível para Airflow local
- ✅ **Secrets Manager**: Se tem acesso (opcional)

### 3. **Exemplo de Saída**
```
🚀 Teste de Conexão AWS para Airflow Local

📍 Região AWS: us-east-1
🪣 Bucket S3: lpsdata-airflow-1
--------------------------------------------------
🔍 Testando credenciais AWS...
✅ Credenciais válidas!
   Account ID: 123456789012
   User ARN: arn:aws:iam::123456789012:user/your-user
   User ID: AIDACKCEVSQ6C2EXAMPLE

🪣 Testando acesso ao bucket S3: lpsdata-airflow-1
✅ Bucket 'lpsdata-airflow-1' acessível!
   Objetos encontrados: 3
   - dags/dbt_pipeline.py
   - logs/airflow.log
   - artifacts/manifest.json

🐳 Testando disponibilidade do Docker...
✅ Docker disponível!
   Versão: Docker version 24.0.7, build afdd53b

🔐 Testando AWS Secrets Manager...
✅ Secrets Manager acessível!
   Secrets encontrados: 2
   - snowflake-credentials
   - airflow-variables

==================================================
✅ Teste de conexão concluído!
```

## 🚨 Troubleshooting

### Erro: "AWS credentials not found"
**Solução:**
1. Verifique se o arquivo `.env` existe
2. Confirme se as variáveis estão corretas
3. Execute `source .env` ou use `direnv`

### Erro: "S3 bucket not found"
**Solução:**
1. Verifique se o bucket existe no AWS Console
2. Confirme se o nome está correto no `.env`
3. Verifique permissões IAM

### Erro: "Docker not found"
**Solução:**
1. Instale o Docker Desktop
2. Inicie o Docker daemon
3. Verifique se está rodando: `docker --version`

### Erro: "Permission denied"
**Solução:**
1. Verifique as permissões IAM do usuário
2. Confirme se tem acesso ao S3 e Secrets Manager
3. Teste com `aws s3 ls` no terminal

## 🔐 Permissões IAM Necessárias

### Política Mínima para S3:
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
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

### Política para Secrets Manager (Opcional):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:*"
        }
    ]
}
```

## 🎯 Próximos Passos

1. **Configure** as credenciais no `.env`
2. **Execute** o teste de conexão
3. **Inicie** o Airflow local com Docker
4. **Teste** o pipeline completo

---

**Nota**: Este guia foca em execução local para reduzir custos. Para ambientes de produção, considere soluções gerenciadas como ECS, EKS ou outras plataformas de container.
