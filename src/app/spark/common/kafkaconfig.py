class KafkaConfig:
    """Central Kafka settings shared by every Spark job and the Locust producer.

    Canonical ingest contract for the whole pipeline
    ------------------------------------------------
    Topic   : ``sensor-data``  (created by src/scripts/kafka-init-topic.sh)
    Payload : JSON, UTF-8 encoded
              {"meter_id": <int>, "voltage": <float>, "timestamp": <float epoch seconds>}

    Every producer (Locust) and every streaming consumer (spark_app1, spark_app2)
    MUST agree on this topic and schema, otherwise no data reaches Spark.
    """

    def __init__(self):
        self.bootstrap_servers = "kafka:9092"

        # Raw smart-meter readings produced by Locust and read by app1/app2.
        self.input_topic = "sensor-data"

        # app1 publishes the per-window maximum voltage here.
        self.output_topic = "processed-voltage"

        # app5 reads forecast requests here and publishes predictions to predictions-topic.
        self.forecast_topic = "forecast-data"
        self.predictions_topic = "predictions-topic"

        self.checkpoint_location = "/tmp/spark-app1-checkpoint"
