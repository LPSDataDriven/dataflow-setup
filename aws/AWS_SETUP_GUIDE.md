# 🚀 Guia de Configuração AWS para MWAA

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

### 2. **Configurações MWAA**

- **S3 Bucket Name**: Nome do bucket para o Airflow
- **MWAA Environment Name**: Nome do ambiente MWAA criado

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
MWAA_ENVIRONMENT_NAME=seu-ambiente-mwaa
```

### Passo 3: Testar conexão

```bash
# Instalar dependências
uv sync

# Executar teste de conexão
python test_aws_connection.py
```

## ✅ O que o teste verifica

1. **Credenciais AWS**: Se estão válidas e funcionando
2. **Acesso S3**: Se consegue acessar o bucket do Airflow
3. **Ambiente MWAA**: Se o ambiente existe e está acessível
4. **Secrets Manager**: Se tem permissão para acessar secrets

## 🔐 Permissões IAM Necessárias

Seu usuário AWS precisa das seguintes permissões:

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
                "mwaa:GetEnvironment",
                "mwaa:ListEnvironments"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue",
                "secretsmanager:ListSecrets"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🚨 Troubleshooting

### Erro: "NoCredentialsError"
- Verifique se AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY estão corretos
- Confirme se as credenciais não expiraram

### Erro: "Access Denied" no S3
- Verifique se o bucket existe
- Confirme se seu usuário tem permissão de acesso ao bucket

### Erro: "MWAA Environment not found"
- Verifique se o nome do ambiente está correto
- Confirme se o ambiente está na região correta

## 📞 Próximos Passos

Após configurar as credenciais:

1. **Teste a conexão**: `python test_aws_connection.py`
2. **Configure o MWAA**: Siga o guia em `airflow-mwaa/README_MWAA_DEPLOYMENT.md`
3. **Deploy dos DAGs**: Use o script `airflow-mwaa/deploy.sh`
4. **Teste os pipelines**: Execute os DAGs no MWAA
