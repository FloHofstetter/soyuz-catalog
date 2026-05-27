from enum import Enum


class ConnectionInfoConnectionTypeType0(str, Enum):
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
