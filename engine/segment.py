from engine.error import ISAError, ISAErrorCodes


class SegmentPermission:
    READ = 0o4
    WRITE = 0o2
    EXEC = 0o1

    def __init__(self, permission: int):
        if permission // 8 != 0:
            raise ISAError(ISAErrorCodes.BAD_ARGS, "Invalid permission")
        self.permission = permission

    def readable(self):
        return self.permission & self.READ == self.READ

    def writable(self):
        return self.permission & self.WRITE == self.WRITE

    def executable(self):
        return self.permission & self.EXEC == self.EXEC


class Segment:
    def __init__(
        self,
        name: str,
        start: int,
        size: int,
        init_data: bytes,
        permission_flag: int,
    ):
        self.name: str = name  # name of the segment
        self.start: int = start  # starting address of the segment
        self.size: int = size  # size of the segment
        self.end: int = start + size  # ending address of the segment
        self.mem: memoryview = memoryview(
            bytearray(self.size)
        )  # memory view of the segment
        self.permission: SegmentPermission = SegmentPermission(
            permission_flag
        )  # permission of the segment

        # initialize the segment with the provided initial data
        self.mem[: len(init_data)] = init_data

    def __getitem__(self, key):
        if not self.readable:
            raise ISAError(ISAErrorCodes.SEG_FAULT, "segment is not readable")

        if isinstance(key, int):
            return self.mem.__getitem__(key - self.start)

        if isinstance(key, slice) and isinstance(key.start, int):
            start = key.start
            stop = key.stop

            # adjust the start address relative to the segment's starting address
            if start is not None:
                start -= self.start
            if stop is not None:
                stop -= self.start

            return self.mem.__getitem__(slice(start, stop, key.step))

        return self.mem.__getitem__(key)

    def __setitem__(self, key, value):
        if not self.writable:
            raise ISAError(ISAErrorCodes.SEG_FAULT, "segment is not writable")

        if isinstance(key, int):
            return self.mem.__setitem__(key - self.start, value)

        if isinstance(key, slice) and isinstance(key.start, int):
            start = key.start
            stop = key.stop

            # adjust the start address relative to the segment's starting address
            if start is not None:
                start -= self.start
            if stop is not None:
                stop -= self.start

            return self.mem.__setitem__(slice(start, stop, key.step), value)

        return self.mem.__setitem__(key, value)

    def __str__(self):
        return f"Segment(name={self.name}, start={self.start:08x}, end={self.end:08x}, size={self.size}, permission={self.permission})"

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self.size

    def find(self, sub, start=None, end=None):
        # adjust the start address relative to the segment's starting address
        if start is not None:
            start -= self.start
        if end is not None:
            end -= self.start

        # find the specified subsequence within the segment's memory view and return its absolute address
        return self.mem.obj.find(sub, start, end) + self.start

    @property
    def readable(self):
        return self.permission.readable()

    @property
    def writable(self):
        return self.permission.writable()

    @property
    def executable(self):
        return self.permission.executable()
