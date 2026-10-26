import json
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, StructField, IntegerType, DoubleType
from pyspark.ml.feature import VectorAssembler
from app.spark.common.config import Config

# Canonical schema of a raw smart-meter message on the sensor-data topic.
SENSOR_SCHEMA = StructType([
    StructField("meter_id", IntegerType(), True),
    StructField("voltage", DoubleType(), True),
    StructField("timestamp", DoubleType(), True),
])


class Utilities:
    def parse_kafka_message(self, value):
        """Parse a single raw Kafka JSON message (bytes) into a dict."""
        try:
            return json.loads(value.decode("utf-8"))
        except Exception as e:
            print(f"Error parsing Kafka message: {e}")
            return None

    def parse_sensor_stream(self, kafka_df):
        """Turn a raw Kafka streaming DataFrame into typed sensor columns.

        Input  : the DataFrame returned by readStream.format("kafka") (binary value).
        Output : columns meter_id (int), voltage (double), timestamp (double).
        """
        return (
            kafka_df
            .selectExpr("CAST(value AS STRING) AS json_str")
            .select(F.from_json(F.col("json_str"), SENSOR_SCHEMA).alias("d"))
            .select("d.*")
            .filter(F.col("voltage").isNotNull())
        )

    def preprocess_data(self, raw_data, feature_columns, label_column=None):
        """Assemble feature columns into a single ``features`` vector.

        If ``label_column`` is given, returns (features, label); otherwise returns
        the features plus any columns needed downstream (used at prediction time).
        """
        for col in feature_columns + ([label_column] if label_column else []):
            if col not in raw_data.columns:
                raise ValueError(f"Column '{col}' not found in input data.")

        assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")
        try:
            assembled = assembler.transform(raw_data)
            if label_column:
                return assembled.select("features", label_column)
            return assembled
        except Exception as e:
            print(f"Error in preprocessing data: {e}")
            return None

    def log_model_to_mlflow(self, model, experiment_name=None, metrics=None, params=None):
        """Log a trained model and its metadata to MLflow."""
        experiment_name = experiment_name or Config.EXPERIMENT_NAME
        metrics = metrics or {}
        params = params or {}
        try:
            import mlflow
            import mlflow.spark  # noqa: F401
            mlflow.set_tracking_uri(Config.MLFLOW_TRACKING_URI)
            mlflow.set_experiment(experiment_name)
            with mlflow.start_run():
                mlflow.spark.log_model(model, "model")
                for metric, value in metrics.items():
                    mlflow.log_metric(metric, value)
                for param, value in params.items():
                    mlflow.log_param(param, value)
                print(f"Model logged to MLflow under experiment: {experiment_name}")
        except Exception as e:
            # MLflow logging is best-effort: the model is still saved to HDFS.
            print(f"Error logging model to MLflow (continuing): {e}")
