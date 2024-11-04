import argparse
from asyncio import run

from engine.error import ISAError, ISAErrorCodes
from engine.engine import Engine


async def main():
    """
    Main function for ISA parser.

    This function parses the command line arguments,
    then execute the ISA program either in run mode or debug mode.

    In run mode, the program is executed until it stops.
    Debug mode is not implemented.
    """
    cmd = argparse.ArgumentParser(description="ISA parser")
    cmd.add_argument("-s", "--source", help="source file", required=True, type=str)

    args = cmd.parse_args()

    if not args.source:
        cmd.error("missing source file")

    try:
        program = open(args.source, "rb")
        execution_engine = Engine(program.read(), vfiles={b"flag.txt": b"flag{1234}\n"})
        program.close()

        await execution_engine.run()

    except OSError as ex:
        raise ISAError(
            ISAErrorCodes.BAD_CONFIG, f"Could not open/read file: {args.source}"
        ) from ex


if __name__ == "__main__":
    run(main())
