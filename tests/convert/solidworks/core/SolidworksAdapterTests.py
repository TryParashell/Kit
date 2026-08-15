# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from pathlib import Path as FilePath
import struct as StructLib
import pytest as PytestLib
from convert.adapters.solidworks import (
    SldprtAdapter,
    SldprtArchive,
    build_sldprt as BuildSldprt,
    read_sldprt as ReadSldprt,
)
from convert.adapters.solidworks.core.Adapter import (
    _FEATURE_KIND_BY_NATIVE as Native,
    _final_body_feature_id as FinalBodyFeatureId,
    _feature_kind as FeatureKindA,
    _is_geometry_brep_payload as IsGeometryBrepPayload,
    _marker_curve_semantic as MarkerCurveSemantic,
    _sketch as Sketch,
    _sketch_constraints as SketchConstraints,
    _solid_body_feature as SolidBodyFeature,
    _timeline as Timeline,
)
from convert.adapters.solidworks.container.Container import (
    container_signatures as ContainerSignatures,
)
from convert.adapters.solidworks.container.Format import (
    CLASS_MARKER as Marker,
    SERIALIZED_STRING_MARKER as MarkerA,
)
from convert.adapters.solidworks.core.Native import (
    NativeConstraint,
    NativeFeature,
    NativeMarker,
    NativeModel,
    NativeOperation,
    NativePlane,
    NativeSketch,
    _decode_planes as DecodePlanes,
    _native_scale_factors as NativeScaleFactors,
    _parse_native_equations as ParseNativeEquations,
    _parse_keywords as ParseKeywords,
    _reference_plane_ids as ReferencePlaneIds,
    _constraints as Constraints,
    _profiles as Profiles,
    decode_native_model as DecodeNativeModel,
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

# centralizes shared evidence so every related assertion uses one value
KSample = (
    FilePath(__file__).resolve().parents[4] / "examples" / ".SLDPRT" / "example.SLDPRT"
)

# centralizes shared evidence so every related assertion uses one value
KCorpus = FilePath(__file__).resolve().parents[4] / "examples" / "Random"

# centralizes shared evidence so every related assertion uses one value
KTwoZeroTwoSix = frozenset(
    (
        ItemValueA.casefold()
        for ItemValueA in "\nAsmExploder\nCompExplodeStep\nExplodeLineProfileFeature\nInContextFeatHolder\nMagneticGroundPlane\nMateCamTangent\nMateCoincident\nMateConcentric\nMateDistanceDim\nMateGearDim\nMateHinge\nMateInPlace\nMateLimitDistanceDim\nMateLinearCoupler\nMateLock\nMateParallel\nMatePerpendicular\nMatePlanarAngleDim\nMateProfileCenter\nMateRackPinionDim\nMateScrew\nMateSlot\nMateSymmetric\nMateTangent\nMateUniversalJoint\nMateWidth\nPosGroupFolder\nReference\nReferencePattern\nSmartComponentFeature\nAdvHoleWzd\nAPattern\nBaseBody\nBending\nBlend\nBlendCut\nBodyExplodeStep\nBoss\nBossThin\nChamfer\nCirPattern\nCombineBodies\nCosmeticThread\nCosmeticWeldBead\nCreateAssemFeat\nCurvePattern\nCut\nCutThin\nDeform\nDeleteBody\nDelFace\nDerivedCirPattern\nDerivedHolePattern\nDerivedLPattern\nDimPattern\nDome\nDraft\nEdgeMerge\nEmboss\nExtrusion\nFillet\nHelix\nHoleSeries\nHoleWzd\nImported\nLocalChainPattern\nLocalCirPattern\nLocalCurvePattern\nLocalLPattern\nLocalSketchPattern\nLPattern\nMacroFeature\nMirrorCompFeat\nMirrorPattern\nMirrorSolid\nMirrorStock\nMoveCopyBody\nNetBlend\nPrtExploder\nPunch\nReplaceFace\nRevCut\nRevolution\nRevolutionThin\nRib\nRip\nSculpt\nShape\nShell\nSketchHole\nSketchPattern\nSplit\nSplitBody\nStock\nSweep\nSweepCut\nSweepThread\nTablePattern\nThicken\nThickenCut\nVarFillet\nBendTableAchor\nBomFeat\nBomTemplate\nDetailCircle\nDrBreakoutSectionLine\nDrSectionLine\nGeneralTableAnchor\nHoleTableAnchor\nLiveSection\nPunchTableAnchor\nRevisionTableAnchor\nWeldmentTableAnchor\nFamilyTableFeat\nWeldTableAnchor\nBlockFolder\nCommentsFolder\nCosmeticWeldSubFolder\nCutListFolder\nFeatSolidBodyFolder\nFeatSurfaceBodyFolder\nFtrFolder\nInsertedFeatureFolder\nMateReferenceGroupFolder\nProfileFtrFolder\nRefAxisFtrFolder\nRefPlaneFtrFolder\nSketchSliceFolder\nSolidBodyFolder\nSubAtomFolder\nSubWeldFolder\nSurfaceBodyFolder\nTemplateFlatPattern\nMBimport\nAttribute\nBlockDef\nCurveInFile\nGridFeature\nLibraryFeature\nScale\nSensor\nViewBodyFeature\nCavity\nMoldCoreCavitySolids\nMoldPartingGeom\nMoldPartLine\nMoldShutOffSrf\nSideCore\nXformStock\nAEM3DContact\nAEMGravity\nAEMLinearDamper\nAEMLinearMotor\nAEMLinearSpring\nAEMRotationalMotor\nAEMTorque\nAEMTorsionalDamper\nAEMTorsionalSpring\nSimPlotFeature\nSimPlotXAxisFeature\nSimPlotYAxisFeature\nSimResultFolder\nBoundingBox\nCenterOfMass\nCoordSys\nGroundPlane\nRefAxis\nRefPlane\nAmbientLight\nCameraFeature\nDirectionLight\nPointLight\nSpotLight\nSMBaseFlange\nBreakCorner\nCornerTrim\nCrossBreak\nEdgeFlange\nFlatPattern\nFlattenBends\nFold\nFormToolInstance\nHem\nJog\nLoftedBend\nNormalCut\nOneBend\nProcessBends\nSheetMetal\nSketchBend\nSM3dBend\nSMGusset\nSMMiteredFlange\nSolidToSheetMetal\nTemplateSheetMetal\nToroidalBend\nUnFold\n3DProfileFeature\n3DSplineCurve\nCompositeCurve\nImportedCurve\nPLine\nProfileFeature\nRefCurve\nRefPoint\nSketchBlockDef\nSketchBlockInst\nSketchBitmap\nBlendRefSurface\nExtendRefSurface\nExtruRefSurface\nFillRefSurface\nFlattenSurface\nMidRefSurface\nOffsetRefSuface\nPlanarSurface\nRadiateRefSurface\nRefSurface\nRevolvRefSurf\nRuledSrfFromEdge\nSewRefSurface\nSurfCut\nSweepRefSurface\nTrimRefSurface\nUnTrimRefSurf\nEndCap\nStrctSysBtwPtsMbrFeat\nStrctSysCnrFeat\nStrctSysCnrGrpFeat\nStrctSysCnrMgmtFeat\nStrctSysFeat\nStrctSysGrpFeat\nStrctSysPathSegMbrFeat\nStrctSysPtToMem\nStrctSysRefPlnMbrFeat\nStrctSysSkPtLenMbrFeat\nStrctSysSupPlnMbrFeat\nStrctSysSurfPlnMbrFeat\nAdvStructMember\nGusset\nWeldBeadFeat\nWeldCornerFeat\nWeldMemberFeat\nWeldmentFeature\nWeldmentTableFeat\nRound fillet corner\n".splitlines()
        if ItemValueA
    )
)


# keeps this focused behavior isolated so regressions remain immediately visible
def ResolvedNR(
    NameText: str, ObjectId: int, Family: int = 0, Operation: int = 0, Schema: int = 0
) -> bytes:
    Encoded = NameText.encode("utf-16le")
    return (
        bytes.fromhex("0480fffeff")
        + bytes((len(NameText),))
        + Encoded
        + StructLib.pack("<IHBBI", 0, Family, Operation, Schema, ObjectId)
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAAESC() -> None:
    assert SldprtAdapter().info.capabilities == frozenset(Capability)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPCRTDD() -> None:
    WithoutBrep = ReadSldprt(KSample, include_brep=False)
    Expected = frozenset(
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
    assert WithoutBrep.capabilities == Expected
    WithBrep = ReadSldprt(KSample, include_brep=True)
    assert WithBrep.capabilities == Expected | {
        Capability.BREP,
        Capability.NATIVE_PAYLOADS,
    }


# keeps this focused behavior isolated so regressions remain immediately visible
def TestOFTRIE() -> None:
    assert len(KTwoZeroTwoSix) == 246
    assert KTwoZeroTwoSix <= Native.keys()
    assert set(FeatureKind) - set(Native.values()) == {
        FeatureKind.PRIMITIVE,
        FeatureKind.REVERSE,
    }
    assert Native["macrofeature"] == FeatureKind.NATIVE
    assert Native["round fillet corner"] == FeatureKind.FILLET


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBCDUPS() -> None:
    assert IsGeometryBrepPayload(
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
    assert not IsGeometryBrepPayload(
        BrepPayload("2", "parasolid", "solid", "schema-2040", "", data=b"opaque")
    )
    assert not IsGeometryBrepPayload(
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


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPSDDNDOIN() -> None:
    Archive = SldprtArchive.open(KSample)
    Streams = Archive.streams
    OriginalName = "Contents/Config-0-Partition"
    Streams["Contents/CustomerGeometryBlob"] = Streams.pop(OriginalName)
    Renamed = BuildSldprt(
        Streams,
        file_id=Archive.file_id,
        format_version=Archive.format_version,
        signatures=ContainerSignatures(KSample.read_bytes()),
    )
    Document = ReadSldprt(Renamed)
    assert len(Document.brep_payloads) == 3
    assert all((Payload.role == PayloadRole.BREP for Payload in Document.brep_payloads))
    assert (
        sum(
            (
                Payload.source_stream == "Contents/CustomerGeometryBlob"
                for Payload in Document.brep_payloads
            )
        )
        == 2
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestSBFDIS() -> None:
    BodyFolder = NativeFeature(
        object_id=9,
        name="Corps solides renommés",
        kind="SolidBodyFolder",
        xml_tag="Feature",
        native_offset=None,
        native_end=None,
        properties={"Type": "SolidBodyFolder"},
        dimensions=(),
    )
    assert SolidBodyFeature((BodyFolder,)) is BodyFolder


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFBFSCCSK() -> None:
    Reference = FeatureStep("reference", "Plane", FeatureKind.REFERENCE, 0)
    Extrusion = FeatureStep("extrusion", "Boss", FeatureKind.EXTRUSION, 1)
    Revolution = FeatureStep("revolution", "Revolve", FeatureKind.REVOLUTION, 2)
    TrailingReference = FeatureStep(
        "trailing-reference", "Folder", FeatureKind.REFERENCE, 3
    )
    TimelineA = (Reference, Extrusion, Revolution, TrailingReference)
    assert FinalBodyFeatureId(TimelineA, frozenset()) == Revolution.id


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFBFSRSAUF() -> None:
    Opaque = FeatureStep("opaque", "Vendor feature", FeatureKind.NATIVE, 0)
    Reference = FeatureStep("reference", "Folder", FeatureKind.REFERENCE, 1)
    TimelineA = (Opaque, Reference)
    assert FinalBodyFeatureId(TimelineA, frozenset({Opaque.id})) == Opaque.id
    assert FinalBodyFeatureId((Opaque,), frozenset()) == Opaque.id


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTDPPS() -> None:
    Principal = NativeFeature(
        object_id=1,
        name="Référence primaire",
        kind="Plane",
        xml_tag="Feature",
        native_offset=None,
        native_end=None,
        properties={"Type": "Plane"},
        dimensions=(),
    )
    Extrusion = NativeFeature(
        object_id=2,
        name="Volume",
        kind="Extrusion",
        xml_tag="Feature",
        native_offset=10,
        native_end=20,
        properties={"Type": "Extrusion"},
        dimensions=(),
    )
    OffsetPlane = NativeFeature(
        object_id=3,
        name="Référence décalée",
        kind="Plane",
        xml_tag="Feature",
        native_offset=30,
        native_end=40,
        properties={"Type": "Plane"},
        dimensions=(),
    )
    Frame = ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    ModelDoc = NativeModel(
        configurations=(),
        features=(Principal, Extrusion, OffsetPlane),
        planes=(
            NativePlane(1, Principal.name, *Frame, None, None, True),
            NativePlane(3, OffsetPlane.name, *Frame, 30, 10, False),
        ),
        sketches=(),
        operations=(
            NativeOperation(
                object_id=2,
                name=Extrusion.name,
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
    TimelineA = Timeline(ModelDoc, ())
    assert TimelineA[0].input_feature_ids == ()
    assert TimelineA[2].input_feature_ids == (TimelineA[1].id,)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPPUNRAR() -> None:
    Features = [
        NativeFeature(
            object_id=Index,
            name=NameText,
            kind=KindInfo,
            xml_tag=TagInfo,
            native_offset=Offset,
            native_end=Offset,
            properties=Properties,
            dimensions=(),
        )
        for Index, NameText, KindInfo, TagInfo, Properties, Offset in (
            (99, "Later Datum", "Plane", "Feature", {"Type": "Plane"}, 100),
            (20, "Primary", "Plane", "Feature", {"Type": "Plane"}, 10),
            (21, "Horizontal", "Plane", "Feature", {"Type": "Plane"}, 20),
            (22, "Side", "Plane", "Feature", {"Type": "Plane"}, 30),
            (23, "Centre", "Sketch", "Sketch", {"Type": "Origin"}, 40),
        )
    ]
    Planes = DecodePlanes(b"", Features)
    assert [Plane.object_id for Plane in Planes] == [20, 21, 22]
    assert [Plane.name for Plane in Planes] == ["Primary", "Horizontal", "Side"]
    assert [Plane.normal for Plane in Planes] == [
        (0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0),
        (1.0, 0.0, 0.0),
    ]


# keeps this focused behavior isolated so regressions remain immediately visible
def TestKHDNAFFT() -> None:
    Configurations, Features = ParseKeywords(
        b'<?xml version="1.0" encoding="UTF-8"?>\n<Keywords>\n  <Configuration id="0" Name="Default" />\n  <Feature id="1" Name="Datum" Type="Plane" />\n  <HoleWizard id="2" Name="Tapped Hole">\n    <Dimension Name="D1">12.5mm</Dimension>\n  </HoleWizard>\n  <FutureFeature id="3" Name="Vendor Operation" Vendor="Parashell">\n    <FutureChild id="4" Name="Nested Operation" />\n  </FutureFeature>\n  <Dimension id="5" Name="Not a Feature">7mm</Dimension>\n  <Invalid id="not-an-integer" Name="Invalid" />\n</Keywords>'
    )
    assert [Configuration.name for Configuration in Configurations] == ["Default"]
    assert [
        (Feature.object_id, Feature.kind, Feature.xml_tag) for Feature in Features
    ] == [
        (1, "Plane", "Feature"),
        (2, "HoleWizard", "HoleWizard"),
        (3, "FutureFeature", "FutureFeature"),
        (4, "FutureChild", "FutureChild"),
    ]
    assert Features[1].dimensions[0].value_mm == 12.5
    assert Features[2].properties["Vendor"] == "Parashell"
    assert FeatureKindA(Features[1]) == FeatureKind.HOLE
    assert FeatureKindA(Features[2]) == FeatureKind.NATIVE


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFRBBOIAMNAR() -> None:
    First = ResolvedNR("Binary original", 41)
    Second = ResolvedNR("Binary fallback", 42)
    ModelDoc = DecodeNativeModel(
        b'<?xml version="1.0" encoding="UTF-8"?>\n<Keywords>\n  <FutureFeature id="41" Name="Renamed display" />\n  <FutureFeature id="42" />\n  <FutureFeature id="43" />\n</Keywords>',
        First + Second,
    )
    ByIdInfo = {Feature.object_id: Feature for Feature in ModelDoc.features}
    assert ByIdInfo[41].name == "Renamed display"
    assert ByIdInfo[41].native_offset == 0
    assert ByIdInfo[41].native_end == len(First)
    assert ByIdInfo[41].data == First
    assert ByIdInfo[42].name == "Binary fallback"
    assert ByIdInfo[42].native_offset == len(First)
    assert ByIdInfo[42].data == Second
    assert ByIdInfo[43].name == "FutureFeature 43"
    assert ByIdInfo[43].native_offset is None


# keeps this focused behavior isolated so regressions remain immediately visible
def TestODUROAFS() -> None:
    Extrusion = ResolvedNR("Extrusion native label", 10, 320, 0, 192)
    Fillet = ResolvedNR("Fillet native label", 20)
    ModelDoc = DecodeNativeModel(
        '<?xml version="1.0" encoding="UTF-8"?>\n<Keywords>\n  <Extrusion id="10" Name="Volume localisé">\n    <Dimension Name="Profondeur">12.5</Dimension>\n  </Extrusion>\n  <Feature id="20" Name="Congé localisé" Type="Fillet">\n    <Dimension Name="Rayon">0.75</Dimension>\n  </Feature>\n</Keywords>'.encode(
            "utf-8"
        ),
        Extrusion + Fillet,
    )
    Operations = {Operation.object_id: Operation for Operation in ModelDoc.operations}
    assert Operations[10].length_mm == 12.5
    assert Operations[20].radius_mm == 0.75
    Features = {Feature.object_id: Feature for Feature in ModelDoc.features}
    assert Features[10].dimensions[0].kind == "length"
    assert Features[20].dimensions[0].kind == "radius"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCDSDNRDTON() -> None:
    Archive = SldprtArchive.open(KSample)
    Keywords = Archive.require("swXmlContents/KeyWords").replace(
        b'Name="D1">&lt;MOD-DIAM&gt;5.5', b'Name="Diametre">5.5'
    )
    ModelDoc = DecodeNativeModel(
        Keywords, Archive.require("Contents/Config-0-ResolvedFeatures")
    )
    SketchA = next(
        (ItemValue for ItemValue in ModelDoc.sketches if ItemValue.object_id == 88)
    )
    assert SketchA.profiles[0].coordinates[2] == PytestLib.approx(2.75)
    assert SketchA.profiles[0].parameter_name == "Diametre"
    assert SketchA.profiles[0].dimension_kind == "diameter"
    assert SketchA.dimensions[0].kind == "diameter"
    assert SketchA.dimensions[0].native_offset is not None


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    ("NativeKind", "NeutralKind"),
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
def TestNFTMTNK(NativeKind: str, NeutralKind: FeatureKind) -> None:
    Feature = NativeFeature(
        object_id=1,
        name="Feature",
        kind=NativeKind,
        xml_tag="Feature",
        native_offset=None,
        native_end=None,
        properties={},
        dimensions=(),
    )
    assert FeatureKindA(Feature) == NeutralKind


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCHWFRTT() -> None:
    Document = ReadSldprt(KCorpus / "Engine_Block.SLDPRT", include_brep=False)
    Holes = [
        Feature
        for Feature in Document.feature_timeline
        if Feature.kind == FeatureKind.HOLE
    ]
    assert len(Holes) == 8
    assert {Feature.attributes["xml_tag"] for Feature in Holes} == {"HoleWizard"}
    assert all((Feature.attributes["native_type"] == "HoleWizard" for Feature in Holes))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCRNS() -> None:
    Archive = SldprtArchive.open(KSample)
    assert Archive.file_id == 1901848975
    assert Archive.format_version == 4
    assert Archive.require("Contents/Config-0-ResolvedFeatures")
    assert b"<?xml" in Archive.require("swXmlContents/KeyWords")
    assert Archive.require("Contents/Config-0-Partition")


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCAVRSD() -> None:
    SourceDoc = bytearray(KSample.read_bytes())
    Original = SldprtArchive.from_bytes(SourceDoc)
    Replacement = bytes.fromhex("01020304")
    for RecordInfo in Original.records:
        SourceDoc[RecordInfo.offset + 6 : RecordInfo.offset + 10] = Replacement
    Recovered = SldprtArchive.from_bytes(SourceDoc)
    assert len(Recovered.records) == len(Original.records)
    assert {RecordInfo.signature[6:] for RecordInfo in Recovered.records} == {
        Replacement
    }
    assert Recovered.require("Contents/Config-0-ResolvedFeatures") == Original.require(
        "Contents/Config-0-ResolvedFeatures"
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARPHAB() -> None:
    Document = ReadSldprt(KSample)
    assert Document.validate() == ()
    assert len(Document.configurations) == 1
    assert len(Document.parameters) == 26
    assert len(Document.support_planes) == 7
    assert len(Document.sketches) == 5
    assert len(Document.feature_timeline) == 39
    assert len(Document.brep_payloads) == 3
    assert [Payload.kind for Payload in Document.brep_payloads] == [
        "partition",
        "partition",
        "deltas",
    ]
    assert [len(Payload.data or b"") for Payload in Document.brep_payloads] == [
        1513,
        30850,
        23150,
    ]
    assert (
        Document.brep_payloads[1].sha256
        == "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6"
    )
    assert (
        Document.brep_payloads[2].sha256
        == "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7"
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARFOAD() -> None:
    Document = ReadSldprt(KSample, include_brep=False)
    Operations = {
        Feature.name: Feature
        for Feature in Document.feature_timeline
        if Feature.name
        in {
            "Boss-Extrude1",
            "Cut-Extrude1",
            "Boss-Extrude2",
            "Cut-Extrude2",
            "Boss-Extrude3",
            "Fillet1",
        }
    }
    assert Operations["Boss-Extrude1"].operation == BooleanOperation.JOIN
    assert Operations["Cut-Extrude1"].operation == BooleanOperation.CUT
    assert Operations["Boss-Extrude2"].operation == BooleanOperation.JOIN
    assert Operations["Cut-Extrude2"].operation == BooleanOperation.CUT
    assert Operations["Boss-Extrude3"].operation == BooleanOperation.JOIN
    assert isinstance(Operations["Boss-Extrude1"].definition, ExtrusionFeature)
    assert isinstance(Operations["Fillet1"].definition, FilletFeature)
    assert Operations["Boss-Extrude1"].definition.length.value == 20.0
    assert Operations["Cut-Extrude1"].definition.length.value == 0.25
    assert Operations["Boss-Extrude2"].definition.length.value == 0.75
    assert Operations["Cut-Extrude2"].definition.length.value == 9.0
    assert Operations["Boss-Extrude3"].definition.length.value == 6.0
    assert Operations["Fillet1"].definition.radius.value == 0.25
    assert Operations["Boss-Extrude1"].attributes["length_mm"] == 20.0
    assert Operations["Cut-Extrude1"].attributes["length_mm"] == 0.25
    assert Operations["Boss-Extrude2"].attributes["length_mm"] == 0.75
    assert Operations["Cut-Extrude2"].attributes["length_mm"] == 9.0
    assert Operations["Boss-Extrude3"].attributes["length_mm"] == 6.0
    assert Operations["Fillet1"].attributes["radius_mm"] == 0.25
    assert Operations["Fillet1"].selection_ids == ("sldprt:selection:116:edge:1",)
    assert Document.parameter("sldprt:parameter:88:D1").value.value == 5.5
    assert Document.parameter("sldprt:parameter:106:D1").value.value == 2.1


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARSFAP() -> None:
    Document = ReadSldprt(KSample, include_brep=False)
    PlaneTwo = Document.plane("sldprt:plane:62")
    assert PlaneTwo.transform.origin.x == PytestLib.approx(124.3)
    assert PlaneTwo.transform.x_axis.z == -1.0
    assert PlaneTwo.transform.y_axis.y == 1.0
    assert PlaneTwo.transform.z_axis.x == 1.0
    SketchOne = Document.sketch("sldprt:sketch:26")
    Profile = [
        Entity
        for Entity in SketchOne.entities
        if Entity.id in SketchOne.closed_profile_entity_ids[0]
    ]
    assert len(Profile) == 4
    assert isinstance(Profile[0].geometry, LineGeometry)
    assert Profile[0].geometry.start.x == PytestLib.approx(-124.3)
    assert Profile[0].geometry.start.y == PytestLib.approx(-89.75)
    SketchThree = Document.sketch("sldprt:sketch:63")
    assert len(SketchThree.closed_profile_entity_ids) == 3
    SketchFour = Document.sketch("sldprt:sketch:88")
    Circle = next(
        (
            Entity
            for Entity in SketchFour.entities
            if Entity.id == SketchFour.closed_profile_entity_ids[0][0]
        )
    )
    assert Circle.geometry.center.x == PytestLib.approx(10.0)
    assert Circle.geometry.center.y == PytestLib.approx(81.631746131982)
    assert Circle.geometry.radius == PytestLib.approx(2.75)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARCGWG() -> None:
    Document = ReadSldprt(KSample, include_brep=False)
    ExpectedLineCounts = {
        "Sketch1": 2,
        "Sketch2": 2,
        "Sketch3": 6,
        "Sketch4": 1,
        "Sketch6": 2,
    }
    for SketchA in Document.sketches:
        Lines = [
            Entity.geometry
            for Entity in SketchA.entities
            if Entity.construction and isinstance(Entity.geometry, LineGeometry)
        ]
        assert len(Lines) == ExpectedLineCounts[SketchA.name]
    SketchOne = Document.sketch("sldprt:sketch:26")
    Diagonals = [
        Entity.geometry
        for Entity in SketchOne.entities
        if Entity.construction and isinstance(Entity.geometry, LineGeometry)
    ]
    assert {
        (LineInfo.start.x, LineInfo.start.y, LineInfo.end.x, LineInfo.end.y)
        for LineInfo in Diagonals
    } == {(124.3, 89.75, -124.3, -89.75), (124.3, -89.75, -124.3, 89.75)}
    SketchFour = Document.sketch("sldprt:sketch:88")
    Construction = [
        Entity.geometry
        for Entity in SketchFour.entities
        if Entity.construction and isinstance(Entity.geometry, LineGeometry)
    ]
    assert (
        Construction[0].start.x,
        Construction[0].start.y,
        Construction[0].end.x,
        Construction[0].end.y,
    ) == PytestLib.approx((10.0, 89.75, 10.0, -89.75))
    assert all(
        (
            not str(Constraint.kind).startswith("native_")
            for Constraint in SketchFour.constraints
        )
    )
    assert any(
        (isinstance(Entity.geometry, NativeGeometry) for Entity in SketchOne.entities)
    )
    SketchSix = Document.sketch("sldprt:sketch:106")
    assert any(
        (
            isinstance(Entity.geometry, NativeGeometry)
            and Entity.geometry.data.get("record_data")
            for Entity in SketchSix.entities
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAAPCP() -> None:
    Document = ReadSldprt(KCorpus / "Cover.SLDPRT", include_brep=False)
    SketchA = Document.sketch("sldprt:sketch:26")
    Entities = {Entity.id: Entity.geometry for Entity in SketchA.entities}
    ProfilesA = [Entities[Profile[0]] for Profile in SketchA.closed_profile_entity_ids]
    assert all((isinstance(Profile, CircleGeometry) for Profile in ProfilesA))
    assert [Profile.radius for Profile in ProfilesA] == PytestLib.approx((16.0, 184.0))
    assert (ProfilesA[0].center.x, ProfilesA[0].center.y) == PytestLib.approx(
        (15.300876095409, 4.677947275564)
    )
    assert (ProfilesA[1].center.x, ProfilesA[1].center.y) == PytestLib.approx(
        (-130.107647738324, 130.107647738325)
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestABDOBMP() -> None:
    Document = ReadSldprt(KCorpus / "Cover.SLDPRT", include_brep=False)
    SketchA = Document.sketch("sldprt:sketch:77")
    ConstraintsA = {
        Constraint.parameter_id: Constraint
        for Constraint in SketchA.constraints
        if Constraint.parameter_id
    }
    assert tuple(
        (
            Reference.entity_id
            for Reference in ConstraintsA["sldprt:parameter:77:D2"].references
        )
    ) == ("sldprt:sketch:77:native:90347", "sldprt:sketch:77:native:87930")
    assert tuple(
        (
            Reference.entity_id
            for Reference in ConstraintsA["sldprt:parameter:77:D6"].references
        )
    ) == ("sldprt:sketch:77:native:87322", "sldprt:sketch:77:native:87484")
    Radial = Document.sketch("sldprt:sketch:27")
    RadialConstraints = {
        Constraint.parameter_id: Constraint
        for Constraint in Radial.constraints
        if Constraint.parameter_id
    }
    assert RadialConstraints["sldprt:parameter:27:D2"].references == ()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestARLEBNMI() -> None:
    Document = ReadSldprt(KCorpus / "Engine_Block.SLDPRT", include_brep=False)
    SketchA = Document.sketch("sldprt:sketch:139")
    Expected = {
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
    Entities = {
        Entity.provenance.spans[0].offset: Entity for Entity in SketchA.entities
    }
    for Offset, (Start, EndInfo) in Expected.items():
        Geometry = Entities[Offset].geometry
        assert isinstance(Geometry, LineGeometry)
        assert (Geometry.start.x, Geometry.start.y) == PytestLib.approx(Start)
        assert (Geometry.end.x, Geometry.end.y) == PytestLib.approx(EndInfo)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestADLRRFNNS() -> None:
    ValueList = (
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
    Markers = tuple(
        (
            NativeMarker(
                Offset,
                Length,
                "ffff1f0003",
                NativeKind,
                "05000100",
                1,
                None,
                None,
                None,
                Coordinates,
                Endpoints,
                False,
                Semantic,
            )
            for Offset, Length, NativeKind, Coordinates, Endpoints, Semantic in ValueList
        )
    )
    ProfilesA, UsedInfo, Dimensions = Profiles(list(Markers), ())
    assert Dimensions == ()
    assert UsedInfo == {MarkerB.offset for MarkerB in Markers}
    assert len(ProfilesA) == 1
    assert ProfilesA[0].coordinates == (-20.0, -10.0, 20.0, 10.0)
    assert ProfilesA[0].marker_offsets[:4] == (860, 1136, 1044, 952)
    Feature = NativeFeature(26, "Sketch1", "Sketch", "Sketch", 0, 1344, {}, ())
    ConstraintsA = Constraints(Feature, Markers, ProfilesA)
    SketchA = NativeSketch(
        26, "Sketch1", 2, 0, 1344, Markers, ProfilesA, (), ConstraintsA
    )
    Decoded = Sketch(SketchA, set())
    assert len(Decoded.entities) == 4
    assert all(
        (isinstance(Entity.geometry, LineGeometry) for Entity in Decoded.entities)
    )
    assert len(Decoded.constraints) == 8
    assert {str(Constraint.kind) for Constraint in Decoded.constraints} == {
        "coincident",
        "horizontal",
        "vertical",
    }
    assert Decoded.closed_profile_entity_ids == (
        tuple((Entity.id for Entity in Decoded.entities)),
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBSLBDRNRS() -> None:

    # keeps this focused behavior isolated so regressions remain immediately visible
    def Declaration(NameText: str) -> bytes:
        return Marker + StructLib.pack("<H", len(NameText)) + NameText.encode("ascii")

    EquationSource = '"Width" = 40mm'
    EquationData = (
        Declaration("moRelMgr_c")
        + Declaration("moRelation_c")
        + MarkerA
        + bytes((len(EquationSource),))
        + EquationSource.encode("utf-16le")
    )
    Equations = ParseNativeEquations(EquationData, 1, "Contents/Config-1")
    assert [
        (ItemValue.lhs, ItemValue.rhs, ItemValue.native_stream)
        for ItemValue in Equations
    ] == [("Width", "40mm", "Contents/Config-1")]
    ReferenceData = (
        b"head" + b"\x00" * 6 + StructLib.pack("<II", 1, 2) + b"\x00\x05tail"
    )
    assert ReferencePlaneIds(
        ReferenceData, 0, len(ReferenceData), 35, frozenset({2, 3, 35})
    ) == (2,)
    ScaleData = (
        StructLib.pack("<I3d", 1, 1.1, 1.1, 1.1)
        + b"\x00" * 8
        + StructLib.pack("<H", 32940)
    )
    assert NativeScaleFactors(ScaleData, 0, len(ScaleData)) == PytestLib.approx(
        (1.1, 1.1, 1.1)
    )
    assert NativeScaleFactors(ScaleData[:-1], 0, len(ScaleData) - 1) is None


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBSRUSEI() -> None:
    ValueList = (
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
    Markers = [
        NativeMarker(
            offset=100 + Index * 100,
            length=92,
            prefix="ffff1f0003",
            native_kind=NativeKind,
            locus="04000200" if Index in {2, 7} else "05000100",
            profile_role=RoleInfo,
            state=1.0,
            object_index=Index,
            local_id=Index,
            coordinates_mm=Coordinates,
            endpoint_indices=Endpoints,
            construction=RoleInfo == 2,
            semantic="line" if Index == 7 else "native",
        )
        for Index, (Coordinates, Endpoints, NativeKind, RoleInfo) in enumerate(
            ValueList
        )
    ]
    ProfilesA, UsedInfo, Dimensions = Profiles(Markers, ())
    assert Dimensions == ()
    assert [(ItemValue.kind, ItemValue.coordinates) for ItemValue in ProfilesA] == [
        ("rectangle", (10.0, -25.0, 25.0, 25.0))
    ]
    assert UsedInfo == {900, 1000, 1100, 1200}


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    ("Length", "Semantic", "Locus", "RoleInfo", "Endpoints", "RecordInfo", "Expected"),
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
        (200, "line", "04000200", 1, (0, 1), b"cptsSplineList_c", "spline"),
    ),
)
def TestBMCSURS(
    Length: int,
    Semantic: str,
    Locus: str,
    RoleInfo: int,
    Endpoints: tuple[int, int],
    RecordInfo: bytes,
    Expected: str,
) -> None:
    DataValue = RecordInfo.ljust(Length, b"\x00")
    MarkerB = NativeMarker(
        0,
        Length,
        "ffff1f0003",
        0,
        Locus,
        RoleInfo,
        None,
        None,
        None,
        None,
        Endpoints,
        False,
        Semantic,
        DataValue,
    )
    assert MarkerCurveSemantic(MarkerB) == Expected


# keeps this focused behavior isolated so regressions remain immediately visible
def TestBMCSUCS() -> None:
    DataValue = bytearray(140)
    DataValue[86:102] = b"\xfe\xff\xff\xff" * 4
    MarkerB = NativeMarker(
        0,
        len(DataValue),
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
        bytes(DataValue),
    )
    assert MarkerCurveSemantic(MarkerB) == "circle"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAPULBRNI() -> None:
    Document = ReadSldprt(KCorpus / "Engine_Block.SLDPRT", include_brep=False)
    SketchA = Document.sketch("sldprt:sketch:200")
    Unknown = next(
        (
            Entity
            for Entity in SketchA.entities
            if Entity.provenance and Entity.provenance.spans[0].offset == 196708
        )
    )
    assert isinstance(Unknown.geometry, NativeGeometry)
    assert Unknown.geometry.data["locus"] == "03000300"
    assert Unknown.geometry.data["record_data"]
    Entity = next(
        (
            Entity
            for Entity in SketchA.entities
            if Entity.provenance and Entity.provenance.spans[0].offset == 198158
        )
    )
    assert isinstance(Entity.geometry, LineGeometry)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestEFWTSHAND() -> None:
    Document = ReadSldprt(KSample, include_brep=False)
    assert all(
        (Feature.definition is not None for Feature in Document.feature_timeline)
    )
    NativeA = [
        Feature.definition
        for Feature in Document.feature_timeline
        if isinstance(Feature.definition, NativeFeatureDefinition)
    ]
    assert NativeA
    assert all((Definition.type_id for Definition in NativeA))
    assert any((Definition.object_data["record_data"] for Definition in NativeA))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestUNCIRWMR() -> None:
    SketchA = NativeSketch(
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
    ConstraintsA = SketchConstraints(SketchA, {}, set())
    assert len(ConstraintsA) == 1
    assert ConstraintsA[0].references == ()
    assert ConstraintsA[0].attributes["native_references"] == ("future-reference",)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAAMARNJ() -> None:
    SourceDoc = KSample.read_bytes()
    Adapter = SldprtAdapter()
    assert Adapter.probe(SourceDoc).confidence == 1.0
    Document = ReadSldprt(SourceDoc, include_brep=False)
    Restored = type(Document).from_json(Document.to_json())
    assert Restored.validate() == ()
    assert Restored.source.path == "<memory>"
    assert Restored.feature("sldprt:feature:116").name == "Fillet1"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestELSCD() -> None:
    Examples = FilePath(__file__).resolve().parents[4] / "examples"
    Parts = sorted(
        (
            TargetPath
            for TargetPath in Examples.rglob("*")
            if TargetPath.is_file()
            and TargetPath.suffix.lower() == ".sldprt"
            and (not TargetPath.name.startswith("~$"))
        )
    )
    Documents = [ReadSldprt(TargetPath) for TargetPath in Parts]
    assert len(Parts) == 111
    assert all((Document.validate() == () for Document in Documents))
    assert sum((len(Document.brep_payloads) for Document in Documents)) == 909
    assert all(
        (
            Payload.role == PayloadRole.BREP
            for Document in Documents
            for Payload in Document.brep_payloads
        )
    )
    assert any(
        (
            not Payload.source_stream.endswith("Partition")
            for Document in Documents
            for Payload in Document.brep_payloads
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAHPZPFV() -> None:
    Document = ReadSldprt(KCorpus / "Addons" / "Alternator.SLDPRT", include_brep=False)
    Plane = Document.plane("sldprt:plane:289")
    assert Plane.transform.origin.z == PytestLib.approx(50.0)
    assert Plane.transform.z_axis.z == 1.0
    assert Document.sketch("sldprt:sketch:292").support_plane_id == Plane.id
    assert Document.validate() == ()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestAAOITDD() -> None:
    Document = ReadSldprt(
        KCorpus / "Cylinder_heads" / "Spark_plug.SLDPRT", include_brep=False
    )
    assert Document.parameter("sldprt:parameter:107:D5").value.value == 2.0
    assert Document.parameter("sldprt:parameter:107:D5:2").value.value == 2.0
    assert Document.validate() == ()
