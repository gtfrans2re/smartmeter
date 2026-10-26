"""SparkApp4 - train a voltage-prediction model.

Reads the ingested readings from the HDFS data lake (the parquet folder written
by app2), trains a LinearRegression model to predict ``voltage`` from the time
features, logs it to MLflow and saves it to HDFS for app5 to serve.
"""
from pyspark.sql import SparkSession
from pyspark.ml.regression import LinearRegression
from app.spark.common import Writer, Utilities
from app.spark.common.config import Config


def main():
    spark = (
        SparkSession.builder
        .appName("Spark_App4-Train")
        .enableHiveSupport()
        .getOrCreate()
    )

    writer = Writer()
    utils = Utilities()

    # Read raw data straight from the HDFS data lake (no metastore needed).
    print(f"Reading training data from: {Config.HDFS_DATA_LAKE_PATH}")
    try:
        raw_data = spark.read.parquet(Config.HDFS_DATA_LAKE_PATH)
    except Exception as e:
        print(f"Error reading data lake (has app2 produced any data yet?): {e}")
        return

    if raw_data.rdd.isEmpty():
        print("No data in the lake yet. Run the Locust load and app2 first. Exiting.")
        return

    # Predict voltage from time + meter features.
    feature_columns = ["timestamp", "meter_id"]
    label_column = "voltage"
    data = utils.preprocess_data(raw_data, feature_columns, label_column)
    if data is None:
        print("Data preprocessing failed. Exiting.")
        return

    train_data, test_data = data.randomSplit([0.8, 0.2], seed=123)

    print("Training the model...")
    lr = LinearRegression(featuresCol="features", labelCol=label_column)
    lr_model = lr.fit(train_data)

    metrics = {
        "rmse": lr_model.summary.rootMeanSquaredError,
        "r2": lr_model.summary.r2,
    }
    print(f"Model evaluation: RMSE = {metrics['rmse']:.4f}, R2 = {metrics['r2']:.4f}")

    utils.log_model_to_mlflow(
        lr_model,
        experiment_name=Config.EXPERIMENT_NAME,
        metrics=metrics,
        params={"algorithm": "LinearRegression", "features": ",".join(feature_columns)},
    )

    # Persist predictions (batch) and the model to HDFS.
    predictions = lr_model.transform(test_data)
    writer.write_batch_to_hdfs(
        predictions.select("features", label_column, "prediction"),
        path="hdfs://namenode:9000/user/hive/warehouse/predictions",
    )
    model_path = Config.HDFS_MODEL_PATH + "model_lr"
    writer.save_model_to_hdfs(lr_model, model_path)

    print("Spark App4 completed successfully!")


if __name__ == "__main__":
    main()
