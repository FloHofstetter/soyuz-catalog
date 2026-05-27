from enum import Enum


class FunctionInfoRoutineBodyType0(str, Enum):
    EXTERNAL = "EXTERNAL"
    SQL = "SQL"

    def __str__(self) -> str:
        return str(self.value)
