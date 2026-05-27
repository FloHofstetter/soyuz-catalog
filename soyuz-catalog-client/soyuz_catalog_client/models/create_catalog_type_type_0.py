from enum import Enum


class CreateCatalogTypeType0(str, Enum):
    FOREIGN = "FOREIGN"
    MANAGED = "MANAGED"

    def __str__(self) -> str:
        return str(self.value)
