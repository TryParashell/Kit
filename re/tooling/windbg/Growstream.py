from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import model as modellib
import renumber as renumberlib


class GrowError(RuntimeError):
    __slots__ = ()


@dataclass(frozen=True, slots=True)
class CountField:
    node: int
    body_offset: int
    width: int

    def read(self, model: modellib.Model) -> int:
        body = model.nodes[self.node].body
        return int.from_bytes(
            body[self.body_offset : self.body_offset + self.width], "little"
        )

    def write(self, model: modellib.Model, value: int) -> None:
        node = model.nodes[self.node]
        body = bytearray(node.body)
        if self.body_offset + self.width > len(body):
            raise GrowError(f"count field runs past node {self.node}")
        body[self.body_offset : self.body_offset + self.width] = value.to_bytes(
            self.width, "little"
        )
        node.body = bytes(body)


def locate(model: modellib.Model, absolute: int, width: int) -> CountField:
    offsets = modellib.node_offsets(model)
    for position, node in enumerate(model.nodes):
        start = offsets[position]
        header = (
            6 + len(node.class_name.encode("ascii")) if node.kind == "definition" else 2
        )
        body_start = start + header
        body_end = body_start + len(node.body)
        if body_start <= absolute and absolute + width <= body_end:
            return CountField(position, absolute - body_start, width)
    raise GrowError(f"offset {absolute} does not fall inside any node body")


def relocate(field: CountField, plan: tuple[tuple[int, int], ...]) -> CountField:
    for position, (source, copy_id) in enumerate(plan):
        if source == field.node and copy_id == 0:
            return CountField(position, field.body_offset, field.width)
    raise GrowError(f"node {field.node} vanished from the growth plan")


def grow(
    model: modellib.Model,
    blocks: tuple[renumberlib.Block, ...],
    copies: int,
    counts: tuple[tuple[CountField, int], ...],
) -> tuple[modellib.Model, tuple[tuple[int, int], ...]]:
    grown, plan = renumberlib.duplicate(model, blocks, copies)
    for field, per_feature in counts:
        moved = relocate(field, plan)
        moved.write(grown, field.read(model) + per_feature * copies)
    return grown, plan
