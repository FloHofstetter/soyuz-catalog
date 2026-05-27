from enum import Enum


class GenerateTemporaryPathCredentialOperation(str, Enum):
    PATH_CREATE_TABLE = "PATH_CREATE_TABLE"
    PATH_READ = "PATH_READ"
    PATH_READ_WRITE = "PATH_READ_WRITE"
    UNKNOWN_PATH_OPERATION = "UNKNOWN_PATH_OPERATION"

    def __str__(self) -> str:
        return str(self.value)
