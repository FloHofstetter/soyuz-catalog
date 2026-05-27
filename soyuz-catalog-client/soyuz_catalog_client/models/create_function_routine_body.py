from enum import Enum


class CreateFunctionRoutineBody(str, Enum):
    EXTERNAL = "EXTERNAL"
    SQL = "SQL"

    def __str__(self) -> str:
        return str(self.value)
