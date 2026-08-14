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

import headercount
import renumber

import serialize
import streamlib

from convert.adapters.solidworks import resolved as resolvedlib

OUT = SCRATCH / "trace" / "out"
PARTS = SCRATCH / "trace" / "parts"

BOSS_RECT_PLANE = ("boss", "rectangle", "plane", True)

DONOR = (SCRATCH / "corpus2" / "parts" / "PADPLANE_rev_d5.SLDPRT").resolve()
LOG = (SCRATCH / "trace" / "out" / "cdb_trace_padplane.log").resolve()


class AuthorError(RuntimeError):
    __slots__ = ()


def boss(
    width: float, height: float, depth: float, x: float, y: float, back: bool
) -> serialize.Extrude:
    return serialize.Extrude(
        profile=serialize.Rectangle(width, height, x, y),
        depth_mm=depth,
        operation="boss",
        plane="front",
        end_condition="blind",
        reversed=back,
        support="plane",
    )


BASE = boss(100.0, 30.0, 12.0, 0.0, 0.0, False)
STUDS = (
    boss(10.0, 10.0, 8.0, -30.0, 0.0, True),
    boss(10.0, 10.0, 6.0, -10.0, 0.0, True),
    boss(10.0, 10.0, 7.0, 10.0, 0.0, True),
    boss(10.0, 10.0, 5.0, 30.0, 0.0, True),
)


def rename_tree(blob: bytes, count: int) -> bytes:
    if count > 9:
        raise AuthorError(f"{count} features exceeds the single-digit name convention")
    output = bytearray(blob)
    nodes = resolvedlib.tree_nodes(bytes(output))
    sketches = [item for item in nodes if item.name.startswith("Sketch")]
    features = [
        item for item in nodes if resolvedlib.feature_kind(item.flags) is not None
    ]
    if len(sketches) != count or len(features) != count:
        raise AuthorError(
            f"grown stream exposes {len(sketches)} sketches and "
            f"{len(features)} features, {count} of each expected"
        )
    for ordinal in range(count):
        wanted = ord(str(ordinal + 1))
        for item in (sketches[ordinal], features[ordinal]):
            struct.pack_into("<H", output, item.text_end - 2, wanted)
    return bytes(output)


def skeleton_for(count: int) -> tuple[serialize.Skeleton, dict[str, object]]:
    copies = count - 2
    if copies < 1:
        raise AuthorError(f"{count} features needs no growth from a 2-feature donor")
    _, payload, _, facts = renumber.grow(DONOR, LOG, copies)
    payload = rename_tree(payload, count)
    donor = streamlib.load_donor(DONOR)
    shape = tuple(BOSS_RECT_PLANE for _ in range(count))
    skeleton = serialize.Skeleton(
        shape=shape,
        source=DONOR,
        resolved=payload,
        keywords=donor.streams[streamlib.KEYWORDS],
        features_xml=donor.streams[streamlib.FEATURES],
        donor=donor,
        grown=True,
        label=f"{DONOR.stem}+{copies}",
    )
    return skeleton, facts


def specification(count: int) -> serialize.Part:
    return serialize.Part(
        features=(BASE,) + STUDS[: count - 1],
        name=f"KitTrace{count}",
        document_name=f"Trace{count}",
    )


def build(count: int, group: str) -> dict[str, object]:
    skeleton, facts = skeleton_for(count)
    spec = specification(count)
    target = PARTS / f"T{count}{group}_{count}_boss.SLDPRT"
    emission = serialize.emit(spec, (skeleton,))
    replacements = {
        streamlib.RESOLVED: emission.resolved,
        streamlib.KEYWORDS: emission.keywords,
        streamlib.FEATURES: emission.features_xml,
    }
    replacements.update(headercount.patched_streams(skeleton.donor, count, group))
    container = streamlib.rebuild(skeleton.donor, replacements)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(container)
    record = {
        "label": target.stem,
        "path": str(target),
        "features": count,
        "skeleton": emission.skeleton,
        "resolved_length": len(emission.resolved),
        "container_length": len(container),
        "expected_volume_mm3": serialize.solid_volume_mm3(spec),
        "history_count_after": facts["history_count_after"],
        "comp_entries_after": facts["comp_entries_after"],
        "map_indices_after": facts["map_indices_after"],
        "count_group": group,
        "patched_streams": sorted(
            headercount.patched_streams(skeleton.donor, count, group)
        ),
        "writes": emission.writes,
    }
    print(
        f"{record['label']:20s} features={count} resolved={len(emission.resolved):6d} "
        f"container={len(container):6d} group={group} "
        f"expected={record['expected_volume_mm3']}"
    )
    return record


def main() -> int:
    PARTS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    group = sys.argv[1]
    counts = [int(item) for item in sys.argv[2:]] or [4]
    records = [build(count, group) for count in counts]
    (OUT / "Author.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    for record in records:
        print(f"{record['label']}: {record['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
