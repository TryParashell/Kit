# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from collections import Counter
from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath
import struct as StructLib
import pytest as PytestLib
from convert.adapters.base import ReadOptions
from convert.adapters.solidworks import (
    SldprtAdapter,
    SldprtArchive,
    build_sldprt as BuildSldprt,
)
from convert.adapters.solidworks.core.Adapter import (
    _companion_payloads as CompanionPayloads,
    _mate_groups as MateGroups,
    _mate_instance_path as MateInstancePath,
    _mate_payload as MatePayload,
    _neutral_mate_alignment as NeutralMateAlignment,
    _neutral_mate_entity_kind as NeutralMateEntityKind,
    _neutral_mate_kind as NeutralMateKind,
    _neutral_mate_value as NeutralMateValue,
)
from convert.adapters.solidworks.assembly.Assembly import (
    MATE_VALUE_SEMANTICS as Semantics,
    NATIVE_MATE_ALIGNMENTS as Alignments,
    NATIVE_MATE_ALIGNMENT_BY_CODE as CodeInfo,
    NATIVE_MATE_ENTITY_GEOMETRY_TYPES as Types,
    NATIVE_MATE_ENTITY_KIND_BY_MARKER as Marker,
    NATIVE_MATE_ENTITY_MARKERS as Markers,
    NATIVE_MATE_ENTITY_REFERENCE_TYPES as TypesA,
    NATIVE_MATE_ENTITY_TYPE_RECORDS as Records,
    NATIVE_MATE_NEUTRAL_KIND_ALIASES as Aliases,
    NATIVE_MATE_TYPE_RECORDS as RecordsA,
    NATIVE_MATE_TYPES as TypesB,
    NativeMate,
    NativeMateAlignmentCode,
    NativeMateDimension,
    _MATE_KIND_BY_CLASS as Class,
    _MATE_KIND_BY_NAME as NameInfo,
    _mate_alignment as MateAlignmentA,
    _mate_entities as MateEntities,
    _mate_kind as MateKindA,
    _native_feature_id as NativeFeatureId,
    decode_mate_list as DecodeMateList,
    decode_native_assembly as DecodeNativeAssembly,
)
from convert.adapters.solidworks.assembly.AssemblyCore import AsmCoreItem, EncodeAsmCore
from interchange import (
    Capability,
    ComponentInstance,
    ComponentKind,
    MateAlignment,
    MateEntityKind,
    MateKind,
    ValueKind,
)

# centralizes shared evidence so every related assertion uses one value
KRandom = FilePath(__file__).resolve().parents[4] / "examples" / "Random"

# centralizes shared evidence so every related assertion uses one value
KAssembly = KRandom / "V8_engine.SLDASM"

# centralizes shared evidence so every related assertion uses one value
KConrod = KRandom / "Pistons" / "Conrod.SLDASM"


# keeps this focused behavior isolated so regressions remain immediately visible
def MixedCoreItems() -> tuple[AsmCoreItem, ...]:
    QuarterTurn = (0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    HalfTurn = (-1.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0, 1.0)
    return (
        AsmCoreItem(
            "unit_1-1",
            "C:\\generated\\unit_1.SLDPRT",
            0.01,
            0.02,
            0.03,
            FileStamp=123456,
            BasisVals=QuarterTurn,
        ),
        AsmCoreItem(
            "unit_1-2",
            "C:\\generated\\unit_1.SLDPRT",
            0.04,
            0.05,
            0.06,
            FileStamp=123456,
        ),
        AsmCoreItem(
            "unit_2-1",
            "C:\\generated\\unit_2.SLDPRT",
            0.07,
            0.08,
            0.09,
            FileStamp=123456,
            BasisVals=HalfTurn,
        ),
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMCWTRBAET() -> None:
    RotatedItems = MixedCoreItems()
    IdentityVals = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
    IdentityItems = tuple(
        (ReplaceData(ItemValue, BasisVals=IdentityVals) for ItemValue in RotatedItems)
    )
    RotatedData = EncodeAsmCore("RotatedMixed", "Default", RotatedItems)[
        "Contents/Config-0"
    ]
    IdentityData = EncodeAsmCore("RotatedMixed", "Default", IdentityItems)[
        "Contents/Config-0"
    ]
    assert len(RotatedData) - len(IdentityData) == 144
    assert (
        StructLib.unpack_from("<i", RotatedData, 18)[0]
        == StructLib.unpack_from("<i", IdentityData, 18)[0] + 144
    )
    for ItemValue in RotatedItems:
        HasBasis = ItemValue.BasisVals != IdentityVals
        ExpectedData = bytearray((int(HasBasis),))
        if HasBasis:
            ExpectedData.extend(StructLib.pack("<9d", *ItemValue.BasisVals))
        ExpectedData.extend(
            StructLib.pack(
                "<4dB", ItemValue.TransX, ItemValue.TransY, ItemValue.TransZ, 1.0, 0
            )
        )
        assert bytes(ExpectedData) in RotatedData


# keeps this focused behavior isolated so regressions remain immediately visible
def StaticCoreSets() -> tuple[tuple[AsmCoreItem, ...], ...]:
    PathSets = (
        ("unit_a.SLDPRT",),
        ("unit_a.SLDPRT", "unit_a.SLDPRT"),
        ("unit_a.SLDPRT", "unit_b.SLDPRT"),
        ("unit_a.SLDPRT", "unit_a.SLDPRT", "unit_a.SLDPRT"),
    )
    return tuple(
        (
            tuple(
                (
                    AsmCoreItem(
                        f"unit_{ItemIndex + 1}-1",
                        f"C:\\generated\\{PathName}",
                        0.111 + ItemIndex,
                        0.222 + ItemIndex,
                        0.333 + ItemIndex,
                    )
                    for ItemIndex, PathName in enumerate(PathNames)
                )
            )
            for PathNames in PathSets
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("CoreItems", StaticCoreSets())
def TestSCWET(CoreItems: tuple[AsmCoreItem, ...]) -> None:
    ConfigData = EncodeAsmCore("StaticCore", "Default", CoreItems)["Contents/Config-0"]
    for ItemValue in CoreItems:
        for TransValue in (ItemValue.TransX, ItemValue.TransY, ItemValue.TransZ):
            assert StructLib.pack("<d", TransValue) in ConfigData


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize("CoreItems", StaticCoreSets())
def TestSCRNB(CoreItems: tuple[AsmCoreItem, ...]) -> None:
    QuarterTurn = (0.0, 1.0, 0.0, -1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
    RotatedItems = (ReplaceData(CoreItems[0], BasisVals=QuarterTurn), *CoreItems[1:])
    with PytestLib.raises(ValueError, match="requires identity component bases"):
        EncodeAsmCore("StaticCore", "Default", RotatedItems)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestNFIDNIFS() -> None:
    FixedItem = ComponentInstance("item", "Unit-1", "unit", "root", fixed=True)
    FloatItem = ReplaceData(FixedItem, fixed=False)
    assert NativeFeatureId(FixedItem, 0) == 24
    assert NativeFeatureId(FloatItem, 0) == 24
    assert NativeFeatureId(FloatItem, 1) == 25


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.fixture(scope="module")
def Document():
    return SldprtAdapter().read(KAssembly, ReadOptions(include_brep=False))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARHDAH(Document) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    assert Document.validate() == ()
    assert len(Assembly.definitions) == 68
    assert Counter((Definition.kind for Definition in Assembly.definitions)) == {
        ComponentKind.PART: 65,
        ComponentKind.ASSEMBLY: 3,
    }
    assert len(Assembly.instances) == 288
    assert Assembly.attributes["flattened_occurrence_count"] == 358
    assert len(Assembly.documents) == 53
    assert Assembly.attributes["linked_part_document_count"] == 51
    assert Assembly.attributes["linked_assembly_document_count"] == 2
    assert Assembly.attributes["linked_sketch_count"] == 391
    assert Assembly.attributes["linked_feature_count"] == 2147
    assert len(Document.sketches) == 3
    assert len(Document.feature_timeline) == 327
    assert (
        sum(
            (
                Feature.attributes["xml_tag"] == "Reference"
                for Feature in Document.feature_timeline
            )
        )
        == 278
    )
    assert len(Document.support_planes) == 6


# keeps this focused behavior isolated so regressions remain immediately visible
def TestACRTDD(Document) -> None:
    assert Document.capabilities == frozenset(
        {
            Capability.ASSEMBLIES,
            Capability.ASSEMBLY_MATES,
            Capability.BODY_STRUCTURE,
            Capability.COMPONENT_DOCUMENTS,
            Capability.CONFIGURATIONS,
            Capability.EDITABLE_SKETCHES,
            Capability.EXPRESSIONS,
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


# keeps this focused behavior isolated so regressions remain immediately visible
def TestOMTHECM() -> None:
    Expected = {
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
    assert {NameText.casefold() for NameText in Expected} <= Class.keys()
    assert {
        NameText: NeutralMateKind(MateKindA("Renamed mate", NameText))
        for NameText in Expected
    } == Expected


# keeps this focused behavior isolated so regressions remain immediately visible
def TestOMTRIEAD() -> None:
    assert tuple(((RecordInfo.code, RecordInfo.api_name) for RecordInfo in TypesB)) == (
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
    assert Class == {
        ClassName.casefold(): RecordInfo.kind
        for RecordInfo in RecordsA
        for ClassName in RecordInfo.class_names
    }
    assert NameInfo == {
        Prefix.casefold(): RecordInfo.kind
        for RecordInfo in RecordsA
        for Prefix in RecordInfo.name_prefixes
    }
    assert len(Class) == 64
    assert len(NameInfo) == 40
    assert Aliases == {"cam_tangent": "cam", "lock_to_sketch": "lock"}
    assert Class["matereferencegroupfolder"] == "group"
    assert MateKindA("Renamed", "MateReferenceGroupFolder") == "group"
    assert Semantics == {
        "distance": "length",
        "angle": "angle",
        "gear": "ratio",
        "rack_pinion": "length",
        "screw": "length",
        "linear_coupler": "ratio",
        "belt": "ratio",
    }


# keeps this focused behavior isolated so regressions remain immediately visible
def TestOMERRIE() -> None:
    assert tuple(((RecordInfo.code, RecordInfo.api_name) for RecordInfo in Types)) == (
        (0, "swMateUnsupported"),
        (1, "swMatePoint"),
        (2, "swMateLine"),
        (3, "swMatePlane"),
        (4, "swMateCylinder"),
        (5, "swMateCone"),
        (6, "swMateSphere"),
        (7, "swMateCircle"),
    )
    assert tuple(((RecordInfo.code, RecordInfo.api_name) for RecordInfo in TypesA)) == (
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
    assert {RecordInfo.kind for RecordInfo in Records} == {
        KindInfo.value for KindInfo in MateEntityKind
    }
    assert len(Marker) == 26
    assert Markers == tuple(
        (
            (MarkerA.casefold(), RecordInfo.kind)
            for RecordInfo in Records
            for MarkerA in RecordInfo.markers
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    ("PersistentReference", "Expected"),
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
def TestMERCUTCR(PersistentReference: str, Expected: MateEntityKind) -> None:
    assert NeutralMateEntityKind(PersistentReference) == Expected


# keeps this focused behavior isolated so regressions remain immediately visible
def TestOMARPEC() -> None:
    assert tuple(
        (
            (RecordInfo.code.value, RecordInfo.api_name, RecordInfo.kind)
            for RecordInfo in Alignments
        )
    ) == (
        (0, "swMateReferenceAlignment_Any", "unknown"),
        (1, "swMateReferenceAlignment_Aligned", "aligned"),
        (2, "swMateReferenceAlignment_AntiAligned", "anti_aligned"),
        (3, "swMateReferenceAlignment_Closest", "closest"),
    )
    assert CodeInfo == {RecordInfo.code.value: RecordInfo for RecordInfo in Alignments}
    for CodeInfoA in NativeMateAlignmentCode:
        DataValue = bytearray(168)
        StructLib.pack_into("<H", DataValue, 159, CodeInfoA.value)
        StructLib.pack_into("<I", DataValue, 164, 2)
        assert MateAlignmentA(bytes(DataValue), len(DataValue), 0) == CodeInfoA.value
    Invalid = bytearray(168)
    StructLib.pack_into("<H", Invalid, 159, 42)
    StructLib.pack_into("<I", Invalid, 164, 2)
    assert MateAlignmentA(bytes(Invalid), len(Invalid), 0) is None
    Expected = (
        MateAlignment.UNKNOWN,
        MateAlignment.ALIGNED,
        MateAlignment.ANTI_ALIGNED,
        MateAlignment.CLOSEST,
    )
    assert (
        tuple(
            (
                NeutralMateAlignment(NativeMateA(AlignmentCode=CodeInfoA.value))
                for CodeInfoA in NativeMateAlignmentCode
            )
        )
        == Expected
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestLCRUTMPR() -> None:
    ItemValueB = NeutralMateValue(
        NativeMateA(
            KindInfo="linear_coupler",
            Dimensions=(
                NativeMateDimension("D1", 2.0, 10),
                NativeMateDimension("D2", 4.0, 20),
            ),
        )
    )
    assert ItemValueB is not None
    assert ItemValueB.value == PytestLib.approx(0.5)
    assert ItemValueB.kind == ValueKind.NUMBER


# keeps this focused behavior isolated so regressions remain immediately visible
def NativeMateA(
    *,
    KindInfo: str = "native",
    AlignmentCode: int | None = None,
    Dimensions: tuple[NativeMateDimension, ...] = (),
) -> NativeMate:
    return NativeMate(
        name="Fixture",
        kind=KindInfo,
        owner_definition_id=0,
        order=0,
        entities=(),
        record_offset=0,
        record_length=0,
        class_name="",
        class_token=None,
        serialized_strings=(),
        alignment_code=AlignmentCode,
        dimensions=Dimensions,
    )


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    ("NameText", "NeutralKind"),
    (
        ("Coordinate17", MateKind.COORDINATE),
        ("Slider8", MateKind.SLIDER),
        ("Magnetic4", MateKind.MAGNETIC),
        ("Path2", MateKind.PATH),
    ),
)
def TestOMNFAS(NameText: str, NeutralKind: MateKind) -> None:
    assert NeutralMateKind(MateKindA(NameText)) == NeutralKind


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMNFDNMCN() -> None:
    assert MateKindA("DistanceVendor") == "native"
    assert MateKindA("CoincidentCustomer1") == "native"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARETAS(Document) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    RingInfo = next(
        (
            Instance
            for Instance in Assembly.instances
            if Instance.id == "sldasm:instance:223"
        )
    )
    assert RingInfo.transform.values == (
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
    Piston = next(
        (
            Instance
            for Instance in Assembly.instances
            if Instance.id == "sldasm:instance:217"
        )
    )
    assert Piston.transform.values[3] == PytestLib.approx(-1.209188127289168e-15)
    assert Piston.transform.values[7] == PytestLib.approx(79.99530923564971)
    assert Piston.transform.values[11] == PytestLib.approx(-79.99530923564954)
    FeatureItem = next(
        (
            Instance
            for Instance in Assembly.instances
            if Instance.id == "sldasm:instance:211"
        )
    )
    assert FeatureItem.attributes["native_feature_id"] == 24
    assert not FeatureItem.fixed
    assert all((not Instance.suppressed for Instance in Assembly.instances))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARRANML(Document) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    assert len(Assembly.mates) == 632
    assert len(Assembly.mate_entities) == 1261
    assert Counter((MateInfo.kind for MateInfo in Assembly.mates)) == {
        MateKind.CONCENTRIC: 301,
        MateKind.COINCIDENT: 280,
        MateKind.CAM: 32,
        MateKind.BELT: 14,
        MateKind.LOCK: 3,
        MateKind.GEAR: 1,
        MateKind.DISTANCE: 1,
    }
    assert len(Assembly.mate_groups) == 3
    assert [len(Group.mate_ids) for Group in Assembly.mate_groups] == [6, 2, 9]
    assert Assembly.attributes["flattened_mate_occurrence_count"] == 765
    Payloads = [
        Payload
        for Payload in Document.brep_payloads
        if Payload.format_id == "solidworks.mates"
    ]
    assert [len(Payload.data or b"") for Payload in Payloads] == [2202551, 18893, 43184]
    assert sum((Payload.attributes["declared_count"] for Payload in Payloads)) == 638
    assert all(
        (MateInfo.attributes["native_payload_id"] for MateInfo in Assembly.mates)
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARDMVAA(Document) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    Distance = next(
        (MateInfo for MateInfo in Assembly.mates if MateInfo.kind == MateKind.DISTANCE)
    )
    assert Distance.name == "Distance1"
    assert Distance.value is not None
    assert Distance.value.value == PytestLib.approx(20.0)
    assert Distance.value.kind == ValueKind.LENGTH
    assert Distance.value.unit == "mm"
    assert Distance.alignment == MateAlignment.ANTI_ALIGNED
    assert not Distance.suppressed
    assert Distance.attributes["native_alignment_code"] == 2
    assert Distance.attributes["native_value_m"] == PytestLib.approx(0.02)
    assert Distance.attributes["native_value_offset"] == 1640514
    GearInfo = next(
        (MateInfo for MateInfo in Assembly.mates if MateInfo.kind == MateKind.GEAR)
    )
    assert GearInfo.value is not None
    assert GearInfo.value.value == PytestLib.approx(1.0)
    assert GearInfo.value.kind == ValueKind.NUMBER
    assert [
        ItemValueA["name"] for ItemValueA in GearInfo.attributes["native_dimensions"]
    ] == ["D1", "D2"]
    assert GearInfo.alignment == MateAlignment.UNKNOWN
    Belts = [MateInfo for MateInfo in Assembly.mates if MateInfo.kind == MateKind.BELT]
    assert all((MateInfo.value is not None for MateInfo in Belts))
    assert all((MateInfo.alignment == MateAlignment.UNKNOWN for MateInfo in Belts))
    assert all(
        (
            MateInfo.value.value
            == PytestLib.approx(
                MateInfo.attributes["native_dimensions"][0]["value"]
                / MateInfo.attributes["native_dimensions"][1]["value"]
            )
            for MateInfo in Belts
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMTUNCWLFR() -> None:
    Archive = SldprtArchive.open(KConrod)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    OldName = "Concentric1".encode("utf-16le")
    NewName = "CustomMate1".encode("utf-16le")
    NameOffset = RecordInfo.data.index(OldName)
    Renamed = (
        RecordInfo.data[:NameOffset]
        + NewName
        + RecordInfo.data[NameOffset + len(OldName) :]
    )
    RenamedList = DecodeMateList(Renamed, RecordInfo.name, 7)
    assert RenamedList.mates[0].name == "CustomMate1"
    assert RenamedList.mates[0].kind == "concentric"
    assert RenamedList.mates[0].class_name == "moMateConcentric"
    OldClass = b"moMateConcentric"
    NewClass = b"moMateVendorType"
    OriginalClassOffset = RecordInfo.data.index(OldClass)
    UnknownClass = (
        RecordInfo.data[:OriginalClassOffset]
        + NewClass
        + RecordInfo.data[OriginalClassOffset + len(OldClass) :]
    )
    UnknownClassList = DecodeMateList(UnknownClass, RecordInfo.name, 7)
    assert UnknownClassList.mates[0].name == "Concentric1"
    assert UnknownClassList.mates[0].kind == "native"
    ClassOffset = Renamed.index(OldClass)
    Future = Renamed[:ClassOffset] + NewClass + Renamed[ClassOffset + len(OldClass) :]
    FutureList = DecodeMateList(Future, RecordInfo.name, 7)
    MateInfo = FutureList.mates[0]
    assert MateInfo.name == "CustomMate1"
    assert MateInfo.kind == "native"
    assert MateInfo.class_name == "moMateVendorType"
    assert MateInfo.serialized_strings[0] == "CustomMate1"
    assert NeutralMateKind(MateInfo.kind) == MateKind.NATIVE
    Payload = MatePayload("future", RecordInfo.name, Future, FutureList, 7, "fixture")
    assert Payload.data == Future
    assert Payload.attributes["records"][0] == {
        "name": "CustomMate1",
        "kind": "native",
        "class_name": "moMateVendorType",
        "class_token": None,
        "offset": MateInfo.record_offset,
        "length": MateInfo.record_length,
    }


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRMCTSARI() -> None:
    Archive = SldprtArchive.open(KConrod)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    OldName = "Coincident2".encode("utf-16le")
    NewName = "CustomMate2".encode("utf-16le")
    Offset = RecordInfo.data.index(OldName)
    Renamed = (
        RecordInfo.data[:Offset] + NewName + RecordInfo.data[Offset + len(OldName) :]
    )
    MateList = DecodeMateList(Renamed, RecordInfo.name, 7)
    MateInfo = MateList.mates[2]
    assert MateInfo.name == "CustomMate2"
    assert MateInfo.kind == "coincident"
    assert MateInfo.class_name == "moMateCoincident"
    assert MateInfo.class_token is not None


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMGBAS() -> None:
    Archive = SldprtArchive.open(KAssembly)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    MateList = DecodeMateList(RecordInfo.data, RecordInfo.name, 7)
    MarkersA = [MateInfo for MateInfo in MateList.mates if MateInfo.kind == "group"]
    Renamed = ReplaceData(
        MateList,
        mates=tuple(
            (
                (
                    ReplaceData(MateInfo, name="Groupe sans suffixe")
                    if MateInfo.order == MarkersA[0].order
                    else (
                        ReplaceData(MateInfo, name="Terminaison locale")
                        if MateInfo.order == MarkersA[1].order
                        else MateInfo
                    )
                )
                for MateInfo in MateList.mates
            )
        ),
    )
    MateIds = {
        MateInfo.order: f"mate:{MateInfo.order}"
        for MateInfo in Renamed.mates
        if MateInfo.kind != "group"
    }
    Groups = MateGroups(Renamed, 7, MateIds, RecordInfo.name, "payload")
    assert Groups[0].name == "Groupe sans suffixe"
    assert Groups[0].mate_ids


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCCPRWNS() -> None:
    Archive = SldprtArchive.open(KConrod)
    Native = DecodeNativeAssembly(Archive)
    Occurrence = next(
        (
            ItemValueA
            for ItemValueA in Native.occurrences
            if ItemValueA.owner_definition_id == Native.root_definition_id
        )
    )
    Owner = next(
        (
            ItemValueA
            for ItemValueA in Native.definitions
            if ItemValueA.object_id == Native.root_definition_id
        )
    )
    Identity = {
        ItemValueA.object_id: ItemValueA.object_id for ItemValueA in Native.occurrences
    }
    assert MateInstancePath(Native, Identity, f"{Occurrence.name}@{Owner.name}") == (
        Occurrence.object_id,
    )
    Entities = MateEntities(
        (
            "moFaceRef_c,1,2,3",
            f"{Occurrence.name}@{Owner.name}",
            Occurrence.name + ".SLDPRT",
        )
    )
    assert Entities[0].component_path == f"{Occurrence.name}@{Owner.name}"
    assert Entities[0].source_path == Occurrence.name + ".SLDPRT"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMLDUSWTSIR() -> None:
    BlobInfo = KConrod.read_bytes()
    Archive = SldprtArchive.from_bytes(BlobInfo, KConrod)
    RecordInfo = next(
        (
            ItemValueA
            for ItemValueA in Archive.records
            if ItemValueA.name.endswith("-MatesList")
        )
    )
    Streams = Archive.streams
    Streams["Relations/AssemblyConstraints"] = Streams.pop(RecordInfo.name)
    Renamed = SldprtArchive.from_bytes(
        BuildSldprt(
            Streams,
            file_id=Archive.file_id,
            format_version=Archive.format_version,
            template=BlobInfo,
        )
    )
    Native = DecodeNativeAssembly(Renamed)
    assert len(Native.mate_lists) == 1
    assert Native.mate_lists[0].stream == "Relations/AssemblyConstraints"
    assert len(Native.mate_lists[0].mates) == 13


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMARERM(Document) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    assert len(Document.meshes) == 65
    assert (
        sum((len(MeshInfo.attributes["faces"]) for MeshInfo in Document.meshes)) == 4391
    )
    assert sum((len(MeshInfo.vertices) for MeshInfo in Document.meshes)) == 492148
    assert sum((len(MeshInfo.triangles) for MeshInfo in Document.meshes)) == 391218
    PartDefinitions = {
        Definition.id
        for Definition in Assembly.definitions
        if Definition.kind == ComponentKind.PART
    }
    MeshedDefinitions = {
        Definition.id for Definition in Assembly.definitions if Definition.mesh_ids
    }
    assert MeshedDefinitions == PartDefinitions


# keeps this focused behavior isolated so regressions remain immediately visible
def TestNADPTOT(Document) -> None:
    Assembly = Document.assembly
    assert Assembly is not None
    Nested = [
        Linked.document
        for Linked in Assembly.documents
        if Linked.document.source.format_id == "solidworks.sldasm"
    ]
    assert sorted((len(ItemValueA.feature_timeline) for ItemValueA in Nested)) == [
        27,
        29,
    ]
    assert sorted((len(ItemValueA.assembly.mates) for ItemValueA in Nested)) == [6, 13]
    assert all((not ItemValueA.assembly.documents for ItemValueA in Nested))


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRACARE() -> None:
    Payloads = CompanionPayloads(str(KAssembly))
    assert [
        (Payload.format_id, len(Payload.data or b""), Payload.sha256)
        for Payload in Payloads
    ] == [
        (
            "acis.sat",
            61518735,
            "accecfe74a515d095c38b12b669546e54cc5d55308d6e1c8e0913dd6649e7017",
        ),
        (
            "parasolid.x_t",
            8036848,
            "00dc62be5c5adb9b9ff4c83ae3f674f5e1df07782c65f86b50987c8dde76dde3",
        ),
    ]
    assert Payloads[0].attributes["body_count"] == 391
