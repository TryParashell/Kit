from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import streamlib

PRINTABLE = set(range(0x20, 0x7F))


def render(blob: bytes, start: int, stop: int) -> None:
    for base in range(start, stop, 16):
        chunk = blob[base : min(base + 16, stop)]
        text = "".join(chr(byte) if byte in PRINTABLE else "." for byte in chunk)
        print(f"{base:6d}  {chunk.hex(' '):<47}  {text}")


def main() -> int:
    part = Path(sys.argv[1]).resolve()
    name = sys.argv[2]
    start = int(sys.argv[3])
    stop = int(sys.argv[4])
    blob = streamlib.load_donor(part).streams[name]
    print(f"{part.stem} {name} length={len(blob)}")
    render(blob, max(0, start), min(len(blob), stop))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
