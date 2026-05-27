from enum import Enum


class OpenLineageEventEventtype(str, Enum):
    ABORT = "ABORT"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"
    OTHER = "OTHER"
    RUNNING = "RUNNING"
    START = "START"

    def __str__(self) -> str:
        return str(self.value)
