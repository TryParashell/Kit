# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path
import struct

import pytest

from convert.adapters.solidworks import (
    SldprtAdapter,
    SldprtArchive,
    build_sldprt,
    read_sldprt,
)
from convert.adapters.solidworks.adapter import (
    _FEATURE_KIND_BY_NATIVE,
    _final_body_feature_id,
    _feature_kind,
    _is_geometry_brep_payload,
    _marker_curve_semantic,
    _sketch,
    _sketch_constraints,
    _solid_body_feature,
    _timeline,
)
from convert.adapters.solidworks.format import CLASS_MARKER, SERIALIZED_STRING_MARKER
from convert.adapters.solidworks.native import (
    NativeConstraint,
    NativeFeature,
    NativeMarker,
    NativeModel,
    NativeOperation,
    NativePlane,
    NativeSketch,
    _decode_planes,
    _native_scale_factors,
    _parse_native_equations,
    _parse_keywords,
    _reference_plane_ids,
    _constraints,
    _profiles,
    decode_native_model,
)
from interchange import (
    BooleanOperation,
    BrepPayload,
    Capability,
    CircleGeometry,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    LineGeometry,
    NativeFeatureDefinition,
    NativeGeometry,
    PayloadRole,
)

SAMPLE = Path(__file__).resolve().parents[2] / "examples" / ".SLDPRT" / "example.SLDPRT"
CORPUS = Path(__file__).resolve().parents[2] / "examples" / "Random"
OFFICIAL_FEATURE_TYPES_2026 = frozenset(value.casefold() for value in """
AsmExploder
CompExplodeStep
ExplodeLineProfileFeature
InContextFeatHolder
MagneticGroundPlane
MateCamTangent
MateCoincident
MateConcentric
MateDistanceDim
MateGearDim
MateHinge
MateInPlace
MateLimitDistanceDim
MateLinearCoupler
MateLock
MateParallel
MatePerpendicular
MatePlanarAngleDim
MateProfileCenter
MateRackPinionDim
MateScrew
MateSlot
MateSymmetric
MateTangent
MateUniversalJoint
MateWidth
PosGroupFolder
Reference
ReferencePattern
SmartComponentFeature
AdvHoleWzd
APattern
BaseBody
Bending
Blend
BlendCut
BodyExplodeStep
Boss
BossThin
Chamfer
CirPattern
CombineBodies
CosmeticThread
CosmeticWeldBead
CreateAssemFeat
CurvePattern
Cut
CutThin
Deform
DeleteBody
DelFace
DerivedCirPattern
DerivedHolePattern
DerivedLPattern
DimPattern
Dome
Draft
EdgeMerge
Emboss
Extrusion
Fillet
Helix
HoleSeries
HoleWzd
Imported
LocalChainPattern
LocalCirPattern
LocalCurvePattern
LocalLPattern
LocalSketchPattern
LPattern
MacroFeature
MirrorCompFeat
MirrorPattern
MirrorSolid
MirrorStock
MoveCopyBody
NetBlend
PrtExploder
Punch
ReplaceFace
RevCut
Revolution
RevolutionThin
Rib
Rip
Sculpt
Shape
Shell
SketchHole
SketchPattern
Split
SplitBody
Stock
Sweep
SweepCut
SweepThread
TablePattern
Thicken
ThickenCut
VarFillet
BendTableAchor
BomFeat
BomTemplate
DetailCircle
DrBreakoutSectionLine
DrSectionLine
GeneralTableAnchor
HoleTableAnchor
LiveSection
PunchTableAnchor
RevisionTableAnchor
WeldmentTableAnchor
FamilyTableFeat
WeldTableAnchor
BlockFolder
CommentsFolder
CosmeticWeldSubFolder
CutListFolder
FeatSolidBodyFolder
FeatSurfaceBodyFolder
FtrFolder
InsertedFeatureFolder
MateReferenceGroupFolder
ProfileFtrFolder
RefAxisFtrFolder
RefPlaneFtrFolder
SketchSliceFolder
SolidBodyFolder
SubAtomFolder
SubWeldFolder
SurfaceBodyFolder
TemplateFlatPattern
MBimport
Attribute
BlockDef
CurveInFile
GridFeature
LibraryFeature
Scale
Sensor
ViewBodyFeature
Cavity
MoldCoreCavitySolids
MoldPartingGeom
MoldPartLine
MoldShutOffSrf
SideCore
XformStock
AEM3DContact
AEMGravity
AEMLinearDamper
AEMLinearMotor
AEMLinearSpring
AEMRotationalMotor
AEMTorque
AEMTorsionalDamper
AEMTorsionalSpring
SimPlotFeature
SimPlotXAxisFeature
SimPlotYAxisFeature
SimResultFolder
BoundingBox
CenterOfMass
CoordSys
GroundPlane
RefAxis
RefPlane
AmbientLight
CameraFeature
DirectionLight
PointLight
SpotLight
SMBaseFlange
BreakCorner
CornerTrim
CrossBreak
EdgeFlange
FlatPattern
FlattenBends
Fold
FormToolInstance
Hem
Jog
LoftedBend
NormalCut
OneBend
ProcessBends
SheetMetal
SketchBend
SM3dBend
SMGusset
SMMiteredFlange
SolidToSheetMetal
TemplateSheetMetal
ToroidalBend
UnFold
3DProfileFeature
3DSplineCurve
CompositeCurve
ImportedCurve
PLine
ProfileFeature
RefCurve
RefPoint
SketchBlockDef
SketchBlockInst
SketchBitmap
BlendRefSurface
ExtendRefSurface
ExtruRefSurface
FillRefSurface
FlattenSurface
MidRefSurface
OffsetRefSuface
PlanarSurface
RadiateRefSurface
RefSurface
RevolvRefSurf
RuledSrfFromEdge
SewRefSurface
SurfCut
SweepRefSurface
TrimRefSurface
UnTrimRefSurf
EndCap
StrctSysBtwPtsMbrFeat
StrctSysCnrFeat
StrctSysCnrGrpFeat
StrctSysCnrMgmtFeat
StrctSysFeat
StrctSysGrpFeat
StrctSysPathSegMbrFeat
StrctSysPtToMem
StrctSysRefPlnMbrFeat
StrctSysSkPtLenMbrFeat
StrctSysSupPlnMbrFeat
StrctSysSurfPlnMbrFeat
AdvStructMember
Gusset
WeldBeadFeat
WeldCornerFeat
WeldMemberFeat
WeldmentFeature
WeldmentTableFeat
Round fillet corner
""".splitlines() if value)


def _resolved_name_record(
    name: str,
    object_id: int,
    family: int = 0,
    operation: int = 0,
    schema: int = 0,
) -> bytes:
    encoded = name.encode("utf-16le")
    return (
        bytes.fromhex("0480fffeff")
        + bytes((len(name),))
        + encoded
        + struct.pack("<IHBBI", 0, family, operation, schema, object_id)
    )


def test_adapter_advertises_exact_supported_capabilities() -> None:
    assert SldprtAdapter().info.capabilities == frozenset(Capability)


def test_part_capabilities_reflect_the_decoded_document() -> None:
    without_brep = read_sldprt(SAMPLE, include_brep=False)
    expected = frozenset(
        {
            Capability.BODY_STRUCTURE,
            Capability.CONFIGURATIONS,
            Capability.EDITABLE_SKETCHES,
            Capability.PARAMETERS,
            Capability.PARAMETRIC_HISTORY,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
            Capability.SELECTIONS,
            Capability.SUPPORT_PLANES,
        }
    )
    assert without_brep.capabilities == expected
    with_brep = read_sldprt(SAMPLE, include_brep=True)
    assert with_brep.capabilities == expected | {
        Capability.BREP,
        Capability.NATIVE_PAYLOADS,
    }


def test_official_feature_type_registry_is_exhaustive() -> None:
    assert len(OFFICIAL_FEATURE_TYPES_2026) == 246
    assert OFFICIAL_FEATURE_TYPES_2026 <= _FEATURE_KIND_BY_NATIVE.keys()
    assert set(FeatureKind) - set(_FEATURE_KIND_BY_NATIVE.values()) == {
        FeatureKind.PRIMITIVE,
        FeatureKind.REVERSE,
    }
    assert _FEATURE_KIND_BY_NATIVE["macrofeature"] == FeatureKind.NATIVE
    assert _FEATURE_KIND_BY_NATIVE["round fillet corner"] == FeatureKind.FILLET


def test_brep_capability_detection_uses_payload_semantics() -> None:
    assert _is_geometry_brep_payload(
        BrepPayload(
            "1",
            "future.kernel",
            "anything",
            "",
            "",
            data=b"geometry",
            role=PayloadRole.BREP,
            file_extension=".geo",
        )
    )
    assert not _is_geometry_brep_payload(
        BrepPayload(
            "2",
            "parasolid",
            "solid",
            "schema-2040",
            "",
            data=b"opaque",
        )
    )
    assert not _is_geometry_brep_payload(
        BrepPayload(
            "3",
            "future.kernel",
            "anything",
            "",
            "",
            role=PayloadRole.BREP,
            file_extension=".geo",
        )
    )


def test_parasolid_stream_discovery_does_not_depend_on_its_name() -> None:
    archive = SldprtArchive.open(SAMPLE)
    streams = archive.streams
    original_name = "Contents/Config-0-Partition"
    streams["Contents/CustomerGeometryBlob"] = streams.pop(original_name)
    renamed = build_sldprt(
        streams,
        file_id=archive.file_id,
        format_version=archive.format_version,
    )
    document = read_sldprt(renamed)
    assert len(document.brep_payloads) == 3
    assert all(payload.role == PayloadRole.BREP for payload in document.brep_payloads)
    assert (
        sum(
            payload.source_stream == "Contents/CustomerGeometryBlob"
            for payload in document.brep_payloads
        )
        == 2
    )


def test_solid_body_folder_detection_is_structural() -> None:
    body_folder = NativeFeature(
        object_id=9,
        name="Corps solides renommés",
        kind="SolidBodyFolder",
        xml_tag="Feature",
        native_offset=None,
        native_end=None,
        properties={"Type": "SolidBodyFolder"},
        dimensions=(),
    )
    assert _solid_body_feature((body_folder,)) is body_folder


def test_final_body_feature_selection_covers_current_solid_kinds() -> None:
    reference = FeatureStep("reference", "Plane", FeatureKind.REFERENCE, 0)
    extrusion = FeatureStep("extrusion", "Boss", FeatureKind.EXTRUSION, 1)
    revolution = FeatureStep("revolution", "Revolve", FeatureKind.REVOLUTION, 2)
    trailing_reference = FeatureStep(
        "trailing-reference", "Folder", FeatureKind.REFERENCE, 3
    )
    timeline = (reference, extrusion, revolution, trailing_reference)
    assert _final_body_feature_id(timeline, frozenset()) == revolution.id


def test_final_body_feature_selection_retains_structural_and_unknown_fallbacks() -> (
    None
):
    opaque = FeatureStep("opaque", "Vendor feature", FeatureKind.NATIVE, 0)
    reference = FeatureStep("reference", "Folder", FeatureKind.REFERENCE, 1)
    timeline = (opaque, reference)
    assert _final_body_feature_id(timeline, frozenset({opaque.id})) == opaque.id
    assert _final_body_feature_id((opaque,), frozenset()) == opaque.id


def test_timeline_distinguishes_principal_planes_structurally() -> None:
    principal = NativeFeature(
        object_id=1,
        name="Référence primaire",
        kind="Plane",
        xml_tag="Feature",
        native_offset=None,
        native_end=None,
        properties={"Type": "Plane"},
        dimensions=(),
    )
    extrusion = NativeFeature(
        object_id=2,
        name="Volume",
        kind="Extrusion",
        xml_tag="Feature",
        native_offset=10,
        native_end=20,
        properties={"Type": "Extrusion"},
        dimensions=(),
    )
    offset_plane = NativeFeature(
        object_id=3,
        name="Référence décalée",
        kind="Plane",
        xml_tag="Feature",
        native_offset=30,
        native_end=40,
        properties={"Type": "Plane"},
        dimensions=(),
    )
    frame = (
        (0.0, 0.0, 0.0),
        (0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
    )
    model = NativeModel(
        configurations=(),
        features=(principal, extrusion, offset_plane),
        planes=(
            NativePlane(1, principal.name, *frame, None, None, True),
            NativePlane(3, offset_plane.name, *frame, 30, 10, False),
        ),
        sketches=(),
        operations=(
            NativeOperation(
                object_id=2,
                name=extrusion.name,
                kind="join",
                profile_id=None,
                dependencies=(),
                native_offset=10,
                native_end=20,
                length_mm=10.0,
                radius_mm=None,
                family_code=0,
                operation_code=0,
                schema_code=0,
                direction_code=0,
                termination_code=0,
                selection_offsets=(),
                selected_local_ids=(),
            ),
        ),
        names=(),
        classes=(),
        scalars=(),
    )
    timeline = _timeline(model, ())
    assert timeline[0].input_feature_ids == ()
    assert timeline[2].input_feature_ids == (timeline[1].id,)


def test_principal_planes_use_native_roles_after_rename() -> None:
    features = [
        NativeFeature(
            object_id=index,
            name=name,
            kind=kind,
            xml_tag=tag,
            native_offset=offset,
            native_end=offset,
            properties=properties,
            dimensions=(),
        )
        for index, name, kind, tag, properties, offset in (
            (99, "Later Datum", "Plane", "Feature", {"Type": "Plane"}, 100),
            (20, "Primary", "Plane", "Feature", {"Type": "Plane"}, 10),
            (21, "Horizontal", "Plane", "Feature", {"Type": "Plane"}, 20),
            (22, "Side", "Plane", "Feature", {"Type": "Plane"}, 30),
            (23, "Centre", "Sketch", "Sketch", {"Type": "Origin"}, 40),
        )
    ]
    planes = _decode_planes(b"", features)
    assert [plane.object_id for plane in planes] == [20, 21, 22]
    assert [plane.name for plane in planes] == ["Primary", "Horizontal", "Side"]
    assert [plane.normal for plane in planes] == [
        (0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0),
        (1.0, 0.0, 0.0),
    ]


def test_keyword_history_discovers_native_and_future_feature_tags() -> None:
    configurations, features = _parse_keywords(
        b"""<?xml version="1.0" encoding="UTF-8"?>
<Keywords>
  <Configuration id="0" Name="Default" />
  <Feature id="1" Name="Datum" Type="Plane" />
  <HoleWizard id="2" Name="Tapped Hole">
    <Dimension Name="D1">12.5mm</Dimension>
  </HoleWizard>
  <FutureFeature id="3" Name="Vendor Operation" Vendor="Parashell">
    <FutureChild id="4" Name="Nested Operation" />
  </FutureFeature>
  <Dimension id="5" Name="Not a Feature">7mm</Dimension>
  <Invalid id="not-an-integer" Name="Invalid" />
</Keywords>"""
    )
    assert [configuration.name for configuration in configurations] == ["Default"]
    assert [
        (feature.object_id, feature.kind, feature.xml_tag) for feature in features
    ] == [
        (1, "Plane", "Feature"),
        (2, "HoleWizard", "HoleWizard"),
        (3, "FutureFeature", "FutureFeature"),
        (4, "FutureChild", "FutureChild"),
    ]
    assert features[1].dimensions[0].value_mm == 12.5
    assert features[2].properties["Vendor"] == "Parashell"
    assert _feature_kind(features[1]) == FeatureKind.HOLE
    assert _feature_kind(features[2]) == FeatureKind.NATIVE


def test_feature_records_bind_by_object_id_and_missing_names_are_retained() -> None:
    first = _resolved_name_record("Binary original", 41)
    second = _resolved_name_record("Binary fallback", 42)
    model = decode_native_model(
        b"""<?xml version="1.0" encoding="UTF-8"?>
<Keywords>
  <FutureFeature id="41" Name="Renamed display" />
  <FutureFeature id="42" />
  <FutureFeature id="43" />
</Keywords>""",
        first + second,
    )
    by_id = {feature.object_id: feature for feature in model.features}
    assert by_id[41].name == "Renamed display"
    assert by_id[41].native_offset == 0
    assert by_id[41].native_end == len(first)
    assert by_id[41].data == first
    assert by_id[42].name == "Binary fallback"
    assert by_id[42].native_offset == len(first)
    assert by_id[42].data == second
    assert by_id[43].name == "FutureFeature 43"
    assert by_id[43].native_offset is None


def test_operation_dimensions_use_record_order_and_feature_semantics() -> None:
    extrusion = _resolved_name_record("Extrusion native label", 10, 320, 0, 192)
    fillet = _resolved_name_record("Fillet native label", 20)
    model = decode_native_model(
        """<?xml version="1.0" encoding="UTF-8"?>
<Keywords>
  <Extrusion id="10" Name="Volume localisé">
    <Dimension Name="Profondeur">12.5</Dimension>
  </Extrusion>
  <Feature id="20" Name="Congé localisé" Type="Fillet">
    <Dimension Name="Rayon">0.75</Dimension>
  </Feature>
</Keywords>""".encode("utf-8"),
        extrusion + fillet,
    )
    operations = {operation.object_id: operation for operation in model.operations}
    assert operations[10].length_mm == 12.5
    assert operations[20].radius_mm == 0.75
    features = {feature.object_id: feature for feature in model.features}
    assert features[10].dimensions[0].kind == "length"
    assert features[20].dimensions[0].kind == "radius"


def test_circle_dimension_semantics_do_not_require_display_tokens_or_names() -> None:
    archive = SldprtArchive.open(SAMPLE)
    keywords = archive.require("swXmlContents/KeyWords").replace(
        b'Name="D1">&lt;MOD-DIAM&gt;5.5',
        b'Name="Diametre">5.5',
    )
    model = decode_native_model(
        keywords,
        archive.require("Contents/Config-0-ResolvedFeatures"),
    )
    sketch = next(item for item in model.sketches if item.object_id == 88)
    assert sketch.profiles[0].coordinates[2] == pytest.approx(2.75)
    assert sketch.profiles[0].parameter_name == "Diametre"
    assert sketch.profiles[0].dimension_kind == "diameter"
    assert sketch.dimensions[0].kind == "diameter"
    assert sketch.dimensions[0].native_offset is not None


@pytest.mark.parametrize(
    ("native_kind", "neutral_kind"),
    (
        ("Revolve", FeatureKind.REVOLUTION),
        ("Cut-Revolve", FeatureKind.REVOLUTION),
        ("Sweep", FeatureKind.SWEEP),
        ("Cut-Sweep", FeatureKind.SWEEP),
        ("Loft-Thin", FeatureKind.LOFT),
        ("Shell", FeatureKind.SHELL),
        ("Mirror", FeatureKind.MIRROR),
        ("LPattern", FeatureKind.PATTERN),
        ("CirPattern", FeatureKind.PATTERN),
        ("Helix/Spiral", FeatureKind.HELIX),
        ("Axis", FeatureKind.REFERENCE),
    ),
)
def test_native_feature_types_map_to_neutral_kinds(
    native_kind: str, neutral_kind: FeatureKind
) -> None:
    feature = NativeFeature(
        object_id=1,
        name="Feature",
        kind=native_kind,
        xml_tag="Feature",
        native_offset=None,
        native_end=None,
        properties={},
        dimensions=(),
    )
    assert _feature_kind(feature) == neutral_kind


def test_corpus_hole_wizard_features_reach_the_timeline() -> None:
    document = read_sldprt(CORPUS / "Engine_Block.SLDPRT", include_brep=False)
    holes = [
        feature
        for feature in document.feature_timeline
        if feature.kind == FeatureKind.HOLE
    ]
    assert len(holes) == 8
    assert {feature.attributes["xml_tag"] for feature in holes} == {"HoleWizard"}
    assert all(feature.attributes["native_type"] == "HoleWizard" for feature in holes)


def test_container_recovers_native_streams() -> None:
    archive = SldprtArchive.open(SAMPLE)
    assert archive.file_id == 1901848975
    assert archive.format_version == 4
    assert archive.require("Contents/Config-0-ResolvedFeatures")
    assert b"<?xml" in archive.require("swXmlContents/KeyWords")
    assert archive.require("Contents/Config-0-Partition")


def test_container_accepts_variable_record_signature_data() -> None:
    source = bytearray(SAMPLE.read_bytes())
    original = SldprtArchive.from_bytes(source)
    replacement = bytes.fromhex("01020304")
    for record in original.records:
        source[record.offset + 6 : record.offset + 10] = replacement
    recovered = SldprtArchive.from_bytes(source)
    assert len(recovered.records) == len(original.records)
    assert {record.signature[6:] for record in recovered.records} == {replacement}
    assert recovered.require("Contents/Config-0-ResolvedFeatures") == original.require(
        "Contents/Config-0-ResolvedFeatures"
    )


def test_adapter_recovers_parametric_history_and_brep() -> None:
    document = read_sldprt(SAMPLE)
    assert document.validate() == ()
    assert len(document.configurations) == 1
    assert len(document.parameters) == 26
    assert len(document.support_planes) == 7
    assert len(document.sketches) == 5
    assert len(document.feature_timeline) == 39
    assert len(document.brep_payloads) == 3
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
    assert document.brep_payloads[1].sha256 == (
        "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6"
    )
    assert document.brep_payloads[2].sha256 == (
        "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7"
    )


def test_adapter_recovers_feature_operations_and_dimensions() -> None:
    document = read_sldprt(SAMPLE, include_brep=False)
    operations = {
        feature.name: feature
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
    }
    assert operations["Boss-Extrude1"].operation == BooleanOperation.JOIN
    assert operations["Cut-Extrude1"].operation == BooleanOperation.CUT
    assert operations["Boss-Extrude2"].operation == BooleanOperation.JOIN
    assert operations["Cut-Extrude2"].operation == BooleanOperation.CUT
    assert operations["Boss-Extrude3"].operation == BooleanOperation.JOIN
    assert isinstance(operations["Boss-Extrude1"].definition, ExtrusionFeature)
    assert isinstance(operations["Fillet1"].definition, FilletFeature)
    assert operations["Boss-Extrude1"].definition.length.value == 20.0
    assert operations["Cut-Extrude1"].definition.length.value == 0.25
    assert operations["Boss-Extrude2"].definition.length.value == 0.75
    assert operations["Cut-Extrude2"].definition.length.value == 9.0
    assert operations["Boss-Extrude3"].definition.length.value == 6.0
    assert operations["Fillet1"].definition.radius.value == 0.25
    assert operations["Boss-Extrude1"].attributes["length_mm"] == 20.0
    assert operations["Cut-Extrude1"].attributes["length_mm"] == 0.25
    assert operations["Boss-Extrude2"].attributes["length_mm"] == 0.75
    assert operations["Cut-Extrude2"].attributes["length_mm"] == 9.0
    assert operations["Boss-Extrude3"].attributes["length_mm"] == 6.0
    assert operations["Fillet1"].attributes["radius_mm"] == 0.25
    assert operations["Fillet1"].selection_ids == ("sldprt:selection:116:edge:1",)
    assert document.parameter("sldprt:parameter:88:D1").value.value == 5.5
    assert document.parameter("sldprt:parameter:106:D1").value.value == 2.1


def test_adapter_recovers_support_frames_and_profiles() -> None:
    document = read_sldprt(SAMPLE, include_brep=False)
    plane2 = document.plane("sldprt:plane:62")
    assert plane2.transform.origin.x == pytest.approx(124.3)
    assert plane2.transform.x_axis.z == -1.0
    assert plane2.transform.y_axis.y == 1.0
    assert plane2.transform.z_axis.x == 1.0
    sketch1 = document.sketch("sldprt:sketch:26")
    profile = [
        entity
        for entity in sketch1.entities
        if entity.id in sketch1.closed_profile_entity_ids[0]
    ]
    assert len(profile) == 4
    assert isinstance(profile[0].geometry, LineGeometry)
    assert profile[0].geometry.start.x == pytest.approx(-124.3)
    assert profile[0].geometry.start.y == pytest.approx(-89.75)
    sketch3 = document.sketch("sldprt:sketch:63")
    assert len(sketch3.closed_profile_entity_ids) == 3
    sketch4 = document.sketch("sldprt:sketch:88")
    circle = next(
        entity
        for entity in sketch4.entities
        if entity.id == sketch4.closed_profile_entity_ids[0][0]
    )
    assert circle.geometry.center.x == pytest.approx(10.0)
    assert circle.geometry.center.y == pytest.approx(81.631746131982)
    assert circle.geometry.radius == pytest.approx(2.75)


def test_adapter_recovers_construction_geometry_without_guessing() -> None:
    document = read_sldprt(SAMPLE, include_brep=False)
    expected_line_counts = {
        "Sketch1": 2,
        "Sketch2": 2,
        "Sketch3": 6,
        "Sketch4": 1,
        "Sketch6": 2,
    }
    for sketch in document.sketches:
        lines = [
            entity.geometry
            for entity in sketch.entities
            if entity.construction and isinstance(entity.geometry, LineGeometry)
        ]
        assert len(lines) == expected_line_counts[sketch.name]
    sketch1 = document.sketch("sldprt:sketch:26")
    diagonals = [
        entity.geometry
        for entity in sketch1.entities
        if entity.construction and isinstance(entity.geometry, LineGeometry)
    ]
    assert {
        (
            line.start.x,
            line.start.y,
            line.end.x,
            line.end.y,
        )
        for line in diagonals
    } == {
        (124.3, 89.75, -124.3, -89.75),
        (124.3, -89.75, -124.3, 89.75),
    }
    sketch4 = document.sketch("sldprt:sketch:88")
    construction = [
        entity.geometry
        for entity in sketch4.entities
        if entity.construction and isinstance(entity.geometry, LineGeometry)
    ]
    assert (
        construction[0].start.x,
        construction[0].start.y,
        construction[0].end.x,
        construction[0].end.y,
    ) == pytest.approx((10.0, 89.75, 10.0, -89.75))
    assert all(
        not str(constraint.kind).startswith("native_")
        for constraint in sketch4.constraints
    )
    assert any(
        isinstance(entity.geometry, NativeGeometry) for entity in sketch1.entities
    )
    sketch6 = document.sketch("sldprt:sketch:106")
    assert any(
        isinstance(entity.geometry, NativeGeometry)
        and entity.geometry.data.get("record_data")
        for entity in sketch6.entities
    )


def test_adapter_accumulates_proven_circle_profiles() -> None:
    document = read_sldprt(CORPUS / "Cover.SLDPRT", include_brep=False)
    sketch = document.sketch("sldprt:sketch:26")
    entities = {entity.id: entity.geometry for entity in sketch.entities}
    profiles = [entities[profile[0]] for profile in sketch.closed_profile_entity_ids]
    assert all(isinstance(profile, CircleGeometry) for profile in profiles)
    assert [profile.radius for profile in profiles] == pytest.approx((16.0, 184.0))
    assert (profiles[0].center.x, profiles[0].center.y) == pytest.approx(
        (15.300876095409, 4.677947275564)
    )
    assert (profiles[1].center.x, profiles[1].center.y) == pytest.approx(
        (-130.107647738324, 130.107647738325)
    )


def test_adapter_binds_dimension_operands_by_marker_position() -> None:
    document = read_sldprt(CORPUS / "Cover.SLDPRT", include_brep=False)
    sketch = document.sketch("sldprt:sketch:77")
    constraints = {
        constraint.parameter_id: constraint
        for constraint in sketch.constraints
        if constraint.parameter_id
    }
    assert tuple(
        reference.entity_id
        for reference in constraints["sldprt:parameter:77:D2"].references
    ) == (
        "sldprt:sketch:77:native:90347",
        "sldprt:sketch:77:native:87930",
    )
    assert tuple(
        reference.entity_id
        for reference in constraints["sldprt:parameter:77:D6"].references
    ) == (
        "sldprt:sketch:77:native:87322",
        "sldprt:sketch:77:native:87484",
    )
    radial = document.sketch("sldprt:sketch:27")
    radial_constraints = {
        constraint.parameter_id: constraint
        for constraint in radial.constraints
        if constraint.parameter_id
    }
    assert radial_constraints["sldprt:parameter:27:D2"].references == ()


def test_adapter_resolves_line_endpoints_by_native_marker_index() -> None:
    document = read_sldprt(CORPUS / "Engine_Block.SLDPRT", include_brep=False)
    sketch = document.sketch("sldprt:sketch:139")
    expected = {
        145018: (
            (-98.287842584929, 161.92745289172),
            (-130.107647738324, 130.107647738326),
        ),
        145110: (
            (-130.107647738324, 130.107647738326),
            (-48.790367901871, 48.790367901872),
        ),
        145202: (
            (-48.790367901871, 48.790367901872),
            (-16.970562748477, 80.610173055267),
        ),
        145294: (
            (-16.970562748477, 80.610173055267),
            (-98.287842584929, 161.92745289172),
        ),
    }
    entities = {entity.provenance.spans[0].offset: entity for entity in sketch.entities}
    for offset, (start, end) in expected.items():
        geometry = entities[offset].geometry
        assert isinstance(geometry, LineGeometry)
        assert (geometry.start.x, geometry.start.y) == pytest.approx(start)
        assert (geometry.end.x, geometry.end.y) == pytest.approx(end)


def test_adapter_decodes_linked_rectangle_records_from_newer_native_streams() -> None:
    values = (
        (100, 178, 0, (-20.0, -10.0), None, "circle"),
        (278, 162, 0, (20.0, 10.0), None, "circle"),
        (440, 162, 0, (-20.0, 10.0), None, "circle"),
        (602, 166, 0, (20.0, -10.0), None, "circle"),
        (768, 92, 0, None, (0, 1), "native"),
        (860, 92, 1, None, (0, 3), "native"),
        (952, 92, 1, None, (0, 2), "native"),
        (1044, 92, 1, None, (2, 1), "native"),
        (1136, 208, 1, None, (3, 1), "native"),
    )
    markers = tuple(
        NativeMarker(
            offset,
            length,
            "ffff1f0003",
            native_kind,
            "05000100",
            1,
            None,
            None,
            None,
            coordinates,
            endpoints,
            False,
            semantic,
        )
        for offset, length, native_kind, coordinates, endpoints, semantic in values
    )
    profiles, used, dimensions = _profiles(list(markers), ())
    assert dimensions == ()
    assert used == {marker.offset for marker in markers}
    assert len(profiles) == 1
    assert profiles[0].coordinates == (-20.0, -10.0, 20.0, 10.0)
    assert profiles[0].marker_offsets[:4] == (860, 1136, 1044, 952)
    feature = NativeFeature(26, "Sketch1", "Sketch", "Sketch", 0, 1344, {}, ())
    constraints = _constraints(feature, markers, profiles)
    sketch = NativeSketch(26, "Sketch1", 2, 0, 1344, markers, profiles, (), constraints)
    decoded = _sketch(sketch, set())
    assert len(decoded.entities) == 4
    assert all(isinstance(entity.geometry, LineGeometry) for entity in decoded.entities)
    assert len(decoded.constraints) == 8
    assert {str(constraint.kind) for constraint in decoded.constraints} == {
        "coincident",
        "horizontal",
        "vertical",
    }
    assert decoded.closed_profile_entity_ids == (
        tuple(entity.id for entity in decoded.entities),
    )


def test_broad_source_less_byte_decoders_require_native_record_shapes() -> None:
    def declaration(name: str) -> bytes:
        return CLASS_MARKER + struct.pack("<H", len(name)) + name.encode("ascii")

    equation_source = '"Width" = 40mm'
    equation_data = (
        declaration("moRelMgr_c")
        + declaration("moRelation_c")
        + SERIALIZED_STRING_MARKER
        + bytes((len(equation_source),))
        + equation_source.encode("utf-16le")
    )
    equations = _parse_native_equations(equation_data, 1, "Contents/Config-1")
    assert [(item.lhs, item.rhs, item.native_stream) for item in equations] == [
        ("Width", "40mm", "Contents/Config-1")
    ]
    reference_data = b"head" + b"\0" * 6 + struct.pack("<II", 1, 2) + b"\0\x05tail"
    assert _reference_plane_ids(
        reference_data, 0, len(reference_data), 35, frozenset({2, 3, 35})
    ) == (2,)
    scale_data = (
        struct.pack("<I3d", 1, 1.1, 1.1, 1.1) + b"\0" * 8 + struct.pack("<H", 0x80AC)
    )
    assert _native_scale_factors(scale_data, 0, len(scale_data)) == pytest.approx(
        (1.1, 1.1, 1.1)
    )
    assert _native_scale_factors(scale_data[:-1], 0, len(scale_data) - 1) is None


def test_broad_structural_rectangle_uses_saved_endpoint_indices() -> None:
    values = (
        ((0.0, -35.0), None, 0, 1),
        ((0.0, 35.0), None, 0, 1),
        (None, (17768, 29816), 1, 1),
        ((10.0, -25.0), None, 0, 1),
        ((25.0, -25.0), None, 0, 1),
        ((25.0, 25.0), None, 0, 1),
        ((10.0, 25.0), None, 0, 1),
        (None, (0, 1), 2, 2),
        (None, (3, 4), 1, 1),
        (None, (4, 5), 1, 1),
        (None, (5, 6), 1, 1),
        (None, (6, 3), 1, 1),
    )
    markers = [
        NativeMarker(
            offset=100 + index * 100,
            length=92,
            prefix="ffff1f0003",
            native_kind=native_kind,
            locus="04000200" if index in {2, 7} else "05000100",
            profile_role=role,
            state=1.0,
            object_index=index,
            local_id=index,
            coordinates_mm=coordinates,
            endpoint_indices=endpoints,
            construction=role == 2,
            semantic="line" if index == 7 else "native",
        )
        for index, (coordinates, endpoints, native_kind, role) in enumerate(values)
    ]
    profiles, used, dimensions = _profiles(markers, ())
    assert dimensions == ()
    assert [(item.kind, item.coordinates) for item in profiles] == [
        ("rectangle", (10.0, -25.0, 25.0, 25.0))
    ]
    assert used == {900, 1000, 1100, 1200}


@pytest.mark.parametrize(
    ("length", "semantic", "locus", "role", "endpoints", "record", "expected"),
    (
        (92, "native", "05000100", 1, (0, 1), b"", "line"),
        (92, "native", "03000300", 0, (0, 1), b"", "native"),
        (104, "native", "05000100", 1, (0, 1), b"", "line"),
        (104, "native", "03000300", 0, (0, 0), b"", "ellipse"),
        (108, "native", "03000300", 0, (0, 1), b"", "arc_ellipse"),
        (112, "native", "03000300", 0, (0, 0), b"", "circle"),
        (116, "native", "03000300", 0, (0, 1), b"", "arc"),
        (124, "native", "03000300", 0, (0, 1), b"", "parabola"),
        (128, "native", "03000300", 0, (0, 1), b"", "conic"),
        (132, "native", "03000300", 0, (0, 1), b"", "spline"),
        (200, "line", "04000200", 1, (0, 1), b"", "line"),
        (
            200,
            "line",
            "04000200",
            1,
            (0, 1),
            b"cptsSplineList_c",
            "spline",
        ),
    ),
)
def test_broad_marker_curve_semantics_use_record_structure(
    length: int,
    semantic: str,
    locus: str,
    role: int,
    endpoints: tuple[int, int],
    record: bytes,
    expected: str,
) -> None:
    data = record.ljust(length, b"\0")
    marker = NativeMarker(
        0,
        length,
        "ffff1f0003",
        0,
        locus,
        role,
        None,
        None,
        None,
        None,
        endpoints,
        False,
        semantic,
        data,
    )
    assert _marker_curve_semantic(marker) == expected


def test_broad_marker_curve_semantics_use_circular_sentinel() -> None:
    data = bytearray(140)
    data[86:102] = b"\xfe\xff\xff\xff" * 4
    marker = NativeMarker(
        0,
        len(data),
        "ffff1f0003",
        0,
        "03000300",
        0,
        None,
        None,
        None,
        None,
        (4, 4),
        False,
        "native",
        bytes(data),
    )
    assert _marker_curve_semantic(marker) == "circle"


def test_adapter_preserves_unknown_locus_before_resolving_native_indices() -> None:
    document = read_sldprt(CORPUS / "Engine_Block.SLDPRT", include_brep=False)
    sketch = document.sketch("sldprt:sketch:200")
    unknown = next(
        entity
        for entity in sketch.entities
        if entity.provenance and entity.provenance.spans[0].offset == 196708
    )
    assert isinstance(unknown.geometry, NativeGeometry)
    assert unknown.geometry.data["locus"] == "03000300"
    assert unknown.geometry.data["record_data"]
    entity = next(
        entity
        for entity in sketch.entities
        if entity.provenance and entity.provenance.spans[0].offset == 198158
    )
    assert isinstance(entity.geometry, LineGeometry)


def test_every_feature_without_typed_semantics_has_a_native_definition() -> None:
    document = read_sldprt(SAMPLE, include_brep=False)
    assert all(feature.definition is not None for feature in document.feature_timeline)
    native = [
        feature.definition
        for feature in document.feature_timeline
        if isinstance(feature.definition, NativeFeatureDefinition)
    ]
    assert native
    assert all(definition.type_id for definition in native)
    assert any(definition.object_data["record_data"] for definition in native)


def test_unknown_native_constraint_is_retained_without_mapped_references() -> None:
    sketch = NativeSketch(
        object_id=7,
        name="Future sketch",
        support_plane_id=1,
        native_offset=10,
        native_end=20,
        markers=(),
        profiles=(),
        dimensions=(),
        constraints=(
            NativeConstraint(
                id="7:future:1",
                kind="native_4096",
                references=("future-reference",),
                parameter=None,
                value=None,
                native_offset=12,
                native_code=4096,
            ),
        ),
    )
    constraints = _sketch_constraints(sketch, {}, set())
    assert len(constraints) == 1
    assert constraints[0].references == ()
    assert constraints[0].attributes["native_references"] == ("future-reference",)


def test_adapter_accepts_memory_and_roundtrips_neutral_json() -> None:
    source = SAMPLE.read_bytes()
    adapter = SldprtAdapter()
    assert adapter.probe(source).confidence == 1.0
    document = read_sldprt(source, include_brep=False)
    restored = type(document).from_json(document.to_json())
    assert restored.validate() == ()
    assert restored.source.path == "<memory>"
    assert restored.feature("sldprt:feature:116").name == "Fillet1"


def test_entire_local_solidworks_corpus_decodes() -> None:
    examples = Path(__file__).resolve().parents[2] / "examples"
    parts = sorted(
        path
        for path in examples.rglob("*")
        if path.is_file()
        and path.suffix.lower() == ".sldprt"
        and not path.name.startswith("~$")
    )
    documents = [read_sldprt(path) for path in parts]
    assert len(parts) == 111
    assert all(document.validate() == () for document in documents)
    assert sum(len(document.brep_payloads) for document in documents) == 909
    assert all(
        payload.role == PayloadRole.BREP
        for document in documents
        for payload in document.brep_payloads
    )
    assert any(
        not payload.source_stream.endswith("Partition")
        for document in documents
        for payload in document.brep_payloads
    )


def test_adapter_handles_positive_zero_plane_frame_variant() -> None:
    document = read_sldprt(CORPUS / "Addons" / "Alternator.SLDPRT", include_brep=False)
    plane = document.plane("sldprt:plane:289")
    assert plane.transform.origin.z == pytest.approx(50.0)
    assert plane.transform.z_axis.z == 1.0
    assert document.sketch("sldprt:sketch:292").support_plane_id == plane.id
    assert document.validate() == ()


def test_adapter_assigns_occurrence_ids_to_duplicate_dimensions() -> None:
    document = read_sldprt(
        CORPUS / "Cylinder_heads" / "Spark_plug.SLDPRT",
        include_brep=False,
    )
    assert document.parameter("sldprt:parameter:107:D5").value.value == 2.0
    assert document.parameter("sldprt:parameter:107:D5:2").value.value == 2.0
    assert document.validate() == ()
