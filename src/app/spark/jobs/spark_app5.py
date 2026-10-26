"""SparkApp5 - serve voltage predictions.

Loads the LinearRegression model trained by app4 from HDFS, reads forecast
requests from the ``forecast-data`` Kafka topic, predicts voltage and publishes
the predictions to the ``predictions-topic`` Kafka topic. Exposes a Prometheus
gauge on :8005.
"""
import json
from pyspark.sql import SparkSession
from pyspark.ml.regression import LinearRegressionModel
from prometheus_client import start_http_server, Gauge
from confluent_kafka import Producer
from app.spark.common import Utilities
from app.spark.common.config import Config
from app.spark.common.kafkaconfig import KafkaConfig

predictions_metric = Gauge("spark_app5_predictions", "Number of predictions made in the last batch")


def main():
    start_http_server(8005)
    print("Prometheus metrics server started on port 8005")

    spark = SparkSession.builder.appName("Spark_App5-Serve").getOrCreate()
    utils = Utilities()
    kafka = KafkaConfig()

    model_path = Config.HDFS_MODEL_PATH + "model_lr"
    print(f"Loading model from HDFS: {model_path}")
    try:
        model = LinearRegressionModel.load(model_path)
    except Exception as e:
        print(f"Error loading model (run app4 first): {e}")
        return

    reader = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka.bootstrap_servers) \
        .option("subscribe", kafka.forecast_topic) \
        .option("startingOffsets", "latest") \
        .load()

    requests = utils.parse_sensor_stream(reader)  # meter_id, voltage, timestamp
    features = utils.preprocess_data(requests, ["timestamp", "meter_id"])

    producer_conf = {'bootstrap.servers': kafka.bootstrap_servers, 'client.id': 'spark-app5-producer'}

    def predict_batch(batch_df, batch_id):
        if batch_df.rdd.isEmpty():
            return
        predicted = model.transform(batch_df).select("meter_id", "timestamp", "prediction")
        rows = predicted.collect()
        predictions_metric.set(len(rows))
        producer = Producer(producer_conf)
        for row in rows:
            message = {
                "meter_id": row["meter_id"],
                "timestamp": row["timestamp"],
                "predicted_voltage": row["prediction"],
            }
            producer.produce(kafka.predictions_topic, value=json.dumps(message).encode("utf-8"))
        producer.flush()
        print(f"Batch {batch_id}: published {len(rows)} predictions")

    (
        features.writeStream
        .outputMode("append")
        .option("checkpointLocation", "/tmp/spark-app5-checkpoint")
        .foreachBatch(predict_batch)
        .start()
        .awaitTermination()
    )


if __name__ == "__main__":
    main()
