from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import blocks as blockslib


def main() -> int:
    stream = sys.argv[1]
    wanted = {int(value) for value in sys.argv[2].split(",")}
    rows = sys.argv[3:]
    for position in range(0, len(rows), 3):
        label = rows[position]
        part = Path(rows[position + 1]).resolve()
        log = Path(rows[position + 2]).resolve()
        model = blockslib.load_model(part, log, stream)
        print(f"== {label} nodes={len(model.nodes)}")
        for index in sorted(wanted):
            if index >= len(model.nodes):
                continue
            node = model.nodes[index]
            print(
                f"  [{index}] {node.kind} {node.class_name or '-'} "
                f"len={len(node.body)} literal={node.literal:#06x}"
            )
            print("    " + node.body.hex())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
