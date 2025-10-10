from dataflow.snowflake_utils.connector import get_snowflake_credentials, test_connection

if __name__ == "__main__":
    snowflake_credentials = get_snowflake_credentials()
    role = snowflake_credentials["role"]
    warehouse = snowflake_credentials["warehouse"]
    database = snowflake_credentials["database"]
    schema = snowflake_credentials["schema"]

    test_connection(role, warehouse, database, schema)
