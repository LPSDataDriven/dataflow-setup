# Fluxo de Dados - Market Data Exports (DataAI → Salesforce)

Diagrama simplificado do pipeline de Market Data que alimenta o Salesforce com relatórios baseados em dados do DataAI, utilizando dados existentes do Salesforce para limitar as saídas.

## Diagrama Principal

```mermaid
flowchart TB
    subgraph FONTES["📥 Fontes de Dados"]
        DATAAI[(DataAI<br/>• Apps / Companies / Publishers<br/>• Performance Metrics<br/>• Share of Voice)]
        SF[(Salesforce<br/>• Account<br/>• App__c<br/>• Company/Publisher IDs)]
    end

    subgraph MAPEAMENTOS["🔗 Mapeamentos SF → DataAI"]
        SF_ACCOUNTS["int_sfdc__account_with_region"]
        SF_COMPANIES["Account → Company<br/>app_annie_company_id__c"]
        SF_PUBLISHERS["Account → Publisher<br/>app_annie_publisher_id / app_store_publisher_id"]
        SF_APPS["stg_salesforce_polytomic__apps<br/>market_id ↔ app_id__c"]
    end

    subgraph DATAAI_PROC["📊 Processamento DataAI"]
        APPS_ENRICHED["dim_dataai__apps_filtered_enriched<br/>Apps + SF App join"]
        APPS_FILTERED["int_dataai__apps_filtered<br/>Apps mensais com métricas"]
        ADPLATFORM["int_app_adplatform_country_filtered<br/>estimated_spend, est_downloads<br/>por app/country/platform"]
    end

    subgraph DECISAO_NEW_APPS["❓ Lógica: New Apps Export"]
        direction TB
        Q1{"App já existe<br/>no Salesforce?"}
        Q2{"Company ou Publisher<br/>mapeado para SF Account?"}
        FILTER_NEW["Filtro: salesforce_app_id IS NULL<br/>+ company_key OU publisher_key"]
    end

    subgraph DECISAO_METRICS["❓ Lógica: Estimated Spend & Downloads"]
        direction TB
        Q3{"App tem match<br/>no Salesforce?"}
        Q4{"Ad Platform no picklist SF?<br/>apenas Estimated Spend"}
    end

    subgraph EXPORTS["📤 Exports para Salesforce"]
        EXP_NEW["dim_new_apps_export<br/>Novos apps para criar"]
        EXP_SPEND["dim_estimated_spend_export<br/>Gasto estimado por país"]
        EXP_DOWN["dim_total_downloads_export<br/>Downloads por país"]
    end

    %% Conexões Fontes
    DATAAI --> APPS_ENRICHED
    DATAAI --> APPS_FILTERED
    DATAAI --> ADPLATFORM
    SF --> SF_ACCOUNTS
    SF --> SF_APPS
    SF_ACCOUNTS --> SF_COMPANIES
    SF_ACCOUNTS --> SF_PUBLISHERS
    SF_APPS --> APPS_ENRICHED

    %% Fluxo New Apps: apps NÃO no SF, mas com Account match
    APPS_FILTERED --> Q1
    Q1 -->|"NÃO"| FILTER_NEW
    FILTER_NEW --> Q2
    Q2 -->|"SIM"| EXP_NEW
    SF_COMPANIES --> Q2
    SF_PUBLISHERS --> Q2

    %% Fluxo Estimated Spend: apps NO SF + Ad Platform válido
    ADPLATFORM --> APPS_ENRICHED
    APPS_ENRICHED --> Q3
    Q3 -->|"SIM"| Q4
    Q4 --> EXP_SPEND

    %% Fluxo Total Downloads: apps NO SF
    ADPLATFORM --> APPS_ENRICHED
    APPS_ENRICHED --> Q3
    Q3 -->|"SIM"| EXP_DOWN
```

## Diagrama Simplificado (Visão de Decisão)

Versão focada apenas na lógica de decisão e critérios de filtro:

```mermaid
flowchart LR
    subgraph ENTRADA["Dados DataAI"]
        APPS[Apps]
        METRICS[Métricas<br/>Spend / Downloads]
    end

    subgraph CRITERIOS["Critérios de Filtro (Salesforce)"]
        C1["✓ Account com Company ID"]
        C2["✓ Account com Publisher ID"]
        C3["✓ App existe no SF"]
        C4["✓ Ad Platform no picklist"]
    end

    subgraph SAIDAS["Saída"]
        NEW["New Apps<br/>Apps NÃO no SF<br/>mas com Account match"]
        SPEND["Estimated Spend<br/>Apps no SF<br/>+ Ad Platform válido"]
        DOWN["Total Downloads<br/>Apps no SF"]
    end

    APPS --> NEW
    APPS --> SPEND
    APPS --> DOWN
    METRICS --> SPEND
    METRICS --> DOWN

    C1 -.->|"obrigatório para New Apps"| NEW
    C2 -.->|"obrigatório para New Apps"| NEW
    C3 -.->|"obrigatório para Spend/Down"| SPEND
    C3 -.->|"obrigatório para Spend/Down"| DOWN
    C4 -.->|"obrigatório para Spend"| SPEND
```

## Resumo da Lógica por Export

| Export | Condição Principal | Objetivo |
|--------|-------------------|----------|
| **dim_new_apps_export** | `salesforce_app_id IS NULL` + Company ou Publisher mapeado para SF Account | Descobrir apps novos que pertencem a contas existentes no Salesforce |
| **dim_estimated_spend_export** | `app_id IS NOT NULL` + Ad Platform no picklist SF + `estimated_spend > 0` | Relatório de gasto estimado por app/country para apps já no Salesforce |
| **dim_total_downloads_export** | `app_id IS NOT NULL` | Relatório de downloads por app/country para apps já no Salesforce |

## Dependências Principais

```
DataAI (stg_dataai__*, int_dataai__*)
    ↓
dim_dataai__apps_filtered_enriched ←── join com stg_salesforce_polytomic__apps
    ↓
int_app_adplatform_country_filtered (reporting_month)
    ↓
┌─────────────────────────────────────────────────────────────┐
│  int_dataai__apps_filtered (salesforce_app_id IS NULL)      │
│       + int_sfdc__account_to_dataai_company_relationships   │
│       + int_sfdc__account_to_dataai_publisher_relationships │
│       → dim_new_apps_export                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  int_app_adplatform_country_filtered                        │
│       + dim_dataai__apps_filtered_enriched (app_id match)    │
│       + int_ios_android_adplatform_stats (picklist)         │
│       → dim_estimated_spend_export / dim_total_downloads_export │
└─────────────────────────────────────────────────────────────┘
```
