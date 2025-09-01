from typing import List
import logging
from dbt.cli.main import dbtRunner, dbtRunnerResult
from snowflake_utils.connector import (
    set_snowflake_private_key_decoded,
)
logger = logging.getLogger(__name__)

class DbtPipelineException(Exception):
    pass

def run_dbt_main_pipeline(dbt_target: str, dbt_args: List[str] = []):
    logger.info("Running dbt main pipeline")
    dbt = dbtRunner()

    cli_args = [
        "build",
        "--project-dir",
        "./my_dbt_project/",
        "--target",
        dbt_target,
    ]
    if dbt_args:
        cli_args += dbt_args

    res: dbtRunnerResult = dbt.invoke(cli_args)
    if not res.success and res.exception:
        raise res.exception

    for result in res.result:
        if result.status in ["fail", "error"]:
            error_message = (
                f"{result.node.resource_type} {result.status} {result.node.name}"
            )
            raise DbtPipelineException(error_message)


@set_snowflake_private_key_decoded
def run_main_pipeline(dbt_target: str, dbt_args: List[str] = []):
    logger.info("Running main pipeline")

    run_dbt_main_pipeline(dbt_target=dbt_target, dbt_args=dbt_args)


if __name__ == "__main__":
    run_main_pipeline(dbt_target="dev")
