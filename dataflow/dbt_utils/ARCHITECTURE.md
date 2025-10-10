# dbt Utils — Arquitetura

Este documento descreve, em alto nível, a organização e as principais responsabilidades do módulo `dataflow/dbt_utils`.

## Objetivo
Fornecer utilitários mínimos para executar operações do dbt Core (e integração básica com dbt Cloud) a partir de Python, com foco em simplicidade e integração com orquestradores (ex.: Airflow).

## Estrutura
```
dataflow/
├── dbt_utils/
│   ├── connector.py     # Operações principais (core + cloud)
│   ├── README.md        # Guia de uso
│   └── ARCHITECTURE.md  # Este documento
└── dbt_usage/
    └── dbt_test.py      # Exemplo de execução via módulo
```

## Componentes

### 1) Conector (`connector.py`)
Responsável por encapsular chamadas ao dbt Core/CLI e, opcionalmente, à API do dbt Cloud. Principais elementos (nomes podem variar conforme evolução):

- Configurações:
  - `DbtRunConfig`, `DbtTestConfig` — estruturas de configuração das execuções.
- Execuções dbt Core:
  - `run_dbt_build`, `run_dbt_run`, `run_dbt_test`, `run_dbt_seed`, etc.
  - `run_full_dbt_pipeline` — orquestra uma sequência comum (ex.: build + test + docs).
- Utilitários:
  - `validate_dbt_project` — verificação rápida da estrutura do projeto.
  - `get_dbt_project_info`, `cleanup_dbt_artifacts` — funções auxiliares.
- Integração dbt Cloud (opcional):
  - `DbtCloudClient`, `trigger_dbt_cloud_job`, `wait_for_dbt_cloud_job`.

### 2) Exemplo de uso (`dataflow/dbt_usage/dbt_test.py`)
Script curto para demonstrar a execução via `python -m dataflow.dbt_usage.dbt_test`, executando uma operação simples (ex.: `build`) com `DbtRunConfig`.

## Fluxo de Execução (dbt Core)
1. Construção da configuração (`DbtRunConfig`) com `project_dir`, `target`, e filtros (`select`/`exclude`) quando necessário.
2. Execução do comando desejado (`run_dbt_build`, `run_dbt_run`, etc.).
3. Leitura do resultado (status, logs/artefatos se aplicável) e tratamento de erros.

## Convenções
- Imports devem usar o caminho completo a partir da raiz do projeto, ex.:
  ```python
  from dataflow.dbt_utils.connector import DbtRunConfig, run_dbt_build
  ```
- Execução como módulo a partir da raiz do repositório:
  ```bash
  python -m dataflow.dbt_usage.dbt_test
  ```
- Caminhos: prefira absolutos ou derive a partir do local do arquivo quando integrar com orquestradores.

## Decisões de Design
- Mantido intencionalmente enxuto: sem camadas extras de configuração/monitoramento para reduzir acoplamento e facilitar reutilização.
- Logs: foco em mensagens claras; detalhes avançados podem ser adicionados via `DEBUG`.
- Compatibilidade: o módulo não depende de frameworks específicos; pode ser chamado de qualquer ambiente Python.

## Evolução
- Adicionar tipagem e validações mais estritas conforme necessário.
- Expandir integrações do dbt Cloud de forma opcional, mantendo o núcleo simples.
