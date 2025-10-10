# dbt Utils - Utilitários mínimos para dbt

Módulo leve com funções úteis do dbt Core e integração básica com dbt Cloud. Ideal para usar em orquestradores como Airflow.

## Estrutura
```
dataflow/
├── dbt_utils/
│   ├── connector.py   # Operações principais (core + cloud)
│   └── README.md
└── dbt_usage/
    └── dbt_test.py    # Exemplo de uso via módulo
```

## Instalação
Dependências principais:
```bash
pip install dbt-core dbt-snowflake requests
```

## Uso básico
```python
from dataflow.dbt_utils.connector import DbtRunConfig, run_dbt_build

config = DbtRunConfig(project_dir="./my_dbt_project/", target="dev")
result = run_dbt_build(config)
print(result.success)
```

### Pipeline completo
```python
from dataflow.dbt_utils.connector import (
    DbtRunConfig, DbtTestConfig, run_full_dbt_pipeline
)

config = DbtRunConfig(project_dir="./my_dbt_project/", target="dev")
test_cfg = DbtTestConfig(store_failures=True, fail_fast=False)
results = run_full_dbt_pipeline(config, test_cfg, include_docs=False)
print(results.keys())
```

### Validação rápida
```python
from dataflow.dbt_utils.connector import validate_dbt_project
print(validate_dbt_project("./my_dbt_project/"))
```

## Execução via módulo
No diretório raiz do projeto:
```bash
python -m dataflow.dbt_usage.dbt_test
```

## Notas
- Caminhos relativos são resolvidos a partir do diretório onde o processo é executado. Use caminhos absolutos ou derive com `Path(__file__).parents[...]` ao integrar com outros sistemas.
