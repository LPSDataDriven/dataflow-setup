from dataflow.dbt_utils.connector import run_dbt_build, DbtRunConfig

if __name__ == "__main__":
    config = DbtRunConfig(project_dir="./my_dbt_project/", target="dev")
    result = run_dbt_build(config)
    print(result)
