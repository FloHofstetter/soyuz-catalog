from enum import Enum


class GenerateTemporaryModelVersionCredentialOperation(str, Enum):
    READ_MODEL_VERSION = "READ_MODEL_VERSION"
    READ_WRITE_MODEL_VERSION = "READ_WRITE_MODEL_VERSION"
    UNKNOWN_MODEL_VERSION_OPERATION = "UNKNOWN_MODEL_VERSION_OPERATION"

    def __str__(self) -> str:
        return str(self.value)
