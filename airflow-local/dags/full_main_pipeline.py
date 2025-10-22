import os
import pendulum
from airflow import DAG
from airflow.decorators import task
from airflow.models.param import Param
from dbt_utils.connector import run_dbt_command, DbtRunConfig

DEFAULT_PROJECT_DIR = "/opt/airflow/my_dbt_project"
DEFAULT_PROFILES_DIR = "/opt/airflow/.dbt"

with DAG(
    dag_id="full_main_pipeline",
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dag_display_name="Main full pipeline",
    tags=["dbt"],
    params={
        "is_update_mapping": Param(
            False,
            type="boolean",
            title="Update mapping",
            description=(
                "If false, exclude raw_label_mappings model from the run."
            ),
        ),
    },
) as dag:
    dag.doc_md = """
    This DAG runs the main dbt pipeline via Python, leveraging dbt's CLI runner.
    """

    @task
    def full_main_pipeline(**context):
        dbt_target = os.getenv("DBT_TARGET", "dev")
        project_dir = os.getenv("DBT_PROJECT_DIR", DEFAULT_PROJECT_DIR)
        profiles_dir = os.getenv("DBT_PROFILES_DIR", DEFAULT_PROFILES_DIR)

        params = context.get("params", {})
        select = os.getenv("DBT_SELECT") or None
        exclude = os.getenv("DBT_EXCLUDE") or None

        if not select and not params.get("is_update_mapping", False):
            exclude = (exclude + " ") if exclude else ""
            exclude += "raw_label_mappings"

        config = DbtRunConfig(
            project_dir=project_dir,
            target=dbt_target,
            profiles_dir=profiles_dir,
            select=select,
            exclude=exclude,
        )

        result = run_dbt_command("build", config)
        if not result.success:
            raise RuntimeError("dbt build failed")

    full_main_pipeline()

if __name__ == "__main__":
    from airflow.models import DagBag

    dag = DagBag().get_dag(dag_id="full_main_pipeline")
    dag.test()
