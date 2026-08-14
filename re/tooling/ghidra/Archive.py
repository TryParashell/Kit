from __future__ import annotations

from dataclasses import dataclass
import struct

NEW_CLASS_TAG = 0xFFFF
CLASS_TAG_BIT = 0x8000
BIG_OBJECT_TAG = 0x7FFF
NULL_TAG = 0x0000

DEFINITION = "definition"
CLASSREF = "classref"
OBJECTREF = "objectref"
NULL = "null"
BIG = "big"

MAX_CLASS_NAME = 64


class ArchiveError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Tag:
    offset: int
    token: int
    kind: str
    header: int
    schema: int
    name: str
    index: int


@dataclass(frozen=True, slots=True)
class Object:
    order: int
    offset: int
    end: int
    kind: str
    token: int
    class_slot: int
    object_slot: int
    class_name: str
    header: int

    @property
    def length(self) -> int:
        return self.end - self.offset

    @property
    def body_offset(self) -> int:
        return self.offset + self.header

    @property
    def body_length(self) -> int:
        return self.end - self.offset - self.header


def decode_tag(blob: bytes, offset: int) -> Tag:
    if offset + 2 > len(blob):
        raise ArchiveError(f"tag at {offset} runs past end of stream {len(blob)}")
    token = struct.unpack_from("<H", blob, offset)[0]
    if token == NEW_CLASS_TAG:
        schema, length = struct.unpack_from("<HH", blob, offset + 2)
        if not 0 < length <= MAX_CLASS_NAME:
            raise ArchiveError(f"class name length {length} at {offset} is implausible")
        raw = blob[offset + 6 : offset + 6 + length]
        return Tag(
            offset, token, DEFINITION, 6 + length, schema, raw.decode("ascii"), -1
        )
    if token == NULL_TAG:
        return Tag(offset, token, NULL, 2, 0, "", -1)
    if token == BIG_OBJECT_TAG:
        index = struct.unpack_from("<I", blob, offset + 2)[0]
        kind = CLASSREF if index & 0x80000000 else OBJECTREF
        return Tag(offset, token, BIG, 6, 0, "", index & 0x7FFFFFFF)
    if token & CLASS_TAG_BIT:
        return Tag(offset, token, CLASSREF, 2, 0, "", token & ~CLASS_TAG_BIT)
    return Tag(offset, token, OBJECTREF, 2, 0, "", token)


def slots_consumed(kind: str) -> int:
    if kind == DEFINITION:
        return 2
    if kind in (CLASSREF, BIG):
        return 1
    return 0


def allocate(
    tags: tuple[Tag, ...], base: int, ends: tuple[int, ...]
) -> tuple[Object, ...]:
    counter = base
    result: list[Object] = []
    names: dict[int, str] = {}
    for order, (tag, end) in enumerate(zip(tags, ends)):
        if tag.kind == DEFINITION:
            class_slot = counter
            object_slot = counter + 1
            names[class_slot] = tag.name
            counter += 2
            name = tag.name
        elif tag.kind in (CLASSREF, BIG):
            class_slot = tag.index
            object_slot = counter
            counter += 1
            name = names.get(tag.index, "")
        else:
            class_slot = -1
            object_slot = -1
            name = tag.kind
        result.append(
            Object(
                order=order,
                offset=tag.offset,
                end=end,
                kind=tag.kind,
                token=tag.token,
                class_slot=class_slot,
                object_slot=object_slot,
                class_name=name,
                header=tag.header,
            )
        )
    return tuple(result)


def class_table(objects: tuple[Object, ...]) -> dict[int, str]:
    return {
        item.class_slot: item.class_name for item in objects if item.kind == DEFINITION
    }


def next_slot(objects: tuple[Object, ...], base: int) -> int:
    counter = base
    for item in objects:
        counter += slots_consumed(item.kind)
    return counter


def encode_reference(kind: str, index: int) -> bytes:
    if kind == CLASSREF:
        if index >= BIG_OBJECT_TAG:
            raise ArchiveError(f"class index {index} needs the big-object escape")
        return struct.pack("<H", CLASS_TAG_BIT | index)
    if kind == OBJECTREF:
        if index >= BIG_OBJECT_TAG:
            raise ArchiveError(f"object index {index} needs the big-object escape")
        return struct.pack("<H", index)
    raise ArchiveError(f"{kind} is not a reference tag")


def retarget(blob: bytes, objects: tuple[Object, ...], shift: dict[int, int]) -> bytes:
    output = bytearray(blob)
    for item in objects:
        if item.kind == CLASSREF:
            target = shift.get(item.class_slot, item.class_slot)
            output[item.offset : item.offset + 2] = encode_reference(CLASSREF, target)
        elif item.kind == OBJECTREF:
            index = item.token
            target = shift.get(index, index)
            output[item.offset : item.offset + 2] = encode_reference(OBJECTREF, target)
        elif item.kind == BIG:
            raise ArchiveError(
                f"big-object escape at {item.offset} is not supported by retarget"
            )
    return bytes(output)
