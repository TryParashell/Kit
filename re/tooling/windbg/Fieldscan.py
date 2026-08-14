from __future__ import annotations

import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[2] / ".rescratch"
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import streamlib

OUT = SCRATCH / "trace" / "out"

FORMULAS = {
    "n": lambda n: n,
    "2n": lambda n: 2 * n,
    "24+2n": lambda n: 24 + 2 * n,
    "25+2n": lambda n: 25 + 2 * n,
    "18+2n": lambda n: 18 + 2 * n,
    "n-1": lambda n: n - 1,
    "n+1": lambda n: n + 1,
    "2n-1": lambda n: 2 * n - 1,
    "2n+1": lambda n: 2 * n + 1,
    "2n+2": lambda n: 2 * n + 2,
    "3n": lambda n: 3 * n,
    "4n": lambda n: 4 * n,
    "19+2n": lambda n: 19 + 2 * n,
    "23+2n": lambda n: 23 + 2 * n,
    "26+2n": lambda n: 26 + 2 * n,
    "40+2n": lambda n: 40 + 2 * n,
}


def matches(blob: bytes, value: int) -> set[tuple[int, int]]:
    found: set[tuple[int, int]] = set()
    limit = len(blob)
    for offset in range(limit - 1):
        if struct.unpack_from("<H", blob, offset)[0] == value:
            found.add((offset, 2))
        if offset + 4 <= limit and struct.unpack_from("<I", blob, offset)[0] == value:
            found.add((offset, 4))
    return found


def main() -> int:
    formula = sys.argv[1]
    if formula not in FORMULAS:
        raise SystemExit(f"formula must be one of {sorted(FORMULAS)}")
    rule = FORMULAS[formula]
    parts = [Path(item).resolve() for item in sys.argv[2:]]
    if len(parts) < 2:
        raise SystemExit("usage: Fieldscan.py <formula> <part> <part> [...]")
    per_stream: dict[str, list[set[tuple[int, int]]]] = {}
    counts: list[int] = []
    for part in parts:
        donor = streamlib.load_donor(part)
        features = len(streamlib.comp_feature_entries(donor.resolved)) // 2
        counts.append(features)
        value = rule(features)
        for name, payload in donor.streams.items():
            per_stream.setdefault(name, []).append(matches(payload, value))
    distinct = sorted(set(counts))
    print(f"parts={len(parts)} feature counts observed={distinct} formula={formula}")
    if len(distinct) < 2:
        raise SystemExit("the part set must contain at least two feature counts")
    report: dict[str, list[list[int]]] = {}
    for name in sorted(per_stream):
        sets = per_stream[name]
        if len(sets) != len(parts):
            continue
        shared = set.intersection(*sets)
        if not shared:
            continue
        report[name] = sorted([list(item) for item in shared])
        print(f"{name}: {sorted(shared)}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"fieldscan_{formula}.json").write_text(
        json.dumps(
            {
                "formula": formula,
                "parts": [str(part) for part in parts],
                "feature_counts": counts,
                "shared": report,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
