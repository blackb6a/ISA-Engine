UINT32_MAX = (1 << 32) - 1
INT32_MAX = (1 << 31) - 1


def uint32_to_bytes(u):
    """
    Convert a uint32 integer into a bytes object with little-endian order.

    Args:
        u: A uint32 integer.

    Returns:
        A bytes object with the value of `u` in little-endian order.
    """
    return u.to_bytes(4, "little")


def uint32_to_int32(u):
    """
    Convert a uint32 integer to a signed 32-bit integer by applying two's complement.

    Args:
        u: A uint32 integer to convert.

    Returns:
        The signed 32-bit integer representation of the input uint32 integer.
    """
    sign_mask = INT32_MAX + 1
    bit_mask = INT32_MAX
    return (u & bit_mask) - (u & sign_mask)


def bytes_to_uint32(b):
    """
    Convert a bytes object to a uint32 integer with little-endian order.

    Args:
        b: A bytes object of length 4 representing the uint32 integer.

    Returns:
        The uint32 integer representation of the input bytes object.
    """
    return int.from_bytes(b, byteorder="little")


def to_u32(i):
    """
    Convert a signed or unsigned integer to an unsigned 32-bit integer.

    This function will take any signed or unsigned integer and convert it to an
    unsigned 32-bit integer by applying modulo 2^32. The result is a uint32
    integer.

    Args:
        i: A signed or unsigned integer to convert.

    Returns:
        The uint32 integer representation of the input signed or unsigned integer.
    """
    return i & UINT32_MAX


def not32(u):
    """
    Perform a bitwise NOT operation on the input uint32 integer `u` by performing an XOR with UINT32_MAX.

    Args:
        u: A uint32 integer to apply the bitwise NOT operation.

    Returns:
        The result of applying the bitwise NOT operation to the input uint32 integer.
    """
    return u ^ UINT32_MAX


def xor32(u1, u2):
    """
    Perform a bitwise XOR operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: A uint32 integer to apply the bitwise XOR operation.
        u2: A uint32 integer to apply the bitwise XOR operation.

    Returns:
        The result of applying the bitwise XOR operation to the two input uint32 integers.
    """
    return u1 ^ u2


def and32(u1, u2):
    """
    Perform a bitwise AND operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: A uint32 integer to apply the bitwise AND operation.
        u2: A uint32 integer to apply the bitwise AND operation.

    Returns:
        The result of applying the bitwise AND operation to the two input uint32 integers.
    """
    return u1 & u2


def or32(u1, u2):
    """
    Perform a bitwise OR operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: A uint32 integer to apply the bitwise OR operation.
        u2: A uint32 integer to apply the bitwise OR operation.

    Returns:
        The result of applying the bitwise OR operation to the two input uint32 integers.
    """
    return u1 | u2


def sal32(u1, u2):
    """
    Perform a bitwise shift left operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: A uint32 integer to apply the bitwise shift left operation.
        u2: A uint32 integer to apply the bitwise shift left operation.

    Returns:
        The result of applying the bitwise shift left operation to the two input uint32 integers.
    """
    return (u1 << u2) & UINT32_MAX


def sar32(u1, u2):
    """
    Perform an arithmetic shift right operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: A uint32 integer to apply the arithmetic shift right operation.
        u2: A uint32 integer to apply the arithmetic shift right operation.

    Returns:
        The result of applying the arithmetic shift right operation to the two input uint32 integers.
    """
    return (uint32_to_int32(u1) >> u2) & UINT32_MAX


def shl32(u1, u2):
    """
    Perform a bitwise shift left operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: A uint32 integer to apply the bitwise shift left operation.
        u2: A uint32 integer to apply the bitwise shift left operation.

    Returns:
        The result of applying the bitwise shift left operation to the two input uint32 integers.
    """
    return (u1 << u2) & UINT32_MAX


def shr32(u1, u2):
    """
    Perform a bitwise shift right operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: A uint32 integer to apply the bitwise shift right operation.
        u2: A uint32 integer to apply the bitwise shift right operation.

    Returns:
        The result of applying the bitwise shift right operation to the two input uint32 integers.
    """
    return u1 >> u2


def rol32(u1, u2):
    """
    Perform a bitwise left rotation on the uint32 integer `u1` by `u2` positions.

    Args:
        u1: A uint32 integer to rotate.
        u2: The number of bit positions to rotate `u1` to the left.

    Returns:
        The result of rotating `u1` to the left by `u2` positions.
    """
    if u2 >= 32:
        return rol32(u1, u2 % 32)
    if u2 == 0:
        return u1
    return shl32(u1, u2) + shr32(u1, (32 - u2))


def ror32(u1, u2):
    """
    Perform a bitwise right rotation on the uint32 integer `u1` by `u2` positions.

    Args:
        u1: A uint32 integer to rotate.
        u2: The number of bit positions to rotate `u1` to the right.

    Returns:
        The result of rotating `u1` to the right by `u2` positions.
    """
    if u2 >= 32:
        return ror32(u1, u2 % 32)
    if u2 == 0:
        return u1
    return shr32(u1, u2) + shl32(u1, (32 - u2))


def add32(u1, u2):
    """
    Perform a 32-bit unsigned integer addition operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: uint32 - The first uint32 integer to add.
        u2: uint32 - The second uint32 integer to add.

    Returns:
        The result of adding the two input uint32 integers, keeping only the lower 32 bits.
    """
    return (u1 + u2) & UINT32_MAX


def sub32(u1, u2):
    """
    Perform a 32-bit unsigned integer subtraction operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: uint32 - The minuend.
        u2: uint32 - The subtrahend.

    Returns:
        The result of subtracting `u2` from `u1`, keeping only the lower 32 bits.
    """
    return (u1 - u2) & UINT32_MAX


def mul32(u1, u2):
    """
    Perform a 32-bit unsigned integer multiplication operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: uint32 - The multiplicand.
        u2: uint32 - The multiplier.

    Returns:
        A tuple containing the lower 32 bits of the multiplication result and the remainder (i.e. the higher 32 bits of the result).
    """
    return ((u1 * u2) & UINT32_MAX, (u1 * u2) // (UINT32_MAX + 1))


def div32(u1, u2):
    """
    Perform a 32-bit unsigned integer division operation on the two input uint32 integers `u1` and `u2`.

    Args:
        u1: uint32 - The dividend.
        u2: uint32 - The divisor.

    Returns:
        A tuple containing the quotient and remainder of the division operation, both of which are uint32 integers.
    """
    return ((u1 // u2) & UINT32_MAX, (u1 % u2))


def eq32(u1, u2):
    """
    Compare two uint32 integers and return True if they are equal.

    Args:
        u1: A uint32 integer to compare.
        u2: A uint32 integer to compare.

    Returns:
        bool: True if the two uint32 integers are equal, False otherwise.
    """
    return u1 == u2


def neq32(u1, u2):
    """
    Compare two uint32 integers and return True if they are not equal.

    Args:
        u1: A uint32 integer to compare.
        u2: A uint32 integer to compare.

    Returns:
        bool: True if the two uint32 integers are not equal, False otherwise.
    """
    return u1 != u2


def gt32(u1, u2):
    """
    Compare two uint32 integers and return True if the first is greater than the second.

    Args:
        u1: A uint32 integer to compare.
        u2: A uint32 integer to compare.

    Returns:
        bool: True if the first uint32 integer is greater than the second uint32 integer, False otherwise.
    """
    return uint32_to_int32(u1) > uint32_to_int32(u2)


def gtu32(u1, u2):
    """
    Compare two uint32 integers and return True if the first is greater than the second.

    Args:
        u1: A uint32 integer to compare.
        u2: A uint32 integer to compare.

    Returns:
        bool: True if the first uint32 integer is greater than the second uint32 integer, False otherwise.
    """
    return u1 > u2


def gte32(u1, u2):
    """
    Compare two uint32 integers and return True if the first is greater than or equal to the second.

    Args:
        u1: A uint32 integer to compare.
        u2: A uint32 integer to compare.

    Returns:
        bool: True if the first uint32 integer is greater than or equal to the second uint32 integer, False otherwise.
    """
    return uint32_to_int32(u1) >= uint32_to_int32(u2)


def gteu32(u1, u2):
    """
    Compare two uint32 integers and return True if the first is greater than or equal to the second.

    Parameters:
        u1: uint32 - The first uint32 integer to compare.
        u2: uint32 - The second uint32 integer to compare.
    """
    return u1 >= u2


def lt32(u1, u2):
    """
    Compare two uint32 integers and return True if the first is less than the second.

    Parameters:
        u1: uint32 - The first uint32 integer to compare.
        u2: uint32 - The second uint32 integer to compare.

    Returns:
        bool: True if the first uint32 integer is less than the second uint32 integer, False otherwise.
    """
    return uint32_to_int32(u1) < uint32_to_int32(u2)


def ltu32(u1, u2):
    """
    Compare two uint32 integers and return True if the first is less than the second.

    Parameters:
        u1: uint32 - The first uint32 integer to compare.
        u2: uint32 - The second uint32 integer to compare.

    Returns:
        bool: True if the first uint32 integer is less than the second uint32 integer, False otherwise.
    """
    return u1 < u2


def lte32(u1, u2):
    """
    Compare two uint32 integers and return True if the first is less than or equal to the second.

    Parameters:
        u1: uint32 - The first uint32 integer to compare.
        u2: uint32 - The second uint32 integer to compare.
    """
    return uint32_to_int32(u1) <= uint32_to_int32(u2)


def lteu32(u1, u2):
    """
    Compare two uint32 integers and return True if the first is less than or equal to the second.

    Parameters:
        u1: uint32 - The first uint32 integer to compare.
        u2: uint32 - The second uint32 integer to compare.

    Returns:
        bool: True if the first uint32 integer is less than or equal to the second uint32 integer, False otherwise.
    """

    return u1 <= u2


def range_collide(s1, e1, s2, e2):
    """
    Check if two ranges defined by their start and end points collide.

    Parameters:
        s1: int - The start point of the first range.
        e1: int - The end point of the first range.
        s2: int - The start point of the second range.
        e2: int - The end point of the second range.

    Returns:
        bool: True if the ranges collide, False otherwise.
    """
    return (s1 >= s2 and s1 < e2) or (s2 >= s1 and s2 < e1)
