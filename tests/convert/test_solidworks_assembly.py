from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path
import struct

import pytest

from convert.adapters.base import ReadOptions
from convert.adapters.solidworks import SldprtAdapter, SldprtArchive, build_sldprt
from convert.adapters.solidworks.adapter import (
    _companion_payloads,
    _mate_groups,
    _mate_instance_path,
    _mate_payload,
    _neutral_mate_alignment,
    _neutral_mate_entity_kind,
    _neutral_mate_kind,
    _neutral_mate_value,
)
from convert.adapters.freecad import read_freecad
from convert.adapters.solidworks.assembly import (
    MATE_LOSS_ENTITY_FRAME,
    MATE_LOSS_EXPRESSION,
    MATE_LOSS_GROUP_MEMBERSHIP,
    MATE_LOSS_REASONS,
    MATE_LOSS_VALUE_MISSING,
    MATE_VALUE_SEMANTICS,
    NATIVE_MATE_ALIGNMENTS,
    NATIVE_MATE_ALIGNMENT_BY_CODE,
    NATIVE_MATE_ENTITY_GEOMETRY_TYPES,
    NATIVE_MATE_ENTITY_KIND_BY_MARKER,
    NATIVE_MATE_ENTITY_MARKERS,
    NATIVE_MATE_ENTITY_REFERENCE_TYPES,
    NATIVE_MATE_ENTITY_TYPE_RECORDS,
    NATIVE_MATE_NEUTRAL_KIND_ALIASES,
    NATIVE_MATE_TYPE_RECORDS,
    NATIVE_MATE_TYPES,
    NativeMate,
    NativeMateAlignmentCode,
    NativeMateDimension,
    _MATE_KIND_BY_CLASS,
    _MATE_KIND_BY_NAME,
    _mate_alignment,
    _mate_entities,
    _mate_kind,
    decode_mate_list,
    decode_native_assembly,
    encode_native_assembly,
)
from interchange import (
    AssemblyData,
    Capability,
    ComponentDefinition,
    ComponentInstance,
    ComponentKind,
    Configuration,
    MateAlignment,
    MateConstraint,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    Matrix4,
    ParameterValue,
    ValueKind,
)


RANDOM = Path(__file__).resolve().parents[2] / "examples" / "Random"
ASSEMBLY = RANDOM / "V8_engine.SLDASM"
CONROD = RANDOM / "Pistons" / "Conrod.SLDASM"


@pytest.fixture(scope="module")
def document():
    return SldprtAdapter().read(ASSEMBLY, ReadOptions(include_brep=False))


def test_massive_assembly_recovers_hierarchy_documents_and_history(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    assert document.validate() == ()
    assert len(assembly.definitions) == 68
    assert Counter(definition.kind for definition in assembly.definitions) == {
        ComponentKind.PART: 65,
        ComponentKind.ASSEMBLY: 3,
    }
    assert len(assembly.instances) == 288
    assert assembly.attributes["flattened_occurrence_count"] == 358
    assert len(assembly.documents) == 53
    assert assembly.attributes["linked_part_document_count"] == 51
    assert assembly.attributes["linked_assembly_document_count"] == 2
    assert assembly.attributes["linked_sketch_count"] == 391
    assert assembly.attributes["linked_feature_count"] == 2147
    assert len(document.sketches) == 3
    assert len(document.feature_timeline) == 327
    assert (
        sum(
            feature.attributes["xml_tag"] == "Reference"
            for feature in document.feature_timeline
        )
        == 278
    )
    assert len(document.support_planes) == 6


def test_assembly_capabilities_reflect_the_decoded_document(document) -> None:
    assert document.capabilities == frozenset(
        {
            Capability.ASSEMBLIES,
            Capability.ASSEMBLY_MATES,
            Capability.BODY_STRUCTURE,
            Capability.COMPONENT_DOCUMENTS,
            Capability.CONFIGURATIONS,
            Capability.EDITABLE_SKETCHES,
            Capability.EXTERNAL_REFERENCES,
            Capability.NATIVE_PAYLOADS,
            Capability.PARAMETERS,
            Capability.PARAMETRIC_HISTORY,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
            Capability.SELECTIONS,
            Capability.SUPPORT_PLANES,
            Capability.TESSELLATION,
        }
    )


def test_official_mate_types_have_explicit_class_mappings() -> None:
    expected = {
        "MatePlanarAngleDim": MateKind.ANGLE,
        "MateCamTangent": MateKind.CAM,
        "MateCoincident": MateKind.COINCIDENT,
        "MateConcentric": MateKind.CONCENTRIC,
        "MateCoordinate": MateKind.COORDINATE,
        "MateDistanceDim": MateKind.DISTANCE,
        "MateGearDim": MateKind.GEAR,
        "MateHinge": MateKind.HINGE,
        "MateLinearCoupler": MateKind.LINEAR_COUPLER,
        "MateLock": MateKind.LOCK,
        "moLockToSketchMate": MateKind.LOCK,
        "MateMagnetic": MateKind.MAGNETIC,
        "MateParallel": MateKind.PARALLEL,
        "MatePath": MateKind.PATH,
        "MatePerpendicular": MateKind.PERPENDICULAR,
        "MateProfileCenter": MateKind.PROFILE_CENTER,
        "MateRackPinionDim": MateKind.RACK_PINION,
        "MateScrew": MateKind.SCREW,
        "MateSlider": MateKind.SLIDER,
        "MateSlot": MateKind.SLOT,
        "MateSymmetric": MateKind.SYMMETRIC,
        "MateTangent": MateKind.TANGENT,
        "MateUniversalJoint": MateKind.UNIVERSAL_JOINT,
        "MateWidth": MateKind.WIDTH,
    }
    assert {name.casefold() for name in expected} <= _MATE_KIND_BY_CLASS.keys()
    assert {
        name: _neutral_mate_kind(_mate_kind("Renamed mate", name)) for name in expected
    } == expected


def test_official_mate_type_registry_is_exhaustive_and_derived() -> None:
    assert tuple((record.code, record.api_name) for record in NATIVE_MATE_TYPES) == (
        (0, "swMateCOINCIDENT"),
        (1, "swMateCONCENTRIC"),
        (2, "swMatePERPENDICULAR"),
        (3, "swMatePARALLEL"),
        (4, "swMateTANGENT"),
        (5, "swMateDISTANCE"),
        (6, "swMateANGLE"),
        (7, "swMateUNKNOWN"),
        (8, "swMateSYMMETRIC"),
        (9, "swMateCAMFOLLOWER"),
        (10, "swMateGEAR"),
        (11, "swMateWIDTH"),
        (12, "swMateLOCKTOSKETCH"),
        (13, "swMateRACKPINION"),
        (14, "swMateMAXMATES"),
        (15, "swMatePATH"),
        (16, "swMateLOCK"),
        (17, "swMateSCREW"),
        (18, "swMateLINEARCOUPLER"),
        (19, "swMateUNIVERSALJOINT"),
        (20, "swMateCOORDINATE"),
        (21, "swMateSLOT"),
        (22, "swMateHINGE"),
        (23, "swMateSLIDER"),
        (24, "swMatePROFILECENTER"),
        (25, "swMateMAGNETIC"),
    )
    assert _MATE_KIND_BY_CLASS == {
        class_name.casefold(): record.kind
        for record in NATIVE_MATE_TYPE_RECORDS
        for class_name in record.class_names
    }
    assert _MATE_KIND_BY_NAME == {
        prefix.casefold(): record.kind
        for record in NATIVE_MATE_TYPE_RECORDS
        for prefix in record.name_prefixes
    }
    assert len(_MATE_KIND_BY_CLASS) == 64
    assert len(_MATE_KIND_BY_NAME) == 40
    assert NATIVE_MATE_NEUTRAL_KIND_ALIASES == {
        "cam_tangent": "cam",
        "lock_to_sketch": "lock",
    }
    assert _MATE_KIND_BY_CLASS["matereferencegroupfolder"] == "group"
    assert _mate_kind("Renamed", "MateReferenceGroupFolder") == "group"
    assert MATE_VALUE_SEMANTICS == {
        "distance": "length",
        "angle": "angle",
        "gear": "ratio",
        "rack_pinion": "length",
        "screw": "length",
        "linear_coupler": "ratio",
        "belt": "ratio",
    }


def test_official_mate_entity_reference_registry_is_exhaustive() -> None:
    assert tuple(
        (record.code, record.api_name) for record in NATIVE_MATE_ENTITY_GEOMETRY_TYPES
    ) == (
        (0, "swMateUnsupported"),
        (1, "swMatePoint"),
        (2, "swMateLine"),
        (3, "swMatePlane"),
        (4, "swMateCylinder"),
        (5, "swMateCone"),
        (6, "swMateSphere"),
        (7, "swMateCircle"),
    )
    assert tuple(
        (record.code, record.api_name) for record in NATIVE_MATE_ENTITY_REFERENCE_TYPES
    ) == (
        (0, "swMateEntity2ReferenceType_Point"),
        (1, "swMateEntity2ReferenceType_Line"),
        (2, "swMateEntity2ReferenceType_Circle"),
        (3, "swMateEntity2ReferenceType_Plane"),
        (4, "swMateEntity2ReferenceType_Cylinder"),
        (5, "swMateEntity2ReferenceType_Sphere"),
        (6, "swMateEntity2ReferenceType_Set"),
        (7, "swMateEntity2ReferenceType_Cone"),
        (8, "swMateEntity2ReferenceType_SweptSurface"),
        (9, "swMateEntity2ReferenceType_MultipleSurface"),
        (10, "swMateEntity2ReferenceType_GenSurface"),
        (11, "swMateEntity2ReferenceType_Ellipse"),
        (12, "swMateEntity2ReferenceType_GeneralCurve"),
        (13, "swMateEntity2ReferenceType_UNKNOWN"),
    )
    assert {record.kind for record in NATIVE_MATE_ENTITY_TYPE_RECORDS} == {
        kind.value for kind in MateEntityKind
    }
    assert len(NATIVE_MATE_ENTITY_KIND_BY_MARKER) == 26
    assert NATIVE_MATE_ENTITY_MARKERS == tuple(
        (marker.casefold(), record.kind)
        for record in NATIVE_MATE_ENTITY_TYPE_RECORDS
        for marker in record.markers
    )


@pytest.mark.parametrize(
    ("persistent_reference", "expected"),
    (
        ("moRefPoint", MateEntityKind.POINT),
        ("moLine", MateEntityKind.LINE),
        ("moCircle", MateEntityKind.CIRCLE),
        ("moPlane", MateEntityKind.PLANE),
        ("moWzdHoleSurfIdRep", MateEntityKind.CYLINDER),
        ("moCone", MateEntityKind.CONE),
        ("moSphere", MateEntityKind.SPHERE),
        ("moGeneralCurve", MateEntityKind.CURVE),
        ("moGenSurface", MateEntityKind.SURFACE),
        ("moVertex", MateEntityKind.VERTEX),
        ("moAxis", MateEntityKind.AXIS),
        ("moEdge", MateEntityKind.EDGE),
        ("moFaceRef_c", MateEntityKind.FACE),
        ("moCoordinateSystem", MateEntityKind.COORDINATE_SYSTEM),
        ("Sketch1^Line1@Part", MateEntityKind.SKETCH_ENTITY),
        ("moVendorEntity", MateEntityKind.NATIVE),
    ),
)
def test_mate_entity_reference_classification_uses_the_complete_registry(
    persistent_reference: str, expected: MateEntityKind
) -> None:
    assert _neutral_mate_entity_kind(persistent_reference) == expected


def test_official_mate_alignment_registry_preserves_every_code() -> None:
    assert tuple(
        (record.code.value, record.api_name, record.kind)
        for record in NATIVE_MATE_ALIGNMENTS
    ) == (
        (0, "swMateReferenceAlignment_Any", "unknown"),
        (1, "swMateReferenceAlignment_Aligned", "aligned"),
        (2, "swMateReferenceAlignment_AntiAligned", "anti_aligned"),
        (3, "swMateReferenceAlignment_Closest", "closest"),
    )
    assert NATIVE_MATE_ALIGNMENT_BY_CODE == {
        record.code.value: record for record in NATIVE_MATE_ALIGNMENTS
    }
    for code in NativeMateAlignmentCode:
        data = bytearray(168)
        struct.pack_into("<H", data, 159, code.value)
        struct.pack_into("<I", data, 164, 2)
        assert _mate_alignment(bytes(data), len(data), 0) == code.value
    invalid = bytearray(168)
    struct.pack_into("<H", invalid, 159, 42)
    struct.pack_into("<I", invalid, 164, 2)
    assert _mate_alignment(bytes(invalid), len(invalid), 0) is None
    expected = (
        MateAlignment.UNKNOWN,
        MateAlignment.ALIGNED,
        MateAlignment.ANTI_ALIGNED,
        MateAlignment.CLOSEST,
    )
    assert (
        tuple(
            _neutral_mate_alignment(_native_mate(alignment_code=code.value))
            for code in NativeMateAlignmentCode
        )
        == expected
    )


def test_linear_coupler_ratio_uses_the_mate_protocol_registry() -> None:
    value = _neutral_mate_value(
        _native_mate(
            kind="linear_coupler",
            dimensions=(
                NativeMateDimension("D1", 2.0, 10),
                NativeMateDimension("D2", 4.0, 20),
            ),
        )
    )
    assert value is not None
    assert value.value == pytest.approx(0.5)
    assert value.kind == ValueKind.NUMBER


def _native_mate(
    *,
    kind: str = "native",
    alignment_code: int | None = None,
    dimensions: tuple[NativeMateDimension, ...] = (),
) -> NativeMate:
    return NativeMate(
        name="Fixture",
        kind=kind,
        owner_definition_id=0,
        order=0,
        entities=(),
        record_offset=0,
        record_length=0,
        class_name="",
        class_token=None,
        serialized_strings=(),
        alignment_code=alignment_code,
        dimensions=dimensions,
    )


@pytest.mark.parametrize(
    ("name", "neutral_kind"),
    (
        ("Coordinate17", MateKind.COORDINATE),
        ("Slider8", MateKind.SLIDER),
        ("Magnetic4", MateKind.MAGNETIC),
        ("Path2", MateKind.PATH),
    ),
)
def test_official_mate_name_fallbacks_are_semantic(
    name: str, neutral_kind: MateKind
) -> None:
    assert _neutral_mate_kind(_mate_kind(name)) == neutral_kind


def test_mate_name_fallback_does_not_masquerade_custom_names() -> None:
    assert _mate_kind("DistanceVendor") == "native"
    assert _mate_kind("CoincidentCustomer1") == "native"


def test_massive_assembly_recovers_exact_transforms_and_state(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    ring = next(
        instance
        for instance in assembly.instances
        if instance.id == "sldasm:instance:223"
    )
    assert ring.transform.values == (
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
        0.0,
        46.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
        0.0,
        0.0,
        1.0,
    )
    piston = next(
        instance
        for instance in assembly.instances
        if instance.id == "sldasm:instance:217"
    )
    assert piston.transform.values[3] == pytest.approx(-1.209188127289168e-15)
    assert piston.transform.values[7] == pytest.approx(79.99530923564972)
    assert piston.transform.values[11] == pytest.approx(-79.99530923564954)
    assert next(
        instance
        for instance in assembly.instances
        if instance.id == "sldasm:instance:211"
    ).fixed
    assert all(not instance.suppressed for instance in assembly.instances)


def test_massive_assembly_recovers_root_and_nested_mates_losslessly(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    assert len(assembly.mates) == 632
    assert len(assembly.mate_entities) == 1261
    assert Counter(mate.kind for mate in assembly.mates) == {
        MateKind.CONCENTRIC: 301,
        MateKind.COINCIDENT: 280,
        MateKind.CAM: 32,
        MateKind.BELT: 14,
        MateKind.LOCK: 3,
        MateKind.GEAR: 1,
        MateKind.DISTANCE: 1,
    }
    assert len(assembly.mate_groups) == 3
    assert [len(group.mate_ids) for group in assembly.mate_groups] == [6, 2, 9]
    assert assembly.attributes["flattened_mate_occurrence_count"] == 765
    payloads = [
        payload
        for payload in document.brep_payloads
        if payload.format_id == "solidworks.mates"
    ]
    assert [len(payload.data or b"") for payload in payloads] == [
        2202551,
        18893,
        43184,
    ]
    assert sum(payload.attributes["declared_count"] for payload in payloads) == 638
    assert all(mate.attributes["native_payload_id"] for mate in assembly.mates)


def test_massive_assembly_recovers_distance_mate_value_and_alignment(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    distance = next(mate for mate in assembly.mates if mate.kind == MateKind.DISTANCE)
    assert distance.name == "Distance1"
    assert distance.value is not None
    assert distance.value.value == pytest.approx(20.0)
    assert distance.value.kind == ValueKind.LENGTH
    assert distance.value.unit == "mm"
    assert distance.alignment == MateAlignment.ANTI_ALIGNED
    assert not distance.suppressed
    assert distance.attributes["native_alignment_code"] == 2
    assert distance.attributes["native_value_m"] == pytest.approx(0.02)
    assert distance.attributes["native_value_offset"] == 1640514
    gear = next(mate for mate in assembly.mates if mate.kind == MateKind.GEAR)
    assert gear.value is not None
    assert gear.value.value == pytest.approx(1.0)
    assert gear.value.kind == ValueKind.NUMBER
    assert [item["name"] for item in gear.attributes["native_dimensions"]] == [
        "D1",
        "D2",
    ]
    assert gear.alignment == MateAlignment.UNKNOWN
    belts = [mate for mate in assembly.mates if mate.kind == MateKind.BELT]
    assert all(mate.value is not None for mate in belts)
    assert all(mate.alignment == MateAlignment.UNKNOWN for mate in belts)
    assert all(
        mate.value.value
        == pytest.approx(
            mate.attributes["native_dimensions"][0]["value"]
            / mate.attributes["native_dimensions"][1]["value"]
        )
        for mate in belts
    )


def test_mate_types_use_native_classes_without_losing_future_records() -> None:
    archive = SldprtArchive.open(CONROD)
    record = next(item for item in archive.records if item.name.endswith("-MatesList"))
    old_name = "Concentric1".encode("utf-16le")
    new_name = "CustomMate1".encode("utf-16le")
    name_offset = record.data.index(old_name)
    renamed = (
        record.data[:name_offset]
        + new_name
        + record.data[name_offset + len(old_name) :]
    )
    renamed_list = decode_mate_list(renamed, record.name, 7)
    assert renamed_list.mates[0].name == "CustomMate1"
    assert renamed_list.mates[0].kind == "concentric"
    assert renamed_list.mates[0].class_name == "moMateConcentric"
    old_class = b"moMateConcentric"
    new_class = b"moMateVendorType"
    original_class_offset = record.data.index(old_class)
    unknown_class = (
        record.data[:original_class_offset]
        + new_class
        + record.data[original_class_offset + len(old_class) :]
    )
    unknown_class_list = decode_mate_list(unknown_class, record.name, 7)
    assert unknown_class_list.mates[0].name == "Concentric1"
    assert unknown_class_list.mates[0].kind == "native"
    class_offset = renamed.index(old_class)
    future = (
        renamed[:class_offset] + new_class + renamed[class_offset + len(old_class) :]
    )
    future_list = decode_mate_list(future, record.name, 7)
    mate = future_list.mates[0]
    assert mate.name == "CustomMate1"
    assert mate.kind == "native"
    assert mate.class_name == "moMateVendorType"
    assert mate.serialized_strings[0] == "CustomMate1"
    assert _neutral_mate_kind(mate.kind) == MateKind.NATIVE
    payload = _mate_payload("future", record.name, future, future_list, 7, "fixture")
    assert payload.data == future
    assert payload.attributes["records"][0] == {
        "name": "CustomMate1",
        "kind": "native",
        "class_name": "moMateVendorType",
        "class_token": None,
        "offset": mate.record_offset,
        "length": mate.record_length,
    }


def test_reused_mate_class_tokens_survive_a_renamed_instance() -> None:
    archive = SldprtArchive.open(CONROD)
    record = next(item for item in archive.records if item.name.endswith("-MatesList"))
    old_name = "Coincident2".encode("utf-16le")
    new_name = "CustomMate2".encode("utf-16le")
    offset = record.data.index(old_name)
    renamed = record.data[:offset] + new_name + record.data[offset + len(old_name) :]
    mate_list = decode_mate_list(renamed, record.name, 7)
    mate = mate_list.mates[2]
    assert mate.name == "CustomMate2"
    assert mate.kind == "coincident"
    assert mate.class_name == "moMateCoincident"
    assert mate.class_token is not None


def test_mate_group_boundaries_are_structural() -> None:
    archive = SldprtArchive.open(ASSEMBLY)
    record = next(item for item in archive.records if item.name.endswith("-MatesList"))
    mate_list = decode_mate_list(record.data, record.name, 7)
    markers = [mate for mate in mate_list.mates if mate.kind == "group"]
    renamed = replace(
        mate_list,
        mates=tuple(
            (
                replace(mate, name="Groupe sans suffixe")
                if mate.order == markers[0].order
                else (
                    replace(mate, name="Terminaison locale")
                    if mate.order == markers[1].order
                    else mate
                )
            )
            for mate in mate_list.mates
        ),
    )
    mate_ids = {
        mate.order: f"mate:{mate.order}"
        for mate in renamed.mates
        if mate.kind != "group"
    }
    groups = _mate_groups(renamed, 7, mate_ids, record.name, "payload")
    assert groups[0].name == "Groupe sans suffixe"
    assert groups[0].mate_ids


def test_custom_component_paths_resolve_without_numeric_suffixes() -> None:
    archive = SldprtArchive.open(CONROD)
    native = decode_native_assembly(archive)
    occurrence = next(
        item
        for item in native.occurrences
        if item.owner_definition_id == native.root_definition_id
    )
    owner = next(
        item
        for item in native.definitions
        if item.object_id == native.root_definition_id
    )
    identity = {item.object_id: item.object_id for item in native.occurrences}
    assert _mate_instance_path(
        native,
        identity,
        f"{occurrence.name}@{owner.name}",
    ) == (occurrence.object_id,)
    entities = _mate_entities(
        (
            "moFaceRef_c,1,2,3",
            f"{occurrence.name}@{owner.name}",
            occurrence.name + ".SLDPRT",
        )
    )
    assert entities[0].component_path == f"{occurrence.name}@{owner.name}"
    assert entities[0].source_path == occurrence.name + ".SLDPRT"


def test_mate_list_discovery_uses_structure_when_the_stream_is_renamed() -> None:
    archive = SldprtArchive.open(CONROD)
    record = next(item for item in archive.records if item.name.endswith("-MatesList"))
    streams = archive.streams
    streams["Relations/AssemblyConstraints"] = streams.pop(record.name)
    renamed = SldprtArchive.from_bytes(
        build_sldprt(
            streams,
            file_id=archive.file_id,
            format_version=archive.format_version,
        )
    )
    native = decode_native_assembly(renamed)
    assert len(native.mate_lists) == 1
    assert native.mate_lists[0].stream == "Relations/AssemblyConstraints"
    assert len(native.mate_lists[0].mates) == 13


def test_massive_assembly_recovers_every_reusable_mesh(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    assert len(document.meshes) == 65
    assert sum(len(mesh.attributes["faces"]) for mesh in document.meshes) == 4391
    assert sum(len(mesh.vertices) for mesh in document.meshes) == 492148
    assert sum(len(mesh.triangles) for mesh in document.meshes) == 391218
    part_definitions = {
        definition.id
        for definition in assembly.definitions
        if definition.kind == ComponentKind.PART
    }
    meshed_definitions = {
        definition.id for definition in assembly.definitions if definition.mesh_ids
    }
    assert meshed_definitions == part_definitions


def test_nested_assembly_documents_preserve_their_own_timelines(document) -> None:
    assembly = document.assembly
    assert assembly is not None
    nested = [
        linked.document
        for linked in assembly.documents
        if linked.document.source.format_id == "solidworks.sldasm"
    ]
    assert sorted(len(item.feature_timeline) for item in nested) == [27, 29]
    assert sorted(len(item.assembly.mates) for item in nested) == [6, 13]
    assert all(not item.assembly.documents for item in nested)


def test_resolved_assembly_companions_are_retained_exactly() -> None:
    payloads = _companion_payloads(str(ASSEMBLY))
    assert [(payload.format_id, len(payload.data or b"")) for payload in payloads] == [
        ("acis.sat", 62444621),
        ("parasolid.x_t", 8036848),
    ]
    assert payloads[0].attributes["body_count"] == 391
