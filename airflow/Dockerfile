FROM apache/airflow:2.9.3-python3.12

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Install this project (editable not required inside container, copy mount recommended)
# If you prefer to bake it in:
# COPY . /opt/airflow/dbt_project
# RUN pip install -e /opt/airflow/dbt_project

ENV DBT_PROFILES_DIR=/opt/airflow/.dbt \
    PYTHONPATH=/opt/airflow
