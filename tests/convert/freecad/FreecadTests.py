# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
import base64 as BaseSixFour
from collections.abc import Callable as FuncCall, Mapping, Sequence
from dataclasses import replace as Replace
import hashlib as Hashlib
import inspect as Inspect
import io as IoStream
import json as JsonValue
import math as MathValue
from pathlib import Path as FilePath
import struct as Struct
from types import MappingProxyType as MapProxy
from typing import TypeGuard, TypedDict as TypeDict
import xml.etree.ElementTree as XmlTree
import zipfile as Zipfile
import zlib as ZlibValue
import pytest as Pytest
from convert import (
    ApplicationUsabilityError as AppUsabilityError,
    convert as Convert,
    open_document as OpenDoc,
    registry as Registry,
    write_document as WriteDoc,
)
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.TransferContract import CarrierReason, TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.freecad import (
    FreeCADAdapter as FreeCadAdapter,
    FreeCADAdapterError as FreeCadAdapterError,
    build_fcstd_archive as BuildFcstdArchive,
    document_to_manifest as DocToManifest,
)
from convert.adapters.freecad.Brep import brep_model_brep as BrepModelBrep
from convert.adapters.freecad import Adapter as FreecadAdapterModule
from convert.adapters.freecad import Archive as FreecadArchiveModule
from convert.adapters.freecad import Native as FreecadNativeModule
from convert.adapters.freecad.Adapter import (
    AnnotateNative,
    FilteredDoc,
    UnchangedNative,
)
from convert.adapters.freecad.Format import (
    CAPABILITY_CARRIER_REASONS as CapabilityCarrierReasons,
    CAPABILITY_WRITE_TYPE_IDS as CapabilityWriteTypeIds,
    FORMAT_ID as FormatId,
    INFO as InfoValue,
    NATIVE_CAPABILITIES as NativeCapabilities,
    SUFFIX as Suffix,
)
from convert.adapters.freecad.Protocol import (
    ADDITIONAL_PART_OBJECT_TYPE_IDS as AdditionalPartObjectType,
    ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES as AsmConnectorPropPrefixes,
    ASSEMBLY_JOINT_GROUP_TYPE_ID as AsmJointGroupTypeId,
    ASSEMBLY_LINK_TYPE_ID as AsmLinkTypeId,
    ASSEMBLY_OBJECT_TYPE_PREFIX as AsmObjectTypePrefix,
    ASSEMBLY_ROOT_TYPE_ID as AsmRootTypeId,
    APP_PART_TYPE_ID as AppPartTypeId,
    APP_LINK_TYPE_ID as AppLinkTypeId,
    BODY_CONTAINER_TYPE_IDS as BodyContainerTypeIds,
    BODY_TYPE_ID as BodyTypeId,
    BOOLEAN_OPERATION_TYPE_BY_KIND as BoolOperationTypeByKind,
    BOOLEAN_OPERATION_TYPES as BoolOperationTypes,
    CIRCULAR_GEOMETRY_KINDS as CircularGeomKinds,
    CONSTRAINT_CODE_BY_KIND as RuleCodeByKind,
    CONSTRAINT_CARRIER_KINDS as RuleCarrierKinds,
    CONSTRAINT_COMPOSED_KINDS as RuleComposedKinds,
    CONSTRAINT_DIRECT_KINDS as RuleDirectKinds,
    CONSTRAINT_KIND_BY_CODE as RuleKindByCode,
    CONSTRAINT_POINT_BY_INDEX as RulePointByIndex,
    CONSTRAINT_POINT_INDEX_BY_NAME as RulePointIndexByName,
    CONSTRAINT_POINTS as RulePoints,
    CONSTRAINT_TYPES as RuleTypes,
    CONSTRAINT_VALUE_KIND_BY_CODE as RuleValueKindByCode,
    CONSTRAINT_WRITE_CODES as RuleWriteCodes,
    CONSTRAINT_WRITE_KINDS as RuleWriteKinds,
    CREATE_OPERATION_NAMES as CreateOperationNames,
    DIMENSIONAL_CONSTRAINT_CODES as DimensionalRuleCodes,
    EXTRUSION_TYPE_BY_CODE as ExtrusionTypeByCode,
    EXTRUSION_TYPES as ExtrusionTypes,
    FEATURE_KIND_BY_TYPE_ID as FeatureKindByTypeId,
    FEATURE_CARRIER_KINDS as FeatureCarrierKinds,
    FEATURE_TYPES as FeatureTypes,
    FEATURE_WRITE_KINDS as FeatureWriteKinds,
    FEATURE_WRITE_TYPE_IDS as FeatureWriteTypeIds,
    FIXED_CONSTRAINT_KINDS as FixedRuleKinds,
    GEOMETRY_KIND_BY_TYPE_ID as GeomKindByTypeId,
    GEOMETRY_CARRIER_KINDS as GeomCarrierKinds,
    GEOMETRY_TYPES as GeomTypes,
    GEOMETRY_TYPE_IDS_BY_KIND as GeomTypeIdsByKind,
    GEOMETRY_WRITE_KINDS as GeomWriteKinds,
    GEOMETRY_WRITE_TYPE_IDS as GeomWriteTypeIds,
    JOINT_GROUND_PROPERTY as JointGroundProp,
    JOINT_REFERENCE_INDEX_BY_PROPERTY as JointRefIndexByProp,
    JOINT_REFERENCE_PROPERTIES as JointRefProperties,
    JOINT_RESERVED_LINK_PROPERTIES as JointReservedLink,
    JOINT_TYPE_BY_MATE_KIND as JointTypeByMateKind,
    JOINT_TYPE_DEFINITIONS as JointTypeDefinitions,
    JOINT_TYPE_PROPERTIES as JointTypeProperties,
    JOINT_TYPES as JointTypes,
    JOINT_TYPES_USING_DISTANCE as JointTypesUsingDistance,
    JOINT_TYPES_USING_SECOND_DISTANCE as JointTypesUsingSecond,
    MATE_KIND_BY_JOINT_TYPE as MateKindByJointType,
    MATE_CARRIER_KINDS as MateCarrierKinds,
    MATE_KINDS_USING_DISTANCE as MateKindsUsingDistance,
    MATE_KINDS_USING_SECOND_DISTANCE as MateKindsUsingSecond,
    MATE_WRITE_KINDS as MateWriteKinds,
    MATE_WRITE_TYPES as MateWriteTypes,
    MIDPOINT_REFERENCE_POINT_NAMES as MidpointRefPointNames,
    NEUTRAL_GEOMETRY_TYPE_BY_KIND as NeutralGeomTypeByKind,
    NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND as NeutralGeomTypeIdByKind,
    NON_FEATURE_OBJECT_TYPE_IDS as NonFeatureObjectTypeIds,
    PART_CONTAINER_TYPE_IDS as PartContainerTypeIds,
    PART_OBJECT_TYPE_IDS as PartObjectTypeIds,
    PERMISSIVE_TRUE_VALUES as PermissiveTrueValues,
    POCKET_TYPE_ID as PocketTypeId,
    PRIMITIVE_FEATURE_FAMILIES as PrimitiveFeatureFamilies,
    PRIMITIVE_FEATURE_TYPE_IDS as PrimitiveFeatureTypeIds,
    QUANTITY_PROPERTY_UNITS as QuantityPropUnits,
    REGISTERED_PART_OBJECT_TYPE_IDS as RegisteredPartObjectType,
    SCALAR_PROPERTY_KINDS as ScalarPropKinds,
    SCALAR_PROPERTY_TYPES as ScalarPropTypes,
    SKETCH_TYPE_ID as SketchTypeId,
    SPLINE_GEOMETRY_KINDS as SplineGeomKinds,
    SPLINE_GEOMETRY_TYPE_IDS as SplineGeomTypeIds,
    SPLINE_CONTROL_TAGS as SplineControlTags,
    STRING_HASHER_TAGS as StringHasherTags,
    SUBELEMENT_KIND_BY_PREFIX as SubElemKindByPrefix,
    SUBELEMENT_MATE_ENTITY_KINDS as SubElemMateEntityKinds,
    SUPPORT_PLANE_TYPE_IDS as SupportPlaneTypeIds,
    XML_TRUE_VALUES as XmlTrueValues,
)
from convert.adapters.freecad.Native import (
    ClosedProfile,
    NativeObject,
    ParseSketchMut,
    PlaneReframe,
    ReframeGeom,
)
from convert.geometry.Opencascade import (
    is_structurally_valid_ascii_brep as IsStructurallyValidAscii,
)
from interchange import (
    ArcEllipseGeometry as ArcEllipseGeom,
    ArcHyperbolaGeometry as ArcHyperbolaGeom,
    ArcParabolaGeometry as ArcParabolaGeom,
    BrepPayload,
    CadDocument,
    ChamferFeature,
    CircleGeometry as CircleGeom,
    CircularPatternFeature,
    Configuration as Config,
    ConstraintReference as RuleRef,
    Expression,
    FeatureStep,
    EllipseGeometry as EllipseGeom,
    HyperbolaGeometry as HyperbolaGeom,
    LineGeometry as LineGeom,
    LinearPatternFeature,
    Mesh as MeshRecord,
    NativeFeatureDefinition,
    NativeGeometry as NativeGeom,
    Parameter as Param,
    ParameterValue as ParamValue,
    ParabolaGeometry as ParabolaGeom,
    PayloadRole,
    PointGeometry as PointGeom,
    Selection as SelectionInfo,
    SelectionPathElement as SelectionPathElem,
    ShellFeature,
    SketchConstraint as SketchRule,
    SketchEntity,
    Transform,
    Vector2 as VectorTwo,
    Vector3 as VectorThree,
)
from interchange.assembly.AssemblyEnums import MateKind
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumFeatures import BooleanOp as BoolOperation, FeatureKind
from interchange.enums.EnumGeometry import ConstraintKind as RuleKind
from interchange.enums.EnumGeometry import GeometryKind as GeomKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureExtrude import ExtrudeEnd as ExtrusionEndCondition
from interchange.features.FeatureExtrude import ExtrudeFeature as ExtrusionFeature
from tests.interchange.document.DocumentTests import document as NeutralDoc
from tests.interchange.brep.BrepTests import triangle_brep as TriangleBrep

# this binding keeps xml element annotations aligned with the imported parser
ET = XmlTree

# this binding keeps fixture paths aligned with the imported pathlib contract
Path = FilePath

# native fixture options need a closed schema so xml payloads remain statically typed
NativeOptions = TypeDict(
    "NativeOptions",
    {
        "id": str | int,
        "touched": bool,
        "extensions": tuple[str, ...],
        "transient_properties": tuple[ET.Element, ...],
    },
    total=False,
)


# runtime mapping checks need an object contract before recursive metadata iteration
def IsMetaMap(SourceValue: object) -> TypeGuard[Mapping[object, object]]:
    return isinstance(SourceValue, Mapping)


# runtime sequence checks need an object contract without accepting scalar containers
def IsMetaSeq(SourceValue: object) -> TypeGuard[Sequence[object]]:
    return isinstance(SourceValue, Sequence) and not isinstance(
        SourceValue, (str, bytes, bytearray)
    )


# nested metadata needs checked string keyed mappings before tests inspect vendor fields
def MetaMap(SourceValue: object) -> dict[str, object]:
    if not IsMetaMap(SourceValue):
        raise TypeError("metadata value must be a mapping")
    ResultValue: dict[str, object] = {}
    for KeyValue, ItemValue in SourceValue.items():
        if not isinstance(KeyValue, str):
            raise TypeError("metadata mapping keys must be strings")
        ResultValue[KeyValue] = ItemValue
    return ResultValue


# nested metadata needs checked sequences without accepting text or binary scalar values
def MetaSeq(SourceValue: object) -> tuple[object, ...]:
    if not IsMetaSeq(SourceValue):
        raise TypeError("metadata value must be a sequence")
    return tuple(SourceValue)


# external document assertions share one recursive metadata boundary across portable write tests
def OuterDocs(DocValue: CadDocument) -> tuple[dict[str, object], ...]:
    FreecadMeta = MetaMap(DocValue.metadata["freecad"])
    return tuple(
        MetaMap(ItemValue) for ItemValue in MetaSeq(FreecadMeta["external_documents"])
    )


# this binding exists because shared behavior needs one stable value
KSample = FilePath(__file__).parents[3] / "examples" / ".SLDPRT" / "example.SLDPRT"

# this binding exists because shared behavior needs one stable value
KFreecadExamples = (
    FilePath(__file__).parents[4]
    / "Parashell"
    / ".pixi"
    / "envs"
    / "default"
    / "Library"
    / "data"
    / "examples"
)


# this definition exists because focused behavior needs one stable owner
def LineEntity(
    IdValue: str, Start: tuple[float, float], EndValue: tuple[float, float]
) -> SketchEntity:
    return SketchEntity(
        IdValue, GeomKind.LINE, LineGeom(VectorTwo(*Start), VectorTwo(*EndValue))
    )


# this definition exists because focused behavior needs one stable owner
def TestClosedEdge() -> None:
    First = tuple(
        (
            LineEntity(IdValue, Start, EndValue)
            for IdValue, Start, EndValue in (
                ("edge:0", (-30.0, -15.0), (30.0, -15.0)),
                ("edge:1", (30.0, -15.0), (30.0, 15.0)),
                ("edge:2", (30.0, 15.0), (-30.0, 15.0)),
                ("edge:3", (-30.0, 15.0), (-30.0, -15.0)),
            )
        )
    )
    Second = tuple(
        (
            LineEntity(IdValue, Start, EndValue)
            for IdValue, Start, EndValue in (
                ("edge:4", (50.0, 0.0), (60.0, 0.0)),
                ("edge:5", (60.0, 0.0), (55.0, 10.0)),
                ("edge:6", (55.0, 10.0), (50.0, 0.0)),
            )
        )
    )
    assert ClosedProfile((*First, *Second)) == (
        ("edge:0", "edge:1", "edge:2", "edge:3"),
        ("edge:4", "edge:5", "edge:6"),
    )


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    "Entities",
    (
        (
            LineEntity("open:0", (0.0, 0.0), (10.0, 0.0)),
            LineEntity("open:1", (10.0, 0.0), (10.0, 10.0)),
            LineEntity("open:2", (10.0, 10.0), (0.0, 10.0)),
        ),
        (
            LineEntity("branch:0", (0.0, 0.0), (10.0, 0.0)),
            LineEntity("branch:1", (10.0, 0.0), (10.0, 10.0)),
            LineEntity("branch:2", (10.0, 10.0), (0.0, 10.0)),
            LineEntity("branch:3", (0.0, 10.0), (0.0, 0.0)),
            LineEntity("branch:4", (0.0, 0.0), (-10.0, 0.0)),
        ),
        (
            LineEntity("cross:0", (-10.0, -10.0), (10.0, 10.0)),
            LineEntity("cross:1", (10.0, 10.0), (-10.0, 10.0)),
            LineEntity("cross:2", (-10.0, 10.0), (10.0, -10.0)),
            LineEntity("cross:3", (10.0, -10.0), (-10.0, -10.0)),
        ),
    ),
)
def TestClosed(Entities: tuple[SketchEntity, ...]) -> None:
    assert ClosedProfile(Entities) == ()


# this definition exists because focused behavior needs one stable owner
def TestReaderFrom() -> None:

    # this definition exists because focused behavior needs one stable owner
    def Rectangle(RootValue: ET.Element) -> None:
        GeomValue = RootValue.find(
            "./ObjectData/Object[@name='Sketch']/Properties/Property[@name='Geometry']/GeometryList"
        )
        Constraints = RootValue.find(
            "./ObjectData/Object[@name='Sketch']/Properties/Property[@name='Constraints']/ConstraintList"
        )
        assert GeomValue is not None
        assert Constraints is not None
        GeomValue.clear()
        GeomValue.set("count", "4")
        Constraints.clear()
        Constraints.set("count", "0")
        Points = ((-30.0, -15.0), (30.0, -15.0), (30.0, 15.0), (-30.0, 15.0))
        for Index, Start in enumerate(Points):
            EndValue = Points[(Index + 1) % len(Points)]
            ItemValue = XmlTree.SubElement(
                GeomValue,
                "Geometry",
                {
                    "type": "Part::GeomLineSegment",
                    "id": str(Index + 1),
                    "migrated": "1",
                },
            )
            XmlTree.SubElement(
                ItemValue,
                "LineSegment",
                {
                    "StartX": str(Start[0]),
                    "StartY": str(Start[1]),
                    "EndX": str(EndValue[0]),
                    "EndY": str(EndValue[1]),
                },
            )
            XmlTree.SubElement(ItemValue, "Construction", {"value": "0"})

    DocValue = FreeCadAdapter().read(RewriteDocXml(NativePart(), Rectangle))
    Sketch = DocValue.sketches[0]
    assert Sketch.constraints == ()
    assert Sketch.closed_profile_entity_ids == (
        tuple((Entity.id for Entity in Sketch.entities)),
    )


# this definition exists because focused behavior needs one stable owner
def TestOriginUse() -> None:

    # this definition exists because focused behavior needs one stable owner
    def Plane(
        NameValue: str,
        Label: str,
        Quaternion: tuple[float, float, float, float],
        Origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
        RoleValue: str = "",
        TypeId: str = "App::Plane",
    ) -> NativeObject:
        Placement = NativePlacement()
        Value = Placement.find("./PropertyPlacement")
        assert Value is not None
        for KeyValue, Coordinate in zip(("Q0", "Q1", "Q2", "Q3"), Quaternion):
            Value.set(KeyValue, str(Coordinate))
        for KeyValue, Coordinate in zip(("Px", "Py", "Pz"), Origin):
            Value.set(KeyValue, str(Coordinate))
        Properties = {
            "Label": NativeProp(
                "Label", "App::PropertyString", "String", {"value": Label}
            ),
            "Placement": Placement,
        }
        if RoleValue:
            Properties["Role"] = NativeProp(
                "Role", "App::PropertyString", "String", {"value": RoleValue}
            )
        return NativeObject(
            NameValue, TypeId, 0, NameValue, False, (), (), (), Properties
        )

    HalfValue = MathValue.sqrt(0.5)
    Objects = (
        Plane("XY_Plane", "XY-plane", (0.0, 0.0, 0.0, 1.0), RoleValue="XY_Plane"),
        Plane(
            "XZ_Plane",
            "XZ-plane",
            (HalfValue, 0.0, 0.0, HalfValue),
            RoleValue="XZ_Plane",
        ),
        Plane("YZ_Plane", "YZ-plane", (0.5, 0.5, 0.5, 0.5), RoleValue="YZ_Plane"),
        Plane(
            "DatumPlane",
            "Datum Plane",
            (
                0.0,
                0.0,
                MathValue.sin(MathValue.pi / 8.0),
                MathValue.cos(MathValue.pi / 8.0),
            ),
            (7.0, 8.0, 9.0),
            TypeId="PartDesign::Plane",
        ),
    )
    Planes, Sketches = ParseSketchMut(Objects, [], set())
    assert Sketches == ()
    assert [Value.id for Value in Planes] == [
        "freecad:plane:XY_Plane",
        "freecad:plane:XZ_Plane",
        "freecad:plane:YZ_Plane",
        "freecad:plane:DatumPlane",
    ]
    assert [Value.attributes.get("principal_index") for Value in Planes] == [
        0,
        1,
        2,
        None,
    ]
    Frames = tuple(
        (
            (
                (
                    Value.transform.x_axis.x,
                    Value.transform.x_axis.y,
                    Value.transform.x_axis.z,
                ),
                (
                    Value.transform.y_axis.x,
                    Value.transform.y_axis.y,
                    Value.transform.y_axis.z,
                ),
                (
                    Value.transform.z_axis.x,
                    Value.transform.z_axis.y,
                    Value.transform.z_axis.z,
                ),
            )
            for Value in Planes[:3]
        )
    )
    assert Frames == (
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
        ((0.0, 0.0, -1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
    )
    Datum = Planes[3].transform
    assert (Datum.origin.x, Datum.origin.y, Datum.origin.z) == (7.0, 8.0, 9.0)
    assert (Datum.x_axis.x, Datum.x_axis.y, Datum.x_axis.z) == Pytest.approx(
        (HalfValue, HalfValue, 0.0)
    )
    assert (Datum.y_axis.x, Datum.y_axis.y, Datum.y_axis.z) == Pytest.approx(
        (-HalfValue, HalfValue, 0.0)
    )


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("Source", "Target", "ExpectedStart", "ExpectedEnd"),
    (
        (
            Transform(
                x_axis=VectorThree(1.0, 0.0, 0.0),
                y_axis=VectorThree(0.0, 0.0, 1.0),
                z_axis=VectorThree(0.0, -1.0, 0.0),
            ),
            Transform(
                x_axis=VectorThree(1.0, 0.0, 0.0),
                y_axis=VectorThree(0.0, 0.0, -1.0),
                z_axis=VectorThree(0.0, 1.0, 0.0),
            ),
            (2.0, -3.0),
            (5.0, -7.0),
        ),
        (
            Transform(
                x_axis=VectorThree(0.0, 1.0, 0.0),
                y_axis=VectorThree(0.0, 0.0, 1.0),
                z_axis=VectorThree(1.0, 0.0, 0.0),
            ),
            Transform(
                x_axis=VectorThree(0.0, 0.0, -1.0),
                y_axis=VectorThree(0.0, 1.0, 0.0),
                z_axis=VectorThree(1.0, 0.0, 0.0),
            ),
            (-3.0, 2.0),
            (-7.0, 5.0),
        ),
    ),
)
def TestPrincipal(
    Source: Transform,
    Target: Transform,
    ExpectedStart: tuple[float, float],
    ExpectedEnd: tuple[float, float],
) -> None:
    GeomValue = LineGeom(VectorTwo(2.0, 3.0), VectorTwo(5.0, 7.0))
    Reframed = ReframeGeom(GeomValue, PlaneReframe(Source, Target))
    assert isinstance(Reframed, LineGeom)
    assert (Reframed.start.x, Reframed.start.y) == ExpectedStart
    assert (Reframed.end.x, Reframed.end.y) == ExpectedEnd

    # this definition exists because focused behavior needs one stable owner
    def World(Transform: Transform, Point: VectorTwo) -> tuple[float, float, float]:
        return (
            Transform.origin.x
            + Point.x * Transform.x_axis.x
            + Point.y * Transform.y_axis.x,
            Transform.origin.y
            + Point.x * Transform.x_axis.y
            + Point.y * Transform.y_axis.y,
            Transform.origin.z
            + Point.x * Transform.x_axis.z
            + Point.y * Transform.y_axis.z,
        )

    assert World(Source, GeomValue.start) == Pytest.approx(
        World(Target, Reframed.start)
    )
    assert World(Source, GeomValue.end) == Pytest.approx(World(Target, Reframed.end))


# this definition exists because focused behavior needs one stable owner
def TestPrePayload() -> None:
    Source = Replace(
        NeutralDoc(),
        brep_payloads=(
            BrepPayload(
                "legacy-shape",
                "opencascade",
                "shape",
                "Open CASCADE 7.8",
                Hashlib.sha256(b"legacy shape").hexdigest(),
                data=b"legacy shape",
                source_stream="Body.Shape.brp",
                role=PayloadRole.BREP,
                file_extension=".brep",
            ),
            BrepPayload(
                "legacy-fcstd",
                "freecad.fcstd",
                "native_document",
                "FreeCAD Schema 4",
                Hashlib.sha256(b"legacy FCStd").hexdigest(),
                data=b"legacy FCStd",
                source_stream="Legacy.FCStd",
                role=PayloadRole.DOCUMENT,
                file_extension=".FCStd",
            ),
            BrepPayload(
                "legacy-history",
                "catia.v5.osmx",
                "native_feature_graph",
                "CATPrtCont",
                Hashlib.sha256(b"legacy history").hexdigest(),
                data=b"legacy history",
                source_stream="1000_00000002_2",
                role=PayloadRole.FEATURE_HISTORY,
                file_extension=".osmx",
            ),
            BrepPayload(
                "legacy-tessellation",
                "catia.cgr",
                "native_tessellation",
                "CATCGRCont",
                Hashlib.sha256(b"legacy tessellation").hexdigest(),
                data=b"legacy tessellation",
                source_stream="1000_00000004_4",
                role=PayloadRole.TESSELLATION,
                file_extension=".cgr",
            ),
        ),
    )
    Manifest = DocToManifest(Source)
    PayloadContainerValue: object = Manifest.get("brep_payloads")
    assert FreecadAdapterModule.IsPayloadMap(PayloadContainerValue)
    PayloadSequenceValue: object = PayloadContainerValue.get("$tuple")
    assert FreecadAdapterModule.IsPayloadSeq(PayloadSequenceValue)
    LegacyPayloads: list[dict[str, object]] = []
    for PayloadValue in PayloadSequenceValue:
        assert FreecadAdapterModule.IsPayloadMap(PayloadValue)
        PayloadData = dict(PayloadValue)
        PayloadData.pop("role")
        PayloadData.pop("file_extension")
        LegacyPayloads.append(PayloadData)
    PayloadContainer = dict(PayloadContainerValue)
    PayloadContainer["$tuple"] = LegacyPayloads
    Manifest["brep_payloads"] = PayloadContainer
    Carrier = BuildFcstdArchive(Manifest)
    Restored = FreeCadAdapter().read(
        Carrier, ReadOptions(include_brep=True, include_tessellation=True)
    )
    Fields = {
        Payload.id: (Payload.role, Payload.file_extension, Payload.data)
        for Payload in Restored.brep_payloads
    }
    assert Fields == {
        "legacy-shape": (PayloadRole.BREP, ".brep", b"legacy shape"),
        "legacy-fcstd": (PayloadRole.DOCUMENT, ".FCStd", b"legacy FCStd"),
        "legacy-history": (PayloadRole.FEATURE_HISTORY, ".osmx", b"legacy history"),
        "legacy-tessellation": (
            PayloadRole.TESSELLATION,
            ".cgr",
            b"legacy tessellation",
        ),
    }
    Filtered = FreeCadAdapter().read(
        Carrier, ReadOptions(include_brep=False, include_tessellation=False)
    )
    assert {Payload.id for Payload in Filtered.brep_payloads} == {
        "legacy-fcstd",
        "legacy-history",
    }


# this definition exists because focused behavior needs one stable owner
def NativeProp(
    NameValue: str, TypeId: str, TagValue: str, Attributes: dict[str, str] | None = None
) -> XmlTree.Element:
    NodeValue = XmlTree.Element("Property", {"name": NameValue, "type": TypeId})
    XmlTree.SubElement(NodeValue, TagValue, Attributes or {})
    return NodeValue


# this definition exists because focused behavior needs one stable owner
def NativePlacement(NameValue: str = "Placement") -> XmlTree.Element:
    return NativeProp(
        NameValue,
        "App::PropertyPlacement",
        "PropertyPlacement",
        {"Px": "0", "Py": "0", "Pz": "0", "Q0": "0", "Q1": "0", "Q2": "0", "Q3": "1"},
    )


# this definition exists because focused behavior needs one stable owner
def NativeLinkList(NameValue: str, Values: tuple[str, ...]) -> XmlTree.Element:
    NodeValue = NativeProp(
        NameValue, "App::PropertyLinkList", "LinkList", {"count": str(len(Values))}
    )
    for Value in Values:
        XmlTree.SubElement(NodeValue[0], "Link", {"value": Value})
    return NodeValue


# this definition exists because focused behavior needs one stable owner
def NativeXlink(
    NameValue: str, Target: str, Subelements: tuple[str, ...] = (), FileValue: str = ""
) -> XmlTree.Element:
    NodeValue = NativeProp(
        NameValue,
        "App::PropertyXLinkSubHidden" if Subelements else "App::PropertyXLink",
        "XLink",
        {
            "file": FileValue,
            "stamp": "",
            "name": Target,
            "count": str(len(Subelements)),
        },
    )
    for SubElem in Subelements:
        XmlTree.SubElement(NodeValue[0], "Sub", {"value": SubElem})
    return NodeValue


# this definition exists because native object declarations have a separate archive responsibility
def NativeDeclsMut(
    RootValue: ET.Element,
    Objects: tuple[tuple[str, str, tuple[str, ...], tuple[ET.Element, ...]], ...],
    ObjectOptions: dict[str, NativeOptions],
) -> None:
    Declarations = XmlTree.SubElement(
        RootValue, "Objects", {"Count": str(len(Objects)), "Dependencies": "1"}
    )
    for ObjectValue in Objects:
        NameValue = ObjectValue[0]
        Dependencies = ObjectValue[2]
        DependencyNode = XmlTree.SubElement(
            Declarations,
            "ObjectDeps",
            {"Name": NameValue, "Count": str(len(Dependencies))},
        )
        for Dependency in Dependencies:
            XmlTree.SubElement(DependencyNode, "Dep", {"Name": Dependency})
    for Index, ObjectValue in enumerate(Objects, start=1):
        NameValue, TypeId = ObjectValue[:2]
        Options = ObjectOptions.get(NameValue, {})
        Attributes = {
            "type": TypeId,
            "name": NameValue,
            "id": str(Options.get("id", Index)),
        }
        if bool(Options.get("touched")):
            Attributes["Touched"] = "1"
        XmlTree.SubElement(Declarations, "Object", Attributes)


# this definition exists because native property payloads have a separate archive responsibility
def NativeDataMut(
    RootValue: ET.Element,
    Objects: tuple[tuple[str, str, tuple[str, ...], tuple[ET.Element, ...]], ...],
    ObjectOptions: dict[str, NativeOptions],
) -> None:
    DataValue = XmlTree.SubElement(
        RootValue, "ObjectData", {"Count": str(len(Objects))}
    )
    for ObjectValue in Objects:
        NameValue = ObjectValue[0]
        Properties = ObjectValue[3]
        Options = ObjectOptions.get(NameValue, {})
        Extensions = Options.get("extensions", ())
        ObjectAttributes = {"name": NameValue}
        if Extensions:
            ObjectAttributes["Extensions"] = "True"
        ObjectNode = XmlTree.SubElement(DataValue, "Object", ObjectAttributes)
        if Extensions:
            ExtensionNode = XmlTree.SubElement(
                ObjectNode, "Extensions", {"Count": str(len(Extensions))}
            )
            for Extension in Extensions:
                XmlTree.SubElement(
                    ExtensionNode,
                    "Extension",
                    {"type": Extension, "name": Extension.rsplit("::", 1)[-1]},
                )
        TransientProperties = Options.get("transient_properties", ())
        PropNode = XmlTree.SubElement(
            ObjectNode,
            "Properties",
            {
                "Count": str(len(Properties)),
                "TransientCount": str(len(TransientProperties)),
            },
        )
        PropNode.extend(TransientProperties)
        PropNode.extend(Properties)


# this definition exists because deterministic archive emission is independent of xml construction
def EmitArchive(RootValue: ET.Element, Entries: dict[str, bytes]) -> bytes:
    Stream = IoStream.BytesIO()
    with Zipfile.ZipFile(Stream, "w", Zipfile.ZIP_DEFLATED) as Archive:
        Archive.writestr(
            "Document.xml",
            XmlTree.tostring(RootValue, encoding="utf-8", xml_declaration=True),
        )
        for NameValue, Value in Entries.items():
            Archive.writestr(NameValue, Value)
    return Stream.getvalue()


# this definition exists because focused behavior needs one stable owner
def NativeArchive(
    Objects: tuple[tuple[str, str, tuple[str, ...], tuple[ET.Element, ...]], ...],
    Entries: dict[str, bytes],
    ObjectOptions: dict[str, NativeOptions] | None = None,
) -> bytes:
    Options = ObjectOptions or {}
    RootValue = XmlTree.Element(
        "Document", {"SchemaVersion": "4", "ProgramVersion": "1.0", "FileVersion": "1"}
    )
    NativeDeclsMut(RootValue, Objects, Options)
    NativeDataMut(RootValue, Objects, Options)
    return EmitArchive(RootValue, Entries)


# this definition exists because focused behavior needs one stable owner
def RewriteDocXml(Source: bytes, Mutate: FuncCall[[ET.Element], None]) -> bytes:
    Output = IoStream.BytesIO()
    with Zipfile.ZipFile(IoStream.BytesIO(Source)) as InputArchive:
        RootValue = XmlTree.fromstring(InputArchive.read("Document.xml"))
        Mutate(RootValue)
        DocXml = XmlTree.tostring(RootValue, encoding="utf-8", xml_declaration=True)
        with Zipfile.ZipFile(Output, "w", Zipfile.ZIP_DEFLATED) as OutputArchive:
            for InfoValue in InputArchive.infolist():
                OutputArchive.writestr(
                    InfoValue,
                    (
                        DocXml
                        if InfoValue.filename == "Document.xml"
                        else InputArchive.read(InfoValue)
                    ),
                )
    return Output.getvalue()


# this definition exists because focused behavior needs one stable owner
def MeshKernel(Endian: str = "<") -> bytes:
    Vertices = ((-2.0, 3.0, 1.0), (5.0, -7.0, 4.0), (1.0, 2.0, -6.0))
    Banner = (b"MESH-" * 52)[:255] + b"\n"
    Result = bytearray(Struct.pack(f"{Endian}II", 2695938256, 65536))
    Result.extend(Banner)
    Result.extend(Struct.pack(f"{Endian}II", len(Vertices), 1))
    for Vertex in Vertices:
        Result.extend(Struct.pack(f"{Endian}fff", *Vertex))
    Result.extend(
        Struct.pack(f"{Endian}IIIIII", 0, 1, 2, 4294967295, 4294967295, 4294967295)
    )
    Result.extend(Struct.pack(f"{Endian}ffffff", -2.0, 5.0, -7.0, 3.0, -6.0, 4.0))
    return bytes(Result)


# this definition exists because focused behavior needs one stable owner
def NativeMesh(Endian: str = "<", Inline: bool = False) -> bytes:
    MeshValue = NativeProp("Mesh", "Mesh::PropertyMeshKernel", "Mesh")
    Entries: dict[str, bytes] = {}
    if Inline:
        Points = XmlTree.SubElement(MeshValue[0], "Points", {"Count": "3"})
        for FirstCoord, SecondCoord, ThirdCoord in ((-2, 3, 1), (5, -7, 4), (1, 2, -6)):
            XmlTree.SubElement(
                Points,
                "P",
                {"x": str(FirstCoord), "y": str(SecondCoord), "z": str(ThirdCoord)},
            )
        Faces = XmlTree.SubElement(MeshValue[0], "Faces", {"Count": "1"})
        XmlTree.SubElement(
            Faces,
            "F",
            {
                "p0": "0",
                "p1": "1",
                "p2": "2",
                "n0": "4294967295",
                "n1": "4294967295",
                "n2": "4294967295",
            },
        )
    else:
        MeshValue[0].set("file", "Derived.MeshKernel.bms")
        Entries["Derived.MeshKernel.bms"] = MeshKernel(Endian)
    Properties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Derived Mesh"}),
        MeshValue,
    )
    return NativeArchive((("Derived", "Mesh::Import", (), Properties),), Entries)


# this definition exists because the native sketch fixture needs one coherent geometry payload
def NativeSketch() -> tuple[ET.Element, ...]:
    Attachment = NativeProp(
        "AttachmentSupport", "App::PropertyLinkSubList", "LinkSubList", {"count": "1"}
    )
    XmlTree.SubElement(Attachment[0], "Link", {"obj": "XY_Plane", "sub": ""})
    GeomValue = NativeProp(
        "Geometry", "Part::PropertyGeometryList", "GeometryList", {"count": "4"}
    )
    Circle = XmlTree.SubElement(
        GeomValue[0],
        "Geometry",
        {"type": "Part::GeomCircle", "id": "101", "migrated": "1"},
    )
    XmlTree.SubElement(
        Circle, "Circle", {"CenterX": "0", "CenterY": "0", "Radius": "5"}
    )
    XmlTree.SubElement(Circle, "Construction", {"value": "0"})
    Point = XmlTree.SubElement(
        GeomValue[0],
        "Geometry",
        {"type": "Part::GeomPoint", "id": "102", "migrated": "1"},
    )
    XmlTree.SubElement(Point, "GeomPoint", {"X": "2", "Y": "3", "Z": "0"})
    XmlTree.SubElement(Point, "Construction", {"value": "0"})
    Ellipse = XmlTree.SubElement(
        GeomValue[0],
        "Geometry",
        {"type": "Part::GeomEllipse", "id": "103", "migrated": "1"},
    )
    XmlTree.SubElement(
        Ellipse,
        "Ellipse",
        {
            "CenterX": "4",
            "CenterY": "5",
            "MajorAxisX": "1",
            "MajorAxisY": "0",
            "MajorRadius": "8",
            "MinorRadius": "3",
        },
    )
    XmlTree.SubElement(Ellipse, "Construction", {"value": "1"})
    Spline = XmlTree.SubElement(
        GeomValue[0],
        "Geometry",
        {"type": "Part::GeomBSplineCurve", "id": "104", "migrated": "1"},
    )
    SplineCurve = XmlTree.SubElement(
        Spline, "BSplineCurve", {"Degree": "2", "Periodic": "false"}
    )
    for FirstCoord, SecondCoord in (("0", "0"), ("2", "4"), ("5", "1")):
        XmlTree.SubElement(
            SplineCurve, "Pole", {"X": FirstCoord, "Y": SecondCoord, "Z": "0"}
        )
    XmlTree.SubElement(Spline, "Construction", {"value": "0"})
    Constraints = NativeProp(
        "Constraints",
        "Sketcher::PropertyConstraintList",
        "ConstraintList",
        {"count": "3"},
    )
    for Attributes in (
        {
            "Name": "Diameter",
            "Type": "18",
            "Value": "10",
            "IsDriving": "1",
            "IsActive": "1",
            "First": "0",
            "FirstPos": "3",
            "Second": "-2000",
            "SecondPos": "0",
            "Third": "-2000",
            "ThirdPos": "0",
        },
        {
            "Name": "Angle",
            "Type": "9",
            "Value": "1.5707963267948966",
            "IsDriving": "1",
            "IsActive": "1",
            "First": "0",
            "FirstPos": "3",
            "Second": "1",
            "SecondPos": "1",
            "Third": "-2000",
            "ThirdPos": "0",
        },
        {
            "Name": "PointOnObject",
            "Type": "13",
            "Value": "0",
            "IsDriving": "1",
            "IsActive": "1",
            "First": "1",
            "FirstPos": "1",
            "Second": "-3",
            "SecondPos": "3",
            "Third": "-2000",
            "ThirdPos": "0",
        },
    ):
        XmlTree.SubElement(Constraints[0], "Constrain", Attributes)
    Expressions = NativeProp(
        "ExpressionEngine",
        "App::PropertyExpressionEngine",
        "ExpressionEngine",
        {"count": "1"},
    )
    XmlTree.SubElement(
        Expressions[0],
        "Expression",
        {"path": "Constraints[0]", "expression": "diameter"},
    )
    return (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Sketch"}),
        Attachment,
        GeomValue,
        Constraints,
        Expressions,
        NativeProp("FullyConstrained", "App::PropertyBool", "Bool", {"value": "true"}),
        NativePlacement(),
    )


# this definition exists because focused behavior needs one stable owner
def NativePart(BrepData: bytes | None = None) -> bytes:
    PlaneProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "XY"}),
        NativePlacement(),
    )
    SketchProperties = NativeSketch()
    Profile = NativeProp(
        "Profile", "App::PropertyLinkSub", "LinkSub", {"value": "Sketch", "count": "0"}
    )
    Direction = NativeProp(
        "Direction",
        "App::PropertyVector",
        "PropertyVector",
        {"valueX": "0", "valueY": "0", "valueZ": "1"},
    )
    Shape = NativeProp(
        "Shape", "Part::PropertyPartShape", "Part", {"file": "Pad.Shape.brp"}
    )
    PadExpressions = NativeProp(
        "ExpressionEngine",
        "App::PropertyExpressionEngine",
        "ExpressionEngine",
        {"count": "1"},
    )
    XmlTree.SubElement(
        PadExpressions[0], "Expression", {"path": "Length", "expression": "height"}
    )
    PadProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Pad"}),
        Profile,
        NativeProp("Length", "App::PropertyLength", "Float", {"value": "25"}),
        NativeProp("Type", "App::PropertyEnumeration", "Integer", {"value": "0"}),
        NativeProp("Reversed", "App::PropertyBool", "Bool", {"value": "false"}),
        NativeProp("Midplane", "App::PropertyBool", "Bool", {"value": "false"}),
        Direction,
        Shape,
        PadExpressions,
    )
    BodyProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Body"}),
        NativeLinkList("Group", ("Sketch", "Pad")),
        NativeProp("Tip", "App::PropertyLink", "Link", {"value": "Pad"}),
    )
    BrepValue = (
        b"\nCASCADE Topology V1, (c) Matra-Datavision\nfixture\n"
        if BrepData is None
        else BrepData
    )
    return NativeArchive(
        (
            ("Body", "PartDesign::Body", ("Sketch", "Pad"), BodyProperties),
            ("XY_Plane", "App::Plane", (), PlaneProperties),
            ("Sketch", "Sketcher::SketchObject", ("XY_Plane",), SketchProperties),
            ("Pad", "PartDesign::Pad", ("Sketch", "Body"), PadProperties),
        ),
        {"Pad.Shape.brp": BrepValue},
    )


# this definition exists because focused behavior needs one stable owner
def NativeAsm(BrepData: bytes | None = None) -> bytes:
    ShapeProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Shape"}),
        NativeProp(
            "Shape", "Part::PropertyPartShape", "Part", {"file": "Shape.Shape.brp"}
        ),
    )
    AsmProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Assembly"}),
        NativeLinkList("Group", ("Joints", "PartLink", "Grounded", "Revolute")),
        NativePlacement(),
    )
    LinkProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Part 1"}),
        NativeXlink("LinkedObject", "Shape"),
        NativePlacement(),
        NativePlacement("LinkPlacement"),
        NativeProp("Visibility", "App::PropertyBool", "Bool", {"value": "true"}),
    )
    GroundedProxy = NativeProp(
        "Proxy",
        "App::PropertyPythonObject",
        "Python",
        {"value": "bnVsbA==", "encoded": "yes", "json": "yes"},
    )
    GroundedProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Grounded"}),
        GroundedProxy,
        NativeProp(
            "ObjectToGround", "App::PropertyLink", "Link", {"value": "PartLink"}
        ),
        NativePlacement(),
    )
    JointType = NativeProp(
        "JointType",
        "App::PropertyEnumeration",
        "Integer",
        {"value": "1", "CustomEnum": "true"},
    )
    EnumList = XmlTree.SubElement(JointType, "CustomEnumList", {"count": "2"})
    XmlTree.SubElement(EnumList, "Enum", {"value": "Fixed"})
    XmlTree.SubElement(EnumList, "Enum", {"value": "Revolute"})
    JointProxy = NativeProp(
        "Proxy",
        "App::PropertyPythonObject",
        "Python",
        {"value": "bnVsbA==", "encoded": "yes", "json": "yes"},
    )
    JointProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Revolute"}),
        JointProxy,
        JointType,
        NativeXlink("Reference1", "Assembly", ("PartLink.Face1", "PartLink.Edge1")),
        NativeXlink("Reference2", "Assembly", ("PartLink.Face2",)),
        NativePlacement("Placement1"),
        NativePlacement("Placement2"),
        NativeProp("Suppressed", "App::PropertyBool", "Bool", {"value": "false"}),
    )
    JointGroupProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Joints"}),
        NativeLinkList("Group", ("Grounded", "Revolute")),
    )
    OpaqueProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Opaque"}),
        NativeProp("Blob", "App::PropertyFileIncluded", "File", {"file": "Blob.bin"}),
    )
    BrepValue = (
        b"\nCASCADE Topology V1, (c) Matra-Datavision\nassembly fixture\n"
        if BrepData is None
        else BrepData
    )
    return NativeArchive(
        (
            ("Shape", "Part::Feature", (), ShapeProperties),
            (
                "Assembly",
                "Assembly::AssemblyObject",
                ("Joints", "PartLink", "Grounded", "Revolute"),
                AsmProperties,
            ),
            (
                "Joints",
                "Assembly::JointGroup",
                ("Grounded", "Revolute"),
                JointGroupProperties,
            ),
            ("PartLink", "App::Link", ("Shape",), LinkProperties),
            (
                "Grounded",
                "App::FeaturePython",
                ("Assembly", "PartLink"),
                GroundedProperties,
            ),
            ("Revolute", "App::FeaturePython", ("Assembly",), JointProperties),
            ("Opaque", "App::FeaturePython", (), OpaqueProperties),
        ),
        {"Shape.Shape.brp": BrepValue, "Blob.bin": b"opaque"},
    )


# this definition exists because focused behavior needs one stable owner
def NativeOuterAsm(
    Links: tuple[tuple[str, str, str, str], ...],
    GroupedNames: tuple[str, ...] | None = None,
) -> bytes:
    LinkNames = tuple((LinkValue[0] for LinkValue in Links))
    GroupedNames = LinkNames if GroupedNames is None else GroupedNames
    AsmProperties = (
        NativeProp(
            "Label", "App::PropertyString", "String", {"value": "External Assembly"}
        ),
        NativeLinkList("Group", GroupedNames),
        NativePlacement(),
    )
    Objects: list[tuple[str, str, tuple[str, ...], tuple[XmlTree.Element, ...]]] = [
        ("Assembly", "Assembly::AssemblyObject", GroupedNames, AsmProperties)
    ]
    for NameValue, TypeId, FileValue, Target in Links:
        Objects.append(
            (
                NameValue,
                TypeId,
                (),
                (
                    NativeProp(
                        "Label", "App::PropertyString", "String", {"value": NameValue}
                    ),
                    NativeXlink("LinkedObject", Target, FileValue=FileValue),
                    NativePlacement(),
                    NativePlacement("LinkPlacement"),
                    NativeProp(
                        "Visibility", "App::PropertyBool", "Bool", {"value": "true"}
                    ),
                ),
            )
        )
    return NativeArchive(tuple(Objects), {})


# this definition exists because focused behavior needs one stable owner
def NativeLinkOnly(FileValue: str, Target: str = "Body") -> bytes:
    Properties = (
        NativeProp(
            "Label", "App::PropertyString", "String", {"value": "External Part"}
        ),
        NativeXlink("LinkedObject", Target, FileValue=FileValue),
        NativePlacement(),
        NativePlacement("LinkPlacement"),
        NativeProp("Visibility", "App::PropertyBool", "Bool", {"value": "true"}),
    )
    return NativeArchive((("PartLink", "App::Link", (), Properties),), {})


# this definition exists because focused behavior needs one stable owner
def TestAdapterAnd() -> None:
    Adapter = FreeCadAdapter()
    assert Adapter.info is InfoValue
    assert FormatId == InfoValue.format_id
    assert (Suffix,) == InfoValue.extensions
    assert Adapter.info.capabilities == frozenset(Capability)
    assert set(CapabilityWriteTypeIds) == set(Capability)
    assert set(CapabilityCarrierReasons) == set(Capability)
    assert all(
        (isinstance(TypeIds, frozenset) for TypeIds in CapabilityWriteTypeIds.values())
    )
    assert all(
        (
            isinstance(Reason, CarrierReason)
            for Reason in CapabilityCarrierReasons.values()
        )
    )
    assert isinstance(CapabilityWriteTypeIds, MapProxy)
    assert isinstance(CapabilityCarrierReasons, MapProxy)
    assert NativeCapabilities == frozenset(
        (
            CapabilityValue
            for CapabilityValue, TypeIds in CapabilityWriteTypeIds.items()
            if TypeIds
        )
    )
    assert Adapter.info.native_capabilities == NativeCapabilities
    assert Adapter.info.media_types == ("application/x-extension-fcstd",)


# this definition exists because focused behavior needs one stable owner
def TestFormatHas() -> None:
    for Module in (FreecadAdapterModule, FreecadArchiveModule, FreecadNativeModule):
        Source = Inspect.getsource(Module)
        assert '"freecad.fcstd"' not in Source
        assert '".FCStd"' not in Source
        assert '".fcstd"' not in Source


# this definition exists because document and object protocol constants form one contract
def VerifyDocTypes() -> None:
    assert FreecadArchiveModule.DOCUMENT_ENTRY == "Document.xml"
    assert AsmObjectTypePrefix == "Assembly::"
    assert AsmRootTypeId == "Assembly::AssemblyObject"
    assert AsmJointGroupTypeId == "Assembly::JointGroup"
    assert AsmLinkTypeId == "Assembly::AssemblyLink"
    assert AppLinkTypeId == "App::Link"
    assert AppPartTypeId == "App::Part"
    assert BodyTypeId == "PartDesign::Body"
    assert SketchTypeId == "Sketcher::SketchObject"
    assert PartContainerTypeIds == frozenset({"Part::BodyBase", BodyTypeId})
    assert BodyContainerTypeIds == PartContainerTypeIds | {AppPartTypeId}
    assert NonFeatureObjectTypeIds == BodyContainerTypeIds | {SketchTypeId}
    assert StringHasherTags == frozenset({"StringHasher", "StringHasher2"})
    assert JointGroundProp == "ObjectToGround"
    assert JointRefProperties == ("Reference1", "Reference2")
    assert JointRefIndexByProp == {
        NameValue: Index for Index, NameValue in enumerate(JointRefProperties)
    }
    assert JointReservedLink == frozenset((JointGroundProp, *JointRefProperties))
    assert JointTypeProperties == frozenset({"JointType", "MateType"})
    assert AsmConnectorPropPrefixes == ("Reference", "Placement")
    assert XmlTrueValues == frozenset({"1", "true"})
    assert PermissiveTrueValues == XmlTrueValues | {"yes"}
    assert SplineControlTags == frozenset({"Pole", "Knot"})
    assert SubElemKindByPrefix == {
        KindValue.value.title(): KindValue for KindValue in SubElemMateEntityKinds
    }
    assert SupportPlaneTypeIds == frozenset(
        {"App::Plane", "Part::DatumPlane", "PartDesign::Plane"}
    )


# this definition exists because scalar registries form one protocol contract
def VerifyScalars() -> None:
    assert len(QuantityPropUnits) == 59
    assert (
        Hashlib.sha256(
            JsonValue.dumps(
                sorted(QuantityPropUnits.items()), separators=(",", ":")
            ).encode()
        ).hexdigest()
        == "e9cb0cb88f8f8cc431a538b891c20635bc685f8800d7118b53881be35839c8b8"
    )
    assert len({Value.type_id for Value in ScalarPropTypes}) == len(ScalarPropTypes)
    assert ScalarPropKinds == {
        **{
            f"App::Property{NameValue}": (ValueKind.QUANTITY, UnitValue, "Float")
            for NameValue, UnitValue in QuantityPropUnits.items()
        },
        **{
            Value.type_id: (Value.value_kind, Value.unit, Value.value_tag)
            for Value in ScalarPropTypes
        },
    }
    assert len(ScalarPropKinds) == 74


# this definition exists because feature registries form one protocol contract
def VerifyFeatures() -> None:
    assert len(FeatureTypes) == 93
    assert len({Value.type_id for Value in FeatureTypes}) == len(FeatureTypes)
    assert FeatureKindByTypeId == {Value.type_id: Value.kind for Value in FeatureTypes}
    assert tuple((Value.operation for Value in BoolOperationTypes)) == tuple(
        BoolOperation
    )
    assert BoolOperationTypeByKind == {
        Value.operation.value: Value for Value in BoolOperationTypes
    }
    assert CreateOperationNames == frozenset({"", BoolOperation.CREATE.value})
    assert set(FeatureWriteTypeIds) == set(FeatureKind)
    assert FeatureWriteKinds == frozenset(
        (KindValue for KindValue, TypeIds in FeatureWriteTypeIds.items() if TypeIds)
    )
    assert FeatureCarrierKinds == frozenset(FeatureKind) - FeatureWriteKinds
    assert FeatureWriteKinds | FeatureCarrierKinds == set(FeatureKind)
    assert FeatureWriteKinds.isdisjoint(FeatureCarrierKinds)
    assert FeatureWriteTypeIds[FeatureKind.EXTRUSION] == frozenset(
        (Value.type_id for Value in BoolOperationTypes)
    )
    assert {Value.type_id for Value in BoolOperationTypes} <= FeatureKindByTypeId.keys()
    assert tuple((Value.code for Value in ExtrusionTypes)) == tuple(range(6))
    assert ExtrusionTypeByCode == {Value.code: Value for Value in ExtrusionTypes}
    assert PocketTypeId == "PartDesign::Pocket"
    assert ExtrusionTypeByCode[1].end_condition == ExtrusionEndCondition.UP_TO_LAST
    assert (
        ExtrusionTypeByCode[1].pocket_end_condition == ExtrusionEndCondition.THROUGH_ALL
    )


# this definition exists because part type registries form one protocol contract
def VerifyPartTypes() -> None:
    assert len(PrimitiveFeatureTypeIds) == 39
    assert PrimitiveFeatureTypeIds == frozenset(
        (
            f"{Family.namespace}::{Prefix}{Shape}"
            for Family in PrimitiveFeatureFamilies
            for Prefix in Family.prefixes
            for Shape in Family.shapes
        )
    )
    assert PartObjectTypeIds == frozenset(
        (
            *FeatureKindByTypeId,
            *PrimitiveFeatureTypeIds,
            *SupportPlaneTypeIds,
            *BodyContainerTypeIds,
        )
    )
    assert len(PartObjectTypeIds) == 138
    assert (
        Hashlib.sha256(
            JsonValue.dumps(sorted(PartObjectTypeIds), separators=(",", ":")).encode()
        ).hexdigest()
        == "589bb6d7434a0fd03697172fe47b83a3385d0a9069aecf014e9de3715f1b1c8e"
    )
    assert AdditionalPartObjectType == frozenset(
        {"App::Plane", "Part::FeatureGeometrySet"}
    )
    assert RegisteredPartObjectType == PartObjectTypeIds - AdditionalPartObjectType
    assert len(RegisteredPartObjectType) == 136
    assert (
        Hashlib.sha256(
            JsonValue.dumps(
                sorted(RegisteredPartObjectType), separators=(",", ":")
            ).encode()
        ).hexdigest()
        == "5d46a78532f802c86552b56704f5238758e098dd1afb4ce9802b4ffc78649993"
    )


# this definition exists because constraint registries must remain internally bijective
def VerifyRules() -> None:
    assert RulePointByIndex == {Value.index: Value.name for Value in RulePoints}
    assert RulePointIndexByName == {
        NameValue: Value.index
        for Value in RulePoints
        for NameValue in (Value.name, *Value.aliases)
    }
    assert MidpointRefPointNames == frozenset(
        {
            "",
            "mid",
            *(
                NameValue
                for Value in RulePoints
                if Value.index == 3
                for NameValue in (Value.name, *Value.aliases)
            ),
        }
    )
    assert tuple((Value.code for Value in RuleTypes)) == tuple(range(1, 22))
    assert RuleKindByCode == {Value.code: Value.kind for Value in RuleTypes}
    assert RuleValueKindByCode == {
        Value.code: (Value.value_kind, Value.unit)
        for Value in RuleTypes
        if Value.value_kind is not None
    }
    assert DimensionalRuleCodes == frozenset(
        (Value.code for Value in RuleTypes if Value.value_kind is not None)
    )
    assert FixedRuleKinds == frozenset(
        (
            KindValue
            for KindValue, CodeValue in RuleCodeByKind.items()
            if CodeValue == RuleCodeByKind[RuleKind.BLOCK.value]
        )
    )
    assert set(RuleKindByCode.values()) == set(RuleKind) - {
        RuleKind.CONCENTRIC,
        RuleKind.FIXED,
        RuleKind.MIDPOINT,
        RuleKind.NATIVE,
    }
    assert set(RuleCodeByKind) == {
        Value.value
        for Value in RuleKind
        if Value not in {RuleKind.MIDPOINT, RuleKind.NATIVE}
    }
    assert set(RuleWriteCodes) == set(RuleKind)
    assert RuleWriteKinds == frozenset(
        (KindValue for KindValue, Codes in RuleWriteCodes.items() if Codes)
    )
    assert RuleComposedKinds == frozenset(
        {RuleKind.CONCENTRIC, RuleKind.FIXED, RuleKind.MIDPOINT}
    )
    assert RuleDirectKinds == RuleWriteKinds - RuleComposedKinds
    assert RuleCarrierKinds == frozenset(RuleKind) - (
        RuleDirectKinds | RuleComposedKinds
    )
    assert RuleWriteKinds | RuleCarrierKinds == set(RuleKind)
    assert RuleWriteKinds.isdisjoint(RuleCarrierKinds)


# this definition exists because geometry registries must partition native and carrier support
def VerifyGeometry() -> None:
    assert len({Value.type_id for Value in GeomTypes}) == len(GeomTypes)
    assert set(GeomKindByTypeId.values()) == set(GeomKind) - {GeomKind.NATIVE}
    assert set(GeomTypeIdsByKind) == {
        Value.value for Value in GeomKind if Value != GeomKind.NATIVE
    }
    NeutralGeomKinds = {
        Value.kind.value for Value in GeomTypes if Value.neutral_default
    }
    assert set(NeutralGeomTypeByKind) == NeutralGeomKinds
    assert set(NeutralGeomTypeIdByKind) == NeutralGeomKinds
    assert set(GeomWriteTypeIds) == set(GeomKind)
    assert GeomWriteKinds == frozenset(
        (KindValue for KindValue, TypeIds in GeomWriteTypeIds.items() if TypeIds)
    )
    assert GeomCarrierKinds == frozenset(GeomKind) - GeomWriteKinds
    assert GeomWriteKinds | GeomCarrierKinds == set(GeomKind)
    assert GeomWriteKinds.isdisjoint(GeomCarrierKinds)
    assert CircularGeomKinds == frozenset({GeomKind.CIRCLE.value, GeomKind.ARC.value})
    assert SplineGeomKinds == frozenset({GeomKind.BEZIER.value, GeomKind.SPLINE.value})
    assert SplineGeomTypeIds == frozenset(
        (Value.type_id for Value in GeomTypes if Value.kind.value in SplineGeomKinds)
    )


# this definition exists because assembly mate registries must preserve support partitions
def VerifyMates() -> None:
    assert len({Value.name for Value in JointTypeDefinitions}) == len(
        JointTypeDefinitions
    )
    assert set(MateKindByJointType) == set(JointTypes)
    assert set(MateKindByJointType.values()) == {
        Value.kind for Value in JointTypeDefinitions
    }
    CarrierOnlyMates = {
        MateKind.COINCIDENT,
        MateKind.TANGENT,
        MateKind.COORDINATE,
        MateKind.UNIVERSAL_JOINT,
        MateKind.CAM,
        MateKind.SLOT,
        MateKind.WIDTH,
        MateKind.SYMMETRIC,
        MateKind.LINEAR_COUPLER,
        MateKind.PATH,
        MateKind.MAGNETIC,
        MateKind.PROFILE_CENTER,
        MateKind.NATIVE,
    }
    SupportedMates = {Value for Value in MateKind if Value.value in JointTypeByMateKind}
    assert SupportedMates.isdisjoint(CarrierOnlyMates)
    assert SupportedMates | CarrierOnlyMates == set(MateKind)
    assert set(MateWriteTypes) == set(MateKind)
    assert MateWriteKinds == frozenset(
        (KindValue for KindValue, Types in MateWriteTypes.items() if Types)
    )
    assert MateCarrierKinds == frozenset(MateKind) - MateWriteKinds
    assert MateWriteKinds == SupportedMates
    assert MateCarrierKinds == CarrierOnlyMates
    assert MateWriteKinds.isdisjoint(MateCarrierKinds)
    assert JointTypesUsingDistance == frozenset(
        (Value.name for Value in JointTypeDefinitions if Value.uses_distance)
    )
    assert JointTypesUsingSecond == frozenset(
        (Value.name for Value in JointTypeDefinitions if Value.uses_second_distance)
    )
    assert MateKindsUsingDistance == frozenset(
        (Value.kind for Value in JointTypeDefinitions if Value.uses_distance)
    )
    assert MateKindsUsingSecond == frozenset(
        (Value.kind for Value in JointTypeDefinitions if Value.uses_second_distance)
    )


# this definition exists because focused behavior needs one stable owner
def TestProtocolAre() -> None:
    VerifyDocTypes()
    VerifyScalars()
    VerifyFeatures()
    VerifyPartTypes()
    VerifyRules()
    VerifyGeometry()
    VerifyMates()


# this definition exists because focused behavior needs one stable owner
def TestBrepFilter() -> None:
    Payloads = tuple(
        (
            BrepPayload(
                f"payload:{RoleValue.value}",
                "test.payload",
                RoleValue.value,
                "1",
                Hashlib.sha256(RoleValue.value.encode("ascii")).hexdigest(),
                data=RoleValue.value.encode("ascii"),
                role=RoleValue,
            )
            for RoleValue in PayloadRole
        )
    )
    Source = NeutralDoc()
    DocValue = Replace(
        Source,
        brep_payloads=Payloads,
        capabilities=Source.capabilities
        | {Capability.BREP, Capability.TESSELLATION, Capability.NATIVE_PAYLOADS},
    )
    Filtered = FilteredDoc(
        DocValue, ReadOptions(include_brep=False, include_tessellation=True)
    )
    assert {Payload.role for Payload in Filtered.brep_payloads} == set(PayloadRole) - {
        PayloadRole.BREP
    }
    assert Capability.BREP not in Filtered.capabilities
    assert Capability.TESSELLATION in Filtered.capabilities
    assert Capability.NATIVE_PAYLOADS in Filtered.capabilities


# this definition exists because focused behavior needs one stable owner
def TestEncodableIs() -> None:
    Source = Replace(NeutralDoc(), brep=TriangleBrep())
    Adapter = FreeCadAdapter()
    CarrierOutput = IoStream.BytesIO()
    CarrierResult = Adapter.write(Source, CarrierOutput)
    CarrierTransfers = {
        Transfer.capability: Transfer for Transfer in CarrierResult.transfers
    }
    assert CarrierTransfers[Capability.BREP].mode == TransferMode.NATIVE
    assert CarrierTransfers[Capability.BREP].carrier_reason is None
    assert Adapter.read(CarrierOutput.getvalue()) == Source
    MeshValue = MeshRecord(
        "mesh:brep-display",
        "BRep display",
        (
            VectorThree(0.0, 0.0, 0.0),
            VectorThree(1.0, 0.0, 0.0),
            VectorThree(0.0, 1.0, 0.0),
        ),
        ((0, 1, 2),),
    )
    Displayed = Replace(Source, meshes=(MeshValue,))
    MixedOutput = IoStream.BytesIO()
    MixedResult = Adapter.write(Displayed, MixedOutput)
    MixedTransfers = {
        Transfer.capability: Transfer for Transfer in MixedResult.transfers
    }
    assert MixedTransfers[Capability.BREP].mode == TransferMode.NATIVE
    assert MixedTransfers[Capability.BREP].carrier_reason is None
    assert MixedTransfers[Capability.TESSELLATION].mode == TransferMode.NATIVE
    with Zipfile.ZipFile(IoStream.BytesIO(MixedOutput.getvalue())) as Archive:
        ShapeEntries = [
            NameValue for NameValue in Archive.namelist() if NameValue.endswith(".brp")
        ]
        assert ShapeEntries
        assert all(
            (
                b"CASCADE Topology V" in Archive.read(NameValue)[:512]
                for NameValue in ShapeEntries
            )
        )
    assert Adapter.read(MixedOutput.getvalue()) == Displayed


# this definition exists because focused behavior needs one stable owner
def TestNonOpenBrep() -> None:
    Source = NeutralDoc()
    Payload = BrepPayload(
        "foreign:brep",
        "parasolid.x_b",
        "shape",
        "SCH_3500040",
        Hashlib.sha256(b"PS\x00\x00foreign").hexdigest(),
        data=b"PS\x00\x00foreign",
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )
    DocValue = Replace(Source, brep_payloads=(Payload,))
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    Transfers = {Transfer.capability: Transfer for Transfer in Result.transfers}
    assert Transfers[Capability.BREP].mode == TransferMode.CARRIER
    assert Transfers[Capability.BREP].carrier_reason is CarrierReason.SOURCE_OPAQUE
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        ShapeFiles = {
            NodeValue.get("file", "")
            for NodeValue in RootValue.findall(
                ".//Property[@type='Part::PropertyPartShape']/Part"
            )
            if NodeValue.get("file", "")
        }
        assert ShapeFiles == set()
        assert Archive.read("interchange/native/foreign_brep.x_b") == Payload.data
    assert FreeCadAdapter().read(Output.getvalue()) == DocValue


# this definition exists because focused behavior needs one stable owner
def TestSolidworksA() -> None:
    Source = NeutralDoc()
    Circle = SketchEntity(
        "sketch:1:circle:1", GeomKind.CIRCLE, CircleGeom(VectorTwo(0.0, 0.0), 10.0)
    )
    Sketch = Replace(
        Source.sketches[0],
        entities=(Circle,),
        constraints=(),
        closed_profile_entity_ids=((Circle.id,),),
    )
    Feature = Replace(
        Source.feature_timeline[0],
        definition=ExtrusionFeature(ParamValue(5.0, ValueKind.LENGTH, "mm")),
    )
    DataValue = b"PS\x00\x00opaque-source"
    Payload = BrepPayload(
        "solidworks:brep",
        "parasolid.x_b",
        "partition",
        "SCH_3500040",
        Hashlib.sha256(DataValue).hexdigest(),
        data=DataValue,
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )
    DocValue = Replace(
        Source,
        source=Replace(Source.source, format_id="solidworks.sldprt"),
        sketches=(Sketch,),
        feature_timeline=(Feature,),
        brep_payloads=(Payload,),
    )
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    assert Result.application_usable is True
    assert FreecadArchiveModule.native_shape_feature_count(DocToManifest(DocValue)) == 1


# this definition exists because focused behavior needs one stable owner
def TestDecodedBrep() -> None:
    Source = NeutralDoc()
    DataValue = b"PS\x00\x00retained-source"
    Payload = BrepPayload(
        "source:brep",
        "parasolid.x_b",
        "partition",
        "SCH_3500040",
        Hashlib.sha256(DataValue).hexdigest(),
        data=DataValue,
        role=PayloadRole.BREP,
        file_extension=".x_b",
    )
    DocValue = Replace(Source, brep=TriangleBrep(), brep_payloads=(Payload,))
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    Transfers = {Transfer.capability: Transfer for Transfer in Result.transfers}
    assert Transfers[Capability.BREP].mode is TransferMode.NATIVE
    assert Transfers[Capability.BREP].carrier_reason is None
    assert Transfers[Capability.NATIVE_PAYLOADS].mode is TransferMode.CARRIER
    assert (
        Transfers[Capability.NATIVE_PAYLOADS].carrier_reason
        is CarrierReason.TARGET_UNSUPPORTED
    )
    assert FreeCadAdapter().read(Output.getvalue()) == DocValue


# this definition exists because focused behavior needs one stable owner
def TestDuplicateDo() -> None:
    Source = NeutralDoc()
    RefValue = FeatureStep(
        "feature:reference-plane",
        "Reference plane",
        FeatureKind.REFERENCE,
        1,
        attributes={"native_type": "Plane"},
    )
    Housekeeping = FeatureStep(
        "feature:comments",
        "Comments",
        FeatureKind.NATIVE,
        2,
        attributes={"native_type": "Comments"},
    )
    DocValue = Replace(
        Source, feature_timeline=(*Source.feature_timeline, RefValue, Housekeeping)
    )
    DocValue.assert_valid()
    Baseline = FreeCadAdapter().write(Source, IoStream.BytesIO())
    Result = FreeCadAdapter().write(DocValue, IoStream.BytesIO())
    BaselineTransfers = {
        Transfer.capability: Transfer for Transfer in Baseline.transfers
    }
    Transfers = {Transfer.capability: Transfer for Transfer in Result.transfers}
    assert (
        Transfers[Capability.PARAMETRIC_HISTORY]
        == BaselineTransfers[Capability.PARAMETRIC_HISTORY]
    )


# this definition exists because focused behavior needs one stable owner
def TestFollow() -> None:
    DocValue = FreeCadAdapter().read(NativePart())
    assert DocValue.capabilities == frozenset(
        {
            Capability.PARAMETERS,
            Capability.PARAMETRIC_HISTORY,
            Capability.SUPPORT_PLANES,
            Capability.EDITABLE_SKETCHES,
            Capability.BODY_STRUCTURE,
            Capability.CONFIGURATIONS,
            Capability.EXPRESSIONS,
            Capability.BREP,
            Capability.NATIVE_PAYLOADS,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
        }
    )
    assert Capability.MATERIALS not in DocValue.capabilities
    AsmValue = FreeCadAdapter().read(NativeAsm())
    assert AsmValue.capabilities == frozenset(
        {
            Capability.PARAMETERS,
            Capability.CONFIGURATIONS,
            Capability.BREP,
            Capability.ASSEMBLIES,
            Capability.ASSEMBLY_MATES,
            Capability.COMPONENT_DOCUMENTS,
            Capability.NATIVE_PAYLOADS,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
        }
    )


# this definition exists because all synthetic part design features share one xml graph mutation
def AddFeatureMut(
    DocRoot: ET.Element,
    NameValue: str,
    TypeId: str,
    Dependencies: tuple[str, ...],
    PropertiesData: tuple[ET.Element, ...],
) -> None:
    ObjectData = DocRoot.find("./ObjectData")
    ObjectsData = DocRoot.find("./Objects")
    assert ObjectData is not None
    assert ObjectsData is not None
    ObjectsData.set("Count", str(int(ObjectsData.get("Count", "0")) + 1))
    ObjectData.set("Count", str(int(ObjectData.get("Count", "0")) + 1))
    BodyDeps = ObjectsData.find("./ObjectDeps[@Name='Body']")
    assert BodyDeps is not None
    XmlTree.SubElement(BodyDeps, "Dep", {"Name": NameValue})
    BodyDeps.set("Count", str(int(BodyDeps.get("Count", "0")) + 1))
    FeatureDeps = XmlTree.SubElement(
        ObjectsData, "ObjectDeps", {"Name": NameValue, "Count": str(len(Dependencies))}
    )
    for DependencyName in Dependencies:
        XmlTree.SubElement(FeatureDeps, "Dep", {"Name": DependencyName})
    XmlTree.SubElement(
        ObjectsData, "Object", {"type": TypeId, "name": NameValue, "id": "5"}
    )
    BodyProperties = ObjectData.find("./Object[@name='Body']/Properties")
    assert BodyProperties is not None
    GroupData = BodyProperties.find("./Property[@name='Group']/LinkList")
    TipData = BodyProperties.find("./Property[@name='Tip']/Link")
    assert GroupData is not None
    assert TipData is not None
    XmlTree.SubElement(GroupData, "Link", {"value": NameValue})
    GroupData.set("count", str(int(GroupData.get("count", "0")) + 1))
    TipData.set("value", NameValue)
    FeatureData = XmlTree.SubElement(ObjectData, "Object", {"name": NameValue})
    FeatureProperties = XmlTree.SubElement(
        FeatureData,
        "Properties",
        {"Count": str(len(PropertiesData)), "TransientCount": "0"},
    )
    FeatureProperties.extend(PropertiesData)


# this definition exists because the chamfer fixture needs one reusable xml mutation
def AddChamferMut(RootData: ET.Element) -> None:
    BaseData = NativeProp(
        "Base", "App::PropertyLinkSub", "LinkSub", {"value": "Pad", "count": "1"}
    )
    XmlTree.SubElement(BaseData[0], "Sub", {"value": "Edge5"})
    PropertiesData = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Chamfer"}),
        BaseData,
        NativeProp("BaseFeature", "App::PropertyLink", "Link", {"value": "Pad"}),
        NativeProp("Size", "App::PropertyQuantityConstraint", "Float", {"value": "2"}),
        NativeProp("Size2", "App::PropertyQuantityConstraint", "Float", {"value": "1"}),
        NativeProp("Angle", "App::PropertyAngle", "Float", {"value": "45"}),
        NativeProp(
            "ChamferType", "App::PropertyEnumeration", "Integer", {"value": "0"}
        ),
        NativeProp("FlipDirection", "App::PropertyBool", "Bool", {"value": "false"}),
        NativeProp("UseAllEdges", "App::PropertyBool", "Bool", {"value": "false"}),
    )
    AddFeatureMut(
        RootData, "Chamfer", "PartDesign::Chamfer", ("Pad", "Body"), PropertiesData
    )


# this definition exists because the thickness fixture needs one reusable xml mutation
def AddThicknessMut(RootData: ET.Element) -> None:
    BaseData = NativeProp(
        "Base", "App::PropertyLinkSub", "LinkSub", {"value": "Pad", "count": "1"}
    )
    XmlTree.SubElement(BaseData[0], "Sub", {"value": "Face6"})
    PropertiesData = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Thickness"}),
        BaseData,
        NativeProp("BaseFeature", "App::PropertyLink", "Link", {"value": "Pad"}),
        NativeProp("Value", "App::PropertyQuantityConstraint", "Float", {"value": "2"}),
        NativeProp("Reversed", "App::PropertyBool", "Bool", {"value": "true"}),
    )
    AddFeatureMut(
        RootData, "Thickness", "PartDesign::Thickness", ("Pad", "Body"), PropertiesData
    )


# this definition exists because pattern fixtures share stable original and axis references
def PatternRefs(NameValue: str) -> tuple[ET.Element, ET.Element]:
    OriginalsData = NativeProp(
        "Originals", "App::PropertyLinkList", "LinkList", {"count": "1"}
    )
    XmlTree.SubElement(OriginalsData[0], "Link", {"value": "Pad"})
    DirectionData = NativeProp(
        NameValue, "App::PropertyLinkSub", "LinkSub", {"value": "Sketch", "count": "1"}
    )
    XmlTree.SubElement(DirectionData[0], "Sub", {"value": "N_Axis"})
    return OriginalsData, DirectionData


# this definition exists because the linear pattern fixture needs one reusable xml mutation
def AddLinearMut(DocRoot: ET.Element) -> None:
    OriginalsData, DirectionData = PatternRefs("Direction")
    PropertiesData = (
        NativeProp(
            "Label", "App::PropertyString", "String", {"value": "LinearPattern"}
        ),
        OriginalsData,
        DirectionData,
        NativeProp("Length", "App::PropertyLength", "Float", {"value": "10"}),
        NativeProp("Offset", "App::PropertyLength", "Float", {"value": "5"}),
        NativeProp("Occurrences", "App::PropertyInteger", "Integer", {"value": "3"}),
        NativeProp("Mode", "App::PropertyEnumeration", "Integer", {"value": "0"}),
        NativeProp("Reversed", "App::PropertyBool", "Bool", {"value": "false"}),
    )
    AddFeatureMut(
        DocRoot,
        "LinearPattern",
        "PartDesign::LinearPattern",
        ("Pad", "Sketch", "Body"),
        PropertiesData,
    )


# this definition exists because the polar pattern fixture needs one reusable xml mutation
def AddPolarMut(DocRoot: ET.Element) -> None:
    OriginalsData, AxisData = PatternRefs("Axis")
    PropertiesData = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "PolarPattern"}),
        OriginalsData,
        AxisData,
        NativeProp("Angle", "App::PropertyAngle", "Float", {"value": "360"}),
        NativeProp("Occurrences", "App::PropertyInteger", "Integer", {"value": "4"}),
        NativeProp("Reversed", "App::PropertyBool", "Bool", {"value": "false"}),
    )
    AddFeatureMut(
        DocRoot,
        "PolarPattern",
        "PartDesign::PolarPattern",
        ("Pad", "Sketch", "Body"),
        PropertiesData,
    )


# this definition exists because focused behavior needs one stable owner
def TestEqualIs() -> None:

    # this definition exists because focused behavior needs one stable owner
    def AddChamfer(RootData: ET.Element) -> None:
        AddChamferMut(RootData)

    DocData = FreeCadAdapter().read(RewriteDocXml(NativePart(), AddChamfer))
    ChamferData = next(
        (
            ItemData
            for ItemData in DocData.feature_timeline
            if ItemData.kind == FeatureKind.CHAMFER
        )
    )
    assert isinstance(ChamferData.definition, ChamferFeature)
    assert ChamferData.definition.distance == ParamValue(2.0, ValueKind.LENGTH, "mm")
    assert ChamferData.definition.mode == "equal_distance"
    assert ChamferData.definition.second_distance is None
    assert ChamferData.definition.angle is None
    assert ChamferData.input_feature_ids == ("freecad:feature:Pad",)
    assert len(ChamferData.selection_ids) == 1
    SelectionData = next(
        (
            ItemData
            for ItemData in DocData.selections
            if ItemData.id == ChamferData.selection_ids[0]
        )
    )
    assert SelectionData.path[0].entity_kind == "edge"
    assert SelectionData.path[0].subelement == "Edge5"


# this definition exists because focused behavior needs one stable owner
def TestInwardIs() -> None:

    # this definition exists because focused behavior needs one stable owner
    def AddThickness(RootData: ET.Element) -> None:
        AddThicknessMut(RootData)

    DocData = FreeCadAdapter().read(RewriteDocXml(NativePart(), AddThickness))
    ShellData = next(
        (
            ItemData
            for ItemData in DocData.feature_timeline
            if ItemData.kind == FeatureKind.SHELL
        )
    )
    assert isinstance(ShellData.definition, ShellFeature)
    assert ShellData.definition.thickness == ParamValue(2.0, ValueKind.LENGTH, "mm")
    assert ShellData.definition.outward is False
    assert ShellData.input_feature_ids == ("freecad:feature:Pad",)
    assert len(ShellData.selection_ids) == 1
    SelectionData = next(
        (
            ItemData
            for ItemData in DocData.selections
            if ItemData.id == ShellData.selection_ids[0]
        )
    )
    assert SelectionData.path[0].entity_kind == "face"
    assert SelectionData.path[0].subelement == "Face6"


# this definition exists because focused behavior needs one stable owner
def TestPartdesignA() -> None:

    # this definition exists because focused behavior needs one stable owner
    def AddLinear(DocRoot: ET.Element) -> None:
        AddLinearMut(DocRoot)

    DocData = FreeCadAdapter().read(RewriteDocXml(NativePart(), AddLinear))
    PatternData = next(
        (
            ItemData
            for ItemData in DocData.feature_timeline
            if ItemData.kind == FeatureKind.PATTERN
        )
    )
    assert isinstance(PatternData.definition, LinearPatternFeature)
    assert PatternData.definition.spacing == ParamValue(5.0, ValueKind.LENGTH, "mm")
    assert PatternData.definition.instance_count == 3
    assert PatternData.definition.reversed is False
    assert PatternData.input_feature_ids == ("freecad:feature:Pad",)
    assert PatternData.selection_ids == (PatternData.definition.direction_selection_id,)
    SelectionData = next(
        (
            ItemData
            for ItemData in DocData.selections
            if ItemData.id == PatternData.definition.direction_selection_id
        )
    )
    assert SelectionData.path[0].entity_kind == "native"
    assert SelectionData.path[0].entity_id == "Sketch"
    assert SelectionData.path[0].subelement == "N_Axis"
    assert DocData.bodies[0].final_feature_id == PatternData.id


# this definition exists because focused behavior needs one stable owner
def TestPartdesignB() -> None:

    # this definition exists because focused behavior needs one stable owner
    def AddPolarPattern(DocRoot: ET.Element) -> None:
        AddPolarMut(DocRoot)

    DocData = FreeCadAdapter().read(RewriteDocXml(NativePart(), AddPolarPattern))
    PatternData = next(
        (
            ItemData
            for ItemData in DocData.feature_timeline
            if ItemData.kind == FeatureKind.PATTERN
        )
    )
    assert isinstance(PatternData.definition, CircularPatternFeature)
    assert PatternData.definition.angle == ParamValue(360.0, ValueKind.ANGLE, "deg")
    assert PatternData.definition.instance_count == 4
    assert PatternData.definition.reversed is False
    assert PatternData.input_feature_ids == ("freecad:feature:Pad",)
    assert PatternData.selection_ids == (PatternData.definition.axis_selection_id,)
    SelectionData = next(
        (
            ItemData
            for ItemData in DocData.selections
            if ItemData.id == PatternData.definition.axis_selection_id
        )
    )
    assert SelectionData.path[0].entity_kind == "native"
    assert SelectionData.path[0].entity_id == "Sketch"
    assert SelectionData.path[0].subelement == "N_Axis"
    assert DocData.bodies[0].final_feature_id == PatternData.id


# this definition exists because native transfer modes form one independent write contract
def VerifyTransfers(Result: WriteResult) -> None:
    Transfers = {ItemValue.capability: ItemValue.mode for ItemValue in Result.transfers}
    assert Transfers[Capability.SUPPORT_PLANES] is TransferMode.NATIVE
    assert Transfers[Capability.BODY_STRUCTURE] is TransferMode.NATIVE
    assert Transfers[Capability.SELECTIONS] is TransferMode.NATIVE
    assert Transfers[Capability.EXPRESSIONS] is TransferMode.NATIVE
    assert Transfers[Capability.MATERIALS] is TransferMode.NATIVE
    assert Transfers[Capability.CONFIGURATIONS] is TransferMode.NATIVE
    assert Transfers[Capability.BREP] is TransferMode.NATIVE
    assert Transfers[Capability.PARAMETRIC_HISTORY] is TransferMode.MIXED


# this definition exists because neutral xml objects must retain every native relationship
def VerifyWriteXml(PayloadData: bytes) -> None:
    with Zipfile.ZipFile(IoStream.BytesIO(PayloadData)) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        Declarations = {
            ItemValue.get("name", ""): ItemValue.get("type", "")
            for ItemValue in RootValue.findall("./Objects/Object")
        }
        assert Declarations["XY"] == "App::Plane"
        assert Declarations["Body"] == "App::DocumentObjectGroup"
        assert Declarations["Revolve_fallback"] == "Part::Feature"
        Formula = RootValue.find(
            "./ObjectData/Object[@name='Parameters']/Properties/Property[@name='cells']/Cells/Cell[@address='B2']"
        )
        assert Formula is not None
        assert Formula.get("content") == "=p_a * 2"
        Material = RootValue.find(
            "./ObjectData/Object[@name='Body']/Properties/Property[@name='MaterialId']/String"
        )
        assert Material is not None
        assert Material.get("value") == "material:steel"
        LinkValue = RootValue.find(
            "./ObjectData/Object[@name='Face_selection']/Properties/Property[@name='Selection']/LinkSubList/Link"
        )
        assert LinkValue is not None
        assert (LinkValue.get("obj"), LinkValue.get("sub")) == ("Boss1", "Face1")
        KindValue = RootValue.find(
            "./ObjectData/Object[@name='Revolve_fallback']/Properties/Property[@name='FeatureKind']/String"
        )
        assert KindValue is not None
        assert KindValue.get("value") == FeatureKind.REVOLUTION.value
        Config = RootValue.find(
            "./ObjectData/Object[@name='Default']/Properties/Property[@name='KitConfigurationId']/String"
        )
        assert Config is not None
        assert Config.get("value") == "config:default"
        Shape = RootValue.find(
            "./ObjectData/Object[@name='BRep']/Properties/Property[@name='Shape']/Part"
        )
        assert Shape is not None
        ShapeFile = Shape.get("file", "")
        assert ShapeFile
        assert IsStructurallyValidAscii(Archive.read(ShapeFile))


# this definition exists because neutral readback must preserve interchange and native projections
def VerifyReadback(PayloadData: bytes, DocValue: CadDocument, SelectionId: str) -> None:
    assert FreeCadAdapter().read(PayloadData) == DocValue
    Native = FreecadNativeModule.read_native_fcstd(PayloadData)
    assert len(Native.support_planes) == 1
    assert Native.bodies[0].material_id == "material:steel"
    assert Native.configurations[0].id == "config:default"
    assert any((ItemValue.id == SelectionId for ItemValue in Native.selections))


# this definition exists because focused behavior needs one stable owner
def TestNeutralAre() -> None:
    Source = NeutralDoc()
    FirstParam = Param("p:a", "A", ParamValue(2.0))
    SecondParam = Param(
        "p:b", "B", ParamValue(4.0), expression=Expression("p:a * 2", ("p:a",), "kit")
    )
    Selection = SelectionInfo(
        "selection:face",
        "Face selection",
        (SelectionPathElem("face", Source.feature_timeline[0].id, "Face1"),),
    )
    Fallback = FeatureStep(
        "feature:fallback",
        "Revolve fallback",
        FeatureKind.REVOLUTION,
        1,
        input_feature_ids=(Source.feature_timeline[0].id,),
        selection_ids=(Selection.id,),
    )
    DocValue = Replace(
        Source,
        parameters=(FirstParam, SecondParam),
        selections=(Selection,),
        feature_timeline=(*Source.feature_timeline, Fallback),
        bodies=(
            Replace(
                Source.bodies[0],
                final_feature_id=Fallback.id,
                material_id="material:steel",
            ),
        ),
        brep=TriangleBrep(),
    )
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    PayloadData = Output.getvalue()
    VerifyTransfers(Result)
    VerifyWriteXml(PayloadData)
    VerifyReadback(PayloadData, DocValue, Selection.id)


# this definition exists because focused behavior needs one stable owner
def TestNeutralAnd() -> None:
    Source = NeutralDoc()
    System = FeatureStep("system:history", "History carrier", FeatureKind.NATIVE, 0)
    RefValue = FeatureStep(
        "reference:sketch",
        "Sketch feature carrier",
        FeatureKind.REFERENCE,
        1,
        sketch_id=Source.sketches[0].id,
    )
    Extrusion = Replace(
        Source.feature_timeline[0], order=2, input_feature_ids=(RefValue.id,)
    )
    DocValue = Replace(Source, feature_timeline=(System, RefValue, Extrusion))
    DocValue.assert_valid()
    Output = IoStream.BytesIO()
    FreeCadAdapter().write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Declarations = {
        ItemValue.get("name", ""): ItemValue.get("type", "")
        for ItemValue in RootValue.findall("./Objects/Object")
    }
    assert Declarations["Boss1"] == "Part::Extrusion"
    assert Declarations["Body"] == "App::DocumentObjectGroup"
    assert "Boss1_Profile" not in Declarations
    Dependencies = RootValue.find("./Objects/ObjectDeps[@Name='Boss1']")
    assert Dependencies is not None
    assert [ItemValue.get("Name") for ItemValue in Dependencies.findall("./Dep")] == [
        "Sketch1",
        "Sketches",
    ]
    BaseValue = RootValue.find(
        "./ObjectData/Object[@name='Boss1']/Properties/Property[@name='Base']/Link"
    )
    assert BaseValue is not None
    assert BaseValue.get("value") == "Sketch1"


# this definition exists because focused behavior needs one stable owner
def TestQuantities() -> None:

    # this definition exists because focused behavior needs one stable owner
    def Quantities(RootValue: ET.Element) -> None:
        Properties = RootValue.find("./ObjectData/Object[@name='Pad']/Properties")
        assert Properties is not None
        Properties.extend(
            (
                NativeProp(
                    "Pressure", "App::PropertyPressure", "Float", {"value": "2.5"}
                ),
                NativeProp(
                    "Percent", "App::PropertyPercent", "Integer", {"value": "75"}
                ),
                NativeProp(
                    "Uuid",
                    "App::PropertyUUID",
                    "Uuid",
                    {"value": "7db2d7ea-e03e-4cd5-a4ac-9f1abc7ad12a"},
                ),
            )
        )
        Properties.set("Count", str(len(Properties.findall("./Property"))))

    DocValue = FreeCadAdapter().read(RewriteDocXml(NativePart(), Quantities))
    ByPath = {
        ItemValue.attributes.get("freecad_path"): ItemValue.value
        for ItemValue in DocValue.parameters
    }
    assert str(ByPath["Pressure"].kind) == "quantity"
    assert ByPath["Pressure"].unit == "kg/(mm*s^2)"
    assert ByPath["Pressure"].value == 2.5
    assert str(ByPath["Percent"].kind) == "quantity"
    assert ByPath["Percent"].unit == "%"
    assert ByPath["Percent"].value == 75
    assert str(ByPath["Uuid"].kind) == "string"
    assert ByPath["Uuid"].value == "7db2d7ea-e03e-4cd5-a4ac-9f1abc7ad12a"


# this definition exists because focused behavior needs one stable owner
def TestDatumPlane() -> None:

    # this definition exists because focused behavior needs one stable owner
    def DatumAnd(RootValue: ET.Element) -> None:
        DeclValue = RootValue.find("./Objects/Object[@name='XY_Plane']")
        assert DeclValue is not None
        DeclValue.set("type", "PartDesign::Plane")
        Attachment = RootValue.find(
            "./ObjectData/Object[@name='Sketch']/Properties/Property[@name='AttachmentSupport']"
        )
        assert Attachment is not None
        Attachment.set("name", "Support")
        Properties = RootValue.find("./ObjectData/Object[@name='Pad']/Properties")
        assert Properties is not None
        Selection = NativeProp(
            "Targets", "Vendor::DerivedLinkSelection", "LinkSub", {"value": "Body"}
        )
        XmlTree.SubElement(Selection[0], "Sub", {"value": "Face1"})
        Properties.append(Selection)
        Properties.set("Count", str(len(Properties.findall("./Property"))))

    DocValue = FreeCadAdapter().read(RewriteDocXml(NativePart(), DatumAnd))
    assert DocValue.sketches[0].support_plane_id == DocValue.support_planes[0].id
    assert (
        MetaMap(DocValue.support_planes[0].attributes["freecad"])["type_id"]
        == "PartDesign::Plane"
    )
    assert len(DocValue.selections) == 1
    assert DocValue.selections[0].path[0].entity_kind == "face"
    assert DocValue.selections[0].path[0].entity_id == "Body"
    assert DocValue.feature_timeline[-1].selection_ids == (DocValue.selections[0].id,)
    assert Capability.SELECTIONS in DocValue.capabilities


# this definition exists because focused behavior needs one stable owner
def TestCustomIsAs() -> None:

    # this definition exists because focused behavior needs one stable owner
    def CustomPlane(RootValue: ET.Element) -> None:
        DeclValue = RootValue.find("./Objects/Object[@name='XY_Plane']")
        assert DeclValue is not None
        DeclValue.set("type", "Vendor::FeaturePythonPlane")

    DocValue = FreeCadAdapter().read(RewriteDocXml(NativePart(), CustomPlane))
    assert len(DocValue.support_planes) == 1
    assert DocValue.sketches[0].support_plane_id == DocValue.support_planes[0].id
    assert (
        MetaMap(DocValue.support_planes[0].attributes["freecad"])["type_id"]
        == "Vendor::FeaturePythonPlane"
    )


# this definition exists because focused behavior needs one stable owner
def TestCustomDatum() -> None:
    assert "Vendor::FutureDatumPlane" not in SupportPlaneTypeIds
    Proxy = NativeProp(
        "Proxy",
        "App::PropertyPythonObject",
        "Python",
        {
            "value": "bnVsbA==",
            "encoded": "yes",
            "module": "VendorDatum",
            "class": "DatumPlane",
        },
    )
    Properties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Future datum"}),
        Proxy,
        NativePlacement(),
        NativePlacement("AttachmentOffset"),
        NativeProp(
            "MapMode", "App::PropertyString", "String", {"value": "Deactivated"}
        ),
    )
    DocValue = FreeCadAdapter().read(
        NativeArchive(
            (("FutureDatum", "Vendor::FutureDatumPlane", (), Properties),), {}
        )
    )
    assert len(DocValue.support_planes) == 1
    assert DocValue.support_planes[0].name == "Future datum"
    assert (
        MetaMap(DocValue.support_planes[0].attributes["freecad"])["type_id"]
        == "Vendor::FutureDatumPlane"
    )


# this definition exists because focused behavior needs one stable owner
def TestCustomAnd() -> None:
    Properties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Custom"}),
        NativeProp("Length", "App::PropertyLength", "Float", {"value": "12"}),
        NativeProp(
            "Result",
            "Vendor::DerivedShapeProperty",
            "Part",
            {"file": "Custom.Result.brp"},
        ),
    )
    DocValue = FreeCadAdapter().read(
        NativeArchive(
            (("Custom", "Vendor::ParametricFeature", (), Properties),),
            {
                "Custom.Result.brp": b"\nCASCADE Topology V1, (c) Matra-Datavision\ncustom\n"
            },
        )
    )
    assert len(DocValue.feature_timeline) == 1
    assert str(DocValue.feature_timeline[0].kind) == "native"
    assert (
        MetaMap(DocValue.feature_timeline[0].attributes["freecad"])["type_id"]
        == "Vendor::ParametricFeature"
    )
    ShapePayloads = tuple(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.role == PayloadRole.BREP
        )
    )
    assert len(ShapePayloads) == 1
    assert ShapePayloads[0].attributes["freecad_property"] == "Result"
    assert ShapePayloads[0].source_stream == "Custom.Result.brp"
    assert Capability.PARAMETRIC_HISTORY in DocValue.capabilities
    assert Capability.BREP in DocValue.capabilities


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("SchemaVersion", (3, 4))
def TestObjectGraph(SchemaVersion: int) -> None:

    # this callback exists because schema mutation needs a typed xml boundary
    def SchemaMut(RootValue: ET.Element) -> None:
        RootValue.set("SchemaVersion", str(SchemaVersion))

    Source = RewriteDocXml(NativePart(), SchemaMut)
    DocValue = FreeCadAdapter().read(Source)
    assert DocValue.validate() == ()
    assert DocValue.source.attributes["freecad_schema_version"] == str(SchemaVersion)


# this definition exists because focused behavior needs one stable owner
def TestSchemaTwoIs() -> None:

    # this definition exists because focused behavior needs one stable owner
    def SchemaTwoMut(RootValue: ET.Element) -> None:
        RootValue.set("SchemaVersion", "2")
        Objects = RootValue.find("./Objects")
        ObjectData = RootValue.find("./ObjectData")
        assert Objects is not None
        assert ObjectData is not None
        Declarations = Objects.findall("./Object")
        DataByName = {
            ItemValue.get("name", ""): ItemValue
            for ItemValue in ObjectData.findall("./Object")
        }
        Features = XmlTree.Element("Features", {"Count": str(len(Declarations))})
        FeatureData = XmlTree.Element("FeatureData", {"Count": str(len(Declarations))})
        for DeclValue in Declarations:
            NameValue = DeclValue.get("name", "")
            XmlTree.SubElement(
                Features,
                "Feature",
                {"type": DeclValue.get("type", ""), "name": NameValue},
            )
            SourceData = DataByName[NameValue]
            TargetData = XmlTree.SubElement(FeatureData, "Feature", {"name": NameValue})
            for Child in SourceData:
                TargetData.append(XmlTree.fromstring(XmlTree.tostring(Child)))
        RootValue.remove(Objects)
        RootValue.remove(ObjectData)
        RootValue.append(Features)
        RootValue.append(FeatureData)

    DocValue = FreeCadAdapter().read(RewriteDocXml(NativePart(), SchemaTwoMut))
    assert DocValue.validate() == ()
    assert DocValue.source.attributes["freecad_schema_version"] == "2"


# this definition exists because focused behavior needs one stable owner
def TestEmptyObject() -> None:
    RootValue = XmlTree.Element(
        "Document", {"SchemaVersion": "4", "ProgramVersion": "1.0", "FileVersion": "1"}
    )
    XmlTree.SubElement(RootValue, "Objects", {"Count": "0", "Dependencies": "1"})
    XmlTree.SubElement(RootValue, "ObjectData", {"Count": "0"})
    Source = IoStream.BytesIO()
    with Zipfile.ZipFile(Source, "w", Zipfile.ZIP_DEFLATED) as Archive:
        Archive.writestr(
            "Document.xml",
            XmlTree.tostring(RootValue, encoding="utf-8", xml_declaration=True),
        )
    DocValue = FreeCadAdapter().read(Source.getvalue())
    assert DocValue.validate() == ()
    assert [Payload.kind for Payload in DocValue.brep_payloads] == [
        "native_document",
        "native_document_binding",
    ]
    assert DocValue.capabilities == frozenset(
        {
            Capability.CONFIGURATIONS,
            Capability.NATIVE_PAYLOADS,
            Capability.PROVENANCE,
            Capability.ROUNDTRIP_METADATA,
        }
    )


# this definition exists because focused behavior needs one stable owner
def TestAllCurrent() -> None:
    Expected = tuple((Value.kind.value for Value in RuleTypes))

    # this definition exists because focused behavior needs one stable owner
    def Constraints(RootValue: ET.Element) -> None:
        RuleList = RootValue.find(
            "./ObjectData/Object[@name='Sketch']/Properties/Property[@name='Constraints']/ConstraintList"
        )
        assert RuleList is not None
        RuleList.clear()
        RuleList.set("count", str(len(RuleTypes)))
        for CodeValue in RuleKindByCode:
            XmlTree.SubElement(
                RuleList,
                "Constrain",
                {
                    "Name": f"Constraint{CodeValue}",
                    "Type": str(CodeValue),
                    "Value": "1.25",
                    "IsDriving": "1",
                    "IsActive": "1",
                    "ElementIds": "0 1 2 3",
                    "ElementPositions": "1 2 3 1",
                },
            )

    DocValue = FreeCadAdapter().read(RewriteDocXml(NativePart(), Constraints))
    Sketch = DocValue.sketches[0]
    assert tuple((str(ItemValue.kind) for ItemValue in Sketch.constraints)) == Expected
    assert all((len(ItemValue.references) == 4 for ItemValue in Sketch.constraints))
    assert len(Sketch.parameter_ids) == 8
    assert Sketch.entities[0].fixed


# this definition exists because unavailable geometry diagnostics have one focused xml contract
def VerifyCarriers(RootValue: ET.Element, Kinds: tuple[GeomKind, ...]) -> None:
    SketchObject = next(
        (
            ItemValue
            for ItemValue in RootValue.findall("./ObjectData/Object")
            if ItemValue.find("./Properties/Property[@name='Geometry']") is not None
        )
    )
    GeomList = SketchObject.find("./Properties/Property[@name='Geometry']/GeometryList")
    assert GeomList is not None
    assert GeomList.get("count") == "0"
    assert GeomList.findall("./Geometry") == []
    assert GeomList.findall(".//GeomPoint") == []
    DiagnosticsNode = SketchObject.find(
        "./Properties/Property[@name='KitSketchDiagnosticsJSON']/String"
    )
    assert DiagnosticsNode is not None
    Diagnostics = JsonValue.loads(DiagnosticsNode.get("value", ""))
    assert {ItemValue["kind"] for ItemValue in Diagnostics} == {
        KindValue.value for KindValue in Kinds
    }
    assert {ItemValue["mode"] for ItemValue in Diagnostics} == {"carrier_only"}
    SourceNode = SketchObject.find(
        "./Properties/Property[@name='SourceSketchJSON']/String"
    )
    assert SourceNode is not None
    SourceSketch = JsonValue.loads(SourceNode.get("value", ""))
    assert len(SourceSketch["entities"]["$tuple"]) == len(Kinds)


# this definition exists because focused behavior needs one stable owner
def TestUnavailable() -> None:
    Source = NeutralDoc()
    Kinds = (
        GeomKind.ARC_ELLIPSE,
        GeomKind.HYPERBOLA,
        GeomKind.ARC_HYPERBOLA,
        GeomKind.PARABOLA,
        GeomKind.ARC_PARABOLA,
        GeomKind.OFFSET,
        GeomKind.TRIMMED,
        GeomKind.NATIVE,
    )
    Entities = tuple(
        (
            SketchEntity(
                f"carrier:{KindValue.value}",
                KindValue,
                NativeGeom(
                    "catia.catpart",
                    f"CATIA::{KindValue.value}",
                    {"token": KindValue.value},
                ),
            )
            for KindValue in Kinds
        )
    )
    Sketch = Replace(Source.sketches[0], entities=Entities, constraints=())
    DocValue = Replace(Source, sketches=(Sketch,))
    DocValue.assert_valid()
    Output = IoStream.BytesIO()
    Adapter = FreeCadAdapter()
    Result = Adapter.write(DocValue, Output)
    Transfers = {Transfer.capability: Transfer for Transfer in Result.transfers}
    assert Transfers[Capability.EDITABLE_SKETCHES].mode == TransferMode.MIXED
    assert (
        Transfers[Capability.EDITABLE_SKETCHES].carrier_reason
        is CarrierReason.SOURCE_OPAQUE
    )
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    VerifyCarriers(RootValue, Kinds)
    assert Adapter.read(Output.getvalue()) == DocValue


# this definition exists because focused behavior needs one stable owner
def TestNeutralTrip() -> None:
    Source = NeutralDoc()
    AxisValue = VectorTwo(0.6, 0.8)
    Values = (
        (
            GeomKind.ELLIPSE,
            EllipseGeom(VectorTwo(1.0, 2.0), AxisValue, 8.0, 3.0),
            "Part::GeomEllipse",
        ),
        (
            GeomKind.ARC_ELLIPSE,
            ArcEllipseGeom(VectorTwo(2.0, 3.0), AxisValue, 9.0, 4.0, -0.5, 1.25),
            "Part::GeomArcOfEllipse",
        ),
        (
            GeomKind.ARC_HYPERBOLA,
            ArcHyperbolaGeom(VectorTwo(4.0, 5.0), AxisValue, 11.0, 6.0, -0.75, 1.5),
            "Part::GeomArcOfHyperbola",
        ),
        (
            GeomKind.ARC_PARABOLA,
            ArcParabolaGeom(VectorTwo(6.0, 7.0), AxisValue, 8.0, -1.0, 2.0),
            "Part::GeomArcOfParabola",
        ),
    )
    Entities = tuple(
        (
            SketchEntity(f"conic:{Index}", Value[0], Value[1])
            for Index, Value in enumerate(Values)
        )
    )
    Sketch = Replace(
        Source.sketches[0],
        entities=Entities,
        constraints=(),
        closed_profile_entity_ids=(),
    )
    DocValue = Replace(
        Source,
        sketches=(Sketch,),
        feature_timeline=(Replace(Source.feature_timeline[0], suppressed=True),),
    )
    DocValue.assert_valid()
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    Transfers = {ItemValue.capability: ItemValue.mode for ItemValue in Result.transfers}
    assert Transfers[Capability.EDITABLE_SKETCHES] is TransferMode.NATIVE
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    GeomNodes = RootValue.findall(".//Property[@name='Geometry']/GeometryList/Geometry")
    assert [ItemValue.get("type") for ItemValue in GeomNodes] == [
        Value[2] for Value in Values
    ]
    Native = FreecadNativeModule.read_native_fcstd(Output.getvalue())
    Restored = Native.sketches[0].entities
    assert [ItemValue.kind for ItemValue in Restored] == [Value[0] for Value in Values]
    for ItemValue, SourceValue in zip(Restored, Values, strict=True):
        Expected = SourceValue[1]
        Actual = ItemValue.geometry
        assert type(Actual) is type(Expected)
        assert isinstance(
            Actual,
            (
                EllipseGeom,
                ArcEllipseGeom,
                HyperbolaGeom,
                ArcHyperbolaGeom,
                ParabolaGeom,
                ArcParabolaGeom,
            ),
        )
        assert isinstance(
            Expected,
            (
                EllipseGeom,
                ArcEllipseGeom,
                HyperbolaGeom,
                ArcHyperbolaGeom,
                ParabolaGeom,
                ArcParabolaGeom,
            ),
        )
        assert (Actual.center.x, Actual.center.y) == Pytest.approx(
            (Expected.center.x, Expected.center.y)
        )
        ExpectedAxis = getattr(Expected, "major_axis", getattr(Expected, "axis", None))
        ActualAxis = getattr(Actual, "major_axis", getattr(Actual, "axis", None))
        assert ExpectedAxis is not None
        assert ActualAxis is not None
        assert (ActualAxis.x, ActualAxis.y) == Pytest.approx(
            (ExpectedAxis.x, ExpectedAxis.y)
        )
        for NameValue in (
            "major_radius",
            "minor_radius",
            "focal_length",
            "start_angle",
            "end_angle",
        ):
            if hasattr(Expected, NameValue):
                assert getattr(Actual, NameValue) == Pytest.approx(
                    getattr(Expected, NameValue)
                )


# this definition exists because focused behavior needs one stable owner
def TestUnbounded() -> None:
    Source = NeutralDoc()
    AxisValue = VectorTwo(0.6, 0.8)
    Values = (
        (GeomKind.HYPERBOLA, HyperbolaGeom(VectorTwo(3.0, 4.0), AxisValue, 10.0, 5.0)),
        (GeomKind.PARABOLA, ParabolaGeom(VectorTwo(5.0, 6.0), AxisValue, 7.0)),
    )
    Entities = tuple(
        (
            SketchEntity(f"unbounded:{Index}", KindValue, GeomValue)
            for Index, (KindValue, GeomValue) in enumerate(Values)
        )
    )
    Sketch = Replace(
        Source.sketches[0],
        entities=Entities,
        constraints=(),
        closed_profile_entity_ids=(),
    )
    DocValue = Replace(
        Source,
        sketches=(Sketch,),
        feature_timeline=(Replace(Source.feature_timeline[0], suppressed=True),),
    )
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    Transfers = {ItemValue.capability: ItemValue for ItemValue in Result.transfers}
    Transfer = Transfers[Capability.EDITABLE_SKETCHES]
    assert Transfer.mode is TransferMode.MIXED
    assert Transfer.carrier_reason is CarrierReason.WRITER_UNIMPLEMENTED
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    GeomNodes = RootValue.findall(".//Property[@name='Geometry']/GeometryList/Geometry")
    assert GeomNodes == []
    assert FreeCadAdapter().read(Output.getvalue()) == DocValue


# this definition exists because focused behavior needs one stable owner
def TestGeomPayload() -> None:
    Source = NeutralDoc()
    Kinds = (
        (GeomKind.ARC_ELLIPSE, "Part::GeomArcOfEllipse", "ArcOfEllipse"),
        (GeomKind.HYPERBOLA, "Part::GeomHyperbola", "Hyperbola"),
        (GeomKind.ARC_HYPERBOLA, "Part::GeomArcOfHyperbola", "ArcOfHyperbola"),
        (GeomKind.PARABOLA, "Part::GeomParabola", "Parabola"),
        (GeomKind.ARC_PARABOLA, "Part::GeomArcOfParabola", "ArcOfParabola"),
        (GeomKind.OFFSET, "Part::GeomOffsetCurve", "OffsetCurve"),
        (GeomKind.TRIMMED, "Part::GeomTrimmedCurve", "TrimmedCurve"),
    )
    Entities = tuple(
        (
            SketchEntity(
                f"native:{KindValue.value}",
                KindValue,
                NativeGeom(
                    "freecad.fcstd",
                    TypeId,
                    {
                        "tag": "Geometry",
                        "attributes": {
                            "type": TypeId,
                            "id": str(Index + 1),
                            "migrated": "1",
                        },
                        "children": [
                            {"tag": TagValue, "attributes": {"Token": KindValue.value}},
                            {"tag": "Construction", "attributes": {"value": "0"}},
                        ],
                    },
                ),
            )
            for Index, (KindValue, TypeId, TagValue) in enumerate(Kinds)
        )
    )
    DocValue = Replace(
        Source,
        sketches=(Replace(Source.sketches[0], entities=Entities, constraints=()),),
    )
    Output = IoStream.BytesIO()
    Adapter = FreeCadAdapter()
    Result = Adapter.write(DocValue, Output)
    Transfers = {Transfer.capability: Transfer.mode for Transfer in Result.transfers}
    assert Transfers[Capability.EDITABLE_SKETCHES] == TransferMode.NATIVE
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    SketchObject = next(
        (
            ItemValue
            for ItemValue in RootValue.findall("./ObjectData/Object")
            if ItemValue.find("./Properties/Property[@name='Geometry']") is not None
        )
    )
    GeomNodes = SketchObject.findall(
        "./Properties/Property[@name='Geometry']/GeometryList/Geometry"
    )
    assert [ItemValue.get("type") for ItemValue in GeomNodes] == [
        Value[1] for Value in Kinds
    ]
    assert [list(ItemValue)[0].tag for ItemValue in GeomNodes] == [
        Value[2] for Value in Kinds
    ]
    assert [list(ItemValue)[0].get("Token") for ItemValue in GeomNodes] == [
        Value[0].value for Value in Kinds
    ]
    assert (
        SketchObject.find("./Properties/Property[@name='KitSketchDiagnosticsJSON']")
        is None
    )
    assert SketchObject.findall(".//GeomPoint") == []
    assert Adapter.read(Output.getvalue()) == DocValue


# this definition exists because carrier and composed constraints share one diagnostic contract
def VerifyRuleXml(RootValue: ET.Element, Midpoint: SketchRule) -> None:
    SketchObject = next(
        (
            ItemValue
            for ItemValue in RootValue.findall("./ObjectData/Object")
            if ItemValue.find("./Properties/Property[@name='Constraints']") is not None
        )
    )
    Encoded = SketchObject.findall(
        "./Properties/Property[@name='Constraints']/ConstraintList/Constrain"
    )
    assert len(Encoded) == 1
    assert Encoded[0].get("Type") == "14"
    assert Encoded[0].get("ElementIds") == "0 0 1"
    assert Encoded[0].get("ElementPositions") == "1 2 1"
    DiagnosticsNode = SketchObject.find(
        "./Properties/Property[@name='KitSketchDiagnosticsJSON']/String"
    )
    assert DiagnosticsNode is not None
    Diagnostics = JsonValue.loads(DiagnosticsNode.get("value", ""))
    CarrierOnly = [
        ItemValue for ItemValue in Diagnostics if ItemValue["mode"] == "carrier_only"
    ]
    assert {ItemValue["kind"] for ItemValue in CarrierOnly} == {
        KindValue.value for KindValue in RuleKind
    }
    Composition = [
        ItemValue
        for ItemValue in Diagnostics
        if ItemValue["mode"] == "native_composition"
    ]
    assert Composition == [
        {
            "code": "freecad.sketch_constraint_composed",
            "constraint_id": Midpoint.id,
            "kind": RuleKind.MIDPOINT.value,
            "mode": "native_composition",
            "native_kind": "Symmetric",
            "reason": "encoded as symmetry between a line's endpoints and the referenced point",
            "severity": "info",
        }
    ]
    SourceNode = SketchObject.find(
        "./Properties/Property[@name='SourceSketchJSON']/String"
    )
    assert SourceNode is not None
    SourceSketch = JsonValue.loads(SourceNode.get("value", ""))
    assert len(SourceSketch["constraints"]["$tuple"]) == len(RuleKind) + 1


# this definition exists because focused behavior needs one stable owner
def TestRuleCarrier() -> None:
    Source = NeutralDoc()
    LineValue = Source.sketches[0].entities[0]
    Point = SketchEntity(
        "sketch:1:point:1", GeomKind.POINT, PointGeom(VectorTwo(5.0, 0.0))
    )
    CarrierConstraints = tuple(
        (
            SketchRule(f"carrier:{KindValue.value}", KindValue, ())
            for KindValue in RuleKind
        )
    )
    Midpoint = SketchRule(
        "midpoint:sound", RuleKind.MIDPOINT, (RuleRef(LineValue.id), RuleRef(Point.id))
    )
    Sketch = Replace(
        Source.sketches[0],
        entities=(LineValue, Point),
        constraints=(*CarrierConstraints, Midpoint),
    )
    DocValue = Replace(Source, sketches=(Sketch,))
    DocValue.assert_valid()
    Output = IoStream.BytesIO()
    Adapter = FreeCadAdapter()
    Result = Adapter.write(DocValue, Output)
    Transfers = {Transfer.capability: Transfer.mode for Transfer in Result.transfers}
    assert Transfers[Capability.EDITABLE_SKETCHES] == TransferMode.MIXED
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    VerifyRuleXml(RootValue, Midpoint)
    assert Adapter.read(Output.getvalue()) == DocValue


# this definition exists because focused behavior needs one stable owner
def TestNeutralUses() -> None:
    Source = NeutralDoc()
    First = SketchEntity(
        "sketch:1:point:1", GeomKind.POINT, PointGeom(VectorTwo(0.0, 0.0))
    )
    Second = SketchEntity(
        "sketch:1:point:2", GeomKind.POINT, PointGeom(VectorTwo(10.0, 0.0))
    )
    Distance = SketchRule(
        "distance:points",
        RuleKind.DISTANCE,
        (RuleRef(First.id), RuleRef(Second.id)),
        attributes={"Value": 10.0},
    )
    Sketch = Replace(
        Source.sketches[0], entities=(First, Second), constraints=(Distance,)
    )
    DocValue = Replace(Source, sketches=(Sketch,))
    Output = IoStream.BytesIO()
    FreeCadAdapter().write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Encoded = RootValue.find(
        ".//Property[@name='Constraints']/ConstraintList/Constrain"
    )
    assert Encoded is not None
    assert Encoded.get("Type") == "6"
    assert Encoded.get("FirstPos") == "1"
    assert Encoded.get("SecondPos") == "1"
    assert Encoded.get("ElementPositions") == "1 1 0"


# this definition exists because focused behavior needs one stable owner
def TestRadiusRule() -> None:
    Source = NeutralDoc()
    Circle = SketchEntity(
        "sketch:1:circle:1", GeomKind.CIRCLE, CircleGeom(VectorTwo(0.0, 0.0), 8.0)
    )
    Radius = SketchRule(
        "radius:native",
        RuleKind.RADIUS,
        (RuleRef(Circle.id),),
        attributes={"native_value": 8.0},
    )
    Sketch = Replace(
        Source.sketches[0],
        entities=(Circle,),
        constraints=(Radius,),
        closed_profile_entity_ids=((Circle.id,),),
    )
    Output = IoStream.BytesIO()
    FreeCadAdapter().write(Replace(Source, sketches=(Sketch,)), Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Encoded = RootValue.find(
        ".//Property[@name='Constraints']/ConstraintList/Constrain"
    )
    assert Encoded is not None
    assert Encoded.get("Type") == str(RuleCodeByKind["radius"])
    assert float(Encoded.get("Value", "")) == 8.0


# this definition exists because focused behavior needs one stable owner
def TestSolidworksB() -> None:
    Source = NeutralDoc()
    DocValue = Replace(
        Source, source=Replace(Source.source, format_id="solidworks.sldprt")
    )
    Output = IoStream.BytesIO()
    FreeCadAdapter().write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    DeclValue = RootValue.find("./Objects/Object[@name='Boss1']")
    assert DeclValue is not None
    assert DeclValue.get("type") == "Part::Feature"
    Properties = RootValue.find("./ObjectData/Object[@name='Boss1']/Properties")
    assert Properties is not None
    Executable = Properties.find("./Property[@name='NativeExecutable']/Bool")
    Reason = Properties.find("./Property[@name='NativeExecutionReason']/String")
    assert Executable is not None and Executable.get("value") == "false"
    assert Reason is not None and Reason.get("value") == "no_native_closed_profile"
    assert FreeCadAdapter().read(Output.getvalue()) == DocValue


# this definition exists because focused behavior needs one stable owner
def TestSolidworks() -> None:
    Source = NeutralDoc()
    First = SketchEntity(
        "sketch:1:circle:1", GeomKind.CIRCLE, CircleGeom(VectorTwo(0.0, 0.0), 10.0)
    )
    Second = SketchEntity(
        "sketch:1:circle:2", GeomKind.CIRCLE, CircleGeom(VectorTwo(15.0, 0.0), 10.0)
    )
    Sketch = Replace(
        Source.sketches[0],
        entities=(First, Second),
        closed_profile_entity_ids=((First.id,), (Second.id,)),
    )
    DocValue = Replace(
        Source,
        source=Replace(Source.source, format_id="solidworks.sldprt"),
        sketches=(Sketch,),
    )
    Output = IoStream.BytesIO()
    FreeCadAdapter().write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    DeclValue = RootValue.find("./Objects/Object[@name='Boss1']")
    Reason = RootValue.find(
        "./ObjectData/Object[@name='Boss1']/Properties/Property[@name='NativeExecutionReason']/String"
    )
    assert DeclValue is not None and DeclValue.get("type") == "Part::Feature"
    assert Reason is not None
    assert Reason.get("value") == "profile_topology_not_statically_sound"
    assert FreeCadAdapter().read(Output.getvalue()) == DocValue


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("TypeId", "TypeCode", "Expected"),
    (
        ("PartDesign::Pad", 0, "blind"),
        ("PartDesign::Pad", 1, "up_to_last"),
        ("PartDesign::Pad", 2, "up_to_first"),
        ("PartDesign::Pad", 3, "up_to_face"),
        ("PartDesign::Pad", 4, "two_lengths"),
        ("PartDesign::Pad", 5, "up_to_shape"),
        ("PartDesign::Pocket", 0, "blind"),
        ("PartDesign::Pocket", 1, "through_all"),
        ("PartDesign::Pocket", 2, "up_to_first"),
        ("PartDesign::Pocket", 3, "up_to_face"),
        ("PartDesign::Pocket", 4, "two_lengths"),
        ("PartDesign::Pocket", 5, "up_to_shape"),
    ),
)
def TestCurrentPad(TypeId: str, TypeCode: int, Expected: str) -> None:
    Properties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "X"}),
        NativeProp("Length", "App::PropertyLength", "Float", {"value": "8"}),
        NativeProp("Length2", "App::PropertyLength", "Float", {"value": "3"}),
        NativeProp(
            "Type", "App::PropertyEnumeration", "Integer", {"value": str(TypeCode)}
        ),
        NativeProp("Type2", "App::PropertyEnumeration", "Integer", {"value": "5"}),
        NativeProp("SideType", "App::PropertyEnumeration", "Integer", {"value": "1"}),
        NativeProp("Offset", "App::PropertyLength", "Float", {"value": "2"}),
        NativeProp("Offset2", "App::PropertyLength", "Float", {"value": "4"}),
        NativeProp("TaperAngle", "App::PropertyAngle", "Float", {"value": "5"}),
        NativeProp("TaperAngle2", "App::PropertyAngle", "Float", {"value": "6"}),
    )
    DocValue = FreeCadAdapter().read(
        NativeArchive((("Extrude", TypeId, (), Properties),), {})
    )
    Definition = DocValue.feature_timeline[0].definition
    assert isinstance(Definition, ExtrusionFeature)
    assert str(Definition.end_condition) == Expected
    assert str(Definition.second_end_condition) == "up_to_shape"
    assert Definition.second_length is not None
    assert Definition.second_length.value == 3.0
    assert Definition.offset is not None
    assert Definition.offset.value == 2.0
    assert Definition.second_offset is not None
    assert Definition.second_offset.value == 4.0
    assert Definition.second_draft_angle is not None
    assert Definition.second_draft_angle.value == 6.0


# this definition exists because focused behavior needs one stable owner
def TestARevolution() -> None:
    Revolution = (
        "Revolution",
        "PartDesign::Revolution",
        (),
        (
            NativeProp(
                "Label", "App::PropertyString", "String", {"value": "Revolution"}
            ),
            NativeProp("Angle", "App::PropertyAngle", "Float", {"value": "360.0"}),
        ),
    )
    Groove = (
        "Groove",
        "PartDesign::Groove",
        ("Revolution",),
        (
            NativeProp("Label", "App::PropertyString", "String", {"value": "Groove"}),
            NativeProp("Angle", "App::PropertyAngle", "Float", {"value": "360.0"}),
        ),
    )
    DocValue = FreeCadAdapter().read(NativeArchive((Revolution, Groove), {}))
    Steps = {ItemValue.name: ItemValue for ItemValue in DocValue.feature_timeline}
    assert Steps["Revolution"].kind == FeatureKind.REVOLUTION
    assert Steps["Revolution"].operation == BoolOperation.CREATE
    assert Steps["Groove"].kind == FeatureKind.REVOLUTION
    assert Steps["Groove"].operation == BoolOperation.CUT


# this definition exists because focused behavior needs one stable owner
def TestFeatureAnd() -> None:
    Properties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Revolution"}),
        NativeProp("Angle", "App::PropertyAngle", "Float", {"value": "45.0"}),
        NativeProp(
            "ReferenceAxis", "App::PropertyString", "String", {"value": "V_Axis"}
        ),
    )
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(
        NativeArchive((("Revolution", "PartDesign::Revolution", (), Properties),), {})
    )
    Feature = DocValue.feature_timeline[0]
    assert Feature.kind == FeatureKind.REVOLUTION
    assert isinstance(Feature.definition, NativeFeatureDefinition)
    assert Feature.definition.format_id == "freecad.fcstd"
    assert Feature.definition.type_id == "PartDesign::Revolution"
    ObjectData = MetaMap(Feature.definition.object_data)
    NativeProperties = MetaMap(ObjectData["properties"])
    Angle = MetaMap(NativeProperties["Angle"])
    AngleValue = MetaMap(MetaSeq(Angle["children"])[0])
    AngleAttributes = MetaMap(AngleValue["attributes"])
    AngleAttributes["value"] = "37.5"
    AngleValue["attributes"] = AngleAttributes
    Angle["children"] = [AngleValue]
    NativeProperties["Angle"] = Angle
    ObjectData["properties"] = NativeProperties
    Edited = Replace(
        DocValue,
        feature_timeline=(
            Replace(
                Feature, definition=Replace(Feature.definition, object_data=ObjectData)
            ),
        ),
    )
    Output = IoStream.BytesIO()
    Adapter.write(Edited, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    AngleNode = RootValue.find(
        "./ObjectData/Object[@name='Revolution']/Properties/Property[@name='Angle']/Float"
    )
    assert AngleNode is not None
    assert AngleNode.get("value") == "37.5"


# this definition exists because focused behavior needs one stable owner
def TestNonFeature() -> None:
    Source = NeutralDoc()
    Previous = Source.feature_timeline[-1]
    Feature = Replace(
        Previous,
        id="feature:native-hole",
        name="Native Hole",
        kind=FeatureKind.HOLE,
        order=Previous.order + 1,
        input_feature_ids=(Previous.id,),
        sketch_id=None,
        parameter_ids=(),
        definition=NativeFeatureDefinition(
            "freecad.fcstd",
            "PartDesign::Hole",
            {"diameter": 6.5, "thread": "M6", "depth": 12.0},
        ),
        selection_ids=(),
    )
    DocValue = Replace(
        Source,
        feature_timeline=Source.feature_timeline + (Feature,),
        bodies=tuple(
            (
                Replace(BodyValue, final_feature_id=Feature.id)
                for BodyValue in Source.bodies
            )
        ),
    )
    DocValue.assert_valid()
    Output = IoStream.BytesIO()
    Adapter = FreeCadAdapter()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    FeatureObject = next(
        (
            NodeValue
            for NodeValue in RootValue.findall("./ObjectData/Object")
            if (KitId := NodeValue.find("./Properties/Property[@name='KitId']/String"))
            is not None
            and KitId.get("value") == Feature.id
        )
    )
    Values = {
        NodeValue.get("name"): StringValue.get("value", "")
        for NodeValue in FeatureObject.findall("./Properties/Property")
        if (StringValue := NodeValue.find("./String")) is not None
    }
    assert Values["KitRole"] == "feature-data"
    assert Values["NativeTypeId"] == "PartDesign::Hole"
    assert '"diameter":6.5' in Values["NativeDefinitionJSON"]
    Restored = Adapter.read(Output.getvalue())
    assert Restored.feature(Feature.id).definition == Feature.definition


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("Source", "ExpectedSource"),
    (
        (NativeMesh(), "Derived.MeshKernel.bms"),
        (NativeMesh(">"), "Derived.MeshKernel.bms"),
        (NativeMesh(Inline=True), ""),
    ),
    ids=("derived_little_endian", "derived_big_endian", "inline"),
)
def TestCurrentMesh(Source: bytes, ExpectedSource: str) -> None:
    DocValue = FreeCadAdapter().read(Source)
    assert DocValue.validate() == ()
    assert len(DocValue.meshes) == 1
    MeshValue = DocValue.meshes[0]
    assert tuple(
        ((ItemValue.x, ItemValue.y, ItemValue.z) for ItemValue in MeshValue.vertices)
    ) == ((-2.0, 3.0, 1.0), (5.0, -7.0, 4.0), (1.0, 2.0, -6.0))
    assert MeshValue.triangles == ((0, 1, 2),)
    assert MeshValue.attributes["source_stream"] == ExpectedSource
    assert Capability.TESSELLATION in DocValue.capabilities


# this definition exists because focused behavior needs one stable owner
def TestMeshKernel() -> None:
    Source = NeutralDoc()
    MeshValue = MeshRecord(
        "mesh:1",
        "Mesh",
        (
            VectorThree(-2.0, 3.0, 1.0),
            VectorThree(5.0, -7.0, 4.0),
            VectorThree(1.0, 2.0, -6.0),
        ),
        ((0, 1, 2),),
    )
    Output = IoStream.BytesIO()
    FreeCadAdapter().write(
        Replace(
            Source,
            meshes=(MeshValue,),
            capabilities=Source.capabilities | {Capability.TESSELLATION},
        ),
        Output,
    )
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        NameValue = next(
            (
                ItemValue
                for ItemValue in Archive.namelist()
                if ItemValue.endswith(".MeshKernel.bms")
            )
        )
        DataValue = Archive.read(NameValue)
    assert Struct.unpack_from("<IIIIII", DataValue, 272 + 36) == (
        0,
        1,
        2,
        4294967295,
        4294967295,
        4294967295,
    )
    assert Struct.unpack_from("<ffffff", DataValue, len(DataValue) - 24) == (
        -2.0,
        5.0,
        -7.0,
        3.0,
        -6.0,
        4.0,
    )


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("JointIndex", "Expected"),
    tuple(
        ((Index, Value.kind.value) for Index, Value in enumerate(JointTypeDefinitions))
    ),
)
def TestCurrentAsm(JointIndex: int, Expected: str) -> None:

    # this definition exists because focused behavior needs one stable owner
    def JointType(RootValue: ET.Element) -> None:
        PropElem = RootValue.find(
            "./ObjectData/Object[@name='Revolute']/Properties/Property[@name='JointType']"
        )
        assert PropElem is not None
        Selected = PropElem.find("./Integer")
        assert Selected is not None
        Selected.set("value", str(JointIndex))
        EnumList = PropElem.find("./CustomEnumList")
        assert EnumList is not None
        EnumList.clear()
        Choices = JointTypes
        EnumList.set("count", str(len(Choices)))
        for Choice in Choices:
            XmlTree.SubElement(EnumList, "Enum", {"value": Choice})

    DocValue = FreeCadAdapter().read(RewriteDocXml(NativeAsm(), JointType))
    assert DocValue.assembly is not None
    assert str(DocValue.assembly.mates[0].kind) == Expected


# this definition exists because gear joint fixtures need one reusable xml mutation
def GearActionMut(RootValue: ET.Element) -> None:
    Properties = RootValue.find("./ObjectData/Object[@name='Revolute']/Properties")
    assert Properties is not None
    JointType = Properties.find("./Property[@name='JointType']")
    assert JointType is not None
    Selected = JointType.find("./Integer")
    assert Selected is not None
    Selected.set("value", "11")
    EnumList = JointType.find("./CustomEnumList")
    assert EnumList is not None
    EnumList.clear()
    Choices = JointTypes
    EnumList.set("count", str(len(Choices)))
    for Choice in Choices:
        XmlTree.SubElement(EnumList, "Enum", {"value": Choice})
    RefValue = Properties.find("./Property[@name='Reference1']/XLink")
    assert RefValue is not None
    for Child in list(RefValue.findall("./Sub")):
        RefValue.remove(Child)
    XmlTree.SubElement(RefValue, "Sub", {"value": ""})
    Properties.extend(
        (
            NativeProp("Distance", "App::PropertyLength", "Float", {"value": "4"}),
            NativeProp("Distance2", "App::PropertyLength", "Float", {"value": "2"}),
            NativeProp("LengthMin", "App::PropertyLength", "Float", {"value": "1"}),
            NativeProp("AngleMax", "App::PropertyAngle", "Float", {"value": "35"}),
            NativeProp(
                "EnableLengthMin", "App::PropertyBool", "Bool", {"value": "true"}
            ),
            NativeProp(
                "EnableAngleMax", "App::PropertyBool", "Bool", {"value": "true"}
            ),
        )
    )
    Properties.set("Count", str(len(Properties.findall("./Property"))))


# this definition exists because focused behavior needs one stable owner
def TestJointValues() -> None:

    # this definition exists because focused behavior needs one stable owner
    def GearAction(RootValue: ET.Element) -> None:
        GearActionMut(RootValue)

    DocValue = FreeCadAdapter().read(RewriteDocXml(NativeAsm(), GearAction))
    assert DocValue.assembly is not None
    MateValue = DocValue.assembly.mates[0]
    assert str(MateValue.kind) == "gear"
    assert MateValue.value is not None
    assert MateValue.value.value == 4.0
    ByIdValue = {ItemValue.id: ItemValue for ItemValue in DocValue.parameters}
    assert {
        ByIdValue[ParamId].attributes["freecad_path"]
        for ParamId in MateValue.parameter_ids
    } == {"Distance", "Distance2", "LengthMin", "AngleMax"}
    Entities = {
        ItemValue.id: ItemValue for ItemValue in DocValue.assembly.mate_entities
    }
    First = Entities[MateValue.entity_ids[0]]
    assert First.source_entity_id == ""
    assert First.attributes["freecad_subelement"] == ""


# this definition exists because focused behavior needs one stable owner
def TestExplicit() -> None:

    # this definition exists because focused behavior needs one stable owner
    def Carrier(RootValue: ET.Element) -> None:
        Properties = RootValue.find("./ObjectData/Object[@name='Revolute']/Properties")
        assert Properties is not None
        for PropName in ("JointType", "Proxy", "Suppressed"):
            Value = Properties.find(f"./Property[@name='{PropName}']")
            assert Value is not None
            Properties.remove(Value)
        Properties.extend(
            (
                NativeProp(
                    "KitMateCarrier", "App::PropertyBool", "Bool", {"value": "true"}
                ),
                NativeProp(
                    "MateType", "App::PropertyString", "String", {"value": "tangent"}
                ),
                NativeProp(
                    "Alignment",
                    "App::PropertyString",
                    "String",
                    {"value": "anti_aligned"},
                ),
                NativeProp(
                    "SourceSuppressed", "App::PropertyBool", "Bool", {"value": "true"}
                ),
                NativeProp("Driving", "App::PropertyBool", "Bool", {"value": "false"}),
            )
        )
        Properties.set("Count", str(len(Properties.findall("./Property"))))

    DocValue = FreeCadAdapter().read(RewriteDocXml(NativeAsm(), Carrier))
    assert DocValue.assembly is not None
    MateValue = DocValue.assembly.mates[0]
    assert str(MateValue.kind) == "tangent"
    assert str(MateValue.alignment) == "anti_aligned"
    assert MateValue.suppressed
    assert not MateValue.driving


# this definition exists because focused behavior needs one stable owner
def TestStrictTo(TmpPath: FilePath) -> None:
    Output = TmpPath / "blocked.FCStd"
    with Pytest.raises(AppUsabilityError) as Captured:
        Convert(KSample, Output, allow_carrier=False)
    assert "opaque_source_data" in Captured.value.issues
    assert not Output.exists()


# this definition exists because focused behavior needs one stable owner
def TestDirectFcstd(TmpPath: FilePath) -> None:
    Output = TmpPath / "example.FCStd"
    Result = Convert(KSample, Output, allow_carrier=True)
    Restored = OpenDoc(Output)
    assert Restored == Result.document
    assert Restored.validate() == ()
    assert [Payload.sha256 for Payload in Restored.brep_payloads] == [
        "8c57db227621a15a0a429cdd65dbe3f374e2c1145ef2f3edc3a25b745513bf3d",
        "3f3e3efbfbee0f41bda187579547881126cbf48101f006eecd759f491fc87ac6",
        "59d5eef7feb40d7a2ce52e20e50e14ca8eedaa1a1671b33a13fdc43720311cb7",
    ]
    with Zipfile.ZipFile(Output) as Archive:
        Archive.testzip()
        Names = set(Archive.namelist())
        assert "Document.xml" in Names
        assert "interchange/document.json" in Names
        assert "Fillet1.Edges" not in Names
        assert (
            len(
                Names
                & {
                    "interchange/native/sldprt_brep_0.x_b",
                    "interchange/native/sldprt_brep_1.x_b",
                    "interchange/native/sldprt_brep_2.x_b",
                }
            )
            == 3
        )
        for Payload in Restored.brep_payloads:
            Entry = f"interchange/native/{Payload.id.replace(':', '_')}.x_b"
            assert Hashlib.sha256(Archive.read(Entry)).hexdigest() == Payload.sha256


# this definition exists because focused behavior needs one stable owner
def TestFcstd(TmpPath: FilePath) -> None:
    Output = TmpPath / "example.FCStd"
    Convert(KSample, Output, allow_carrier=True)
    with Zipfile.ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        Objects = RootValue.findall("./Objects/Object")
        Types = [ItemValue.get("type") for ItemValue in Objects]
        Names = {ItemValue.get("name") for ItemValue in Objects}
        assert Types.count("Spreadsheet::Sheet") == 1
        assert Types.count("Sketcher::SketchObject") == 5
        assert Types.count("Part::Extrusion") == 5
        assert Types.count("Part::Cut") == 2
        assert Types.count("Part::MultiFuse") == 2
        assert Types.count("Part::Fillet") == 0
        assert {
            "Parameters",
            "Sketch1",
            "Sketch2",
            "Sketch3",
            "Sketch4",
            "Sketch6",
            "Boss_Extrude1",
            "Cut_Extrude1",
            "Boss_Extrude2",
            "Cut_Extrude2",
            "Boss_Extrude3",
            "Fillet1",
        } <= Names
        Fillet = RootValue.find("./Objects/Object[@name='Fillet1']")
        assert Fillet is not None
        assert Fillet.get("type") == "Part::Feature"
        Executable = RootValue.find(
            "./ObjectData/Object[@name='Fillet1']/Properties/Property[@name='NativeExecutable']/Bool"
        )
        Reason = RootValue.find(
            "./ObjectData/Object[@name='Fillet1']/Properties/Property[@name='NativeExecutionReason']/String"
        )
        assert Executable is not None and Executable.get("value") == "false"
        assert Reason is not None
        assert Reason.get("value") == "topology_selection_not_statically_provable"
        XmlValue = Archive.read("Document.xml")
        assert b"KitMetadata" in XmlValue


# this definition exists because focused behavior needs one stable owner
def TestFcstdEmits() -> None:
    Source = NeutralDoc()
    First = Replace(Source.feature_timeline[0], operation=BoolOperation.CREATE)
    Second = Replace(
        First,
        id="feature:intersection",
        name="Intersection",
        order=1,
        input_feature_ids=(First.id,),
        operation=BoolOperation.INTERSECT,
    )
    Source = Replace(
        Source,
        feature_timeline=(First, Second),
        bodies=(Replace(Source.bodies[0], final_feature_id=Second.id),),
    )
    Target = IoStream.BytesIO()
    FreeCadAdapter().write(Source, Target)
    DataValue = Target.getvalue()
    with Zipfile.ZipFile(IoStream.BytesIO(DataValue)) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    DeclValue = RootValue.find("./Objects/Object[@type='Part::Common']")
    assert DeclValue is not None
    NameValue = DeclValue.get("name")
    BaseValue = RootValue.find(
        f"./ObjectData/Object[@name='{NameValue}']/Properties/Property[@name='Base']/Link"
    )
    ToolValue = RootValue.find(
        f"./ObjectData/Object[@name='{NameValue}']/Properties/Property[@name='Tool']/Link"
    )
    assert BaseValue is not None and BaseValue.get("value") == "Boss1"
    assert ToolValue is not None and ToolValue.get("value") == "Intersection_Profile"
    assert FreeCadAdapter().read(DataValue) == Source


# this definition exists because focused behavior needs one stable owner
def TestFcstdOutput(TmpPath: FilePath) -> None:
    First = TmpPath / "first.FCStd"
    Second = TmpPath / "second.FCStd"
    Convert(KSample, First, allow_carrier=True)
    Convert(KSample, Second, allow_carrier=True)
    assert First.read_bytes() == Second.read_bytes()


# this definition exists because focused behavior needs one stable owner
def TestFcstdStream(TmpPath: FilePath) -> None:
    Output = TmpPath / "example.FCStd"
    Result = Convert(KSample, Output, allow_carrier=True)
    Stream = IoStream.BytesIO(Output.read_bytes())
    assert FreeCadAdapter().probe(Stream).confidence == 1.0
    assert Stream.tell() == 0
    assert OpenDoc(Stream) == Result.document


# this definition exists because focused behavior needs one stable owner
def TestGenericIsAs() -> None:
    Stream = IoStream.BytesIO()
    with Zipfile.ZipFile(Stream, "w") as Archive:
        Archive.writestr("Document.xml", "<Document/>")
    assert FreeCadAdapter().probe(Stream.getvalue()).confidence == 0.0


# this definition exists because opaque reads must retain their exact native payload
def VerifyOpaque(DocValue: CadDocument, Source: bytes) -> None:
    assert DocValue.validate() == ()
    assert DocValue.feature_timeline == ()
    assert len(DocValue.brep_payloads) == 2
    Payload = next(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.kind == "native_document"
        )
    )
    assert Payload.kind == "native_document"
    assert Payload.format_id == "freecad.fcstd"
    assert Payload.role == PayloadRole.DOCUMENT
    assert Payload.file_extension == ".FCStd"
    assert Payload.data == Source
    assert Capability.NATIVE_PAYLOADS in DocValue.capabilities
    assert Capability.BREP not in DocValue.capabilities


# this definition exists because opaque writes must retain xml declarations exactly
def VerifyOpaqueXml(PayloadData: bytes) -> None:
    with Zipfile.ZipFile(IoStream.BytesIO(PayloadData)) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        Opaque = RootValue.find("./ObjectData/Object[@name='Opaque']")
        assert Opaque is not None
        Token = Opaque.find("./Properties/Property[@name='Token']/String")
        assert Token is not None
        assert Token.get("value") == "retained"
        DeclValue = RootValue.find("./Objects/Object[@name='Opaque']")
        assert DeclValue is not None
        assert DeclValue.attrib == {
            "type": "App::FeaturePython",
            "name": "Opaque",
            "id": "41",
            "Touched": "1",
        }
        assert "interchange/document.json" not in Archive.namelist()


# this definition exists because focused behavior needs one stable owner
def TestOpaqueOnly() -> None:
    Source = NativeArchive(
        (
            (
                "Opaque",
                "App::FeaturePython",
                (),
                (
                    NativeProp(
                        "Label", "App::PropertyString", "String", {"value": "Opaque"}
                    ),
                    NativeProp(
                        "Token", "App::PropertyString", "String", {"value": "retained"}
                    ),
                ),
            ),
        ),
        {},
        {"Opaque": {"id": "41", "touched": True}},
    )
    Adapter = FreeCadAdapter()
    assert Adapter.probe(Source).confidence == 0.95
    DocValue = Adapter.read(Source)
    VerifyOpaque(DocValue, Source)
    WithoutBrep = Adapter.read(Source, ReadOptions(include_brep=False))
    assert WithoutBrep.brep_payloads == DocValue.brep_payloads
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    VerifyOpaqueXml(Output.getvalue())
    assert Output.getvalue() == Source
    assert Adapter.read(Output.getvalue()) == DocValue


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("CarrierSuffix", (".SLDPRT", ".CATPart"))
def TestUnknownData(CarrierSuffix: str, TmpPath: Path) -> None:
    SourceData = NativeArchive(
        (
            (
                "FutureResult",
                "FutureWorkbench::SolverResult",
                (),
                (
                    NativeProp(
                        "Label",
                        "App::PropertyString",
                        "String",
                        {"value": "Future Result"},
                    ),
                    NativeProp(
                        "SolverState",
                        "FutureWorkbench::PropertyState",
                        "FutureState",
                        {"encoding": "opaque", "value": "future-state"},
                    ),
                ),
            ),
        ),
        {"FutureWorkbench/state.bin": b"future opaque state\x00\xff"},
    )
    Source = TmpPath / "Future.FCStd"
    Source.write_bytes(SourceData)
    Carrier = TmpPath / f"Future{CarrierSuffix}"
    Convert(Source, Carrier, allow_carrier=True)
    Carried = OpenDoc(Carrier)
    NativeDoc = next(
        (
            Payload
            for Payload in Carried.brep_payloads
            if Payload.id == "freecad:native-document"
        )
    )
    NativeBinding = next(
        (
            Payload
            for Payload in Carried.brep_payloads
            if Payload.id == "freecad:native-document-binding"
        )
    )
    assert NativeDoc.data == SourceData
    assert NativeBinding.data == Hashlib.sha256(SourceData).digest()
    FreecadMeta = MetaMap(Carried.metadata["freecad"])
    FutureObject = next(
        (
            MetaMap(ItemValue)
            for ItemValue in MetaSeq(FreecadMeta["objects"])
            if MetaMap(ItemValue)["name"] == "FutureResult"
        )
    )
    FutureProps = MetaMap(FutureObject["properties"])
    SolverState = MetaMap(FutureProps["SolverState"])
    SolverChild = MetaMap(MetaSeq(SolverState["children"])[0])
    assert SolverChild["attributes"] == {
        "encoding": "opaque",
        "value": "future-state",
    }
    Restored = TmpPath / "Restored.FCStd"
    Result = Convert(Carrier, Restored)
    assert Result.output.metadata["compatibility"] == "native-exact"
    assert Restored.read_bytes() == SourceData
    with Zipfile.ZipFile(Restored) as Archive:
        assert (
            Archive.read("FutureWorkbench/state.bin") == b"future opaque state\x00\xff"
        )


# this definition exists because native part reads have a focused interchange contract
def VerifyPart(DocValue: CadDocument) -> None:
    assert DocValue.validate() == ()
    assert len(DocValue.sketches) == 1
    assert [str(Entity.kind) for Entity in DocValue.sketches[0].entities] == [
        "circle",
        "point",
        "ellipse",
        "spline",
    ]
    assert [str(RuleValue.kind) for RuleValue in DocValue.sketches[0].constraints] == [
        "diameter",
        "angle",
        "point_on_object",
    ]
    Angle = next(
        (
            Param
            for Param in DocValue.parameters
            if Param.attributes.get("freecad_path") == "Constraints[1]"
        )
    )
    assert Angle.value.value == 1.5707963267948966
    assert Angle.value.unit == "rad"
    assert [Feature.name for Feature in DocValue.feature_timeline] == ["Pad"]
    assert DocValue.bodies[0].final_feature_id == "freecad:feature:Pad"
    assert (
        DocValue.brep_payloads[0].data
        == b"\nCASCADE Topology V1, (c) Matra-Datavision\nfixture\n"
    )
    assert sum((Param.expression is not None for Param in DocValue.parameters)) == 2
    NativeRule = DocValue.sketches[0].constraints[2]
    Slots = MetaSeq(NativeRule.attributes["freecad_reference_slots"])
    assert [MetaMap(SlotValue)["freecad_geometry_index"] for SlotValue in Slots] == [
        1,
        -3,
        -2000,
    ]


# this definition exists because circle edits should alter only the intended sketch entity
def EditCircle(DocValue: CadDocument) -> CadDocument:
    SketchModel = DocValue.sketches[0]
    CircleEntity = SketchModel.entities[0]
    assert isinstance(CircleEntity.geometry, CircleGeom)
    EditedCircle = Replace(
        CircleEntity, geometry=Replace(CircleEntity.geometry, radius=7.5)
    )
    EditedSketch = Replace(
        SketchModel, entities=(EditedCircle, *SketchModel.entities[1:])
    )
    return Replace(DocValue, sketches=(EditedSketch,))


# this definition exists because native part xml must retain geometry and constraint structure
def VerifyPartXml(RootValue: ET.Element) -> None:
    Sketch = RootValue.find("./ObjectData/Object[@name='Sketch']")
    assert Sketch is not None
    assert [
        ItemValue.get("type")
        for ItemValue in Sketch.findall(
            "./Properties/Property[@name='Geometry']/GeometryList/Geometry"
        )
    ] == [
        "Part::GeomCircle",
        "Part::GeomPoint",
        "Part::GeomEllipse",
        "Part::GeomBSplineCurve",
    ]
    Circle = Sketch.find(
        "./Properties/Property[@name='Geometry']/GeometryList/Geometry/Circle"
    )
    assert Circle is not None
    assert float(Circle.get("Radius", "")) == 7.5
    EncodedConstraints = Sketch.findall(
        "./Properties/Property[@name='Constraints']/ConstraintList/Constrain"
    )
    assert len(EncodedConstraints) == 3
    assert EncodedConstraints[2].get("Type") == "13"
    assert EncodedConstraints[2].get("Second") == "-3"
    PadValue = RootValue.find("./ObjectData/Object[@name='Pad']")
    assert PadValue is not None
    assert len(PadValue.findall("./Properties/Property[@name='Shape']")) == 1


# this definition exists because focused behavior needs one stable owner
def TestSelfPart() -> None:
    DataValue = NativePart()
    Adapter = FreeCadAdapter()
    assert Adapter.probe(DataValue).confidence == 0.95
    DocValue = Adapter.read(DataValue)
    VerifyPart(DocValue)
    DocValue = EditCircle(DocValue)
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    VerifyPartXml(RootValue)


# this definition exists because focused behavior needs one stable owner
def TestReplayPlane() -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativePart())
    Plane = DocValue.support_planes[0]
    EditedPlane = Replace(
        Plane, transform=Replace(Plane.transform, origin=VectorThree(12.0, 34.0, 56.0))
    )
    Output = IoStream.BytesIO()
    Adapter.write(Replace(DocValue, support_planes=(EditedPlane,)), Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Placement = RootValue.find(
        "./ObjectData/Object[@name='XY_Plane']/Properties/Property[@name='Placement']/PropertyPlacement"
    )
    assert Placement is not None
    assert tuple(
        (float(Placement.get(NameValue, "")) for NameValue in ("Px", "Py", "Pz"))
    ) == (12.0, 34.0, 56.0)


# this definition exists because focused behavior needs one stable owner
def TestReplayProp() -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativePart())
    Feature = DocValue.feature_timeline[0]
    Output = IoStream.BytesIO()
    Adapter.write(
        Replace(DocValue, feature_timeline=(Replace(Feature, suppressed=True),)), Output
    )
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Suppressed = RootValue.find(
        "./ObjectData/Object[@name='Pad']/Properties/Property[@name='Suppressed']/Bool"
    )
    assert Suppressed is not None
    assert Suppressed.get("value") == "true"


# this definition exists because mapped shape fixtures share one sidecar structure
def ShapeFixture(Owner: str, ElemMap: str) -> ET.Element:
    NodeValue = NativeProp(
        "Shape",
        "Part::PropertyPartShape",
        "Part",
        {"ElementMap": ElemMap, "file": f"{Owner}.Shape.brp"},
    )
    ElemMapNode = XmlTree.SubElement(
        NodeValue, "ElementMap", {"new": "1", "count": "1"}
    )
    XmlTree.SubElement(ElemMapNode, "Element", {"key": "Dummy", "value": "Dummy"})
    XmlTree.SubElement(NodeValue, "ElementMap2", {"file": f"{Owner}.Shape.Map.txt"})
    return NodeValue


# this definition exists because focused behavior needs one stable owner
def TestSketchShape() -> None:
    SketchBrep = b"\nCASCADE Topology V1, (c) Matra-Datavision\nsketch\n"
    FinalBrep = b"\nCASCADE Topology V1, (c) Matra-Datavision\nfinal\n"
    SketchMap = b"BeginElementMap v1\nSketch map\nEndMap\n"
    FinalMap = b"BeginElementMap v1\nFinal map\nEndMap\n"
    Source = NativeArchive(
        (
            (
                "Sketch",
                "Sketcher::SketchObject",
                (),
                (
                    NativeProp(
                        "Label", "App::PropertyString", "String", {"value": "Sketch"}
                    ),
                    NativeProp(
                        "Geometry",
                        "Part::PropertyGeometryList",
                        "GeometryList",
                        {"count": "0"},
                    ),
                    NativeProp(
                        "Constraints",
                        "Sketcher::PropertyConstraintList",
                        "ConstraintList",
                        {"count": "0"},
                    ),
                    ShapeFixture("Sketch", "0.15.70200.5"),
                ),
            ),
            (
                "Final",
                "Part::Feature",
                ("Sketch",),
                (
                    NativeProp(
                        "Label", "App::PropertyString", "String", {"value": "Final"}
                    ),
                    ShapeFixture("Final", "1.15.70200.5"),
                ),
            ),
        ),
        {
            "Sketch.Shape.brp": SketchBrep,
            "Sketch.Shape.Map.txt": SketchMap,
            "Final.Shape.brp": FinalBrep,
            "Final.Shape.Map.txt": FinalMap,
        },
    )
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(Source)
    Payloads = {Payload.source_stream: Payload for Payload in DocValue.brep_payloads}
    assert Payloads["Sketch.Shape.brp"].data == SketchBrep
    assert Payloads["Sketch.Shape.brp"].attributes["freecad_sidecars"] == [
        {"source_stream": "Sketch.Shape.Map.txt", "data": SketchMap}
    ]
    assert Payloads["Final.Shape.brp"].data == FinalBrep
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        assert Archive.read("Sketch.Shape.brp") == SketchBrep
        assert Archive.read("Sketch.Shape.Map.txt") == SketchMap
        assert Archive.read("Final.Shape.brp") == FinalBrep
        assert Archive.read("Final.Shape.Map.txt") == FinalMap
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    SketchShape = RootValue.find(
        "./ObjectData/Object[@name='Sketch']/Properties/Property[@name='Shape']"
    )
    FinalShape = RootValue.find(
        "./ObjectData/Object[@name='Final']/Properties/Property[@name='Shape']"
    )
    assert SketchShape is not None
    assert FinalShape is not None
    SketchPart = SketchShape.find("./Part")
    SketchMapNode = SketchShape.find("./ElementMap")
    SketchElem = SketchShape.find("./ElementMap/Element")
    SketchMapTwo = SketchShape.find("./ElementMap2")
    FinalPart = FinalShape.find("./Part")
    FinalMapTwo = FinalShape.find("./ElementMap2")
    assert SketchPart is not None
    assert SketchMapNode is not None
    assert SketchElem is not None
    assert SketchMapTwo is not None
    assert FinalPart is not None
    assert FinalMapTwo is not None
    assert SketchPart.attrib == {
        "ElementMap": "0.15.70200.5",
        "file": "Sketch.Shape.brp",
    }
    assert SketchMapNode.attrib == {"new": "1", "count": "1"}
    assert SketchElem.attrib == {
        "key": "Dummy",
        "value": "Dummy",
    }
    assert SketchMapTwo.attrib == {"file": "Sketch.Shape.Map.txt"}
    assert FinalPart.attrib == {
        "ElementMap": "1.15.70200.5",
        "file": "Final.Shape.brp",
    }
    assert FinalMapTwo.attrib == {"file": "Final.Shape.Map.txt"}


# this definition exists because string hasher fixtures require deterministic archive ordering
def HasherSource(Table: bytes) -> bytes:
    with Zipfile.ZipFile(IoStream.BytesIO(NativePart())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        Entries = [
            (NameValue, Archive.read(NameValue))
            for NameValue in Archive.namelist()
            if NameValue != "Document.xml"
        ]
    RootValue.set("StringHasher", "1")
    RootValue.insert(
        0,
        XmlTree.Element(
            "StringHasher", {"saveall": "0", "threshold": "0", "count": "0", "new": "1"}
        ),
    )
    RootValue.insert(
        1, XmlTree.Element("StringHasher2", {"file": "StringHasher.Table.txt"})
    )
    Source = IoStream.BytesIO()
    with Zipfile.ZipFile(Source, "w", Zipfile.ZIP_DEFLATED) as Archive:
        Archive.writestr(
            "Document.xml",
            XmlTree.tostring(RootValue, encoding="utf-8", xml_declaration=True),
        )
        Archive.writestr("StringHasher.Table.txt", Table)
        for NameValue, DataValue in Entries:
            Archive.writestr(NameValue, DataValue)
    return Source.getvalue()


# this definition exists because focused behavior needs one stable owner
def TestStringRoot() -> None:
    Table = b"StringTableStart v1 0\n"
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(HasherSource(Table))
    StringHasher = MetaMap(MetaMap(DocValue.metadata["freecad"])["string_hasher"])
    assert StringHasher["attribute"] == "1"
    assert StringHasher["entries"] == [
        {"source_stream": "StringHasher.Table.txt", "data": Table}
    ]
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        assert Archive.namelist()[:3] == [
            "Document.xml",
            "StringHasher.Table.txt",
            "Pad.Shape.brp",
        ]
        assert Archive.read("StringHasher.Table.txt") == Table
        RestoredRoot = XmlTree.fromstring(Archive.read("Document.xml"))
    assert RestoredRoot.get("StringHasher") == "1"
    Hasher = RestoredRoot.find("./StringHasher")
    HasherTable = RestoredRoot.find("./StringHasher2")
    assert Hasher is not None
    assert Hasher.attrib == {"saveall": "0", "threshold": "0", "count": "0", "new": "1"}
    assert HasherTable is not None
    assert HasherTable.attrib == {"file": "StringHasher.Table.txt"}


# this definition exists because part graph shape properties share one sidecar encoding
def GraphShapeProp(NameValue: str, Source: str, Mapped: bool = False) -> ET.Element:
    NodeValue = NativeProp(
        NameValue,
        "Part::PropertyPartShape",
        "Part",
        {"ElementMap": "1.15.70200.5", "file": Source},
    )
    XmlTree.SubElement(NodeValue, "ElementMap")
    if Mapped:
        XmlTree.SubElement(NodeValue, "ElementMap2", {"file": Source + ".Map.txt"})
    return NodeValue


# this definition exists because the part graph fixture has one coherent native object graph
def GraphFixture() -> tuple[bytes, dict[str, bytes]]:
    Attachment = NativeProp(
        "AttachmentSupport", "App::PropertyLinkSubList", "LinkSubList", {"count": "1"}
    )
    XmlTree.SubElement(Attachment[0], "Link", {"obj": "XY_Plane", "sub": ""})
    Profile = NativeProp(
        "Profile", "App::PropertyLinkSub", "LinkSub", {"value": "Sketch", "count": "0"}
    )
    BodyProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Body"}),
        NativeLinkList("Group", ("Sketch", "Pad")),
        GraphShapeProp("Shape", "Body.Shape.brp", True),
        NativeProp("Tip", "App::PropertyLink", "Link", {"value": "Pad"}),
        NativeProp("Visibility", "App::PropertyBool", "Bool", {"value": "true"}),
    )
    OpaqueProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Opaque"}),
        NativeProp("Token", "App::PropertyString", "String", {"value": "retained"}),
        NativeProp(
            "Blob", "App::PropertyFileIncluded", "FileIncluded", {"file": "Blob.bin"}
        ),
    )
    PlaneProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "XY_Plane"}),
        NativePlacement(),
        NativeProp("Visibility", "App::PropertyBool", "Bool", {"value": "false"}),
    )
    SketchProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Sketch"}),
        Attachment,
        NativeProp(
            "Geometry", "Part::PropertyGeometryList", "GeometryList", {"count": "0"}
        ),
        NativeProp(
            "Constraints",
            "Sketcher::PropertyConstraintList",
            "ConstraintList",
            {"count": "0"},
        ),
        GraphShapeProp("InternalShape", "Sketch.InternalShape.brp"),
        NativePlacement(),
        GraphShapeProp("Shape", "Sketch.Shape.brp", True),
        NativeProp("Visibility", "App::PropertyBool", "Bool", {"value": "false"}),
    )
    PadProperties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Pad"}),
        GraphShapeProp("AddSubShape", "Pad.AddSubShape.brp", True),
        Profile,
        NativeProp("Length", "App::PropertyLength", "Float", {"value": "25"}),
        NativeProp("Type", "App::PropertyEnumeration", "Integer", {"value": "0"}),
        NativeProp("Reversed", "App::PropertyBool", "Bool", {"value": "false"}),
        NativeProp("Midplane", "App::PropertyBool", "Bool", {"value": "false"}),
        GraphShapeProp("Shape", "Pad.Shape.brp", True),
        GraphShapeProp("SuppressedShape", "Pad.SuppressedShape.brp"),
        NativeProp("Suppressed", "App::PropertyBool", "Bool", {"value": "false"}),
        NativeProp("Visibility", "App::PropertyBool", "Bool", {"value": "true"}),
    )
    BodyTransient = XmlTree.Element(
        "_Property",
        {
            "name": "_ElementMapVersion",
            "type": "App::PropertyString",
            "status": "234881024",
        },
    )
    SketchTransient = XmlTree.Element(
        "_Property",
        {
            "name": "_ElementMapVersion",
            "type": "App::PropertyString",
            "status": "234881024",
        },
    )
    PadTransients = (
        XmlTree.Element(
            "_Property",
            {
                "name": "PreviewShape",
                "type": "Part::PropertyPartShape",
                "status": "152",
            },
        ),
        XmlTree.Element(
            "_Property",
            {"name": "_Body", "type": "App::PropertyLinkHidden", "status": "251658240"},
        ),
        XmlTree.Element(
            "_Property",
            {
                "name": "_ElementMapVersion",
                "type": "App::PropertyString",
                "status": "234881024",
            },
        ),
    )
    Entries = {
        "Body.Shape.brp": b"\nCASCADE Topology V1, (c) Matra-Datavision\nbody\n",
        "Blob.bin": b"opaque-native-stream",
        "Body.Shape.brp.Map.txt": b"Body map",
        "Sketch.InternalShape.brp": b"",
        "Sketch.Shape.brp": b"\nCASCADE Topology V1, (c) Matra-Datavision\nsketch\n",
        "Sketch.Shape.brp.Map.txt": b"Sketch map",
        "Pad.AddSubShape.brp": b"\nCASCADE Topology V1, (c) Matra-Datavision\nadd\n",
        "Pad.AddSubShape.brp.Map.txt": b"Add map",
        "Pad.Shape.brp": b"\nCASCADE Topology V1, (c) Matra-Datavision\npad\n",
        "Pad.Shape.brp.Map.txt": b"Pad map",
        "Pad.SuppressedShape.brp": b"",
    }
    Source = NativeArchive(
        (
            ("Body", "PartDesign::Body", ("Sketch", "Pad"), BodyProperties),
            ("Opaque", "App::FeaturePython", (), OpaqueProperties),
            ("XY_Plane", "App::Plane", (), PlaneProperties),
            ("Sketch", "Sketcher::SketchObject", ("XY_Plane",), SketchProperties),
            ("Pad", "PartDesign::Pad", ("Body", "Sketch"), PadProperties),
        ),
        Entries,
        {
            "Body": {
                "id": "1",
                "extensions": ("App::OriginGroupExtension",),
                "transient_properties": (BodyTransient,),
            },
            "Opaque": {"id": "50"},
            "XY_Plane": {"id": "3"},
            "Sketch": {
                "id": "9",
                "extensions": ("Part::AttachExtension",),
                "transient_properties": (SketchTransient,),
            },
            "Pad": {
                "id": "12",
                "touched": True,
                "extensions": ("App::SuppressibleExtension", "Part::PreviewExtension"),
                "transient_properties": PadTransients,
            },
        },
    )
    return Source, Entries


# this definition exists because part graph declarations and transient properties must round trip together
def VerifyGraphXml(RootValue: ET.Element) -> None:
    Declarations = RootValue.findall("./Objects/Object")
    assert [ItemValue.get("name") for ItemValue in Declarations[:5]] == [
        "Body",
        "Opaque",
        "XY_Plane",
        "Sketch",
        "Pad",
    ]
    assert [ItemValue.get("type") for ItemValue in Declarations[:5]] == [
        "PartDesign::Body",
        "App::FeaturePython",
        "App::Plane",
        "Sketcher::SketchObject",
        "PartDesign::Pad",
    ]
    assert [ItemValue.get("id") for ItemValue in Declarations[:5]] == [
        "1",
        "50",
        "3",
        "9",
        "12",
    ]
    assert Declarations[4].get("Touched") == "1"
    Objects = {
        ItemValue.get("name", ""): ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
    }
    assert [
        ItemValue.get("name")
        for ItemValue in Objects["Opaque"].findall("./Properties/Property")
    ] == ["Label", "Token", "Blob"]
    TokenValue = Objects["Opaque"].find("./Properties/Property[@name='Token']/String")
    assert TokenValue is not None
    assert TokenValue.get("value") == "retained"
    assert [
        ItemValue.get("type")
        for ItemValue in Objects["Pad"].findall("./Extensions/Extension")
    ] == ["App::SuppressibleExtension", "Part::PreviewExtension"]
    assert [
        ItemValue.get("name")
        for ItemValue in Objects["Pad"].findall("./Properties/_Property")
    ] == ["PreviewShape", "_Body", "_ElementMapVersion"]
    BodyShape = Objects["Body"].find("./Properties/Property[@name='Shape']/Part")
    assert BodyShape is not None
    assert BodyShape.get("file") == "Body.Shape.brp"
    assert Objects["Pad"].find("./Properties/Property[@name='Sketches']") is None


# this definition exists because focused behavior needs one stable owner
def TestPartGraph() -> None:
    Source, Entries = GraphFixture()
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(Source)
    FreecadMeta = MetaMap(DocValue.metadata["freecad"])
    assert [
        MetaMap(ItemValue)["name"] for ItemValue in MetaSeq(FreecadMeta["objects"])
    ] == ["Body", "Opaque", "XY_Plane", "Sketch", "Pad"]
    assert {Payload.source_stream: Payload.data for Payload in DocValue.brep_payloads}[
        "Sketch.InternalShape.brp"
    ] == b""
    assert FreecadMeta["entries"] == [
        {"source_stream": "Blob.bin", "data": b"opaque-native-stream"}
    ]
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        Names = Archive.namelist()
        assert Names[: 1 + len(Entries)] == ["Document.xml", *Entries]
        assert Archive.read("Blob.bin") == b"opaque-native-stream"
        assert Archive.read("Sketch.InternalShape.brp") == b""
        assert Archive.read("Pad.SuppressedShape.brp") == b""
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    VerifyGraphXml(RootValue)


# this definition exists because focused behavior needs one stable owner
def TestSelfAsmAnd() -> None:
    DocValue = FreeCadAdapter().read(NativeAsm())
    assert DocValue.validate() == ()
    assert DocValue.assembly is not None
    assert len(DocValue.assembly.definitions) == 2
    assert len(DocValue.assembly.instances) == 1
    assert DocValue.assembly.instances[0].fixed
    assert [str(MateValue.kind) for MateValue in DocValue.assembly.mates] == ["hinge"]
    Revolute = DocValue.assembly.mates[0]
    Entities = {Entity.id: Entity for Entity in DocValue.assembly.mate_entities}
    assert [
        Entities[EntityId].source_entity_id for EntityId in Revolute.entity_ids
    ] == ["Face1", "Edge1", "Face2"]


# this definition exists because custom assembly fixtures need one reusable type mutation
def CustomTypesMut(RootValue: ET.Element) -> None:
    Declarations = {
        ItemValue.get("name", ""): ItemValue
        for ItemValue in RootValue.findall("./Objects/Object")
    }
    Declarations["Assembly"].set("type", "Vendor::FutureAssemblyRoot")
    Declarations["Joints"].set("type", "Vendor::FutureConstraintCollection")
    Declarations["PartLink"].set("type", "Vendor::FutureOccurrenceLink")
    Declarations["Grounded"].set("type", "Vendor::FutureFixedObject")
    Declarations["Revolute"].set("type", "Vendor::FutureKinematicObject")
    Linked = RootValue.find(
        "./ObjectData/Object[@name='PartLink']/Properties/Property[@name='LinkedObject']"
    )
    assert Linked is not None
    Linked.set("name", "ComponentLink")


# this definition exists because focused behavior needs one stable owner
def TestCustomAsm() -> None:

    # this definition exists because focused behavior needs one stable owner
    def CustomTypes(RootValue: ET.Element) -> None:
        CustomTypesMut(RootValue)

    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(RewriteDocXml(NativeAsm(), CustomTypes))
    assert DocValue.assembly is not None
    assert len(DocValue.assembly.instances) == 1
    assert len(DocValue.assembly.mates) == 1
    assert (
        MetaMap(DocValue.assembly.attributes["freecad"])["type_id"]
        == "Vendor::FutureAssemblyRoot"
    )
    assert (
        MetaMap(DocValue.assembly.instances[0].attributes["freecad"])["type_id"]
        == "Vendor::FutureOccurrenceLink"
    )
    assert (
        MetaMap(DocValue.assembly.mate_groups[0].attributes["freecad"])["type_id"]
        == "Vendor::FutureConstraintCollection"
    )
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Types = {
        ItemValue.get("name", ""): ItemValue.get("type", "")
        for ItemValue in RootValue.findall("./Objects/Object")
    }
    assert "Vendor::FutureAssemblyRoot" in Types.values()
    assert "Vendor::FutureConstraintCollection" in Types.values()
    assert "Vendor::FutureOccurrenceLink" in Types.values()
    assert "Vendor::FutureFixedObject" in Types.values()
    assert "Vendor::FutureKinematicObject" in Types.values()
    LinkValue = next(
        (NameValue for NameValue, TypeId in Types.items() if TypeId.endswith("Link"))
    )
    assert (
        RootValue.find(
            f"./ObjectData/Object[@name='{LinkValue}']/Properties/Property[@name='ComponentLink']/XLink"
        )
        is not None
    )


# this definition exists because focused behavior needs one stable owner
def TestAsmObjects() -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativeAsm())
    assert MetaMap(DocValue.metadata["freecad"])["entries"] == [
        {"source_stream": "Blob.bin", "data": b"opaque"}
    ]
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        Names = set(Archive.namelist())
        assert Archive.read("Blob.bin") == b"opaque"
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Declarations = {
        ItemValue.get("name", ""): ItemValue.get("type", "")
        for ItemValue in RootValue.findall("./Objects/Object")
    }
    assert Declarations["Opaque"] == "App::FeaturePython"
    assert "Assembly::AssemblyObject" in Declarations.values()
    assert "App::Link" in Declarations.values()
    Objects = {
        ItemValue.get("name", ""): ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
    }
    BlobValue = Objects["Opaque"].find("./Properties/Property[@name='Blob']/File")
    assert BlobValue is not None
    assert BlobValue.get("file") == "Blob.bin"
    assert any(
        (
            ItemValue.find("./Properties/Property[@name='JointType']") is not None
            for ItemValue in Objects.values()
        )
    )
    References = {
        NodeValue.get("file") or ""
        for NodeValue in RootValue.findall(".//*[@file]")
        if NodeValue.tag != "XLink" and (NodeValue.get("file") or "")
    }
    assert References <= Names


# this definition exists because assembly link and grounded object fields form one xml contract
def VerifyAsmLinks(RootValue: ET.Element) -> None:
    Types = {
        ItemValue.get("name", ""): ItemValue.get("type", "")
        for ItemValue in RootValue.findall("./Objects/Object")
    }
    Objects = {
        ItemValue.get("name", ""): ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
    }
    LinkName = next(
        (NameValue for NameValue, TypeId in Types.items() if TypeId == "App::Link")
    )
    LinkProperties = {
        ItemValue.get("name", ""): ItemValue
        for ItemValue in Objects[LinkName].findall("./Properties/Property")
    }
    assert int(LinkProperties["Placement"].get("status", "0")) & 4
    assert int(LinkProperties["LinkPlacement"].get("status", "0")) & 4
    Grounded = [
        ItemValue
        for ItemValue in Objects.values()
        if ItemValue.find("./Properties/Property[@name='ObjectToGround']") is not None
    ]
    assert len(Grounded) == 1
    GroundedName = Grounded[0].get("name", "")
    GroundedLinkProp = Grounded[0].find("./Properties/Property[@name='ObjectToGround']")
    assert GroundedLinkProp is not None
    GroundedLink = GroundedLinkProp.find("./Link")
    GroundedProxy = Grounded[0].find("./Properties/Property[@name='Proxy']/Python")
    assert Types[GroundedName] == "App::FeaturePython"
    assert GroundedLinkProp.get("type") == "App::PropertyLink"
    assert GroundedLink is not None
    assert GroundedLink.get("value") == LinkName
    assert GroundedProxy is not None
    assert GroundedProxy.attrib == {
        "value": "bnVsbA==",
        "encoded": "yes",
        "json": "yes",
    }


# this definition exists because assembly joint references and grouping form one xml contract
def VerifyAsmMate(RootValue: ET.Element) -> None:
    Types = {
        ItemValue.get("name", ""): ItemValue.get("type", "")
        for ItemValue in RootValue.findall("./Objects/Object")
    }
    Objects = {
        ItemValue.get("name", ""): ItemValue
        for ItemValue in RootValue.findall("./ObjectData/Object")
    }
    AsmName = next(
        (
            NameValue
            for NameValue, TypeId in Types.items()
            if TypeId == "Assembly::AssemblyObject"
        )
    )
    LinkName = next(
        (NameValue for NameValue, TypeId in Types.items() if TypeId == "App::Link")
    )
    Grounded = [
        ItemValue
        for ItemValue in Objects.values()
        if ItemValue.find("./Properties/Property[@name='ObjectToGround']") is not None
    ]
    GroundedName = Grounded[0].get("name", "")
    Joints = [
        ItemValue
        for ItemValue in Objects.values()
        if ItemValue.find("./Properties/Property[@name='JointType']") is not None
    ]
    assert len(Joints) == 1
    JointName = Joints[0].get("name", "")
    RefOne = Joints[0].find("./Properties/Property[@name='Reference1']/XLink")
    RefTwo = Joints[0].find("./Properties/Property[@name='Reference2']/XLink")
    assert RefOne is not None
    assert RefTwo is not None
    assert RefOne.get("name") == AsmName
    assert RefTwo.get("name") == AsmName
    assert [ItemValue.get("value") for ItemValue in RefOne.findall("./Sub")] == [
        f"{LinkName}.Face1",
        f"{LinkName}.Edge1",
    ]
    assert [ItemValue.get("value") for ItemValue in RefTwo.findall("./Sub")] == [
        f"{LinkName}.Face2"
    ]
    JointGroups = [
        NameValue
        for NameValue, TypeId in Types.items()
        if TypeId == "Assembly::JointGroup"
    ]
    assert len(JointGroups) == 1
    GroupLinks = Objects[JointGroups[0]].findall(
        "./Properties/Property[@name='Group']/LinkList/Link"
    )
    assert [ItemValue.get("value") for ItemValue in GroupLinks] == [
        GroundedName,
        JointName,
    ]
    assert not any(
        (
            ItemValue.find("./Properties/Property[@name='MateGroupId']") is not None
            for ItemValue in Objects.values()
        )
    )


# this definition exists because focused behavior needs one stable owner
def TestAsmWritesA() -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativeAsm())
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    VerifyAsmLinks(RootValue)
    VerifyAsmMate(RootValue)


# this definition exists because focused behavior needs one stable owner
def TestAsmWrites() -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativeAsm(BrepModelBrep(TriangleBrep())))
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        Types = {
            ObjValue.get("name", ""): ObjValue.get("type", "")
            for ObjValue in RootValue.findall("./Objects/Object")
        }
        ComponentGroups: list[list[str]] = []
        for ObjValue in RootValue.findall("./ObjectData/Object"):
            DefinitionId = ObjValue.find(
                "./Properties/Property[@name='DefinitionId']/String"
            )
            Group = ObjValue.find("./Properties/Property[@name='Group']/LinkList")
            if DefinitionId is not None and Group is not None:
                ComponentGroups.append(
                    [LinkValue.get("value", "") for LinkValue in Group]
                )
        assert any((Group for Group in ComponentGroups))
        assert "Part::Feature" in Types.values()
        ShapeEntries = [
            NameValue
            for NameValue in Archive.namelist()
            if NameValue.endswith(".Shape.brp")
        ]
        assert ShapeEntries
        assert all((Archive.read(NameValue) for NameValue in ShapeEntries))
    Restored = Adapter.read(Output.getvalue())
    assert Restored == DocValue
    assert Restored.validate() == ()


# this definition exists because focused behavior needs one stable owner
def TestOuterSource(TmpPath: FilePath) -> None:
    First = TmpPath / "First.FCStd"
    Second = TmpPath / "Second.FCStd"
    First.write_bytes(NativePart())
    Second.write_bytes(NativePart())
    AsmValue = TmpPath / "Assembly.FCStd"
    AsmValue.write_bytes(
        NativeOuterAsm(
            (
                ("First", "App::Link", First.name, "Body"),
                ("Second", "App::Link", Second.name, "Body"),
            )
        )
    )
    DocValue = FreeCadAdapter().read(AsmValue)
    assert DocValue.assembly is not None
    assert len(DocValue.assembly.definitions) == 3
    assert len(DocValue.assembly.documents) == 2
    assert (
        len({Instance.definition_id for Instance in DocValue.assembly.instances}) == 2
    )
    assert not any(
        (
            DiagValue.code == "freecad.unresolved_external_documents"
            for DiagValue in DocValue.diagnostics
        )
    )


# this definition exists because focused behavior needs one stable owner
def TestAsmGrouped(TmpPath: FilePath) -> None:
    First = TmpPath / "First.FCStd"
    Second = TmpPath / "Second.FCStd"
    First.write_bytes(NativePart())
    Second.write_bytes(NativePart())
    Source = TmpPath / "Mixed.FCStd"
    Source.write_bytes(
        NativeOuterAsm(
            (
                ("Grouped", "App::Link", First.name, "Body"),
                ("Standalone", "App::Link", Second.name, "Body"),
            ),
            GroupedNames=("Grouped",),
        )
    )
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(Source)
    assert DocValue.assembly is not None
    assert [ItemValue.name for ItemValue in DocValue.assembly.instances] == [
        "Grouped",
        "Standalone",
    ]
    assert len(DocValue.assembly.documents) == 2
    Output = TmpPath / "portable" / "Mixed.FCStd"
    Result = Adapter.write(DocValue, Output)
    assert Result.metadata["component_file_count"] == 2
    with Zipfile.ZipFile(Output) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    Links = [
        ItemValue.get("name", "")
        for ItemValue in RootValue.findall("./Objects/Object")
        if ItemValue.get("type") in {"App::Link", "Assembly::AssemblyLink"}
    ]
    Files = {
        ItemValue.get("file", "")
        for ItemValue in RootValue.findall(".//XLink[@file]")
        if ItemValue.get("file", "")
    }
    assert len(Links) == 2
    assert len(Files) == 2
    assert all(((Output.parent / FileName).is_file() for FileName in Files))
    Restored = Adapter.read(Output)
    assert Restored.assembly is not None
    assert len(Restored.assembly.instances) == 2
    assert len(Restored.assembly.documents) == 2


# this definition exists because portable external links must survive manifest free replay
def VerifyPortable(Adapter: FreeCadAdapter, Target: FilePath) -> None:
    NativeOnly = Target.parent / "NativeOnly.FCStd"
    with Zipfile.ZipFile(Target) as Archive:
        RootXml = XmlTree.fromstring(Archive.read("Document.xml"))
        Linked = RootXml.find(
            "./ObjectData/Object[@name='PartLink']/Properties/Property[@name='LinkedObject']/XLink"
        )
        assert Linked is not None
        assert Linked.get("file") == "Portable/Child.FCStd"
        assert Linked.get("stamp") == ""
        with Zipfile.ZipFile(NativeOnly, "w", Zipfile.ZIP_DEFLATED) as Output:
            for InfoValue in Archive.infolist():
                if InfoValue.filename != "interchange/document.json":
                    Output.writestr(InfoValue, Archive.read(InfoValue))
    Restored = Adapter.read(NativeOnly)
    assert Restored.assembly is None
    assert not any(
        (
            DiagValue.code == "freecad.unresolved_external_documents"
            for DiagValue in Restored.diagnostics
        )
    )


# this definition exists because stream targets must diagnose embedded external references
def VerifyEmbedMut(Adapter: FreeCadAdapter, DocValue: CadDocument) -> None:
    PortableStream = IoStream.BytesIO()
    PortableResult = Adapter.write(DocValue, PortableStream)
    assert PortableResult.application_usable is False
    assert PortableResult.metadata["carrier_embedded_reference_count"] == 1
    assert any(
        (
            DiagValue.code == "freecad.references_embedded_without_files"
            for DiagValue in PortableResult.diagnostics
        )
    )
    PortableRestored = Adapter.read(PortableStream.getvalue())
    assert (
        OuterDocs(PortableRestored)[0]["document"] == OuterDocs(DocValue)[0]["document"]
    )


# this definition exists because nonportable writes must retain their original relative reference
def VerifyLinkMut(Adapter: FreeCadAdapter, DocValue: CadDocument) -> None:
    Nonportable = IoStream.BytesIO()
    Adapter.write(DocValue, Nonportable, WriteOptions(values={"portable": False}))
    with Zipfile.ZipFile(IoStream.BytesIO(Nonportable.getvalue())) as Archive:
        NonportableXml = XmlTree.fromstring(Archive.read("Document.xml"))
    OriginalLink = NonportableXml.find(
        "./ObjectData/Object[@name='PartLink']/Properties/Property[@name='LinkedObject']/XLink"
    )
    assert OriginalLink is not None
    assert OriginalLink.get("file") == "nested/Child.FCStd"


# this definition exists because focused behavior needs one stable owner
def TestLinkOnlyDoc(TmpPath: FilePath) -> None:
    SourceFolder = TmpPath / "source"
    Child = SourceFolder / "nested" / "Child.FCStd"
    Child.parent.mkdir(parents=True)
    Child.write_bytes(NativePart())
    RootValue = SourceFolder / "LinkOnly.FCStd"
    RootValue.write_bytes(NativeLinkOnly("nested/Child.FCStd"))
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(RootValue)
    assert DocValue.assembly is None
    assert [ItemValue["file"] for ItemValue in OuterDocs(DocValue)] == [
        "nested/Child.FCStd"
    ]
    WithoutBrep = Adapter.read(RootValue, ReadOptions(include_brep=False))
    LinkedWithoutBrep = OuterDocs(WithoutBrep)[0]["document"]
    assert isinstance(LinkedWithoutBrep, CadDocument)
    assert not any(
        (
            Payload.role == PayloadRole.BREP
            for Payload in LinkedWithoutBrep.brep_payloads
        )
    )
    Staging = TmpPath / "staging"
    Target = Staging / "Portable.FCStd"
    Result = Adapter.write(DocValue, Target)
    Staging.rename(TmpPath / "relocated")
    Target = TmpPath / "relocated" / "Portable.FCStd"
    Bundled = Target.parent / "Portable" / "Child.FCStd"
    assert Bundled.is_file()
    assert Result.metadata["external_document_file_count"] == 1
    assert Result.metadata["external_document_bytes_written"] == Bundled.stat().st_size
    VerifyPortable(Adapter, Target)
    VerifyEmbedMut(Adapter, DocValue)
    VerifyLinkMut(Adapter, DocValue)


# this definition exists because focused behavior needs one stable owner
def TestNonportable(TmpPath: FilePath) -> None:
    Child = TmpPath / "nested" / "Child.FCStd"
    Child.parent.mkdir()
    Child.write_bytes(NativePart())
    Source = TmpPath / "LinkOnly.FCStd"
    Source.write_bytes(NativeLinkOnly("nested/Child.FCStd"))
    DocValue = OpenDoc(Source)
    Blocked = TmpPath / "blocked.FCStd"
    with Pytest.raises(AppUsabilityError) as Captured:
        Registry.write(
            DocValue, Blocked, options=WriteOptions(values={"portable": False})
        )
    assert Captured.value.requirements == ("referenced FreeCAD component files",)
    assert not Blocked.exists()
    Explicit = TmpPath / "explicit.FCStd"
    Result = Registry.write(
        DocValue,
        Explicit,
        options=WriteOptions(
            values={
                "portable": False,
                "allow_carrier": True,
                "require_self_contained": False,
            }
        ),
    )
    assert Result.requirements == ("referenced FreeCAD component files",)
    assert Result.metadata["native_self_contained"] is False
    assert Result.metadata["referenced_files_written"] == 0
    assert Result.near_lossless is False
    assert Explicit.read_bytes() == Source.read_bytes()


# this definition exists because focused behavior needs one stable owner
def TestPartExact(TmpPath: FilePath) -> None:
    Source = TmpPath / "source.FCStd"
    Source.write_bytes(NativePart())
    Target = TmpPath / "replay.FCStd"
    Result = WriteDoc(OpenDoc(Source), Target)
    assert Result.metadata["mode"] == "exact_native_roundtrip"
    assert Result.metadata["native_self_contained"] is True
    assert Result.requirements == ()
    assert Result.near_lossless is True
    assert Target.read_bytes() == Source.read_bytes()


# this definition exists because focused behavior needs one stable owner
def ForgedNativeDoc(DocValue: CadDocument, DataValue: bytes) -> CadDocument:
    Payload = next(
        (Value for Value in DocValue.brep_payloads if Value.role is PayloadRole.BREP)
    )
    ForgedPayload = Replace(
        Payload, data=DataValue, sha256=Hashlib.sha256(DataValue).hexdigest()
    )
    Forged = Replace(
        DocValue,
        brep_payloads=tuple(
            (
                ForgedPayload if Value.id == Payload.id else Value
                for Value in DocValue.brep_payloads
            )
        ),
    )
    return AnnotateNative(Forged)


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("Rebuild", (False, True))
def TestRecomputed(Rebuild: bool) -> None:
    DocValue = FreeCadAdapter().read(NativePart())
    ForgedData = b"\nCASCADE Topology V1, (c) Matra-Datavision\nchanged-invalid\n"
    Forged = ForgedNativeDoc(DocValue, ForgedData)
    assert UnchangedNative(Forged) is None
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(
        Forged, Output, WriteOptions(values={"rebuild": Rebuild})
    )
    Transfers = {Value.capability: Value for Value in Result.transfers}
    assert Result.metadata.get("mode") != "exact_native_roundtrip"
    assert Transfers[Capability.BREP].mode is TransferMode.CARRIER
    assert Transfers[Capability.BREP].carrier_reason is CarrierReason.SOURCE_OPAQUE
    assert Result.application_usable is False
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        NativeShapeFiles = tuple(
            (
                Value.get("file", "")
                for Value in RootValue.findall(".//Part[@file]")
                if Value.get("file", "")
            )
        )
        assert all(
            (Archive.read(NameValue) != ForgedData for NameValue in NativeShapeFiles)
        )
    Restored = FreeCadAdapter().read(Output.getvalue())
    ForgedPayloadId = next(
        (Value.id for Value in Forged.brep_payloads if Value.role is PayloadRole.BREP)
    )
    RestoredPayload = next(
        (Value for Value in Restored.brep_payloads if Value.id == ForgedPayloadId)
    )
    assert RestoredPayload.data == ForgedData


# this definition exists because focused behavior needs one stable owner
def TestRootCannot(TmpPath: FilePath) -> None:
    Child = TmpPath / "Child.FCStd"
    Child.write_bytes(NativePart())
    Parent = TmpPath / "Parent.FCStd"
    Parent.write_bytes(
        NativeOuterAsm((("Child", "Assembly::AssemblyLink", Child.name, "Body"),))
    )
    DocValue = FreeCadAdapter().read(Parent)
    assert DocValue.assembly is not None
    NestedEntry = next(
        (
            Value
            for Value in DocValue.assembly.documents
            if any(
                (
                    Payload.role is PayloadRole.BREP
                    for Payload in getattr(Value.document, "brep_payloads", ())
                )
            )
        )
    )
    ForgedData = b"\nCASCADE Topology V1, (c) Matra-Datavision\nnested-invalid\n"
    ForgedNested = ForgedNativeDoc(NestedEntry.document, ForgedData)
    AsmValue = Replace(
        DocValue.assembly,
        documents=tuple(
            (
                (
                    Replace(Value, document=ForgedNested)
                    if Value.id == NestedEntry.id
                    else Value
                )
                for Value in DocValue.assembly.documents
            )
        ),
    )
    Forged = AnnotateNative(Replace(DocValue, assembly=AsmValue))
    Target = TmpPath / "rebuilt" / "Parent.FCStd"
    Result = WriteDoc(Forged, Target, values={"rebuild": True})
    Transfers = {Value.capability: Value for Value in Result.transfers}
    assert Transfers[Capability.BREP].mode is TransferMode.CARRIER
    assert Transfers[Capability.BREP].carrier_reason is CarrierReason.SOURCE_OPAQUE
    assert Result.application_usable is False
    ComponentFiles = tuple(Target.parent.rglob("*.FCStd"))
    assert Target in ComponentFiles
    assert len(ComponentFiles) > 1
    for ComponentFile in ComponentFiles:
        with Zipfile.ZipFile(ComponentFile) as Archive:
            RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
            NativeShapeFiles = tuple(
                (
                    Value.get("file", "")
                    for Value in RootValue.findall(".//Part[@file]")
                    if Value.get("file", "")
                )
            )
            assert all(
                (
                    Archive.read(NameValue) != ForgedData
                    for NameValue in NativeShapeFiles
                )
            )


# this definition exists because focused behavior needs one stable owner
def TestAsmLink(TmpPath: FilePath) -> None:
    Child = TmpPath / "Child.FCStd"
    Child.write_bytes(NativeAsm())
    Parent = TmpPath / "Parent.FCStd"
    Parent.write_bytes(
        NativeOuterAsm((("Child", "Assembly::AssemblyLink", Child.name, "Assembly"),))
    )
    DocValue = FreeCadAdapter().read(Parent)
    assert DocValue.assembly is not None
    Definition = next(
        (
            ItemValue
            for ItemValue in DocValue.assembly.definitions
            if ItemValue.id != DocValue.assembly.root_definition_id
        )
    )
    assert str(Definition.kind) == "assembly"
    Nested = DocValue.assembly.document(Definition.document_id)
    assert Nested.assembly is not None
    assert len(Nested.assembly.instances) == 1


# this definition exists because focused behavior needs one stable owner
def TestFcstdData() -> None:
    Source = NativePart()
    Stripped = IoStream.BytesIO()
    with Zipfile.ZipFile(IoStream.BytesIO(Source)) as InputArchive:
        DocXml = InputArchive.read("Document.xml")
    with Zipfile.ZipFile(Stripped, "w", Zipfile.ZIP_DEFLATED) as OutputArchive:
        OutputArchive.writestr("Document.xml", DocXml)
    Adapter = FreeCadAdapter()
    assert Adapter.probe(Stripped.getvalue()).confidence == 0.0
    with Pytest.raises(FreeCadAdapterError, match="missing referenced data"):
        Adapter.read(Stripped.getvalue())


# this definition exists because focused behavior needs one stable owner
def TestFcstdUnsafe() -> None:
    Properties = (
        NativeProp("Label", "App::PropertyString", "String", {"value": "Bad"}),
    )
    Unsafe = NativeArchive((("../Bad", "App::FeaturePython", (), Properties),), {})
    Adapter = FreeCadAdapter()
    assert Adapter.probe(Unsafe).confidence == 0.0
    with Pytest.raises(FreeCadAdapterError, match="unsafe or invalid"):
        Adapter.read(Unsafe)
    DocValue = Adapter.read(NativePart())
    Freecad = MetaMap(DocValue.metadata["freecad"])
    Objects = [MetaMap(ItemValue) for ItemValue in MetaSeq(Freecad["objects"])]
    Objects[0]["name"] = "../Bad"
    Freecad["objects"] = Objects
    Invalid = Replace(DocValue, metadata={"freecad": Freecad})
    Output = IoStream.BytesIO()
    with Pytest.raises(ValueError, match="unsafe or invalid"):
        Adapter.write(Invalid, Output)
    assert Output.getvalue() == b""


# this definition exists because focused behavior needs one stable owner
def TestFcstdXml() -> None:
    Depth = 1200
    XmlValue = (
        b'<?xml version="1.0" encoding="utf-8"?><Document SchemaVersion="4" ProgramVersion="1.0" FileVersion="1"><Objects Count="1" Dependencies="1"><ObjectDeps Name="Deep" Count="0"/><Object type="App::FeaturePython" name="Deep" id="1"/></Objects><ObjectData Count="1"><Object name="Deep"><Properties Count="1" TransientCount="0"><Property name="Deep" type="App::PropertyString">'
        + b"<N>" * Depth
        + b"</N>" * Depth
        + b"</Property></Properties></Object></ObjectData></Document>"
    )
    Source = IoStream.BytesIO()
    with Zipfile.ZipFile(Source, "w", Zipfile.ZIP_DEFLATED) as Archive:
        Archive.writestr("Document.xml", XmlValue)
    Adapter = FreeCadAdapter()
    assert Adapter.probe(Source.getvalue()).confidence == 0.0
    with Pytest.raises(FreeCadAdapterError, match="nesting exceeds safe limits"):
        Adapter.read(Source.getvalue())


# this definition exists because focused behavior needs one stable owner
def TestCarrierA() -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativePart())
    Valid = IoStream.BytesIO()
    Adapter.write(DocValue, Valid, WriteOptions(values={"rebuild": True}))
    Malformed = IoStream.BytesIO()
    with Zipfile.ZipFile(IoStream.BytesIO(Valid.getvalue())) as Source:
        with Zipfile.ZipFile(Malformed, "w", Zipfile.ZIP_DEFLATED) as Output:
            for InfoValue in Source.infolist():
                if InfoValue.filename != "interchange/document.json":
                    Output.writestr(InfoValue, Source.read(InfoValue))
            Output.writestr("interchange/document.json", b"{")
    assert Adapter.probe(Malformed.getvalue()).confidence == 0.0
    with Pytest.raises(FreeCadAdapterError, match="corrupt"):
        Adapter.read(Malformed.getvalue())


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize("ChangedCopy", ("entry", "xml"))
def TestCarrier(ChangedCopy: str) -> None:
    Adapter = FreeCadAdapter()
    Valid = IoStream.BytesIO()
    Adapter.write(NeutralDoc(), Valid)
    with Zipfile.ZipFile(IoStream.BytesIO(Valid.getvalue())) as Source:
        Entries = {
            InfoValue.filename: Source.read(InfoValue)
            for InfoValue in Source.infolist()
        }
    Changed = JsonValue.loads(Entries["interchange/document.json"])
    Changed["source"]["path"] = "different-source"
    Canonical = JsonValue.dumps(
        Changed, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    if ChangedCopy == "entry":
        Entries["interchange/document.json"] = Canonical + b"\n"
    else:
        RootValue = XmlTree.fromstring(Entries["Document.xml"])
        DataProp = RootValue.find(".//Property[@name='KitManifestData']/String")
        DigestProp = RootValue.find(".//Property[@name='KitManifestSHA256']/String")
        assert DataProp is not None
        assert DigestProp is not None
        DataProp.set(
            "value",
            BaseSixFour.b64encode(ZlibValue.compress(Canonical, 9)).decode("ascii"),
        )
        DigestProp.set("value", Hashlib.sha256(Canonical).hexdigest())
        Entries["Document.xml"] = XmlTree.tostring(
            RootValue, encoding="utf-8", xml_declaration=True
        )
    Divergent = IoStream.BytesIO()
    with Zipfile.ZipFile(Divergent, "w", Zipfile.ZIP_DEFLATED) as Output:
        for NameValue, Value in Entries.items():
            Output.writestr(NameValue, Value)
    Result = Adapter.probe(Divergent.getvalue())
    assert Result.confidence == 0.0
    assert "copies do not match" in Result.reason
    with Pytest.raises(FreeCadAdapterError, match="copies do not match"):
        Adapter.read(Divergent.getvalue())


# this definition exists because focused behavior needs one stable owner
def TestCarrierUses() -> None:
    Adapter = FreeCadAdapter()
    DocValue = NeutralDoc()
    Valid = IoStream.BytesIO()
    Adapter.write(DocValue, Valid, WriteOptions(values={"rebuild": True}))
    Legacy = IoStream.BytesIO()
    with Zipfile.ZipFile(IoStream.BytesIO(Valid.getvalue())) as Source:
        with Zipfile.ZipFile(Legacy, "w", Zipfile.ZIP_DEFLATED) as Output:
            for InfoValue in Source.infolist():
                if InfoValue.filename != "interchange/document.json":
                    Output.writestr(InfoValue, Source.read(InfoValue))
    assert Adapter.probe(Legacy.getvalue()).confidence == 1.0
    assert Adapter.read(Legacy.getvalue()) == DocValue


# this definition exists because focused behavior needs one stable owner
def TestCarrierById() -> None:
    Configurations = (
        Config("configuration:a", "Shared", active=True),
        Config("configuration:b", "Second"),
        Config("configuration:c", "Shared"),
    )
    DocValue = Replace(NeutralDoc(), configurations=Configurations)
    Output = IoStream.BytesIO()
    Adapter = FreeCadAdapter()
    Adapter.write(DocValue, Output)
    ByIdValue = Adapter.read(
        Output.getvalue(), ReadOptions(configuration="configuration:b")
    )
    assert [
        ItemValue.id for ItemValue in ByIdValue.configurations if ItemValue.active
    ] == ["configuration:b"]
    ByName = Adapter.read(Output.getvalue(), ReadOptions(configuration="Shared"))
    assert [
        ItemValue.id for ItemValue in ByName.configurations if ItemValue.active
    ] == ["configuration:a", "configuration:c"]


# this definition exists because focused behavior needs one stable owner
def TestRejectsAnd() -> None:
    Adapter = FreeCadAdapter()
    Carrier = IoStream.BytesIO()
    Adapter.write(NeutralDoc(), Carrier)
    for Source in (Carrier.getvalue(), NativePart()):
        with Pytest.raises(FreeCadAdapterError, match="configuration"):
            Adapter.read(Source, ReadOptions(configuration="missing-configuration"))


# this definition exists because focused behavior needs one stable owner
def TestSelectsById() -> None:
    Adapter = FreeCadAdapter()
    Source = NativePart()
    Config = Adapter.read(Source).configurations[0]
    for Selected in (Config.id, Config.name):
        Restored = Adapter.read(Source, ReadOptions(configuration=Selected))
        assert [
            ItemValue.id for ItemValue in Restored.configurations if ItemValue.active
        ] == [Config.id]


# this definition exists because focused behavior needs one stable owner
def TestCarrierAndA() -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativePart())
    Valid = IoStream.BytesIO()
    Adapter.write(DocValue, Valid, WriteOptions(values={"rebuild": True}))
    Invalid = IoStream.BytesIO()
    InvalidManifest = b'{"foo":"bar"}'
    with Zipfile.ZipFile(IoStream.BytesIO(Valid.getvalue())) as Source:
        RootValue = XmlTree.fromstring(Source.read("Document.xml"))
        DataProp = RootValue.find(".//Property[@name='KitManifestData']/String")
        DigestProp = RootValue.find(".//Property[@name='KitManifestSHA256']/String")
        assert DataProp is not None
        assert DigestProp is not None
        DataProp.set(
            "value",
            BaseSixFour.b64encode(ZlibValue.compress(InvalidManifest, 9)).decode(
                "ascii"
            ),
        )
        DigestProp.set("value", Hashlib.sha256(InvalidManifest).hexdigest())
        with Zipfile.ZipFile(Invalid, "w", Zipfile.ZIP_DEFLATED) as Output:
            for InfoValue in Source.infolist():
                if InfoValue.filename not in {
                    "Document.xml",
                    "interchange/document.json",
                }:
                    Output.writestr(InfoValue, Source.read(InfoValue))
            Output.writestr(
                "Document.xml",
                XmlTree.tostring(RootValue, encoding="utf-8", xml_declaration=True),
            )
            Output.writestr("interchange/document.json", InvalidManifest)
    Result = Adapter.probe(Invalid.getvalue())
    assert Result.confidence == 0.0
    assert "cannot be restored" in Result.reason
    with Pytest.raises(FreeCadAdapterError, match="cannot be restored"):
        Adapter.read(Invalid.getvalue())


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    "DocXml", (None, b"not XML", b"<Document/>"), ids=("missing", "invalid", "empty")
)
def TestCarrierDoc(DocXml: bytes | None) -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativePart())
    Valid = IoStream.BytesIO()
    Adapter.write(DocValue, Valid, WriteOptions(values={"rebuild": True}))
    with Zipfile.ZipFile(IoStream.BytesIO(Valid.getvalue())) as Source:
        Manifest = Source.read("interchange/document.json")
    Invalid = IoStream.BytesIO()
    with Zipfile.ZipFile(Invalid, "w", Zipfile.ZIP_DEFLATED) as Output:
        if DocXml is not None:
            Output.writestr("Document.xml", DocXml)
        Output.writestr("interchange/document.json", Manifest)
    Result = Adapter.probe(Invalid.getvalue())
    assert Result.confidence == 0.0
    assert "Document.xml" in Result.reason
    with Pytest.raises(FreeCadAdapterError, match="Document.xml"):
        Adapter.read(Invalid.getvalue())


# this definition exists because focused behavior needs one stable owner
def TestCarrierNon() -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativePart(BrepModelBrep(TriangleBrep())))
    Valid = IoStream.BytesIO()
    Adapter.write(DocValue, Valid, WriteOptions(values={"rebuild": True}))
    Invalid = IoStream.BytesIO()
    with Zipfile.ZipFile(IoStream.BytesIO(Valid.getvalue())) as Source:
        RootValue = XmlTree.fromstring(Source.read("Document.xml"))
        Referenced = [
            NodeValue.get("file") or ""
            for NodeValue in RootValue.findall(".//*[@file]")
            if NodeValue.tag != "XLink" and (NodeValue.get("file") or "")
        ]
        assert Referenced
        Missing = Referenced[0]
        with Zipfile.ZipFile(Invalid, "w", Zipfile.ZIP_DEFLATED) as Output:
            for InfoValue in Source.infolist():
                if InfoValue.filename != Missing:
                    Output.writestr(InfoValue, Source.read(InfoValue))
    Result = Adapter.probe(Invalid.getvalue())
    assert Result.confidence == 0.0
    assert "missing referenced data" in Result.reason
    with Pytest.raises(FreeCadAdapterError, match="missing referenced data"):
        Adapter.read(Invalid.getvalue())


# this definition exists because focused behavior needs one stable owner
def TestCarrierDeep() -> None:
    RawValue = ('{"metadata":' + "[" * 2000 + "0" + "]" * 2000 + "}").encode("utf-8")
    Native = NativePart()
    with Zipfile.ZipFile(IoStream.BytesIO(Native)) as Source:
        DocXml = Source.read("Document.xml")
        NativeEntries = [
            (InfoValue.filename, Source.read(InfoValue))
            for InfoValue in Source.infolist()
            if InfoValue.filename != "Document.xml"
        ]
    Direct = IoStream.BytesIO()
    with Zipfile.ZipFile(Direct, "w", Zipfile.ZIP_DEFLATED) as Archive:
        Archive.writestr("Document.xml", DocXml)
        for NameValue, DataValue in NativeEntries:
            Archive.writestr(NameValue, DataValue)
        Archive.writestr("interchange/document.json", RawValue)
    RootValue = XmlTree.fromstring(DocXml)
    Properties = RootValue.find("./ObjectData/Object/Properties")
    assert Properties is not None
    Properties.set("Count", str(int(Properties.get("Count", "0")) + 3))
    Encoded = BaseSixFour.b64encode(ZlibValue.compress(RawValue, 9)).decode("ascii")
    Properties.extend(
        (
            NativeProp(
                "KitManifestData", "App::PropertyString", "String", {"value": Encoded}
            ),
            NativeProp(
                "KitManifestEncoding",
                "App::PropertyString",
                "String",
                {"value": "zlib+base64+utf-8"},
            ),
            NativeProp(
                "KitManifestSHA256",
                "App::PropertyString",
                "String",
                {"value": Hashlib.sha256(RawValue).hexdigest()},
            ),
        )
    )
    Embedded = IoStream.BytesIO()
    with Zipfile.ZipFile(Embedded, "w", Zipfile.ZIP_DEFLATED) as Archive:
        Archive.writestr(
            "Document.xml",
            XmlTree.tostring(RootValue, encoding="utf-8", xml_declaration=True),
        )
        for NameValue, DataValue in NativeEntries:
            Archive.writestr(NameValue, DataValue)
    Adapter = FreeCadAdapter()
    for Hostile in (Direct.getvalue(), Embedded.getvalue()):
        Result = Adapter.probe(Hostile)
        assert Result.confidence == 0.0
        assert "JSON nesting exceeds safe limits" in Result.reason
        with Pytest.raises(
            FreeCadAdapterError, match="JSON nesting exceeds safe limits"
        ):
            Adapter.read(Hostile)


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("EntryName", "EntryData", "Message"),
    (
        ("../Bad.bin", b"bad", "unsafe entry name"),
        ("Bomb.bin", b"\x00" * (1024 * 1024), "compression ratio is unsafe"),
    ),
    ids=("unsafe_path", "compression_bomb"),
)
def TestCarrierAnd(EntryName: str, EntryData: bytes, Message: str) -> None:
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(NativePart())
    Valid = IoStream.BytesIO()
    Adapter.write(DocValue, Valid, WriteOptions(values={"rebuild": True}))
    Hostile = IoStream.BytesIO()
    with Zipfile.ZipFile(IoStream.BytesIO(Valid.getvalue())) as Source:
        with Zipfile.ZipFile(Hostile, "w", Zipfile.ZIP_DEFLATED) as Output:
            Output.writestr("Document.xml", Source.read("Document.xml"))
            Output.writestr(
                "interchange/document.json", Source.read("interchange/document.json")
            )
            Output.writestr(EntryName, EntryData)
    assert Adapter.probe(Hostile.getvalue()).confidence == 0.0
    with Pytest.raises(FreeCadAdapterError, match=Message):
        Adapter.read(Hostile.getvalue())


# this definition exists because focused behavior needs one stable owner
def TestProbeEntry() -> None:
    DataValue = bytearray(NativePart())
    with Zipfile.ZipFile(IoStream.BytesIO(DataValue)) as Archive:
        Shape = Archive.getinfo("Pad.Shape.brp")
    Flags = Struct.unpack_from("<H", DataValue, Shape.header_offset + 6)[0] | 1
    Struct.pack_into("<H", DataValue, Shape.header_offset + 6, Flags)
    Offset = 0
    while True:
        Offset = DataValue.find(b"PK\x01\x02", Offset)
        if Offset < 0:
            break
        NameLength = Struct.unpack_from("<H", DataValue, Offset + 28)[0]
        ExtraLength = Struct.unpack_from("<H", DataValue, Offset + 30)[0]
        CommentLength = Struct.unpack_from("<H", DataValue, Offset + 32)[0]
        NameValue = bytes(DataValue[Offset + 46 : Offset + 46 + NameLength]).decode(
            "utf-8"
        )
        if NameValue == "Pad.Shape.brp":
            CentralFlags = Struct.unpack_from("<H", DataValue, Offset + 8)[0] | 1
            Struct.pack_into("<H", DataValue, Offset + 8, CentralFlags)
            break
        Offset += 46 + NameLength + ExtraLength + CommentLength
    assert FreeCadAdapter().probe(bytes(DataValue)).confidence == 0.0


# this definition exists because focused behavior needs one stable owner
def TestSupports() -> None:
    DocValue = FreeCadAdapter().read(NativePart())
    Adapter = FreeCadAdapter()
    assert Adapter.supports(DocValue, IoStream.BytesIO())
    assert not Adapter.supports(DocValue, IoStream.StringIO())
    assert not Adapter.supports(DocValue, IoStream.BufferedReader(IoStream.BytesIO()))


# this definition exists because focused behavior needs one stable owner
def TestReadCanBrep() -> None:
    DocValue = FreeCadAdapter().read(NativeAsm(), ReadOptions(include_brep=False))
    assert not any(
        (Payload.role == PayloadRole.BREP for Payload in DocValue.brep_payloads)
    )
    assert DocValue.assembly is not None
    assert all(
        (
            not any(
                (
                    Payload.role == PayloadRole.BREP
                    for Payload in ItemValue.document.brep_payloads
                )
            )
            for ItemValue in DocValue.assembly.documents
        )
    )


# this definition exists because focused behavior needs one stable owner
def TestPartdesignC() -> None:
    Source = KFreecadExamples / "PartDesignExample.FCStd"
    if not Source.is_file():
        Pytest.skip("bundled FreeCAD PartDesign example is unavailable")
    Adapter = FreeCadAdapter()
    DocValue = Adapter.read(Source, ReadOptions(include_brep=False))
    assert not any(
        (Payload.role == PayloadRole.BREP for Payload in DocValue.brep_payloads)
    )
    Output = IoStream.BytesIO()
    Adapter.write(DocValue, Output)
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        Names = set(Archive.namelist())
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    References = [
        NodeValue.get("file") or ""
        for NodeValue in RootValue.findall(".//*[@file]")
        if NodeValue.tag != "XLink" and (NodeValue.get("file") or "")
    ]
    assert References
    assert set(References) <= Names
    NativeShapes = [
        PropElem
        for PropElem in RootValue.findall(".//Property")
        if PropElem.get("type")
        in {"Part::PropertyPartShape", "Part::PropertyPartShapeHidden"}
    ]
    assert NativeShapes
    Parts = [PropElem.find("./Part") for PropElem in NativeShapes]
    assert all(
        (PartValue is None or not PartValue.get("file", "") for PartValue in Parts)
    )


# this definition exists because focused behavior needs one stable owner
def TestPartdesign() -> None:
    Source = KFreecadExamples / "PartDesignExample.FCStd"
    if not Source.is_file():
        Pytest.skip("bundled FreeCAD PartDesign example is unavailable")
    Adapter = FreeCadAdapter()
    assert Adapter.probe(Source).confidence == 0.95
    DocValue = Adapter.read(Source)
    assert DocValue.validate() == ()
    assert [
        (Sketch.name, len(Sketch.entities), len(Sketch.constraints))
        for Sketch in DocValue.sketches
    ] == [
        ("Sketch", 4, 12),
        ("Sketch001", 4, 11),
        ("Sketch003", 1, 2),
        ("Sketch002", 12, 32),
    ]
    assert [Feature.name for Feature in DocValue.feature_timeline] == [
        "Pad",
        "Pocket",
        "Pocket001",
        "Pocket002",
    ]
    assert DocValue.bodies[0].final_feature_id == "freecad:feature:Pocket002"
    FinalPayload = next(
        (
            Payload
            for Payload in DocValue.brep_payloads
            if Payload.source_stream == "Pocket002.Shape.brp"
        )
    )
    assert (
        FinalPayload.sha256
        == "285ae851c79757d7252b67236637f52c776b45b8c42d1e5749109b048d0430c9"
    )
    assert len(FinalPayload.data or b"") == 51454


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    "NameValue",
    (
        "ArchDetail.FCStd",
        "AssemblyExample.FCStd",
        "BIMExample.FCStd",
        "draft_test_objects.FCStd",
        "EngineBlock.FCStd",
        "FEMExample.FCStd",
        "PartDesignExample.FCStd",
    ),
)
def TestExample(NameValue: str) -> None:
    Source = KFreecadExamples / NameValue
    if not Source.is_file():
        Pytest.skip(f"bundled FreeCAD example {NameValue} is unavailable")
    DocValue = FreeCadAdapter().read(Source)
    assert DocValue.validate() == ()


# this definition exists because the bundled assembly has one stable native read contract
def VerifyBundled(DocValue: CadDocument) -> tuple[bytes, ...]:
    assert DocValue.validate() == ()
    assert DocValue.assembly is not None
    assert len(DocValue.assembly.definitions) == 14
    assert len(DocValue.assembly.instances) == 13
    assert len(DocValue.assembly.mates) == 16
    assert len(DocValue.brep_payloads) == 15
    assert DocValue.brep is None
    SourceShapes = tuple(
        (
            Payload.data
            for Payload in DocValue.brep_payloads
            if Payload.role == PayloadRole.BREP and Payload.data is not None
        )
    )
    assert len(SourceShapes) == 13
    assert all((IsStructurallyValidAscii(DataValue) for DataValue in SourceShapes))
    BasePin = DocValue.assembly.instances[0]
    assert BasePin.fixed
    assert BasePin.transform.values[3:12:4] == (
        -206.51702880859375,
        40.255699157714844,
        364.26800537109375,
    )
    Revolute = next(
        (
            MateValue
            for MateValue in DocValue.assembly.mates
            if MateValue.name == "Revolute"
        )
    )
    Entities = {Entity.id: Entity for Entity in DocValue.assembly.mate_entities}
    assert [
        Entities[EntityId].source_entity_id for EntityId in Revolute.entity_ids
    ] == ["Face1", "Edge2", "Edge107", "Edge107"]
    assert str(Revolute.kind) == "hinge"
    return SourceShapes


# this definition exists because each emitted component must contain loadable native shape data
def CollectShapes(ComponentFiles: list[FilePath]) -> list[bytes]:
    EmittedShapes: list[bytes] = []
    for ComponentFile in ComponentFiles:
        with Zipfile.ZipFile(ComponentFile) as Archive:
            RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
            assert any(
                (
                    ItemValue.get("type") == "Part::Feature"
                    for ItemValue in RootValue.findall("./Objects/Object")
                )
            )
            ShapeEntries = [
                NameValue
                for NameValue in Archive.namelist()
                if NameValue.endswith(".Shape.brp")
            ]
            assert ShapeEntries
            assert all((Archive.read(NameValue) for NameValue in ShapeEntries))
            EmittedShapes.extend(
                (Archive.read(NameValue) for NameValue in ShapeEntries)
            )
    return EmittedShapes


# this definition exists because focused behavior needs one stable owner
def TestAsmFcstdAnd(TmpPath: FilePath) -> None:
    Source = KFreecadExamples / "AssemblyExample.FCStd"
    if not Source.is_file():
        Pytest.skip("bundled FreeCAD assembly example is unavailable")
    DocValue = FreeCadAdapter().read(Source)
    SourceShapes = VerifyBundled(DocValue)
    Output = TmpPath / "Assembly.FCStd"
    Result = Convert(Source, Output)
    assert Result.near_lossless
    Transfers = {Transfer.capability: Transfer for Transfer in Result.transfers}
    assert Transfers[Capability.BREP].mode is TransferMode.NATIVE
    assert Transfers[Capability.NATIVE_PAYLOADS].mode is TransferMode.NATIVE
    ComponentFiles = sorted((TmpPath / "Assembly").glob("*.FCStd"))
    assert len(ComponentFiles) == 13
    EmittedShapes = CollectShapes(ComponentFiles)
    assert sorted(
        (Hashlib.sha256(DataValue).digest() for DataValue in EmittedShapes)
    ) == sorted((Hashlib.sha256(DataValue).digest() for DataValue in SourceShapes))
    assert FreeCadAdapter().read(Output) == DocValue


# this binding exists because shared behavior needs one stable value
globals()["ADDITIONAL_PART_OBJECT_TYPE_IDS"] = AdditionalPartObjectType

# this binding exists because shared behavior needs one stable value
globals()["APP_LINK_TYPE_ID"] = AppLinkTypeId

# this binding exists because shared behavior needs one stable value
globals()["APP_PART_TYPE_ID"] = AppPartTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES"] = AsmConnectorPropPrefixes

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_JOINT_GROUP_TYPE_ID"] = AsmJointGroupTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_LINK_TYPE_ID"] = AsmLinkTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_OBJECT_TYPE_PREFIX"] = AsmObjectTypePrefix

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_ROOT_TYPE_ID"] = AsmRootTypeId

# this binding exists because shared behavior needs one stable value
globals()["ApplicationUsabilityError"] = AppUsabilityError

# this binding exists because shared behavior needs one stable value
globals()["ArcEllipseGeometry"] = ArcEllipseGeom

# this binding exists because shared behavior needs one stable value
globals()["ArcHyperbolaGeometry"] = ArcHyperbolaGeom

# this binding exists because shared behavior needs one stable value
globals()["ArcParabolaGeometry"] = ArcParabolaGeom

# this binding exists because shared behavior needs one stable value
globals()["BODY_CONTAINER_TYPE_IDS"] = BodyContainerTypeIds

# this binding exists because shared behavior needs one stable value
globals()["BODY_TYPE_ID"] = BodyTypeId

# this binding exists because shared behavior needs one stable value
globals()["BOOLEAN_OPERATION_TYPES"] = BoolOperationTypes

# this binding exists because shared behavior needs one stable value
globals()["BOOLEAN_OPERATION_TYPE_BY_KIND"] = BoolOperationTypeByKind

# this binding exists because shared behavior needs one stable value
globals()["BooleanOperation"] = BoolOperation

# this binding exists because shared behavior needs one stable value
globals()["CAPABILITY_CARRIER_REASONS"] = CapabilityCarrierReasons

# this binding exists because shared behavior needs one stable value
globals()["CAPABILITY_WRITE_TYPE_IDS"] = CapabilityWriteTypeIds

# this binding exists because shared behavior needs one stable value
globals()["CIRCULAR_GEOMETRY_KINDS"] = CircularGeomKinds

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_CARRIER_KINDS"] = RuleCarrierKinds

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_CODE_BY_KIND"] = RuleCodeByKind

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_COMPOSED_KINDS"] = RuleComposedKinds

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_DIRECT_KINDS"] = RuleDirectKinds

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_KIND_BY_CODE"] = RuleKindByCode

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_POINTS"] = RulePoints

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_POINT_BY_INDEX"] = RulePointByIndex

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_POINT_INDEX_BY_NAME"] = RulePointIndexByName

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_TYPES"] = RuleTypes

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_VALUE_KIND_BY_CODE"] = RuleValueKindByCode

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_WRITE_CODES"] = RuleWriteCodes

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_WRITE_KINDS"] = RuleWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["CREATE_OPERATION_NAMES"] = CreateOperationNames

# this binding exists because shared behavior needs one stable value
globals()["CircleGeometry"] = CircleGeom

# this binding exists because shared behavior needs one stable value
globals()["Configuration"] = Config

# this binding exists because shared behavior needs one stable value
globals()["ConstraintKind"] = RuleKind

# this binding exists because shared behavior needs one stable value
globals()["ConstraintReference"] = RuleRef

# this binding exists because shared behavior needs one stable value
globals()["DIMENSIONAL_CONSTRAINT_CODES"] = DimensionalRuleCodes

# this binding exists because shared behavior needs one stable value
globals()["ET"] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()["EXTRUSION_TYPES"] = ExtrusionTypes

# this binding exists because shared behavior needs one stable value
globals()["EXTRUSION_TYPE_BY_CODE"] = ExtrusionTypeByCode

# this binding exists because shared behavior needs one stable value
globals()["EllipseGeometry"] = EllipseGeom

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_CARRIER_KINDS"] = FeatureCarrierKinds

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_KIND_BY_TYPE_ID"] = FeatureKindByTypeId

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_TYPES"] = FeatureTypes

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_WRITE_KINDS"] = FeatureWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_WRITE_TYPE_IDS"] = FeatureWriteTypeIds

# this binding exists because shared behavior needs one stable value
globals()["FIXED_CONSTRAINT_KINDS"] = FixedRuleKinds

# this binding exists because shared behavior needs one stable value
globals()["FORMAT_ID"] = FormatId

# this binding exists because shared behavior needs one stable value
globals()["FREECAD_EXAMPLES"] = KFreecadExamples

# this binding exists because shared behavior needs one stable value
globals()["FreeCADAdapter"] = FreeCadAdapter

# this binding exists because shared behavior needs one stable value
globals()["FreeCADAdapterError"] = FreeCadAdapterError

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_CARRIER_KINDS"] = GeomCarrierKinds

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_KIND_BY_TYPE_ID"] = GeomKindByTypeId

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_TYPES"] = GeomTypes

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_TYPE_IDS_BY_KIND"] = GeomTypeIdsByKind

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_WRITE_KINDS"] = GeomWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_WRITE_TYPE_IDS"] = GeomWriteTypeIds

# this binding exists because shared behavior needs one stable value
globals()["GeometryKind"] = GeomKind

# this binding exists because shared behavior needs one stable value
globals()["HyperbolaGeometry"] = HyperbolaGeom

# this binding exists because shared behavior needs one stable value
globals()["INFO"] = InfoValue

# this binding exists because shared behavior needs one stable value
globals()["JOINT_GROUND_PROPERTY"] = JointGroundProp

# this binding exists because shared behavior needs one stable value
globals()["JOINT_REFERENCE_INDEX_BY_PROPERTY"] = JointRefIndexByProp

# this binding exists because shared behavior needs one stable value
globals()["JOINT_REFERENCE_PROPERTIES"] = JointRefProperties

# this binding exists because shared behavior needs one stable value
globals()["JOINT_RESERVED_LINK_PROPERTIES"] = JointReservedLink

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPES"] = JointTypes

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPES_USING_DISTANCE"] = JointTypesUsingDistance

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPES_USING_SECOND_DISTANCE"] = JointTypesUsingSecond

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPE_BY_MATE_KIND"] = JointTypeByMateKind

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPE_DEFINITIONS"] = JointTypeDefinitions

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPE_PROPERTIES"] = JointTypeProperties

# this binding exists because shared behavior needs one stable value
globals()["LineGeometry"] = LineGeom

# this binding exists because shared behavior needs one stable value
globals()["MATE_CARRIER_KINDS"] = MateCarrierKinds

# this binding exists because shared behavior needs one stable value
globals()["MATE_KINDS_USING_DISTANCE"] = MateKindsUsingDistance

# this binding exists because shared behavior needs one stable value
globals()["MATE_KINDS_USING_SECOND_DISTANCE"] = MateKindsUsingSecond

# this binding exists because shared behavior needs one stable value
globals()["MATE_KIND_BY_JOINT_TYPE"] = MateKindByJointType

# this binding exists because shared behavior needs one stable value
globals()["MATE_WRITE_KINDS"] = MateWriteKinds

# this binding exists because shared behavior needs one stable value
globals()["MATE_WRITE_TYPES"] = MateWriteTypes

# this binding exists because shared behavior needs one stable value
globals()["MIDPOINT_REFERENCE_POINT_NAMES"] = MidpointRefPointNames

# this binding exists because shared behavior needs one stable value
globals()["Mesh"] = MeshRecord

# this binding exists because shared behavior needs one stable value
globals()["NATIVE_CAPABILITIES"] = NativeCapabilities

# this binding exists because shared behavior needs one stable value
globals()["NEUTRAL_GEOMETRY_TYPE_BY_KIND"] = NeutralGeomTypeByKind

# this binding exists because shared behavior needs one stable value
globals()["NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND"] = NeutralGeomTypeIdByKind

# this binding exists because shared behavior needs one stable value
globals()["NON_FEATURE_OBJECT_TYPE_IDS"] = NonFeatureObjectTypeIds

# this binding exists because shared behavior needs one stable value
globals()["NativeGeometry"] = NativeGeom

# this binding exists because shared behavior needs one stable value
globals()["PART_CONTAINER_TYPE_IDS"] = PartContainerTypeIds

# this binding exists because shared behavior needs one stable value
globals()["PART_OBJECT_TYPE_IDS"] = PartObjectTypeIds

# this binding exists because shared behavior needs one stable value
globals()["PERMISSIVE_TRUE_VALUES"] = PermissiveTrueValues

# this binding exists because shared behavior needs one stable value
globals()["POCKET_TYPE_ID"] = PocketTypeId

# this binding exists because shared behavior needs one stable value
globals()["PRIMITIVE_FEATURE_FAMILIES"] = PrimitiveFeatureFamilies

# this binding exists because shared behavior needs one stable value
globals()["PRIMITIVE_FEATURE_TYPE_IDS"] = PrimitiveFeatureTypeIds

# this binding exists because shared behavior needs one stable value
globals()["ParabolaGeometry"] = ParabolaGeom

# this binding exists because shared behavior needs one stable value
globals()["Parameter"] = Param

# this binding exists because shared behavior needs one stable value
globals()["ParameterValue"] = ParamValue

# this binding exists because shared behavior needs one stable value
globals()["Path"] = FilePath

# this binding exists because shared behavior needs one stable value
globals()["PointGeometry"] = PointGeom

# this binding exists because shared behavior needs one stable value
globals()["QUANTITY_PROPERTY_UNITS"] = QuantityPropUnits

# this binding exists because shared behavior needs one stable value
globals()["REGISTERED_PART_OBJECT_TYPE_IDS"] = RegisteredPartObjectType

# this binding exists because shared behavior needs one stable value
globals()["SAMPLE"] = KSample

# this binding exists because shared behavior needs one stable value
globals()["SCALAR_PROPERTY_KINDS"] = ScalarPropKinds

# this binding exists because shared behavior needs one stable value
globals()["SCALAR_PROPERTY_TYPES"] = ScalarPropTypes

# this binding exists because shared behavior needs one stable value
globals()["SKETCH_TYPE_ID"] = SketchTypeId

# this binding exists because shared behavior needs one stable value
globals()["SPLINE_CONTROL_TAGS"] = SplineControlTags

# this binding exists because shared behavior needs one stable value
globals()["SPLINE_GEOMETRY_KINDS"] = SplineGeomKinds

# this binding exists because shared behavior needs one stable value
globals()["SPLINE_GEOMETRY_TYPE_IDS"] = SplineGeomTypeIds

# this binding exists because shared behavior needs one stable value
globals()["STRING_HASHER_TAGS"] = StringHasherTags

# this binding exists because shared behavior needs one stable value
globals()["SUBELEMENT_KIND_BY_PREFIX"] = SubElemKindByPrefix

# this binding exists because shared behavior needs one stable value
globals()["SUBELEMENT_MATE_ENTITY_KINDS"] = SubElemMateEntityKinds

# this binding exists because shared behavior needs one stable value
globals()["SUFFIX"] = Suffix

# this binding exists because shared behavior needs one stable value
globals()["SUPPORT_PLANE_TYPE_IDS"] = SupportPlaneTypeIds

# this binding exists because shared behavior needs one stable value
globals()["SelectionPathElement"] = SelectionPathElem

# this binding exists because shared behavior needs one stable value
globals()["SketchConstraint"] = SketchRule

# this binding exists because shared behavior needs one stable value
globals()["Vector2"] = VectorTwo

# this binding exists because shared behavior needs one stable value
globals()["Vector3"] = VectorThree

# this binding exists because shared behavior needs one stable value
globals()["XML_TRUE_VALUES"] = XmlTrueValues

# this binding exists because shared behavior needs one stable value
globals()["_filtered_document"] = FilteredDoc

# this binding exists because shared behavior needs one stable value
globals()["_forged_native_brep_document"] = ForgedNativeDoc

# this binding exists because shared behavior needs one stable value
globals()["_line_entity"] = LineEntity

# this binding exists because shared behavior needs one stable value
globals()["_mesh_kernel_fixture"] = MeshKernel

# this binding exists because shared behavior needs one stable value
globals()["_native_archive"] = NativeArchive

# this binding exists because shared behavior needs one stable value
globals()["_native_assembly_fixture"] = NativeAsm

# this binding exists because shared behavior needs one stable value
globals()["_native_external_assembly_fixture"] = NativeOuterAsm

# this binding exists because shared behavior needs one stable value
globals()["_native_link_list"] = NativeLinkList

# this binding exists because shared behavior needs one stable value
globals()["_native_link_only_fixture"] = NativeLinkOnly

# this binding exists because shared behavior needs one stable value
globals()["_native_mesh_fixture"] = NativeMesh

# this binding exists because shared behavior needs one stable value
globals()["_native_part_fixture"] = NativePart

# this binding exists because shared behavior needs one stable value
globals()["_native_placement"] = NativePlacement

# this binding exists because shared behavior needs one stable value
globals()["_native_property"] = NativeProp

# this binding exists because shared behavior needs one stable value
globals()["_native_xlink"] = NativeXlink

# this binding exists because shared behavior needs one stable value
globals()["_rewrite_document_xml"] = RewriteDocXml

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["base64"] = BaseSixFour

# this binding exists because shared behavior needs one stable value
globals()["brep_model_brep"] = BrepModelBrep

# this binding exists because shared behavior needs one stable value
globals()["build_fcstd_archive"] = BuildFcstdArchive

# this binding exists because shared behavior needs one stable value
globals()["convert"] = Convert

# this binding exists because shared behavior needs one stable value
globals()["document_to_manifest"] = DocToManifest

# this binding exists because shared behavior needs one stable value
globals()["freecad_adapter_module"] = FreecadAdapterModule

# this binding exists because shared behavior needs one stable value
globals()["freecad_archive_module"] = FreecadArchiveModule

# this binding exists because shared behavior needs one stable value
globals()["freecad_native_module"] = FreecadNativeModule

# this binding exists because shared behavior needs one stable value
globals()["hashlib"] = Hashlib

# this binding exists because shared behavior needs one stable value
globals()["inspect"] = Inspect

# this binding exists because shared behavior needs one stable value
globals()["io"] = IoStream

# this binding exists because shared behavior needs one stable value
globals()["is_structurally_valid_ascii_brep"] = IsStructurallyValidAscii

# this binding exists because shared behavior needs one stable value
globals()["json"] = JsonValue

# this binding exists because shared behavior needs one stable value
globals()["math"] = MathValue

# this binding exists because shared behavior needs one stable value
globals()["neutral_document"] = NeutralDoc

# this binding exists because shared behavior needs one stable value
globals()["open_document"] = OpenDoc

# this binding exists because shared behavior needs one stable value
globals()["pytest"] = Pytest

# this binding exists because shared behavior needs one stable value
globals()["registry"] = Registry

# this binding exists because shared behavior needs one stable value
globals()["replace"] = Replace

# this binding exists because shared behavior needs one stable value
globals()["struct"] = Struct

# this binding exists because shared behavior needs one stable value
globals()["triangle_brep"] = TriangleBrep

# this binding exists because shared behavior needs one stable value
globals()["write_document"] = WriteDoc

# this binding exists because shared behavior needs one stable value
globals()["zipfile"] = Zipfile

# this binding exists because shared behavior needs one stable value
globals()["zlib"] = ZlibValue
