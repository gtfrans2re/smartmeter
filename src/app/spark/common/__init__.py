from dataclasses import dataclass, field
from abc import abstractmethod
from typing import Optional
from pyspark.sql import SparkSession, DataFrame

from .reader import Reader
from .writer import Writer
from .utilities import Utilities

__all__ = ["Reader", "Writer", "Utilities", "TransformationBase"]


@dataclass
class TransformationBase:
    """Template for a Spark streaming job: read -> transform -> write.

    The SparkSession is NOT pinned to a master here. When the job is launched
    with ``spark-submit --master spark://spark-master:7077`` (how Airflow runs
    it) that master is used; running the file directly in local mode also works.
    """

    spark: Optional[SparkSession] = None
    PROCESS_NAME: str = ""
    source_df: Optional[DataFrame] = None
    final_df: Optional[DataFrame] = None

    def __post_init__(self):
        if self.spark is None:
            print("Creating a new SparkSession")
            self.spark = (
                SparkSession.builder
                .appName(self.PROCESS_NAME or "SmartMeterJob")
                .enableHiveSupport()
                .getOrCreate()
            )
        self.reader = Reader(self.spark)
        self.writer = Writer()

    @abstractmethod
    def transform(self):
        raise NotImplementedError("transform method must be implemented")

    @abstractmethod
    def read(self):
        raise NotImplementedError("read method must be implemented")

    @abstractmethod
    def write(self):
        raise NotImplementedError("write method must be implemented")

    def process_data(self):
        try:
            self.read()
            self.transform()
            self.write()
        except Exception as ex:
            print("An error occurred while processing the stream:", str(ex))
            raise ex
