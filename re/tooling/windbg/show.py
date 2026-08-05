from __future__ import annotations

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import model as modellib
import segment as segmentlib

import streamlib

from convert.adapters.solidworks import resolved as resolvedlib


def anchors(blob: bytes) -> dict[int, str]:
    marks: dict[int, str] = {}
    for node in resolvedlib.tree_nodes(blob):
        marks[node.text_end] = f"tree:{node.name}:flags@{node.text_end + 4}"
    for index, layout in enumerate(resolvedlib.locate_features(blob)):
        marks[layout.depth_offset] = f"depth[{index}]"
    for index, entry in enumerate(streamlib.comp_feature_entries(blob)):
        marks[entry[0]] = f"comp_entry[{index}] id={entry[2]}"
    return marks


def main() -> int:
    part = Path(sys.argv[1]).resolve()
    log = Path(sys.argv[2]).resolve()
    low = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    high = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    blob, model, segments = modellib.load(part, log)
    offsets = modellib.node_offsets(model)
    marks = anchors(blob)
    stop = high if high else len(segments)
    print(f"{part.name} stream={len(blob)} nodes={len(segments)} base={model.base}")
    print(
        f"{'node':>5} {'offset':>7} {'len':>5} {'tag':>6} {'kind':>10} "
        f"{'map':>5} {'d':>2} {'parent':>6} class"
    )
    for position in range(low, stop):
        item = segments[position]
        note = ""
        for offset, label in marks.items():
            if item.offset <= offset < item.end:
                note += f"  <{label}>"
        print(
            f"{position:>5} {item.offset:>7} {item.length:>5} {item.tag:>6x} "
            f"{item.kind:>10} {item.map_index:>5} {item.depth:>2} "
            f"{item.parent:>6} {item.class_name}{note}"
        )
    _ = offsets
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
