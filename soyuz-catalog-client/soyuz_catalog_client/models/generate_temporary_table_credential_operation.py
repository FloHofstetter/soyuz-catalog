from enum import Enum


class GenerateTemporaryTableCredentialOperation(str, Enum):
    READ = "READ"
    READ_WRITE = "READ_WRITE"
    UNKNOWN_TABLE_OPERATION = "UNKNOWN_TABLE_OPERATION"

    def __str__(self) -> str:
        return str(self.value)
