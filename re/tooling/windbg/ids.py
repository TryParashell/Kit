from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import streamlib

from convert.adapters.solidworks import resolved as resolvedlib


def main() -> int:
    for item in sys.argv[1:]:
        part = Path(item).resolve()
        donor = streamlib.load_donor(part)
        blob = donor.resolved
        nodes = resolvedlib.tree_nodes(blob)
        features = resolvedlib.locate_features(blob)
        entries = streamlib.comp_feature_entries(blob)
        print(f"{part.stem}")
        print(
            "  tree: " + ", ".join(f"{node.name}#{node.feature_id}" for node in nodes)
        )
        print(
            "  features: "
            + ", ".join(
                f"{item.kind}:{item.feature_id}/sketch={item.sketch_id}"
                for item in features
            )
        )
        print("  comp ids: " + ", ".join(str(entry[2]) for entry in entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
