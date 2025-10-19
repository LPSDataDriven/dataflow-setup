"""
DAG completo para pipeline principal no AWS MWAA
Adaptado do full_main_pipeline.py para funcionar no ambiente gerenciado
"""

import os
import pendulum
from airflow import DAG
from airflow.decorators import task
from airflow.models.param import Param
from airflow.models import Variable
from airflow.exceptions import AirflowException

# Configurações específicas para MWAA
DEFAULT_PROJECT_DIR = Variable.get("dbt_project_dir", default_var="/opt/airflow/dbt_project")
DEFAULT_PROFILES_DIR = Variable.get("dbt_profiles_dir", default_var="/opt/airflow/.dbt")

with DAG(
    dag_id="full_main_pipeline_mwaa",
    schedule=None,  # Execução manual
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dag_display_name="Main full pipeline (MWAA)",
    tags=["dbt", "mwaa", "full-pipeline"],
    description="Pipeline completo principal para AWS MWAA",
    params={
        "is_update_mapping": Param(
            False,
            type="boolean",
            title="Update mapping",
            description=(
                "If false, exclude raw_label_mappings model from the run."
            ),
        ),
        "dbt_select": Param(
            "",
            type="string",
            title="DBT Select",
            description="Models to select for dbt run (e.g., 'model1 model2')",
        ),
        "dbt_exclude": Param(
            "",
            type="string",
            title="DBT Exclude",
            description="Models to exclude from dbt run (e.g., 'model1 model2')",
        ),
    },
) as dag:

    dag.doc_md = """
    ## Pipeline Completo Principal para AWS MWAA

    Este DAG executa o pipeline principal do DBT via Python no ambiente AWS MWAA.

    ### Parâmetros:
    - **is_update_mapping**: Se false, exclui o modelo raw_label_mappings
    - **dbt_select**: Modelos específicos para executar
    - **dbt_exclude**: Modelos para excluir da execução

    ### Configurações:
    Configure as seguintes variáveis no Airflow UI:
    - `dbt_project_dir`: Caminho para o projeto DBT
    - `dbt_profiles_dir`: Caminho para os profiles DBT
    - `dbt_target`: Target do DBT
    """

    @task
    def full_main_pipeline(**context):
        """
        Executa o pipeline principal do DBT
        """
        # Obter configurações
        dbt_target = Variable.get("dbt_target", default_var="dev")
        project_dir = Variable.get("dbt_project_dir", default_var=DEFAULT_PROJECT_DIR)
        profiles_dir = Variable.get("dbt_profiles_dir", default_var=DEFAULT_PROFILES_DIR)

        # Obter parâmetros do DAG
        params = context.get("params", {})
        select = params.get("dbt_select", "").strip() or None
        exclude = params.get("dbt_exclude", "").strip() or None

        # Lógica para excluir raw_label_mappings se necessário
        if not select and not params.get("is_update_mapping", False):
            exclude = (exclude + " ") if exclude else ""
            exclude += "raw_label_mappings"

        # Construir comando dbt
        cmd_parts = [
            "dbt build",
            f"--project-dir {project_dir}",
            f"--profiles-dir {profiles_dir}",
            f"--target {dbt_target}",
            "--log-level info"
        ]

        if select:
            cmd_parts.append(f"--select {select}")

        if exclude:
            cmd_parts.append(f"--exclude {exclude}")

        dbt_command = " ".join(cmd_parts)

        print(f"Executando comando: {dbt_command}")
        print(f"Project dir: {project_dir}")
        print(f"Profiles dir: {profiles_dir}")
        print(f"Target: {dbt_target}")
        print(f"Select: {select}")
        print(f"Exclude: {exclude}")

        # Executar comando dbt
        import subprocess
        import sys

        try:
            # Mudar para o diretório do projeto
            original_cwd = os.getcwd()
            os.chdir(project_dir)

            # Executar dbt
            result = subprocess.run(
                dbt_command,
                shell=True,
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "DBT_PROFILES_DIR": profiles_dir,
                    "DBT_TARGET": dbt_target,
                }
            )

            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            if result.returncode != 0:
                raise AirflowException(f"dbt build failed with return code {result.returncode}")

            return {
                "status": "success",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        except Exception as e:
            print(f"Erro ao executar dbt: {str(e)}")
            raise AirflowException(f"Erro ao executar dbt: {str(e)}")

        finally:
            # Restaurar diretório original
            os.chdir(original_cwd)

    @task
    def validate_dbt_config(**context):
        """
        Valida a configuração do DBT antes da execução
        """
        project_dir = Variable.get("dbt_project_dir", default_var=DEFAULT_PROJECT_DIR)
        profiles_dir = Variable.get("dbt_profiles_dir", default_var=DEFAULT_PROFILES_DIR)
        dbt_target = Variable.get("dbt_target", default_var="dev")

        print(f"Validando configuração DBT:")
        print(f"  Project dir: {project_dir}")
        print(f"  Profiles dir: {profiles_dir}")
        print(f"  Target: {dbt_target}")

        # Verificar se os diretórios existem
        if not os.path.exists(project_dir):
            raise AirflowException(f"Diretório do projeto não encontrado: {project_dir}")

        if not os.path.exists(profiles_dir):
            raise AirflowException(f"Diretório de profiles não encontrado: {profiles_dir}")

        # Verificar se dbt_project.yml existe
        dbt_project_yml = os.path.join(project_dir, "dbt_project.yml")
        if not os.path.exists(dbt_project_yml):
            raise AirflowException(f"Arquivo dbt_project.yml não encontrado: {dbt_project_yml}")

        print("Configuração DBT validada com sucesso!")
        return {"status": "validated"}

    # Definir dependências
    validation_task = validate_dbt_config()
    pipeline_task = full_main_pipeline()

    validation_task >> pipeline_task

if __name__ == "__main__":
    from airflow.models import DagBag

    dag = DagBag().get_dag(dag_id="full_main_pipeline_mwaa")
    dag.test()

