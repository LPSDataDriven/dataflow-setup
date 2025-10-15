# Snowflake Utils - Conector e utilitários para Snowflake

Módulo sob `dataflow/snowflake_utils/connector.py` com funções para conexão e operações no Snowflake (senha ou chave privada).

## Estrutura
```
dataflow/
├── snowflake_utils/
│   ├── connector.py    # Conector e operações (Core/Snowpark)
│   ├── README.md
│   └── ARCHITECTURE.md
└── snowflake_usage/
    └── snowflake_test.py  # Exemplo de uso via módulo
```

## 📋 Índice

- [Configuração](#configuração)
- [Fluxo de Funcionamento](#fluxo-de-funcionamento)
- [Funções Principais](#funções-principais)
- [Exemplos de Uso](#exemplos-de-uso)
- [Troubleshooting](#troubleshooting)

## ⚙️ Configuração

### Variáveis de Ambiente Necessárias

```bash
# Configurações obrigatórias
SNOWFLAKE_ACCOUNT=your_account.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema

# Método de autenticação (escolha um):
# Opção 1: Senha
SNOWFLAKE_PASSWORD=your_password

# Opção 2: Chave privada (arquivo)
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/your/private_key.pem
SNOWFLAKE_PRIVATE_KEY_PASSWORD=your_key_password

# Opção 3: Chave privada (base64)
SNOWFLAKE_PRIVATE_KEY=your_base64_encoded_key
SNOWFLAKE_PRIVATE_KEY_PASSWORD=your_key_password
```

## 🔄 Fluxo de Funcionamento 🏗️ Arquitetura das Funções

### Nível 1: Configuração e Autenticação
- `get_snowflake_credentials()` - Coleta e valida credenciais
- `get_snowflake_private_key()` - Processa chave privada
- `set_snowflake_private_key_decoded()` - Decorator para decodificação automática

### Nível 2: Conexão
- `get_snowflake_connection()` - Cria conexão direta
- `get_snowflake_connection_context()` - Context manager (recomendado)

### Nível 3: Operações
- `execute_query()` - Executa queries SQL
- `write_dataframe_to_snowflake()` - Escreve DataFrames
- `get_snowflake_session()` - Cria sessão Snowpark

### Nível 4: Utilitários
- `test_connection()` - Testa conectividade
- `get_current_*()` - Informações do ambiente

## 🚀 Funções Principais

### 1. Conexão Básica

```python
from dataflow.snowflake_utils.connector import get_snowflake_connection_context

# Usar context manager (recomendado)
with get_snowflake_connection_context() as conn:
    # Sua conexão está ativa aqui
    cursor = conn.cursor()
    cursor.execute("SELECT CURRENT_TIMESTAMP()")
    result = cursor.fetchone()
```

### 2. Executar Queries

```python
from dataflow.snowflake_utils.connector import execute_query

# Query simples
df = execute_query("SELECT * FROM my_table LIMIT 10")

# Query com parâmetros específicos
df = execute_query(
    "SELECT * FROM my_table WHERE date > %s",
    role="ANALYST_ROLE",
    warehouse="COMPUTE_WH"
)
```

### 3. Escrever DataFrames

```python
import pandas as pd
from dataflow.snowflake_utils.connector import write_dataframe_to_snowflake

# Criar DataFrame
df = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie']
})

# Escrever no Snowflake
success = write_dataframe_to_snowflake(
    df,
    'my_table',
    auto_create_table=True,
    overwrite=False
)
```

### 4. Sessão Snowpark

```python
from dataflow.snowflake_utils.connector import get_snowflake_session

# Criar sessão
session = get_snowflake_session()

# Operações Snowpark
df = session.create_dataframe([(1, "Alice"), (2, "Bob")], ["id", "name"])
df.write.mode("overwrite").save_as_table("my_table")

# Fechar sessão
session.close()
```

## 📊 Exemplos de Uso

### Exemplo 1: Pipeline de Dados Simples

```python
from dataflow.snowflake_utils.connector import execute_query, write_dataframe_to_snowflake
import pandas as pd

# 1. Ler dados
df_source = execute_query("SELECT * FROM source_table")

# 2. Transformar
df_transformed = df_source.groupby('category').agg({
    'value': 'sum',
    'count': 'count'
}).reset_index()

# 3. Escrever resultado
write_dataframe_to_snowflake(df_transformed, 'transformed_table')
```

### Exemplo 2: Monitoramento de Performance

```python
from dataflow.snowflake_utils.connector import execute_query

# Verificar queries recentes
queries = execute_query("""
    SELECT
        QUERY_ID,
        QUERY_TEXT,
        START_TIME,
        TOTAL_ELAPSED_TIME,
        STATUS
    FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
    WHERE START_TIME >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
    ORDER BY START_TIME DESC
    LIMIT 10
""")

print(f"Executadas {len(queries)} queries na última hora")
```

### Exemplo 3: Backup de Tabela

```python
from dataflow.snowflake_utils.connector import execute_query

# Criar backup
execute_query("""
    CREATE OR REPLACE TABLE my_table_backup AS
    SELECT * FROM my_table
""")

print("Backup criado com sucesso")
```

## 🔧 Troubleshooting

### Erro: "Chave privada não configurada"

**Causa**: Variáveis de ambiente não configuradas corretamente.

**Solução**:
```bash
# Verificar se as variáveis estão definidas
echo $SNOWFLAKE_PRIVATE_KEY_PATH
echo $SNOWFLAKE_PRIVATE_KEY_PASSWORD

# Se usando arquivo, verificar se existe
ls -la /path/to/your/private_key.pem
```

### Erro: "Insufficient privileges"

**Causa**: Role sem permissões adequadas.

**Solução**:
```sql
-- Executar como SECURITYADMIN
GRANT USAGE ON DATABASE your_database TO ROLE your_role;
GRANT CREATE SCHEMA ON DATABASE your_database TO ROLE your_role;
GRANT ALL ON SCHEMA your_database.your_schema TO ROLE your_role;
GRANT USAGE ON WAREHOUSE your_warehouse TO ROLE your_role;
GRANT OPERATE ON WAREHOUSE your_warehouse TO ROLE your_role;
```

### Erro: "Connection timeout"

**Causa**: Problemas de rede ou configuração.

**Solução**:
```python
# Usar context manager para garantir fechamento
with get_snowflake_connection_context() as conn:
    # Suas operações aqui
    pass
```

## 📝 Boas Práticas

### 1. Sempre use Context Managers

```python
# ✅ Correto
with get_snowflake_connection_context() as conn:
    # operações

# ❌ Evite
conn = get_snowflake_connection()
# operações
conn.close()  # Pode ser esquecido
```

### 2. Trate Exceções

```python
try:
    df = execute_query("SELECT * FROM my_table")
except Exception as e:
    logger.error(f"Erro na query: {e}")
    # Tratamento adequado
```

### 3. Use Query Tags

```bash
# No .env
SNOWFLAKE_QUERY_TAG=dbt_project_name
```

### 4. Monitore Performance

```python
# Verificar tempo de execução
import time
start = time.time()
df = execute_query("SELECT * FROM large_table")
print(f"Query executada em {time.time() - start:.2f}s")
```

## 🧪 Execução via módulo

No diretório raiz do projeto:
```bash
python -m dataflow.snowflake_usage.snowflake_test
```

## 📚 Recursos Adicionais

- [Documentação oficial do Snowflake](https://docs.snowflake.com/)
- [Snowflake Connector Python](https://docs.snowflake.com/en/developer-guide/python-connector/)
- [Snowpark Python](https://docs.snowflake.com/en/developer-guide/snowpark/python/)
- [dbt Snowflake](https://docs.getdbt.com/reference/warehouse-setups/snowflake-setup)
