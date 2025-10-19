#!/usr/bin/env python3
"""
Script para testar conexão com AWS e verificar configurações
"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

def test_aws_credentials(region='us-east-1'):
    """Testa se as credenciais AWS estão configuradas corretamente"""
    print("🔍 Testando credenciais AWS...")

    try:
        # Testa credenciais básicas
        sts = boto3.client('sts', region_name=region)
        identity = sts.get_caller_identity()

        print(f"✅ Credenciais válidas!")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN: {identity['Arn']}")
        print(f"   User ID: {identity['UserId']}")
        return True

    except NoCredentialsError:
        print("❌ Credenciais AWS não encontradas!")
        print("   Configure AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY")
        return False
    except ClientError as e:
        print(f"❌ Erro de autenticação: {e}")
        return False

def test_s3_access(bucket_name, region='us-east-1'):
    """Testa acesso ao bucket S3"""
    print(f"\n🪣 Testando acesso ao bucket S3: {bucket_name}")

    try:
        s3 = boto3.client('s3', region_name=region)

        # Testa se o bucket existe e é acessível
        s3.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket '{bucket_name}' acessível!")

        # Lista objetos no bucket
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
        if 'Contents' in response:
            print(f"   Objetos encontrados: {len(response['Contents'])}")
            for obj in response['Contents'][:3]:
                print(f"   - {obj['Key']}")
        else:
            print("   Bucket vazio")

        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f"❌ Bucket '{bucket_name}' não encontrado!")
        elif error_code == '403':
            print(f"❌ Sem permissão para acessar bucket '{bucket_name}'!")
        else:
            print(f"❌ Erro ao acessar bucket: {e}")
        return False

def test_docker_availability():
    """Testa se o Docker está disponível para execução local"""
    print(f"\n🐳 Testando disponibilidade do Docker...")

    try:
        import subprocess
        result = subprocess.run(['docker', '--version'],
                              capture_output=True, text=True, check=True)
        print(f"✅ Docker disponível!")
        print(f"   Versão: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ Docker não encontrado!")
        print(f"   Instale o Docker para execução local do Airflow")
        return False

def test_secrets_manager(region='us-east-1'):
    """Testa acesso ao AWS Secrets Manager"""
    print(f"\n🔐 Testando AWS Secrets Manager...")

    try:
        secrets = boto3.client('secretsmanager', region_name=region)

        # Lista secrets (limitado a 5)
        response = secrets.list_secrets(MaxResults=5)

        if response['SecretList']:
            print(f"✅ Secrets Manager acessível!")
            print(f"   Secrets encontrados: {len(response['SecretList'])}")
            for secret in response['SecretList'][:3]:
                print(f"   - {secret['Name']}")
        else:
            print("✅ Secrets Manager acessível (sem secrets)")

        return True

    except ClientError as e:
        print(f"❌ Erro ao acessar Secrets Manager: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 Teste de Conexão AWS para Airflow Local\n")

    # Carrega variáveis de ambiente
    load_dotenv()

    # Configurações do arquivo .env
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    s3_bucket = os.getenv('S3_BUCKET_NAME')

    print(f"📍 Região AWS: {aws_region}")
    print(f"🪣 Bucket S3: {s3_bucket}")
    print("-" * 50)

    # Testa credenciais
    if not test_aws_credentials(aws_region):
        print("\n❌ Falha na autenticação. Verifique suas credenciais AWS.")
        return

    # Testa S3 se bucket foi especificado
    if s3_bucket:
        test_s3_access(s3_bucket, aws_region)
    else:
        print("\n⚠️  S3_BUCKET_NAME não configurado no .env")

    # Testa Docker para execução local
    test_docker_availability()

    # Testa Secrets Manager
    test_secrets_manager(aws_region)

    print("\n" + "=" * 50)
    print("✅ Teste de conexão concluído!")

if __name__ == "__main__":
    main()
