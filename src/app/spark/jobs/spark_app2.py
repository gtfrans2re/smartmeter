"""SparkApp2 - raw ingest into the HDFS data lake.

Reads raw smart-meter JSON from ``sensor-data``, adds a processing timestamp and
appends the rows as parquet to the data-lake folder (the LOCATION of the Hive
``ddd`` table). app3 registers the Hive table over this folder; app4 trains on it.
"""
import pyspark.sql.functions as F
from app.spark.common import TransformationBase, Utilities
from app.spark.common.config import Config


class Transformation(TransformationBase):
    PROCESS_NAME = "SparkApp2-Ingest"

    def __init__(self):
        super().__init__()
        self.utils = Utilities()

    def read(self):
        self.source_df = self.reader.read_stream_from_kafka()  # sensor-data

    def transform(self):
        self.final_df = (
            self.utils.parse_sensor_stream(self.source_df)
            .withColumn("processed_time", F.current_timestamp())
        )

    def write(self):
        self.writer.write_stream_to_hdfs(self.final_df, path=Config.HDFS_DATA_LAKE_PATH)


if __name__ == "__main__":
    app = Transformation()
    app.process_data()
