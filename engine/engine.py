from asyncio import get_running_loop, sleep, AbstractEventLoop, Event
from enum import Enum, auto
import random
import time
from urllib.request import urlopen
from urllib.parse import urlparse
import os
import socket

from engine.instruction import Instruction
from engine.const import (
    FILE_SIZE_LIMIT,
    INST_DELIMITER,
    BASE_POINTER_REG_NAME,
    SEGMENTS,
    STACK_POINTER_REG_NAME,
)
from engine.error import ISAError, ISAErrorCodes
from engine.event_emitter import EventEmitter, EventType
from engine.file_manager import FileManager
from engine.memory_manager import MemoryManager
from engine.operand import Operand, OperandType
from engine.register import Registers
from engine.util import (
    add32,
    and32,
    div32,
    eq32,
    gt32,
    gte32,
    gteu32,
    gtu32,
    lt32,
    lte32,
    lteu32,
    ltu32,
    mul32,
    neq32,
    not32,
    or32,
    rol32,
    ror32,
    sal32,
    sar32,
    shl32,
    shr32,
    sub32,
    uint32_to_int32,
    xor32,
)


class EngineState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    STEPPING = auto()
    UNKNOWN = auto()


class Engine:
    def __init__(
        self,
        program: bytes,
        stdin_no: int = 0,
        stdout_no: int = 1,
        vfiles: dict[bytes, bytes] | None = None,
        event_loop: AbstractEventLoop | None = None,
    ):
        try:
            self.state: EngineState = EngineState.STOPPED
            self.stdin_no: int = stdin_no
            self.stdout_no: int = stdout_no
            self.exit_code: int = 0
            self._registers: Registers = Registers()
            self._memory: MemoryManager = MemoryManager()
            self._files: FileManager = FileManager(vfiles)
            self.loop = event_loop
        except Exception as e:
            raise ISAError(ISAErrorCodes.BAD_CONFIG, str(e)) from e

        self._memory.map(
            b"code",
            SEGMENTS[b"code"][b"start"],
            SEGMENTS[b"code"][b"size"],
            SEGMENTS[b"code"][b"permission"],
        )
        self._memory.map(
            b"bss",
            SEGMENTS[b"bss"][b"start"],
            SEGMENTS[b"bss"][b"size"],
            SEGMENTS[b"bss"][b"permission"],
        )
        self._memory.map(
            b"stack",
            SEGMENTS[b"stack"][b"start"],
            SEGMENTS[b"stack"][b"size"],
            SEGMENTS[b"stack"][b"permission"],
        )

        # init
        self.init(program)

        # async related
        self.event_emitter: EventEmitter = EventEmitter()
        self.event_continue = Event()

    def init(self, program: bytes):
        # init breakpoints
        self.breakpoints: list[int] = []

        # init program
        self._memory.segments[b"code"].mem[: len(program)] = program

        # init registers
        self._registers.set_reg(
            BASE_POINTER_REG_NAME,
            SEGMENTS[b"stack"][b"start"] + SEGMENTS[b"stack"][b"size"] - 0x10,
        )
        self._registers.set_reg(
            STACK_POINTER_REG_NAME,
            SEGMENTS[b"stack"][b"start"] + SEGMENTS[b"stack"][b"size"] - 0x10,
        )
        self._registers.set_program_counter(SEGMENTS[b"code"][b"start"])

        random.seed(int(time.time()))

    # add breakpoint
    def add_breakpoint(self, breakpoint: int):
        self.breakpoints.append(breakpoint)

    # remove breakpoint
    def remove_breakpoint(self, breakpoint: int):
        if breakpoint in self.breakpoints:
            self.breakpoints.remove(breakpoint)

    # import files to the virtual file manager
    def import_vfiles(self, vfiles: dict[bytes, bytes]):
        self._files.insert(vfiles)

    # clear files in the virtual file manager
    def prune_vfiles(self):
        self._files.prune()

    # get asyncio event loop of the current thread
    def get_running_loop(self):
        if self.loop is None:
            return get_running_loop()
        return self.loop

    def get_current_regs(self):
        return self._registers.get_regs()

    def get_current_memory(self):
        return self._memory.segments

    # parse the assembly code at the specified program counter (pc)
    def parse_code_at(self, pc: int) -> bytes:
        segment = self._memory.find_segment_by_addr(pc)
        if not segment.executable:
            raise ISAError(ISAErrorCodes.SEG_FAULT, "segment is not writable")
        line_end_pos = segment.find(INST_DELIMITER, pc)
        if line_end_pos == -1:
            raise ISAError(ISAErrorCodes.BAD_INST, "instruction ends unexpectedly")

        line = segment[pc:line_end_pos].tobytes()

        return Instruction(line)

    # evaluate the operand and return the immediate value
    def eval(self, operand: Operand) -> int:
        op_val, dereference = self._registers.eval(operand)

        if dereference:
            return self._memory.get32(op_val)

        return op_val

    # pop a 32-bit value from the stack
    def stack_pop(self) -> int:
        sp = self._registers.get_reg(STACK_POINTER_REG_NAME)
        value = self._memory.get32(sp)
        sp += 4
        self._registers.set_reg(STACK_POINTER_REG_NAME, sp)

        return value

    # push a 32-bit value onto the stack
    def stack_push(self, value: int):
        sp = self._registers.get_reg(STACK_POINTER_REG_NAME)
        sp -= 4
        self._registers.set_reg(STACK_POINTER_REG_NAME, sp)

        self._memory.set32(sp, value)

    # jmp to code with the location according to the operand value and its sign
    # jmp 123 => jmp to code at 123
    # jmp +123/-123 => jmp to code at <current PC> +/- 123
    def jmp_to(self, operand: Operand):
        new_pc = self.eval(operand)
        if operand.type == OperandType.IMMEDIATE and (
            operand.data[:1] == b"+" or operand.data[:1] == b"-"
        ):
            new_pc += self._registers.get_program_counter()

        if new_pc < 0:
            raise ISAError(ISAErrorCodes.BAD_INST, "invalid PC")

        self._registers.set_program_counter(new_pc)

    # assign a value to the specified operand
    def assign_value(self, dest: Operand, value: int):
        match dest.type:
            case OperandType.IMMEDIATE:
                raise ISAError(
                    ISAErrorCodes.BAD_INST, "destination operand cannot be an immediate"
                )
            case OperandType.REGISTER:
                self._registers.set_reg(dest.data, value)
            case OperandType.ADDRESS:
                addr, _ = self._registers.eval(dest)
                self._memory.set32(addr, value)

    # resolve the instruction works
    async def resolve_inst(self, inst: Instruction):
        regs = self._registers
        mem = self._memory
        await self.event_emitter.trigger(EventType.STEP, "before", inst)

        match inst.mnemonic:
            # Jump instructions
            ## Unconditional jump
            case b"JMP":
                self.jmp_to(inst.operands[0])

            ## Conditional jump
            case b"JZ":
                condition_flag = self.stack_pop()
                if condition_flag == 0:
                    self.jmp_to(inst.operands[0])

            case b"JNZ":
                condition_flag = self.stack_pop()
                if condition_flag != 0:
                    self.jmp_to(inst.operands[0])

            # Assignment
            case b"MOV":
                if (
                    inst.operands[0].type == OperandType.ADDRESS
                    and inst.operands[1].type == OperandType.ADDRESS
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "memory-to-memory instruction is not supported",
                    )
                self.assign_value(inst.operands[0], self.eval(inst.operands[1]))

            # Bitwise operations
            case b"NOT":
                self.assign_value(inst.operands[0], not32(self.eval(inst.operands[0])))

            case b"AND":
                if (
                    inst.operands[0].type == OperandType.ADDRESS
                    and inst.operands[1].type == OperandType.ADDRESS
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "memory-to-memory instruction is not supported",
                    )
                self.assign_value(
                    inst.operands[0],
                    and32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            case b"OR":
                if (
                    inst.operands[0].type == OperandType.ADDRESS
                    and inst.operands[1].type == OperandType.ADDRESS
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "memory-to-memory instruction is not supported",
                    )
                self.assign_value(
                    inst.operands[0],
                    or32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            case b"XOR":
                if (
                    inst.operands[0].type == OperandType.ADDRESS
                    and inst.operands[1].type == OperandType.ADDRESS
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "memory-to-memory instruction is not supported",
                    )
                self.assign_value(
                    inst.operands[0],
                    xor32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            # SHIFT ARITHMETIC
            case b"SAL":
                if inst.operands[1].type == OperandType.ADDRESS:
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "shift operand must be a register or a immediate",
                    )
                self.assign_value(
                    inst.operands[0],
                    sal32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            case b"SAR":
                if inst.operands[1].type == OperandType.ADDRESS:
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "shift operand must be a register or a immediate",
                    )
                self.assign_value(
                    inst.operands[0],
                    sar32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            # SHIFT LOGICAL
            case b"SHL":
                if inst.operands[1].type == OperandType.ADDRESS:
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "shift operand must be a register or a immediate",
                    )
                self.assign_value(
                    inst.operands[0],
                    shl32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            case b"SHR":
                if inst.operands[1].type == OperandType.ADDRESS:
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "shift operand must be a register or a immediate",
                    )
                self.assign_value(
                    inst.operands[0],
                    shr32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            # ROTATE
            case b"ROL":
                if inst.operands[1].type == OperandType.ADDRESS:
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "rotate operand must be a register or a immediate",
                    )
                self.assign_value(
                    inst.operands[0],
                    rol32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            case b"ROR":
                if inst.operands[1].type == OperandType.ADDRESS:
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "rotate operand must be a register or a immediate",
                    )
                self.assign_value(
                    inst.operands[0],
                    ror32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            # Arimetric operations
            case b"ADD":
                if (
                    inst.operands[0].type == OperandType.ADDRESS
                    and inst.operands[1].type == OperandType.ADDRESS
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "memory-to-memory instruction is not supported",
                    )
                self.assign_value(
                    inst.operands[0],
                    add32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            case b"SUB":
                if (
                    inst.operands[0].type == OperandType.ADDRESS
                    and inst.operands[1].type == OperandType.ADDRESS
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "memory-to-memory instruction is not supported",
                    )
                self.assign_value(
                    inst.operands[0],
                    sub32(self.eval(inst.operands[0]), self.eval(inst.operands[1])),
                )

            case b"MULu":
                if (
                    inst.operands[0].type != OperandType.REGISTER
                    or inst.operands[1].type != OperandType.REGISTER
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "MULu source and destination operand must be a register",
                    )
                lo, hi = self.eval(inst.operands[0]), self.eval(inst.operands[1])
                lo, hi = mul32(lo, hi)

                self.assign_value(inst.operands[0], lo)
                self.assign_value(inst.operands[1], hi)

            case b"MUL":
                if (
                    inst.operands[0].type != OperandType.REGISTER
                    or inst.operands[1].type != OperandType.REGISTER
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "MUL source and destination operand must be a register",
                    )

                lo, hi = self.eval(inst.operands[0]), self.eval(inst.operands[1])
                lo, hi = uint32_to_int32(lo), uint32_to_int32(hi)
                lo, hi = mul32(lo, hi)

                self.assign_value(inst.operands[0], lo)
                self.assign_value(inst.operands[1], hi)

            case b"DIVu":
                if (
                    inst.operands[0].type != OperandType.REGISTER
                    or inst.operands[1].type != OperandType.REGISTER
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "DIVu source and destination operand must be a register",
                    )
                div, mod = self.eval(inst.operands[0]), self.eval(inst.operands[1])
                div, mod = div32(div, mod)

                self.assign_value(inst.operands[0], div)
                self.assign_value(inst.operands[1], mod)

            case b"DIV":
                if (
                    inst.operands[0].type != OperandType.REGISTER
                    or inst.operands[1].type != OperandType.REGISTER
                ):
                    raise ISAError(
                        ISAErrorCodes.BAD_INST,
                        "DIV source and destination operand must be a register",
                    )

                div, mod = self.eval(inst.operands[0]), self.eval(inst.operands[1])
                div, mod = uint32_to_int32(div), uint32_to_int32(mod)
                div, mod = div32(div, mod)

                self.assign_value(inst.operands[0], div)
                self.assign_value(inst.operands[1], mod)

            # Compare operations
            case b"EQ":
                self.stack_push(
                    int(eq32(self.eval(inst.operands[0]), self.eval(inst.operands[1])))
                )

            case b"NEQ":
                self.stack_push(
                    int(neq32(self.eval(inst.operands[0]), self.eval(inst.operands[1])))
                )

            case b"GT":
                self.stack_push(
                    int(gt32(self.eval(inst.operands[0]), self.eval(inst.operands[1])))
                )

            case b"GTu":
                self.stack_push(
                    int(gtu32(self.eval(inst.operands[0]), self.eval(inst.operands[1])))
                )

            case b"GTE":
                self.stack_push(
                    int(gte32(self.eval(inst.operands[0]), self.eval(inst.operands[1])))
                )

            case b"GTEu":
                self.stack_push(
                    int(
                        gteu32(self.eval(inst.operands[0]), self.eval(inst.operands[1]))
                    )
                )

            case b"LT":
                self.stack_push(
                    int(lt32(self.eval(inst.operands[0]), self.eval(inst.operands[1])))
                )

            case b"LTu":
                self.stack_push(
                    int(ltu32(self.eval(inst.operands[0]), self.eval(inst.operands[1])))
                )

            case b"LTE":
                self.stack_push(
                    int(lte32(self.eval(inst.operands[0]), self.eval(inst.operands[1])))
                )

            case b"LTEu":
                self.stack_push(
                    int(
                        lteu32(self.eval(inst.operands[0]), self.eval(inst.operands[1]))
                    )
                )

            # Function operations
            case b"CALL":
                pc = regs.get_program_counter()
                self.stack_push(pc)
                regs.set_program_counter(self.eval(inst.operands[0]))

            case b"RET":
                ret_addr = self.stack_pop()
                regs.set_program_counter(ret_addr)

            case b"SYSCALL":
                reg_list = regs.get_regs()
                ret_value = await self.syscall(
                    reg_list[b"R8"],
                    reg_list[b"R1"],
                    reg_list[b"R2"],
                    reg_list[b"R3"],
                )
                regs.set_reg(b"R8", ret_value)

            # Stack operations
            case b"PUSH":
                self.stack_push(self.eval(inst.operands[0]))

            case b"POP":
                value = self.stack_pop()
                self.assign_value(inst.operands[0], value)

            case b"SWAP":
                sp = regs.get_reg(STACK_POINTER_REG_NAME)
                target = sub32(sp, self.eval(inst.operands[0]) * 4)

                value1 = mem.get32(sp)
                value2 = mem.get32(target)
                mem.set32(sp, value2)
                mem.set32(target, value1)

            case b"COPY":
                sp = regs.get_reg(STACK_POINTER_REG_NAME)
                target = sub32(sp, self.eval(inst.operands[0]) * 4)
                value = mem.get32(target)

                self.stack_push(value)

            case b"NOP":
                pass

            case _:
                raise ISAError(ISAErrorCodes.BAD_INST, "unknown mnemonic")

        await self.event_emitter.trigger(EventType.STEP, "after", inst)

    # handle system calls
    async def syscall(
        self,
        syscall_number: int,
        arg1: int,
        arg2: int,
        arg3: int,
    ) -> int:

        # SYSCALL_INPUT
        @self.event_emitter.emit(EventType.INPUT)
        async def syscall_input(buf, length):
            loop = self.get_running_loop()
            fut = loop.create_future()

            def __check_for_input():
                try:
                    data = os.read(self.stdin_no, length)
                except Exception as e:
                    loop.remove_reader(self.stdin_no)
                    fut.set_exception(e)
                else:
                    loop.remove_reader(self.stdin_no)
                    fut.set_result(data)

            loop.add_reader(self.stdin_no, __check_for_input)

            data = await fut

            read_len = len(data)
            self._memory[buf : buf + read_len] = data
            return read_len

        # SYSCALL_OUTPUT
        @self.event_emitter.emit(EventType.OUTPUT)
        async def syscall_output(buf, length):
            loop = self.get_running_loop()
            fut = loop.create_future()

            data = self._memory[buf : buf + length].tobytes()

            def __wait_for_output():
                try:
                    out_len = os.write(self.stdout_no, data)
                except Exception as e:
                    loop.remove_writer(self.stdout_no)
                    fut.set_exception(e)
                else:
                    loop.remove_writer(self.stdout_no)
                    fut.set_result(out_len)

            loop.add_writer(self.stdout_no, __wait_for_output)

            return await fut

        # SYSCALL_EXIT
        @self.event_emitter.emit(EventType.EXIT)
        async def syscall_exit(exit_code):
            self.stop()
            self.exit_code = exit_code
            return exit_code

        # SYSCALL_READFILE
        async def syscall_readfile(filename, buf, length):
            filename = self._memory.get_cstring(filename)
            file = self._files[filename]
            if file is not None:
                read_len = min(length, file["size"])
                self._memory[buf : buf + read_len] = file["content"][:read_len]
                return read_len
            return -1

        # SYSCALL_LIST_FILES
        @self.event_emitter.emit(EventType.OUTPUT)
        async def syscall_list_files():
            loop = self.get_running_loop()
            fut = loop.create_future()

            file_numbers = len(self._files.list())
            data = b"\n".join(self._files.list()) + b"\n"

            def __wait_for_output():
                try:
                    os.write(self.stdout_no, data)
                except Exception as e:
                    loop.remove_writer(self.stdout_no)
                    fut.set_exception(e)
                else:
                    if data is not None:
                        loop.remove_writer(self.stdout_no)
                        fut.set_result(file_numbers)

            loop.add_writer(self.stdout_no, __wait_for_output)

            return await fut

        # SYSCALL_EXEC
        async def syscall_exec(filename):
            command = self._memory.get_cstring(filename)
            file = self._files[command]

            if file is not None:
                self.init(file["content"])
            return -1

        # SYSCALL_DOWNLOAD
        @self.event_emitter.emit(EventType.DOWNLOAD)
        async def syscall_download(filename, url):
            filename = self._memory.get_cstring(filename)
            url = self._memory.get_cstring(url)

            scheme_blacklist = [
                b"file",
                b"gopher",
                b"php",
                b"dict",
                b"ftp",
                b"glob",
                b"data",
            ]
            scheme = urlparse(url).scheme
            netloc = urlparse(url).netloc
            if (
                scheme in scheme_blacklist
                or socket.gethostbyname(netloc) == "127.0.0.1"
            ):
                raise ISAError(ISAErrorCodes.BAD_ARGS, "invalid download url")
            download_data = urlopen(url.decode(), timeout=10).read()
            file_size = len(download_data)

            if file_size > FILE_SIZE_LIMIT:
                raise ISAError(
                    ISAErrorCodes.INVALID_SOURCE_FILE,
                    f"file size exceeds limit of {FILE_SIZE_LIMIT} bytes",
                )
            else:
                self._files.insert({filename: download_data})
            return file_size

        # SYSCALL_RANDOM
        async def syscall_random():
            return random.getrandbits(32)

        match syscall_number:
            case 0:
                return await syscall_input(buf=arg1, length=arg2)
            case 1:
                return await syscall_output(buf=arg1, length=arg2)
            case 2:
                return await syscall_exit(exit_code=arg1)
            case 3:
                return await syscall_readfile(filename=arg1, buf=arg2, length=arg3)
            case 4:
                return await syscall_list_files()
            case 5:
                return await syscall_exec(filename=arg1)
            case 6:
                return await syscall_download(filename=arg1, url=arg2)
            case 7:
                return await syscall_random()

            case _:
                raise ISAError(ISAErrorCodes.BAD_INST, "unknown syscall")

    # execute a single step of the program
    async def step(self):
        try:
            if self.state != EngineState.RUNNING:
                raise ISAError(ISAErrorCodes.UNKNOWN, "program is not running")

            # change state to prevent race condition
            self.state = EngineState.STEPPING

            # parse and run the instruction
            pc = self._registers.get_program_counter()
            inst = self.parse_code_at(pc)

            self._registers.set_program_counter(pc + len(inst))

            await self.resolve_inst(inst)

            if self.state == EngineState.STEPPING:
                self.state = EngineState.RUNNING

        except Exception as ex:
            if isinstance(ex, ISAError):
                isa_err = ex
            else:
                isa_err = ISAError(ISAErrorCodes.UNKNOWN, str(ex))
            print(isa_err)
            await self.event_emitter.trigger(EventType.ERROR, "before", isa_err)
            raise isa_err from ex

    # set engine state to running
    def start(self):
        self.state = EngineState.RUNNING

    # set engine state to stop
    def stop(self):
        self.state = EngineState.STOPPED

    # run the program
    async def run(self):
        self.start()
        while True:
            try:
                # check if breakpoint is hit
                pc = self._registers.get_program_counter()
                if pc in self.breakpoints:

                    self.event_continue.clear()
                    await self.event_emitter.trigger(EventType.BREAKPOINT, "before", pc)
                    await self.event_continue.wait()
                    await self.event_emitter.trigger(EventType.BREAKPOINT, "after", pc)

                match self.state:
                    case EngineState.STOPPED:
                        break
                    case EngineState.STEPPING:
                        await sleep(0.5)
                    case EngineState.RUNNING:
                        await self.step()

            except:
                self.stop()
                break
