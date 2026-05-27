from enum import Enum


class CreateTableRequestDataSourceFormat(str, Enum):
    AVRO = "AVRO"
    CSV = "CSV"
    DELTA = "DELTA"
    ICEBERG = "ICEBERG"
    JSON = "JSON"
    ORC = "ORC"
    PARQUET = "PARQUET"
    TEXT = "TEXT"

    def __str__(self) -> str:
        return str(self.value)
