# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

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
from convert.adapters.solidworks.container import container_signatures
from convert.adapters.solidworks.adapter import (
    _ASSEMBLY_DONOR_CARRIED_STREAMS,
    _document_without_source,
    _native_stream_sha256,
    _semantic_sha256,
)
from convert.adapters.solidworks.cmgr import CONFIGURATION_MANAGER_STREAM
from convert.adapters.solidworks.format import (
    COMPONENT_TREE_STREAM,
    CONFIGURATION_STREAM,
    CONTENT_TYPES_STREAM,
    FEATURES_STREAM,
    KEYWORDS_STREAM,
    KIT_DOCUMENT_STREAM,
    KIT_NATIVE_STREAM,
    KIT_RESOLVED_STREAM,
    PARTITION_STREAM,
    RELATIONSHIPS_STREAM,
    RESOLVED_FEATURES_STREAM,
)
from convert.adapters.solidworks.native import (
    VENDOR_UNLOADABLE_NOTES,
    decode_native_model_header,
    encode_native_part,
    native_axis_bindings,
)
from convert.adapters.solidworks.resolved import BLIND_END_CONDITION, locate_features
from convert.parasolid import _parasolid_header, _scan_partition_records
from interchange import (
    BooleanOperation,
    BrepPayload,
    CadDocument,
    Capability,
    CircleGeometry,
    Configuration,
    Diagnostic,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    GeometryKind,
    LineGeometry,
    MateAlignment,
    Matrix4,
    NativeFeatureDefinition,
    NativeSurface,
    Parameter,
    ParameterValue,
    PayloadRole,
    Provenance,
    Selection,
    SelectionPathElement,
    Severity,
    Sketch,
    SketchEntity,
    Transform,
    ValueKind,
    Vector2,
    Vector3,
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


def _freecad_rectangle_pad_document(
    bounds: tuple[float, float, float, float] = (-30.0, -15.0, 30.0, 15.0),
    depth: float = 12.0,
) -> CadDocument:
    source = document()
    minimum_x, minimum_y, maximum_x, maximum_y = bounds
    points = (
        Vector2(minimum_x, minimum_y),
        Vector2(maximum_x, minimum_y),
        Vector2(maximum_x, maximum_y),
        Vector2(minimum_x, maximum_y),
    )
    entities = tuple(
        SketchEntity(
            f"freecad:edge:{index}",
            GeometryKind.LINE,
            LineGeometry(points[index], points[(index + 1) % 4]),
        )
        for index in range(4)
    )
    sketch = Sketch(
        source.sketches[0].id,
        "Sketch",
        source.sketches[0].support_plane_id,
        entities,
        closed_profile_entity_ids=(tuple(item.id for item in entities),),
        attributes=frozen_mapping({"freecad": {"type_id": "Sketcher::SketchObject"}}),
    )
    feature = replace(
        source.feature_timeline[0],
        name="Pad",
        operation=BooleanOperation.CREATE,
        definition=ExtrusionFeature(
            ParameterValue(depth, ValueKind.LENGTH, "mm"),
            direction=Vector3(0.0, 0.0, 1.0),
            second_length=ParameterValue(10.0, ValueKind.LENGTH, "mm"),
            offset=ParameterValue(0.0, ValueKind.LENGTH, "mm"),
            second_offset=ParameterValue(0.0, ValueKind.LENGTH, "mm"),
            draft_angle=ParameterValue(0.0, ValueKind.ANGLE, "deg"),
            second_draft_angle=ParameterValue(0.0, ValueKind.ANGLE, "deg"),
        ),
        attributes=frozen_mapping({"freecad": {"type_id": "PartDesign::Pad"}}),
    )
    values = (
        ("AllowMultiFace", True, ValueKind.BOOLEAN, ""),
        ("AlongSketchNormal", True, ValueKind.BOOLEAN, ""),
        ("FuzzyTolerance", 0.0, ValueKind.NUMBER, ""),
        ("Label", "Pad", ValueKind.STRING, ""),
        ("Label2", "", ValueKind.STRING, ""),
        ("Length", depth, ValueKind.LENGTH, "mm"),
        ("Length2", 10.0, ValueKind.LENGTH, "mm"),
        ("Midplane", False, ValueKind.BOOLEAN, ""),
        ("Offset", 0.0, ValueKind.LENGTH, "mm"),
        ("Offset2", 0.0, ValueKind.LENGTH, "mm"),
        ("Refine", True, ValueKind.BOOLEAN, ""),
        ("Reversed", False, ValueKind.BOOLEAN, ""),
        ("SideType", 0, ValueKind.INTEGER, ""),
        ("Suppressed", False, ValueKind.BOOLEAN, ""),
        ("TaperAngle", 0.0, ValueKind.ANGLE, "deg"),
        ("TaperAngle2", 0.0, ValueKind.ANGLE, "deg"),
        ("Type", 0, ValueKind.INTEGER, ""),
        ("Type2", 0, ValueKind.INTEGER, ""),
        ("UseCustomVector", False, ValueKind.BOOLEAN, ""),
        ("Visibility", True, ValueKind.BOOLEAN, ""),
    )
    parameters = tuple(
        Parameter(
            f"freecad:parameter:Pad:{path}",
            f"Pad.{path}",
            ParameterValue(value, kind, unit),
            owner_id=feature.id,
            attributes=frozen_mapping({"freecad_path": path}),
        )
        for path, value, kind, unit in values
    )
    feature = replace(feature, parameter_ids=tuple(item.id for item in parameters))
    return replace(
        source,
        source=replace(
            source.source,
            format_id="freecad.fcstd",
            path="FreeCADRectanglePad.FCStd",
        ),
        parameters=parameters,
        sketches=(sketch,),
        feature_timeline=(feature,),
        bodies=(replace(source.bodies[0], final_feature_id=feature.id),),
        capabilities=frozenset(
            {
                Capability.PARAMETERS,
                Capability.PARAMETRIC_HISTORY,
                Capability.SUPPORT_PLANES,
                Capability.EDITABLE_SKETCHES,
                Capability.BODY_STRUCTURE,
                Capability.CONFIGURATIONS,
                Capability.BREP,
                Capability.NATIVE_PAYLOADS,
                Capability.PROVENANCE,
                Capability.ROUNDTRIP_METADATA,
            }
        ),
    )


# a synthetic FreeCAD pad-pocket history exercises canonical ids without local corpus files
def _FreeCADPadPocketDocument(*, ThroughAll: bool = False) -> CadDocument:
    SourceData = _freecad_rectangle_pad_document(
        bounds=(-30.0, -20.0, 30.0, 20.0),
        depth=15.0,
    )
    FeatureOne = SourceData.feature_timeline[0]
    SketchTemplate = SourceData.sketches[0]
    PocketPoints = (
        Vector2(-10.0, -8.0),
        Vector2(10.0, -8.0),
        Vector2(10.0, 8.0),
        Vector2(-10.0, 8.0),
    )
    PocketEntities = tuple(
        SketchEntity(
            f"freecad:pocket-edge:{IndexValue}",
            GeometryKind.LINE,
            LineGeometry(PocketPoints[IndexValue], PocketPoints[(IndexValue + 1) % 4]),
        )
        for IndexValue in range(4)
    )
    SketchTwo = replace(
        SketchTemplate,
        id="freecad:sketch:Sketch001",
        name="Sketch001",
        entities=PocketEntities,
        parameter_ids=(),
        closed_profile_entity_ids=(tuple(ItemData.id for ItemData in PocketEntities),),
    )
    FeatureTwo = replace(
        FeatureOne,
        id="freecad:feature:Pocket",
        name="Pocket",
        order=1,
        operation=BooleanOperation.CUT,
        sketch_id=SketchTwo.id,
        input_feature_ids=(FeatureOne.id,),
        definition=ExtrusionFeature(
            ParameterValue(5.0 if ThroughAll else 6.0, ValueKind.LENGTH, "mm"),
            end_condition=(
                ExtrusionEndCondition.THROUGH_ALL
                if ThroughAll
                else ExtrusionEndCondition.BLIND
            ),
            reversed=True,
            direction=Vector3(0.0, 0.0, -1.0),
            second_length=ParameterValue(5.0, ValueKind.LENGTH, "mm"),
            offset=ParameterValue(0.0, ValueKind.LENGTH, "mm"),
            second_offset=ParameterValue(0.0, ValueKind.LENGTH, "mm"),
            draft_angle=ParameterValue(0.0, ValueKind.ANGLE, "deg"),
            second_draft_angle=ParameterValue(0.0, ValueKind.ANGLE, "deg"),
        ),
        attributes=frozen_mapping({"freecad": {"type_id": "PartDesign::Pocket"}}),
    )
    FirstParameters = tuple(
        replace(
            ItemData,
            value=(
                ParameterValue(False, ValueKind.BOOLEAN)
                if ItemData.attributes.get("freecad_path") == "Visibility"
                else ItemData.value
            ),
        )
        for ItemData in SourceData.parameters
    )
    PocketValues = {
        "Label": ParameterValue("Pocket", ValueKind.STRING),
        "Length": ParameterValue(
            5.0 if ThroughAll else 6.0,
            ValueKind.LENGTH,
            "mm",
        ),
        "Length2": ParameterValue(5.0, ValueKind.LENGTH, "mm"),
        "Reversed": ParameterValue(True, ValueKind.BOOLEAN),
        "Type": ParameterValue(1 if ThroughAll else 0, ValueKind.INTEGER),
        "Visibility": ParameterValue(True, ValueKind.BOOLEAN),
    }
    SecondParameters = tuple(
        replace(
            ItemData,
            id=f"freecad:parameter:Pocket:{ItemData.attributes['freecad_path']}",
            name=f"Pocket.{ItemData.attributes['freecad_path']}",
            value=PocketValues.get(
                str(ItemData.attributes["freecad_path"]), ItemData.value
            ),
            owner_id=FeatureTwo.id,
        )
        for ItemData in SourceData.parameters
    )
    FeatureTwo = replace(
        FeatureTwo,
        parameter_ids=tuple(ItemData.id for ItemData in SecondParameters),
    )
    return replace(
        SourceData,
        parameters=(*FirstParameters, *SecondParameters),
        sketches=(SketchTemplate, SketchTwo),
        feature_timeline=(FeatureOne, FeatureTwo),
        bodies=(replace(SourceData.bodies[0], final_feature_id=FeatureTwo.id),),
    )


# a synthetic three-stage FreeCAD history exercises the connected native CMgr graph
def _FreeCADPadTwoPocketDocument() -> CadDocument:
    SourceData = _FreeCADPadPocketDocument()
    FeatureTwo = SourceData.feature_timeline[1]
    SketchTemplate = SourceData.sketches[1]
    PocketPoints = (
        Vector2(15.0, -5.0),
        Vector2(25.0, -5.0),
        Vector2(25.0, 5.0),
        Vector2(15.0, 5.0),
    )
    PocketEntities = tuple(
        SketchEntity(
            f"freecad:pocket-two-edge:{IndexValue}",
            GeometryKind.LINE,
            LineGeometry(
                PocketPoints[IndexValue],
                PocketPoints[(IndexValue + 1) % 4],
            ),
        )
        for IndexValue in range(4)
    )
    SketchThree = replace(
        SketchTemplate,
        id="freecad:sketch:Sketch002",
        name="Sketch002",
        entities=PocketEntities,
        parameter_ids=(),
        closed_profile_entity_ids=(tuple(ItemData.id for ItemData in PocketEntities),),
    )
    assert isinstance(FeatureTwo.definition, ExtrusionFeature)
    FeatureThree = replace(
        FeatureTwo,
        id="freecad:feature:Pocket001",
        name="Pocket001",
        order=2,
        sketch_id=SketchThree.id,
        input_feature_ids=(FeatureTwo.id,),
        definition=replace(
            FeatureTwo.definition,
            length=ParameterValue(5.0, ValueKind.LENGTH, "mm"),
        ),
    )
    ParametersOneTwo = tuple(
        replace(
            ItemData,
            value=(
                ParameterValue(False, ValueKind.BOOLEAN)
                if ItemData.owner_id == FeatureTwo.id
                and ItemData.attributes.get("freecad_path") == "Visibility"
                else ItemData.value
            ),
        )
        for ItemData in SourceData.parameters
    )
    PocketValues = {
        "Label": ParameterValue("Pocket001", ValueKind.STRING),
        "Length": ParameterValue(5.0, ValueKind.LENGTH, "mm"),
        "Visibility": ParameterValue(True, ValueKind.BOOLEAN),
    }
    ParametersThree = tuple(
        replace(
            ItemData,
            id=(
                "freecad:parameter:Pocket001:" f"{ItemData.attributes['freecad_path']}"
            ),
            name=f"Pocket001.{ItemData.attributes['freecad_path']}",
            value=PocketValues.get(
                str(ItemData.attributes["freecad_path"]),
                ItemData.value,
            ),
            owner_id=FeatureThree.id,
        )
        for ItemData in SourceData.parameters
        if ItemData.owner_id == FeatureTwo.id
    )
    FeatureThree = replace(
        FeatureThree,
        parameter_ids=tuple(ItemData.id for ItemData in ParametersThree),
    )
    return replace(
        SourceData,
        parameters=(*ParametersOneTwo, *ParametersThree),
        sketches=(*SourceData.sketches, SketchThree),
        feature_timeline=(*SourceData.feature_timeline, FeatureThree),
        bodies=(replace(SourceData.bodies[0], final_feature_id=FeatureThree.id),),
    )


# a four-stage FreeCAD history exercises every recovered predecessor edge
def _FreeCADPadThreePocketDocument() -> CadDocument:
    SourceData = _FreeCADPadTwoPocketDocument()
    FeatureThree = SourceData.feature_timeline[2]
    SketchTemplate = SourceData.sketches[2]
    PocketPoints = (
        Vector2(-25.0, -4.0),
        Vector2(-17.0, -4.0),
        Vector2(-17.0, 4.0),
        Vector2(-25.0, 4.0),
    )
    PocketEntities = tuple(
        SketchEntity(
            f"freecad:pocket-three-edge:{IndexValue}",
            GeometryKind.LINE,
            LineGeometry(
                PocketPoints[IndexValue],
                PocketPoints[(IndexValue + 1) % 4],
            ),
        )
        for IndexValue in range(4)
    )
    SketchFour = replace(
        SketchTemplate,
        id="freecad:sketch:Sketch003",
        name="Sketch003",
        entities=PocketEntities,
        parameter_ids=(),
        closed_profile_entity_ids=(tuple(ItemData.id for ItemData in PocketEntities),),
    )
    assert isinstance(FeatureThree.definition, ExtrusionFeature)
    FeatureFour = replace(
        FeatureThree,
        id="freecad:feature:Pocket002",
        name="Pocket002",
        order=3,
        sketch_id=SketchFour.id,
        input_feature_ids=(FeatureThree.id,),
        definition=replace(
            FeatureThree.definition,
            length=ParameterValue(4.0, ValueKind.LENGTH, "mm"),
        ),
    )
    ParametersFirstThree = tuple(
        replace(
            ItemData,
            value=(
                ParameterValue(False, ValueKind.BOOLEAN)
                if ItemData.owner_id == FeatureThree.id
                and ItemData.attributes.get("freecad_path") == "Visibility"
                else ItemData.value
            ),
        )
        for ItemData in SourceData.parameters
    )
    PocketValues = {
        "Label": ParameterValue("Pocket002", ValueKind.STRING),
        "Length": ParameterValue(4.0, ValueKind.LENGTH, "mm"),
        "Visibility": ParameterValue(True, ValueKind.BOOLEAN),
    }
    ParametersFour = tuple(
        replace(
            ItemData,
            id=(
                "freecad:parameter:Pocket002:" f"{ItemData.attributes['freecad_path']}"
            ),
            name=f"Pocket002.{ItemData.attributes['freecad_path']}",
            value=PocketValues.get(
                str(ItemData.attributes["freecad_path"]),
                ItemData.value,
            ),
            owner_id=FeatureFour.id,
        )
        for ItemData in SourceData.parameters
        if ItemData.owner_id == FeatureThree.id
    )
    FeatureFour = replace(
        FeatureFour,
        parameter_ids=tuple(ItemData.id for ItemData in ParametersFour),
    )
    return replace(
        SourceData,
        parameters=(*ParametersFirstThree, *ParametersFour),
        sketches=(*SourceData.sketches, SketchFour),
        feature_timeline=(*SourceData.feature_timeline, FeatureFour),
        bodies=(replace(SourceData.bodies[0], final_feature_id=FeatureFour.id),),
    )


# a synthetic FreeCAD full revolution exercises the recovered angular feature tree
def _FreeCADRectangleRevolutionDocument() -> CadDocument:
    SourceData = _freecad_rectangle_pad_document(
        bounds=(6.0, -9.0, 18.0, 9.0),
    )
    SourceFeature = SourceData.feature_timeline[0]
    SelectionData = Selection(
        "freecad:selection:Revolution:ReferenceAxis:0",
        "Revolution.ReferenceAxis.V_Axis",
        (
            SelectionPathElement(
                "native",
                SourceData.sketches[0].name,
                "V_Axis",
            ),
        ),
        provenance=Provenance(
            "freecad.fcstd",
            "Revolution.ReferenceAxis.V_Axis",
        ),
        attributes=frozen_mapping(
            {
                "freecad_object": "Revolution",
                "freecad_property": "ReferenceAxis",
                "freecad_target": SourceData.sketches[0].name,
                "freecad_subelement": "V_Axis",
            }
        ),
    )
    FeatureData = replace(
        SourceFeature,
        name="Revolution",
        kind=FeatureKind.REVOLUTION,
        operation=BooleanOperation.CREATE,
        definition=NativeFeatureDefinition(
            "freecad.fcstd",
            "PartDesign::Revolution",
        ),
        selection_ids=(SelectionData.id,),
        provenance=Provenance("freecad.fcstd", "Revolution"),
        attributes=frozen_mapping({"freecad": {"type_id": "PartDesign::Revolution"}}),
    )
    ValuesData = (
        ("AllowMultiFace", True, ValueKind.BOOLEAN, ""),
        ("Angle", 360.0, ValueKind.ANGLE, "deg"),
        ("Angle2", 0.0, ValueKind.ANGLE, "deg"),
        ("FuseOrder", 0, ValueKind.INTEGER, ""),
        ("FuzzyTolerance", -1.0, ValueKind.NUMBER, ""),
        ("Label", "Revolution", ValueKind.STRING, ""),
        ("Label2", "", ValueKind.STRING, ""),
        ("Midplane", False, ValueKind.BOOLEAN, ""),
        ("Refine", True, ValueKind.BOOLEAN, ""),
        ("Reversed", False, ValueKind.BOOLEAN, ""),
        ("Suppressed", False, ValueKind.BOOLEAN, ""),
        ("Type", 0, ValueKind.INTEGER, ""),
        ("Visibility", True, ValueKind.BOOLEAN, ""),
    )
    ParametersData = tuple(
        Parameter(
            f"freecad:parameter:Revolution:{PathValue}",
            f"Revolution.{PathValue}",
            ParameterValue(ValueData, KindData, UnitData),
            owner_id=FeatureData.id,
            attributes=frozen_mapping({"freecad_path": PathValue}),
        )
        for PathValue, ValueData, KindData, UnitData in ValuesData
    )
    FeatureData = replace(
        FeatureData,
        parameter_ids=tuple(ItemData.id for ItemData in ParametersData),
    )
    return replace(
        SourceData,
        parameters=ParametersData,
        selections=(SelectionData,),
        feature_timeline=(FeatureData,),
        bodies=(replace(SourceData.bodies[0], final_feature_id=FeatureData.id),),
        capabilities=SourceData.capabilities | {Capability.SELECTIONS},
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
        signatures=container_signatures(generated.getvalue()),
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
    resolved_features = archive.require(KIT_RESOLVED_STREAM)
    features = archive.require(FEATURES_STREAM)
    assert RESOLVED_FEATURES_STREAM not in archive.streams
    assert archive.require(CONFIGURATION_MANAGER_STREAM)
    assert archive.require(CONFIGURATION_STREAM)
    assert "Contents/DisplayLists" not in archive.streams
    assert "Contents/Config-0-LWDATA" not in archive.streams
    assert archive.require("Contents/Config-0-ModelHeader") == archive.require(
        "Header2"
    )
    assert keywords.startswith(b"\x86<?xml")
    assert features.startswith(b"<?xml")
    native = decode_native_model(
        keywords, resolved_features, resolved_stream=KIT_RESOLVED_STREAM
    )
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
    assert [item.code for item in result.diagnostics] == [
        "sldprt.neutral_write",
        "sldprt.donor_declined",
    ]
    assert [
        item.severity
        for item in result.diagnostics
        if item.code == "sldprt.donor_declined"
    ] == [Severity.WARNING]
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
    assert RESOLVED_FEATURES_STREAM not in archive.streams
    native = decode_native_model(
        archive.require(KEYWORDS_STREAM),
        archive.require(KIT_RESOLVED_STREAM),
        resolved_stream=KIT_RESOLVED_STREAM,
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
        archive.require(KEYWORDS_STREAM),
        archive.require(KIT_RESOLVED_STREAM),
        resolved_stream=KIT_RESOLVED_STREAM,
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


def test_source_less_native_configuration_lanes_are_absent() -> None:
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
    assert [
        name
        for name in archive.streams
        if name.startswith("Contents/Config-") and name.endswith("-ResolvedFeatures")
    ] == []
    assert (
        encode_native_part(
            _document_without_source(source), "memory"
        ).configuration_lanes
        == ()
    )
    assert archive.require(KIT_RESOLVED_STREAM)
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
        archive.require(KEYWORDS_STREAM),
        archive.require(KIT_RESOLVED_STREAM),
        resolved_stream=KIT_RESOLVED_STREAM,
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
    feature = replace(
        source.feature_timeline[0],
        name="Boss-Extrude1",
        operation=BooleanOperation.JOIN,
        definition=ExtrusionFeature(length),
    )
    source = replace(source, sketches=(sketch,), feature_timeline=(feature,))
    output = BytesIO()
    write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    assert RESOLVED_FEATURES_STREAM in archive.streams
    assert KIT_RESOLVED_STREAM not in archive.streams
    assert archive.require(CONFIGURATION_MANAGER_STREAM)
    assert archive.require(CONFIGURATION_STREAM)
    resolved = archive.require(RESOLVED_FEATURES_STREAM)
    native = decode_native_model(
        archive.require(KEYWORDS_STREAM),
        resolved,
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    assert native.diagnostics == ()
    assert native.sketches[0].object_id == 26
    assert native.sketches[0].name == "Sketch1"
    assert native.sketches[0].profiles[0].coordinates == (
        -30.0,
        -15.0,
        30.0,
        15.0,
    )
    assert native.operations[0].object_id == 32
    assert native.operations[0].name == "Boss-Extrude1"
    assert native.operations[0].profile_id == native.sketches[0].object_id
    assert native.operations[0].length_mm == pytest.approx(12.0)
    assert native.operations[0].termination_code == BLIND_END_CONDITION
    assert native.operations[0].native_stream == RESOLVED_FEATURES_STREAM
    restored = read_sldprt(output.getvalue())
    assert restored.sketches[0].entities == sketch.entities
    assert restored.feature_timeline[0].definition == feature.definition


def test_freecad_rectangle_pad_writes_native_parametric_solidworks_part(
    tmp_path: Path,
) -> None:
    source = _freecad_rectangle_pad_document()
    target = tmp_path / "FreeCADRectanglePad.SLDPRT"
    with pytest.raises(ApplicationUsabilityError) as captured:
        write_document(source, target, allow_carrier=False)
    assert not target.exists()
    assert captured.value.unimplemented_capabilities == frozenset({Capability.BREP})
    result = write_document(source, target, allow_carrier=True)
    data = target.read_bytes()
    archive = SldprtArchive.from_bytes(data)
    assert RESOLVED_FEATURES_STREAM in archive.streams
    assert KIT_RESOLVED_STREAM not in archive.streams
    assert archive.require(CONFIGURATION_MANAGER_STREAM)
    assert archive.require(CONFIGURATION_STREAM)
    resolved = archive.require(RESOLVED_FEATURES_STREAM)
    partition = archive.require(PARTITION_STREAM)
    native = decode_native_model(
        archive.require(KEYWORDS_STREAM),
        resolved,
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    transfers = {item.capability: item for item in result.transfers}
    assert result.application_usable is False
    assert result.vendor_loadable is True
    assert result.near_lossless is False
    assert result.requirements == ()
    assert partition == encode_blank_partition_stream()
    assert native.sketches[0].object_id == 26
    assert native.sketches[0].profiles[0].coordinates == (
        -30.0,
        -15.0,
        30.0,
        15.0,
    )
    assert native.operations[0].object_id == 32
    assert native.operations[0].length_mm == pytest.approx(12.0)
    assert native.operations[0].termination_code == BLIND_END_CONDITION
    assert transfers[Capability.PARAMETERS].mode.value == "native"
    assert transfers[Capability.PARAMETRIC_HISTORY].mode.value == "native"
    assert transfers[Capability.EDITABLE_SKETCHES].mode.value == "native"
    assert transfers[Capability.BREP].mode.value == "carrier"
    assert transfers[Capability.BREP].carrier_reason.value == "writer_unimplemented"
    for capability in (
        Capability.NATIVE_PAYLOADS,
        Capability.PROVENANCE,
        Capability.ROUNDTRIP_METADATA,
    ):
        assert transfers[capability].mode.value == "carrier"
        assert transfers[capability].carrier_reason.value == "target_unsupported"
    restored = read_sldprt(data)
    assert (
        restored.feature_timeline[0].definition == source.feature_timeline[0].definition
    )
    replay = BytesIO()
    replay_result = write_sldprt(restored, replay)
    assert replay.getvalue() == data
    assert replay_result.application_usable is False
    assert replay_result.vendor_loadable is True


# direction variant construction keeps unit and live-oracle fixtures identical
def _FreeCADDirectionVariant(SourceData: CadDocument, VariantName: str) -> CadDocument:
    FeatureData = SourceData.feature_timeline[0]
    DefinitionData = replace(
        FeatureData.definition,
        reversed=VariantName == "reversed",
        symmetric=VariantName == "midplane",
    )
    ParametersData = tuple(
        (
            replace(
                ItemData,
                value=ParameterValue(
                    (
                        2
                        if ItemData.attributes.get("freecad_path") == "SideType"
                        and VariantName == "midplane"
                        else (
                            0
                            if ItemData.attributes.get("freecad_path") == "SideType"
                            else VariantName
                            == ItemData.attributes.get("freecad_path", "").casefold()
                        )
                    ),
                    (
                        ValueKind.INTEGER
                        if ItemData.attributes.get("freecad_path") == "SideType"
                        else ValueKind.BOOLEAN
                    ),
                ),
            )
            if ItemData.attributes.get("freecad_path")
            in {"Midplane", "Reversed", "SideType"}
            else ItemData
        )
        for ItemData in SourceData.parameters
    )
    return replace(
        SourceData,
        parameters=ParametersData,
        feature_timeline=(replace(FeatureData, definition=DefinitionData),),
    )


@pytest.mark.parametrize(
    ("VariantName", "DirectionCode", "TerminationCode"),
    (("reversed", 1, 0), ("midplane", 0, 6)),
)
# direction variants prove source semantics reach the native editable operation record
def test_freecad_rectangle_pad_writes_native_direction_variants(
    VariantName: str,
    DirectionCode: int,
    TerminationCode: int,
) -> None:
    SourceData = _FreeCADDirectionVariant(
        _freecad_rectangle_pad_document(depth=18.0),
        VariantName,
    )
    OutputData = BytesIO()
    ResultData = write_sldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    NativeData = decode_native_model(
        ArchiveData.require(KEYWORDS_STREAM),
        ArchiveData.require(RESOLVED_FEATURES_STREAM),
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    OperationData = NativeData.operations[0]
    assert ResultData.vendor_loadable is True
    assert OperationData.direction_code == DirectionCode
    assert OperationData.termination_code == TerminationCode
    assert OperationData.length_mm == pytest.approx(18.0)
    assert OperationData.depth_copies[0].value_mm == pytest.approx(18.0)


# pad-pocket writes preserve both source profiles and the dependency-ordered native tree
def test_freecad_pad_pocket_writes_two_editable_native_features() -> None:
    SourceData = _FreeCADPadPocketDocument()
    OutputData = BytesIO()
    ResultData = write_sldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = locate_features(ArchiveData.require(RESOLVED_FEATURES_STREAM))
    assert ResultData.vendor_loadable is True
    assert KIT_RESOLVED_STREAM not in ArchiveData.streams
    ConfigurationData = ArchiveData.require(CONFIGURATION_STREAM)
    assert len(ConfigurationData) == 25300
    AtomDefinition = b"\xff\xff\x01\x00\x08\x00moAtom_c"
    AtomPos = ConfigurationData.index(AtomDefinition)
    assert struct.unpack_from("<II", ConfigurationData, AtomPos - 8) == (102, 2)
    HeaderData = ArchiveData.require("Contents/Config-0-ModelHeader")
    CStringName = b"moCStringHandle_c"
    CStringEnd = HeaderData.index(CStringName) + len(CStringName)
    assert HeaderData[CStringEnd + 4 : CStringEnd + 6] == struct.pack("<H", 0x804B)
    assert bytes.fromhex("f65a1a69") + struct.pack("<IHI", 41, 0, 110) in HeaderData
    assert [
        (
            ItemData.feature_id,
            ItemData.name,
            ItemData.kind,
            ItemData.sketch_id,
            ItemData.reversed,
            ItemData.depth_mm,
            ItemData.bounds_mm,
        )
        for ItemData in FeatureData
    ] == [
        (
            32,
            "Boss-Extrude1",
            "boss",
            26,
            False,
            pytest.approx(15.0),
            pytest.approx((-30.0, -20.0, 30.0, 20.0)),
        ),
        (
            40,
            "Cut-Extrude1",
            "cut",
            33,
            True,
            pytest.approx(6.0),
            pytest.approx((-10.0, -8.0, 10.0, 8.0)),
        ),
    ]
    assert ResultData.application_usable is True
    assert ResultData.metadata["native_brep"] == "feature-rebuilt"
    assert ResultData.metadata["native_geometry"] is True
    TransferData = {
        ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers
    }
    for CapabilityValue in (
        Capability.PARAMETERS,
        Capability.PARAMETRIC_HISTORY,
        Capability.EDITABLE_SKETCHES,
        Capability.BODY_STRUCTURE,
    ):
        assert TransferData[CapabilityValue] == "native"


# through-all cuts preserve their depthless native end specification and feature tree
def test_freecad_pad_through_all_pocket_writes_depthless_native_cut() -> None:
    SourceData = _FreeCADPadPocketDocument(ThroughAll=True)
    OutputData = BytesIO()
    ResultData = write_sldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = locate_features(ArchiveData.require(RESOLVED_FEATURES_STREAM))
    NativeData = decode_native_model(
        ArchiveData.require(KEYWORDS_STREAM),
        ArchiveData.require(RESOLVED_FEATURES_STREAM),
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata["native_brep"] == "feature-rebuilt"
    assert ResultData.metadata["native_geometry"] is True
    assert len(ArchiveData.require(RESOLVED_FEATURES_STREAM)) == 14693
    assert [ItemData.depth_mm for ItemData in FeatureData] == [
        pytest.approx(15.0),
        None,
    ]
    assert [ItemData.termination_code for ItemData in NativeData.operations] == [0, 1]
    assert [ItemData.direction_code for ItemData in NativeData.operations] == [0, 1]
    assert [ItemData.length_mm for ItemData in NativeData.operations] == [
        pytest.approx(15.0),
        None,
    ]
    TransferData = {
        ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers
    }
    for CapabilityValue in (
        Capability.PARAMETERS,
        Capability.PARAMETRIC_HISTORY,
        Capability.EDITABLE_SKETCHES,
        Capability.BODY_STRUCTURE,
    ):
        assert TransferData[CapabilityValue] == "native"


# chained pockets preserve all three editable profiles and depth parameters
def test_freecad_pad_two_pockets_writes_three_editable_native_features() -> None:
    SourceData = _FreeCADPadTwoPocketDocument()
    OutputData = BytesIO()
    ResultData = write_sldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = locate_features(ArchiveData.require(RESOLVED_FEATURES_STREAM))
    NativeData = decode_native_model(
        ArchiveData.require(KEYWORDS_STREAM),
        ArchiveData.require(RESOLVED_FEATURES_STREAM),
        ArchiveData.require(CONFIGURATION_STREAM),
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata["native_brep"] == "feature-rebuilt"
    assert KIT_RESOLVED_STREAM not in ArchiveData.streams
    assert len(ArchiveData.require(RESOLVED_FEATURES_STREAM)) == 21780
    assert [
        (
            ItemData.feature_id,
            ItemData.name,
            ItemData.kind,
            ItemData.sketch_id,
            ItemData.depth_mm,
            ItemData.bounds_mm,
        )
        for ItemData in FeatureData
    ] == [
        (
            32,
            "Boss-Extrude1",
            "boss",
            26,
            pytest.approx(15.0),
            pytest.approx((-30.0, -20.0, 30.0, 20.0)),
        ),
        (
            40,
            "Cut-Extrude1",
            "cut",
            33,
            pytest.approx(6.0),
            pytest.approx((-10.0, -8.0, 10.0, 8.0)),
        ),
        (
            47,
            "Cut-Extrude2",
            "cut",
            41,
            pytest.approx(5.0),
            pytest.approx((15.0, -5.0, 25.0, 5.0)),
        ),
    ]
    assert [ItemData.object_id for ItemData in NativeData.operations] == [32, 40, 47]
    assert [ItemData.length_mm for ItemData in NativeData.operations] == [
        pytest.approx(15.0),
        pytest.approx(6.0),
        pytest.approx(5.0),
    ]
    ManagerData = ArchiveData.require(CONFIGURATION_MANAGER_STREAM)
    assert struct.pack("<IIIII", 2, 103, 102, 102, 101) in ManagerData
    ConfigurationData = ArchiveData.require(CONFIGURATION_STREAM)
    AtomDefinition = b"\xff\xff\x01\x00\x08\x00moAtom_c"
    AtomPos = ConfigurationData.index(AtomDefinition)
    assert struct.unpack_from("<II", ConfigurationData, AtomPos - 8) == (103, 3)
    TransferData = {
        ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers
    }
    for CapabilityValue in (
        Capability.BREP,
        Capability.PARAMETERS,
        Capability.PARAMETRIC_HISTORY,
        Capability.EDITABLE_SKETCHES,
        Capability.BODY_STRUCTURE,
    ):
        assert TransferData[CapabilityValue] == "native"


# four-stage histories preserve every profile, depth, and predecessor edge
def test_freecad_pad_three_pockets_writes_four_editable_native_features() -> None:
    SourceData = _FreeCADPadThreePocketDocument()
    OutputData = BytesIO()
    ResultData = write_sldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = locate_features(ArchiveData.require(RESOLVED_FEATURES_STREAM))
    NativeData = decode_native_model(
        ArchiveData.require(KEYWORDS_STREAM),
        ArchiveData.require(RESOLVED_FEATURES_STREAM),
        ArchiveData.require(CONFIGURATION_STREAM),
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata["native_brep"] == "feature-rebuilt"
    assert KIT_RESOLVED_STREAM not in ArchiveData.streams
    assert len(ArchiveData.require(RESOLVED_FEATURES_STREAM)) == 27092
    assert [
        (
            ItemData.feature_id,
            ItemData.name,
            ItemData.kind,
            ItemData.sketch_id,
            ItemData.depth_mm,
            ItemData.bounds_mm,
        )
        for ItemData in FeatureData
    ] == [
        (
            32,
            "Boss-Extrude1",
            "boss",
            26,
            pytest.approx(15.0),
            pytest.approx((-30.0, -20.0, 30.0, 20.0)),
        ),
        (
            40,
            "Cut-Extrude1",
            "cut",
            33,
            pytest.approx(6.0),
            pytest.approx((-10.0, -8.0, 10.0, 8.0)),
        ),
        (
            47,
            "Cut-Extrude2",
            "cut",
            41,
            pytest.approx(5.0),
            pytest.approx((15.0, -5.0, 25.0, 5.0)),
        ),
        (
            54,
            "Cut-Extrude3",
            "cut",
            48,
            pytest.approx(4.0),
            pytest.approx((-25.0, -4.0, -17.0, 4.0)),
        ),
    ]
    assert [ItemData.object_id for ItemData in NativeData.operations] == [
        32,
        40,
        47,
        54,
    ]
    assert [ItemData.length_mm for ItemData in NativeData.operations] == [
        pytest.approx(15.0),
        pytest.approx(6.0),
        pytest.approx(5.0),
        pytest.approx(4.0),
    ]
    ManagerData = ArchiveData.require(CONFIGURATION_MANAGER_STREAM)
    assert (
        struct.pack(
            "<IIIIIII",
            3,
            104,
            103,
            103,
            102,
            102,
            101,
        )
        in ManagerData
    )
    ConfigurationData = ArchiveData.require(CONFIGURATION_STREAM)
    AtomDefinition = b"\xff\xff\x01\x00\x08\x00moAtom_c"
    AtomPos = ConfigurationData.index(AtomDefinition)
    assert struct.unpack_from("<II", ConfigurationData, AtomPos - 8) == (104, 4)
    TransferData = {
        ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers
    }
    for CapabilityValue in (
        Capability.BREP,
        Capability.PARAMETERS,
        Capability.PARAMETRIC_HISTORY,
        Capability.EDITABLE_SKETCHES,
        Capability.BODY_STRUCTURE,
    ):
        assert TransferData[CapabilityValue] == "native"


# full revolutions preserve the editable profile, angle, and sketch-axis binding
def test_freecad_full_revolution_writes_editable_native_revolved_boss() -> None:
    SourceData = _FreeCADRectangleRevolutionDocument()
    OutputData = BytesIO()
    ResultData = write_sldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    FeatureData = locate_features(ArchiveData.require(RESOLVED_FEATURES_STREAM))
    NativeData = decode_native_model(
        ArchiveData.require(KEYWORDS_STREAM),
        ArchiveData.require(RESOLVED_FEATURES_STREAM),
        ArchiveData.require(CONFIGURATION_STREAM),
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.metadata["native_brep"] == "feature-rebuilt"
    assert KIT_RESOLVED_STREAM not in ArchiveData.streams
    assert len(ArchiveData.require(RESOLVED_FEATURES_STREAM)) == 12135
    assert len(FeatureData) == 1
    assert FeatureData[0].feature_id == 31
    assert FeatureData[0].name == "Revolve1"
    assert FeatureData[0].kind == "revolve"
    assert FeatureData[0].sketch_id == 26
    assert FeatureData[0].angle_radians == pytest.approx(2.0 * 3.141592653589793)
    assert FeatureData[0].bounds_mm == pytest.approx((6.0, -9.0, 18.0, 9.0))
    assert len(NativeData.operations) == 1
    assert NativeData.operations[0].object_id == 31
    assert NativeData.operations[0].kind == "revolve_join"
    assert NativeData.operations[0].angle_degrees == pytest.approx(360.0)
    assert native_axis_bindings(NativeData) == frozenset({(31, 26, "V_Axis")})
    HeaderData = ArchiveData.require("Contents/Config-0-ModelHeader")
    DecodedHeader = decode_native_model_header(HeaderData)
    assert DecodedHeader.objects[-2:] == ((26, "Sketch1"), (31, "Revolve1"))
    CreationStamp = struct.unpack_from("<I", ArchiveData.require("ModelStamps"))[0]
    SerializedCreated = b"\xff\xfe\xff\x07" + "Created".encode("utf-16le")
    SerializedModified = b"\xff\xfe\xff\x08" + "Modified".encode("utf-16le")
    SerializedSketch = b"\xff\xfe\xff\x07" + "Sketch1".encode("utf-16le")
    SerializedRevolve = b"\xff\xfe\xff\x08" + "Revolve1".encode("utf-16le")
    assert (
        bytes.fromhex("088002000a80")
        + struct.pack("<I", 0)
        + b"\0\0"
        + struct.pack("<I", CreationStamp + 1)
        + SerializedCreated
        + bytes.fromhex("0a80")
        + struct.pack("<I", 1)
        + b"\0\0"
        + struct.pack("<I", CreationStamp + 2)
        + SerializedModified
        + struct.pack("<I", 26)
        + SerializedSketch
        in HeaderData
    )
    assert (
        bytes.fromhex("088001000a80")
        + struct.pack("<I", 0)
        + b"\0\0"
        + struct.pack("<I", CreationStamp + 2)
        + SerializedCreated
        + struct.pack("<I", 31)
        + SerializedRevolve
        in HeaderData
    )
    ConfigurationData = ArchiveData.require(CONFIGURATION_STREAM)
    AtomDefinition = b"\xff\xff\x01\x00\x08\x00moAtom_c"
    AtomPos = ConfigurationData.index(AtomDefinition)
    assert struct.unpack_from("<II", ConfigurationData, AtomPos - 8) == (101, 1)
    TransferData = {
        ItemData.capability: ItemData.mode.value for ItemData in ResultData.transfers
    }
    for CapabilityValue in (
        Capability.BREP,
        Capability.PARAMETERS,
        Capability.PARAMETRIC_HISTORY,
        Capability.EDITABLE_SKETCHES,
        Capability.BODY_STRUCTURE,
        Capability.SELECTIONS,
    ):
        assert TransferData[CapabilityValue] == "native"


@pytest.mark.parametrize("CenterData", (Vector2(0.0, 0.0), Vector2(3.0, -2.0)))
# circle pads use the oracle-proven first-principles circular feature program
def test_freecad_circle_pad_writes_native_editable_feature(
    CenterData: Vector2,
) -> None:
    SourceData = _freecad_rectangle_pad_document(depth=14.0)
    SourceSketch = SourceData.sketches[0]
    CircleEntity = SketchEntity(
        "freecad:circle:0",
        GeometryKind.CIRCLE,
        CircleGeometry(CenterData, 18.0),
    )
    CircleSketch = replace(
        SourceSketch,
        entities=(CircleEntity,),
        closed_profile_entity_ids=((CircleEntity.id,),),
    )
    SourceData = replace(SourceData, sketches=(CircleSketch,))
    OutputData = BytesIO()
    ResultData = write_sldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    NativeData = decode_native_model(
        ArchiveData.require(KEYWORDS_STREAM),
        ArchiveData.require(RESOLVED_FEATURES_STREAM),
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    assert ResultData.vendor_loadable is True
    assert len(NativeData.sketches) == 1
    assert len(NativeData.sketches[0].profiles) == 1
    assert NativeData.sketches[0].profiles[0].kind == "circle"
    assert NativeData.sketches[0].profiles[0].coordinates == pytest.approx(
        (CenterData.x, CenterData.y, 18.0)
    )
    assert NativeData.operations[0].length_mm == pytest.approx(14.0)


# source XZ coordinates and direction are normalized into the SOLIDWORKS Top basis
def test_freecad_top_plane_pad_writes_native_editable_feature() -> None:
    SourceData = _freecad_rectangle_pad_document(
        bounds=(-17.0, -8.0, 29.0, 12.0),
        depth=13.0,
    )
    SourcePlane = replace(
        SourceData.support_planes[0],
        transform=Transform(
            x_axis=Vector3(1.0, 0.0, 0.0),
            y_axis=Vector3(0.0, 0.0, 1.0),
            z_axis=Vector3(0.0, -1.0, 0.0),
        ),
    )
    SourceFeature = SourceData.feature_timeline[0]
    assert isinstance(SourceFeature.definition, ExtrusionFeature)
    SourceFeature = replace(
        SourceFeature,
        definition=replace(
            SourceFeature.definition,
            direction=Vector3(0.0, -1.0, 0.0),
        ),
    )
    SourceData = replace(
        SourceData,
        support_planes=(SourcePlane,),
        feature_timeline=(SourceFeature,),
    )
    OutputData = BytesIO()
    ResultData = write_sldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    NativeData = decode_native_model(
        ArchiveData.require(KEYWORDS_STREAM),
        ArchiveData.require(RESOLVED_FEATURES_STREAM),
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    assert ResultData.vendor_loadable is True
    assert NativeData.sketches[0].support_plane_id == 3
    assert NativeData.sketches[0].profiles[0].coordinates == pytest.approx(
        (-17.0, -12.0, 29.0, 8.0)
    )
    assert NativeData.operations[0].direction_code == 1
    assert NativeData.operations[0].length_mm == pytest.approx(13.0)


# source YZ coordinates are rotated into the SOLIDWORKS Right-plane sketch basis
def test_freecad_right_plane_pad_writes_native_editable_feature() -> None:
    SourceData = _freecad_rectangle_pad_document(
        bounds=(-17.0, -8.0, 29.0, 12.0),
        depth=7.0,
    )
    SourcePlane = replace(
        SourceData.support_planes[0],
        transform=Transform(
            x_axis=Vector3(0.0, 1.0, 0.0),
            y_axis=Vector3(0.0, 0.0, 1.0),
            z_axis=Vector3(1.0, 0.0, 0.0),
        ),
    )
    SourceFeature = SourceData.feature_timeline[0]
    assert isinstance(SourceFeature.definition, ExtrusionFeature)
    SourceFeature = replace(
        SourceFeature,
        definition=replace(
            SourceFeature.definition,
            direction=Vector3(1.0, 0.0, 0.0),
        ),
    )
    SourceData = replace(
        SourceData,
        support_planes=(SourcePlane,),
        feature_timeline=(SourceFeature,),
    )
    OutputData = BytesIO()
    ResultData = write_sldprt(SourceData, OutputData)
    ArchiveData = SldprtArchive.from_bytes(OutputData.getvalue())
    NativeData = decode_native_model(
        ArchiveData.require(KEYWORDS_STREAM),
        ArchiveData.require(RESOLVED_FEATURES_STREAM),
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    assert ResultData.vendor_loadable is True
    assert NativeData.sketches[0].support_plane_id == 4
    assert NativeData.sketches[0].profiles[0].coordinates == pytest.approx(
        (-12.0, -17.0, 8.0, 29.0)
    )
    assert NativeData.operations[0].direction_code == 0
    assert NativeData.operations[0].length_mm == pytest.approx(7.0)


@pytest.mark.parametrize(
    "variant",
    ("foreign", "construction", "open", "taper"),
)
def test_freecad_rectangle_pad_native_gate_rejects_non_equivalent_models(
    variant: str,
) -> None:
    source = _freecad_rectangle_pad_document()
    feature = source.feature_timeline[0]
    sketch = source.sketches[0]
    if variant == "foreign":
        source = replace(source, source=replace(source.source, format_id="test"))
    elif variant == "construction":
        entities = (
            replace(sketch.entities[0], construction=True),
            *sketch.entities[1:],
        )
        source = replace(source, sketches=(replace(sketch, entities=entities),))
    elif variant == "open":
        source = replace(
            source,
            sketches=(
                replace(
                    sketch,
                    entities=sketch.entities[:-1],
                    closed_profile_entity_ids=(),
                ),
            ),
        )
    else:
        source = replace(
            source,
            feature_timeline=(
                replace(
                    feature,
                    definition=replace(
                        feature.definition,
                        draft_angle=ParameterValue(1.0, ValueKind.ANGLE, "deg"),
                    ),
                ),
            ),
        )
    output = BytesIO()
    result = write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert "Contents/DisplayLists" not in archive.streams
    assert (
        hashlib.sha256(archive.require(PARTITION_STREAM)).hexdigest()
        != "56df5b4e4ccac3158b60ea75dd57959b991660d6d9c7bc05cbff795e56f44439"
    )


def test_source_less_native_rectangle_boss_profile_preserves_custom_names() -> None:
    source = document()
    points = (
        Vector2(-20.0, -10.0),
        Vector2(20.0, -10.0),
        Vector2(20.0, 10.0),
        Vector2(-20.0, 10.0),
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
        "CustomSketch",
        source.sketches[0].support_plane_id,
        entities,
        closed_profile_entity_ids=(tuple(item.id for item in entities),),
    )
    feature = replace(
        source.feature_timeline[0],
        name="CustomBoss",
        operation=BooleanOperation.JOIN,
        definition=ExtrusionFeature(ParameterValue(10.0, ValueKind.LENGTH, "mm")),
    )
    source = replace(source, sketches=(sketch,), feature_timeline=(feature,))
    output = BytesIO()
    write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    native = decode_native_model(
        archive.require(KEYWORDS_STREAM),
        archive.require(KIT_RESOLVED_STREAM),
        resolved_stream=KIT_RESOLVED_STREAM,
    )
    assert native.sketches[0].name == "CustomSketch"
    assert native.operations[0].name == "CustomBoss"
    assert "Contents/DisplayLists" not in archive.streams


def _non_native_rectangle_boss_document() -> CadDocument:
    source = document()
    points = (
        Vector2(-20.0, -10.0),
        Vector2(20.0, -10.0),
        Vector2(20.0, 10.0),
        Vector2(-20.0, 10.0),
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
        "CustomSketch",
        source.sketches[0].support_plane_id,
        entities,
        closed_profile_entity_ids=(tuple(item.id for item in entities),),
    )
    feature = replace(
        source.feature_timeline[0],
        name="CustomBoss",
        operation=BooleanOperation.JOIN,
        definition=ExtrusionFeature(ParameterValue(10.0, ValueKind.LENGTH, "mm")),
    )
    return replace(
        source,
        sketches=(sketch,),
        feature_timeline=(feature,),
        configurations=(
            Configuration("config:default", "Default", True),
            Configuration("config:machined", "Machined"),
        ),
    )


def test_non_native_document_writes_no_vendor_resolved_feature_lanes() -> None:
    source = _non_native_rectangle_boss_document()
    output = BytesIO()
    result = write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    lanes = sorted(
        name
        for name in archive.streams
        if name.startswith("Contents/Config-") and name.endswith("-ResolvedFeatures")
    )
    assert lanes == []
    part = encode_native_part(_document_without_source(source), "memory")
    assert part.configuration_lanes == ()
    assert part.donor_notes == VENDOR_UNLOADABLE_NOTES
    assert archive.require(CONFIGURATION_MANAGER_STREAM)
    assert archive.require(CONFIGURATION_STREAM)
    records = archive.require(KIT_RESOLVED_STREAM)
    assert records == part.kit_resolved_features
    assert result.application_usable is False
    assert result.vendor_loadable is False
    assert result.metadata["compatibility"] == "native-metadata-with-kit-neutral"
    assert result.metadata["native_content"] == "native-metadata"
    donor_declined = next(
        item for item in result.diagnostics if item.code == "sldprt.donor_declined"
    )
    assert donor_declined.severity is Severity.WARNING
    assert all(note in donor_declined.message for note in VENDOR_UNLOADABLE_NOTES)


def test_non_native_kit_resolved_stream_preserves_decoded_records() -> None:
    source = _non_native_rectangle_boss_document()
    output = BytesIO()
    write_sldprt(source, output)
    archive = SldprtArchive.from_bytes(output.getvalue())
    keywords = archive.require(KEYWORDS_STREAM)
    native = decode_native_model(
        keywords,
        archive.require(KIT_RESOLVED_STREAM),
        resolved_stream=KIT_RESOLVED_STREAM,
    )
    assert [item.name for item in native.sketches] == ["CustomSketch"]
    assert native.sketches[0].object_id == 26
    assert native.sketches[0].support_plane_id == 2
    assert [(item.kind, item.coordinates) for item in native.sketches[0].profiles] == [
        ("rectangle", (-20.0, -10.0, 20.0, 10.0))
    ]
    assert [(item.name, item.object_id) for item in native.operations] == [
        ("CustomBoss", 27)
    ]
    assert native.operations[0].length_mm == pytest.approx(10.0)
    assert native.operations[0].profile_id == 26
    assert [(item.object_id, item.name) for item in native.planes] == [
        (2, "Front Plane"),
        (3, "Top Plane"),
        (4, "Right Plane"),
    ]
    assert {item.native_stream for item in native.planes} == {KIT_RESOLVED_STREAM}
    assert {item.native_stream for item in native.sketches} == {KIT_RESOLVED_STREAM}
    assert {item.native_stream for item in native.operations} == {KIT_RESOLVED_STREAM}
    assert RESOLVED_FEATURES_STREAM not in archive.streams
    assert archive.require(CONFIGURATION_MANAGER_STREAM)
    assert archive.require(CONFIGURATION_STREAM)
    restored = read_sldprt(output.getvalue())
    assert [item.name for item in restored.sketches] == ["CustomSketch"]
    assert [item.name for item in restored.feature_timeline] == ["CustomBoss"]
    assert restored.sketches[0].entities == source.sketches[0].entities
    assert restored.feature_timeline[0].definition == (
        source.feature_timeline[0].definition
    )


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
    Part = encode_native_part(source, "Part1")
    FeatureId = Part.object_ids[f"feature:{source.bodies[0].final_feature_id}"]
    assert native.schema == "SCH_1200000_12006"
    assert native.data == encode_brep_model(
        source.brep,
        solidworks_feature_ids={source.brep.bodies[0].id: FeatureId},
    )
    assert b"LAST_BODY_MODIFYING_FEATURE_ID" in native.data
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
    assert RESOLVED_FEATURES_STREAM not in archive.streams
    assert archive.require(CONFIGURATION_MANAGER_STREAM)
    assert archive.require(CONFIGURATION_STREAM)
    resolved = archive.require(KIT_RESOLVED_STREAM)
    native = decode_native_model(
        archive.require(KEYWORDS_STREAM),
        resolved,
        resolved_stream=KIT_RESOLVED_STREAM,
    )
    imported = next(item for item in native.features if item.object_id == 26)
    classes = {item.offset: item.name for item in native.classes}
    assert imported.name == "Imported1"
    assert imported.kind == "Imported"
    assert classes[imported.native_offset - 18] == "moBaseBody_c"
    assert native.diagnostics == ()
    assert imported.native_end == len(resolved)
    assert resolved[imported.native_offset : imported.native_end] == imported.data


# generated Parasolid topology must be credited independently of feature history
def test_generated_parasolid_partition_is_native_brep(tmp_path) -> None:
    base = document()
    source = replace(
        base,
        brep=triangle_brep(),
        capabilities=base.capabilities | {Capability.BREP},
    )
    blocked = tmp_path / "blocked.SLDPRT"
    with pytest.raises(ApplicationUsabilityError) as captured:
        write_document(source, blocked, allow_carrier=False)
    assert Capability.BREP not in captured.value.unimplemented_capabilities
    assert captured.value.unimplemented_capabilities == frozenset(
        {
            Capability.BODY_STRUCTURE,
            Capability.EDITABLE_SKETCHES,
            Capability.PARAMETRIC_HISTORY,
        }
    )
    assert not blocked.exists()
    explicit = tmp_path / "explicit.SLDPRT"
    result = write_document(source, explicit, allow_carrier=True)
    assert result.metadata["native_brep"] == "generated"
    assert (
        next(
            item for item in result.transfers if item.capability is Capability.BREP
        ).mode.value
        == "native"
    )
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
        signatures=container_signatures(SAMPLE.read_bytes()),
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
        signatures=container_signatures(SAMPLE.read_bytes()),
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
            signatures=container_signatures(output.read_bytes()),
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
        signatures=container_signatures(trusted.read_bytes()),
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
        signatures=container_signatures(trusted.read_bytes()),
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
            signatures=container_signatures(output.read_bytes()),
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
    assert result.vendor_loadable is True
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
    assert result.near_lossless is False
    assert result.vendor_loadable is False
    assert result.application_usable is False
    rejection = next(
        item.message
        for item in result.diagnostics
        if item.code == "sldasm.vendor_reader_rejects"
    )
    assert f"donor_instance_diverged:{instance.id}" in rejection
    assert f"donor_mate_diverged:{mate.id}" in rejection
    assert result.requirements == ()
    assert result.metadata["referenced_files_written"] == len(assembly.documents)
    restored = read_sldprt(output)
    assert restored.assembly.instances[0].transform == Matrix4(tuple(transform))
    assert restored.assembly.mates[0].alignment is alignment
    assert restored.assembly.documents[0].document.parameters[
        0
    ].value.value == pytest.approx(target_value)


def test_portable_assembly_carries_the_load_critical_donor_streams(tmp_path) -> None:
    source = read_sldprt(ASSEMBLY)
    output = tmp_path / "carried.SLDASM"
    result = write_document(source, output)
    assert result.vendor_loadable is True
    assert result.application_usable is True
    assert result.metadata["compatibility"] == "native-template"
    assert not [
        item
        for item in result.diagnostics
        if item.code == "sldasm.vendor_reader_rejects"
    ]
    donor = SldprtArchive.open(ASSEMBLY).streams
    written = SldprtArchive.open(output).streams
    for name in _ASSEMBLY_DONOR_CARRIED_STREAMS:
        assert written[name] == donor[name]


def test_portable_assembly_declines_when_a_component_is_removed(tmp_path) -> None:
    source = read_sldprt(ASSEMBLY)
    assembly = source.assembly
    removed = assembly.instances[-1]
    entities = tuple(
        entity
        for entity in assembly.mate_entities
        if removed.id not in entity.instance_path
    )
    entity_ids = {entity.id for entity in entities}
    mates = tuple(mate for mate in assembly.mates if set(mate.entity_ids) <= entity_ids)
    mate_ids = {mate.id for mate in mates}
    edited = replace(
        source,
        assembly=replace(
            assembly,
            instances=assembly.instances[:-1],
            mate_entities=entities,
            mates=mates,
            mate_groups=tuple(
                replace(
                    group,
                    mate_ids=tuple(item for item in group.mate_ids if item in mate_ids),
                )
                for group in assembly.mate_groups
            ),
        ),
    )
    output = tmp_path / "shrunk.SLDASM"
    result = registry.write(
        edited,
        output,
        options=WriteOptions(
            validate=False,
            values={"portable": True, "allow_carrier": True},
        ),
    )
    assert result.vendor_loadable is False
    assert result.application_usable is False
    rejection = next(
        item.message
        for item in result.diagnostics
        if item.code == "sldasm.vendor_reader_rejects"
    )
    assert f"donor_instance_diverged:{removed.id}" in rejection
    donor = SldprtArchive.open(ASSEMBLY).streams
    written = SldprtArchive.open(output).streams
    for name in _ASSEMBLY_DONOR_CARRIED_STREAMS:
        assert written[name] == donor[name]
