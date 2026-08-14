# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from convert.adapters.base import (
    AdapterInfo,
    CarrierReason,
    CapabilityTransfer,
    Destination,
    ProbeResult,
    ReadOptions,
    Source,
    TransferMode,
    WriteOptions,
    WriteResult,
    is_binary_destination,
    is_windows_device_name,
)
from interchange import (
    BrepPayload,
    CadDocument,
    CadSource,
    Capability,
    ChamferFeature,
    ComponentDefinition,
    ComponentKind,
    Configuration,
    Diagnostic,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    FilletFeature,
    Mesh,
    PayloadRole,
    Severity,
    filter_document,
    frozen_mapping,
    infer_capabilities,
    semantic_metadata,
    source_payload_indexes,
)
from interchange.serialization import ToData

from convert.adapters.freecad.Archive import DOCUMENT_ENTRY, MANIFEST_ENTRY, NATIVE_DOCUMENT_SHA256_ATTRIBUTE, NativeBrepKey, _MAX_ENTRY_SIZE, _MAX_EXTERNAL_FILES, _MAX_TOTAL_SIZE, _native_brep_key as _manifest_native_brep_key, _validated_archive_members, _validated_document_xml, build_fcstd_archive, extract_manifest_from_fcstd, native_expression_parts, native_shape_feature_count, native_sketch_carrier_reasons, native_sketch_parts
from convert.adapters.freecad.Brep import FreeCADBrepWriteError, brep_model_brep, proven_ascii_brep
from convert.adapters.freecad.Format import CAPABILITY_CARRIER_REASONS, INFO, SUFFIX
from convert.adapters.freecad.Native import NativeFreeCADError, probe_native_fcstd, read_native_fcstd
from convert.adapters.freecad.Protocol import FEATURE_WRITE_KINDS, FREECAD_BREP_FORMAT_IDS, MATE_WRITE_KINDS, XML_TRUE_VALUES

_NATIVE_DOCUMENT_ID = "freecad:native-document"
_NATIVE_DOCUMENT_BINDING_ID = "freecad:native-document-binding"
_REPLAY_SEMANTIC_ATTRIBUTE = "freecad.replay_semantic_sha256"
_NATIVE_EXTRUSION_END_CONDITIONS = frozenset(
    {
        ExtrusionEndCondition.BLIND.value,
        ExtrusionEndCondition.TWO_LENGTHS.value,
        ExtrusionEndCondition.MID_PLANE.value,
    }
)
_FEATURE_WRITE_VALUES = frozenset(kind.value for kind in FEATURE_WRITE_KINDS)
_MATE_WRITE_VALUES = frozenset(kind.value for kind in MATE_WRITE_KINDS)


class FreeCADAdapterError(RuntimeError):
    def __init__(self, message: str) -> None:
        super().__init__(message)


def document_to_manifest(document: Any) -> dict[str, Any]:
    manifest = ToData(document)
    if not isinstance(manifest, dict):
        raise TypeError("CadDocument.to_dict() must produce a mapping")
    if manifest.get("$type") == "CadDocument":
        required = set(document.to_dict())
        missing = sorted(required.difference(manifest))
        if missing:
            raise ValueError("CadDocument manifest is missing: " + ", ".join(missing))
    return manifest


def _source_bytes(source: Source) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, bytearray):
        return bytes(source)
    if isinstance(source, (str, Path)):
        return Path(source).expanduser().resolve().read_bytes()
    reader = getattr(source, "read", None)
    if callable(reader):
        position = None
        tell = getattr(source, "tell", None)
        seek = getattr(source, "seek", None)
        if callable(tell):
            try:
                position = tell()
            except (OSError, ValueError):
                position = None
        data = reader()
        if position is not None and callable(seek):
            try:
                seek(position)
            except (OSError, ValueError):
                position = None
        if isinstance(data, str):
            raise TypeError("FCStd input must be opened in binary mode")
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
    raise TypeError("source must be a path, bytes, or binary stream")


def _destination_path(destination: Destination) -> Path | None:
    if isinstance(destination, (str, Path)):
        return Path(destination).expanduser().resolve()
    return None


def _source_path(source: Source) -> str:
    if isinstance(source, (str, Path)):
        return str(Path(source).expanduser().resolve())
    name = getattr(source, "name", "")
    return str(name) if isinstance(name, (str, Path)) else ""


def _filtered_document(document: CadDocument, settings: ReadOptions) -> CadDocument:
    filtered = filter_document(
        document,
        include_brep=settings.include_brep,
        include_tessellation=settings.include_tessellation,
        keep_payload_records=False,
    )
    metadata: Mapping[str, Any] = filtered.metadata
    freecad = metadata.get("freecad", {}) if isinstance(metadata, Mapping) else {}
    external = (
        freecad.get("external_documents", []) if isinstance(freecad, Mapping) else []
    )
    if isinstance(external, Sequence) and not isinstance(
        external, (str, bytes, bytearray)
    ):
        stripped_external: list[Any] = []
        changed = False
        for value in external:
            if not isinstance(value, Mapping):
                stripped_external.append(value)
                continue
            linked = value.get("document")
            mapped = isinstance(linked, Mapping)
            if mapped:
                try:
                    linked = CadDocument.from_dict(linked)
                except (TypeError, ValueError, RecursionError):
                    stripped_external.append(value)
                    continue
            if not isinstance(linked, CadDocument):
                stripped_external.append(value)
                continue
            item = dict(value)
            stripped = _filtered_document(linked, settings)
            item["document"] = stripped.to_dict() if mapped else stripped
            stripped_external.append(item)
            changed = True
        if changed:
            freecad_copy = dict(freecad)
            freecad_copy["external_documents"] = stripped_external
            metadata_copy = dict(metadata)
            metadata_copy["freecad"] = freecad_copy
            metadata = metadata_copy
    return replace(
        filtered,
        metadata=metadata,
    )


def _is_native_document(payload: BrepPayload) -> bool:
    return (
        payload.id == _NATIVE_DOCUMENT_ID
        and payload.format_id == INFO.format_id
        and payload.kind == "native_document"
        and payload.role == PayloadRole.DOCUMENT
    )


def _is_native_document_binding(payload: BrepPayload) -> bool:
    return (
        payload.id == _NATIVE_DOCUMENT_BINDING_ID
        and payload.format_id == f"{INFO.format_id}.sha256"
        and payload.kind == "native_document_binding"
        and payload.schema == "sha256"
        and payload.role == PayloadRole.VERIFICATION
    )


def _is_native_envelope(payload: BrepPayload) -> bool:
    return _is_native_document(payload) or _is_native_document_binding(payload)


def _native_document_pair(
    document: CadDocument,
) -> tuple[BrepPayload, BrepPayload] | None:
    documents = tuple(
        payload for payload in document.brep_payloads if _is_native_document(payload)
    )
    bindings = tuple(
        payload
        for payload in document.brep_payloads
        if _is_native_document_binding(payload)
    )
    if len(documents) != 1 or len(bindings) != 1:
        return None
    native_document = documents[0]
    binding = bindings[0]
    try:
        native_digest = bytes.fromhex(native_document.sha256)
    except ValueError:
        return None
    if len(native_digest) != hashlib.sha256().digest_size:
        return None
    if (
        native_document.data is None
        or hashlib.sha256(native_document.data).digest() != native_digest
        or binding.data != native_digest
        or binding.sha256 != hashlib.sha256(native_digest).hexdigest()
    ):
        return None
    return native_document, binding


def _mapped_external_documents(
    metadata: Mapping[str, Any],
    transform: Callable[[CadDocument], CadDocument],
) -> Mapping[str, Any]:
    freecad = metadata.get("freecad", {})
    if not isinstance(freecad, Mapping):
        return metadata
    values = freecad.get("external_documents", [])
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        return metadata
    changed = False
    mapped: list[Any] = []
    for value in values:
        if not isinstance(value, Mapping):
            mapped.append(value)
            continue
        linked = value.get("document")
        if not isinstance(linked, CadDocument):
            mapped.append(value)
            continue
        item = dict(value)
        item["document"] = transform(linked)
        mapped.append(item)
        changed = True
    if not changed:
        return metadata
    freecad_copy = dict(freecad)
    freecad_copy["external_documents"] = mapped
    result = dict(metadata)
    result["freecad"] = freecad_copy
    return frozen_mapping(result)


def _semantic_document(document: CadDocument) -> CadDocument:
    envelope_indexes = source_payload_indexes(document)
    assembly = document.assembly
    if assembly is not None:
        assembly = replace(
            assembly,
            documents=tuple(
                replace(
                    item,
                    document=(
                        _semantic_document(item.document)
                        if isinstance(item.document, CadDocument)
                        else item.document
                    ),
                )
                for item in assembly.documents
            ),
        )
    payloads = tuple(
        replace(
            payload,
            data=None,
            sha256=(
                hashlib.sha256(payload.data).hexdigest()
                if payload.data is not None
                else payload.sha256
            ),
            attributes=frozen_mapping(
                {
                    key: value
                    for key, value in payload.attributes.items()
                    if key != _REPLAY_SEMANTIC_ATTRIBUTE
                }
            ),
        )
        for index, payload in enumerate(document.brep_payloads)
        if index not in envelope_indexes and not _is_native_envelope(payload)
    )
    metadata = _mapped_external_documents(document.metadata, _semantic_document)
    return replace(
        document,
        source=CadSource("", "", ""),
        brep_payloads=payloads,
        metadata=semantic_metadata(metadata),
        assembly=assembly,
    )


def _semantic_digest(document: CadDocument) -> str:
    data = _semantic_document(document).to_json(indent=None).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _annotate_native_sources(document: CadDocument) -> CadDocument:
    assembly = document.assembly
    if assembly is not None:
        assembly = replace(
            assembly,
            documents=tuple(
                replace(
                    item,
                    document=(
                        _annotate_native_sources(item.document)
                        if isinstance(item.document, CadDocument)
                        else item.document
                    ),
                )
                for item in assembly.documents
            ),
        )
    metadata = _mapped_external_documents(document.metadata, _annotate_native_sources)
    annotated = replace(document, metadata=metadata, assembly=assembly)
    pair = _native_document_pair(annotated)
    if pair is None:
        return annotated
    native_document, _ = pair
    digest = _semantic_digest(annotated)
    payloads = tuple(
        (
            replace(
                payload,
                attributes=frozen_mapping(
                    {
                        **payload.attributes,
                        _REPLAY_SEMANTIC_ATTRIBUTE: digest,
                    }
                ),
            )
            if payload.id == native_document.id and _is_native_document(payload)
            else payload
        )
        for payload in annotated.brep_payloads
    )
    return replace(annotated, brep_payloads=payloads)


def _unchanged_native_source(document: CadDocument) -> bytes | None:
    pair = _native_document_pair(document)
    if pair is None:
        return None
    native_document, _ = pair
    expected = native_document.attributes.get(_REPLAY_SEMANTIC_ATTRIBUTE)
    if not isinstance(expected, str) or expected != _semantic_digest(document):
        return None
    data = native_document.data
    if data is None:
        return None
    try:
        archive, _ = _validated_archive_members(data)
        archive.close()
    except (OSError, ValueError, zipfile.BadZipFile):
        return None
    try:
        reparsed = read_native_fcstd(data, document.source.path)
    except (NativeFreeCADError, OSError, TypeError, ValueError):
        return None
    if _semantic_digest(reparsed) != expected:
        return None
    return data


def _enum_text(value: Any) -> str:
    return str(getattr(value, "value", value) or "").casefold()


def _document_tree(document: CadDocument) -> tuple[CadDocument, ...]:
    pending = [document]
    result: list[CadDocument] = []
    seen: set[int] = set()
    while pending:
        item = pending.pop()
        identity = id(item)
        if identity in seen:
            continue
        seen.add(identity)
        result.append(item)
        if item.assembly is not None:
            pending.extend(
                component.document
                for component in reversed(item.assembly.documents)
                if isinstance(component.document, CadDocument)
            )
    return tuple(result)


def _has_native_freecad_graph(document: CadDocument) -> bool:
    freecad = document.metadata.get("freecad", {})
    if not isinstance(freecad, Mapping):
        return False
    objects = freecad.get("objects", ())
    return (
        isinstance(objects, Sequence)
        and not isinstance(objects, (str, bytes, bytearray))
        and bool(objects)
    )


def _feature_has_native_edges(document: CadDocument, feature: Any) -> bool:
    attributes = feature.attributes
    for name in (
        "selected_native_local_edge_ids",
        "native_local_edge_ids",
        "edge_ids",
        "edges",
    ):
        values = attributes.get(name, ())
        if (
            isinstance(values, Sequence)
            and not isinstance(values, (str, bytes, bytearray))
            and any(isinstance(value, (int, float)) and value > 0 for value in values)
        ):
            return True
    selections = {selection.id: selection for selection in document.selections}
    for selection_id in feature.selection_ids:
        selection = selections.get(selection_id)
        if selection is None:
            continue
        if any(
            re.fullmatch(r"(?:Edge|edge:)(\d+)", item.subelement, re.IGNORECASE)
            for item in selection.path
        ):
            return True
        if selection.query.get("topology_role") == (
            "extrusion_terminal_profile_boundary"
        ):
            return True
        if any(
            isinstance(selection.query.get(name), (int, float))
            and selection.query[name] > 0
            for name in ("edge_index", "native_local_id", "index")
        ):
            return True
    return False


def _extrusion_is_native(feature: Any) -> bool:
    definition = feature.definition
    if not isinstance(definition, ExtrusionFeature):
        return False
    if _enum_text(definition.end_condition) not in _NATIVE_EXTRUSION_END_CONDITIONS:
        return False
    if (
        definition.second_end_condition is not None
        and _enum_text(definition.second_end_condition)
        not in _NATIVE_EXTRUSION_END_CONDITIONS
    ):
        return False
    if any(
        value is not None
        for value in (
            definition.offset,
            definition.second_offset,
            definition.draft_angle,
            definition.second_draft_angle,
        )
    ):
        return False
    if definition.up_to_reference or definition.second_up_to_reference:
        return False
    return _enum_text(feature.operation) in {
        "",
        "create",
        "join",
        "cut",
        "intersect",
    }


def _feature_parts(
    document: CadDocument,
    sketch_native: Mapping[str, bool],
    sketch_carrier_reasons: Mapping[str, CarrierReason],
) -> tuple[int, int, frozenset[CarrierReason]]:
    dependent_feature_ids = {
        feature_id
        for feature in document.feature_timeline
        for feature_id in feature.input_feature_ids
    }
    final_feature_ids = {body.final_feature_id for body in document.bodies}
    features = tuple(
        feature
        for feature in document.feature_timeline
        if _enum_text(feature.kind) != FeatureKind.IMPORTED.value
        and not (
            _enum_text(feature.kind) == FeatureKind.REFERENCE.value
            and str(feature.attributes.get("native_type", "")).casefold()
            in {"plane", "sketch"}
        )
        and not (
            _enum_text(feature.kind) == FeatureKind.NATIVE.value
            and feature.id not in dependent_feature_ids
            and feature.id not in final_feature_ids
            and not feature.input_feature_ids
            and feature.sketch_id is None
            and not feature.parameter_ids
            and not feature.selection_ids
        )
    )
    if _has_native_freecad_graph(document) and document.assembly is None:
        return len(features), 0, frozenset()
    native = 0
    carrier = 0
    reasons: set[CarrierReason] = set()
    for feature in features:
        kind = _enum_text(feature.kind)
        writable = not feature.suppressed and kind in _FEATURE_WRITE_VALUES
        if kind == FeatureKind.EXTRUSION.value:
            writable = (
                writable
                and bool(feature.sketch_id)
                and sketch_native.get(feature.sketch_id or "", False)
                and _extrusion_is_native(feature)
            )
        elif kind == FeatureKind.FILLET.value:
            writable = (
                writable
                and isinstance(feature.definition, FilletFeature)
                and not feature.definition.variable_radius_parameter_ids
                and bool(feature.input_feature_ids)
                and _feature_has_native_edges(document, feature)
            )
        elif kind == FeatureKind.CHAMFER.value:
            writable = (
                writable
                and isinstance(feature.definition, ChamferFeature)
                and feature.definition.mode == "equal_distance"
                and feature.definition.second_distance is None
                and feature.definition.angle is None
                and bool(feature.input_feature_ids)
                and _feature_has_native_edges(document, feature)
            )
        else:
            writable = False
        native += 1
        if not writable:
            carrier += 1
            feature_reasons: set[CarrierReason] = set()
            if feature.suppressed:
                feature_reasons.add(CarrierReason.TARGET_UNSUPPORTED)
            elif kind == FeatureKind.REFERENCE.value:
                feature_reasons.add(CarrierReason.TARGET_UNSUPPORTED)
            elif kind == FeatureKind.NATIVE.value:
                feature_reasons.add(CarrierReason.SOURCE_OPAQUE)
            else:
                if kind == FeatureKind.EXTRUSION.value:
                    sketch_reason = sketch_carrier_reasons.get(feature.sketch_id or "")
                    if sketch_reason is not None:
                        feature_reasons.add(sketch_reason)
                    if not feature.sketch_id or not _extrusion_is_native(feature):
                        feature_reasons.add(CarrierReason.WRITER_UNIMPLEMENTED)
                if not feature_reasons:
                    feature_reasons.add(CarrierReason.WRITER_UNIMPLEMENTED)
            reasons.update(feature_reasons)
    return native, carrier, frozenset(reasons)


def _selection_parts(document: CadDocument) -> tuple[int, int]:
    targets = {
        *(plane.id for plane in document.support_planes),
        *(sketch.id for sketch in document.sketches),
        *(feature.id for feature in document.feature_timeline),
        *(body.id for body in document.bodies),
    }
    native = 0
    carrier = 0
    for selection in document.selections:
        native_path = bool(selection.path) and all(
            item.entity_id in targets for item in selection.path
        )
        native_point = selection.point is not None
        if native_path or native_point:
            native += 1
        else:
            carrier += 1
        if selection.query:
            carrier += 1
    return native, carrier


def _configuration_parts(document: CadDocument) -> tuple[int, int]:
    native = 0
    carrier = 0
    for configuration in document.configurations:
        if (
            len(document.configurations) == 1
            and configuration.active
            and configuration.parent_id is None
            and not configuration.overrides
            and not configuration.suppressed_feature_ids
        ):
            native += 1
        else:
            carrier += 1
    return native, carrier


def _mate_parts(document: CadDocument) -> tuple[int, int]:
    assembly = document.assembly
    if assembly is None:
        return 0, 0
    entities = {entity.id: entity for entity in assembly.mate_entities}
    instance_ids = {instance.id for instance in assembly.instances}
    native = 0
    carrier = 0
    for mate in assembly.mates:
        attributes = mate.attributes
        references = attributes.get("references", ())
        has_native_references = (
            isinstance(references, Sequence)
            and not isinstance(references, (str, bytes, bytearray))
            and len(references) >= 2
        )
        linked = [entities.get(entity_id) for entity_id in mate.entity_ids[:2]]
        has_occurrence_references = len(linked) == 2 and all(
            entity is not None
            and bool(entity.instance_path)
            and all(instance_id in instance_ids for instance_id in entity.instance_path)
            for entity in linked
        )
        if _enum_text(mate.kind) in _MATE_WRITE_VALUES and (
            has_native_references or has_occurrence_references
        ):
            native += 1
        else:
            carrier += 1
    return native, carrier


def _payload_is_exact_native_brep(payload: BrepPayload) -> bool:
    data = payload.data
    provenance = payload.provenance
    attributes = payload.attributes
    freecad_object = attributes.get("freecad_object")
    freecad_object_type = attributes.get("freecad_object_type")
    freecad_property = attributes.get("freecad_property")
    native_document_sha256 = attributes.get(NATIVE_DOCUMENT_SHA256_ATTRIBUTE)
    property_data = attributes.get("freecad_property_data")
    property_attributes = (
        property_data.get("attributes", {})
        if isinstance(property_data, Mapping)
        else {}
    )
    property_children = (
        property_data.get("children", ()) if isinstance(property_data, Mapping) else ()
    )
    part_files = tuple(
        child_attributes.get("file")
        for child in property_children
        if isinstance(child, Mapping)
        and child.get("tag") == "Part"
        and isinstance((child_attributes := child.get("attributes")), Mapping)
    )
    return (
        payload.role == PayloadRole.BREP
        and data is not None
        and payload.format_id.casefold() in FREECAD_BREP_FORMAT_IDS
        and payload.kind == "shape"
        and payload.schema.startswith("CASCADE Topology V")
        and payload.sha256 == hashlib.sha256(data).hexdigest()
        and provenance is not None
        and provenance.adapter == INFO.format_id
        and provenance.confidence == 1.0
        and isinstance(freecad_object, str)
        and bool(freecad_object)
        and isinstance(freecad_object_type, str)
        and bool(freecad_object_type)
        and isinstance(freecad_property, str)
        and bool(freecad_property)
        and isinstance(native_document_sha256, str)
        and re.fullmatch(r"[0-9a-f]{64}", native_document_sha256) is not None
        and provenance.native_id == f"{freecad_object}.{freecad_property}"
        and payload.source_stream == f"{freecad_object}.{freecad_property}.brp"
        and isinstance(property_data, Mapping)
        and property_data.get("tag") == "Property"
        and property_attributes.get("name") == freecad_property
        and property_attributes.get("type") == "Part::PropertyPartShape"
        and part_files == (payload.source_stream,)
    )


def _manifest_brep_payloads(document: CadDocument) -> tuple[Mapping[str, Any], ...]:
    values = document_to_manifest(document).get("brep_payloads", ())
    if isinstance(values, Mapping):
        values = values.get("$tuple", ())
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        return ()
    result = tuple(value for value in values if isinstance(value, Mapping))
    return result if len(result) == len(document.brep_payloads) else ()


def _native_document_sha256(document: CadDocument) -> str:
    pair = _native_document_pair(document)
    if pair is not None and pair[0].data is not None:
        return hashlib.sha256(pair[0].data).hexdigest()
    values = {
        value
        for payload in document.brep_payloads
        if isinstance(
            (value := payload.attributes.get(NATIVE_DOCUMENT_SHA256_ATTRIBUTE)),
            str,
        )
        and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    }
    return next(iter(values)) if len(values) == 1 else ""


def _xml_element_data(node: ET.Element) -> dict[str, Any]:
    result: dict[str, Any] = {
        "tag": node.tag,
        "attributes": dict(sorted(node.attrib.items())),
    }
    text = (node.text or "").strip()
    if text:
        result["text"] = text
    children = [_xml_element_data(child) for child in node]
    if children:
        result["children"] = children
    return result


def _archive_member_data(
    archive: zipfile.ZipFile,
    members: Mapping[str, zipfile.ZipInfo],
    name: str,
) -> bytes | None:
    info = members.get(name)
    if info is None or info.is_dir():
        return None
    try:
        return archive.read(info)
    except (OSError, RuntimeError, NotImplementedError, zipfile.BadZipFile):
        return None


def _payload_matches_native_archive(
    payload: BrepPayload,
    archive: zipfile.ZipFile,
    members: Mapping[str, zipfile.ZipInfo],
    root: ET.Element,
    native_document_sha256: str,
) -> bool:
    if not _payload_is_exact_native_brep(payload) or payload.data is None:
        return False
    if _archive_member_data(archive, members, payload.source_stream) != payload.data:
        return False
    attributes = payload.attributes
    if attributes[NATIVE_DOCUMENT_SHA256_ATTRIBUTE] != native_document_sha256:
        return False
    object_name = str(attributes["freecad_object"])
    object_type = str(attributes["freecad_object_type"])
    property_name = str(attributes["freecad_property"])
    declarations = tuple(
        value
        for value in root.findall("./Objects/Object")
        if value.get("name") == object_name and value.get("type") == object_type
    )
    objects = tuple(
        value
        for value in root.findall("./ObjectData/Object")
        if value.get("name") == object_name
    )
    if len(declarations) != 1 or len(objects) != 1:
        return False
    properties = tuple(
        value
        for value in objects[0].findall("./Properties/Property")
        if value.get("name") == property_name
    )
    if len(properties) != 1:
        return False
    property_element = properties[0]
    if _xml_element_data(property_element) != attributes["freecad_property_data"]:
        return False
    referenced_sidecars = tuple(
        name
        for child in property_element.findall(".//*[@file]")
        if (name := child.get("file", "")) and name != payload.source_stream
    )
    sidecars = attributes.get("freecad_sidecars", ())
    if not isinstance(sidecars, Sequence) or isinstance(
        sidecars, (str, bytes, bytearray)
    ):
        return False
    if len(sidecars) != len(referenced_sidecars):
        return False
    for sidecar, source_stream in zip(sidecars, referenced_sidecars, strict=True):
        if not isinstance(sidecar, Mapping):
            return False
        sidecar_data = sidecar.get("data")
        if (
            sidecar.get("source_stream") != source_stream
            or not isinstance(sidecar_data, bytes)
            or _archive_member_data(archive, members, source_stream) != sidecar_data
        ):
            return False
    return True


def _trusted_native_breps(
    document: CadDocument,
) -> frozenset[NativeBrepKey]:
    trusted: set[NativeBrepKey] = set()
    for item in _document_tree(document):
        native_source = _unchanged_native_source(item)
        mapped_payloads = _manifest_brep_payloads(item)
        if native_source is None or not mapped_payloads:
            continue
        try:
            archive, members = _validated_archive_members(native_source)
            root, _ = _validated_document_xml(archive, members)
        except (OSError, TypeError, ValueError, zipfile.BadZipFile):
            continue
        try:
            native_document_sha256 = hashlib.sha256(native_source).hexdigest()
            for payload, mapped in zip(
                item.brep_payloads,
                mapped_payloads,
                strict=True,
            ):
                if not _payload_matches_native_archive(
                    payload,
                    archive,
                    members,
                    root,
                    native_document_sha256,
                ):
                    continue
                if payload.data is None:
                    continue
                key = _manifest_native_brep_key(
                    mapped,
                    payload.data,
                    native_document_sha256,
                )
                if key is not None:
                    trusted.add(key)
        finally:
            archive.close()
    return frozenset(trusted)


def _payload_native_brep(
    payload: BrepPayload,
    mapped_payload: Mapping[str, Any] | None = None,
    native_document_sha256: str = "",
    trusted_native_breps: frozenset[NativeBrepKey] = frozenset(),
) -> bytes | None:
    if not (
        payload.role == PayloadRole.BREP
        and payload.data is not None
        and payload.format_id.casefold() in FREECAD_BREP_FORMAT_IDS
    ):
        return None
    if mapped_payload is not None:
        key = _manifest_native_brep_key(
            mapped_payload,
            payload.data,
            native_document_sha256,
        )
        if key in trusted_native_breps:
            return payload.data
    return proven_ascii_brep(payload.data)


def _payload_is_reattachable_brep(
    payload: BrepPayload,
    mapped_payload: Mapping[str, Any] | None = None,
    native_document_sha256: str = "",
    trusted_native_breps: frozenset[NativeBrepKey] = frozenset(),
) -> bool:
    return (
        _payload_native_brep(
            payload,
            mapped_payload,
            native_document_sha256,
            trusted_native_breps,
        )
        is not None
    )


def _neutral_brep_is_native(document: CadDocument) -> bool:
    if document.brep is None:
        return False
    try:
        brep_model_brep(document.brep)
    except FreeCADBrepWriteError:
        return False
    return True


def _mesh_is_usable(mesh: Mesh) -> bool:
    points = tuple((value.x, value.y, value.z) for value in mesh.vertices)
    if not points or any(not all(map(math.isfinite, point)) for point in points):
        return False
    for triangle in mesh.triangles:
        if len(set(triangle)) != 3 or any(
            index < 0 or index >= len(points) for index in triangle
        ):
            continue
        first, second, third = (points[index] for index in triangle)
        left = tuple(second[index] - first[index] for index in range(3))
        right = tuple(third[index] - first[index] for index in range(3))
        cross = (
            left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0],
        )
        if sum(value * value for value in cross) > 1e-24:
            return True
    return False


def _native_geometry_is_usable(
    document: CadDocument,
    trusted_native_breps: frozenset[NativeBrepKey] = frozenset(),
) -> bool:
    items = [document]
    if document.assembly is not None:
        documents = {
            item.id: item.document
            for item in document.assembly.documents
            if isinstance(item.document, CadDocument)
        }
        for definition in document.assembly.definitions:
            if definition.id == document.assembly.root_definition_id:
                continue
            component = _component_document(document, definition, documents)
            if component is not None:
                items.append(component)
    for item in items:
        if item.assembly is not None:
            continue
        mapped_payloads = _manifest_brep_payloads(item)
        mapped_by_identity = (
            {
                id(payload): mapped
                for payload, mapped in zip(
                    item.brep_payloads,
                    mapped_payloads,
                    strict=True,
                )
            }
            if mapped_payloads
            else {}
        )
        native_document_sha256 = _native_document_sha256(item)
        raw_breps = tuple(
            payload
            for payload in item.brep_payloads
            if payload.role == PayloadRole.BREP and payload.data is not None
        )
        if item.brep is None and not raw_breps:
            continue
        if item.brep is not None and _neutral_brep_is_native(item):
            continue
        if any(
            _payload_is_reattachable_brep(
                payload,
                mapped_by_identity.get(id(payload)),
                native_document_sha256,
                trusted_native_breps,
            )
            for payload in raw_breps
        ):
            continue
        if any(_mesh_is_usable(mesh) for mesh in item.meshes):
            continue
        if (
            item.source.format_id.casefold() != INFO.format_id.casefold()
            and native_shape_feature_count(document_to_manifest(item)) > 0
        ):
            continue
        return False
    return True


def _transfer_mode(parts: Sequence[bool]) -> TransferMode:
    if parts and all(parts):
        return TransferMode.NATIVE
    if any(parts):
        return TransferMode.MIXED
    return TransferMode.CARRIER


def _carrier_reason(
    capability: Capability,
    reasons: Mapping[Capability, set[CarrierReason]],
) -> CarrierReason:
    values = reasons[capability]
    for reason in (
        CarrierReason.SOURCE_OPAQUE,
        CarrierReason.WRITER_UNIMPLEMENTED,
        CarrierReason.TARGET_UNSUPPORTED,
    ):
        if reason in values:
            return reason
    return CAPABILITY_CARRIER_REASONS[capability]


def _capability_transfers(
    document: CadDocument,
    destination_path: Path | None,
    portable: bool,
    exact: bool,
    trusted_native_breps: frozenset[NativeBrepKey] = frozenset(),
) -> tuple[CapabilityTransfer, ...]:
    required = document.capabilities | infer_capabilities(
        document,
        roundtrip_metadata=(Capability.ROUNDTRIP_METADATA in document.capabilities),
    )
    if exact:
        return tuple(
            CapabilityTransfer(capability, TransferMode.NATIVE)
            for capability in sorted(required, key=lambda value: value.value)
        )
    parts = {capability: [] for capability in Capability}
    carrier_reasons = {capability: set() for capability in Capability}
    for item in _document_tree(document):
        source_native = _has_native_freecad_graph(item)
        manifest = document_to_manifest(item)
        mapped_payloads = _manifest_brep_payloads(item)
        mapped_by_identity = (
            {
                id(payload): mapped
                for payload, mapped in zip(
                    item.brep_payloads,
                    mapped_payloads,
                    strict=True,
                )
            }
            if mapped_payloads
            else {}
        )
        native_document_sha256 = _native_document_sha256(item)
        sketch_parts = native_sketch_parts(manifest)
        sketch_reason_parts = native_sketch_carrier_reasons(manifest)
        sketch_native: dict[str, bool] = {}
        sketch_carrier_reasons: dict[str, CarrierReason] = {}
        for sketch, (native_count, carrier_count), reason_values in zip(
            item.sketches, sketch_parts, sketch_reason_parts, strict=True
        ):
            parts[Capability.EDITABLE_SKETCHES].extend(
                [True] * native_count + [False] * carrier_count
            )
            if carrier_count:
                sketch_reasons = {CarrierReason(value) for value in reason_values} or {
                    CarrierReason.WRITER_UNIMPLEMENTED
                }
                sketch_reason = next(
                    reason
                    for reason in (
                        CarrierReason.SOURCE_OPAQUE,
                        CarrierReason.WRITER_UNIMPLEMENTED,
                        CarrierReason.TARGET_UNSUPPORTED,
                    )
                    if reason in sketch_reasons
                )
                sketch_carrier_reasons[sketch.id] = sketch_reason
                carrier_reasons[Capability.EDITABLE_SKETCHES].update(sketch_reasons)
            sketch_native[sketch.id] = carrier_count == 0
        parts[Capability.PARAMETERS].extend(True for _ in item.parameters)
        feature_native, feature_carrier, feature_reasons = _feature_parts(
            item, sketch_native, sketch_carrier_reasons
        )
        parts[Capability.PARAMETRIC_HISTORY].extend(
            [True] * feature_native + [False] * feature_carrier
        )
        carrier_reasons[Capability.PARAMETRIC_HISTORY].update(feature_reasons)
        parts[Capability.SUPPORT_PLANES].extend(True for _ in item.support_planes)
        if source_native:
            parts[Capability.SELECTIONS].extend(True for _ in item.selections)
        else:
            native_selections, carrier_selections = _selection_parts(item)
            parts[Capability.SELECTIONS].extend(
                [True] * native_selections + [False] * carrier_selections
            )
        parts[Capability.BODY_STRUCTURE].extend(True for _ in item.bodies)
        native_configurations, carrier_configurations = _configuration_parts(item)
        parts[Capability.CONFIGURATIONS].extend(
            [True] * native_configurations + [False] * carrier_configurations
        )
        if source_native:
            expression_count = sum(
                parameter.expression is not None for parameter in item.parameters
            )
            native_expressions, carrier_expressions = expression_count, 0
        else:
            native_expressions, carrier_expressions = native_expression_parts(manifest)
        parts[Capability.EXPRESSIONS].extend(
            [True] * native_expressions + [False] * carrier_expressions
        )
        raw_breps = [
            _payload_is_reattachable_brep(
                payload,
                mapped_by_identity.get(id(payload)),
                native_document_sha256,
                trusted_native_breps,
            )
            for payload in item.brep_payloads
            if payload.role == PayloadRole.BREP and payload.data is not None
        ]
        if item.brep is not None:
            native_brep = _neutral_brep_is_native(item) or any(raw_breps)
            parts[Capability.BREP].append(native_brep)
            if not native_brep:
                carrier_reasons[Capability.BREP].add(CarrierReason.WRITER_UNIMPLEMENTED)
        else:
            parts[Capability.BREP].extend(raw_breps)
            if any(not value for value in raw_breps):
                carrier_reasons[Capability.BREP].add(CarrierReason.SOURCE_OPAQUE)
        rebuilt_shape_features = (
            native_shape_feature_count(manifest)
            if item.source.format_id.casefold() != INFO.format_id.casefold()
            else 0
        )
        if rebuilt_shape_features and not all(parts[Capability.BREP]):
            parts[Capability.BREP].extend(True for _ in range(rebuilt_shape_features))
        parts[Capability.TESSELLATION].extend(True for _ in item.meshes)
        parts[Capability.TESSELLATION].extend(
            False
            for payload in item.brep_payloads
            if payload.role == PayloadRole.TESSELLATION and payload.data is not None
        )
        if item.assembly is not None:
            parts[Capability.ASSEMBLIES].append(True)
            native_mates, carrier_mates = _mate_parts(item)
            parts[Capability.ASSEMBLY_MATES].extend(
                [True] * native_mates + [False] * carrier_mates
            )
            native_documents = destination_path is not None
            parts[Capability.COMPONENT_DOCUMENTS].extend(
                native_documents for _ in item.assembly.documents
            )
            native_external = destination_path is not None and portable
            parts[Capability.EXTERNAL_REFERENCES].extend(
                native_external
                for definition in item.assembly.definitions
                if definition.source_path
            )
        parts[Capability.EXTERNAL_REFERENCES].extend(
            destination_path is not None and portable
            for _ in _native_external_documents(item)
        )
        parts[Capability.MATERIALS].extend(
            True for body in item.bodies if body.material_id
        )
        envelope_indexes = source_payload_indexes(item)
        for index, payload in enumerate(item.brep_payloads):
            if index in envelope_indexes:
                continue
            native_payload = _payload_native_brep(
                payload,
                mapped_by_identity.get(id(payload)),
                native_document_sha256,
                trusted_native_breps,
            )
            if native_payload is not None:
                parts[Capability.NATIVE_PAYLOADS].append(True)
                if native_payload != payload.data:
                    parts[Capability.NATIVE_PAYLOADS].append(False)
                    carrier_reasons[Capability.NATIVE_PAYLOADS].add(
                        CarrierReason.WRITER_UNIMPLEMENTED
                    )
                continue
            parts[Capability.NATIVE_PAYLOADS].append(False)
            carrier_reasons[Capability.NATIVE_PAYLOADS].add(
                (
                    CarrierReason.TARGET_UNSUPPORTED
                    if payload.role == PayloadRole.BREP and item.brep is not None
                    else CarrierReason.SOURCE_OPAQUE
                )
            )
        provenance_values = (
            *item.parameters,
            *item.support_planes,
            *item.sketches,
            *item.selections,
            *item.feature_timeline,
            *item.bodies,
            *item.meshes,
            *item.brep_payloads,
        )
        parts[Capability.PROVENANCE].extend(
            False for value in provenance_values if value.provenance is not None
        )
    parts[Capability.ROUNDTRIP_METADATA].append(False)
    return tuple(
        CapabilityTransfer(
            capability,
            (mode := _transfer_mode(parts[capability])),
            (
                None
                if mode is TransferMode.NATIVE
                else _carrier_reason(capability, carrier_reasons)
            ),
        )
        for capability in sorted(required, key=lambda value: value.value)
    )


def _write_bytes(destination: Destination, data: bytes, overwrite: bool) -> Path | None:
    path = _destination_path(destination)
    if path is None:
        writer = getattr(destination, "write", None)
        if not callable(writer):
            raise TypeError("destination must be a path or binary stream")
        try:
            written = writer(data)
        except TypeError as exc:
            raise TypeError("FCStd destination must be opened in binary mode") from exc
        if written is not None and written != len(data):
            raise OSError(
                f"short FCStd write: expected {len(data)} bytes, wrote {written}"
            )
        return None
    if path.suffix.casefold() != SUFFIX.casefold():
        raise ValueError(f"FreeCAD destination must end in {SUFFIX}")
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise
    return path


def _component_stem(value: str) -> str:
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip(" .")
    stem = stem or "Component"
    if is_windows_device_name(stem):
        stem = f"_{stem}"
    return stem[:120].rstrip(" .") or "Component"


def _component_paths(document: CadDocument, destination: Path) -> dict[str, Path]:
    assembly = document.assembly
    if assembly is None:
        return {}
    documents = {item.id for item in assembly.documents}
    directory = destination.parent / destination.stem
    used: set[str] = set()
    result: dict[str, Path] = {}
    for definition in assembly.definitions:
        if definition.id == assembly.root_definition_id:
            continue
        if definition.document_id not in documents and not definition.mesh_ids:
            continue
        base = _component_stem(definition.name or definition.id)
        candidate = base
        suffix = 1
        while candidate.casefold() in used:
            suffix += 1
            ending = f"_{suffix}"
            candidate = base[: 120 - len(ending)].rstrip(" .") + ending
        used.add(candidate.casefold())
        result[definition.id] = directory / f"{candidate}{SUFFIX}"
    return result


def _selected_meshes(
    document: CadDocument, definition: ComponentDefinition
) -> tuple[Mesh, ...]:
    meshes = {item.id: item for item in document.meshes}
    missing = [mesh_id for mesh_id in definition.mesh_ids if mesh_id not in meshes]
    if missing:
        raise FreeCADAdapterError(
            f"component definition {definition.id!r} references missing meshes: "
            + ", ".join(missing)
        )
    return tuple(meshes[mesh_id] for mesh_id in definition.mesh_ids)


def _mesh_component_document(
    document: CadDocument,
    definition: ComponentDefinition,
    meshes: tuple[Mesh, ...],
) -> CadDocument:
    source = CadSource(
        format_id=definition.source_format_id or document.source.format_id,
        path=definition.source_path or definition.name or definition.id,
        sha256=definition.source_sha256,
        container_version=document.source.container_version,
        application_version=document.source.application_version,
        attributes=definition.attributes,
    )
    configuration_name = definition.configuration_name or "Default"
    configuration_id = (
        definition.configuration_id or f"{definition.id}:configuration:default"
    )
    return CadDocument(
        source=source,
        configurations=(
            Configuration(configuration_id, configuration_name, active=True),
        ),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        meshes=meshes,
        capabilities=frozenset({Capability.TESSELLATION}),
        units=document.units,
        schema_version=document.schema_version,
    )


def _component_document(
    document: CadDocument,
    definition: ComponentDefinition,
    documents: Mapping[str, CadDocument],
) -> CadDocument | None:
    selected_meshes = _selected_meshes(document, definition)
    linked = documents.get(definition.document_id)
    if linked is None:
        return (
            _mesh_component_document(document, definition, selected_meshes)
            if selected_meshes
            else None
        )
    selected_ids = {mesh.id for mesh in selected_meshes}
    meshes = (
        *selected_meshes,
        *(mesh for mesh in linked.meshes if mesh.id not in selected_ids),
    )
    capabilities = linked.capabilities
    if meshes:
        capabilities = capabilities | {Capability.TESSELLATION}
    return replace(linked, meshes=meshes, capabilities=capabilities)


def _xml_string(node: ET.Element, name: str, default: str = "") -> str:
    value = node.find(f"./Properties/Property[@name='{name}']/String")
    return default if value is None else value.get("value", default)


def _xml_bool(node: ET.Element, name: str, default: bool = False) -> bool:
    value = node.find(f"./Properties/Property[@name='{name}']/Bool")
    if value is None:
        return default
    return value.get("value", "false").casefold() in XML_TRUE_VALUES


def _xml_string_list(node: ET.Element, name: str) -> list[str]:
    return [
        value.get("value", "")
        for value in node.findall(
            f"./Properties/Property[@name='{name}']/StringList/String"
        )
    ]


def _xml_link_list(node: ET.Element, name: str) -> list[str]:
    return [
        value.get("value", "")
        for value in node.findall(
            f"./Properties/Property[@name='{name}']/LinkList/Link"
        )
    ]


def _xml_number(value: str | None, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _xml_transform(node: ET.Element) -> list[float]:
    value = node.find("./Properties/Property[@name='Placement']/PropertyPlacement")
    if value is None:
        return [
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]
    x = _xml_number(value.get("Q0"), 0.0)
    y = _xml_number(value.get("Q1"), 0.0)
    z = _xml_number(value.get("Q2"), 0.0)
    w = _xml_number(value.get("Q3"), 1.0)
    norm = (x * x + y * y + z * z + w * w) ** 0.5
    if norm <= 1e-15:
        x, y, z, w = 0.0, 0.0, 0.0, 1.0
    else:
        x, y, z, w = x / norm, y / norm, z / norm, w / norm
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    xw, yw, zw = x * w, y * w, z * w
    return [
        1.0 - 2.0 * (yy + zz),
        2.0 * (xy - zw),
        2.0 * (xz + yw),
        _xml_number(value.get("Px"), 0.0),
        2.0 * (xy + zw),
        1.0 - 2.0 * (xx + zz),
        2.0 * (yz - xw),
        _xml_number(value.get("Py"), 0.0),
        2.0 * (xz - yw),
        2.0 * (yz + xw),
        1.0 - 2.0 * (xx + yy),
        _xml_number(value.get("Pz"), 0.0),
        0.0,
        0.0,
        0.0,
        1.0,
    ]


def _xml_scale(node: ET.Element) -> list[float]:
    value = node.find("./Properties/Property[@name='ScaleVector']/PropertyVector")
    if value is None:
        return [1.0, 1.0, 1.0]
    return [
        _xml_number(value.get("valueX"), 1.0),
        _xml_number(value.get("valueY"), 1.0),
        _xml_number(value.get("valueZ"), 1.0),
    ]


def _external_link_details(data: bytes) -> tuple[str, list[dict[str, Any]]]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        root = ET.fromstring(archive.read(DOCUMENT_ENTRY))
    value = root.find(
        "./ObjectData/Object[@name='KitMetadata']/Properties/"
        "Property[@name='ExternalLinkTarget']/String"
    )
    target = "" if value is None else value.get("value", "")
    if not target:
        raise FreeCADAdapterError("component FCStd has no external link target")
    types = {
        item.get("name", ""): item.get("type", "")
        for item in root.findall("./Objects/Object")
    }
    objects = {
        item.get("name", ""): item for item in root.findall("./ObjectData/Object")
    }

    def occurrence(name: str, active: frozenset[str]) -> dict[str, Any] | None:
        node = objects.get(name)
        type_id = types.get(name, "")
        if (
            node is None
            or name in active
            or node.find("./Properties/Property[@name='LinkedObject']/XLink") is None
        ):
            return None
        instance_id = _xml_string(node, "InstanceId")
        if not instance_id:
            return None
        link_fields = tuple(
            sorted(
                property_element.get("name", "")
                for property_element in node.findall("./Properties/Property")
                if property_element.get("name", "")
            )
        )
        raw_instance_data = _xml_string(node, "InstanceDataJSON")
        instance_data: Any = {}
        if raw_instance_data:
            try:
                instance_data = json.loads(raw_instance_data)
            except json.JSONDecodeError:
                instance_data = {}
        children = [
            child
            for child_name in _xml_link_list(node, "Group")
            if (child := occurrence(child_name, active | {name})) is not None
        ]
        return {
            "target": name,
            "type_id": type_id,
            "link_fields": link_fields,
            "label": _xml_string(node, "Label", name),
            "instance_id": instance_id,
            "definition_id": _xml_string(node, "DefinitionId"),
            "owner_definition_id": _xml_string(node, "OwnerDefinitionId"),
            "instance_path": _xml_string_list(node, "InstancePath"),
            "reference_number": _xml_string(node, "ReferenceNumber"),
            "configuration_name": _xml_string(node, "ConfigurationName"),
            "configuration_id": _xml_string(node, "ConfigurationId"),
            "suppressed": _xml_bool(node, "Suppressed"),
            "hidden": _xml_bool(node, "Hidden"),
            "fixed": _xml_bool(node, "Fixed"),
            "flexible": _xml_bool(node, "Flexible"),
            "exclude_from_bom": _xml_bool(node, "ExcludeFromBOM"),
            "visibility": _xml_bool(node, "Visibility", True),
            "rigid": _xml_bool(node, "Rigid", True),
            "transform": _xml_transform(node),
            "scale": _xml_scale(node),
            "instance_data": instance_data,
            "occurrences": children,
        }

    target_node = objects.get(target)
    occurrences = (
        [
            item
            for child_name in _xml_link_list(target_node, "Group")
            if (item := occurrence(child_name, frozenset())) is not None
        ]
        if target_node is not None
        else []
    )
    return target, occurrences


def _external_link_target(data: bytes) -> str:
    return _external_link_details(data)[0]


def _parsed_timestamp(value: str) -> float | None:
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return None
    return parsed.timestamp()


def _existing_timestamps(path: Path) -> tuple[float, ...]:
    values: list[float] = []
    try:
        values.append(path.stat().st_mtime)
    except OSError:
        return ()
    try:
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("Document.xml"))
    except (OSError, KeyError, ET.ParseError, zipfile.BadZipFile):
        return tuple(values)
    for property_name in ("CreationDate", "LastModifiedDate"):
        element = root.find(f"./Properties/Property[@name='{property_name}']/String")
        parsed = _parsed_timestamp("" if element is None else element.get("value", ""))
        if parsed is not None:
            values.append(parsed)
    for element in root.findall(".//XLink"):
        parsed = _parsed_timestamp(element.get("stamp", ""))
        if parsed is not None:
            values.append(parsed)
    return tuple(values)


def _bundle_timestamp(destination: Path) -> tuple[str, float]:
    now = datetime.now(timezone.utc).replace(microsecond=0).timestamp()
    files = [destination]
    directory = destination.parent / destination.stem
    if directory.is_dir():
        try:
            component_files = tuple(
                path
                for path in directory.iterdir()
                if path.is_file() and path.suffix.casefold() == SUFFIX.casefold()
            )
        except OSError:
            component_files = ()
        files.extend(component_files)
    existing = [timestamp for path in files for timestamp in _existing_timestamps(path)]
    epoch = int(now)
    if existing:
        epoch = max(epoch, int(max(existing)) + 1)
    modified = datetime.fromtimestamp(epoch, timezone.utc)
    return modified.strftime("%Y-%m-%dT%H:%M:%SZ"), float(epoch)


def _definition_sources(
    definition: ComponentDefinition, documents: Mapping[str, CadDocument]
) -> frozenset[tuple[str, str, str]]:
    configuration = definition.configuration_id or definition.configuration_name
    scope = f"{definition.kind.value}:{configuration}"
    values: set[tuple[str, str, str]] = set()

    def add(sha256: str, path: str) -> None:
        if sha256:
            values.add(("sha256", sha256.casefold(), scope))
        if path:
            normalized = os.path.normpath(path).replace("\\", "/").casefold()
            segments = [value for value in normalized.split("/") if value]
            values.add(("path", normalized, scope))
            values.add(("path-tail", "/".join(segments[-2:]), scope))

    add(definition.source_sha256, definition.source_path)
    if definition.name:
        values.add(("name", definition.name.casefold(), scope))
    linked = documents.get(definition.document_id)
    if linked is not None:
        add(linked.source.sha256, linked.source.path)
    return frozenset(values)


def _matching_component_link(
    definition: ComponentDefinition,
    documents: Mapping[str, CadDocument],
    root_definitions: Mapping[str, ComponentDefinition],
    root_documents: Mapping[str, CadDocument],
    links: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    sources = _definition_sources(definition, documents)
    if not sources:
        return None
    matches = [
        link
        for definition_id, link in links.items()
        if sources
        & _definition_sources(root_definitions[definition_id], root_documents)
    ]
    identities = {
        (
            str(link.get("path", "")),
            str(link.get("target", "")),
            str(link.get("stamp", "")),
        )
        for link in matches
    }
    return matches[0] if len(identities) == 1 else None


def _nested_external_links(
    component: CadDocument,
    component_path: Path,
    root_definitions: Mapping[str, ComponentDefinition],
    root_documents: Mapping[str, CadDocument],
    links: Mapping[str, Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    assembly = component.assembly
    if assembly is None:
        return {}
    documents = {
        item.id: item.document
        for item in assembly.documents
        if isinstance(item.document, CadDocument)
    }
    result: dict[str, dict[str, Any]] = {}
    for definition in assembly.definitions:
        if definition.id == assembly.root_definition_id:
            continue
        link = _matching_component_link(
            definition,
            documents,
            root_definitions,
            root_documents,
            links,
        )
        if link is None:
            continue
        path = Path(link["path"])
        result[definition.id] = {
            "file": Path(os.path.relpath(path, component_path.parent)).as_posix(),
            "stamp": str(link.get("stamp", "")),
            "target": str(link.get("target", "")),
            "occurrences": list(link.get("occurrences", [])),
        }
    return result


def _write_components(
    document: CadDocument,
    destination: Path,
    overwrite: bool,
    validate: bool,
    document_timestamp: str,
    timestamp_epoch: float,
    trusted_native_breps: frozenset[NativeBrepKey] = frozenset(),
) -> tuple[dict[str, dict[str, Any]], int]:
    assembly = document.assembly
    if assembly is None:
        return {}, 0
    paths = _component_paths(document, destination)
    if not overwrite:
        existing = next((path for path in paths.values() if path.exists()), None)
        if existing is not None:
            raise FileExistsError(existing)
    documents = {
        item.id: item.document
        for item in assembly.documents
        if isinstance(item.document, CadDocument)
    }
    definitions = {item.id: item for item in assembly.definitions}
    plans: list[tuple[str, Path, ComponentDefinition, CadDocument]] = []
    for definition_id, path in paths.items():
        definition = definitions[definition_id]
        component = _component_document(document, definition, documents)
        if component is not None:
            plans.append((definition_id, path, definition, component))
    plans.sort(key=lambda item: item[2].kind == ComponentKind.ASSEMBLY)
    component_links: dict[str, dict[str, Any]] = {}
    external_links: dict[str, dict[str, Any]] = {}
    bytes_written = 0
    for definition_id, path, definition, component in plans:
        if validate:
            component.assert_valid()
        nested_links = (
            _nested_external_links(
                component,
                path,
                definitions,
                documents,
                component_links,
            )
            if definition.kind == ComponentKind.ASSEMBLY
            else {}
        )
        data = build_fcstd_archive(
            document_to_manifest(component),
            external_links=nested_links,
            document_timestamp=document_timestamp,
            trusted_native_breps=trusted_native_breps,
        )
        target, occurrences = _external_link_details(data)
        _write_bytes(path, data, overwrite)
        os.utime(path, (timestamp_epoch, timestamp_epoch))
        component_links[definition_id] = {
            "path": path,
            "stamp": document_timestamp,
            "target": target,
            "occurrences": occurrences,
        }
        external_links[definition_id] = {
            "file": path.relative_to(destination.parent).as_posix(),
            "stamp": document_timestamp,
            "target": target,
            "occurrences": occurrences,
        }
        bytes_written += len(data)
    return external_links, bytes_written


def _native_external_documents(document: CadDocument) -> list[tuple[str, CadDocument]]:
    metadata = document.metadata
    freecad = metadata.get("freecad", {}) if isinstance(metadata, Mapping) else {}
    values = (
        freecad.get("external_documents", []) if isinstance(freecad, Mapping) else []
    )
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
        raise FreeCADAdapterError(
            "native FreeCAD external document metadata is invalid"
        )
    result: list[tuple[str, CadDocument]] = []
    seen: set[str] = set()
    total = 0
    for value in values:
        if not isinstance(value, Mapping):
            raise FreeCADAdapterError(
                "native FreeCAD external document metadata is invalid"
            )
        source_file = str(value.get("file", ""))
        linked = value.get("document")
        if isinstance(linked, Mapping):
            try:
                linked = CadDocument.from_dict(linked)
            except (TypeError, ValueError, RecursionError) as exc:
                raise FreeCADAdapterError(
                    "native FreeCAD external document metadata is invalid"
                ) from exc
        if not source_file or not isinstance(linked, CadDocument):
            raise FreeCADAdapterError(
                "native FreeCAD external document metadata is invalid"
            )
        if source_file in seen:
            raise FreeCADAdapterError(
                "native FreeCAD external document metadata contains duplicates"
            )
        seen.add(source_file)
        native_payload_size = sum(
            len(payload.data)
            for payload in linked.brep_payloads
            if payload.role == PayloadRole.DOCUMENT and payload.data is not None
        )
        total += native_payload_size
        if len(result) >= _MAX_EXTERNAL_FILES or total > _MAX_TOTAL_SIZE:
            raise FreeCADAdapterError(
                "native FreeCAD external documents exceed safe limits"
            )
        result.append((source_file, linked))
    return result


def _write_native_external_documents(
    document: CadDocument,
    destination: Path,
    overwrite: bool,
    validate: bool,
) -> tuple[dict[str, str], int]:
    records = _native_external_documents(document)
    directory = destination.parent / destination.stem
    used: set[str] = set()
    links: dict[str, str] = {}
    bytes_written = 0
    for source_file, linked in records:
        source_name = Path(source_file).name
        suffix = Path(source_name).suffix or SUFFIX
        base = _component_stem(Path(source_name).stem)
        candidate = base
        index = 1
        while (candidate + suffix).casefold() in used:
            index += 1
            ending = f"_{index}"
            candidate = base[: 120 - len(ending)].rstrip(" .") + ending
        filename = candidate + suffix
        used.add(filename.casefold())
        output = directory / filename
        result = FreeCADAdapter().write(
            linked,
            output,
            WriteOptions(
                overwrite=overwrite,
                validate=validate,
                values={"portable": True},
            ),
        )
        if result.bytes_written > _MAX_ENTRY_SIZE:
            raise FreeCADAdapterError(
                "native FreeCAD external document exceeds safe limits"
            )
        bytes_written += result.bytes_written
        if bytes_written > _MAX_TOTAL_SIZE:
            raise FreeCADAdapterError(
                "native FreeCAD external documents exceed safe limits"
            )
        links[source_file] = output.relative_to(destination.parent).as_posix()
    return links, bytes_written


def _manifest_document(value: Mapping[str, Any]) -> CadDocument:
    try:
        return CadDocument.from_dict(value)
    except (TypeError, ValueError, RecursionError) as exc:
        raise FreeCADAdapterError(
            "embedded neutral document cannot be restored"
        ) from exc


def _selected_configurations(
    configurations: tuple[Configuration, ...], selected: str | None
) -> tuple[Configuration, ...]:
    if selected is None:
        return configurations
    matches = {
        configuration.id
        for configuration in configurations
        if selected in {configuration.id, configuration.name}
    }
    if not matches:
        raise FreeCADAdapterError(f"configuration {selected!r} is unavailable")
    return tuple(
        replace(configuration, active=configuration.id in matches)
        for configuration in configurations
    )


class FreeCADAdapter:
    @property
    def info(self) -> AdapterInfo:
        return INFO

    def probe(self, source: Source) -> ProbeResult:
        try:
            data = _source_bytes(source)
            archive, members = _validated_archive_members(data)
            archive.close()
            if MANIFEST_ENTRY in members:
                try:
                    value = extract_manifest_from_fcstd(data)
                    _manifest_document(value)
                except (ValueError, FreeCADAdapterError) as exc:
                    return ProbeResult(self.info.format_id, 0.0, str(exc))
                return ProbeResult(self.info.format_id, 1.0, "Kit FCStd archive")
            if "Document.xml" in members:
                try:
                    value = extract_manifest_from_fcstd(data)
                except ValueError as exc:
                    if (
                        str(exc)
                        != "FCStd archive has no embedded Kit interchange document"
                    ):
                        return ProbeResult(self.info.format_id, 0.0, str(exc))
                else:
                    try:
                        _manifest_document(value)
                    except FreeCADAdapterError as exc:
                        return ProbeResult(self.info.format_id, 0.0, str(exc))
                    return ProbeResult(self.info.format_id, 1.0, "Kit FCStd archive")
                confidence, reason = probe_native_fcstd(data)
                return ProbeResult(self.info.format_id, confidence, reason)
        except (OSError, TypeError, ValueError, zipfile.BadZipFile) as exc:
            return ProbeResult(self.info.format_id, 0.0, str(exc))
        return ProbeResult(
            self.info.format_id, 0.0, "ZIP archive has no FreeCAD document"
        )

    def read(self, source: Source, options: ReadOptions | None = None) -> CadDocument:
        settings = options or ReadOptions(include_tessellation=True)
        data = _source_bytes(source)
        native = False
        try:
            value = extract_manifest_from_fcstd(data)
        except ValueError as exc:
            if str(exc) != "FCStd archive has no embedded Kit interchange document":
                raise FreeCADAdapterError(str(exc)) from exc
            try:
                document = read_native_fcstd(data, _source_path(source))
            except (NativeFreeCADError, TypeError, ValueError) as native_exc:
                raise FreeCADAdapterError(str(native_exc)) from native_exc
            native = True
        else:
            document = _manifest_document(value)
        if native:
            document = _annotate_native_sources(document)
        document = replace(
            document,
            configurations=_selected_configurations(
                document.configurations, settings.configuration
            ),
        )
        document = _filtered_document(document, settings)
        if settings.strict:
            document.assert_valid()
        return document

    def supports(self, document: CadDocument, destination: Destination) -> bool:
        path = _destination_path(destination)
        if path is not None:
            return path.suffix.casefold() == SUFFIX.casefold()
        if not is_binary_destination(destination):
            return False
        writable = getattr(destination, "writable", None)
        if callable(writable):
            try:
                return bool(writable())
            except (OSError, ValueError):
                return False
        return True

    def write(
        self,
        document: CadDocument,
        destination: Destination,
        options: WriteOptions | None = None,
        *,
        overwrite: bool | None = None,
    ) -> WriteResult:
        selected = options or WriteOptions()
        should_overwrite = selected.overwrite if overwrite is None else overwrite
        if selected.validate:
            document.assert_valid()
        if not self.supports(document, destination):
            raise FreeCADAdapterError(
                f"FreeCAD destination must be a {SUFFIX} path or writable binary stream"
            )
        destination_path = _destination_path(destination)
        if (
            destination_path is not None
            and destination_path.exists()
            and not should_overwrite
        ):
            raise FileExistsError(destination_path)
        portable = selected.values.get("portable", True) is True
        native_external_documents = _native_external_documents(document)
        verified_native_source = _unchanged_native_source(document)
        trusted_native_breps = _trusted_native_breps(document)
        native_source = (
            None
            if selected.values.get("rebuild", False) is True
            or (
                portable
                and (document.assembly is not None or bool(native_external_documents))
            )
            else verified_native_source
        )
        if native_source is not None:
            path = _write_bytes(destination, native_source, should_overwrite)
            external_requirements = document.assembly is not None or bool(
                native_external_documents
            )
            requirements = (
                ("referenced FreeCAD component files",) if external_requirements else ()
            )
            return WriteResult(
                path=path,
                adapter=self.info.format_id,
                bytes_written=len(native_source),
                diagnostics=document.diagnostics,
                transfers=_capability_transfers(
                    document,
                    destination_path,
                    portable,
                    True,
                ),
                metadata={
                    "mode": "exact_native_roundtrip",
                    "compatibility": "native-exact",
                    "vendor_loadable": True,
                    "application_usable": True,
                    "native_self_contained": not external_requirements,
                    "referenced_files_written": 0,
                    "runtime": "python-stdlib",
                },
                requirements=requirements,
                application_usable=True,
                vendor_loadable=True,
            )
        external_links: dict[str, dict[str, Any]] = {}
        native_external_links: dict[str, str] = {}
        component_bytes_written = 0
        native_external_bytes_written = 0
        document_timestamp: str | None = None
        timestamp_epoch: float | None = None
        carrier_only_references = (
            destination_path is None
            and portable
            and (bool(native_external_documents) or document.assembly is not None)
        )
        if destination_path is not None and document.assembly is not None:
            document_timestamp, timestamp_epoch = _bundle_timestamp(destination_path)
            external_links, component_bytes_written = _write_components(
                document,
                destination_path,
                should_overwrite,
                selected.validate,
                document_timestamp,
                timestamp_epoch,
                trusted_native_breps,
            )
        if destination_path is not None and native_external_documents and portable:
            native_external_links, native_external_bytes_written = (
                _write_native_external_documents(
                    document,
                    destination_path,
                    should_overwrite,
                    selected.validate,
                )
            )
        manifest = document_to_manifest(document)
        data = build_fcstd_archive(
            manifest,
            external_links=external_links,
            native_external_links=native_external_links,
            document_timestamp=document_timestamp,
            trusted_native_breps=trusted_native_breps,
        )
        path = _write_bytes(destination, data, should_overwrite)
        if path is not None and timestamp_epoch is not None:
            os.utime(path, (timestamp_epoch, timestamp_epoch))
        transfers = _capability_transfers(
            document,
            destination_path,
            portable,
            False,
            trusted_native_breps,
        )
        application_usable = not carrier_only_references and _native_geometry_is_usable(
            document,
            trusted_native_breps,
        )
        metadata = {
            "schema_version": document.schema_version,
            "sketch_count": len(document.sketches),
            "timeline_count": len(document.feature_timeline),
            "native_payload_count": len(document.brep_payloads),
            "assembly_occurrence_count": (
                len(document.assembly.instances) if document.assembly is not None else 0
            ),
            "assembly_mate_count": (
                len(document.assembly.mates) if document.assembly is not None else 0
            ),
            "component_file_count": len(external_links),
            "component_bytes_written": component_bytes_written,
            "external_document_file_count": len(native_external_links),
            "external_document_bytes_written": native_external_bytes_written,
            "runtime": "python-stdlib",
            "recompute_required": True,
            "native_referenced_files_emitted": not carrier_only_references,
            "carrier_embedded_reference_count": (
                len(native_external_documents)
                + (
                    len(document.assembly.documents)
                    if document.assembly is not None
                    else 0
                )
            ),
            "application_usable": application_usable,
            "vendor_loadable": True,
        }
        diagnostics = document.diagnostics
        if carrier_only_references:
            diagnostics = (
                *diagnostics,
                Diagnostic(
                    "freecad.references_embedded_without_files",
                    "Referenced documents are retained in the Kit carrier but cannot be exposed as native relative files from a stream destination",
                    Severity.WARNING,
                ),
            )
        return WriteResult(
            path=path,
            adapter=self.info.format_id,
            bytes_written=len(data),
            diagnostics=diagnostics,
            metadata=metadata,
            transfers=transfers,
            application_usable=application_usable,
            vendor_loadable=True,
        )


def extract_freecad_manifest(source: Source) -> dict[str, Any]:
    return extract_manifest_from_fcstd(_source_bytes(source))


def read_freecad(source: Source, options: ReadOptions | None = None) -> CadDocument:
    return FreeCADAdapter().read(source, options)


def write_freecad(
    document: CadDocument,
    destination: Destination,
    *,
    overwrite: bool = False,
    validate: bool = True,
) -> WriteResult:
    return FreeCADAdapter().write(
        document, destination, WriteOptions(overwrite=overwrite, validate=validate)
    )
