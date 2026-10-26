"""SparkApp3 - register the Hive external table over the data-lake folder.

Creates ``default.ddd`` as an EXTERNAL parquet table pointing at the folder that
app2 writes to, so the ingested data is queryable through the metastore.
Requires a configured Hive metastore (see the spark.hadoop.* settings in the DAG).
"""
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("CreateHiveTable")
    .enableHiveSupport()
    .getOrCreate()
)

spark.sql("""
    CREATE EXTERNAL TABLE IF NOT EXISTS default.ddd (
        meter_id INT,
        voltage DOUBLE,
        timestamp DOUBLE,
        processed_time TIMESTAMP
    )
    STORED AS PARQUET
    LOCATION 'hdfs://namenode:9000/user/hive/warehouse/ddd'
""")

# Refresh so newly landed parquet files are visible, then show a sample.
spark.sql("MSCK REPAIR TABLE default.ddd")
print("######### Hive table default.ddd is ready #########")
spark.sql("SELECT * FROM default.ddd LIMIT 10").show()
print(spark.sql("DESCRIBE EXTENDED default.ddd").collect())
