"""Read a pickle file's steps WITHOUT running them, using only Python's own standard library.

    python -m pickletools sentiment-community.pkl

A pickle is a list of steps for the loader. `pickletools` prints them one per line. You do not need a scanner to find the
dangerous ones: look for the steps that bring in code and run it.

    GLOBAL / STACK_GLOBAL / INST     import something by name (a function, a class)
    REDUCE / OBJ / NEWOBJ / BUILD    call it

A model made of plain numbers needs none of these. A pickle that imports `posix.mkdir` or `os.system` and then REDUCEs
(calls) it is asking the loader to run code. The real scanners in Lab 9.3 automate this reading and have the same limits.
"""
import io
import pickletools

RUNS_CODE = ("GLOBAL", "STACK_GLOBAL", "INST", "REDUCE", "OBJ", "NEWOBJ", "NEWOBJ_EX", "BUILD")
MAX_LINES = 120


def disassemble(data: bytes) -> list[dict]:
    """The steps of a pickle, one per line, each marked if it imports or calls something."""
    out = io.StringIO()
    try:
        pickletools.dis(data, out)
    except Exception as exc:  # not a valid pickle
        return [{"text": f"This is not a readable pickle: {type(exc).__name__}: {exc}", "flag": False}]
    lines = []
    for raw in out.getvalue().splitlines()[:MAX_LINES]:
        parts = raw.split(":", 1)
        tokens = parts[1].split() if len(parts) == 2 else []
        opcode = tokens[1] if len(tokens) >= 2 else ""           # the line is: offset: <the byte> <OPCODE> <argument>
        lines.append({"text": raw, "flag": opcode in RUNS_CODE})
    return lines
