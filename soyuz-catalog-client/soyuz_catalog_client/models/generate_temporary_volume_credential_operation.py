from enum import Enum


class GenerateTemporaryVolumeCredentialOperation(str, Enum):
    READ_VOLUME = "READ_VOLUME"
    UNKNOWN_VOLUME_OPERATION = "UNKNOWN_VOLUME_OPERATION"
    WRITE_VOLUME = "WRITE_VOLUME"

    def __str__(self) -> str:
        return str(self.value)
