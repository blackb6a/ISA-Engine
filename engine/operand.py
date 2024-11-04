from enum import Enum, auto
from engine.const import REGISTERS
from engine.error import ISAError, ISAErrorCodes


class OperandType(Enum):
    REGISTER = auto()
    ADDRESS = auto()
    IMMEDIATE = auto()


class Operand:
    def __str__(self) -> str:
        # convert the operand to a string representation based on its type
        match self.type:
            case OperandType.REGISTER:
                return self.data.decode()
            case OperandType.ADDRESS:
                return "[" + self.data.decode() + "]"
            case OperandType.IMMEDIATE:
                return self.data.decode()

    def __init__(self, expression: bytes):
        self.data: bytes
        self.type: OperandType = ""

        # check if the operand is a register
        if expression in REGISTERS:
            self.data = expression
            self.type = OperandType.REGISTER

        # check if the operand is memory dereference
        elif expression[:1] == b"[" and expression[-1:] == b"]":
            self.type = OperandType.ADDRESS
            self.data = expression[1:-1]

        # check if the an immediate value
        else:
            try:
                int(expression)
                self.data = expression
                self.type = OperandType.IMMEDIATE
            except ValueError:
                try:
                    # support hex num with 0x and bin num with 0b
                    int(expression, 0)
                    self.data = expression
                    self.type = OperandType.IMMEDIATE
                except ValueError:
                    pass

        if self.type == "":
            raise ISAError(ISAErrorCodes.BAD_INST, "invalid operand")
