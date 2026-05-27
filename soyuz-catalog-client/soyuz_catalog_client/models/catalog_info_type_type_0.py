from enum import Enum


class CatalogInfoTypeType0(str, Enum):
    FOREIGN = "FOREIGN"
    MANAGED = "MANAGED"

    def __str__(self) -> str:
        return str(self.value)
