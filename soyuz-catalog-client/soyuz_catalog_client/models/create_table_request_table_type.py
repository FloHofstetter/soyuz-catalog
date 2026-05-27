from enum import Enum


class CreateTableRequestTableType(str, Enum):
    EXTERNAL = "EXTERNAL"
    MANAGED = "MANAGED"

    def __str__(self) -> str:
        return str(self.value)
