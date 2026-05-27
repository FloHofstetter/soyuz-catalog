from enum import Enum


class StorageCredentialOperation(str, Enum):
    READ = "READ"
    READ_WRITE = "READ_WRITE"

    def __str__(self) -> str:
        return str(self.value)
