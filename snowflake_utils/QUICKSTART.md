# Quick Start - Snowflake Connector

## 🚀 Começando em 5 minutos

### 1. Configuração Básica

Configure suas variáveis de ambiente no arquivo `.env`:

```bash
# Configurações obrigatórias
SNOWFLAKE_ACCOUNT=your_account.snowflakecomputing.com
SNOWFLAKE_USER=your_username
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=your_schema

# Autenticação (escolha uma opção)
SNOWFLAKE_PASSWORD=your_password
# OU
SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/your/private_key.pem
SNOWFLAKE_PRIVATE_KEY_PASSWORD=your_key_password
```

### 2. Teste de Conexão

```bash
# Teste básico
python snowflake/test_connection.py

# Teste completo
python snowflake/test_operations.py
```

### 3. Primeiro Código

```python
from snowflake.connector import execute_query

# Ler dados
df = execute_query("SELECT CURRENT_TIMESTAMP() as now")
print(df)
```

## 📚 Exemplos Práticos

### Exemplo 1: Pipeline de Dados Simples

```python
from snowflake.connector import execute_query, write_dataframe_to_snowflake
import pandas as pd

# 1. Ler dados de origem
df_source = execute_query("""
    SELECT
        customer_id,
        order_date,
        total_amount
    FROM orders
    WHERE order_date >= '2024-01-01'
""")

# 2. Transformar dados
df_daily = df_source.groupby('order_date').agg({
    'total_amount': 'sum',
    'customer_id': 'count'
}).reset_index()

df_daily.columns = ['date', 'total_revenue', 'order_count']

# 3. Escrever resultado
write_dataframe_to_snowflake(
    df_daily,
    'daily_sales_summary',
    auto_create_table=True
)

print(f"Processados {len(df_source)} pedidos")
```

### Exemplo 2: Monitoramento de Sistema

```python
from snowflake.connector import execute_query
import pandas as pd

# Verificar performance do warehouse
warehouse_stats = execute_query("""
    SELECT
        WAREHOUSE_NAME,
        START_TIME,
        END_TIME,
        TOTAL_ELAPSED_TIME,
        BYTES_SCANNED,
        PERCENTAGE_SCANNED_FROM_CACHE
    FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
        DATE_RANGE_START=>DATEADD('hour', -24, CURRENT_TIMESTAMP()),
        DATE_RANGE_END=>CURRENT_TIMESTAMP()
    ))
    ORDER BY START_TIME DESC
""")

print("Estatísticas do warehouse nas últimas 24h:")
print(warehouse_stats)
```

### Exemplo 3: Backup de Tabela

```python
from snowflake.connector import execute_query
from datetime import datetime

# Criar backup com timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_table = f"my_table_backup_{timestamp}"

execute_query(f"""
    CREATE OR REPLACE TABLE {backup_table} AS
    SELECT * FROM my_table
""")

print(f"Backup criado: {backup_table}")
```

## 🔧 Operações Comuns

### Leitura de Dados

```python
# Query simples
df = execute_query("SELECT * FROM my_table LIMIT 100")

# Query com filtros
df = execute_query("""
    SELECT * FROM my_table
    WHERE created_date >= '2024-01-01'
    AND status = 'active'
""")

# Query com agregação
df = execute_query("""
    SELECT
        category,
        COUNT(*) as count,
        AVG(amount) as avg_amount
    FROM transactions
    GROUP BY category
    ORDER BY count DESC
""")
```

### Escrita de Dados

```python
import pandas as pd

# Criar DataFrame
df = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'email': ['alice@email.com', 'bob@email.com', 'charlie@email.com']
})

# Escrever no Snowflake
write_dataframe_to_snowflake(
    df,
    'users',
    auto_create_table=True,  # Cria tabela se não existir
    overwrite=False          # Não sobrescreve dados existentes
)
```

### Operações com Snowpark

```python
from snowflake.connector import get_snowflake_session

# Criar sessão
session = get_snowflake_session()

# Criar DataFrame Snowpark
df = session.create_dataframe([
    (1, "Product A", 100.50),
    (2, "Product B", 200.75),
    (3, "Product C", 150.25)
], ["id", "name", "price"])

# Operações de transformação
df_filtered = df.filter(df.price > 150)
df_grouped = df.group_by("name").agg({"price": "sum"})

# Salvar no Snowflake
df_filtered.write.mode("overwrite").save_as_table("expensive_products")

# Fechar sessão
session.close()
```

## 🛠️ Troubleshooting Rápido

### Erro: "Connection failed"

```bash
# Verificar variáveis de ambiente
python -c "
import os
print('Account:', os.getenv('SNOWFLAKE_ACCOUNT'))
print('User:', os.getenv('SNOWFLAKE_USER'))
print('Database:', os.getenv('SNOWFLAKE_DATABASE'))
"
```

### Erro: "Insufficient privileges"

```sql
-- Executar como SECURITYADMIN
GRANT USAGE ON DATABASE your_database TO ROLE your_role;
GRANT CREATE SCHEMA ON DATABASE your_database TO ROLE your_role;
GRANT ALL ON SCHEMA your_database.your_schema TO ROLE your_role;
GRANT USAGE ON WAREHOUSE your_warehouse TO ROLE your_role;
GRANT OPERATE ON WAREHOUSE your_warehouse TO ROLE your_role;
```

### Erro: "Private key not found"

```bash
# Verificar arquivo da chave
ls -la /path/to/your/private_key.pem

# Verificar permissões
chmod 600 /path/to/your/private_key.pem
```

## 📊 Monitoramento

### Verificar Queries Recentes

```python
queries = execute_query("""
    SELECT
        QUERY_ID,
        QUERY_TEXT,
        START_TIME,
        TOTAL_ELAPSED_TIME,
        STATUS
    FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
    WHERE START_TIME >= DATEADD(hour, -1, CURRENT_TIMESTAMP())
    AND USER = CURRENT_USER()
    ORDER BY START_TIME DESC
    LIMIT 10
""")

for _, row in queries.iterrows():
    print(f"{row['START_TIME']}: {row['TOTAL_ELAPSED_TIME']}ms - {row['STATUS']}")
```

### Verificar Uso do Warehouse

```python
warehouse_usage = execute_query("""
    SELECT
        WAREHOUSE_NAME,
        START_TIME,
        END_TIME,
        TOTAL_ELAPSED_TIME,
        CREDITS_USED
    FROM TABLE(INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
        DATE_RANGE_START=>DATEADD('day', -7, CURRENT_TIMESTAMP()),
        DATE_RANGE_END=>CURRENT_TIMESTAMP()
    ))
    ORDER BY START_TIME DESC
""")

total_credits = warehouse_usage['CREDITS_USED'].sum()
print(f"Total de créditos usados na semana: {total_credits}")
```
