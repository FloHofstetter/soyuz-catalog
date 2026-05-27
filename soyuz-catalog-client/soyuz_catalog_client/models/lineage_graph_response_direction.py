from enum import Enum


class LineageGraphResponseDirection(str, Enum):
    DOWNSTREAM = "downstream"
    UPSTREAM = "upstream"

    def __str__(self) -> str:
        return str(self.value)
