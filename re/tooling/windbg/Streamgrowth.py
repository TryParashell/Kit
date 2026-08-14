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
    parts = [Path(item).resolve() for item in sys.argv[1:]]
    if not parts:
        raise SystemExit("usage: Streamgrowth.py <part> <part> [...]")
    table: dict[str, list[int]] = {}
    for part in parts:
        donor = streamlib.load_donor(part)
        for name, payload in donor.streams.items():
            table.setdefault(name, []).append(len(payload))
    width = max(len(name) for name in table)
    print("stream sizes across " + ", ".join(part.stem for part in parts))
    for name in sorted(table):
        sizes = table[name]
        if len(sizes) != len(parts):
            print(f"{name:<{width}}  {sizes} (missing from some parts)")
            continue
        trend = "grows" if sizes == sorted(sizes) and sizes[0] != sizes[-1] else "flat"
        print(f"{name:<{width}}  {sizes} {trend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
