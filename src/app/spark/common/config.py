class Config:
    # HDFS Configuration (data lake). The ``ddd`` folder is both the parquet
    # landing zone written by app2 and the LOCATION of the Hive external table.
    HDFS_WAREHOUSE = "hdfs://namenode:9000/user/hive/warehouse"
    HDFS_DATA_LAKE_PATH = "hdfs://namenode:9000/user/hive/warehouse/ddd"
    HDFS_MODEL_PATH = "hdfs://namenode:9000/user/models/"

    # Hive Configuration
    HIVE_TABLE_NAME = "default.ddd"

    # MLflow Configuration.
    # Inside the Docker network MLflow is reachable at the service name on its
    # CONTAINER port (5000). The host maps it to localhost:5001 for the browser.
    MLFLOW_TRACKING_URI = "http://mlflow:5000"
    EXPERIMENT_NAME = "Voltage Prediction"
