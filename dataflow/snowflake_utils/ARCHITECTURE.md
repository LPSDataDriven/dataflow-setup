# Arquitetura do Snowflake Connector

## 🔄 Diagrama de Fluxo Detalhado 🏗️ Hierarquia de Funções

### Nível 1: Configuração e Validação
```
get_snowflake_credentials()
├── Valida variáveis de ambiente
├── Escolhe método de autenticação
└── Retorna dicionário de credenciais
```

### Nível 2: Processamento de Chave Privada
```
get_snowflake_private_key()
├── @set_snowflake_private_key_decoded (decorator)
│   ├── Lê arquivo ou decodifica base64
│   └── Salva em SNOWFLAKE_PRIVATE_KEY_DECODED
├── Processa chave PEM
└── Retorna bytes DER
```

### Nível 3: Gerenciamento de Conexão
```
get_snowflake_connection()
├── Usa credenciais do Nível 1
└── Cria SnowflakeConnection

get_snowflake_connection_context()
├── Context manager wrapper
├── Garante fechamento automático
└── Tratamento de exceções
```

### Nível 4: Operações de Alto Nível
```
execute_query()
├── Usa context manager
├── Executa SQL
└── Retorna DataFrame

write_dataframe_to_snowflake()
├── Usa context manager
├── Escreve DataFrame
└── Retorna success/failure

get_snowflake_session()
├── Cria sessão Snowpark
└── Retorna Session object
```

### Nível 5: Utilitários
```
test_connection()
├── Testa conectividade básica
└── Retorna boolean

get_current_*()
├── Queries de informação do ambiente
└── Retorna strings
```
