from __future__ import annotations

from pathlib import Path
import json
import struct
import sys

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[2] / ".rescratch"
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import model as modellib

import streamlib

OUT = SCRATCH / "trace" / "out"

HISTORY_ITEM_CLASS = "moHistoryFeatItemData_c"


def item_count(blob: bytes, mode: str) -> int:
    entries = len(streamlib.comp_feature_entries(blob))
    if mode == "items":
        return entries
    if mode == "features":
        return entries // 2
    raise SystemExit(f"unknown mode {mode!r}")


def first_item_node(model: modellib.Model) -> int:
    for position, node in enumerate(model.nodes):
        if node.class_name == HISTORY_ITEM_CLASS:
            return position
    raise KeyError(HISTORY_ITEM_CLASS)


def candidates(
    model: modellib.Model, count: int, keying: str
) -> set[tuple[object, ...]]:
    anchor = first_item_node(model)
    total = len(model.nodes)
    found: set[tuple[object, ...]] = set()
    for position, node in enumerate(model.nodes):
        if keying == "anchor":
            key: object = position - anchor
        elif keying == "tail":
            key = position - total
        elif keying == "class":
            key = (node.class_name, node.kind)
        else:
            raise SystemExit(f"unknown keying {keying!r}")
        body = node.body
        for offset in range(len(body) - 1):
            if struct.unpack_from("<H", body, offset)[0] == count:
                found.add((key, offset, 2))
            if offset + 4 <= len(body):
                if struct.unpack_from("<I", body, offset)[0] == count:
                    found.add((key, offset, 4))
    return found


def main() -> int:
    mode = sys.argv[1]
    arguments = sys.argv[2:]
    if not arguments or len(arguments) % 3:
        raise SystemExit("usage: counts.py <items|features> <label> <part> <log> [...]")
    loaded: list[tuple[str, Path, bytes, modellib.Model, int]] = []
    for position in range(0, len(arguments), 3):
        label = arguments[position]
        part = Path(arguments[position + 1]).resolve()
        log = Path(arguments[position + 2]).resolve()
        blob, model, _ = modellib.load(part, log)
        count = item_count(blob, mode)
        loaded.append((label, part, blob, model, count))
        print(
            f"{label:12s} target={count:3d} nodes={len(model.nodes)} "
            f"anchor_node={first_item_node(model)}"
        )
    report: dict[str, list[list[object]]] = {}
    for keying in ("anchor", "tail", "class"):
        sets = [candidates(model, count, keying) for _, _, _, model, count in loaded]
        shared = set.intersection(*sets)
        report[keying] = sorted([list(item) for item in shared], key=repr)
        print(f"keying={keying:7s} shared fields={len(shared)}")
        for entry in sorted(shared, key=repr):
            print(f"  key={entry[0]!r} body_offset={entry[1]} width={entry[2]}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"counts_{mode}.json").write_text(
        json.dumps(
            {
                "mode": mode,
                "parts": [
                    {"label": label, "part": str(part), "target": count}
                    for label, part, _, _, count in loaded
                ],
                "shared": report,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
