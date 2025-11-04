#!/bin/bash
# Script para build e push da imagem Docker para AWS ECR
# Uso: ./airflow/build-ecr.sh [tag]

set -e

# Configurações (usando variáveis de ambiente)
AWS_REGION="${AWS_REGION}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
ECR_REPO_NAME="${ECR_REPO_NAME}"
TAG="${1:-latest}"

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
IMAGE_NAME="${ECR_REPOSITORY}:${TAG}"

# Mostrar configurações
echo "📋 Configurações:"
echo "   AWS_REGION: ${AWS_REGION}"
echo "   AWS_ACCOUNT_ID: ${AWS_ACCOUNT_ID}"
echo "   ECR_REPO_NAME: ${ECR_REPO_NAME}"
echo "   TAG: ${TAG}"
echo ""

# Verificar se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Erro: Docker não está instalado"
    echo "Instale com: https://docs.docker.com/get-docker/"
    exit 1
fi

echo "🔨 Building Docker image..."
docker build -f airflow/Dockerfile -t ${ECR_REPO_NAME}:${TAG} -t ${IMAGE_NAME} .

echo "🔐 Autenticando no ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

echo "📤 Pushing image to ECR..."
docker push ${IMAGE_NAME}

echo ""
echo "✅ Image pushed successfully!"
echo "   Repository: ${ECR_REPOSITORY}"
echo "   Tag: ${TAG}"
echo ""
echo "Para usar esta imagem:"
echo "   docker pull ${IMAGE_NAME}"
