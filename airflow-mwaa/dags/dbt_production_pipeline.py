"""
DAG de Produção para Pipeline DBT no AWS MWAA
Este DAG demonstra como executar DBT Core em produção no MWAA
"""

import os
import pendulum
from airflow import DAG
from airflow.decorators import task
from airflow.models import Variable
from airflow.exceptions import AirflowException
from airflow.providers.amazon.aws.operators.s3 import S3ListOperator
from airflow.providers.amazon.aws.secrets.secrets_manager import SecretsManagerBackend

# Configurações do MWAA
DEFAULT_PROJECT_DIR = Variable.get("dbt_project_dir", default_var="/opt/airflow/dbt_project")
DEFAULT_PROFILES_DIR = Variable.get("dbt_profiles_dir", default_var="/opt/airflow/.dbt")

with DAG(
    dag_id="dbt_production_pipeline",
    schedule="0 6 * * *",  # Executa diariamente às 6h UTC
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    dag_display_name="DBT Production Pipeline",
    tags=["dbt", "production", "mwaa"],
    description="Pipeline de produção DBT para AWS MWAA",
    max_active_runs=1,  # Apenas uma execução por vez
    default_args={
        "retries": 2,
        "retry_delay": pendulum.duration(minutes=5),
        "email_on_failure": True,
        "email_on_retry": False,
    },
) as dag:

    dag.doc_md = """
    ## Pipeline de Produção DBT

    Este DAG executa o pipeline completo do DBT em produção:

    ### Fluxo:
    1. **Preparação**: Valida configurações e conectividade
    2. **Extração**: Executa dbt deps (dependências)
    3. **Transformação**: Executa dbt build (models + tests)
    4. **Validação**: Executa dbt test (testes adicionais)
    5. **Documentação**: Gera documentação (opcional)
    6. **Limpeza**: Remove arquivos temporários

    ### Configurações:
    - **Schedule**: Diário às 6h UTC
    - **Retry**: 2 tentativas com 5min de intervalo
    - **Max Active Runs**: 1 (evita sobreposição)
    """

    @task
    def validate_environment(**context):
        """
        Valida o ambiente e configurações antes da execução
        """
        project_dir = Variable.get("dbt_project_dir", default_var=DEFAULT_PROJECT_DIR)
        profiles_dir = Variable.get("dbt_profiles_dir", default_var=DEFAULT_PROFILES_DIR)
        dbt_target = Variable.get("dbt_target", default_var="prod")

        print(f"🔍 Validando ambiente de produção:")
        print(f"  Project dir: {project_dir}")
        print(f"  Profiles dir: {profiles_dir}")
        print(f"  Target: {dbt_target}")

        # Verificar se os diretórios existem
        if not os.path.exists(project_dir):
            raise AirflowException(f"❌ Diretório do projeto não encontrado: {project_dir}")

        if not os.path.exists(profiles_dir):
            raise AirflowException(f"❌ Diretório de profiles não encontrado: {profiles_dir}")

        # Verificar se dbt_project.yml existe
        dbt_project_yml = os.path.join(project_dir, "dbt_project.yml")
        if not os.path.exists(dbt_project_yml):
            raise AirflowException(f"❌ Arquivo dbt_project.yml não encontrado: {dbt_project_yml}")

        # Verificar se profiles.yml existe
        profiles_yml = os.path.join(profiles_dir, "profiles.yml")
        if not os.path.exists(profiles_yml):
            raise AirflowException(f"❌ Arquivo profiles.yml não encontrado: {profiles_yml}")

        print("✅ Ambiente validado com sucesso!")
        return {"status": "validated", "timestamp": context["ts"]}

    @task
    def install_dbt_dependencies(**context):
        """
        Instala dependências do DBT (packages)
        """
        project_dir = Variable.get("dbt_project_dir", default_var=DEFAULT_PROJECT_DIR)
        profiles_dir = Variable.get("dbt_profiles_dir", default_var=DEFAULT_PROFILES_DIR)

        print("📦 Instalando dependências do DBT...")

        import subprocess

        try:
            # Mudar para o diretório do projeto
            original_cwd = os.getcwd()
            os.chdir(project_dir)

            # Executar dbt deps
            result = subprocess.run(
                ["dbt", "deps", "--profiles-dir", profiles_dir],
                capture_output=True,
                text=True,
                env={
                    **os.environ,
                    "DBT_PROFILES_DIR": profiles_dir,
                }
            )

            print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            if result.returncode != 0:
                raise AirflowException(f"❌ dbt deps falhou com código {result.returncode}")

            print("✅ Dependências instaladas com sucesso!")
            return {"status": "deps_installed", "output": result.stdout}

        except Exception as e:
            print(f"❌ Erro ao instalar dependências: {str(e)}")
            raise AirflowException(f"Erro ao instalar dependências: {str(e)}")

        finally:
            os.chdir(original_cwd)

    @task
    def run_dbt_build(**context):
        """
        Executa dbt build (models + tests)
        """
        project_dir = Variable.get("dbt_project_dir", default_var=DEFAULT_PROJECT_DIR)
        profiles_dir = Variable.get("dbt_profiles_dir", default_var=DEFAULT_PROFILES_DIR)
        dbt_target = Variable.get("dbt_target", default_var="prod")

        print("🏗️ Executando dbt build...")

        import subprocess

        try:
            # Mudar para o diretório do projeto
            original_cwd = os.getcwd()
            os.chdir(project_dir)

            # Executar dbt build
            cmd = [
                "dbt", "build",
                "--project-dir", project_dir,
                "--profiles-dir", profiles_dir,
                "--target", dbt_target,
                "--log-level", "info"
            ]

            result = subprocess.run(
                cmd,
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
                raise AirflowException(f"❌ dbt build falhou com código {result.returncode}")

            print("✅ dbt build executado com sucesso!")
            return {
                "status": "build_completed",
                "output": result.stdout,
                "returncode": result.returncode
            }

        except Exception as e:
            print(f"❌ Erro ao executar dbt build: {str(e)}")
            raise AirflowException(f"Erro ao executar dbt build: {str(e)}")

        finally:
            os.chdir(original_cwd)

    @task
    def run_dbt_tests(**context):
        """
        Executa testes adicionais do DBT
        """
        project_dir = Variable.get("dbt_project_dir", default_var=DEFAULT_PROJECT_DIR)
        profiles_dir = Variable.get("dbt_profiles_dir", default_var=DEFAULT_PROFILES_DIR)
        dbt_target = Variable.get("dbt_target", default_var="prod")

        print("🧪 Executando testes adicionais do DBT...")

        import subprocess

        try:
            # Mudar para o diretório do projeto
            original_cwd = os.getcwd()
            os.chdir(project_dir)

            # Executar dbt test
            result = subprocess.run(
                ["dbt", "test", "--profiles-dir", profiles_dir, "--target", dbt_target],
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
                raise AirflowException(f"❌ dbt test falhou com código {result.returncode}")

            print("✅ Testes executados com sucesso!")
            return {
                "status": "tests_passed",
                "output": result.stdout,
                "returncode": result.returncode
            }

        except Exception as e:
            print(f"❌ Erro ao executar testes: {str(e)}")
            raise AirflowException(f"Erro ao executar testes: {str(e)}")

        finally:
            os.chdir(original_cwd)

    @task
    def generate_dbt_docs(**context):
        """
        Gera documentação do DBT (opcional)
        """
        project_dir = Variable.get("dbt_project_dir", default_var=DEFAULT_PROJECT_DIR)
        profiles_dir = Variable.get("dbt_profiles_dir", default_var=DEFAULT_PROFILES_DIR)
        dbt_target = Variable.get("dbt_target", default_var="prod")

        print("📚 Gerando documentação do DBT...")

        import subprocess

        try:
            # Mudar para o diretório do projeto
            original_cwd = os.getcwd()
            os.chdir(project_dir)

            # Executar dbt docs generate
            result = subprocess.run(
                ["dbt", "docs", "generate", "--profiles-dir", profiles_dir, "--target", dbt_target],
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
                print(f"⚠️ Aviso: dbt docs generate falhou com código {result.returncode}")
                return {"status": "docs_failed", "output": result.stderr}

            print("✅ Documentação gerada com sucesso!")
            return {
                "status": "docs_generated",
                "output": result.stdout,
                "returncode": result.returncode
            }

        except Exception as e:
            print(f"⚠️ Aviso: Erro ao gerar documentação: {str(e)}")
            return {"status": "docs_error", "error": str(e)}

        finally:
            os.chdir(original_cwd)

    @task
    def cleanup_temp_files(**context):
        """
        Remove arquivos temporários
        """
        project_dir = Variable.get("dbt_project_dir", default_var=DEFAULT_PROJECT_DIR)

        print("🧹 Limpando arquivos temporários...")

        try:
            # Remover arquivos temporários do DBT
            temp_files = [
                "target/",
                "logs/",
                "dbt_packages/",
            ]

            for temp_file in temp_files:
                temp_path = os.path.join(project_dir, temp_file)
                if os.path.exists(temp_path):
                    import shutil
                    shutil.rmtree(temp_path)
                    print(f"  ✅ Removido: {temp_path}")

            print("✅ Limpeza concluída!")
            return {"status": "cleaned", "timestamp": context["ts"]}

        except Exception as e:
            print(f"⚠️ Aviso: Erro na limpeza: {str(e)}")
            return {"status": "cleanup_error", "error": str(e)}

    # Definir dependências entre as tasks
    validation_task = validate_environment()
    deps_task = install_dbt_dependencies()
    build_task = run_dbt_build()
    tests_task = run_dbt_tests()
    docs_task = generate_dbt_docs()
    cleanup_task = cleanup_temp_files()

    # Fluxo de execução
    validation_task >> deps_task >> build_task >> tests_task >> docs_task >> cleanup_task

if __name__ == "__main__":
    from airflow.models import DagBag

    dag = DagBag().get_dag(dag_id="dbt_production_pipeline")
    dag.test()
