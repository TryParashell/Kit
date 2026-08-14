from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import streamlib


def main() -> int:
    name = sys.argv[3] if len(sys.argv) > 3 else streamlib.RESOLVED
    left = streamlib.load_donor(Path(sys.argv[1]).resolve()).streams[name]
    right = streamlib.load_donor(Path(sys.argv[2]).resolve()).streams[name]
    print(f"left={len(left)} right={len(right)}")
    if len(left) != len(right):
        print("lengths differ; byte comparison covers the common prefix")
    runs: list[tuple[int, int]] = []
    start = -1
    for offset in range(min(len(left), len(right))):
        if left[offset] != right[offset]:
            if start < 0:
                start = offset
        elif start >= 0:
            runs.append((start, offset))
            start = -1
    if start >= 0:
        runs.append((start, min(len(left), len(right))))
    print(f"differing runs={len(runs)} differing bytes={sum(b - a for a, b in runs)}")
    for begin, end in runs[:40]:
        print(
            f"  [{begin}, {end}) left={left[begin:end].hex(' ')} "
            f"right={right[begin:end].hex(' ')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
