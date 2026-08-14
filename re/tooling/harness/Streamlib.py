from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for candidate in (HERE, ROOT, ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from convert.adapters.solidworks.container.Container import SldprtArchive, _template_fields
from convert.adapters.solidworks import resolved as resolvedlib

import carchive

RESOLVED = "Contents/Config-0-ResolvedFeatures"
KEYWORDS = "swXmlContents/KeyWords"
FEATURES = "swXmlContents/Features"
PARTITION = "Contents/Config-0-Partition"

COMP_FEATURE_CLASS = "moCompFeature_c"
COMP_ENTRY_STRIDE = 119
COMP_FIRST_ENTRY = 93
COMP_ENTRY_ID_BACK = 8
COMP_ENTRY_TIME_BACK = 4

BOSS_FLAGS = 0x40000140
BOSS_FLAGS_ALT = 0x40000040
CUT_FLAGS = 0x400201CA
SKETCH_FLAGS = 0x40000000
PLANE_FLAGS = 0xC0000000

BLIND = 0
THROUGH_ALL = 1
MID_PLANE = 6

FIRST_REVERSE_BACK = 824
FIRST_END_CONDITION_BACK = 818
LATER_REVERSE_BACK = 721
LATER_END_CONDITION_BACK = 715


@dataclass(frozen=True, slots=True)
class Donor:
    path: Path
    blob: bytes
    file_id: int
    format_version: int
    signatures: tuple[bytes, bytes, bytes]
    type_ids: dict[str, int]
    order: tuple[str, ...]
    streams: dict[str, bytes]

    @property
    def resolved(self) -> bytes:
        return self.streams[RESOLVED]


def load_donor(path: str | Path) -> Donor:
    source = Path(path)
    blob = source.read_bytes()
    archive = SldprtArchive.from_bytes(blob)
    signatures, type_ids = _template_fields(blob, archive)
    order = tuple(
        record.name for record in sorted(archive.records, key=lambda item: item.offset)
    )
    return Donor(
        path=source,
        blob=blob,
        file_id=archive.file_id,
        format_version=archive.format_version,
        signatures=signatures,
        type_ids=type_ids,
        order=order,
        streams=archive.streams,
    )


def rebuild(
    donor: Donor,
    replacements: dict[str, bytes],
    *,
    drop: frozenset[str] = frozenset({PARTITION}),
) -> bytes:
    from convert.adapters.solidworks.container.Container import build_sldprt

    items: list[tuple[str, bytes]] = []
    for name in donor.order:
        if name in drop:
            continue
        items.append((name, replacements.get(name, donor.streams[name])))
    for name, payload in replacements.items():
        if name not in donor.order:
            items.append((name, payload))
    return build_sldprt(items, template=donor.blob)


def comp_feature_span(blob: bytes) -> tuple[int, int]:
    definitions = carchive.class_definitions(blob)
    for index, definition in enumerate(definitions):
        if definition.name != COMP_FEATURE_CLASS:
            continue
        end = (
            definitions[index + 1].tag_offset
            if index + 1 < len(definitions)
            else len(blob)
        )
        return definition.data_offset, end
    raise KeyError(COMP_FEATURE_CLASS)


def comp_feature_entries(blob: bytes) -> tuple[tuple[int, int, int, int], ...]:
    start, end = comp_feature_span(blob)
    total = end - start
    if total < COMP_FIRST_ENTRY:
        raise ValueError("moCompFeature_c record is too short")
    remainder = total - COMP_FIRST_ENTRY
    if remainder % COMP_ENTRY_STRIDE:
        raise ValueError(
            f"moCompFeature_c record length {total} is not "
            f"{COMP_FIRST_ENTRY} + n*{COMP_ENTRY_STRIDE}"
        )
    count = 1 + remainder // COMP_ENTRY_STRIDE
    result: list[tuple[int, int, int, int]] = []
    cursor = start
    for index in range(count):
        width = COMP_FIRST_ENTRY if index == 0 else COMP_ENTRY_STRIDE
        entry_end = cursor + width
        feature_id = struct.unpack_from("<I", blob, entry_end - COMP_ENTRY_ID_BACK)[0]
        stamp = struct.unpack_from("<I", blob, entry_end - COMP_ENTRY_TIME_BACK)[0]
        result.append((cursor, entry_end, feature_id, stamp))
        cursor = entry_end
    return tuple(result)


def features(blob: bytes) -> tuple[resolvedlib.FeatureLayout, ...]:
    return resolvedlib.locate_features(blob)


def tree_nodes(blob: bytes) -> tuple[resolvedlib.NameRecord, ...]:
    return resolvedlib.tree_nodes(blob)


def write_u32(output: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", output, offset, value)


def write_double(output: bytearray, offset: int, value: float) -> None:
    struct.pack_into("<d", output, offset, value)


def read_u32(blob: bytes, offset: int) -> int:
    return struct.unpack_from("<I", blob, offset)[0]


def read_double(blob: bytes, offset: int) -> float:
    return struct.unpack_from("<d", blob, offset)[0]


def flag_offsets(ordinal: int, depth_offset: int) -> tuple[int, int]:
    if ordinal == 0:
        return (
            depth_offset - FIRST_REVERSE_BACK,
            depth_offset - FIRST_END_CONDITION_BACK,
        )
    return (
        depth_offset - LATER_REVERSE_BACK,
        depth_offset - LATER_END_CONDITION_BACK,
    )
