from __future__ import annotations

from dataclasses import replace
from io import BytesIO, StringIO
import hashlib
import json
from pathlib import Path, PureWindowsPath
import struct
import xml.etree.ElementTree as ET

import pytest

from convert import (
    ApplicationUsabilityError,
    convert,
    open_document,
    registry,
    write_document,
)
from convert.adapters import WriteOptions
from convert.adapters.catia import read_catia, write_catia
from convert.adapters.freecad import read_freecad, write_freecad
from convert.adapters.solidworks import (
    SldprtArchive,
    SldprtFormatError,
    build_sldprt,
    decode_native_assembly,
    decode_native_model,
    decode_brep_model,
    decode_partition_stream,
    encode_blank_partition_stream,
    encode_brep_model,
    read_sldprt,
    write_sldprt,
)
from convert.adapters.solidworks.adapter import (
    _document_without_source,
    _native_stream_sha256,
    _semantic_sha256,
)
from convert.adapters.solidworks.format import (
    COMPONENT_TREE_STREAM,
    CONTENT_TYPES_STREAM,
    FEATURES_STREAM,
    KEYWORDS_STREAM,
    KIT_DOCUMENT_STREAM,
    KIT_NATIVE_STREAM,
    PARTITION_STREAM,
    RELATIONSHIPS_STREAM,
    RESOLVED_FEATURES_STREAM,
)
from convert.parasolid import _parasolid_header, _scan_partition_records
from interchange import (
    BooleanOperation,
    BrepPayload,
    CadDocument,
    Capability,
    Configuration,
    Diagnostic,
    ExtrusionFeature,
    GeometryKind,
    LineGeometry,
    MateAlignment,
    Matrix4,
    NativeSurface,
    Parameter,
    ParameterValue,
    PayloadRole,
    Severity,
    Sketch,
    SketchEntity,
    ValueKind,
    Vector2,
    frozen_mapping,
)
from tests.interchange.test_assembly import assembly_document
from tests.interchange.test_brep import triangle_brep
from tests.interchange.test_document import document

SAMPLE = Path(__file__).parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"
ASSEMBLY = (
    Path(__file__).parents[2] / "examples" / "Random" / "Pistons" / "Piston.SLDASM"
)
CONROD = Path(__file__).parents[2] / "examples" / "Random" / "Pistons" / "Conrod.SLDASM"
PISTON_RING = (
    Path(__file__).parents[2] / "examples" / "Random" / "Pistons" / "Piston_ring.SLDPRT"
)
CATPRODUCT = (
    Path(__file__).parents[2] / "examples" / ".CATProduct" / "Tilton_Set.CATProduct"
)


def test_pre_payload_field_solidworks_carrier_restores_payload_semantics() -> None:
    native_document = b"legacy CATProduct"
    native_digest = hashlib.sha256(native_document).digest()
    source = replace(
        document(),
        brep_payloads=(
            BrepPayload(
                "legacy-brep",
                "parasolid",
                "binary",
                "SCH_3500040",
                hashlib.sha256(b"PS\0\0legacy").hexdigest(),
                data=b"PS\0\0legacy",
                source_stream="Contents/Bodies/Partition",
                role=PayloadRole.BREP,
                file_extension=".x_b",
            ),
            BrepPayload(
                "legacy-mates",
                "solidworks.mates",
                "mate-list",
                "solidworks.serialized-object-stream",
                hashlib.sha256(b"legacy mates").hexdigest(),
                data=b"legacy mates",
                source_stream="Contents/Mates",
                role=PayloadRole.ASSEMBLY_STRUCTURE,
                file_extension=".bin",
            ),
            BrepPayload(
                "legacy-document",
                "catia.v5.cfv2",
                "native_document",
                "CATProduct",
                hashlib.sha256(native_document).hexdigest(),
                data=native_document,
                source_stream="V5_CFV2",
                role=PayloadRole.DOCUMENT,
                file_extension=".catproduct",
            ),
            BrepPayload(
                "legacy-binding",
                "catia.v5.sha256",
                "native_document_binding",
                "sha256",
                hashlib.sha256(native_digest).hexdigest(),
                data=native_digest,
                source_stream="V5_CFV2",
                role=PayloadRole.VERIFICATION,
                file_extension=".sha256",
            ),
        ),
    )
    generated = BytesIO()
    write_sldprt(source, generated)
    archive = SldprtArchive.from_bytes(generated.getvalue())
    manifest = json.loads(archive.require(KIT_DOCUMENT_STREAM))
    for payload in manifest["brep_payloads"]["$tuple"]:
        payload.pop("role")
        payload.pop("file_extension")
    streams = archive.streams
    streams[KIT_DOCUMENT_STREAM] = json.dumps(manifest).encode("utf-8")
    legacy = build_sldprt(
        streams,
        file_id=archive.file_id,
        format_version=archive.format_version,
    )
    restored = read_sldprt(legacy)
    fields = {
        payload.id: (payload.role, payload.file_extension, payload.data)
        for payload in restored.brep_payloads
    }
    assert fields == {
        "legacy-brep": (PayloadRole.BREP, ".x_b", b"PS\0\0legacy"),
        "legacy-mates": (
            PayloadRole.ASSEMBLY_STRUCTURE,
            ".bin",
            b"legacy mates",
        ),
        "legacy-document": (
            PayloadRole.DOCUMENT,
            ".catproduct",
            native_document,
        ),
        "legacy-binding": (
            PayloadRole.VERIFICATION,
            ".sha256",
            native_digest,
        ),
    }
    filtered = read_sldprt(legacy, include_brep=False)
    assert {payload.id for payload in filtered.brep_payloads} == {
        "legacy-mates",
        "legacy-document",
        "legacy-binding",
    }


def test_solidworks_source_replays_exactly_after_freecad_roundtrip(tmp_path) -> None:
    source = read_sldprt(SAMPLE)
    fcstd = tmp_path / "source.FCStd"
    output = tmp_path / "source.SLDPRT"
    write_freecad(source, fcstd)
    restored = read_freecad(fcstd)
    result = write_sldprt(restored, output)
    assert output.read_bytes() == SAMPLE.read_bytes()
    assert result.metadata["mode"] == "exact"
    assert result.metadata["native_content"] == "exact"
    assert result.metadata["compatibility"] == "native-exact"
    assert result.metadata["neutral_edits_are_native"] is True
    assert result.metadata["native_self_contained"] is True
    assert result.metadata["referenced_files_written"] == 0


def test_solidworks_source_replays_exactly_after_catia_carrier(tmp_path) -> None:
    source = read_sldprt(SAMPLE)
    catpart = tmp_path / "source.CATPart"
    output = tmp_path / "source.SLDPRT"
    write_catia(source, catpart, allow_non_native=True)
    restored = read_catia(catpart)
    result = write_sldprt(restored, output)
    assert output.read_bytes() == SAMPLE.read_bytes()
    assert result.metadata["mode"] == "exact"
    assert result.metadata["compatibility"] == "native-exact"


def test_portable_solidworks_assembly_discards_active_catia_carrier_envelope(
    tmp_path,
) -> None:
    source = read_sldprt(ASSEMBLY)
    catproduct = tmp_path / "source.CATProduct"
    output = tmp_path / "source.SLDASM"
    write_catia(source, catproduct, allow_non_native=True)
    restored = open_document(catproduct)
    write_document(restored, output, allow_carrier=True)
    reversed_document = read_sldprt(output)
    assert reversed_document.brep_payloads == source.brep_payloads
    assert reversed_document.assembly == source.assembly


@pytest.mark.parametrize("change", ("capabilities", "metadata", "diagnostics"))
def test_semantic_edits_disable_exact_source_replay(change: str) -> None:
    document = read_sldprt(SAMPLE)
    if change == "capabilities":
        changed = replace(
            document,
            capabilities=document.capabilities | {Capability.MATERIALS},
        )
    elif change == "metadata":
        changed = replace(
            document,
            metadata=frozen_mapping({**document.metadata, "user.tag": "changed"}),
        )
    else:
        changed = replace(
            document,
            diagnostics=(
                *document.diagnostics,
                Diagnostic("user.changed", "changed", Severity.INFO),
            ),
        )
    output = BytesIO()
    result = write_sldprt(changed, output)
    assert result.metadata["mode"] != "exact"
    assert output.getvalue() != SAMPLE.read_bytes()
    restored = read_sldprt(output.getvalue())
    if change == "capabilities":
        assert Capability.MATERIALS in restored.capabilities
    elif change == "metadata":
        assert restored.metadata["user.tag"] == "changed"
    else:
        assert restored.diagnostics[-1].code == "user.changed"


def test_recomputed_source_semantic_digest_cannot_forge_native_exact_replay() -> None:
    document = read_sldprt(SAMPLE)
    feature = document.feature_timeline[0]
    changed = replace(
        document,
        feature_timeline=(
            replace(feature, name="Forged metadata cannot certify native semantics"),
            *document.feature_timeline[1:],
        ),
    )
    changed = replace(
        changed,
        metadata=frozen_mapping(
            {
                **changed.metadata,
                "solidworks_source_semantic_sha256": _semantic_sha256(changed),
            }
        ),
    )
    output = BytesIO()
    result = write_sldprt(changed, output)
    assert result.metadata["mode"] == "template"
    assert result.metadata["compatibility"] == "native-source-with-kit-neutral"
    assert output.getvalue() != SAMPLE.read_bytes()
    assert read_sldprt(output.getvalue()).feature_timeline[0].name == (
        "Forged metadata cannot certify native semantics"
    )


def test_freecad_document_writes_structural_solidworks_container(tmp_path) -> None:
    source = document()
    fcstd = tmp_path / "neutral.FCStd"
    output = tmp_path / "neutral.SLDPRT"
    write_freecad(source, fcstd)
    restored = read_freecad(fcstd)
    with pytest.raises(SldprtFormatError, match="allow_non_native"):
        write_sldprt(restored, output, allow_non_native=False)
    result = write_sldprt(restored, output)
    archive = SldprtArchive.open(output)
    assert archive.format_version == 4
    assert archive.require("Kit/Interchange")
    keywords = archive.require(KEYWORDS_STREAM)
    resolved_features = archive.require(RESOLVED_FEATURES_STREAM)
    features = archive.require(FEATURES_STREAM)
    assert keywords.startswith(b"\x86<?xml")
    assert features.startswith(b"<?xml")
    native = decode_native_model(keywords, resolved_features)
    assert native.diagnostics == ()
    assert [(item.name, item.configuration_id) for item in native.configurations] == [
        ("Default", 0)
    ]
    assert [item.name for item in native.features[-2:]] == ["Sketch1", "Boss1"]
    assert [(item.name, item.support_plane_id) for item in native.sketches] == [
        ("Sketch1", 2)
    ]
    assert [(item.name, item.profile_id) for item in native.operations] == [
        ("Boss1", native.sketches[0].object_id)
    ]
    assert output.read_bytes()[:1] not in {b"{", b"["}
    assert output.read_bytes()[:4] != b"PK\x03\x04"
    reread = read_sldprt(output)
    assert reread.configurations == source.configurations
    assert reread.support_planes == source.support_planes
    assert reread.sketches == source.sketches
    assert reread.feature_timeline == source.feature_timeline
    assert reread.bodies == source.bodies
    assert result.metadata["mode"] == "generated"
    assert result.metadata["native_content"] == "native-metadata"
    assert result.metadata["compatibility"] == "native-metadata-with-kit-neutral"
    assert result.metadata["neutral_edits_are_native"] is False
    assert result.metadata["vendor_loadable"] is False
    assert result.metadata["native_geometry"] is False
    assert result.metadata["native_history"] is False
    assert result.metadata["native_assembly"] is False
    assert result.metadata["native_self_contained"] is False
    assert result.metadata["referenced_files_written"] == 0
    assert [item.code for item in result.diagnostics] == ["sldprt.neutral_write"]
    replay = BytesIO()
    replay_result = write_sldprt(reread, replay)
    assert replay.getvalue() == output.read_bytes()
    assert replay_result.metadata["compatibility"] == "native-metadata-with-kit-neutral"
    assert replay_result.metadata["vendor_loadable"] is False


def test_source_less_native_part_streams_are_deterministic() -> None:
    first = BytesIO()
    second = BytesIO()
    write_sldprt(document(), first)
    write_sldprt(document(), second)
    assert first.getvalue() == second.getvalue()
    archive = SldprtArchive.from_bytes(first.getvalue())
    content_types = archive.require(CONTENT_TYPES_STREAM)
    relationships = archive.require(RELATIONSHIPS_STREAM)
    assert len(content_types) == 556
    assert len(relationships) == 597
    assert ET.fromstring(content_types).tag.endswith("Types")
    targets = {
        item.attrib["Target"]
        for item in ET.fromstring(relationships)
        if item.tag.endswith("Relationship")
    }
    assert targets == {
        "docProps/app.xml",
        "docProps/core.xml",
        "docProps/custom.xml",
    }
    assert targets <= set(archive.streams)
    assert len(archive.require("docProps/app.xml")) == 570
    assert b"<dc:lastModifiedBy>Kit</dc:lastModifiedBy>" in archive.require(
        "docProps/core.xml"
    )
    assert len(archive.require("docProps/custom.xml")) == 853
    keywords = archive.require(KEYWORDS_STREAM)
    features = archive.require(FEATURES_STREAM)
    assert keywords.startswith(
        b'\x86<?xml version="1.0" encoding="UTF-8"?>\r\n<Keywords '
    )
    assert keywords.endswith(b"</Keywords>\r\n")
    assert features.startswith(
        b'<?xml version="1.0" encoding="UTF-8"?>\r\n<swSolidWorks '
    )
    assert features.endswith(b"</swSolidWorks>\r\n")
    assert b" />" not in keywords
    assert b" />" not in features
    keyword_root = ET.fromstring(keywords[keywords.find(b"<") :])
    features_root = ET.fromstring(features)
    assert keyword_root.tag == "Keywords"
    assert keyword_root.attrib["Name"] == "Part1"
    assert features_root.tag.rsplit("}", 1)[-1] == "swSolidWorks"
    assert features_root.attrib == {"swObjCount": "3", "swVersion": "18000"}
    native_elements = {
        item.tag.rsplit("}", 1)[-1]: item for item in features_root.iter()
    }
    native_file = native_elements["swFile"]
    native_model = native_elements["swModel"]
    native_configuration = native_elements["swConfiguration"]
    assert keyword_root.attrib["id"] == native_file.attrib["swCreationTime"]
    assert native_file.attrib["swPath"] == "memory.sldprt"
    assert native_model.attrib["swName"] == "memory"
    assert native_model.attrib["swConfigurationFlags"] == "-2143288960"
    assert native_configuration.attrib["swReference"] == "Part1"
    assert native_configuration.attrib["swConfigurationNeedsUpdate"] == "NO"
    model_stamps = struct.unpack("<III", archive.require("ModelStamps"))
    assert model_stamps == (
        int(keyword_root.attrib["id"]),
        int(native_model.attrib["swLastModifiedStamp"]),
        101,
    )
    assert archive.require("Contents/CnfgObjs") == bytes.fromhex(
        "00000000fffeff00fffeff00"
    )
    assert archive.require("Contents/OleItems") == b"\0" * 4
    assert archive.require("Contents/eModelLic") == b"\0" * 4
    assert len(archive.require("Contents/CusProps")) == 102
    assert len(archive.require("Contents/CMgrHdr2")) == 137
    assert len(archive.require("_MO_VERSION_18000/History")) == 101
    assert archive.require("_MO_VERSION_18000/Biography")


def test_source_less_blank_part_writes_native_blank_partition() -> None:
    marker = b"blank-part"
    source = replace(
        _document_without_source(document()),
        sketches=(),
        feature_timeline=(),
        bodies=(),
        brep_payloads=(
            BrepPayload(
                "blank-part",
                "kit",
                "blank",
                "1",
                hashlib.sha256(marker).hexdigest(),
                data=marker,
                role=PayloadRole.AUXILIARY,
            ),
        ),
        capabilities=frozenset(),
    )
    output = BytesIO()
    write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    assert archive.require(PARTITION_STREAM) == encode_blank_partition_stream()


def test_source_less_native_system_features_are_emitted_once() -> None:
    source = _document_without_source(read_sldprt(PISTON_RING, include_brep=False))
    output = BytesIO()
    write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    native = decode_native_model(
        archive.require(KEYWORDS_STREAM), archive.require(RESOLVED_FEATURES_STREAM)
    )
    system_ids = {
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        21,
        22,
        23,
        24,
        25,
    }
    assert {item.object_id for item in native.features if item.object_id <= 25} == (
        system_ids
    )
    assert all(
        sum(item.object_id == object_id for item in native.features) == 1
        for object_id in system_ids
    )
    assert [
        (item.object_id, item.name) for item in native.features if item.object_id > 25
    ] == [(26, "Sketch1"), (36, "Boss-Extrude1")]
    sketch = next(item for item in native.features if item.object_id == 26)
    extrusion = next(item for item in native.features if item.object_id == 36)
    assert sketch.properties == {
        "id": "26",
        "Name": "Sketch1",
        "Dissectable": "true",
    }
    assert [(item.name, item.source_text) for item in sketch.dimensions] == [
        ("D1", "<MOD-DIAM>90"),
        ("D2", "<MOD-DIAM>89"),
    ]
    assert extrusion.properties == {
        "id": "36",
        "Name": "Boss-Extrude1",
        "Type": "Boss-Extrude",
    }
    assert [(item.name, item.source_text) for item in extrusion.dimensions] == [
        ("D1", "1")
    ]
    configurations = ET.fromstring(
        archive.require(KEYWORDS_STREAM)[archive.require(KEYWORDS_STREAM).find(b"<") :]
    )
    configuration = next(item for item in configurations if item.tag == "Configuration")
    assert configuration.attrib["Material"] == "Rubber"


def test_source_less_native_dimension_scalar_roundtrips() -> None:
    source = document()
    feature = source.feature_timeline[0]
    value = ParameterValue(12.5, ValueKind.LENGTH, "mm")
    parameter = Parameter("length", "D1", value, owner_id=feature.id)
    feature = replace(
        feature,
        parameter_ids=(parameter.id,),
        operation=BooleanOperation.JOIN,
        definition=ExtrusionFeature(value),
    )
    source = replace(source, parameters=(parameter,), feature_timeline=(feature,))
    output = BytesIO()
    result = write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    native = decode_native_model(
        archive.require(KEYWORDS_STREAM), archive.require(RESOLVED_FEATURES_STREAM)
    )
    operation = next(item for item in native.operations if item.name == feature.name)
    dimension = next(
        dimension
        for native_feature in native.features
        if native_feature.object_id == operation.object_id
        for dimension in native_feature.dimensions
        if dimension.name == "D1"
    )
    assert operation.length_mm == pytest.approx(12.5)
    assert operation.operation_code == 0
    assert operation.termination_code == 0
    assert dimension.native_value == pytest.approx(0.0125)
    assert dimension.native_role == "driving"
    assert Capability.PARAMETERS in result.native_capabilities
    assert result.vendor_loadable is False


def test_source_less_native_configuration_lanes_are_complete() -> None:
    source = replace(
        document(),
        configurations=(
            Configuration("config:default", "Default"),
            Configuration("config:machined", "Machined", True),
        ),
    )
    output = BytesIO()
    result = write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    assert archive.require("Contents/Config-0-ResolvedFeatures")
    assert archive.require("Contents/Config-1-ResolvedFeatures")
    features = ET.fromstring(archive.require(FEATURES_STREAM))
    configurations = [
        item
        for item in features.iter()
        if item.tag.rsplit("}", 1)[-1] == "swConfiguration"
    ]
    assert [item.attrib["swName"] for item in configurations] == [
        "Default",
        "Machined",
    ]
    assert [item.attrib["swMostRecentConfiguration"] for item in configurations] == [
        "NO",
        "YES",
    ]
    assert {item.attrib["swConfigurationNeedsUpdate"] for item in configurations} == {
        "NO"
    }
    assert Capability.CONFIGURATIONS in result.native_capabilities


def test_source_less_native_rectangle_markers_roundtrip() -> None:
    source = document()
    points = (
        Vector2(0.0, 0.0),
        Vector2(20.0, 0.0),
        Vector2(20.0, 10.0),
        Vector2(0.0, 10.0),
    )
    entities = tuple(
        SketchEntity(
            f"edge:{index}",
            GeometryKind.LINE,
            LineGeometry(points[index], points[(index + 1) % len(points)]),
        )
        for index in range(len(points))
    )
    sketch = Sketch(
        source.sketches[0].id,
        source.sketches[0].name,
        source.sketches[0].support_plane_id,
        entities,
        closed_profile_entity_ids=(tuple(item.id for item in entities),),
    )
    source = replace(source, sketches=(sketch,))
    output = BytesIO()
    write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    native = decode_native_model(
        archive.require(KEYWORDS_STREAM), archive.require(RESOLVED_FEATURES_STREAM)
    )
    decoded = next(item for item in native.sketches if item.name == sketch.name)
    assert len(decoded.markers) == 8
    assert [(item.kind, item.coordinates) for item in decoded.profiles] == [
        ("rectangle", (0.0, 0.0, 20.0, 10.0))
    ]


def test_source_less_native_rectangle_boss_records_are_parametric() -> None:
    source = document()
    points = (
        Vector2(-30.0, -15.0),
        Vector2(30.0, -15.0),
        Vector2(30.0, 15.0),
        Vector2(-30.0, 15.0),
    )
    entities = tuple(
        SketchEntity(
            f"edge:{index}",
            GeometryKind.LINE,
            LineGeometry(points[index], points[(index + 1) % len(points)]),
        )
        for index in range(len(points))
    )
    sketch = Sketch(
        source.sketches[0].id,
        source.sketches[0].name,
        source.sketches[0].support_plane_id,
        entities,
        closed_profile_entity_ids=(tuple(item.id for item in entities),),
    )
    length = ParameterValue(12.0, ValueKind.LENGTH, "mm")
    feature = replace(source.feature_timeline[0], definition=ExtrusionFeature(length))
    source = replace(source, sketches=(sketch,), feature_timeline=(feature,))
    output = BytesIO()
    write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    resolved = archive.require(RESOLVED_FEATURES_STREAM)
    native = decode_native_model(archive.require(KEYWORDS_STREAM), resolved)
    assert len(resolved) == 11285
    assert native.sketches[0].object_id == 26
    assert native.sketches[0].profiles[0].coordinates == (
        -30.0,
        -15.0,
        30.0,
        15.0,
    )
    assert native.operations[0].object_id == 32
    assert native.operations[0].name == "Boss-Extrude1"
    assert native.operations[0].length_mm == pytest.approx(12.0)
    assert struct.unpack_from("<d", resolved, 10092)[0] == pytest.approx(0.012)


def test_neutral_brep_writes_native_parasolid_partition() -> None:
    base = document()
    source = replace(
        base,
        brep=triangle_brep(),
        capabilities=base.capabilities | {Capability.BREP},
    )
    output = BytesIO()
    result = write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    partition = archive.require(PARTITION_STREAM)
    native = decode_partition_stream(partition)[0]
    restored = read_sldprt(output.getvalue())
    assert native.schema == "SCH_1200000_12006"
    assert native.data == encode_brep_model(source.brep)
    assert partition != native.data
    assert restored.brep == source.brep
    assert result.metadata["mode"] == "generated"
    assert result.metadata["native_content"] == "native-metadata-and-neutral-brep"
    assert result.metadata["compatibility"] == "native-brep-with-kit-neutral"
    assert result.metadata["native_brep"] == "generated"
    assert result.metadata["native_geometry"] is True
    assert result.metadata["native_history"] is False
    assert result.metadata["native_assembly"] is False
    assert result.metadata["vendor_loadable"] is False


def test_source_less_brep_only_writes_native_imported_feature_metadata() -> None:
    base = document()
    feature = replace(
        base.feature_timeline[0],
        name="Imported1",
        kind="imported",
        sketch_id=None,
        attributes=frozen_mapping({"native_object_id": 26, "native_type": "Imported"}),
    )
    body = replace(base.bodies[0], final_feature_id=feature.id)
    source = replace(
        base,
        support_planes=(),
        sketches=(),
        feature_timeline=(feature,),
        bodies=(body,),
        brep=triangle_brep(),
        capabilities=frozenset({Capability.BREP}),
    )
    output = BytesIO()
    write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    resolved = archive.require(RESOLVED_FEATURES_STREAM)
    native = decode_native_model(archive.require(KEYWORDS_STREAM), resolved)
    imported = next(item for item in native.features if item.object_id == 26)
    classes = {item.offset: item.name for item in native.classes}
    assert imported.name == "Imported1"
    assert imported.kind == "Imported"
    assert classes[imported.native_offset - 18] == "moBaseBody_c"
    assert len(resolved) == 5913
    assert resolved[0] == 0x6B
    assert resolved[4] == 0x12
    assert resolved[1495] == 0x80
    assert resolved[5302] == 0x52


def test_public_sdk_does_not_promote_generated_parasolid_partition(tmp_path) -> None:
    base = document()
    source = replace(
        base,
        brep=triangle_brep(),
        capabilities=base.capabilities | {Capability.BREP},
    )
    blocked = tmp_path / "blocked.SLDPRT"
    with pytest.raises(ApplicationUsabilityError) as captured:
        write_document(source, blocked, allow_carrier=False)
    assert Capability.BREP in captured.value.unimplemented_capabilities
    assert not blocked.exists()
    explicit = tmp_path / "explicit.SLDPRT"
    result = write_document(source, explicit, allow_carrier=True)
    assert result.metadata["native_brep"] == "generated"
    assert result.vendor_loadable is False
    assert result.near_lossless is False
    assert open_document(explicit).brep == source.brep


def test_parasolid_partition_decodes_to_kernel_neutral_brep() -> None:
    encoded = encode_brep_model(triangle_brep())
    decoded = decode_brep_model(encoded)
    assert decoded is not None
    assert decoded.validate() == ()
    assert len(decoded.bodies) == 1
    assert len(decoded.faces) == 1
    assert len(decoded.edges) == 3
    assert len(decoded.vertices) == 3
    assert {vertex.point for vertex in decoded.vertices} == {
        vertex.point for vertex in triangle_brep().vertices
    }


def test_native_sldprt_read_preserves_partition_and_adds_typed_brep() -> None:
    encoded = encode_brep_model(triangle_brep())
    source = SldprtArchive.open(SAMPLE)
    streams = source.streams
    streams[PARTITION_STREAM] = encoded
    streams.pop("Contents/Config-0-GhostPartition", None)
    native = build_sldprt(
        streams,
        file_id=source.file_id,
        format_version=source.format_version,
    )
    decoded = read_sldprt(native)
    assert decoded.brep is not None
    assert decoded.brep.validate() == ()
    assert len(decoded.brep_payloads) == 1
    assert decoded.brep_payloads[0].data == encoded


def test_parasolid_decoder_rejects_open_topology_and_deltas() -> None:
    encoded = encode_brep_model(triangle_brep())
    broken = bytearray(encoded)
    header = _parasolid_header(encoded)
    assert header is not None
    tables = _scan_partition_records(encoded[header.body_offset :])
    assert tables is not None
    loop = next(iter(tables.loops.values()))
    struct.pack_into(">H", broken, header.body_offset + loop.offset + 10, 1)
    assert decode_brep_model(broken) is None
    deltas = encoded.replace(b"partition", b"deltasxxx", 1)
    assert decode_brep_model(deltas) is None


def test_native_sldprt_include_brep_false_omits_typed_and_raw_geometry() -> None:
    encoded = encode_brep_model(triangle_brep())
    source = SldprtArchive.open(SAMPLE)
    streams = source.streams
    streams[PARTITION_STREAM] = encoded
    streams.pop("Contents/Config-0-GhostPartition", None)
    native = build_sldprt(
        streams,
        file_id=source.file_id,
        format_version=source.format_version,
    )
    decoded = read_sldprt(native, include_brep=False)
    assert decoded.brep is None
    assert decoded.brep_payloads == ()


def test_unsupported_neutral_brep_remains_an_honest_carrier() -> None:
    base = document()
    brep = triangle_brep()
    unsupported = replace(
        brep,
        surfaces=(NativeSurface("surface:0", "future.cad", "future-surface"),),
    )
    source = replace(
        base,
        brep=unsupported,
        capabilities=base.capabilities | {Capability.BREP},
    )
    output = BytesIO()
    result = write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    restored = read_sldprt(output.getvalue())
    assert archive.get(PARTITION_STREAM) is None
    assert restored.brep == source.brep
    assert result.metadata["native_content"] == "native-metadata"
    assert result.metadata["native_brep"].startswith("unsupported:")
    assert result.metadata["native_geometry"] is False
    assert result.metadata["vendor_loadable"] is False
    assert result.diagnostics[-1].code == "sldprt.native_brep_unsupported"


def test_generated_carrier_include_brep_filter_retains_non_geometry_payloads(
    tmp_path,
) -> None:
    base = document()
    source = replace(
        base,
        brep_payloads=(
            BrepPayload(
                "geometry",
                "future.kernel",
                "body",
                "1",
                "",
                data=b"geometry",
                role=PayloadRole.BREP,
                file_extension=".geo",
            ),
            BrepPayload(
                "history",
                "future.cad",
                "feature-records",
                "1",
                "",
                data=b"history",
                role=PayloadRole.FEATURE_HISTORY,
            ),
        ),
        capabilities=base.capabilities
        | frozenset({Capability.BREP, Capability.NATIVE_PAYLOADS}),
    )
    target = tmp_path / "payloads.SLDPRT"
    write_sldprt(source, target)
    without_brep = read_sldprt(target, include_brep=False)
    assert [payload.id for payload in without_brep.brep_payloads] == ["history"]
    assert without_brep.brep_payloads[0].data == b"history"
    assert without_brep.capabilities == source.capabilities - {Capability.BREP}
    with_brep = read_sldprt(target, include_brep=True)
    assert [payload.id for payload in with_brep.brep_payloads] == [
        "geometry",
        "history",
    ]
    assert with_brep.capabilities == source.capabilities


@pytest.mark.parametrize("source", (document(), assembly_document()))
def test_generated_carrier_preserves_declared_sparse_capabilities(source) -> None:
    output = BytesIO()
    write_sldprt(source, output)
    restored = read_sldprt(output.getvalue())
    assert restored.capabilities == source.capabilities
    if source.assembly is not None:
        assert restored.assembly is not None
        assert tuple(
            item.document.capabilities
            for item in restored.assembly.documents
            if item.document is not None
        ) == tuple(
            item.document.capabilities
            for item in source.assembly.documents
            if item.document is not None
        )


@pytest.mark.parametrize(
    ("payload_index", "changes"),
    (
        (0, {"data": b"changed document"}),
        (1, {"data": b"changed binding"}),
        (0, {"id": "changed-document"}),
        (1, {"id": "changed-binding"}),
    ),
)
def test_foreign_document_payload_mutation_invalidates_outer_replay(
    payload_index: int, changes: dict[str, bytes | str]
) -> None:
    source = replace(
        document(),
        brep_payloads=(
            BrepPayload(
                "foreign-document",
                "future.cad.document",
                "native_document",
                "v1",
                "",
                data=b"original document",
                role=PayloadRole.DOCUMENT,
                file_extension=".cad",
            ),
            BrepPayload(
                "foreign-binding",
                "future.cad.sha256",
                "native_document_binding",
                "sha256",
                "",
                data=b"original binding",
                role=PayloadRole.VERIFICATION,
                file_extension=".sha256",
            ),
        ),
    )
    carrier = BytesIO()
    write_sldprt(source, carrier)
    original = carrier.getvalue()
    restored = read_sldprt(original)
    payloads = list(restored.brep_payloads)
    payloads[payload_index] = replace(payloads[payload_index], **changes)
    mutated = replace(
        restored,
        brep_payloads=tuple(payloads),
    )
    output = BytesIO()
    result = write_sldprt(mutated, output)
    assert result.metadata["mode"] == "template"
    assert output.getvalue() != original
    reread = read_sldprt(output.getvalue())
    changed = reread.brep_payloads[payload_index]
    for key, value in changes.items():
        assert getattr(changed, key) == value


def test_semantic_edit_uses_native_template_without_claiming_native_edit(
    tmp_path,
) -> None:
    source = read_sldprt(SAMPLE)
    edited_feature = replace(source.feature_timeline[0], name="Edited in Kit")
    edited = replace(
        source,
        feature_timeline=(edited_feature, *source.feature_timeline[1:]),
    )
    output = tmp_path / "edited.SLDPRT"
    with pytest.raises(SldprtFormatError, match="allow_non_native"):
        write_sldprt(edited, output, allow_non_native=False)
    result = write_sldprt(edited, output)
    original_archive = SldprtArchive.open(SAMPLE)
    edited_archive = SldprtArchive.open(output)
    assert output.read_bytes() != SAMPLE.read_bytes()
    assert set(original_archive.streams) <= set(edited_archive.streams)
    assert edited_archive.require("Kit/Interchange")
    assert read_sldprt(output).feature_timeline[0].name == "Edited in Kit"
    assert result.metadata["mode"] == "template"
    assert result.metadata["native_content"] == "source-preserved"
    assert result.metadata["compatibility"] == "native-source-with-kit-neutral"
    assert result.metadata["neutral_edits_are_native"] is False
    assert result.diagnostics[-1].code == "sldprt.neutral_write"


def test_native_template_patches_driving_dimension_without_carrier_opt_in(
    tmp_path,
) -> None:
    source = read_sldprt(SAMPLE)
    parameter = source.parameters[0]
    target_value = float(parameter.value.value) + 1.25
    edited = replace(
        source,
        parameters=(
            replace(parameter, value=replace(parameter.value, value=target_value)),
            *source.parameters[1:],
        ),
    )
    output = tmp_path / "dimension.SLDPRT"
    result = write_document(edited, output)
    assert result.application_usable is True
    assert result.vendor_loadable is True
    assert result.near_lossless is True
    assert result.metadata["compatibility"] == "native-template"
    assert {
        Capability.PARAMETERS,
        Capability.PARAMETRIC_HISTORY,
        Capability.EDITABLE_SKETCHES,
    } <= result.native_capabilities
    archive = SldprtArchive.open(output)
    streams = archive.streams
    streams.pop(KIT_DOCUMENT_STREAM)
    streams.pop(KIT_NATIVE_STREAM)
    native = read_sldprt(
        build_sldprt(
            streams,
            file_id=archive.file_id,
            format_version=archive.format_version,
        )
    )
    native_parameter = next(
        item for item in native.parameters if item.id == parameter.id
    )
    assert native_parameter.value.value == pytest.approx(target_value)


def test_recomputed_attestation_cannot_forge_native_template_claims(
    tmp_path,
) -> None:
    source = read_sldprt(SAMPLE)
    parameter = source.parameters[0]
    native_value = float(parameter.value.value) + 1.25
    native_document = replace(
        source,
        parameters=(
            replace(parameter, value=replace(parameter.value, value=native_value)),
            *source.parameters[1:],
        ),
    )
    trusted = tmp_path / "trusted.SLDPRT"
    trusted_result = write_document(native_document, trusted)
    assert trusted_result.metadata["compatibility"] == "native-template"
    archive = SldprtArchive.open(trusted)
    streams = archive.streams
    embedded = CadDocument.from_json(streams[KIT_DOCUMENT_STREAM].decode("utf-8"))
    embedded_parameter = embedded.parameters[0]
    forged_value = native_value + 7.5
    forged_document = replace(
        embedded,
        parameters=(
            replace(
                embedded_parameter,
                value=replace(embedded_parameter.value, value=forged_value),
            ),
            *embedded.parameters[1:],
        ),
    )
    forged_manifest = forged_document.to_json(indent=None).encode("utf-8")
    streams[KIT_DOCUMENT_STREAM] = forged_manifest
    attestation = json.loads(streams[KIT_NATIVE_STREAM].decode("utf-8"))
    attestation["embedded_sha256"] = hashlib.sha256(forged_manifest).hexdigest()
    attestation["semantic_sha256"] = _semantic_sha256(forged_document)
    attestation["native_stream_sha256"] = _native_stream_sha256(streams)
    streams[KIT_NATIVE_STREAM] = json.dumps(
        attestation, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    forged = build_sldprt(
        streams,
        file_id=archive.file_id,
        format_version=archive.format_version,
    )
    restored = read_sldprt(forged)
    assert restored.parameters[0].value.value == pytest.approx(forged_value)
    blocked = tmp_path / "blocked.SLDPRT"
    with pytest.raises(ApplicationUsabilityError):
        write_document(restored, blocked, allow_carrier=False)
    assert not blocked.exists()
    output = tmp_path / "carrier.SLDPRT"
    result = write_document(restored, output)
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert result.metadata["compatibility"] == "kit-neutral-only"
    assert result.near_lossless is False
    assert output.read_bytes() == forged


def test_attestation_cannot_promote_kit_stream_to_native_exact(tmp_path) -> None:
    source = read_sldprt(SAMPLE)
    parameter = source.parameters[0]
    edited = replace(
        source,
        parameters=(
            replace(
                parameter,
                value=replace(
                    parameter.value,
                    value=float(parameter.value.value) + 1.25,
                ),
            ),
            *source.parameters[1:],
        ),
    )
    trusted = tmp_path / "trusted.SLDPRT"
    write_document(edited, trusted)
    archive = SldprtArchive.open(trusted)
    streams = archive.streams
    attestation = json.loads(streams[KIT_NATIVE_STREAM].decode("utf-8"))
    attestation["compatibility"] = "native-exact"
    attestation["application_usable"] = False
    attestation["vendor_loadable"] = False
    streams[KIT_NATIVE_STREAM] = json.dumps(
        attestation, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    forged = build_sldprt(
        streams,
        file_id=archive.file_id,
        format_version=archive.format_version,
    )
    restored = read_sldprt(forged)
    blocked = tmp_path / "blocked.SLDPRT"
    with pytest.raises(ApplicationUsabilityError):
        write_document(restored, blocked, allow_carrier=False)
    assert not blocked.exists()
    output = tmp_path / "carrier.SLDPRT"
    result = write_document(restored, output)
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert result.metadata["compatibility"] == "kit-neutral-only"
    assert result.carrier_capabilities == result.transferred_capabilities


def test_native_template_patches_same_width_feature_name(tmp_path) -> None:
    source = read_sldprt(SAMPLE)
    feature = source.feature_timeline[0]
    target_name = "X" * len(feature.name)
    edited = replace(
        source,
        feature_timeline=(
            replace(feature, name=target_name),
            *source.feature_timeline[1:],
        ),
    )
    output = tmp_path / "feature-name.SLDPRT"
    result = write_document(edited, output)
    assert result.near_lossless is True
    archive = SldprtArchive.open(output)
    streams = archive.streams
    streams.pop(KIT_DOCUMENT_STREAM)
    streams.pop(KIT_NATIVE_STREAM)
    native = read_sldprt(
        build_sldprt(
            streams,
            file_id=archive.file_id,
            format_version=archive.format_version,
        )
    )
    assert native.feature_timeline[0].name == target_name


def test_solidworks_aliases_enforce_document_kind(tmp_path) -> None:
    adapter = registry.writer("solidworks.sldprt")
    assert registry.reader("solidworks.sldasm") is registry.reader("solidworks.sldprt")
    assert registry.writer("solidworks.sldasm") is adapter
    assert "solidworks.sldasm" in registry.format_ids()
    part = document()
    assembly = assembly_document()
    assert adapter.supports(part, tmp_path / "part.SLDPRT")
    assert not adapter.supports(part, tmp_path / "part.SLDASM")
    assert adapter.supports(assembly, tmp_path / "assembly.SLDASM")
    assert not adapter.supports(assembly, tmp_path / "assembly.SLDPRT")
    assert adapter.supports(part, BytesIO())
    assert not adapter.supports(part, StringIO())
    with pytest.raises(ValueError, match=r"\.SLDPRT"):
        write_sldprt(part, tmp_path / "part.SLDASM")
    with pytest.raises(ValueError, match=r"\.SLDASM"):
        write_sldprt(assembly, tmp_path / "assembly.SLDPRT")
    result = write_sldprt(
        assembly,
        tmp_path / "assembly.SLDASM",
        allow_non_native=True,
    )
    assert result.adapter == "solidworks.sldasm"
    assert result.metadata["format_id"] == "solidworks.sldasm"
    assembly_json = assembly.write_json(tmp_path / "assembly.json")
    part_json = part.write_json(tmp_path / "part.json")
    with pytest.raises(ValueError, match="does not support this document kind"):
        convert(
            part_json,
            BytesIO(),
            destination_format="solidworks.sldasm",
        )
    with pytest.raises(ValueError, match="does not support this document kind"):
        convert(
            assembly_json,
            BytesIO(),
            destination_format="solidworks.sldprt",
        )
    with pytest.raises(ValueError, match="does not support this document kind"):
        convert(
            part_json,
            tmp_path / "explicit.SLDPRT",
            destination_format="solidworks.sldasm",
        )
    conversion = convert(
        assembly_json,
        tmp_path / "converted.SLDASM",
        destination_format="solidworks.sldasm",
        allow_carrier=True,
    )
    assert conversion.destination_format == "solidworks.sldasm"


@pytest.mark.parametrize(
    ("source", "wrong_suffix"),
    ((SAMPLE, ".SLDASM"), (ASSEMBLY, ".SLDPRT")),
)
def test_solidworks_reader_rejects_native_suffix_kind_mismatch(
    source, wrong_suffix, tmp_path
) -> None:
    renamed = tmp_path / f"renamed{wrong_suffix}"
    renamed.write_bytes(source.read_bytes())
    with pytest.raises(SldprtFormatError, match="content requires"):
        read_sldprt(renamed)


def test_solidworks_reader_rejects_carrier_suffix_kind_mismatch(tmp_path) -> None:
    valid = tmp_path / "valid.SLDPRT"
    write_sldprt(document(), valid)
    renamed = tmp_path / "renamed.SLDASM"
    renamed.write_bytes(valid.read_bytes())
    with pytest.raises(SldprtFormatError, match="content requires"):
        read_sldprt(renamed)


def test_generated_sldasm_stream_retains_assembly_identity() -> None:
    source = assembly_document()
    output = BytesIO()
    result = write_sldprt(source, output)
    restored = read_sldprt(output.getvalue())
    assert result.adapter == "solidworks.sldasm"
    assert restored.source.format_id == "solidworks.sldasm"
    assert restored.assembly == source.assembly


def test_source_less_assembly_emits_redecodable_native_component_graph() -> None:
    source = assembly_document()
    output = BytesIO()
    result = write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    native = decode_native_assembly(archive)
    transfers = {item.capability: item.mode.value for item in result.transfers}
    assert COMPONENT_TREE_STREAM in archive.streams
    assert transfers[Capability.ASSEMBLIES] == "native"
    assert transfers[Capability.ASSEMBLY_MATES] == "carrier"
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert native.name == "Engine"
    assert tuple(item.name for item in native.definitions) == (
        "Engine",
        "Piston",
        "Piston",
    )
    assert tuple(item.document_type for item in native.definitions) == (
        "ASSEMBLY",
        "ASSEMBLY",
        "PART",
    )
    assert native.occurrences[0].transform[12:15] == (0.1, 0.02, 0.03)


def test_source_less_assembly_encodes_only_exactly_redecodable_mates() -> None:
    source = assembly_document()
    assembly = source.assembly
    component_entity, root_entity = assembly.mate_entities
    component_entity = replace(
        component_entity,
        id="mate-entity:component",
        instance_path=("instance:subassembly", "instance:part"),
        source_entity_id="moPlaneSurfIdRep_c,1,2, ",
        attributes=frozen_mapping(
            {"persistent_references": ("moPlaneSurfIdRep_c,1,2, ",)}
        ),
    )
    root_entity = replace(
        root_entity,
        id="mate-entity:root",
        instance_path=(),
        source_entity_id="moPlaneSurfIdRep_c,3,4, ",
        attributes=frozen_mapping(
            {"persistent_references": ("moPlaneSurfIdRep_c,3,4, ",)}
        ),
    )
    mate = replace(
        assembly.mates[0],
        entity_ids=(component_entity.id, root_entity.id),
        alignment=MateAlignment.ALIGNED,
    )
    source = replace(
        source,
        assembly=replace(
            assembly,
            mate_entities=(component_entity, root_entity),
            mates=(mate,),
        ),
    )
    output = BytesIO()
    result = write_sldprt(source, output)
    native = decode_native_assembly(SldprtArchive.from_bytes(output.getvalue()))
    transfers = {item.capability: item.mode.value for item in result.transfers}
    assert transfers[Capability.ASSEMBLY_MATES] == "native"
    assert len(native.mate_lists) == 1
    assert native.mate_lists[0].declared_count == 1
    restored = native.mate_lists[0].mates[0]
    assert restored.name == "Coincident1"
    assert restored.kind == "coincident"
    assert restored.alignment_code == 1
    assert tuple(
        (
            entity.component_path,
            entity.persistent_references[-1],
        )
        for entity in restored.entities
    ) == (
        (
            "Piston-1@Engine/Piston-1@Piston",
            "moPlaneSurfIdRep_c,1,2, ",
        ),
        ("", "moPlaneSurfIdRep_c,3,4, "),
    )


def test_source_less_native_mate_payload_is_replayed_without_template() -> None:
    source = _document_without_source(read_sldprt(CONROD))
    output = BytesIO()
    result = write_sldprt(source, output)
    native = decode_native_assembly(SldprtArchive.from_bytes(output.getvalue()))
    transfers = {item.capability: item.mode.value for item in result.transfers}
    assert transfers[Capability.ASSEMBLY_MATES] == "native"
    assert sum(len(item.mates) for item in native.mate_lists) == len(
        source.assembly.mates
    )
    assert tuple(
        mate.name for item in native.mate_lists for mate in item.mates
    ) == tuple(mate.name for mate in source.assembly.mates)


def test_public_sdk_requires_explicit_carrier_opt_in(tmp_path) -> None:
    source = document()
    direct = tmp_path / "direct.SLDPRT"
    blocked = tmp_path / "blocked.SLDPRT"
    with pytest.raises(ApplicationUsabilityError):
        write_document(source, blocked, allow_carrier=False)
    assert not blocked.exists()
    written = write_document(source, direct, allow_carrier=True)
    assert written.metadata["compatibility"] == "native-metadata-with-kit-neutral"
    fcstd = tmp_path / "source.FCStd"
    converted = tmp_path / "converted.SLDPRT"
    write_freecad(source, fcstd)
    blocked_conversion = tmp_path / "blocked_conversion.SLDPRT"
    with pytest.raises(ApplicationUsabilityError):
        convert(fcstd, blocked_conversion, allow_carrier=False)
    assert not blocked_conversion.exists()
    result = convert(
        fcstd,
        converted,
        allow_carrier=True,
    )
    assert result.destination_format == "solidworks.sldprt"
    assert result.output.metadata["compatibility"] == "native-metadata-with-kit-neutral"


def test_attested_native_template_survives_wrapper_metadata_removal(tmp_path) -> None:
    original = open_document(SAMPLE)
    changed = replace(
        original,
        metadata=frozen_mapping({**original.metadata, "audit_change": True}),
    )
    carrier = tmp_path / "carrier.SLDPRT"
    first = write_document(changed, carrier)
    assert first.vendor_loadable is True
    assert first.near_lossless is True
    assert first.metadata["mode"] == "template"
    restored = open_document(carrier)
    metadata = dict(restored.metadata)
    assert metadata.pop("solidworks.container_compatibility") == "native-template"
    stripped = replace(restored, metadata=frozen_mapping(metadata))
    replay = tmp_path / "replay.SLDPRT"
    result = write_document(stripped, replay)
    assert result.vendor_loadable is True
    assert result.near_lossless is True
    assert replay.read_bytes() == carrier.read_bytes()
    assert open_document(replay).feature_timeline == restored.feature_timeline


def test_public_sdk_defaults_to_portable_assembly_writes(tmp_path) -> None:
    source = read_sldprt(ASSEMBLY)
    portable = tmp_path / "portable.SLDASM"
    portable_result = write_document(source, portable)
    assert portable_result.metadata["compatibility"] == "native-template"
    assert portable_result.metadata["native_self_contained"] is True
    assert portable_result.metadata["referenced_files_written"] == len(
        source.assembly.documents
    )
    assert portable_result.requirements == ()
    assert portable_result.near_lossless is True
    assert read_sldprt(portable).assembly == source.assembly
    exact = tmp_path / "exact.SLDASM"
    exact_result = registry.write(
        source,
        exact,
        options=WriteOptions(
            values={
                "portable": False,
                "allow_carrier": True,
                "require_self_contained": False,
            },
        ),
    )
    assert exact_result.metadata["compatibility"] == "native-exact"
    assert exact_result.metadata["native_self_contained"] is False
    assert exact_result.requirements == ("referenced SOLIDWORKS component files",)
    assert exact_result.near_lossless is False
    assert exact.read_bytes() == ASSEMBLY.read_bytes()


def test_incomplete_portable_assembly_downgrades_to_root_carrier(tmp_path) -> None:
    isolated = tmp_path / "isolated" / ASSEMBLY.name
    isolated.parent.mkdir()
    isolated.write_bytes(ASSEMBLY.read_bytes())
    source = read_sldprt(isolated)
    assert source.assembly is not None
    assert source.assembly.documents == ()
    assert source.meshes
    output = tmp_path / "portable" / ASSEMBLY.name
    result = write_document(source, output)
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert result.metadata["native_self_contained"] is False
    assert result.metadata["referenced_files_written"] == 0
    assert result.requirements == ()
    assert tuple(output.parent.iterdir()) == (output,)
    attestation = json.loads(
        SldprtArchive.open(output).require(KIT_NATIVE_STREAM).decode("utf-8")
    )
    assert attestation["compatibility"] == result.metadata["compatibility"]
    assert attestation["application_usable"] is False
    assert attestation["vendor_loadable"] is False
    restored = read_sldprt(output)
    assert restored.assembly == source.assembly
    assert restored.meshes == source.meshes
    blocked = tmp_path / "blocked" / ASSEMBLY.name
    with pytest.raises(ApplicationUsabilityError) as captured:
        write_document(source, blocked, allow_carrier=False)
    assert captured.value.requirements == ("referenced SOLIDWORKS component files",)
    assert not blocked.exists()


def test_catproduct_defaults_to_relocatable_solidworks_root_carrier(tmp_path) -> None:
    source = open_document(CATPRODUCT)
    output = tmp_path / "converted" / "Tilton_Set.SLDASM"
    result = convert(CATPRODUCT, output)
    assert result.requirements == ()
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert result.output.metadata["native_self_contained"] is False
    assert result.output.metadata["referenced_files_written"] == len(
        source.assembly.documents
    )
    native = decode_native_assembly(SldprtArchive.open(output))
    referenced = tuple(
        output.parent / PureWindowsPath(definition.source_path).name
        for definition in native.definitions
        if definition.object_id != native.root_definition_id
    )
    assert referenced
    assert all(path.is_file() for path in referenced)
    assert all(SldprtArchive.open(path).records for path in referenced)
    relocated = tmp_path / "relocated" / output.name
    relocated.parent.mkdir()
    relocated.write_bytes(output.read_bytes())
    restored = open_document(relocated)
    assert restored.assembly == source.assembly
    assert restored.meshes == source.meshes


def test_portable_assembly_patches_transform_mate_and_linked_part(tmp_path) -> None:
    source = read_sldprt(ASSEMBLY)
    assembly = source.assembly
    instance = assembly.instances[0]
    transform = list(instance.transform.values)
    transform[3] += 12.5
    mate = assembly.mates[0]
    alignment = (
        MateAlignment.ANTI_ALIGNED
        if mate.alignment is MateAlignment.ALIGNED
        else MateAlignment.ALIGNED
    )
    component = assembly.documents[0]
    part = component.document
    parameter = part.parameters[0]
    target_value = float(parameter.value.value) + 0.5
    part = replace(
        part,
        parameters=(
            replace(parameter, value=replace(parameter.value, value=target_value)),
            *part.parameters[1:],
        ),
    )
    edited = replace(
        source,
        assembly=replace(
            assembly,
            instances=(
                replace(instance, transform=Matrix4(tuple(transform))),
                *assembly.instances[1:],
            ),
            mates=(replace(mate, alignment=alignment), *assembly.mates[1:]),
            documents=(replace(component, document=part), *assembly.documents[1:]),
        ),
    )
    output = tmp_path / "edited.SLDASM"
    result = write_document(edited, output)
    assert result.near_lossless is True
    assert result.requirements == ()
    assert result.metadata["referenced_files_written"] == len(assembly.documents)
    restored = read_sldprt(output)
    assert restored.assembly.instances[0].transform == Matrix4(tuple(transform))
    assert restored.assembly.mates[0].alignment is alignment
    assert restored.assembly.documents[0].document.parameters[
        0
    ].value.value == pytest.approx(target_value)
