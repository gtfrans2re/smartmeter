"""Shared Spark-submit settings for every DAG (imported, not a DAG itself)."""
from datetime import datetime

DEFAULT_ARGS = {
    "owner": "airflow",
    "start_date": datetime(2023, 1, 1),
}

# Jars pulled at submit time: Kafka source + Postgres JDBC (for the metastore).
PACKAGES = (
    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,"
    "org.postgresql:postgresql:42.7.3"
)

# One shared config. The spark.hadoop.javax.jdo.* settings point Spark's built-in
# Hive metastore at the dedicated `metastore` database in Postgres, so every job
# shares one metastore with no separate thrift server. DataNucleus auto-creates
# the schema on first use.
SPARK_CONF = {
    "spark.master": "spark://spark-master:7077",
    "spark.jars.ivy": "/opt/ivy2",
    "spark.sql.warehouse.dir": "hdfs://namenode:9000/user/hive/warehouse",
    "spark.hadoop.javax.jdo.option.ConnectionURL":
        "jdbc:postgresql://postgres:5432/metastore",
    "spark.hadoop.javax.jdo.option.ConnectionDriverName": "org.postgresql.Driver",
    "spark.hadoop.javax.jdo.option.ConnectionUserName": "airflow",
    "spark.hadoop.javax.jdo.option.ConnectionPassword": "airflow",
    "spark.hadoop.datanucleus.autoCreateSchema": "true",
    "spark.hadoop.datanucleus.fixedDatastore": "false",
    "spark.hadoop.hive.metastore.schema.verification": "false",
    # Fixed allocation: the standalone cluster has no external shuffle service,
    # so dynamic allocation is disabled for reproducibility.
    "spark.dynamicAllocation.enabled": "false",
    "spark.executor.cores": "1",
    "spark.executor.memory": "1g",
    "spark.cores.max": "2",
    "spark.metrics.conf": "/opt/spark/conf/metrics.properties",
}
