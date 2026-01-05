
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
import os

# Define default arguments
default_args = {
    'owner': 'apexflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
with DAG(
    'apexflow_weekly_retraining',
    default_args=default_args,
    description='Weekly continuous training pipeline for F1 Lap Time Predictor',
    schedule_interval='@weekly', # Runs once a week (midnight on Sunday)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['apexflow', 'training'],
) as dag:

    # Task: Run the continuous training script
    # We assume the script is mounted/accessible at /app/scripts/ or relative to AIRFLOW_HOME
    # Adjust path as necessary for the deployment environment.
    # For local dev, we point to the absolute path or relative if in same project root.
    
    # Using relative path assuming Airflow runs from project root or has PYTHONPATH set
    # Using python -m scripts.continuous_training_pipeline might be safer if modules are set up
    
    retraining_task = BashOperator(
        task_id='run_continuous_training',
        bash_command='python scripts/continuous_training_pipeline.py',
        env={**os.environ, 'PYTHONPATH': '.:$PYTHONPATH'} # Ensure src is importable
    )

    retraining_task
