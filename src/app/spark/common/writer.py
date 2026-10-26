from app.spark.common.kafkaconfig import KafkaConfig
from app.spark.common.config import Config
from pyspark.ml.regression import LinearRegressionModel


class Writer:
    def __init__(self):
        self.kafka_config = KafkaConfig()

    def write_stream_to_kafka(self, df, topic: str = None, checkpoint: str = None):
        """Write a streaming DataFrame that already has a string ``value`` column to Kafka."""
        if topic is None:
            topic = self.kafka_config.output_topic
        if checkpoint is None:
            checkpoint = f"/tmp/checkpoint-kafka-{topic}"
        return (
            df.writeStream
            .format("kafka")
            .option("kafka.bootstrap.servers", self.kafka_config.bootstrap_servers)
            .option("topic", topic)
            .option("checkpointLocation", checkpoint)
            .outputMode("append")
            .start()
            .awaitTermination()
        )

    def write_stream_to_hdfs(self, df, path: str = None, checkpoint: str = None):
        """Append a streaming DataFrame to HDFS as parquet (the data lake landing zone)."""
        if path is None:
            path = Config.HDFS_DATA_LAKE_PATH
        if checkpoint is None:
            checkpoint = f"{path}/_checkpoints"
        return (
            df.writeStream
            .format("parquet")
            .option("checkpointLocation", checkpoint)
            .option("path", path)
            .outputMode("append")
            .trigger(processingTime="30 seconds")
            .start()
            .awaitTermination()
        )

    # Kept for backward compatibility with older call sites.
    write_stream_to_delta = write_stream_to_hdfs

    def write_batch_to_hdfs(self, df, path: str, mode: str = "overwrite"):
        """Write a (non-streaming) batch DataFrame to HDFS as parquet."""
        df.write.mode(mode).parquet(path)
        print(f"Batch data written to HDFS: {path}")

    def save_model_to_hdfs(self, model, path: str = None):
        """Save a trained Spark ML model to HDFS."""
        if path is None:
            path = Config.HDFS_MODEL_PATH + "model_lr"
        model.write().overwrite().save(path)
        print(f"Model saved to HDFS: {path}")

    def write_to_hive(self, df, table_name: str = None, mode="overwrite"):
        """Write a DataFrame to a Hive table (requires a configured metastore)."""
        if table_name is None:
            table_name = Config.HIVE_TABLE_NAME
        try:
            df.write.mode(mode).saveAsTable(table_name)
            print(f"Data successfully written to Hive table: {table_name}")
        except Exception as e:
            print(f"Error writing to Hive table {table_name}: {e}")
            raise
