from __future__ import annotations

from pathlib import PureWindowsPath
import re
from types import MappingProxyType
from typing import Iterable

from convert.adapters.base import AdapterInfo
from interchange import Capability


PART_FORMAT_ID = "solidworks.sldprt"
ASSEMBLY_FORMAT_ID = "solidworks.sldasm"
DRAWING_FORMAT_ID = "solidworks.slddrw"
DRAWING_SUFFIX = ".slddrw"
DRAWING_FORMAT_NAME = "SOLIDWORKS drawing"
FORMAT_ID_BY_SUFFIX = MappingProxyType(
    {
        ".sldprt": PART_FORMAT_ID,
        ".sldasm": ASSEMBLY_FORMAT_ID,
    }
)
SUFFIX_BY_FORMAT_ID = MappingProxyType(
    {format_id: suffix for suffix, format_id in FORMAT_ID_BY_SUFFIX.items()}
)
PART_SUFFIX = SUFFIX_BY_FORMAT_ID[PART_FORMAT_ID]
ASSEMBLY_SUFFIX = SUFFIX_BY_FORMAT_ID[ASSEMBLY_FORMAT_ID]
FORMAT_IDS = tuple(FORMAT_ID_BY_SUFFIX.values())

INFO = AdapterInfo(
    format_id=PART_FORMAT_ID,
    name="SOLIDWORKS",
    version="1.0",
    extensions=tuple(FORMAT_ID_BY_SUFFIX),
    aliases=(ASSEMBLY_FORMAT_ID,),
    capabilities=frozenset(Capability),
    media_types=(
        "application/x-solidworks-part",
        "application/x-solidworks-assembly",
    ),
    part_extensions=(PART_SUFFIX,),
    assembly_extensions=(ASSEMBLY_SUFFIX,),
)
CONTAINER_VERSIONS = frozenset({3, 4})

COMPONENT_TREE_STREAM = "swXmlContents/COMPINSTANCETREE"
DISPLAY_LISTS_STREAM = "Contents/DisplayLists"
KEYWORDS_STREAM = "swXmlContents/KeyWords"
FEATURES_STREAM = "swXmlContents/Features"
RESOLVED_FEATURES_STREAM = "Contents/Config-0-ResolvedFeatures"
PARTITION_STREAM = "Contents/Config-0-Partition"
SOLIDWORKS_STREAM = "Contents/SolidWorks"
KIT_DOCUMENT_STREAM = "Kit/Interchange"
KIT_NATIVE_STREAM = "Kit/Native"
KIT_RESOLVED_STREAM = "Kit/ResolvedFeatures"
CONTENT_TYPES_STREAM = "[Content_Types].xml"
RELATIONSHIPS_STREAM = "_rels/.rels"
MATES_STREAM_NAME = "MatesList"
MATES_STREAM_SUFFIX = f"-{MATES_STREAM_NAME}"
_RESOLVED_LANE_PREFIX, _RESOLVED_LANE_SUFFIX = RESOLVED_FEATURES_STREAM.split("0", 1)
RESOLVED_FEATURES_LANE = re.compile(
    rf"^{re.escape(_RESOLVED_LANE_PREFIX)}(\d+){re.escape(_RESOLVED_LANE_SUFFIX)}$"
)
DRAWING_STREAM_TOKENS = frozenset(
    {"drsheet", "drview", "drawingsheet", "drawingview", "sheetformat"}
)

CLASS_MARKER = bytes.fromhex("ffff0100")
SERIALIZED_STRING_MARKER = bytes.fromhex("fffeff")
DIMENSION_SCALAR_HEADERS = (
    bytes.fromhex("0000000000000040ffffffff00000000fffeff000000"),
    bytes.fromhex("0000000000000040ffffffff000000000000"),
)

CANONICAL_PLANE_FEATURE_TYPE = "plane"
OFFICIAL_REFERENCE_PLANE_FEATURE_TYPES = frozenset({"refplane"})
PLANE_FEATURE_TYPES = OFFICIAL_REFERENCE_PLANE_FEATURE_TYPES | {
    CANONICAL_PLANE_FEATURE_TYPE
}
SOLID_BODY_FEATURE_TYPES = frozenset({"featsolidbodyfolder", "solidbodyfolder"})


def dimension_scalar_value_offset(
    data: bytes,
    text_end: int,
    end: int,
    *,
    trailing_bytes: int = 0,
) -> int | None:
    for header in DIMENSION_SCALAR_HEADERS:
        if data[text_end : text_end + len(header)] != header:
            continue
        value_offset = text_end + len(header)
        if value_offset + 8 + trailing_bytes <= end:
            return value_offset
    return None


def is_cad_path(value: str) -> bool:
    return PureWindowsPath(value).suffix.casefold() in FORMAT_ID_BY_SUFFIX


def is_drawing_path(value: str) -> bool:
    return PureWindowsPath(value).suffix.casefold() == DRAWING_SUFFIX


def part_lane_names(names: Iterable[str]) -> tuple[str, ...]:
    return tuple(name for name in names if RESOLVED_FEATURES_LANE.fullmatch(name))


def drawing_stream_names(names: Iterable[str]) -> tuple[str, ...]:
    return tuple(
        name
        for name in names
        if any(token in name.casefold() for token in DRAWING_STREAM_TOKENS)
    )


def unsupported_document_reason(names: Iterable[str]) -> str:
    values = tuple(names)
    if part_lane_names(values) or COMPONENT_TREE_STREAM in values:
        return ""
    if drawing_stream_names(values):
        return (
            f"{DRAWING_FORMAT_NAME} content ({DRAWING_FORMAT_ID}) is not supported; "
            "SOLIDWORKS reading requires a part or assembly container"
        )
    return (
        "SOLIDWORKS container carries neither a part lane "
        f"({RESOLVED_FEATURES_STREAM}) nor an assembly lane "
        f"({COMPONENT_TREE_STREAM})"
    )


def is_component_path(value: str) -> bool:
    if "^" in value or is_cad_path(value):
        return False
    segments = value.split("/")
    if not segments:
        return False
    for segment in segments:
        if segment.count("@") != 1:
            return False
        instance, owner = segment.split("@", 1)
        if not instance.strip() or not owner.strip():
            return False
    return True
