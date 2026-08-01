from __future__ import annotations

from dataclasses import dataclass
from pathlib import PureWindowsPath
import math
import re
import struct
from typing import Iterable
import xml.etree.ElementTree as ET

from .container import SldprtArchive, SldprtFormatError
from .display import (
    NativeDisplayComponent,
    NativeTessellationFace,
    decode_display_lists,
    decode_tessellation_faces,
)


_COMPONENT_STREAM = "swXmlContents/COMPINSTANCETREE"
_DISPLAY_STREAM = "Contents/DisplayLists"
_MATES_SUFFIX = "-MatesList"
_STRING_MARKER = bytes.fromhex("fffeff")
_DIMENSION_NAME = re.compile(r"D\d+")
_WIDE_TEXT = re.compile(rb"(?:[ -~]\x00){4,}")
_DISTANCE_DIMENSION_MARKER = _STRING_MARKER + b"\x02D\x001\x00"
_MATE_ALIGNMENT_OFFSET = 159
_MATE_ENTITY_COUNT_OFFSET = 164
_DIMENSION_SCALAR_OFFSET = 30


@dataclass(frozen=True, slots=True)
class NativeAssemblyFile:
    object_id: int
    document_type: str
    creation_time: int
    source_path: str


@dataclass(frozen=True, slots=True)
class NativeAssemblyDefinition:
    object_id: int
    name: str
    document_type: str
    file_id: int
    source_path: str
    configuration_name: str
    configuration_id: int
    alternate_configuration_name: str
    last_modified_stamp: int
    configuration_flags: int
    bounding_box_m: tuple[float, float, float, float, float, float] | None
    child_occurrence_ids: tuple[int, ...]
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class NativeAssemblyOccurrence:
    object_id: int
    feature_id: int
    owner_definition_id: int
    definition_id: int
    name: str
    reference_number: int
    component_reference: str
    configuration_name: str
    configuration_id: int
    transform: tuple[float, ...]
    transform_stamp: int
    suppressed: bool
    hidden: bool
    flexible: bool
    virtual: bool
    exclude_from_bom: bool
    zone: bool
    display_mode: int
    display_quality: int
    edges_in_shaded_mode: bool
    order: int
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class NativeAssemblyConfiguration:
    object_id: int
    configuration_id: int
    name: str
    reference: str
    model_id: int
    most_recent: bool
    needs_update: bool
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class NativeDisplayState:
    object_id: int
    name: str
    configuration_id: int | None
    attributes: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class NativeMateEntity:
    component_path: str
    persistent_references: tuple[str, ...]
    source_path: str
    configuration_name: str


@dataclass(frozen=True, slots=True)
class NativeMate:
    name: str
    kind: str
    owner_definition_id: int
    order: int
    entities: tuple[NativeMateEntity, ...]
    record_offset: int
    record_length: int
    class_name: str
    serialized_strings: tuple[str, ...]
    alignment_code: int | None
    value_m: float | None
    value_offset: int | None


@dataclass(frozen=True, slots=True)
class NativeMateList:
    native_id: int
    declared_count: int
    owner_definition_id: int
    mates: tuple[NativeMate, ...]
    stream: str


@dataclass(frozen=True, slots=True)
class NativeOccurrencePath:
    occurrence_id: int
    definition_id: int
    path: str
    depth: int


@dataclass(frozen=True, slots=True)
class NativeAssembly:
    name: str
    root_definition_id: int
    files: tuple[NativeAssemblyFile, ...]
    definitions: tuple[NativeAssemblyDefinition, ...]
    occurrences: tuple[NativeAssemblyOccurrence, ...]
    configurations: tuple[NativeAssemblyConfiguration, ...]
    display_states: tuple[NativeDisplayState, ...]
    occurrence_paths: tuple[NativeOccurrencePath, ...]
    mate_lists: tuple[NativeMateList, ...]
    display_components: tuple[NativeDisplayComponent, ...]
    application_version: int


def decode_native_assembly(
    archive: SldprtArchive, *, include_tessellation: bool = False
) -> NativeAssembly:
    root = _xml_root(archive.require(_COMPONENT_STREAM))
    files = _files(root)
    file_by_id = {item.object_id: item for item in files}
    definitions, occurrences = _models(root, file_by_id)
    configurations = _configurations(root)
    if not configurations:
        raise SldprtFormatError("assembly contains no configuration")
    root_definition_id = configurations[0].model_id
    definition_by_id = {item.object_id: item for item in definitions}
    if root_definition_id not in definition_by_id:
        raise SldprtFormatError("assembly configuration references a missing model")
    occurrence_paths = expand_occurrence_paths(
        root_definition_id, definitions, occurrences
    )
    mate_lists = tuple(
        decode_mate_list(record.data, record.name, root_definition_id)
        for record in archive.records
        if record.name.startswith("Contents/Config-")
        and record.name.endswith(_MATES_SUFFIX)
    )
    display_components: tuple[NativeDisplayComponent, ...] = ()
    display = archive.get(_DISPLAY_STREAM)
    if include_tessellation and display:
        display_components = decode_display_lists(display)
    return NativeAssembly(
        name=definition_by_id[root_definition_id].name,
        root_definition_id=root_definition_id,
        files=files,
        definitions=definitions,
        occurrences=occurrences,
        configurations=configurations,
        display_states=_display_states(root),
        occurrence_paths=occurrence_paths,
        mate_lists=mate_lists,
        display_components=display_components,
        application_version=_integer(root.attrib.get("swVersion")),
    )


def decode_mate_list(
    data: bytes, stream: str = "", owner_definition_id: int = 0
) -> NativeMateList:
    if len(data) < 6:
        raise SldprtFormatError(f"mate stream is truncated: {stream}")
    native_id, declared_count = struct.unpack_from("<IH", data, 0)
    class_offset = data.find(bytes.fromhex("ffff0100"), 6)
    if class_offset < 0 or class_offset + 6 > len(data):
        raise SldprtFormatError(f"mate stream has no class table: {stream}")
    class_size = struct.unpack_from("<H", data, class_offset + 4)[0]
    class_end = class_offset + 6 + class_size
    if class_end + 5 > len(data):
        raise SldprtFormatError(f"mate class record is truncated: {stream}")
    object_prefix = data[class_end : class_end + 2]
    name_prefix = object_prefix + _STRING_MARKER
    candidates = [
        item
        for item in _prefixed_strings(data, name_prefix)
        if not _DIMENSION_NAME.fullmatch(item[1])
    ]
    if len(candidates) != declared_count:
        raise SldprtFormatError(
            f"mate count mismatch in {stream}: expected {declared_count}, decoded {len(candidates)}"
        )
    starts = [_mate_record_start(data, offset) for offset, _, _ in candidates]
    mates: list[NativeMate] = []
    for order, ((_, name, name_end), start) in enumerate(zip(candidates, starts)):
        end = starts[order + 1] if order + 1 < len(starts) else len(data)
        strings = _record_strings(data, start, end)
        kind = _mate_kind(name)
        alignment_code, value_m, value_offset = (
            _distance_mate_data(data, start, end, name_end)
            if kind == "distance"
            else (None, None, None)
        )
        mates.append(
            NativeMate(
                name=name,
                kind=kind,
                owner_definition_id=owner_definition_id,
                order=order,
                entities=_mate_entities(strings),
                record_offset=start,
                record_length=end - start,
                class_name=_inline_class_name(data, start),
                serialized_strings=strings,
                alignment_code=alignment_code,
                value_m=value_m,
                value_offset=value_offset,
            )
        )
    return NativeMateList(
        native_id=native_id,
        declared_count=declared_count,
        owner_definition_id=owner_definition_id,
        mates=tuple(mates),
        stream=stream,
    )


def expand_occurrence_paths(
    root_definition_id: int,
    definitions: Iterable[NativeAssemblyDefinition],
    occurrences: Iterable[NativeAssemblyOccurrence],
) -> tuple[NativeOccurrencePath, ...]:
    definition_by_id = {item.object_id: item for item in definitions}
    children: dict[int, list[NativeAssemblyOccurrence]] = {}
    for occurrence in occurrences:
        children.setdefault(occurrence.owner_definition_id, []).append(occurrence)
    result: list[NativeOccurrencePath] = []

    def visit(
        definition_id: int, prefix: str, depth: int, stack: frozenset[int]
    ) -> None:
        if definition_id in stack:
            raise SldprtFormatError("cyclic assembly definition hierarchy")
        owner = definition_by_id[definition_id]
        for occurrence in children.get(definition_id, []):
            segment = f"{occurrence.name}-{occurrence.reference_number}@{owner.name}"
            path = f"{prefix}/{segment}" if prefix else segment
            result.append(
                NativeOccurrencePath(
                    occurrence_id=occurrence.object_id,
                    definition_id=occurrence.definition_id,
                    path=path,
                    depth=depth,
                )
            )
            target = definition_by_id[occurrence.definition_id]
            if target.document_type == "ASSEMBLY":
                visit(
                    target.object_id,
                    path,
                    depth + 1,
                    stack | {definition_id},
                )

    visit(root_definition_id, "", 0, frozenset())
    return tuple(result)


def _xml_root(data: bytes) -> ET.Element:
    marker = data.find(b"<?xml")
    if marker >= 0:
        data = data[marker:]
    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise SldprtFormatError(f"invalid assembly component XML: {exc}") from exc


def _local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _elements(root: ET.Element, name: str) -> tuple[ET.Element, ...]:
    return tuple(item for item in root.iter() if _local_name(item) == name)


def _files(root: ET.Element) -> tuple[NativeAssemblyFile, ...]:
    return tuple(
        NativeAssemblyFile(
            object_id=_integer(item.attrib.get("id")),
            document_type=item.attrib.get("swDocType", ""),
            creation_time=_integer(item.attrib.get("swCreationTime")),
            source_path=item.attrib.get("swPath", ""),
        )
        for item in _elements(root, "swFile")
    )


def _models(
    root: ET.Element, files: dict[int, NativeAssemblyFile]
) -> tuple[tuple[NativeAssemblyDefinition, ...], tuple[NativeAssemblyOccurrence, ...]]:
    definitions: list[NativeAssemblyDefinition] = []
    occurrences: list[NativeAssemblyOccurrence] = []
    order = 0
    for item in _elements(root, "swModel"):
        file_id = _integer(item.attrib.get("swFileRef"))
        source = files.get(file_id)
        if source is None:
            raise SldprtFormatError(f"assembly model references missing file {file_id}")
        child_elements = tuple(
            child for child in item if _local_name(child) == "swReference"
        )
        definition_id = _integer(item.attrib.get("id"))
        definitions.append(
            NativeAssemblyDefinition(
                object_id=definition_id,
                name=item.attrib.get("swName", ""),
                document_type=source.document_type,
                file_id=file_id,
                source_path=source.source_path,
                configuration_name=item.attrib.get("swConfigurationName", ""),
                configuration_id=_integer(item.attrib.get("swConfigurationId")),
                alternate_configuration_name=item.attrib.get(
                    "swConfigurationAlternateName", ""
                ),
                last_modified_stamp=_integer(item.attrib.get("swLastModifiedStamp")),
                configuration_flags=_integer(item.attrib.get("swConfigurationFlags")),
                bounding_box_m=_bounding_box(item.attrib.get("swBoundingBox")),
                child_occurrence_ids=tuple(
                    _integer(child.attrib.get("id")) for child in child_elements
                ),
                attributes=tuple(sorted(item.attrib.items())),
            )
        )
        for child in child_elements:
            transform = _float_tuple(child.attrib.get("swTransform"), 16)
            occurrences.append(
                NativeAssemblyOccurrence(
                    object_id=_integer(child.attrib.get("id")),
                    feature_id=_integer(child.attrib.get("swID")),
                    owner_definition_id=definition_id,
                    definition_id=_integer(child.attrib.get("swModelRef")),
                    name=child.attrib.get("swName", ""),
                    reference_number=_integer(child.attrib.get("swReferenceNumber"), 1),
                    component_reference=child.attrib.get("swComponentReference", ""),
                    configuration_name=child.attrib.get("swConfigurationName", ""),
                    configuration_id=_integer(child.attrib.get("swConfigurationId")),
                    transform=transform,
                    transform_stamp=_integer(child.attrib.get("swTransformStamp")),
                    suppressed=_yes(child.attrib.get("swSuppressed")),
                    hidden=_yes(child.attrib.get("swHidden")),
                    flexible=_yes(child.attrib.get("swFlexible")),
                    virtual=_yes(child.attrib.get("swIsVirtualComponent")),
                    exclude_from_bom=_yes(child.attrib.get("swExcludeFromBOM")),
                    zone=_yes(child.attrib.get("swZone")),
                    display_mode=_integer(child.attrib.get("swDisplayMode")),
                    display_quality=_integer(child.attrib.get("swHlrDisplayQuality")),
                    edges_in_shaded_mode=_yes(child.attrib.get("swEdgesInShadedMode")),
                    order=order,
                    attributes=tuple(sorted(child.attrib.items())),
                )
            )
            order += 1
    definition_ids = {item.object_id for item in definitions}
    for occurrence in occurrences:
        if occurrence.definition_id not in definition_ids:
            raise SldprtFormatError(
                f"component {occurrence.object_id} references missing model {occurrence.definition_id}"
            )
    return tuple(definitions), tuple(occurrences)


def _configurations(root: ET.Element) -> tuple[NativeAssemblyConfiguration, ...]:
    return tuple(
        NativeAssemblyConfiguration(
            object_id=_integer(item.attrib.get("id")),
            configuration_id=_integer(item.attrib.get("swID")),
            name=item.attrib.get("swName", ""),
            reference=item.attrib.get("swReference", ""),
            model_id=_integer(item.attrib.get("swModelRef")),
            most_recent=_yes(item.attrib.get("swMostRecentConfiguration")),
            needs_update=_yes(item.attrib.get("swConfigurationNeedsUpdate")),
            attributes=tuple(sorted(item.attrib.items())),
        )
        for item in _elements(root, "swConfiguration")
    )


def _display_states(root: ET.Element) -> tuple[NativeDisplayState, ...]:
    return tuple(
        NativeDisplayState(
            object_id=_integer(item.attrib.get("id")),
            name=item.attrib.get("swName", ""),
            configuration_id=(
                _integer(item.attrib.get("swConfigurationId"))
                if "swConfigurationId" in item.attrib
                else None
            ),
            attributes=tuple(sorted(item.attrib.items())),
        )
        for item in _elements(root, "swDisplayState")
    )


def _prefixed_strings(data: bytes, prefix: bytes) -> tuple[tuple[int, str, int], ...]:
    result: list[tuple[int, str, int]] = []
    cursor = 0
    while True:
        offset = data.find(prefix, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        length_offset = offset + len(prefix)
        decoded = _utf16_string(data, length_offset)
        if decoded is not None:
            value, end = decoded
            result.append((offset, value, end))
    return tuple(result)


def _serialized_strings(
    data: bytes, start: int = 0, end: int | None = None
) -> tuple[tuple[int, str, int], ...]:
    limit = len(data) if end is None else min(end, len(data))
    result: list[tuple[int, str, int]] = []
    cursor = max(start, 0)
    while True:
        offset = data.find(_STRING_MARKER, cursor, limit)
        if offset < 0:
            break
        cursor = offset + 1
        decoded = _utf16_string(data, offset + len(_STRING_MARKER), limit)
        if decoded is not None:
            value, string_end = decoded
            result.append((offset, value, string_end))
    return tuple(result)


def _utf16_string(
    data: bytes, length_offset: int, end: int | None = None
) -> tuple[str, int] | None:
    limit = len(data) if end is None else end
    if length_offset >= limit:
        return None
    length = data[length_offset]
    if length == 0xFF:
        return None
    string_start = length_offset + 1
    string_end = string_start + length * 2
    if string_end > limit:
        return None
    try:
        value = data[string_start:string_end].decode("utf-16le")
    except UnicodeDecodeError:
        return None
    if any(ord(character) < 0x20 for character in value):
        return None
    return value, string_end


def _mate_record_start(data: bytes, name_prefix_offset: int) -> int:
    inline = data.rfind(bytes.fromhex("ffff0100"), 0, name_prefix_offset)
    if inline >= 0 and inline + 6 <= name_prefix_offset:
        size = struct.unpack_from("<H", data, inline + 4)[0]
        if inline + 6 + size == name_prefix_offset:
            return inline
    return max(6, name_prefix_offset - 2)


def _inline_class_name(data: bytes, start: int) -> str:
    if data[start : start + 4] != bytes.fromhex("ffff0100"):
        return ""
    if start + 6 > len(data):
        return ""
    size = struct.unpack_from("<H", data, start + 4)[0]
    try:
        return data[start + 6 : start + 6 + size].decode("ascii")
    except UnicodeDecodeError:
        return ""


def _mate_entities(strings: tuple[str, ...]) -> tuple[NativeMateEntity, ...]:
    paths = tuple(value for value in strings if _component_path(value))
    source_paths = tuple(value for value in strings if _cad_path(value))
    entity_values: list[tuple[str, list[str]]] = []
    persistent: list[str] = []
    for value in strings:
        if value.startswith("mo"):
            persistent.append(value)
            continue
        if _component_path(value):
            entity_values.append((value, persistent))
            persistent = []
            continue
        if "@" in value and entity_values:
            entity_values[-1][1].append(value)
    entities: list[NativeMateEntity] = []
    for component_path, references in entity_values:
        leaf = component_path.rsplit("/", 1)[-1].split("@", 1)[0]
        source_name = re.sub(r"-\d+$", "", leaf).lower()
        source_path = next(
            (
                value
                for value in source_paths
                if PureWindowsPath(value).stem.lower() == source_name
            ),
            "",
        )
        entities.append(
            NativeMateEntity(
                component_path=component_path,
                persistent_references=tuple(references),
                source_path=source_path,
                configuration_name="",
            )
        )
    synthetic = tuple(value for value in strings if "^" in value and "@" in value)
    entities.extend(
        NativeMateEntity(
            component_path="",
            persistent_references=(value,),
            source_path="",
            configuration_name="",
        )
        for value in synthetic
    )
    if len(entities) != len(paths) + len(synthetic):
        raise SldprtFormatError("mate entity path decoding is inconsistent")
    return tuple(entities)


def _mate_kind(name: str) -> str:
    kinds = (
        ("Concentric", "concentric"),
        ("Coincident", "coincident"),
        ("CamMateTangent", "cam_tangent"),
        ("GearMate", "gear"),
        ("BeltMates", "group"),
        ("BeltMate", "belt"),
        ("Distance", "distance"),
        ("LockToSketchMate", "lock_to_sketch"),
    )
    return next((kind for prefix, kind in kinds if name.startswith(prefix)), "native")


def _distance_mate_data(
    data: bytes, start: int, end: int, name_end: int
) -> tuple[int | None, float | None, int | None]:
    alignment_offset = name_end + _MATE_ALIGNMENT_OFFSET
    entity_count_offset = name_end + _MATE_ENTITY_COUNT_OFFSET
    if entity_count_offset + 4 > end:
        return None, None, None
    alignment_code = struct.unpack_from("<H", data, alignment_offset)[0]
    if alignment_code not in {1, 2}:
        alignment_code = None
    entity_count = struct.unpack_from("<I", data, entity_count_offset)[0]
    if entity_count != 2:
        return alignment_code, None, None
    marker_offset = data.find(_DISTANCE_DIMENSION_MARKER, start, end)
    if marker_offset < 0:
        return alignment_code, None, None
    if data.find(_DISTANCE_DIMENSION_MARKER, marker_offset + 1, end) >= 0:
        return alignment_code, None, None
    value_offset = marker_offset + _DIMENSION_SCALAR_OFFSET
    if value_offset + 8 > end:
        return alignment_code, None, None
    value_m = struct.unpack_from("<d", data, value_offset)[0]
    if not math.isfinite(value_m):
        return alignment_code, None, None
    return alignment_code, value_m, value_offset


def _cad_path(value: str) -> bool:
    lowered = value.lower()
    return lowered.endswith(".sldprt") or lowered.endswith(".sldasm")


def _component_path(value: str) -> bool:
    if "@" not in value or "^" in value:
        return False
    return all(
        "@" in segment and re.search(r"-\d+$", segment.split("@", 1)[0]) is not None
        for segment in value.split("/")
    )


def _record_strings(data: bytes, start: int, end: int) -> tuple[str, ...]:
    values = [
        (offset, value)
        for offset, value, _ in _serialized_strings(data, start, end)
        if value
    ]
    for match in _WIDE_TEXT.finditer(data, start, end):
        values.append((match.start(), match.group().decode("utf-16le")))
    values.sort(key=lambda item: item[0])
    result: list[str] = []
    for _, value in values:
        if not result or result[-1] != value:
            result.append(value)
    return tuple(result)


def _bounding_box(
    value: str | None,
) -> tuple[float, float, float, float, float, float] | None:
    if not value:
        return None
    return _float_tuple(value, 6)


def _float_tuple(value: str | None, count: int) -> tuple[float, ...]:
    if value is None:
        raise SldprtFormatError("required floating-point tuple is missing")
    result = tuple(float(item) for item in value.split())
    if len(result) != count or not all(math.isfinite(item) for item in result):
        raise SldprtFormatError(
            f"expected {count} finite floating-point values, found {len(result)}"
        )
    return result


def _integer(value: str | None, default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError as exc:
        raise SldprtFormatError(f"invalid integer value {value!r}") from exc


def _yes(value: str | None) -> bool:
    return value == "YES"
