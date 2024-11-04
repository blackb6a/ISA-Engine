from engine.segment import SegmentPermission


PROGRAM_COUNTER_REG_NAME = b"PC"
BASE_POINTER_REG_NAME = b"FP"
STACK_POINTER_REG_NAME = b"SP"
STACK_SEGMENT_NAME = b"STACK"
CODE_SEGMENT_NAME = b"CODE"

MNEMONIC = [
    b"JMP",
    b"JZ",
    b"JNZ",
    b"MOV",
    b"NOT",
    b"AND",
    b"OR",
    b"XOR",
    b"SAL",
    b"SAR",
    b"SHL",
    b"SHR",
    b"ROL",
    b"ROR",
    b"ADD",
    b"SUB",
    b"MULu",
    b"MUL",
    b"DIVu",
    b"DIV",
    b"EQ",
    b"NEQ",
    b"GT",
    b"GTu",
    b"GTE",
    b"GTEu",
    b"LT",
    b"LTu",
    b"LTE",
    b"LTEu",
    b"CALL",
    b"RET",
    b"SYSCALL",
    b"PUSH",
    b"POP",
    b"SWAP",
    b"COPY",
    b"NOP",
]
REGISTERS = [
    b"R1",
    b"R2",
    b"R3",
    b"R4",
    b"R5",
    b"R6",
    b"R7",
    b"R8",
    PROGRAM_COUNTER_REG_NAME,
    BASE_POINTER_REG_NAME,
    STACK_POINTER_REG_NAME,
]

INST_DELIMITER = b"\n"
INST_MNEMONIC_SEPARATOR = b" "
INST_OPERANDS_SEPARATOR = b","

FILE_SIZE_LIMIT = 0x10000
SEGMENTS = {
    b"code": {
        b"start": 0x400000,
        b"size": 0x100000,
        b"permission": SegmentPermission.READ | SegmentPermission.EXEC,
    },
    b"bss": {
        b"start": 0x500000,
        b"size": 0x10000,
        b"permission": SegmentPermission.READ | SegmentPermission.WRITE,
    },
    b"stack": {
        b"start": 0xFFF00000,
        b"size": 0x100000,
        b"permission": SegmentPermission.READ | SegmentPermission.WRITE,
    },
}
