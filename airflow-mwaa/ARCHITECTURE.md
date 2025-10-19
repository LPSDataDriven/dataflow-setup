# Arquitetura AWS MWAA + DBT

## Visão Geral

Este projeto implementa uma arquitetura híbrida que permite usar tanto Airflow local (Docker) quanto AWS MWAA (Managed Workflows for Apache Airflow) para executar pipelines DBT.

## Arquitetura Atual

```
┌─────────────────────────────────────────────────────────────────┐
│                    AMBIENTE LOCAL (Docker)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Airflow   │    │  PostgreSQL │    │    DBT      │        │
│  │  Webserver  │    │  Database   │    │  Project    │        │
│  │  Scheduler  │    │             │    │             │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                   │                   │              │
│         └───────────────────┼───────────────────┘              │
│                             │                                  │
│  ┌─────────────────────────┴─────────────────────────────────┐ │
│  │              Docker Compose Network                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ (Desenvolvimento/Teste)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AMBIENTE AWS MWAA                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   MWAA      │    │     S3      │    │  Secrets    │        │
│  │ Environment │    │   Bucket    │    │  Manager    │        │
│  │             │    │             │    │             │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│         │                   │                   │              │
│         └───────────────────┼───────────────────┘              │
│                             │                                  │
│  ┌─────────────────────────┴─────────────────────────────────┐ │
│  │              VPC + Security Groups                       │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ (Produção)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DESTINOS DE DADOS                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │ Snowflake   │    │   Outros    │    │   AWS       │        │
│  │  Warehouse  │    │  Databases  │    │ Services    │        │
│  │             │    │             │    │             │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes

### 1. Ambiente Local (Docker)
- **Airflow**: Webserver + Scheduler em containers
- **PostgreSQL**: Banco de dados para metadados do Airflow
- **DBT Project**: Projeto DBT montado como volume
- **Uso**: Desenvolvimento, testes, debugging

### 2. Ambiente AWS MWAA
- **MWAA Environment**: Airflow gerenciado pela AWS
- **S3 Bucket**: Armazenamento de DAGs, plugins e requirements
- **Secrets Manager**: Credenciais sensíveis
- **VPC**: Isolamento de rede
- **Uso**: Produção, execução escalável

### 3. Destinos de Dados
- **Snowflake**: Data warehouse principal
- **Outros Databases**: Conectores adicionais
- **AWS Services**: Integração com serviços AWS

## Fluxo de Dados

### Desenvolvimento Local:
1. Desenvolver DAGs no ambiente Docker
2. Testar pipelines localmente
3. Validar conectividade com destinos
4. Commit das mudanças

### Deploy para Produção:
1. Upload de DAGs para S3
2. Configuração de variáveis no MWAA
3. Execução de pipelines no ambiente gerenciado
4. Monitoramento via CloudWatch

## Estrutura de Arquivos

```
dataflow-setup/
├── airflow/                    # Ambiente local (Docker)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── dags/
│       ├── dbt_main_pipeline.py
│       └── full_main_pipeline.py
├── airflow-mwaa/              # Ambiente AWS MWAA
│   ├── dags/
│   │   ├── dbt_main_pipeline_mwaa.py
│   │   └── full_main_pipeline_mwaa.py
│   ├── requirements/
│   │   └── requirements.txt
│   ├── plugins/
│   ├── deploy.sh
│   ├── config.env.example
│   ├── README_MWAA_DEPLOYMENT.md
│   └── ARCHITECTURE.md
├── my_dbt_project/            # Projeto DBT compartilhado
├── .dbt/                      # Profiles DBT
└── docker-compose.yml         # Orquestração local
```

## Vantagens da Arquitetura Híbrida

### Ambiente Local:
- ✅ Desenvolvimento rápido
- ✅ Debugging fácil
- ✅ Testes sem custo
- ✅ Controle total do ambiente

### Ambiente MWAA:
- ✅ Escalabilidade automática
- ✅ Alta disponibilidade
- ✅ Integração nativa com AWS
- ✅ Monitoramento avançado
- ✅ Segurança gerenciada

## Considerações de Segurança

### Ambiente Local:
- Credenciais em variáveis de ambiente
- Rede isolada via Docker
- Acesso local apenas

### Ambiente MWAA:
- Credenciais no Secrets Manager
- VPC com Security Groups
- IAM roles com princípio de menor privilégio
- Logs centralizados no CloudWatch

## Monitoramento

### Métricas Importantes:
- **DAG Success Rate**: Taxa de sucesso dos pipelines
- **Task Duration**: Tempo de execução das tasks
- **Resource Utilization**: Uso de CPU/memória
- **Error Rate**: Taxa de erros

### Alertas Recomendados:
- Falha de DAGs críticos
- Tempo de execução excessivo
- Falhas de conectividade
- Uso excessivo de recursos

## Custos

### Ambiente Local:
- Apenas custos de infraestrutura local
- Sem custos adicionais de cloud

### Ambiente MWAA:
- Custo base do MWAA (por hora)
- Custo de S3 (armazenamento)
- Custo de Secrets Manager
- Custo de CloudWatch Logs

## Próximos Passos

1. **Configurar MWAA**: Seguir o guia de deployment
2. **Testar Conectividade**: Validar conexões com destinos
3. **Configurar Monitoramento**: Alertas e dashboards
4. **Otimizar Performance**: Ajustar configurações
5. **Implementar CI/CD**: Automação de deployment

## Troubleshooting

### Problemas Comuns:
1. **DAGs não aparecem**: Verificar S3 e sintaxe
2. **Erro de dependências**: Verificar requirements.txt
3. **Falha de conectividade**: Verificar VPC e Security Groups
4. **Performance lenta**: Verificar recursos e configurações

### Logs Importantes:
- **Airflow UI**: Logs de tasks
- **CloudWatch**: Logs do scheduler e webserver
- **S3**: Arquivos de log do DBT
