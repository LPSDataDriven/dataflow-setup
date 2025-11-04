from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

# DBT variables
DBT_PROJECT_DIR = "/opt/airflow/dbt"
DBT_PROFILES_DIR = "/opt/airflow/.dbt"
DBT_TARGET = "dev"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
}

with DAG(
    dag_id="dbt_main_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    default_args=default_args,
    tags=["dbt"],
) as dag:

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"dbt build --project-dir {DBT_PROJECT_DIR} --profiles-dir {DBT_PROFILES_DIR} --target {DBT_TARGET}"
        ),
        env={
            "DBT_PROFILES_DIR": DBT_PROFILES_DIR,
        },
    )

    dbt_build
