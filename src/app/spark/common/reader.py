from app.spark.common.kafkaconfig import KafkaConfig
from app.spark.common.config import Config
from pyspark.sql import SparkSession


class Reader:
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.kafka_config = KafkaConfig()

    def read_stream_from_kafka(self, topic: str = None):
        """Read streaming data from a Kafka topic.

        Defaults to the canonical raw ingest topic (``sensor-data``).
        """
        if topic is None:
            topic = self.kafka_config.input_topic
        return (
            self.spark
            .readStream
            .format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_config.bootstrap_servers)
            .option("subscribe", topic)
            .option("startingOffsets", "latest")
            .load()
        )

    def read_data_from_hdfs(self, path: str = None):
        """Read parquet data from HDFS. Defaults to the data-lake path (the ddd folder)."""
        if path is None:
            path = Config.HDFS_DATA_LAKE_PATH
        return self.spark.read.format("parquet").load(path)

    def read_from_hive(self, table_name: str = None):
        """Read from a Hive table. Requires a configured metastore (see docker-compose)."""
        if table_name is None:
            table_name = Config.HIVE_TABLE_NAME
        try:
            return self.spark.sql(f"SELECT * FROM {table_name}")
        except Exception as e:
            print(f"Error reading Hive table {table_name}: {e}")
            raise
