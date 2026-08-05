import pathlib
import re
import sys

OUT = pathlib.Path(__file__).resolve().parents[3] / ".rescratch/ghidra/out"


def blocks(path):
    text = path.read_text(errors="replace")
    for part in text.split("\n=== FUNCTION ")[1:]:
        head, _, body = part.partition("\n")
        yield head.strip(), body


def main():
    path = OUT / (sys.argv[1] if len(sys.argv) > 1 else "sldmodu_accessors.c")
    keys = sys.argv[2:]
    for name, body in blocks(path):
        if keys and not any(k in name for k in keys):
            continue
        offs = []
        for match in re.finditer(r"(?:this|param_1)\s*\+\s*(0x[0-9a-f]+|\d+)", body):
            value = int(match.group(1), 0)
            if value not in offs:
                offs.append(value)
        types = sorted(
            set(
                re.findall(
                    r"\*\((u?int|double|float|short|ushort|char|byte|longlong|undefined\d?)\s?\*\)",
                    body,
                )
            )
        )
        lines = len(body.splitlines())
        print(
            f"{name:56s} lines={lines:4d} offs={[hex(o) for o in offs[:8]]} types={types}"
        )


if __name__ == "__main__":
    main()
