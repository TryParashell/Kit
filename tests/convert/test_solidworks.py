from __future__ import annotations

import ast
from pathlib import Path
import struct

import pytest

import convert.adapters.solidworks.adapter as solidworks_adapter
import convert.adapters.solidworks.assembly as solidworks_assembly
import convert.adapters.solidworks.display as solidworks_display
import convert.adapters.solidworks.native as solidworks_native
from convert.adapters.solidworks.adapter import SldprtAdapter
from convert.adapters.solidworks.container import SldprtArchive
from convert.adapters.solidworks.format import (
    ASSEMBLY_FORMAT_ID,
    ASSEMBLY_SUFFIX,
    CANONICAL_PLANE_FEATURE_TYPE,
    CLASS_MARKER,
    COMPONENT_TREE_STREAM,
    CONTAINER_VERSIONS,
    CONTENT_TYPES_STREAM,
    DIMENSION_SCALAR_HEADERS,
    DISPLAY_LISTS_STREAM,
    FEATURES_STREAM,
    FORMAT_IDS,
    FORMAT_ID_BY_SUFFIX,
    INFO,
    KEYWORDS_STREAM,
    KIT_DOCUMENT_STREAM,
    MATES_STREAM_NAME,
    MATES_STREAM_SUFFIX,
    OFFICIAL_REFERENCE_PLANE_FEATURE_TYPES,
    PARTITION_STREAM,
    PART_FORMAT_ID,
    PART_SUFFIX,
    PLANE_FEATURE_TYPES,
    RELATIONSHIPS_STREAM,
    RESOLVED_FEATURES_STREAM,
    SERIALIZED_STRING_MARKER,
    SOLIDWORKS_STREAM,
    SOLID_BODY_FEATURE_TYPES,
    SUFFIX_BY_FORMAT_ID,
    dimension_scalar_value_offset,
    is_cad_path,
    is_component_path,
)
from interchange import (
    BooleanOperation,
    Capability,
    CircleGeometry,
    FeatureKind,
    LineGeometry,
)


SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"


def test_format_protocol_values_are_exact_and_derived_from_adapter_info() -> None:
    assert SldprtAdapter().info is INFO
    assert FORMAT_IDS == (INFO.format_id, *INFO.aliases)
    assert tuple(FORMAT_ID_BY_SUFFIX) == INFO.extensions
    assert tuple(FORMAT_ID_BY_SUFFIX.values()) == FORMAT_IDS
    assert SUFFIX_BY_FORMAT_ID == {
        format_id: suffix for suffix, format_id in FORMAT_ID_BY_SUFFIX.items()
    }
    assert (PART_FORMAT_ID, ASSEMBLY_FORMAT_ID) == FORMAT_IDS
    assert (PART_SUFFIX, ASSEMBLY_SUFFIX) == INFO.extensions
    assert CONTAINER_VERSIONS == frozenset({3, 4})
    assert (
        COMPONENT_TREE_STREAM,
        DISPLAY_LISTS_STREAM,
        KEYWORDS_STREAM,
        FEATURES_STREAM,
        RESOLVED_FEATURES_STREAM,
        PARTITION_STREAM,
        SOLIDWORKS_STREAM,
        KIT_DOCUMENT_STREAM,
        CONTENT_TYPES_STREAM,
        RELATIONSHIPS_STREAM,
        MATES_STREAM_NAME,
        MATES_STREAM_SUFFIX,
    ) == (
        "swXmlContents/COMPINSTANCETREE",
        "Contents/DisplayLists",
        "swXmlContents/KeyWords",
        "swXmlContents/Features",
        "Contents/Config-0-ResolvedFeatures",
        "Contents/Config-0-Partition",
        "Contents/SolidWorks",
        "Kit/Interchange",
        "[Content_Types].xml",
        "_rels/.rels",
        "MatesList",
        "-MatesList",
    )
    assert CLASS_MARKER.hex() == "ffff0100"
    assert SERIALIZED_STRING_MARKER.hex() == "fffeff"
    assert tuple(header.hex() for header in DIMENSION_SCALAR_HEADERS) == (
        "0000000000000040ffffffff00000000fffeff000000",
        "0000000000000040ffffffff000000000000",
    )
    assert CANONICAL_PLANE_FEATURE_TYPE == "plane"
    assert OFFICIAL_REFERENCE_PLANE_FEATURE_TYPES == frozenset({"refplane"})
    assert PLANE_FEATURE_TYPES == frozenset({"plane", "refplane"})
    assert SOLID_BODY_FEATURE_TYPES == frozenset(
        {"featsolidbodyfolder", "solidbodyfolder"}
    )
    assert all(
        solidworks_adapter._FEATURE_KIND_BY_NATIVE[native_type] == FeatureKind.REFERENCE
        for native_type in (*PLANE_FEATURE_TYPES, *SOLID_BODY_FEATURE_TYPES)
    )


def test_marker_local_id_record_lengths_are_centralized_with_unknown_fallback() -> None:
    expected = {
        142: 138,
        146: 138,
        152: 148,
        154: 150,
        156: 148,
        158: 144,
        162: 158,
        166: 158,
        167: 158,
    }
    assert solidworks_native.MARKER_LOCAL_ID_OFFSET_BY_LENGTH == expected
    for length, relative in expected.items():
        data = bytearray(length + 4)
        struct.pack_into("<I", data, relative, 42)
        assert solidworks_native._marker_local_id(bytes(data), 0, length) == 42
    assert solidworks_native._marker_local_id(bytes(2048), 0, 2048) is None


@pytest.mark.parametrize("header", DIMENSION_SCALAR_HEADERS)
def test_dimension_scalar_header_bounds_are_shared_and_exact(header: bytes) -> None:
    data = b"x" + header + struct.pack("<d", 2.0)
    expected = 1 + len(header)
    assert dimension_scalar_value_offset(data, 1, len(data)) == expected
    assert dimension_scalar_value_offset(data[:-1], 1, len(data) - 1) is None
    assert dimension_scalar_value_offset(data, 1, len(data), trailing_bytes=7) is None
    with_trailer = data + b"\0" * 7
    assert (
        dimension_scalar_value_offset(
            with_trailer,
            1,
            len(with_trailer),
            trailing_bytes=7,
        )
        == expected
    )


def test_protocol_consumers_share_authoritative_objects() -> None:
    assert (
        solidworks_native.dimension_scalar_value_offset is dimension_scalar_value_offset
    )
    assert (
        solidworks_assembly.dimension_scalar_value_offset
        is dimension_scalar_value_offset
    )
    assert solidworks_assembly.COMPONENT_TREE_STREAM is COMPONENT_TREE_STREAM
    assert solidworks_assembly.DISPLAY_LISTS_STREAM is DISPLAY_LISTS_STREAM
    assert solidworks_display.DISPLAY_LISTS_STREAM is DISPLAY_LISTS_STREAM
    assert solidworks_display.is_cad_path is is_cad_path
    assert solidworks_display.is_component_path is is_component_path
    assert solidworks_adapter.INFO is INFO
    assert solidworks_adapter.FORMAT_ID_BY_SUFFIX is FORMAT_ID_BY_SUFFIX
    assert solidworks_adapter.SUFFIX_BY_FORMAT_ID is SUFFIX_BY_FORMAT_ID


def test_protocol_literals_have_one_source_definition() -> None:
    values = {
        ".sldprt",
        ".sldasm",
        "swXmlContents/COMPINSTANCETREE",
        "Contents/DisplayLists",
        "swXmlContents/KeyWords",
        "swXmlContents/Features",
        "Contents/Config-0-ResolvedFeatures",
        "Contents/Config-0-Partition",
        "Contents/SolidWorks",
        "Kit/Interchange",
        "[Content_Types].xml",
        "_rels/.rels",
        "MatesList",
        "ffff0100",
        "fffeff",
        "0000000000000040ffffffff00000000fffeff000000",
        "0000000000000040ffffffff000000000000",
        "refplane",
        "featsolidbodyfolder",
        "solidbodyfolder",
    }
    source_root = Path(solidworks_adapter.__file__).parent
    occurrences = {value: [] for value in values}
    for path in source_root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value in occurrences:
                occurrences[node.value].append(path.name)
    assert occurrences == {value: ["format.py"] for value in values}


@pytest.mark.parametrize(
    ("value", "is_cad", "is_component"),
    (
        ("C:/parts/Part.SLDPRT", True, False),
        ("C:/parts/Assembly.SLDASM", True, False),
        ("C:/parts/Part.sldprtx", False, False),
        ("Rotor@Assembly", False, True),
        ("Top Plane@Rotor@Assembly", False, False),
    ),
)
def test_protocol_path_classification_is_exact(
    value: str, is_cad: bool, is_component: bool
) -> None:
    assert is_cad_path(value) is is_cad
    assert is_component_path(value) is is_component


def test_container_recovers_every_integrity_checked_stream() -> None:
    archive = SldprtArchive.open(SAMPLE)
    assert archive.format_version == 4
    assert len(archive.records) == 44
    assert archive.records[0].name == "Contents/3DExperienceExchange2"
    assert archive.records[-1].name == "swXmlContents/KeyWords"
    assert {record.name for record in archive.records} >= {
        "Contents/Config-0-ResolvedFeatures",
        "Contents/Config-0-Partition",
        "PreviewPNG",
        "Header2",
        "Preview",
    }


def test_parametric_history_is_native_and_ordered() -> None:
    document = SldprtAdapter().read(SAMPLE)
    operations = [
        feature
        for feature in document.feature_timeline
        if feature.name
        in {
            "Boss-Extrude1",
            "Cut-Extrude1",
            "Boss-Extrude2",
            "Cut-Extrude2",
            "Boss-Extrude3",
            "Fillet1",
        }
    ]
    assert [feature.name for feature in operations] == [
        "Boss-Extrude1",
        "Cut-Extrude1",
        "Boss-Extrude2",
        "Cut-Extrude2",
        "Boss-Extrude3",
        "Fillet1",
    ]
    assert [feature.operation for feature in operations[:-1]] == [
        BooleanOperation.JOIN,
        BooleanOperation.CUT,
        BooleanOperation.JOIN,
        BooleanOperation.CUT,
        BooleanOperation.JOIN,
    ]
    assert [
        document.parameter(feature.parameter_ids[0]).value.value
        for feature in operations
    ] == [20.0, 0.25, 0.75, 9.0, 6.0, 0.25]
    assert Capability.PARAMETRIC_HISTORY in document.capabilities
    assert Capability.EDITABLE_SKETCHES in document.capabilities
    assert document.validate() == ()


def test_sketch_profiles_and_support_planes_are_exact() -> None:
    document = SldprtAdapter().read(SAMPLE)
    assert len(document.sketches) == 5
    first = document.sketch("sldprt:sketch:26")
    first_edges = [
        entity.geometry
        for entity in first.entities
        if entity.id in first.closed_profile_entity_ids[0]
    ]
    assert all(isinstance(edge, LineGeometry) for edge in first_edges)
    assert first_edges[0].start.x == -124.3
    assert first_edges[0].start.y == -89.75
    assert first_edges[2].start.x == 124.3
    assert first_edges[2].start.y == 89.75
    hole = document.sketch("sldprt:sketch:88")
    hole_profile = next(
        entity.geometry
        for entity in hole.entities
        if entity.id == hole.closed_profile_entity_ids[0][0]
    )
    assert isinstance(hole_profile, CircleGeometry)
    assert hole_profile.center.x == 10.0
    assert hole_profile.center.y == 81.631746131982
    assert hole_profile.radius == 2.75
    assert document.plane("sldprt:plane:62").transform.origin.x == 124.30000000000001
    assert document.plane("sldprt:plane:104").transform.origin.x == -115.3


def test_parasolid_brep_is_preserved_byte_for_byte() -> None:
    document = SldprtAdapter().read(SAMPLE)
    assert [payload.kind for payload in document.brep_payloads] == [
        "partition",
        "partition",
        "deltas",
    ]
    assert [len(payload.data or b"") for payload in document.brep_payloads] == [
        1513,
        30850,
        23150,
    ]
    assert [payload.sha256 for payload in document.brep_payloads] == [
        "8c57db227621a15a0a429cdd65dbe3f374e2c1145ef2f3edc3a25b745513bf3d",
        "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6",
        "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7",
    ]
    assert all(
        payload.data is not None and payload.data.startswith(b"PS\0\0")
        for payload in document.brep_payloads
    )


def test_neutral_json_roundtrip_keeps_history_and_brep() -> None:
    source = SldprtAdapter().read(SAMPLE)
    restored = type(source).from_json(source.to_json())
    assert restored == source
