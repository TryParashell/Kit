from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parents[2] / ".rescratch"
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import model as modellib
import segment as segmentlib

import streamlib

from convert.adapters.solidworks import resolved as resolvedlib

OUT = SCRATCH / "trace" / "out"

COMP_CLASS = "moCompFeature_c"
HISTORY_ITEM_CLASS = "moHistoryFeatItemData_c"


class RenumberError(RuntimeError):
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Block:
    start: int
    stop: int

    @property
    def size(self) -> int:
        return self.stop - self.start

    def __contains__(self, position: int) -> bool:
        return self.start <= position < self.stop


def history_count_node(model: modellib.Model) -> int:
    for position, node in enumerate(model.nodes):
        if node.class_name == HISTORY_ITEM_CLASS:
            if position == 0:
                raise RenumberError(
                    f"{HISTORY_ITEM_CLASS} is the first object; the array count "
                    "cannot precede it"
                )
            return position - 1
    raise RenumberError(f"{HISTORY_ITEM_CLASS} never appears in the stream")


def read_history_count(model: modellib.Model) -> int:
    node = model.nodes[history_count_node(model)]
    if len(node.body) < 2:
        raise RenumberError("the object preceding the history array is too short")
    return int.from_bytes(node.body[-2:], "little")


def set_history_count(model: modellib.Model, value: int) -> None:
    if not 0 < value < 0x10000:
        raise RenumberError(f"history item count {value} does not fit in a u16")
    position = history_count_node(model)
    node = model.nodes[position]
    node.body = node.body[:-2] + value.to_bytes(2, "little")


def node_range(model: modellib.Model, start_byte: int, stop_byte: int) -> Block:
    offsets = modellib.node_offsets(model)
    try:
        start = offsets.index(start_byte)
        stop = offsets.index(stop_byte)
    except ValueError as error:
        raise RenumberError(
            f"byte span [{start_byte}, {stop_byte}) does not align with object "
            f"boundaries"
        ) from error
    return Block(start, stop)


def comp_unit(model: modellib.Model, blob: bytes) -> Block:
    entries = streamlib.comp_feature_entries(blob)
    if len(entries) < 4 or len(entries) % 2:
        raise RenumberError(
            f"{COMP_CLASS} holds {len(entries)} entries; an even count of at "
            "least four is required to duplicate one feature"
        )
    return node_range(model, entries[-2][0], entries[-1][1])


def feature_unit(blob: bytes, segments: tuple[segmentlib.Segment, ...]) -> Block:
    sketches = [
        item for item in resolvedlib.tree_nodes(blob) if item.name.startswith("Sketch")
    ]
    if len(sketches) < 2:
        raise RenumberError(
            f"the donor exposes {len(sketches)} sketch nodes; at least two are "
            "needed so the duplicated group is not the first feature"
        )
    anchor = sketches[-1].text_end
    position = -1
    for item in segments:
        if item.offset <= anchor < item.end:
            position = item.index
            break
    if position < 0:
        raise RenumberError(f"sketch name record at {anchor} is outside every object")
    while position > 0 and segments[position].depth != 0:
        position -= 1
    if segments[position].depth != 0:
        raise RenumberError("no top-level object precedes the last sketch")
    return Block(position, len(segments))


def duplicate(
    model: modellib.Model, blocks: tuple[Block, ...], copies: int
) -> tuple[modellib.Model, tuple[tuple[int, int], ...]]:
    if copies < 1:
        raise RenumberError("copies must be at least 1")
    ordered = sorted(blocks, key=lambda item: item.start)
    for block in ordered:
        if block.start < 0 or block.stop > len(model.nodes) or block.size <= 0:
            raise RenumberError(f"block {block} is out of range")
    for left, right in zip(ordered, ordered[1:]):
        if left.stop > right.start:
            raise RenumberError("blocks overlap")

    plan: list[tuple[int, int]] = []
    cursor = 0
    for block in ordered:
        while cursor < block.stop:
            plan.append((cursor, 0))
            cursor += 1
        for copy_id in range(1, copies + 1):
            for source in range(block.start, block.stop):
                plan.append((source, copy_id))
    while cursor < len(model.nodes):
        plan.append((cursor, 0))
        cursor += 1

    lookup = {key: position for position, key in enumerate(plan)}

    def duplicated(source: int) -> bool:
        return any(source in block for block in ordered)

    result = modellib.Model(header=model.header, base=model.base, nodes=[])
    for source, copy_id in plan:
        original = model.nodes[source]
        kind = original.kind
        target = original.target
        literal = original.literal
        if copy_id and kind == "definition":
            kind = "classref"
            target = lookup[(source, 0)]
            literal = modellib.CLASS_TAG_BIT
        if target >= 0:
            if copy_id and duplicated(target):
                target = lookup[(target, copy_id)]
            else:
                target = lookup[(target, 0)]
        result.nodes.append(
            modellib.Node(
                kind=kind,
                body=original.body,
                schema=original.schema,
                class_name=original.class_name,
                target=target,
                literal=literal,
                origin=original.origin,
            )
        )
    result.assign()
    return result, tuple(plan)


def remove(
    model: modellib.Model, blocks: tuple[Block, ...]
) -> tuple[modellib.Model, tuple[int, ...]]:
    ordered = sorted(blocks, key=lambda item: item.start)
    dropped: set[int] = set()
    for block in ordered:
        for position in range(block.start, block.stop):
            dropped.add(position)
    for position in sorted(dropped):
        node = model.nodes[position]
        if node.kind == "definition":
            raise RenumberError(
                f"node {position} defines {node.class_name}; deleting a class "
                "definition needs the definition moved to its first surviving use"
            )
    survivors = [
        position for position in range(len(model.nodes)) if position not in dropped
    ]
    lookup = {source: index for index, source in enumerate(survivors)}
    result = modellib.Model(header=model.header, base=model.base, nodes=[])
    for source in survivors:
        original = model.nodes[source]
        target = original.target
        if target >= 0:
            if target not in lookup:
                raise RenumberError(
                    f"node {source} references deleted node {target}; "
                    "the deletion set is not closed"
                )
            target = lookup[target]
        result.nodes.append(
            modellib.Node(
                kind=original.kind,
                body=original.body,
                schema=original.schema,
                class_name=original.class_name,
                target=target,
                literal=original.literal,
                origin=original.origin,
            )
        )
    result.assign()
    return result, tuple(survivors)


def renumbering_table(
    before: modellib.Model,
    after: modellib.Model,
    plan: tuple[tuple[int, int], ...],
) -> list[dict[str, int | str]]:
    before.assign()
    after.assign()
    rows: list[dict[str, int | str]] = []
    for position, (source, copy_id) in enumerate(plan):
        old_node = before.nodes[source]
        new_node = after.nodes[position]
        rows.append(
            {
                "source_node": source,
                "copy": copy_id,
                "target_node": position,
                "kind": new_node.kind,
                "class_name": new_node.class_name,
                "old_class_index": old_node.class_index,
                "new_class_index": new_node.class_index,
                "old_map_index": old_node.object_index,
                "new_map_index": new_node.object_index,
                "shift": new_node.object_index - old_node.object_index,
            }
        )
    return rows


def grow(
    part: Path, log: Path, copies: int
) -> tuple[bytes, bytes, modellib.Model, dict[str, object]]:
    blob, base_model, segments = modellib.load(part, log)
    comp = comp_unit(base_model, blob)
    feature = feature_unit(blob, segments)
    print(f"comp unit nodes=[{comp.start},{comp.stop}) size={comp.size}")
    print(f"feature unit nodes=[{feature.start},{feature.stop}) size={feature.size}")
    grown, plan = duplicate(base_model, (comp, feature), copies)
    before_count = read_history_count(base_model)
    entries_before = len(streamlib.comp_feature_entries(blob))
    if before_count != entries_before:
        raise RenumberError(
            f"history array count {before_count} disagrees with the "
            f"{entries_before} moCompFeature_c entries in {part.name}"
        )
    set_history_count(grown, before_count + 2 * copies)
    payload = grown.emit()
    table = renumbering_table(base_model, grown, plan)
    facts = {
        "renumbering_table": table,
        "part": str(part),
        "copies": copies,
        "comp_block": [comp.start, comp.stop],
        "feature_block": [feature.start, feature.stop],
        "nodes_before": len(base_model.nodes),
        "nodes_after": len(grown.nodes),
        "bytes_before": len(blob),
        "bytes_after": len(payload),
        "map_indices_before": len(base_model.nodes)
        and base_model.nodes[-1].object_index,
        "map_indices_after": grown.nodes[-1].object_index,
        "comp_entries_before": entries_before,
        "comp_entries_after": len(streamlib.comp_feature_entries(payload)),
        "history_count_before": before_count,
        "history_count_after": read_history_count(grown),
        "layouts_before": len(resolvedlib.locate_features(blob)),
        "layouts_after": len(resolvedlib.locate_features(payload)),
    }
    return blob, payload, grown, facts


def main() -> int:
    part = Path(sys.argv[1]).resolve()
    log = Path(sys.argv[2]).resolve()
    copies = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    blob, payload, grown, facts = grow(part, log, copies)
    OUT.mkdir(parents=True, exist_ok=True)
    table = facts.pop("renumbering_table")
    (OUT / f"grown_{part.stem}_{copies}.bin").write_bytes(payload)
    (OUT / f"renumbering_{part.stem}_{copies}.json").write_text(
        json.dumps(table, indent=2), encoding="utf-8"
    )
    shifts = sorted({int(row["shift"]) for row in table})
    facts["distinct_map_index_shifts"] = shifts
    (OUT / f"grown_{part.stem}_{copies}.json").write_text(
        json.dumps(facts, indent=2), encoding="utf-8"
    )
    nodes = resolvedlib.tree_nodes(payload)
    sketches = [item.name for item in nodes if item.name.startswith("Sketch")]
    features = [
        item.name for item in nodes if resolvedlib.feature_kind(item.flags) is not None
    ]
    print(json.dumps(facts, indent=2))
    print(f"sketch nodes={sketches}")
    print(f"feature nodes={features}")
    print(f"comp ids={[entry[2] for entry in streamlib.comp_feature_entries(payload)]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
