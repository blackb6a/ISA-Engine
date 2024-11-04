import re

from engine.operand import Operand, OperandType
from engine.const import REGISTERS, PROGRAM_COUNTER_REG_NAME
from engine.error import ISAError, ISAErrorCodes
from engine.util import to_u32


class Registers:
    def __init__(self):
        self._regs: dict[bytes, int] = {}

        # initialize all registers to 0
        for reg in REGISTERS:
            self._regs[reg] = 0

    # return a copy of the register dictionary
    def get_regs(self) -> dict[bytes, int]:
        return self._regs.copy()

    # return the value of the specified register
    def get_reg(self, name: bytes) -> int:
        if not (name in REGISTERS) or name == PROGRAM_COUNTER_REG_NAME:
            raise ISAError(ISAErrorCodes.BAD_INST, "invalid operand")
        return self._regs[name]

    # set the value of the specified register
    def set_reg(self, name: bytes, value: int):
        if not (name in REGISTERS) or name == PROGRAM_COUNTER_REG_NAME:
            raise ISAError(ISAErrorCodes.BAD_INST, "invalid operand")
        self._regs[name] = to_u32(value)

    # return the value of the program counter register
    def get_program_counter(self) -> int:
        return self._regs[PROGRAM_COUNTER_REG_NAME]

    # set the value of the program counter register
    def set_program_counter(self, new_pc: int):
        self._regs[PROGRAM_COUNTER_REG_NAME] = to_u32(new_pc)

    # evaluate the operand and return the result along with a flag indicating if the value is a memory address
    def eval(self, operand: Operand) -> tuple[int, bool]:
        match operand.type:
            case OperandType.REGISTER:
                return (self.get_reg(operand.data), False)
            case OperandType.ADDRESS:
                matches = re.search(b"(.*)([+*-])(.*)", operand.data)
                value = 0
                if matches is None:
                    value = self.get_reg(operand.data.strip())
                else:
                    # resolve the register value experssion in operand, e.g. [R1 + 5]
                    reg, op, imm = matches.groups()
                    reg_val = self.get_reg(reg.strip())
                    imm_val = int(imm, 0)
                    match (op):
                        case b"+":
                            value = reg_val + imm_val
                        case b"-":
                            value = reg_val - imm_val
                        case b"*":
                            value = reg_val * imm_val
                return (value, True)
            case OperandType.IMMEDIATE:
                value = int(operand.data, 0)
                return (to_u32(value), False)
            case _:
                raise ISAError(ISAErrorCodes.BAD_INST, "BAD EVAL")
