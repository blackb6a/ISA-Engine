from engine.operand import Operand
from engine.const import INST_MNEMONIC_SEPARATOR, INST_OPERANDS_SEPARATOR, MNEMONIC
from engine.error import ISAError, ISAErrorCodes


class Instruction:
    def __len__(self):
        return self.len

    def __str__(self) -> str:
        inst = f"{self.mnemonic.decode()}"

        if self.operands is not None:
            for operand in self.operands:
                inst += f" {operand},"

            if inst[-1] == ",":
                inst = inst[:-1]

        return inst

    def __init__(self, line: bytes):
        self.mnemonic: bytes
        self.operands: list[Operand]
        self.len: int = len(line) + 1

        # anything after ';' are commment, ignore them
        line, _, _ = line.partition(b";")
        line = line.strip()

        # do nothing for empty line
        if line == b"":
            self.mnemonic = b"NOP"
            self.operands = []
            return

        # parse mnemonic and operands from the line
        mnemonic, _, operands = line.partition(INST_MNEMONIC_SEPARATOR)

        self.mnemonic = mnemonic
        self.operands = []

        if operands != b"":
            for operand in operands.split(INST_OPERANDS_SEPARATOR):
                self.operands.append(Operand(operand.strip()))

        self.validate()

    # validate the current Instruction
    def validate(self):
        if self.mnemonic not in MNEMONIC:
            raise ISAError(ISAErrorCodes.BAD_INST, "unknown mnemonic")
