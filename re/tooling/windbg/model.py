from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
GRAMMAR = HERE.parent / "harness"
for candidate in (HERE, GRAMMAR):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import segment as segmentlib

NEW_CLASS_TAG = 0xFFFF
CLASS_TAG_BIT = 0x8000
BIG_OBJECT_TAG = 0x7FFF
NULL_TAG = 0x0000


class ModelError(RuntimeError):
    __slots__ = ()


@dataclass(slots=True)
class Node:
    kind: str
    body: bytes
    schema: int = 0
    class_name: str = ""
    target: int = -1
    literal: int = 0
    origin: int = -1
    class_index: int = 0
    object_index: int = 0


@dataclass(slots=True)
class Model:
    header: bytes
    base: int
    nodes: list[Node] = field(default_factory=list)

    def clone(self) -> "Model":
        return Model(
            header=self.header,
            base=self.base,
            nodes=[
                Node(
                    kind=node.kind,
                    body=node.body,
                    schema=node.schema,
                    class_name=node.class_name,
                    target=node.target,
                    literal=node.literal,
                    origin=node.origin,
                )
                for node in self.nodes
            ],
        )

    def definition_index(self, name: str) -> int:
        for position, node in enumerate(self.nodes):
            if node.kind == "definition" and node.class_name == name:
                return position
        raise KeyError(name)

    def assign(self) -> None:
        counter = self.base
        for node in self.nodes:
            if node.kind == "definition":
                node.class_index = counter
                node.object_index = counter + 1
                counter += 2
            elif node.kind == "classref":
                node.class_index = 0
                node.object_index = counter
                counter += 1
            else:
                node.class_index = 0
                node.object_index = 0

    def emit(self) -> bytes:
        self.assign()
        out = bytearray(self.header)
        for node in self.nodes:
            if node.kind == "definition":
                encoded = node.class_name.encode("ascii")
                out += struct.pack("<HHH", NEW_CLASS_TAG, node.schema, len(encoded))
                out += encoded
            elif node.kind == "classref":
                if node.target < 0:
                    token = node.literal
                else:
                    token = CLASS_TAG_BIT | self.nodes[node.target].class_index
                if token & ~CLASS_TAG_BIT >= BIG_OBJECT_TAG:
                    raise ModelError(
                        f"class index {token & ~CLASS_TAG_BIT} needs wBigObjectTag"
                    )
                out += struct.pack("<H", token)
            elif node.kind == "objectref":
                token = (
                    node.literal
                    if node.target < 0
                    else self.nodes[node.target].object_index
                )
                if token >= BIG_OBJECT_TAG:
                    raise ModelError(f"object index {token} needs wBigObjectTag")
                out += struct.pack("<H", token)
            elif node.kind == "null":
                out += struct.pack("<H", NULL_TAG)
            else:
                raise ModelError(f"cannot emit node kind {node.kind}")
            out += node.body
        return bytes(out)


def parse(blob: bytes, segments: tuple[segmentlib.Segment, ...]) -> Model:
    if not segments:
        raise ModelError("empty segmentation")
    base = segments[0].map_index
    model = Model(header=blob[: segments[0].offset], base=base)
    class_position: dict[int, int] = {}
    object_position: dict[int, int] = {}
    for position, item in enumerate(segments):
        body = blob[item.offset + item.header : item.end]
        if item.kind == "definition":
            schema = struct.unpack_from("<H", blob, item.offset + 2)[0]
            node = Node(
                kind="definition",
                body=body,
                schema=schema,
                class_name=item.class_name,
                origin=item.offset,
            )
            class_position[item.class_index] = position
            object_position[item.object_index] = position
        elif item.kind == "classref":
            node = Node(
                kind="classref",
                body=body,
                literal=item.tag,
                target=class_position.get(item.class_index, -1),
                class_name=item.class_name,
                origin=item.offset,
            )
            object_position[item.object_index] = position
        elif item.kind == "objectref":
            node = Node(
                kind="objectref",
                body=body,
                literal=item.tag,
                target=object_position.get(item.tag, -1),
                origin=item.offset,
            )
        elif item.kind == "null":
            node = Node(kind="null", body=body, origin=item.offset)
        else:
            raise ModelError(f"unsupported tag kind {item.kind} at {item.offset}")
        model.nodes.append(node)
    for position, item in enumerate(segments):
        node = model.nodes[position]
        if node.kind == "objectref" and node.target < 0 and item.tag >= base:
            raise ModelError(
                f"object reference {item.tag} at {item.offset} is unresolved"
            )
        if node.kind == "classref" and node.target < 0 and item.class_index >= base:
            raise ModelError(
                f"class reference {item.class_index} at {item.offset} is unresolved"
            )
    model.assign()
    return model


def load(
    part: Path, log: Path, *, stream: str | None = None
) -> tuple[bytes, Model, tuple[segmentlib.Segment, ...]]:
    if stream is None:
        blob, segments = segmentlib.load(part, log)
    else:
        blob, segments = segmentlib.load(part, log, stream=stream)
    return blob, parse(blob, segments), segments


def token_table(model: Model) -> list[dict[str, int | str]]:
    model.assign()
    offsets = node_offsets(model)
    rows: list[dict[str, int | str]] = []
    for position, node in enumerate(model.nodes):
        rows.append(
            {
                "node": position,
                "offset": offsets[position],
                "kind": node.kind,
                "class_name": node.class_name,
                "map_index": node.object_index,
                "class_index": node.class_index,
                "target": node.target,
                "literal": node.literal,
            }
        )
    return rows


def node_offsets(model: Model) -> list[int]:
    offsets: list[int] = []
    cursor = len(model.header)
    for node in model.nodes:
        offsets.append(cursor)
        if node.kind == "definition":
            cursor += 6 + len(node.class_name.encode("ascii"))
        else:
            cursor += 2
        cursor += len(node.body)
    offsets.append(cursor)
    return offsets


def main() -> int:
    arguments = sys.argv[1:]
    if len(arguments) % 3:
        raise SystemExit("usage: model.py <label> <part> <log> [...]")
    for position in range(0, len(arguments), 3):
        label = arguments[position]
        part = Path(arguments[position + 1]).resolve()
        log = Path(arguments[position + 2]).resolve()
        blob, model, _ = load(part, log)
        rebuilt = model.emit()
        external_classes = sum(
            1 for node in model.nodes if node.kind == "classref" and node.target < 0
        )
        external_objects = sum(
            1 for node in model.nodes if node.kind == "objectref" and node.target < 0
        )
        status = "IDENTICAL" if rebuilt == blob else "DIFFERS"
        print(
            f"{label:14s} nodes={len(model.nodes):4d} base={model.base} "
            f"external classrefs={external_classes:3d} objectrefs={external_objects:3d} "
            f"round-trip={status} {len(rebuilt)}/{len(blob)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
