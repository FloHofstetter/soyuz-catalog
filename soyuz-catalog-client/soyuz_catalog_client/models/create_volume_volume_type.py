from enum import Enum


class CreateVolumeVolumeType(str, Enum):
    EXTERNAL = "EXTERNAL"
    MANAGED = "MANAGED"

    def __str__(self) -> str:
        return str(self.value)
