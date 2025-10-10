from typing import List, Dict, Optional, Any, Union
import logging
import os
import json
import time
import requests
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from dbt.cli.main import dbtRunner, dbtRunnerResult
from dbt.cli.exceptions import DbtUsageException

logger = logging.getLogger(__name__)

# =============================================================================
# EXCEPTIONS
# =============================================================================

class DbtPipelineException(Exception):
    """Exceção base para erros de pipeline dbt."""
    pass

class DbtCloudException(Exception):
    """Exceção para erros relacionados ao dbt Cloud."""
    pass

class DbtValidationException(Exception):
    """Exceção para erros de validação."""
    pass

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class DbtCloudConfig:
    """Configuração para dbt Cloud."""
    account_id: str
    api_key: str
    base_url: str = "https://cloud.getdbt.com/api/v2"

@dataclass
class DbtRunConfig:
    """Configuração para execução dbt."""
    project_dir: str = "./my_dbt_project/"
    target: str = "dev"
    threads: Optional[int] = None
    vars: Optional[Dict[str, Any]] = None
    profiles_dir: Optional[str] = None
    select: Optional[str] = None
    exclude: Optional[str] = None
    full_refresh: bool = False
    defer: bool = False
    state: Optional[str] = None

@dataclass
class DbtTestConfig:
    """Configuração para testes dbt."""
    store_failures: bool = True
    fail_fast: bool = False
    severity: str = "warn"  # warn, error

# =============================================================================
# DBT CORE OPERATIONS
# =============================================================================

def run_dbt_command(command: str, config: DbtRunConfig) -> dbtRunnerResult:
    """
    Executa um comando dbt genérico.

    Args:
        command: Comando dbt (build, run, test, seed, etc.)
        config: Configuração da execução

    Returns:
        Resultado da execução dbt
    """
    logger.info(f"Executando comando dbt: {command}")
    dbt = dbtRunner()

    cli_args = [command, "--project-dir", config.project_dir, "--target", config.target]

    if config.threads:
        cli_args.extend(["--threads", str(config.threads)])

    if config.vars:
        for key, value in config.vars.items():
            cli_args.extend(["--vars", f"{key}:{value}"])

    if config.profiles_dir:
        cli_args.extend(["--profiles-dir", config.profiles_dir])

    if config.select:
        cli_args.extend(["--select", config.select])

    if config.exclude:
        cli_args.extend(["--exclude", config.exclude])

    if config.full_refresh:
        cli_args.append("--full-refresh")

    if config.defer:
        cli_args.append("--defer")

    if config.state:
        cli_args.extend(["--state", config.state])

    logger.debug(f"Argumentos CLI: {cli_args}")

    try:
        result = dbt.invoke(cli_args)
        return result
    except Exception as e:
        logger.error(f"Erro ao executar comando dbt {command}: {e}")
        raise DbtPipelineException(f"Falha no comando {command}: {e}")

def run_dbt_build(config: DbtRunConfig) -> dbtRunnerResult:
    """Executa dbt build."""
    return run_dbt_command("build", config)

def run_dbt_run(config: DbtRunConfig) -> dbtRunnerResult:
    """Executa dbt run."""
    return run_dbt_command("run", config)

def run_dbt_test(config: DbtRunConfig, test_config: DbtTestConfig) -> dbtRunnerResult:
    """Executa dbt test com configurações específicas."""
    logger.info("Executando testes dbt")

    # Configuração base para testes
    test_run_config = DbtRunConfig(
        project_dir=config.project_dir,
        target=config.target,
        profiles_dir=config.profiles_dir
    )

    cli_args = ["test", "--project-dir", test_run_config.project_dir, "--target", test_run_config.target]

    if test_config.store_failures:
        cli_args.append("--store-failures")

    if test_config.fail_fast:
        cli_args.append("--fail-fast")

    if test_config.severity:
        cli_args.extend(["--severity", test_config.severity])

    dbt = dbtRunner()
    try:
        result = dbt.invoke(cli_args)
        return result
    except Exception as e:
        logger.error(f"Erro ao executar testes dbt: {e}")
        raise DbtPipelineException(f"Falha nos testes: {e}")

def run_dbt_seed(config: DbtRunConfig) -> dbtRunnerResult:
    """Executa dbt seed."""
    return run_dbt_command("seed", config)

def run_dbt_snapshot(config: DbtRunConfig) -> dbtRunnerResult:
    """Executa dbt snapshot."""
    return run_dbt_command("snapshot", config)

def run_dbt_docs_generate(config: DbtRunConfig) -> dbtRunnerResult:
    """Gera documentação dbt."""
    return run_dbt_command("docs", config)

def run_dbt_docs_serve(config: DbtRunConfig, port: int = 8080) -> dbtRunnerResult:
    """Serve documentação dbt."""
    logger.info(f"Iniciando servidor de documentação na porta {port}")
    dbt = dbtRunner()

    cli_args = [
        "docs", "serve",
        "--project-dir", config.project_dir,
        "--target", config.target,
        "--port", str(port)
    ]

    try:
        result = dbt.invoke(cli_args)
        return result
    except Exception as e:
        logger.error(f"Erro ao servir documentação: {e}")
        raise DbtPipelineException(f"Falha ao servir documentação: {e}")

def run_dbt_compile(config: DbtRunConfig) -> dbtRunnerResult:
    """Compila modelos dbt sem executá-los."""
    return run_dbt_command("compile", config)

def run_dbt_parse(config: DbtRunConfig) -> dbtRunnerResult:
    """Parse do projeto dbt."""
    return run_dbt_command("parse", config)

def run_dbt_debug(config: DbtRunConfig) -> dbtRunnerResult:
    """Executa dbt debug para verificar configurações."""
    return run_dbt_command("debug", config)

def run_dbt_clean(config: DbtRunConfig) -> dbtRunnerResult:
    """Limpa arquivos temporários dbt."""
    return run_dbt_command("clean", config)

def run_dbt_deps(config: DbtRunConfig) -> dbtRunnerResult:
    """Instala dependências do projeto."""
    return run_dbt_command("deps", config)

def run_dbt_list(config: DbtRunConfig) -> dbtRunnerResult:
    """Lista recursos do projeto."""
    return run_dbt_command("list", config)

def run_dbt_show(config: DbtRunConfig, model_name: str) -> dbtRunnerResult:
    """Mostra preview de um modelo."""
    logger.info(f"Mostrando preview do modelo: {model_name}")
    dbt = dbtRunner()

    cli_args = [
        "show",
        "--project-dir", config.project_dir,
        "--target", config.target,
        "--select", model_name
    ]

    try:
        result = dbt.invoke(cli_args)
        return result
    except Exception as e:
        logger.error(f"Erro ao mostrar modelo {model_name}: {e}")
        raise DbtPipelineException(f"Falha ao mostrar modelo: {e}")

# =============================================================================
# DBT CLOUD OPERATIONS
# =============================================================================

class DbtCloudClient:
    """Cliente para interação com dbt Cloud API."""

    def __init__(self, config: DbtCloudConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {config.api_key}",
            "Content-Type": "application/json"
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Faz requisição para API do dbt Cloud."""
        url = f"{self.config.base_url}/{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para dbt Cloud: {e}")
            raise DbtCloudException(f"Falha na requisição: {e}")

    def get_jobs(self, project_id: Optional[int] = None) -> Dict[str, Any]:
        """Lista jobs do projeto."""
        endpoint = "accounts/{account_id}/jobs"
        if project_id:
            endpoint += f"?project_id={project_id}"

        return self._make_request("GET", endpoint.format(account_id=self.config.account_id))

    def trigger_job(self, job_id: int, cause: str = "API Trigger") -> Dict[str, Any]:
        """Dispara um job específico."""
        endpoint = f"accounts/{self.config.account_id}/jobs/{job_id}/run"
        payload = {"cause": cause}

        return self._make_request("POST", endpoint, json=payload)

    def get_run_status(self, run_id: int) -> Dict[str, Any]:
        """Obtém status de uma execução."""
        endpoint = f"accounts/{self.config.account_id}/runs/{run_id}"
        return self._make_request("GET", endpoint)

    def cancel_run(self, run_id: int) -> Dict[str, Any]:
        """Cancela uma execução em andamento."""
        endpoint = f"accounts/{self.config.account_id}/runs/{run_id}/cancel"
        return self._make_request("POST", endpoint)

    def get_run_artifacts(self, run_id: int, path: str = "manifest.json") -> Dict[str, Any]:
        """Obtém artefatos de uma execução."""
        endpoint = f"accounts/{self.config.account_id}/runs/{run_id}/artifacts/{path}"
        return self._make_request("GET", endpoint)

    def wait_for_run_completion(self, run_id: int, timeout_minutes: int = 60) -> Dict[str, Any]:
        """Aguarda conclusão de uma execução."""
        logger.info(f"Aguardando conclusão da execução {run_id}")
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        while time.time() - start_time < timeout_seconds:
            status = self.get_run_status(run_id)
            run_status = status.get("status")

            if run_status in [1, 2, 3]:  # Running, Success, Error
                if run_status == 2:  # Success
                    logger.info(f"Execução {run_id} concluída com sucesso")
                    return status
                elif run_status == 3:  # Error
                    logger.error(f"Execução {run_id} falhou")
                    return status
                else:  # Running
                    logger.info(f"Execução {run_id} ainda em andamento...")
                    time.sleep(30)  # Aguarda 30 segundos antes de verificar novamente
            else:
                logger.warning(f"Status desconhecido: {run_status}")
                time.sleep(30)

        raise DbtCloudException(f"Timeout aguardando execução {run_id}")

def trigger_dbt_cloud_job(
    cloud_config: DbtCloudConfig,
    job_id: int,
    cause: str = "Pipeline Trigger"
) -> Dict[str, Any]:
    """Dispara um job no dbt Cloud."""
    logger.info(f"Disparando job {job_id} no dbt Cloud")

    client = DbtCloudClient(cloud_config)
    result = client.trigger_job(job_id, cause)

    logger.info(f"Job disparado com sucesso. Run ID: {result.get('id')}")
    return result

def wait_for_dbt_cloud_job(
    cloud_config: DbtCloudConfig,
    run_id: int,
    timeout_minutes: int = 60
) -> Dict[str, Any]:
    """Aguarda conclusão de um job no dbt Cloud."""
    logger.info(f"Aguardando conclusão do job {run_id}")

    client = DbtCloudClient(cloud_config)
    return client.wait_for_run_completion(run_id, timeout_minutes)

# =============================================================================
# PIPELINE ORCHESTRATION
# =============================================================================

def run_full_dbt_pipeline(
    config: DbtRunConfig,
    test_config: DbtTestConfig,
    include_seed: bool = True,
    include_snapshot: bool = True,
    include_docs: bool = False
) -> Dict[str, Any]:
    """
    Executa pipeline completo dbt com todas as etapas.

    Args:
        config: Configuração da execução
        test_config: Configuração dos testes
        include_seed: Se deve executar seed
        include_snapshot: Se deve executar snapshot
        include_docs: Se deve gerar documentação

    Returns:
        Dicionário com resultados de cada etapa
    """
    logger.info("Iniciando pipeline completo dbt")
    results = {}

    try:
        # 1. Instalar dependências
        logger.info("Instalando dependências...")
        results["deps"] = run_dbt_deps(config)

        # 2. Executar seed (se solicitado)
        if include_seed:
            logger.info("Executando seed...")
            results["seed"] = run_dbt_seed(config)

        # 3. Executar snapshot (se solicitado)
        if include_snapshot:
            logger.info("Executando snapshot...")
            results["snapshot"] = run_dbt_snapshot(config)

        # 4. Executar build (inclui run e test)
        logger.info("Executando build...")
        results["build"] = run_dbt_build(config)

        # 5. Executar testes adicionais
        logger.info("Executando testes...")
        results["test"] = run_dbt_test(config, test_config)

        # 6. Gerar documentação (se solicitado)
        if include_docs:
            logger.info("Gerando documentação...")
            results["docs"] = run_dbt_docs_generate(config)

        logger.info("Pipeline completo executado com sucesso!")
        return results

    except Exception as e:
        logger.error(f"Erro no pipeline completo: {e}")
        raise DbtPipelineException(f"Falha no pipeline completo: {e}")

def run_incremental_pipeline(
    config: DbtRunConfig,
    models_to_run: List[str],
    run_tests: bool = True
) -> Dict[str, Any]:
    """
    Executa pipeline incremental para modelos específicos.

    Args:
        config: Configuração da execução
        models_to_run: Lista de modelos para executar
        run_tests: Se deve executar testes

    Returns:
        Dicionário com resultados
    """
    logger.info(f"Executando pipeline incremental para modelos: {models_to_run}")

    # Configuração para execução incremental
    incremental_config = DbtRunConfig(
        project_dir=config.project_dir,
        target=config.target,
        profiles_dir=config.profiles_dir,
        select=" ".join(models_to_run)
    )

    results = {}

    try:
        # Executar apenas os modelos especificados
        results["run"] = run_dbt_run(incremental_config)

        if run_tests:
            test_config = DbtTestConfig(store_failures=True, fail_fast=False)
            results["test"] = run_dbt_test(incremental_config, test_config)

        return results

    except Exception as e:
        logger.error(f"Erro no pipeline incremental: {e}")
        raise DbtPipelineException(f"Falha no pipeline incremental: {e}")

def run_parallel_pipeline(
    config: DbtRunConfig,
    model_groups: List[List[str]],
    max_workers: int = 3
) -> Dict[str, Any]:
    """
    Executa pipeline em paralelo para diferentes grupos de modelos.

    Args:
        config: Configuração base
        model_groups: Lista de grupos de modelos para executar em paralelo
        max_workers: Número máximo de workers paralelos

    Returns:
        Dicionário com resultados de cada grupo
    """
    logger.info(f"Executando pipeline paralelo com {len(model_groups)} grupos")

    def run_model_group(group: List[str], group_id: int) -> tuple:
        """Executa um grupo de modelos."""
        try:
            group_config = DbtRunConfig(
                project_dir=config.project_dir,
                target=config.target,
                profiles_dir=config.profiles_dir,
                select=" ".join(group)
            )

            result = run_dbt_run(group_config)
            return group_id, {"status": "success", "result": result}
        except Exception as e:
            return group_id, {"status": "error", "error": str(e)}

    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submete todos os grupos para execução paralela
        future_to_group = {
            executor.submit(run_model_group, group, i): i
            for i, group in enumerate(model_groups)
        }

        # Coleta resultados conforme são concluídos
        for future in as_completed(future_to_group):
            group_id, result = future.result()
            results[f"group_{group_id}"] = result

    return results

# =============================================================================
# VALIDATION AND UTILITIES
# =============================================================================

def validate_dbt_project(project_dir: str) -> bool:
    """
    Valida se o projeto dbt está configurado corretamente.

    Args:
        project_dir: Diretório do projeto

    Returns:
        True se válido, False caso contrário
    """
    logger.info("Validando projeto dbt")

    project_path = Path(project_dir)

    # Verificar se existe dbt_project.yml
    if not (project_path / "dbt_project.yml").exists():
        logger.error("dbt_project.yml não encontrado")
        return False

    # Verificar se existe profiles.yml
    profiles_path = Path.home() / ".dbt" / "profiles.yml"
    if not profiles_path.exists():
        logger.warning("profiles.yml não encontrado em ~/.dbt/")

    # Verificar estrutura básica
    required_dirs = ["models", "macros"]
    for dir_name in required_dirs:
        if not (project_path / dir_name).exists():
            logger.warning(f"Diretório {dir_name} não encontrado")

    # Tentar parse do projeto
    try:
        config = DbtRunConfig(project_dir=project_dir)
        run_dbt_parse(config)
        logger.info("Projeto dbt validado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Falha na validação do projeto: {e}")
        return False

def get_dbt_project_info(project_dir: str) -> Dict[str, Any]:
    """
    Obtém informações sobre o projeto dbt.

    Args:
        project_dir: Diretório do projeto

    Returns:
        Dicionário com informações do projeto
    """
    logger.info("Obtendo informações do projeto dbt")

    try:
        config = DbtRunConfig(project_dir=project_dir)
        list_result = run_dbt_list(config)

        # Processar resultado para extrair informações
        project_info = {
            "models": [],
            "tests": [],
            "seeds": [],
            "snapshots": [],
            "macros": []
        }

        if list_result.success and list_result.result:
            for node in list_result.result:
                resource_type = node.resource_type
                if resource_type in project_info:
                    project_info[resource_type].append({
                        "name": node.name,
                        "path": node.path,
                        "description": getattr(node, 'description', '')
                    })

        return project_info

    except Exception as e:
        logger.error(f"Erro ao obter informações do projeto: {e}")
        raise DbtPipelineException(f"Falha ao obter informações: {e}")

def cleanup_dbt_artifacts(project_dir: str, keep_days: int = 7) -> None:
    """
    Limpa artefatos antigos do dbt.

    Args:
        project_dir: Diretório do projeto
        keep_days: Número de dias para manter artefatos
    """
    logger.info(f"Limpando artefatos dbt mais antigos que {keep_days} dias")

    target_dir = Path(project_dir) / "target"
    if not target_dir.exists():
        logger.info("Diretório target não encontrado")
        return

    cutoff_date = datetime.now() - timedelta(days=keep_days)

    for item in target_dir.iterdir():
        if item.is_file():
            stat = item.stat()
            file_date = datetime.fromtimestamp(stat.st_mtime)

            if file_date < cutoff_date:
                try:
                    item.unlink()
                    logger.info(f"Arquivo removido: {item.name}")
                except Exception as e:
                    logger.warning(f"Erro ao remover {item.name}: {e}")
        elif item.is_dir():
            # Recursivamente limpar subdiretórios
            cleanup_dbt_artifacts(str(item), keep_days)

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Exemplo simples de uso das funcionalidades
    print("🚀 dbt Jobs - Exemplo de Uso")
    print("=" * 40)

    try:
        # Exemplo 1: Validação do projeto
        print("1. Validando projeto...")
        success = validate_dbt_project("./my_dbt_project/")
        if success:
            print("✅ Projeto válido")
        else:
            print("❌ Projeto inválido")
            exit(1)

        # Exemplo 2: Executar build
        print("2. Executando build...")
        config = DbtRunConfig(project_dir="./my_dbt_project/", target="dev")
        result = run_dbt_build(config)

        if result.success:
            print("✅ Build executado com sucesso")
        else:
            print("❌ Falha no build")
            exit(1)

        # Exemplo 3: Pipeline completo
        print("3. Executando pipeline completo...")
        test_config = DbtTestConfig(store_failures=True, fail_fast=False)
        results = run_full_dbt_pipeline(config, test_config, include_docs=True)

        print("✅ Pipeline completo executado!")
        print(f"Etapas: {list(results.keys())}")

    except Exception as e:
        print(f"❌ Erro: {e}")
        exit(1)
