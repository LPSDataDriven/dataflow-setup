#!/bin/bash
# Script para criar repositório ECR na AWS (se não existir)
# Uso: ./airflow/setup-ecr.sh

set -e

# Configurações (usando variáveis de ambiente)
AWS_REGION="${AWS_REGION}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
ECR_REPO_NAME="${ECR_REPO_NAME}"

# Verificar se AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo "❌ Erro: AWS CLI não está instalado"
    echo "Instale com: https://aws.amazon.com/cli/"
    exit 1
fi

# Verificar credenciais AWS
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Erro: Credenciais AWS não configuradas ou inválidas"
    echo "Configure com: aws configure"
    echo "Ou exporte: AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY"
    exit 1
fi

# Verificar se variáveis obrigatórias estão configuradas
if [ -z "$AWS_REGION" ]; then
    echo "❌ Erro: AWS_REGION não está configurado"
    echo "Configure com: export AWS_REGION=us-east-1"
    exit 1
fi

if [ -z "$ECR_REPO_NAME" ]; then
    echo "❌ Erro: ECR_REPO_NAME não está configurado"
    echo "Configure com: export ECR_REPO_NAME=dataflow-airflow"
    exit 1
fi

if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "🔍 AWS_ACCOUNT_ID não configurado, tentando obter automaticamente..."
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)

    if [ -z "$AWS_ACCOUNT_ID" ]; then
        echo "❌ Erro: Não foi possível obter AWS_ACCOUNT_ID"
        echo "Configure com: export AWS_ACCOUNT_ID=123456789012"
        exit 1
    fi

    echo "✅ AWS_ACCOUNT_ID obtido automaticamente: ${AWS_ACCOUNT_ID}"
fi

# Nome completo do repositório ECR
ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"

# Mostrar configurações
echo "📋 Configurações:"
echo "   AWS_REGION: ${AWS_REGION}"
echo "   AWS_ACCOUNT_ID: ${AWS_ACCOUNT_ID}"
echo "   ECR_REPO_NAME: ${ECR_REPO_NAME}"
echo ""

echo "🔍 Verificando se repositório ECR existe..."

# Verificar se o repositório já existe
if aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${AWS_REGION} &>/dev/null; then
    echo "✅ Repositório ECR '${ECR_REPO_NAME}' já existe"
else
    echo "📦 Criando repositório ECR '${ECR_REPO_NAME}'..."

    # Criar repositório e verificar se foi bem-sucedido
    if aws ecr create-repository \
        --repository-name ${ECR_REPO_NAME} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true \
        --encryption-configuration encryptionType=AES256 \
        --image-tag-mutability MUTABLE \
        --output none &>/dev/null; then
        echo "✅ Repositório ECR criado com sucesso!"
    else
        echo "❌ Erro ao criar repositório ECR"
        echo "Verifique suas credenciais AWS e permissões"
        exit 1
    fi
fi

echo ""
echo "📋 Informações do repositório:"
echo "   Nome: ${ECR_REPO_NAME}"
echo "   URI: ${ECR_REPOSITORY}"
echo "   Região: ${AWS_REGION}"
echo ""
echo "Para fazer build e push:"
echo "   ./airflow/build-ecr.sh [tag]"
