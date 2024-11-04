from engine.segment import Segment, SegmentPermission
from engine.error import ISAError, ISAErrorCodes
from engine.util import bytes_to_uint32, to_u32, range_collide, uint32_to_bytes


class MemoryManager:
    def __init__(self):
        self.segments: dict[str, Segment] = {}  # dictionary to store memory segments

    def __getitem__(self, key):
        if isinstance(key, int):
            segment = self.find_segment_by_addr(key)
            return segment[key]

        if isinstance(key, slice) and isinstance(key.start, int):
            segment = self.find_segment_by_addr(key.start)
            return segment[key]

        raise TypeError("MemoryManager indices must be integers or slices")

    def __setitem__(self, key, value):
        if isinstance(key, int):
            segment = self.find_segment_by_addr(key)
            segment[key] = value
            return

        if isinstance(key, slice) and isinstance(key.start, int):
            segment = self.find_segment_by_addr(key.start)
            segment[key] = value
            return

        raise TypeError("MemoryManager indices must be integers or slices")

    # return the segment which owning the address
    def find_segment_by_addr(self, addr: int) -> Segment:
        for segment in self.segments.values():
            # check if the address falls within the segment's range
            if addr >= segment.start and addr < segment.end:
                return segment

        raise ISAError(
            ISAErrorCodes.SEG_FAULT, f"cannot access memory address {addr:08x}"
        )

    # allocate a segment
    def map(
        self,
        name: bytes,
        start: int,
        size: int,
        permission_flag: int = SegmentPermission.READ
        | SegmentPermission.WRITE
        | SegmentPermission.EXEC,
        init_data: bytes = b"",
    ):
        for segment in self.segments.values():
            # check for collision with existing segments
            if range_collide(start, start + size, segment.start, segment.end):
                raise ISAError(ISAErrorCodes.ALLOC_FAIL, "allocate segment failed")

        # create a new segment and add to the dictionary of segments
        segment = Segment(name, start, size, init_data, permission_flag)
        self.segments[name] = segment

    # deallocate a segment
    def munmap(self, addr_or_name: int | bytes):
        if isinstance(addr_or_name, int):
            segment_name = self.find_segment_by_addr(addr_or_name).name
        else:
            segment_name = addr_or_name
        self.segments.pop(segment_name)

    # deallocate a segment

    # set a 32-bit value in memory by converting it to bytes
    def set32(self, addr: int, value: int):
        addr = to_u32(addr)
        self[addr : addr + 4] = uint32_to_bytes(value)

    # retrieve a 32-bit value from memory by converting bytes to an integer
    def get32(self, addr: int) -> int:
        addr = to_u32(addr)
        return bytes_to_uint32(self[addr : addr + 4])

    # retrieve the null-terminated string that started at addr
    def get_cstring(self, addr: int) -> bytes:
        segment = self.find_segment_by_addr(addr)

        csting_end = segment.find(b"\0", addr)
        # if null-terminator is not found, set the end to the end of the segment
        if csting_end == -1:
            csting_end = segment.start + segment.size

        return segment[addr:csting_end].tobytes()
