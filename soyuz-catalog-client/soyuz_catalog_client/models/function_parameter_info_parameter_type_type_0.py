from enum import Enum


class FunctionParameterInfoParameterTypeType0(str, Enum):
    COLUMN = "COLUMN"
    PARAM = "PARAM"

    def __str__(self) -> str:
        return str(self.value)
