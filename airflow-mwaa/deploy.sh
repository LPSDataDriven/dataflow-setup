#!/bin/bash

# Script de deployment para AWS MWAA
# Uso: ./deploy.sh <bucket-name> [environment-name]

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Verificar parâmetros
if [ $# -lt 1 ]; then
    error "Uso: $0 <bucket-name> [environment-name]"
    echo "Exemplo: $0 my-airflow-bucket my-mwaa-environment"
    exit 1
fi

BUCKET_NAME=$1
ENVIRONMENT_NAME=${2:-""}

log "Iniciando deployment para AWS MWAA"
log "Bucket: $BUCKET_NAME"
if [ -n "$ENVIRONMENT_NAME" ]; then
    log "Environment: $ENVIRONMENT_NAME"
fi

# Verificar se AWS CLI está configurado
if ! command -v aws &> /dev/null; then
    error "AWS CLI não encontrado. Instale e configure o AWS CLI primeiro."
    exit 1
fi

# Verificar se o bucket existe
log "Verificando se o bucket $BUCKET_NAME existe..."
if ! aws s3 ls "s3://$BUCKET_NAME" &> /dev/null; then
    error "Bucket $BUCKET_NAME não encontrado ou sem permissão de acesso."
    exit 1
fi

success "Bucket encontrado!"

# Criar estrutura de diretórios no S3 se não existir
log "Criando estrutura de diretórios no S3..."
aws s3api put-object --bucket "$BUCKET_NAME" --key "dags/" --content-length 0 || true
aws s3api put-object --bucket "$BUCKET_NAME" --key "plugins/" --content-length 0 || true
aws s3api put-object --bucket "$BUCKET_NAME" --key "requirements/" --content-length 0 || true

# Upload dos DAGs
log "Fazendo upload dos DAGs..."
if [ -d "dags" ]; then
    aws s3 sync ./dags/ "s3://$BUCKET_NAME/dags/" --delete
    success "DAGs enviados com sucesso!"
else
    warning "Diretório 'dags' não encontrado. Pulando upload de DAGs."
fi

# Upload dos requirements
log "Fazendo upload dos requirements..."
if [ -f "requirements/requirements.txt" ]; then
    aws s3 cp ./requirements/requirements.txt "s3://$BUCKET_NAME/requirements/requirements.txt"
    success "Requirements enviados com sucesso!"
else
    warning "Arquivo 'requirements/requirements.txt' não encontrado. Pulando upload de requirements."
fi

# Upload dos plugins (se existirem)
log "Fazendo upload dos plugins..."
if [ -d "plugins" ] && [ "$(ls -A plugins)" ]; then
    aws s3 sync ./plugins/ "s3://$BUCKET_NAME/plugins/" --delete
    success "Plugins enviados com sucesso!"
else
    log "Nenhum plugin encontrado. Pulando upload de plugins."
fi

# Verificar se o environment existe e reiniciar se necessário
if [ -n "$ENVIRONMENT_NAME" ]; then
    log "Verificando se o environment $ENVIRONMENT_NAME existe..."
    if aws mwaa get-environment --name "$ENVIRONMENT_NAME" &> /dev/null; then
        success "Environment encontrado!"

        # Perguntar se deve reiniciar o environment
        echo -e "${YELLOW}Deseja reiniciar o environment $ENVIRONMENT_NAME para aplicar as mudanças? (y/N)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            log "Reiniciando environment $ENVIRONMENT_NAME..."
            aws mwaa update-environment --name "$ENVIRONMENT_NAME" --requirements-s3-path "s3://$BUCKET_NAME/requirements/requirements.txt"
            success "Environment reiniciado! Aguarde alguns minutos para que as mudanças sejam aplicadas."
        else
            log "Environment não foi reiniciado. As mudanças serão aplicadas na próxima reinicialização."
        fi
    else
        warning "Environment $ENVIRONMENT_NAME não encontrado. Verifique o nome do environment."
    fi
fi

# Mostrar informações úteis
echo ""
success "Deployment concluído!"
echo ""
log "Próximos passos:"
echo "1. Acesse o Airflow UI do MWAA"
echo "2. Configure as variáveis necessárias:"
echo "   - dbt_project_dir: /opt/airflow/dbt_project"
echo "   - dbt_profiles_dir: /opt/airflow/.dbt"
echo "   - dbt_target: dev"
echo "3. Verifique se os DAGs aparecem na interface"
echo "4. Execute um teste manual dos DAGs"
echo ""

if [ -n "$ENVIRONMENT_NAME" ]; then
    log "Para acessar o Airflow UI:"
    echo "aws mwaa get-environment --name $ENVIRONMENT_NAME --query 'Environment.WebserverUrl' --output text"
fi

log "Para verificar o status do environment:"
echo "aws mwaa get-environment --name $ENVIRONMENT_NAME --query 'Environment.Status' --output text"
