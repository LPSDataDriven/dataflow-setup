"""
DAG para executar pipeline DBT no AWS MWAA
Adaptado do dbt_main_pipeline.py para funcionar no ambiente gerenciado
"""

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.models import Variable

# Configurações específicas para MWAA
# No MWAA, usamos variáveis do Airflow ou AWS Systems Manager Parameter Store
DBT_PROJECT_DIR = Variable.get("dbt_project_dir", default_var="/opt/airflow/dbt_project")
DBT_PROFILES_DIR = Variable.get("dbt_profiles_dir", default_var="/opt/airflow/.dbt")
DBT_TARGET = Variable.get("dbt_target", default_var="dev")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": 300,  # 5 minutos
    "email_on_failure": True,
    "email_on_retry": False,
}

with DAG(
    dag_id="dbt_main_pipeline_mwaa",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # Execução manual
    catchup=False,
    default_args=default_args,
    tags=["dbt", "mwaa"],
    description="Pipeline principal DBT para AWS MWAA",
    doc_md="""
    ## Pipeline DBT para AWS MWAA

    Este DAG executa o pipeline principal do DBT no ambiente AWS MWAA.

    ### Configurações:
    - **DBT_PROJECT_DIR**: Diretório do projeto DBT
    - **DBT_PROFILES_DIR**: Diretório dos profiles DBT
    - **DBT_TARGET**: Target do DBT (dev/prod)

    ### Variáveis do Airflow:
    Configure as seguintes variáveis no Airflow UI:
    - `dbt_project_dir`: Caminho para o projeto DBT
    - `dbt_profiles_dir`: Caminho para os profiles DBT
    - `dbt_target`: Target do DBT
    """,
) as dag:

    # Task para executar dbt build
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt build --project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--target {DBT_TARGET} "
            f"--log-level info"
        ),
        env={
            "DBT_PROFILES_DIR": DBT_PROFILES_DIR,
            "DBT_TARGET": DBT_TARGET,
        },
    )

    # Task para executar dbt test (opcional)
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"cd {DBT_PROJECT_DIR} && "
            f"dbt test --project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR} "
            f"--target {DBT_TARGET}"
        ),
        env={
            "DBT_PROFILES_DIR": DBT_PROFILES_DIR,
            "DBT_TARGET": DBT_TARGET,
        },
    )

    # Definir dependências
    dbt_build >> dbt_test

