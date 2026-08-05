from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
for candidate in (ROOT, ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from convert.adapters.solidworks.container import SldprtArchive

RESOLVED = "Contents/Config-0-ResolvedFeatures"
KEYWORDS = "swXmlContents/KeyWords"
FEATURES = "swXmlContents/Features"
PARTITION = "Contents/Config-0-Partition"

NEW_CLASS_TAG = 0xFFFF
CLASS_TAG_BIT = 0x8000
BIG_OBJECT_TAG = 0x7FFF
NULL_TAG = 0x0000
STRING_UNICODE_MARKER = bytes.fromhex("fffeff")
MAX_CLASS_NAME = 64


@dataclass(frozen=True, slots=True)
class ClassDefinition:
    tag_offset: int
    schema: int
    name: str
    name_offset: int
    data_offset: int


@dataclass(frozen=True, slots=True)
class ClassReference:
    offset: int
    index: int


def stream(path: Path, name: str = RESOLVED) -> bytes:
    return SldprtArchive.open(path).require(name)


def streams(path: Path) -> dict[str, bytes]:
    return SldprtArchive.open(path).streams


def class_definitions(blob: bytes) -> tuple[ClassDefinition, ...]:
    result: list[ClassDefinition] = []
    cursor = 0
    limit = len(blob)
    while True:
        offset = blob.find(b"\xff\xff", cursor)
        if offset < 0 or offset + 6 > limit:
            break
        cursor = offset + 1
        schema, length = struct.unpack_from("<HH", blob, offset + 2)
        if not 0 < length <= MAX_CLASS_NAME:
            continue
        start = offset + 6
        end = start + length
        if end > limit:
            continue
        raw = blob[start:end]
        try:
            name = raw.decode("ascii")
        except UnicodeDecodeError:
            continue
        if not name.replace("_", "").isalnum():
            continue
        result.append(ClassDefinition(offset, schema, name, start, end))
    return tuple(result)


def class_index_map(blob: bytes) -> dict[str, int]:
    definitions = class_definitions(blob)
    references = class_references(blob, definitions)
    counts: dict[int, int] = {}
    for reference in references:
        counts[reference.index] = counts.get(reference.index, 0) + 1
    return {definition.name: definition.tag_offset for definition in definitions} | {
        f"#ref:{index}": count for index, count in sorted(counts.items())
    }


def class_references(
    blob: bytes, definitions: tuple[ClassDefinition, ...]
) -> tuple[ClassReference, ...]:
    boundaries = _definition_spans(definitions)
    result: list[ClassReference] = []
    for offset in range(0, len(blob) - 1):
        if _inside(boundaries, offset):
            continue
        token = struct.unpack_from("<H", blob, offset)[0]
        if token == NEW_CLASS_TAG or not token & CLASS_TAG_BIT:
            continue
        result.append(ClassReference(offset, token & ~CLASS_TAG_BIT))
    return tuple(result)


def named_object_tokens(blob: bytes) -> dict[int, int]:
    counts: dict[int, int] = {}
    cursor = 0
    while True:
        offset = blob.find(STRING_UNICODE_MARKER, cursor)
        if offset < 2:
            if offset < 0:
                break
            cursor = offset + 1
            continue
        cursor = offset + 1
        token = struct.unpack_from("<H", blob, offset - 2)[0]
        counts[token] = counts.get(token, 0) + 1
    return dict(sorted(counts.items()))


def unicode_strings(blob: bytes) -> tuple[tuple[int, int, str], ...]:
    result: list[tuple[int, int, str]] = []
    cursor = 0
    while True:
        offset = blob.find(STRING_UNICODE_MARKER, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        units_offset = offset + 3
        if units_offset >= len(blob):
            continue
        units = blob[units_offset]
        if units == 0 or units == 0xFF:
            continue
        start = units_offset + 1
        end = start + units * 2
        if end > len(blob):
            continue
        try:
            text = blob[start:end].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if any(not character.isprintable() for character in text):
            continue
        token = (
            struct.unpack_from("<H", blob, offset - 2)[0] if offset >= 2 else NULL_TAG
        )
        result.append((offset, token, text))
    return tuple(result)


def _definition_spans(
    definitions: tuple[ClassDefinition, ...],
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (definition.tag_offset, definition.data_offset) for definition in definitions
    )


def _inside(spans: tuple[tuple[int, int], ...], offset: int) -> bool:
    for start, end in spans:
        if start <= offset < end:
            return True
    return False


def hexdump(blob: bytes, offset: int, width: int = 64) -> str:
    start = max(0, offset)
    end = min(len(blob), offset + width)
    return blob[start:end].hex(" ")
