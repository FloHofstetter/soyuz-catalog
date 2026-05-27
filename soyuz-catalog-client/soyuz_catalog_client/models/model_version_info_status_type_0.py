from enum import Enum


class ModelVersionInfoStatusType0(str, Enum):
    FAILED_REGISTRATION = "FAILED_REGISTRATION"
    MODEL_VERSION_STATUS_UNKNOWN = "MODEL_VERSION_STATUS_UNKNOWN"
    PENDING_REGISTRATION = "PENDING_REGISTRATION"
    READY = "READY"

    def __str__(self) -> str:
        return str(self.value)
