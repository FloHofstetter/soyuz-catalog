from enum import Enum


class UpdateTagsTagsSecurableTypeFullNamePatchSecurableType(str, Enum):
    CATALOG = "catalog"
    COLUMN = "column"
    SCHEMA = "schema"
    TABLE = "table"

    def __str__(self) -> str:
        return str(self.value)
