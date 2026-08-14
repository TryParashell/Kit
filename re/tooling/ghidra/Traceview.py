from __future__ import annotations

from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "grammar"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import carchive
import streamlib
import tracedump


def main() -> None:
    part = Path(sys.argv[1]).resolve()
    report = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    blob = streamlib.load_donor(part).resolved
    items = report["items"]
    base = report["base_counter"]

    static = carchive.class_definitions(blob)
    static_offsets = [definition.tag_offset for definition in static]
    traced_defs = [item["offset"] for item in items if item["kind"] == "definition"]
    print(f"static definitions={len(static_offsets)} traced={len(traced_defs)}")
    print(f"definition offsets identical={static_offsets == traced_defs}")
    missing = sorted(set(static_offsets) - set(traced_defs))
    extra = sorted(set(traced_defs) - set(static_offsets))
    print(f"static-only={missing} traced-only={extra}")

    slot_of_class: dict[int, str] = {}
    counter = base
    for item in items:
        if item["kind"] == "definition":
            slot_of_class[counter] = item["name"]
            counter += 2
        elif item["kind"] in {"classref", "big"}:
            counter += 1
    print(f"final counter={counter} classes in stream={len(slot_of_class)}")

    external = sorted(
        {
            item["index"]
            for item in items
            if item["kind"] == "classref" and item["index"] < base
        }
    )
    internal = sorted(
        {
            item["index"]
            for item in items
            if item["kind"] == "classref" and item["index"] >= base
        }
    )
    print(f"classref indices below base (external)={external}")
    unresolved = [index for index in internal if index not in slot_of_class]
    print(f"classref indices at/above base={len(internal)} unresolved={unresolved}")

    obj_external = sorted(
        {
            item["index"]
            for item in items
            if item["kind"] == "objectref" and item["index"] < base
        }
    )
    print(f"objectref indices below base={obj_external}")

    gaps: list[tuple[int, int, int]] = []
    for position, item in enumerate(items):
        start = item["offset"] + item["header"]
        end = items[position + 1]["offset"] if position + 1 < len(items) else len(blob)
        gaps.append((item["offset"], start, end - start))
    zero = sum(1 for _, _, size in gaps if size == 0)
    print(f"gaps={len(gaps)} zero-length={zero} tail={gaps[-1]}")

    print()
    print(f"{'off':>6} {'ctr':>5} {'kind':>10} {'tok':>6} {'idx':>5} {'gap':>6} name")
    for item, (_, _, size) in zip(items, gaps):
        label = item["name"] or slot_of_class.get(item["index"], "")
        print(
            f"{item['offset']:>6} {item['counter']:>5} {item['kind']:>10} "
            f"{item['token']:#06x} {item['index']:>5} {size:>6} {label}"
        )


if __name__ == "__main__":
    main()
