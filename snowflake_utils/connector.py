import base64
import os
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from contextlib import contextmanager

import pandas as pd
import snowflake.connector
import snowflake.snowpark as sp
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import dsa, rsa
from snowflake.connector.pandas_tools import write_pandas
from snowflake.snowpark.functions import function
from snowflake.connector.errors import ProgrammingError, DatabaseError

from snowflake.connector import SnowflakeConnection

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SnowflakeConfig:
    """Configuração para conexão com Snowflake."""
    account: str
    user: str
    role: str
    warehouse: str
    database: str
    schema: str
    password: Optional[str] = None
    private_key: Optional[bytes] = None
    private_key_passphrase: Optional[str] = None
    threads: int = 5
    client_session_keep_alive: bool = False
    query_tag: Optional[str] = None


def set_snowflake_private_key_decoded(func):
    def wrapper(*args, **kwargs):
        snowflake_private_key_decoded = os.getenv("SNOWFLAKE_PRIVATE_KEY_DECODED", None)
        snowflake_private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH", None)
        snowflake_private_key_base64 = os.getenv("SNOWFLAKE_PRIVATE_KEY", None)

        if not snowflake_private_key_decoded:
            try:
                if snowflake_private_key_path:
                    # Lê do arquivo
                    with open(snowflake_private_key_path, 'r') as f:
                        snowflake_private_key_decoded = f.read()
                    logger.info(f"Chave privada lida do arquivo: {snowflake_private_key_path}")
                elif snowflake_private_key_base64:
                    # Decodifica de base64
                    snowflake_private_key_decoded = base64.b64decode(snowflake_private_key_base64).decode("ascii")
                    logger.info("Chave privada decodificada de base64 com sucesso")
                else:
                    logger.warning("Nenhuma chave privada configurada")
                    return func(*args, **kwargs)

                os.environ["SNOWFLAKE_PRIVATE_KEY_DECODED"] = snowflake_private_key_decoded
            except Exception as e:
                logger.error(f"Erro ao processar chave privada: {e}")
                raise

        return func(*args, **kwargs)

    return wrapper


@set_snowflake_private_key_decoded
def get_snowflake_private_key() -> bytes:

    snowflake_private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    snowflake_private_key_base64 = os.getenv("SNOWFLAKE_PRIVATE_KEY")
    snowflake_private_key_decoded = os.getenv("SNOWFLAKE_PRIVATE_KEY_DECODED")
    snowflake_private_key_password = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSWORD")

    if not snowflake_private_key_path and not snowflake_private_key_base64:
        raise ValueError("Configure SNOWFLAKE_PRIVATE_KEY_PATH ou SNOWFLAKE_PRIVATE_KEY")

    if not snowflake_private_key_decoded:
        raise ValueError("SNOWFLAKE_PRIVATE_KEY_DECODED não foi gerada automaticamente")

    if not snowflake_private_key_password:
        snowflake_private_key_password = ""
        logger.info("Chave privada sem senha detectada")

    try:
        private_key_password = bytes(snowflake_private_key_password, "utf-8")
        private_key = bytes(snowflake_private_key_decoded, "utf-8")

        p_key: Any[rsa.RSAPrivateKey, dsa.DSAPrivateKey] = (
            serialization.load_pem_private_key(
                private_key,
                password=private_key_password if private_key_password else None,
                backend=default_backend()
            )
        )

        pkb: bytes = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        logger.info("Chave privada carregada com sucesso")
        return pkb

    except Exception as e:
        logger.error(f"Erro ao processar chave privada: {e}")
        raise


def get_snowflake_credentials(
    role: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
) -> Dict:

    snowflake_credentials = {
        "user": os.getenv("SNOWFLAKE_USER"),
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "role": role if role else os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": warehouse if warehouse else os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": database if database else os.getenv("SNOWFLAKE_DATABASE"),
        "schema": schema if schema else os.getenv("SNOWFLAKE_SCHEMA"),
        "threads": int(os.getenv("SNOWFLAKE_THREADS", "5")),
        "client_session_keep_alive": os.getenv("SNOWFLAKE_CLIENT_SESSION_KEEP_ALIVE", "False").lower() == "true",
    }

    # Adicionar query tag se configurada
    query_tag = os.getenv("SNOWFLAKE_QUERY_TAG")
    if query_tag:
        snowflake_credentials["query_tag"] = query_tag

    # Verificar método de autenticação
    if os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH") or os.getenv("SNOWFLAKE_PRIVATE_KEY"):
        try:
            snowflake_credentials["private_key"] = get_snowflake_private_key()
            logger.info("Usando autenticação por chave privada")
        except Exception as e:
            logger.error(f"Erro ao configurar chave privada: {e}")
            raise
    elif os.getenv("SNOWFLAKE_PASSWORD"):
        snowflake_credentials["password"] = os.getenv("SNOWFLAKE_PASSWORD")
        logger.info("Usando autenticação por senha")
    else:
        raise ValueError("Configure SNOWFLAKE_PASSWORD, SNOWFLAKE_PRIVATE_KEY_PATH ou SNOWFLAKE_PRIVATE_KEY")

    # Validar credenciais obrigatórias
    required_fields = ["user", "account", "role", "warehouse", "database", "schema"]
    missing_fields = [field for field in required_fields if not snowflake_credentials.get(field)]

    if missing_fields:
        raise ValueError(f"Campos obrigatórios não configurados: {', '.join(missing_fields)}")

    return snowflake_credentials


def get_snowflake_connection(
    role: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
) -> SnowflakeConnection:

    try:
        credentials = get_snowflake_credentials(role, warehouse, database, schema)
        connection = snowflake.connector.connect(**credentials)
        logger.info("Conexão com Snowflake estabelecida com sucesso")
        return connection
    except Exception as e:
        logger.error(f"Erro ao conectar com Snowflake: {e}")
        raise


@contextmanager
def get_snowflake_connection_context(
    role: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
):

    connection = None
    try:
        connection = get_snowflake_connection(role, warehouse, database, schema)
        yield connection
    finally:
        if connection:
            connection.close()
            logger.info("Conexão com Snowflake fechada")


def execute_query(
    query: str,
    role: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
) -> pd.DataFrame:

    try:
        with get_snowflake_connection_context(role, warehouse, database, schema) as conn:
            logger.info(f"Executando query: {query[:100]}...")

            # Usar cursor para evitar warning do pandas
            cursor = conn.cursor()
            cursor.execute(query)

            # Obter resultados
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

            # Criar DataFrame
            df = pd.DataFrame(results, columns=column_names)

            logger.info(f"Query executada com sucesso. Retornou {len(df)} linhas")
            return df
    except Exception as e:
        logger.error(f"Erro ao executar query: {e}")
        raise


def test_connection(
    role: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
) -> bool:

    try:
        df = execute_query(
            "SELECT CURRENT_TIMESTAMP() as current_time, CURRENT_USER() as current_user, CURRENT_ROLE() as current_role",
            role, warehouse, database, schema
        )
        logger.info("Teste de conexão bem-sucedido")
        logger.info(f"DataFrame: {df}")

    except Exception as e:
        logger.error(f"Teste de conexão falhou: {e}")
        return False


def write_dataframe_to_snowflake(
    df: pd.DataFrame,
    table_name: str,
    role: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
    auto_create_table: bool = True,
    overwrite: bool = False,
) -> bool:

    try:
        with get_snowflake_connection_context(role, warehouse, database, schema) as conn:
            logger.info(f"Escrevendo DataFrame na tabela {table_name}")

            success, nchunks, nrows, _ = write_pandas(
                conn, df, table_name,
                auto_create_table=auto_create_table,
                overwrite=overwrite
            )

            if success:
                logger.info(f"Dados escritos com sucesso: {nrows} linhas em {nchunks} chunks")
                return True
            else:
                logger.error("Falha ao escrever dados")
                return False

    except Exception as e:
        logger.error(f"Erro ao escrever DataFrame: {e}")
        raise


def get_snowflake_session(
    role: Optional[str] = None,
    warehouse: Optional[str] = None,
    database: Optional[str] = None,
    schema: Optional[str] = None,
) -> sp.Session:

    try:
        credentials = get_snowflake_credentials(role, warehouse, database, schema)
        session = sp.Session.builder.configs(credentials).create()
        logger.info("Sessão Snowpark criada com sucesso")
        return session
    except Exception as e:
        logger.error(f"Erro ao criar sessão Snowpark: {e}")
        raise


# Funções de conveniência para operações comuns
def get_current_user() -> str:
    """Retorna o usuário atual do Snowflake."""
    df = execute_query("SELECT CURRENT_USER() as user")
    return df['user'].iloc[0]


def get_current_role() -> str:
    """Retorna a role atual do Snowflake."""
    df = execute_query("SELECT CURRENT_ROLE() as role")
    return df['role'].iloc[0]


def get_current_database() -> str:
    """Retorna o database atual do Snowflake."""
    df = execute_query("SELECT CURRENT_DATABASE() as database")
    return df['database'].iloc[0]


def get_current_schema() -> str:
    """Retorna o schema atual do Snowflake."""
    df = execute_query("SELECT CURRENT_SCHEMA() as schema")
    return df['schema'].iloc[0]


def get_current_warehouse() -> str:
    """Retorna o warehouse atual do Snowflake."""
    df = execute_query("SELECT CURRENT_WAREHOUSE() as warehouse")
    return df['warehouse'].iloc[0]
