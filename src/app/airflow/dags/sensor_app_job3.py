"""DAG: register the Hive external table over the data lake (spark_app3). Batch."""
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

from spark_defaults import DEFAULT_ARGS, SPARK_CONF, PACKAGES

with DAG(
    "sensor_app_job3",
    default_args=DEFAULT_ARGS,
    schedule_interval=None,
    catchup=False,
    tags=["smartmeter", "batch"],
) as dag:
    SparkSubmitOperator(
        task_id="spark_submit_task",
        application="/opt/airflow/app/spark/jobs/spark_app3.py",
        conf=SPARK_CONF,
        conn_id="spark_default",
        packages=PACKAGES,
        env_vars={"PYTHONPATH": "/opt/airflow"},
    )
