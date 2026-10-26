"""DAG: streaming max-voltage aggregation (spark_app1). Long-running stream."""
from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

from spark_defaults import DEFAULT_ARGS, SPARK_CONF, PACKAGES

with DAG(
    "sensor_app_job1",
    default_args=DEFAULT_ARGS,
    schedule_interval=None,
    catchup=False,
    tags=["smartmeter", "streaming"],
) as dag:
    SparkSubmitOperator(
        task_id="spark_submit_task",
        application="/opt/airflow/app/spark/jobs/spark_app1.py",
        conf={**SPARK_CONF, "spark.metrics.namespace": "spark_app1"},
        conn_id="spark_default",
        packages=PACKAGES,
        env_vars={"PYTHONPATH": "/opt/airflow"},
    )
