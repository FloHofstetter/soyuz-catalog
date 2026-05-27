from enum import Enum


class CreateConnectionConnectionType(str, Enum):
    BIGQUERY = "BIGQUERY"
    DATABRICKS = "DATABRICKS"
    GLUE = "GLUE"
    HTTP = "HTTP"
    MYSQL = "MYSQL"
    POSTGRESQL = "POSTGRESQL"
    REDSHIFT = "REDSHIFT"
    SNOWFLAKE = "SNOWFLAKE"
    SQLSERVER = "SQLSERVER"

    def __str__(self) -> str:
        return str(self.value)
