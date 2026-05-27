from enum import Enum


class CreateFunctionSqlDataAccess(str, Enum):
    CONTAINS_SQL = "CONTAINS_SQL"
    NO_SQL = "NO_SQL"
    READS_SQL_DATA = "READS_SQL_DATA"

    def __str__(self) -> str:
        return str(self.value)
