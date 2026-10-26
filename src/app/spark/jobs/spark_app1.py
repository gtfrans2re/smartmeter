"""SparkApp1 - streaming max-voltage aggregation.

Reads raw smart-meter JSON from the ``sensor-data`` Kafka topic, computes the
maximum voltage per 1-minute event-time window, exposes it as a Prometheus
gauge on :8001 and republishes each window result to the ``processed-voltage``
Kafka topic.
"""
import json
import pyspark.sql.functions as F
from app.spark.common import TransformationBase, Utilities
from app.spark.common.kafkaconfig import KafkaConfig
from prometheus_client import start_http_server, Gauge
from confluent_kafka import Producer

# Prometheus metrics endpoint for this driver.
start_http_server(8001)
max_voltage_metric = Gauge('spark_app1_max_voltage', 'Maximum voltage processed by SparkApp1')

_kafka = KafkaConfig()
kafka_conf = {'bootstrap.servers': _kafka.bootstrap_servers, 'client.id': 'spark-app1-producer'}


class Transformation(TransformationBase):
    PROCESS_NAME = "SparkApp1-MaxVoltage"

    def __init__(self):
        super().__init__()
        self.utils = Utilities()
        self.producer = Producer(kafka_conf)

    def read(self):
        self.source_df = self.reader.read_stream_from_kafka()  # sensor-data

    def transform(self):
        parsed = self.utils.parse_sensor_stream(self.source_df)
        self.final_df = (
            parsed
            .withColumn("event_time", F.to_timestamp(F.col("timestamp")))
            .withWatermark("event_time", "5 minutes")
            .groupBy(F.window("event_time", "1 minute"))
            .agg(F.max("voltage").alias("max_voltage"))
        )
        print("Transformation ready")

    def write(self):
        producer = self.producer

        def handle_batch(batch_df, batch_id):
            for row in batch_df.collect():
                max_voltage = row["max_voltage"]
                if max_voltage is None:
                    continue
                max_voltage_metric.set(max_voltage)
                message = {"max_voltage": max_voltage, "window": str(row["window"])}
                producer.produce(
                    topic=KafkaConfig().output_topic,
                    value=json.dumps(message).encode("utf-8"),
                )
                producer.flush()
                print(f"Max voltage published: {message}")

        (
            self.final_df.writeStream
            .outputMode("update")
            .option("checkpointLocation", "/tmp/spark-app1-checkpoint")
            .foreachBatch(handle_batch)
            .start()
            .awaitTermination()
        )


if __name__ == "__main__":
    app = Transformation()
    app.process_data()
