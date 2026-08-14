# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass, replace as Replace
import hashlib as Hashlib
import json as JsonValue
import math as MathValue
from pathlib import Path as FilePath, PurePosixPath
import re as RegexLib
import struct as Struct
from typing import Any as AnyValue
import xml.etree.ElementTree as XmlTree
import zipfile as Zipfile
from interchange import (
    ArcEllipseGeometry as ArcEllipseGeom,
    ArcGeometry as ArcGeom,
    ArcHyperbolaGeometry as ArcHyperbolaGeom,
    ArcParabolaGeometry as ArcParabolaGeom,
    AssemblyData as AsmData,
    Body as BodyValue,
    BooleanOperation as BoolOperation,
    BrepModel,
    BrepPayload,
    CadDocument as CadDoc,
    CadSource,
    Capability,
    ChamferFeature,
    CircleGeometry as CircleGeom,
    CircularPatternFeature,
    ComponentDefinition,
    ComponentDocument as ComponentDoc,
    ComponentInstance,
    ComponentKind,
    Configuration as Config,
    ConstraintKind as RuleKind,
    ConstraintReference as RuleRef,
    Diagnostic as DiagValue,
    EllipseGeometry as EllipseGeom,
    Expression,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureDefinition,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    GeometryKind as GeomKind,
    HyperbolaGeometry as HyperbolaGeom,
    LineGeometry as LineGeom,
    LinearPatternFeature,
    MateConstraint as MateRule,
    MateEntity,
    MateEntityKind,
    MateGroup,
    MateKind,
    Matrix4 as MatrixFour,
    Mesh as MeshValue,
    NativeGeometry as NativeGeom,
    NativeFeatureDefinition,
    Parameter as Param,
    ParameterValue as ParamValue,
    ParabolaGeometry as ParabolaGeom,
    PayloadRole,
    PointGeometry as PointGeom,
    Provenance,
    ProvenanceSpan,
    Selection,
    SelectionPathElement as SelectionPathElem,
    Severity,
    ShellFeature,
    Sketch,
    SketchConstraint as SketchRule,
    SketchEntity,
    SplineGeometry as SplineGeom,
    SupportPlane,
    TopologySummary,
    Transform,
    ValueKind,
    Vector2 as VectorTwo,
    Vector3 as VectorThree,
    infer_capabilities as InferCapabilities,
)
from convert.geometry.Opencascade import decode_ascii_brep as DecodeAsciiBrep
from convert.adapters.freecad.Archive import (
    DOCUMENT_ENTRY as DocEntry,
    NATIVE_DOCUMENT_SHA256_ATTRIBUTE as KNativeDocHashAttr,
    _MAX_ENTRY_SIZE as MaxEntrySize,
    _MAX_EXTERNAL_FILES as MaxOuterFiles,
    _MAX_TOTAL_SIZE as MaxTotalSize,
    _validated_archive_members as ValidatedArchiveMembers,
    _validated_document_xml as ValidatedDocXml,
    _validated_entry_name as ValidatedEntryName,
    _validated_object_name as ValidatedObjectName,
    extract_manifest_from_fcstd as ExtractManifestFromFcstd,
)
from convert.adapters.freecad.Format import FORMAT_ID as FormatId, SUFFIX as Suffix
from convert.adapters.freecad.Protocol import (
    ASSEMBLY_JOINT_GROUP_TYPE_ID as AsmJointGroupTypeId,
    ASSEMBLY_OBJECT_TYPE_PREFIX as AsmObjectTypePrefix,
    ASSEMBLY_ROOT_TYPE_ID as AsmRootTypeId,
    BODY_CONTAINER_TYPE_IDS as BodyContainerTypeIds,
    CONSTRAINT_KIND_BY_CODE as RuleKindByCode,
    CONSTRAINT_POINT_BY_INDEX as RulePointByIndex,
    CONSTRAINT_VALUE_KIND_BY_CODE as RuleValueKindByCode,
    DIMENSIONAL_CONSTRAINT_CODES as DimensionalRuleCodes,
    EXTRUSION_TYPE_BY_CODE as ExtrusionTypeByCode,
    FEATURE_KIND_BY_TYPE_ID as FeatureKindByTypeId,
    GEOMETRY_KIND_BY_TYPE_ID as GeomKindByTypeId,
    JOINT_GROUND_PROPERTY as JointGroundProp,
    JOINT_REFERENCE_PROPERTIES as JointRefProperties,
    JOINT_RESERVED_LINK_PROPERTIES as JointReservedLink,
    JOINT_TYPE_PROPERTIES as JointTypeProperties,
    MATE_KIND_BY_JOINT_TYPE as MateKindByJointType,
    MATE_KINDS_USING_DISTANCE as MateKindsUsingDistance,
    MATE_KINDS_USING_SECOND_DISTANCE as MateKindsUsingSecond,
    NON_FEATURE_OBJECT_TYPE_IDS as NonFeatureObjectTypeIds,
    PERMISSIVE_TRUE_VALUES as PermissiveTrueValues,
    POCKET_TYPE_ID as PocketTypeId,
    PRIMITIVE_FEATURE_TYPE_IDS as PrimitiveFeatureTypeIds,
    SCALAR_PROPERTY_KINDS as ScalarPropKinds,
    SKETCH_TYPE_ID as SketchTypeId,
    SPLINE_GEOMETRY_TYPE_IDS as SplineGeomTypeIds,
    STRING_HASHER_TAGS as StringHasherTags,
    SUBELEMENT_KIND_BY_PREFIX as SubElemKindByPrefix,
    SUPPORT_PLANE_TYPE_IDS as SupportPlaneTypeIds,
    XML_TRUE_VALUES as XmlTrueValues,
)

# this binding exists because shared behavior needs one stable value
KMaxOuterDepth = 16

# this binding exists because shared behavior needs one stable value
KMinObjectGraphSchema = 2

# this binding exists because shared behavior needs one stable value
KGrooveTypeId = "PartDesign::Groove"

# this binding exists because shared behavior needs one stable value
KSubtractiveTypeIds = frozenset({PocketTypeId, KGrooveTypeId})

# this binding exists because shared behavior needs one stable value
KSubtractiveCapableKinds = frozenset({FeatureKind.EXTRUSION, FeatureKind.REVOLUTION})


# this definition exists because focused behavior needs one stable owner
class NativeFreeCad(ValueError):
    KSlots = ()


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class NativeObject:
    locals().setdefault("__annotations__", {})
    __annotations__["name"] = "str"
    __annotations__["type_id"] = "str"
    __annotations__["index"] = "int"
    __annotations__["object_id"] = "str"
    __annotations__["touched"] = "bool"
    __annotations__["dependencies"] = "tuple[str, ...]"
    __annotations__["extensions"] = "tuple[XmlTree.Element, ...]"
    __annotations__["transient_properties"] = "tuple[XmlTree.Element, ...]"
    __annotations__["properties"] = "dict[str, XmlTree.Element]"


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class NativeArchive:
    locals().setdefault("__annotations__", {})
    __annotations__["root"] = "XmlTree.Element"
    __annotations__["objects"] = "tuple[NativeObject, ...]"
    __annotations__["entries"] = "dict[str, bytes]"
    __annotations__["document_xml"] = "bytes"
    __annotations__["entry_order"] = "tuple[str, ...]"


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class OuterState:
    locals().setdefault("__annotations__", {})
    __annotations__["root"] = "FilePath"
    __annotations__["cache"] = "dict[FilePath, CadDoc]"
    __annotations__["active"] = "set[FilePath]"
    __annotations__["FileCount"] = "int"
    __annotations__["TotalBytes"] = "int"


# this definition exists because focused behavior needs one stable owner
def EntryName(NameValue: str) -> str:
    try:
        return ValidatedEntryName(NameValue)
    except ValueError as ErrorInfo:
        raise NativeFreeCad(str(ErrorInfo)) from ErrorInfo


# this definition exists because focused behavior needs one stable owner
def DeclaredCount(NodeValue: ET.Element, Actual: int, Label: str) -> None:
    Value = NodeValue.get("Count", NodeValue.get("count"))
    if Value is None:
        return
    try:
        Expected = int(Value)
    except ValueError as ErrorInfo:
        raise NativeFreeCad(f"FreeCAD {Label} count is invalid") from ErrorInfo
    if Expected != Actual:
        raise NativeFreeCad(f"FreeCAD {Label} count does not match its data")


# this definition exists because focused behavior needs one stable owner
def ArchiveMembers(
    DataValue: bytes,
) -> tuple[Zipfile.ZipFile, dict[str, Zipfile.ZipInfo]]:
    try:
        return ValidatedArchiveMembers(DataValue)
    except ValueError as ErrorInfo:
        raise NativeFreeCad(str(ErrorInfo)) from ErrorInfo


# this definition exists because focused behavior needs one stable owner
def StoredCount(NodeValue: ET.Element, NameValue: str, Actual: int, Label: str) -> None:
    Value = NodeValue.get(NameValue)
    if Value is None:
        return
    try:
        Expected = int(Value)
    except ValueError as ErrorInfo:
        raise NativeFreeCad(f"FreeCAD {Label} count is invalid") from ErrorInfo
    if Expected != Actual:
        raise NativeFreeCad(f"FreeCAD {Label} count does not match its data")


# this definition validates and indexes native object declarations
def ParseDecls(ObjectsNode: ET.Element) -> dict[str, tuple[str, int, str, bool]]:
    Declarations = ObjectsNode.findall("./Object")
    DeclaredCount(ObjectsNode, len(Declarations), "object")
    DeclByName: dict[str, tuple[str, int, str, bool]] = {}
    IdsValue: set[str] = set()
    for Index, NodeValue in enumerate(Declarations):
        NameValue = NodeValue.get("name", "")
        TypeId = NodeValue.get("type", "")
        ObjectId = NodeValue.get("id", "")
        if not NameValue or not TypeId or NameValue in DeclByName:
            raise NativeFreeCad("FreeCAD object declarations are malformed")
        try:
            ValidatedObjectName(NameValue)
        except ValueError as ErrorInfo:
            raise NativeFreeCad(str(ErrorInfo)) from ErrorInfo
        if ObjectId and ObjectId in IdsValue:
            raise NativeFreeCad("FreeCAD object declarations contain duplicate ids")
        if ObjectId:
            IdsValue.add(ObjectId)
        DeclByName[NameValue] = (
            TypeId,
            Index,
            ObjectId,
            NodeValue.get("Touched") == "1",
        )
    return DeclByName


# this definition validates and indexes native object data records
def ParseDataMap(DataNode: ET.Element) -> dict[str, ET.Element]:
    ObjectData = DataNode.findall("./Object")
    DeclaredCount(DataNode, len(ObjectData), "object data")
    DataByName: dict[str, XmlTree.Element] = {}
    for NodeValue in ObjectData:
        NameValue = NodeValue.get("name", "")
        if not NameValue or NameValue in DataByName:
            raise NativeFreeCad("FreeCAD object data contains duplicate names")
        DataByName[NameValue] = NodeValue
    return DataByName


# this definition validates native object dependency relationships
def ParseDeps(
    ObjectsNode: ET.Element, DeclByName: Mapping[str, AnyValue]
) -> dict[str, tuple[str, ...]]:
    Dependencies: dict[str, tuple[str, ...]] = {}
    for NodeValue in ObjectsNode.findall("./ObjectDeps"):
        NameValue = NodeValue.get("Name", "")
        if not NameValue or NameValue in Dependencies or NameValue not in DeclByName:
            raise NativeFreeCad("FreeCAD dependency graph is malformed")
        Values = tuple(
            (ItemValue.get("Name", "") for ItemValue in NodeValue.findall("./Dep"))
        )
        if any((not Value or Value not in DeclByName for Value in Values)):
            raise NativeFreeCad("FreeCAD dependency graph has missing objects")
        DeclaredCount(NodeValue, len(Values), "dependency")
        Dependencies[NameValue] = Values
    return Dependencies


# this definition validates and indexes one native objects persistent properties
def ParseProps(
    NameValue: str, ObjectElem: ET.Element
) -> tuple[tuple[ET.Element, ...], dict[str, ET.Element]]:
    PropertiesElem = ObjectElem.find("./Properties")
    if PropertiesElem is None:
        raise NativeFreeCad(f"FreeCAD object {NameValue!r} has no properties")
    Properties = PropertiesElem.findall("./Property")
    Transient = tuple(PropertiesElem.findall("./_Property"))
    StoredCount(PropertiesElem, "Count", len(Properties), "property")
    StoredCount(PropertiesElem, "TransientCount", len(Transient), "transient property")
    PropNodes: dict[str, ET.Element] = {}
    for NodeValue in Properties:
        PropName = NodeValue.get("name", "")
        if not PropName or PropName in PropNodes:
            raise NativeFreeCad(
                f"FreeCAD object {NameValue!r} has malformed properties"
            )
        PropNodes[PropName] = NodeValue
    return (Transient, PropNodes)


# this definition combines validated declarations data dependencies and properties
def ParseObjects(RootValue: ET.Element) -> tuple[NativeObject, ...]:
    ObjectsNode = RootValue.find("./Objects")
    DataNode = RootValue.find("./ObjectData")
    if ObjectsNode is None or DataNode is None:
        raise NativeFreeCad("FreeCAD Document.xml has no object graph")
    DeclByName = ParseDecls(ObjectsNode)
    DataByName = ParseDataMap(DataNode)
    if set(DeclByName) != set(DataByName):
        raise NativeFreeCad("FreeCAD object declarations and data do not match")
    Dependencies = ParseDeps(ObjectsNode, DeclByName)
    Result: list[NativeObject] = []
    for NameValue, (TypeId, Index, ObjectId, Touched) in DeclByName.items():
        ObjectElem = DataByName[NameValue]
        TransientProperties, PropNodes = ParseProps(NameValue, ObjectElem)
        Result.append(
            NativeObject(
                NameValue,
                TypeId,
                Index,
                ObjectId,
                Touched,
                Dependencies.get(NameValue, ()),
                tuple(ObjectElem.findall("./Extensions/Extension")),
                TransientProperties,
                PropNodes,
            )
        )
    return tuple(Result)


# this definition validates every sidecar name referenced by document xml
def ReferencedNames(
    RootValue: ET.Element, Members: Mapping[str, Zipfile.ZipInfo]
) -> set[str]:
    Referenced: set[str] = set()
    for NodeValue in RootValue.findall(".//*[@file]"):
        if NodeValue.tag == "XLink":
            continue
        FileName = NodeValue.get("file", "")
        if FileName:
            Referenced.add(EntryName(FileName))
    Missing = sorted(Referenced.difference(Members))
    if Missing:
        raise NativeFreeCad(
            "FCStd archive is missing referenced data: " + ", ".join(Missing)
        )
    return Referenced


# this definition reads validated sidecars while normalizing archive errors
def ReadEntries(
    Archive: Zipfile.ZipFile,
    Members: Mapping[str, Zipfile.ZipInfo],
    Referenced: set[str],
) -> dict[str, bytes]:
    try:
        return {NameValue: Archive.read(Members[NameValue]) for NameValue in Referenced}
    except (
        OSError,
        RuntimeError,
        NotImplementedError,
        Zipfile.BadZipFile,
    ) as ErrorInfo:
        raise NativeFreeCad(
            "FCStd archive contains unreadable referenced data"
        ) from ErrorInfo


# this definition loads and validates a native freecad object graph
def LoadNative(DataValue: bytes, *, LoadEntries: bool = True) -> NativeArchive:
    Archive, Members = ArchiveMembers(DataValue)
    with Archive:
        try:
            RootValue, DocXml = ValidatedDocXml(Archive, Members)
        except ValueError as ErrorInfo:
            raise NativeFreeCad(str(ErrorInfo)) from ErrorInfo
        try:
            SchemaVersion = int(RootValue.get("SchemaVersion", ""))
        except ValueError as ErrorInfo:
            raise NativeFreeCad("FreeCAD schema version is invalid") from ErrorInfo
        if SchemaVersion < KMinObjectGraphSchema:
            raise NativeFreeCad("FreeCAD schema version is not supported")
        Objects = ParseObjects(RootValue)
        Referenced = ReferencedNames(RootValue, Members)
        Entries = ReadEntries(Archive, Members, Referenced) if LoadEntries else {}
    return NativeArchive(
        RootValue,
        Objects,
        Entries,
        DocXml,
        tuple((NameValue for NameValue in Members if NameValue in Referenced)),
    )


# this definition exists because focused behavior needs one stable owner
def ProbeNative(DataValue: bytes) -> tuple[float, str]:
    try:
        Native = LoadNative(DataValue, LoadEntries=False)
    except NativeFreeCad as ErrorInfo:
        return (0.0, str(ErrorInfo))
    return (0.95, f"native FreeCAD schema {Native.root.get('SchemaVersion')} document")


# this definition exists because focused behavior needs one stable owner
def ElemData(NodeValue: ET.Element) -> dict[str, AnyValue]:
    Result: dict[str, AnyValue] = {
        "tag": NodeValue.tag,
        "attributes": dict(sorted(NodeValue.attrib.items())),
    }
    TextValue = (NodeValue.text or "").strip()
    if TextValue:
        Result["text"] = TextValue
    Children = [ElemData(Child) for Child in NodeValue]
    if Children:
        Result["children"] = Children
    return Result


# this definition exists because focused behavior needs one stable owner
def NativeObjectA(ObjValue: _NativeObject) -> dict[str, AnyValue]:
    return {
        "name": ObjValue.name,
        "type_id": ObjValue.type_id,
        "order": ObjValue.index,
        "object_id": ObjValue.object_id,
        "touched": ObjValue.touched,
        "dependencies": list(ObjValue.dependencies),
        "extensions": [ElemData(NodeValue) for NodeValue in ObjValue.extensions],
        "transient_properties": [
            ElemData(NodeValue) for NodeValue in ObjValue.transient_properties
        ],
        "property_order": list(ObjValue.properties),
        "properties": {
            NameValue: ElemData(NodeValue)
            for NameValue, NodeValue in ObjValue.properties.items()
        },
    }


# this definition exists because focused behavior needs one stable owner
def ReadStringHash(Native: _NativeArchive) -> dict[str, AnyValue] | None:
    Nodes = [
        ElemData(NodeValue)
        for NodeValue in Native.root
        if NodeValue.tag in StringHasherTags
    ]
    Entries: list[dict[str, AnyValue]] = []
    for NodeValue in Native.root:
        if NodeValue.tag not in StringHasherTags:
            continue
        for Child in NodeValue.iter():
            FileName = Child.get("file", "")
            if FileName and FileName in Native.entries:
                Entries.append(
                    {"source_stream": FileName, "data": Native.entries[FileName]}
                )
    AttrValue = Native.root.get("StringHasher", "")
    if not AttrValue and (not Nodes) and (not Entries):
        return None
    return {"attribute": AttrValue, "nodes": Nodes, "entries": Entries}


# this definition exists because focused behavior needs one stable owner
def OtherEntryData(Native: _NativeArchive) -> list[dict[str, AnyValue]]:
    Represented: set[str] = set()
    for ObjValue in Native.objects:
        for NodeValue in ObjValue.properties.values():
            if NodeValue.find("./Part") is None:
                continue
            Represented.update(
                (
                    FileName
                    for Child in NodeValue.findall(".//*[@file]")
                    if (FileName := Child.get("file", ""))
                )
            )
    for NodeValue in Native.root:
        if NodeValue.tag not in StringHasherTags:
            continue
        Represented.update(
            (
                FileName
                for Child in NodeValue.iter()
                if (FileName := Child.get("file", ""))
            )
        )
    return [
        {"source_stream": NameValue, "data": Native.entries[NameValue]}
        for NameValue in Native.entry_order
        if NameValue in Native.entries and NameValue not in Represented
    ]


# this definition exists because focused behavior needs one stable owner
def NativePayloads(
    Native: _NativeArchive, DataValue: bytes, SourcePath: str
) -> tuple[BrepPayload, BrepPayload]:
    NativeDigest = Hashlib.sha256(DataValue).digest()
    NativeName = FilePath(SourcePath).name if SourcePath else f"Document{Suffix}"
    DocValue = BrepPayload(
        "freecad:native-document",
        FormatId,
        "native_document",
        f"FreeCAD Schema {Native.root.get('SchemaVersion', '')}",
        NativeDigest.hex(),
        data=DataValue,
        source_stream=NativeName,
        provenance=Provenance(
            FormatId,
            DocEntry,
            spans=(ProvenanceSpan(DocEntry, 0, len(Native.document_xml), "xml"),),
        ),
        attributes={
            "object_count": len(Native.objects),
            "entry_order": list(Native.entry_order),
        },
        role=PayloadRole.DOCUMENT,
        file_extension=Suffix,
    )
    Binding = BrepPayload(
        "freecad:native-document-binding",
        f"{FormatId}.sha256",
        "native_document_binding",
        "sha256",
        Hashlib.sha256(NativeDigest).hexdigest(),
        data=NativeDigest,
        source_stream=NativeName,
        provenance=Provenance(FormatId, NativeDigest.hex()),
        role=PayloadRole.VERIFICATION,
        file_extension=".sha256",
    )
    return (DocValue, Binding)


# this definition exists because focused behavior needs one stable owner
def FindChild(
    ObjValue: _NativeObject, NameValue: str, TagValue: str | None = None
) -> XmlTree.Element | None:
    NodeValue = ObjValue.properties.get(NameValue)
    if NodeValue is None:
        return None
    if TagValue is not None:
        return NodeValue.find(f"./{TagValue}")
    return next(iter(NodeValue), None)


# this definition exists because focused behavior needs one stable owner
def Number(Value: str | None, Default: float = 0.0) -> float:
    try:
        Result = float(Value)
    except (TypeError, ValueError):
        return Default
    return Result if MathValue.isfinite(Result) else Default


# this definition exists because focused behavior needs one stable owner
def Integer(Value: str | None, Default: int = 0) -> int:
    try:
        return int(Value)
    except (TypeError, ValueError):
        return Default


# this definition exists because focused behavior needs one stable owner
def String(ObjValue: _NativeObject, NameValue: str, Default: str = "") -> str:
    NodeValue = FindChild(ObjValue, NameValue, "String")
    return Default if NodeValue is None else NodeValue.get("value", Default)


# this definition exists because focused behavior needs one stable owner
def IsBoolValue(ObjValue: _NativeObject, NameValue: str, Default: bool = False) -> bool:
    NodeValue = FindChild(ObjValue, NameValue, "Bool")
    if NodeValue is None:
        return Default
    return NodeValue.get("value", "false").casefold() in PermissiveTrueValues


# this definition exists because focused behavior needs one stable owner
def Float(ObjValue: _NativeObject, NameValue: str, Default: float = 0.0) -> float:
    NodeValue = FindChild(ObjValue, NameValue, "Float")
    return Default if NodeValue is None else Number(NodeValue.get("value"), Default)


# this definition exists because focused behavior needs one stable owner
def EnumAction(ObjValue: _NativeObject, NameValue: str, Default: int = 0) -> int:
    NodeValue = FindChild(ObjValue, NameValue, "Integer")
    return Default if NodeValue is None else Integer(NodeValue.get("value"), Default)


# this definition exists because focused behavior needs one stable owner
def LinkAction(ObjValue: _NativeObject, NameValue: str) -> str:
    NodeValue = ObjValue.properties.get(NameValue)
    if NodeValue is None:
        return ""
    Child = NodeValue.find("./Link")
    if Child is not None:
        return Child.get("value", "")
    Child = NodeValue.find("./LinkSub")
    if Child is not None:
        return Child.get("value", "")
    Child = NodeValue.find("./XLink")
    if Child is not None:
        return Child.get("name", "")
    return ""


# this definition exists because focused behavior needs one stable owner
def LinkList(ObjValue: _NativeObject, NameValue: str) -> tuple[str, ...]:
    NodeValue = ObjValue.properties.get(NameValue)
    if NodeValue is None:
        return ()
    Values: list[str] = []
    for PathValue, AttrValue in (
        ("./LinkList/Link", "value"),
        ("./XLinkList/XLink", "name"),
        ("./LinkSubList/Link", "obj"),
    ):
        Values.extend(
            (
                Value
                for Child in NodeValue.findall(PathValue)
                if (Value := Child.get(AttrValue, ""))
            )
        )
    return tuple(Values)


# this definition exists because focused behavior needs one stable owner
def PlacementElem(ObjValue: _NativeObject, NameValue: str) -> XmlTree.Element | None:
    return FindChild(ObjValue, NameValue, "PropertyPlacement")


# this definition exists because focused behavior needs one stable owner
def PlacementMatrix(NodeValue: ET.Element | None) -> tuple[float, ...]:
    if NodeValue is None:
        return (
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
        )
    FirstCoord = Number(NodeValue.get("Q0"))
    SecondCoord = Number(NodeValue.get("Q1"))
    ThirdCoord = Number(NodeValue.get("Q2"))
    WidthValue = Number(NodeValue.get("Q3"), 1.0)
    NormValue = MathValue.sqrt(
        FirstCoord * FirstCoord
        + SecondCoord * SecondCoord
        + ThirdCoord * ThirdCoord
        + WidthValue * WidthValue
    )
    if NormValue <= 1e-15:
        FirstCoord, SecondCoord, ThirdCoord, WidthValue = (0.0, 0.0, 0.0, 1.0)
    else:
        FirstCoord, SecondCoord, ThirdCoord, WidthValue = (
            FirstCoord / NormValue,
            SecondCoord / NormValue,
            ThirdCoord / NormValue,
            WidthValue / NormValue,
        )
    return (
        1.0 - 2.0 * (SecondCoord * SecondCoord + ThirdCoord * ThirdCoord),
        2.0 * (FirstCoord * SecondCoord - ThirdCoord * WidthValue),
        2.0 * (FirstCoord * ThirdCoord + SecondCoord * WidthValue),
        Number(NodeValue.get("Px")),
        2.0 * (FirstCoord * SecondCoord + ThirdCoord * WidthValue),
        1.0 - 2.0 * (FirstCoord * FirstCoord + ThirdCoord * ThirdCoord),
        2.0 * (SecondCoord * ThirdCoord - FirstCoord * WidthValue),
        Number(NodeValue.get("Py")),
        2.0 * (FirstCoord * ThirdCoord - SecondCoord * WidthValue),
        2.0 * (SecondCoord * ThirdCoord + FirstCoord * WidthValue),
        1.0 - 2.0 * (FirstCoord * FirstCoord + SecondCoord * SecondCoord),
        Number(NodeValue.get("Pz")),
        0.0,
        0.0,
        0.0,
        1.0,
    )


# this definition exists because focused behavior needs one stable owner
def TransformA(NodeValue: ET.Element | None) -> Transform:
    Values = PlacementMatrix(NodeValue)
    return Transform(
        origin=VectorThree(Values[3], Values[7], Values[11]),
        x_axis=VectorThree(Values[0], Values[4], Values[8]),
        y_axis=VectorThree(Values[1], Values[5], Values[9]),
        z_axis=VectorThree(Values[2], Values[6], Values[10]),
    )


# this definition exists because focused behavior needs one stable owner
def ReadExpressions(ObjValue: _NativeObject) -> dict[str, str]:
    NodeValue = ObjValue.properties.get("ExpressionEngine")
    if NodeValue is None:
        return {}
    Values: dict[str, str] = {}
    for Child in NodeValue.findall("./ExpressionEngine/Expression"):
        PathValue = Child.get("path", "").lstrip(".")
        Expression = Child.get("expression", "")
        if PathValue and Expression:
            Values[PathValue] = Expression
    return Values


# this definition exists because focused behavior needs one stable owner
def PropParamValue(NodeValue: ET.Element) -> ParamValue | None:
    TypeId = NodeValue.get("type", "")
    if TypeId == "App::PropertyEnumeration":
        Child = NodeValue.find("./Integer")
        if Child is None:
            return None
        Choices = [
            ItemValue.get("value", "")
            for ItemValue in NodeValue.findall("./CustomEnumList/Enum")
        ]
        Index = Integer(Child.get("value"))
        Value: str | int = Choices[Index] if 0 <= Index < len(Choices) else Index
        return ParamValue(Value, ValueKind.STRING if Choices else ValueKind.INTEGER)
    KindAndUnit = ScalarPropKinds.get(TypeId)
    if KindAndUnit is None:
        return None
    KindValue, UnitValue, TagValue = KindAndUnit
    Child = NodeValue.find(f"./{TagValue}")
    if Child is None:
        return None
    if KindValue == ValueKind.BOOLEAN:
        Value = Child.get("value", "false").casefold() in PermissiveTrueValues
    elif KindValue == ValueKind.INTEGER:
        Value = Integer(Child.get("value"))
    elif KindValue == ValueKind.STRING:
        Value = Child.get("value", "")
    elif TagValue == "Integer":
        Value = Integer(Child.get("value"))
    else:
        Value = Number(Child.get("value"))
    return ParamValue(Value, KindValue, UnitValue)


# this definition decodes one line segment geometry record
def LineAction(NodeValue: ET.Element) -> tuple[GeomKind, AnyValue] | None:
    Value = NodeValue.find("./LineSegment")
    if Value is None:
        return None
    StartValue = VectorTwo(Number(Value.get("StartX")), Number(Value.get("StartY")))
    EndValue = VectorTwo(Number(Value.get("EndX")), Number(Value.get("EndY")))
    return (GeomKind.LINE, LineGeom(StartValue, EndValue))


# this definition decodes one circle geometry record
def CircleAction(NodeValue: ET.Element) -> tuple[GeomKind, AnyValue] | None:
    Value = NodeValue.find("./Circle")
    if Value is None:
        return None
    Center = VectorTwo(Number(Value.get("CenterX")), Number(Value.get("CenterY")))
    return (GeomKind.CIRCLE, CircleGeom(Center, abs(Number(Value.get("Radius")))))


# this definition decodes one circular arc geometry record
def ArcAction(NodeValue: ET.Element) -> tuple[GeomKind, AnyValue] | None:
    Value = NodeValue.find("./ArcOfCircle")
    if Value is None:
        return None
    Center = VectorTwo(Number(Value.get("CenterX")), Number(Value.get("CenterY")))
    return (
        GeomKind.ARC,
        ArcGeom(
            Center,
            abs(Number(Value.get("Radius"))),
            Number(Value.get("StartAngle")),
            Number(Value.get("EndAngle")),
        ),
    )


# this definition decodes one point geometry record
def PointAction(NodeValue: ET.Element) -> tuple[GeomKind, AnyValue] | None:
    Value = NodeValue.find("./GeomPoint")
    if Value is None:
        Value = NodeValue.find("./Point")
    if Value is None:
        return None
    PointValue = VectorTwo(Number(Value.get("X")), Number(Value.get("Y")))
    return (GeomKind.POINT, PointGeom(PointValue))


# this definition decodes complete and trimmed ellipse geometry records
def EllipseAction(
    NodeValue: ET.Element, TypeId: str
) -> tuple[GeomKind, AnyValue] | None:
    IsArc = TypeId == "Part::GeomArcOfEllipse"
    Value = NodeValue.find("./ArcOfEllipse" if IsArc else "./Ellipse")
    if Value is None:
        return None
    Arguments = (
        VectorTwo(Number(Value.get("CenterX")), Number(Value.get("CenterY"))),
        GeomAxis(Value),
        abs(Number(Value.get("MajorRadius"))),
        abs(Number(Value.get("MinorRadius"))),
    )
    if not IsArc:
        return (GeomKind.ELLIPSE, EllipseGeom(*Arguments))
    return (
        GeomKind.ARC_ELLIPSE,
        ArcEllipseGeom(
            *Arguments,
            Number(Value.get("StartAngle")),
            Number(Value.get("EndAngle")),
        ),
    )


# this definition decodes complete and trimmed hyperbola geometry records
def HyperbolaAction(
    NodeValue: ET.Element, TypeId: str
) -> tuple[GeomKind, AnyValue] | None:
    IsArc = TypeId == "Part::GeomArcOfHyperbola"
    Value = NodeValue.find("./ArcOfHyperbola" if IsArc else "./Hyperbola")
    if Value is None:
        return None
    Arguments = (
        VectorTwo(Number(Value.get("CenterX")), Number(Value.get("CenterY"))),
        GeomAxis(Value),
        abs(Number(Value.get("MajorRadius"))),
        abs(Number(Value.get("MinorRadius"))),
    )
    if not IsArc:
        return (GeomKind.HYPERBOLA, HyperbolaGeom(*Arguments))
    return (
        GeomKind.ARC_HYPERBOLA,
        ArcHyperbolaGeom(
            *Arguments,
            Number(Value.get("StartAngle")),
            Number(Value.get("EndAngle")),
        ),
    )


# this definition decodes complete and trimmed parabola geometry records
def ParabolaAction(
    NodeValue: ET.Element, TypeId: str
) -> tuple[GeomKind, AnyValue] | None:
    IsArc = TypeId == "Part::GeomArcOfParabola"
    Value = NodeValue.find("./ArcOfParabola" if IsArc else "./Parabola")
    if Value is None:
        return None
    Arguments = (
        VectorTwo(Number(Value.get("CenterX")), Number(Value.get("CenterY"))),
        GeomAxis(Value),
        abs(Number(Value.get("Focal"))),
    )
    if not IsArc:
        return (GeomKind.PARABOLA, ParabolaGeom(*Arguments))
    return (
        GeomKind.ARC_PARABOLA,
        ArcParabolaGeom(
            *Arguments,
            Number(Value.get("StartAngle")),
            Number(Value.get("EndAngle")),
        ),
    )


# this definition decodes bezier and spline geometry records
def SplineAction(
    NodeValue: ET.Element, TypeId: str
) -> tuple[GeomKind, AnyValue] | None:
    Value = NodeValue.find("./BSplineCurve")
    if Value is None:
        Value = NodeValue.find("./BezierCurve")
    if Value is None:
        return None
    Points = tuple(
        VectorTwo(Number(ItemValue.get("X")), Number(ItemValue.get("Y")))
        for ItemValue in Value.findall(".//*[@X][@Y]")
    )
    if not Points:
        return None
    Degree = (
        max(1, len(Points) - 1)
        if TypeId == "Part::GeomBezierCurve"
        else max(1, Integer(Value.get("Degree"), 3))
    )
    return (
        GeomKindByTypeId[TypeId],
        SplineGeom(
            Points,
            Degree,
            knots=tuple(
                Number(ItemValue.get("Value")) for ItemValue in Value.findall("./Knot")
            ),
            multiplicities=tuple(
                Integer(ItemValue.get("Mult"), 1)
                for ItemValue in Value.findall("./Knot")
            ),
            weights=tuple(
                Number(ItemValue.get("Weight"), 1.0)
                for ItemValue in Value.findall("./Pole")
            ),
            periodic=Value.get("IsPeriodic", Value.get("Periodic", "false")).casefold()
            in XmlTrueValues,
        ),
    )


# this definition dispatches each supported geometry record to its focused decoder
def GeomAction(NodeValue: ET.Element, EntityId: str) -> tuple[GeomKind, AnyValue]:
    TypeId = NodeValue.get("type", "")
    Result = None
    if TypeId == "Part::GeomLineSegment":
        Result = LineAction(NodeValue)
    elif TypeId == "Part::GeomCircle":
        Result = CircleAction(NodeValue)
    elif TypeId == "Part::GeomArcOfCircle":
        Result = ArcAction(NodeValue)
    elif TypeId == "Part::GeomPoint":
        Result = PointAction(NodeValue)
    elif TypeId in {"Part::GeomEllipse", "Part::GeomArcOfEllipse"}:
        Result = EllipseAction(NodeValue, TypeId)
    elif TypeId in {"Part::GeomHyperbola", "Part::GeomArcOfHyperbola"}:
        Result = HyperbolaAction(NodeValue, TypeId)
    elif TypeId in {"Part::GeomParabola", "Part::GeomArcOfParabola"}:
        Result = ParabolaAction(NodeValue, TypeId)
    elif TypeId in SplineGeomTypeIds:
        Result = SplineAction(NodeValue, TypeId)
    if Result is not None:
        return Result
    return (
        GeomKindByTypeId.get(TypeId, GeomKind.NATIVE),
        NativeGeom(FormatId, TypeId or "unknown", ElemData(NodeValue)),
    )


# this definition exists because focused behavior needs one stable owner
def GeomAxis(Value: ET.Element) -> VectorTwo:
    if Value.get("MajorAxisX") is not None:
        return VectorTwo(
            Number(Value.get("MajorAxisX"), 1.0), Number(Value.get("MajorAxisY"))
        )
    Angle = Number(Value.get("AngleXU"))
    return VectorTwo(MathValue.cos(Angle), MathValue.sin(Angle))


# this definition exists because focused behavior needs one stable owner
def IsPointClose(First: Vector2, Second: Vector2, Tolerance: float = 1e-07) -> bool:
    return MathValue.hypot(First.x - Second.x, First.y - Second.y) <= Tolerance


# this definition exists because focused behavior needs one stable owner
def Segment(First: Vector2, Second: Vector2, Third: Vector2) -> float:
    return (Second.x - First.x) * (Third.y - First.y) - (Second.y - First.y) * (
        Third.x - First.x
    )


# this definition exists because focused behavior needs one stable owner
def IsPointOnSeg(
    Point: Vector2, First: Vector2, Second: Vector2, Tolerance: float = 1e-07
) -> bool:
    return (
        abs(Segment(First, Second, Point)) <= Tolerance
        and min(First.x, Second.x) - Tolerance
        <= Point.x
        <= max(First.x, Second.x) + Tolerance
        and (
            min(First.y, Second.y) - Tolerance
            <= Point.y
            <= max(First.y, Second.y) + Tolerance
        )
    )


# this definition exists because focused behavior needs one stable owner
def HasSegmentTouch(
    FirstStart: Vector2,
    FirstEnd: Vector2,
    SecondStart: Vector2,
    SecondEnd: Vector2,
    Tolerance: float = 1e-07,
) -> bool:
    FirstA = Segment(FirstStart, FirstEnd, SecondStart)
    FirstB = Segment(FirstStart, FirstEnd, SecondEnd)
    SecondA = Segment(SecondStart, SecondEnd, FirstStart)
    SecondB = Segment(SecondStart, SecondEnd, FirstEnd)
    if (
        FirstA > Tolerance
        and FirstB < -Tolerance
        or (FirstA < -Tolerance and FirstB > Tolerance)
    ) and (
        SecondA > Tolerance
        and SecondB < -Tolerance
        or (SecondA < -Tolerance and SecondB > Tolerance)
    ):
        return True
    return any(
        (
            abs(Value) <= Tolerance and IsPointOnSeg(Point, Start, EndValue, Tolerance)
            for Value, Point, Start, EndValue in (
                (FirstA, SecondStart, FirstStart, FirstEnd),
                (FirstB, SecondEnd, FirstStart, FirstEnd),
                (SecondA, FirstStart, SecondStart, SecondEnd),
                (SecondB, FirstEnd, SecondStart, SecondEnd),
            )
        )
    )


# this definition finds a union root while compressing the traversal path
def FindRootMut(Parents: list[int], Index: int) -> int:
    while Parents[Index] != Index:
        Parents[Index] = Parents[Parents[Index]]
        Index = Parents[Index]
    return Index


# this definition merges two endpoint clusters deterministically
def UnionRootsMut(Parents: list[int], First: int, Second: int) -> None:
    FirstRoot = FindRootMut(Parents, First)
    SecondRoot = FindRootMut(Parents, Second)
    if FirstRoot != SecondRoot:
        Parents[max(FirstRoot, SecondRoot)] = min(FirstRoot, SecondRoot)


# this definition clusters coincident endpoints and rejects inconsistent clusters
def ClusterRoots(Endpoints: tuple[VectorTwo, ...]) -> tuple[int, ...] | None:
    Parents = list(range(len(Endpoints)))
    for First in range(len(Endpoints)):
        for Second in range(First + 1, len(Endpoints)):
            if IsPointClose(Endpoints[First], Endpoints[Second]):
                UnionRootsMut(Parents, First, Second)
    Clusters: dict[int, list[int]] = {}
    for Index in range(len(Endpoints)):
        Clusters.setdefault(FindRootMut(Parents, Index), []).append(Index)
    if any(
        not IsPointClose(Endpoints[First], Endpoints[Second])
        for Members in Clusters.values()
        for Position, First in enumerate(Members)
        for Second in Members[Position + 1 :]
    ):
        return None
    return tuple(FindRootMut(Parents, Index) for Index in range(len(Endpoints)))


# this definition builds the two edge incidence contract for a closed line graph
def BuildIncident(
    Roots: tuple[int, ...], EdgeCount: int
) -> dict[int, list[int]] | None:
    Incident: dict[int, list[int]] = {}
    for EdgeIndex in range(EdgeCount):
        Start = Roots[EdgeIndex * 2]
        EndValue = Roots[EdgeIndex * 2 + 1]
        if Start == EndValue:
            return None
        Incident.setdefault(Start, []).append(EdgeIndex)
        Incident.setdefault(EndValue, []).append(EdgeIndex)
    if any((len(Values) != 2 for Values in Incident.values())):
        return None
    return Incident


# this definition rejects degenerate or self intersecting line loops
def IsSimpleLoop(Vertices: list[VectorTwo], Ordered: list[int]) -> bool:
    if len(Ordered) < 3 or len(set(Vertices[:-1])) != len(Vertices) - 1:
        return False
    AreaValue = abs(
        sum(
            First.x * Second.y - Second.x * First.y
            for First, Second in zip(Vertices[:-1], Vertices[1:], strict=True)
        )
    )
    if AreaValue <= 1e-09:
        return False
    Segments = list(zip(Vertices[:-1], Vertices[1:], strict=True))
    for FirstIndex, FirstSegment in enumerate(Segments):
        for SecondIndex in range(FirstIndex + 1, len(Segments)):
            if SecondIndex in {FirstIndex + 1, (FirstIndex - 1) % len(Segments)}:
                continue
            if HasSegmentTouch(*FirstSegment, *Segments[SecondIndex]):
                return False
    return True


# this definition walks one closed line component in deterministic edge order
def TraceLoopMut(
    Lines: tuple[tuple[int, SketchEntity], ...],
    Endpoints: tuple[VectorTwo, ...],
    Roots: tuple[int, ...],
    Incident: Mapping[int, list[int]],
    Remaining: set[int],
) -> tuple[int, tuple[str, ...], tuple[VectorTwo, ...]] | None:
    EdgeOrder = {Index: Lines[Index][0] for Index in Remaining}
    FirstEdge = min(Remaining, key=EdgeOrder.__getitem__)
    StartVertex = Roots[FirstEdge * 2]
    CurrentVertex = Roots[FirstEdge * 2 + 1]
    Ordered = [FirstEdge]
    Vertices = [Endpoints[FirstEdge * 2], Endpoints[FirstEdge * 2 + 1]]
    Remaining.remove(FirstEdge)
    while CurrentVertex != StartVertex:
        NextEdges = [Value for Value in Incident[CurrentVertex] if Value in Remaining]
        if len(NextEdges) != 1:
            return None
        EdgeIndex = NextEdges[0]
        EdgeStart, EdgeEnd = Roots[EdgeIndex * 2 : EdgeIndex * 2 + 2]
        if CurrentVertex == EdgeStart:
            CurrentVertex = EdgeEnd
            Vertices.append(Endpoints[EdgeIndex * 2 + 1])
        elif CurrentVertex == EdgeEnd:
            CurrentVertex = EdgeStart
            Vertices.append(Endpoints[EdgeIndex * 2])
        else:
            return None
        Ordered.append(EdgeIndex)
        Remaining.remove(EdgeIndex)
    if not IsSimpleLoop(Vertices, Ordered):
        return None
    return (
        min(Lines[Index][0] for Index in Ordered),
        tuple(Lines[Index][1].id for Index in Ordered),
        tuple(Vertices[:-1]),
    )


# this definition detects contact between otherwise independent profile loops
def HasLoopTouch(
    Profiles: Sequence[tuple[int, tuple[str, ...], tuple[VectorTwo, ...]]],
) -> bool:
    for FirstIndex, (Ignored, Ignored, FirstVertices) in enumerate(Profiles):
        FirstSegments = tuple(
            zip(FirstVertices, (*FirstVertices[1:], FirstVertices[0]), strict=True)
        )
        for Ignored, Ignored, SecondVertices in Profiles[FirstIndex + 1 :]:
            SecondSegments = tuple(
                zip(
                    SecondVertices,
                    (*SecondVertices[1:], SecondVertices[0]),
                    strict=True,
                )
            )
            if any(
                HasSegmentTouch(*FirstSegment, *SecondSegment)
                for FirstSegment in FirstSegments
                for SecondSegment in SecondSegments
            ):
                return True
    return False


# this definition derives closed profile identifiers from supported sketch geometry
def ClosedProfile(Entities: tuple[SketchEntity, ...]) -> tuple[tuple[str, ...], ...]:
    Candidates = tuple(Entity for Entity in Entities if not Entity.construction)
    if not Candidates:
        return ()
    Closed = tuple(
        Entity
        for Entity in Candidates
        if isinstance(Entity.geometry, (CircleGeom, EllipseGeom))
    )
    Lines = tuple(
        (Index, Entity)
        for Index, Entity in enumerate(Candidates)
        if isinstance(Entity.geometry, LineGeom)
    )
    if len(Closed) + len(Lines) != len(Candidates):
        return ()
    if Closed:
        Invalid = Lines or any(
            isinstance(Entity.geometry, CircleGeom)
            and Entity.geometry.radius <= 1e-09
            or isinstance(Entity.geometry, EllipseGeom)
            and min(Entity.geometry.major_radius, Entity.geometry.minor_radius) <= 1e-09
            for Entity in Closed
        )
        return () if Invalid else tuple((Entity.id,) for Entity in Closed)
    Endpoints = tuple(
        Point
        for Ignored, Entity in Lines
        for Point in (Entity.geometry.start, Entity.geometry.end)
    )
    Roots = ClusterRoots(Endpoints)
    Incident = BuildIncident(Roots, len(Lines)) if Roots is not None else None
    if Roots is None or Incident is None:
        return ()
    Remaining = set(range(len(Lines)))
    Profiles = []
    while Remaining:
        Profile = TraceLoopMut(Lines, Endpoints, Roots, Incident, Remaining)
        if Profile is None:
            return ()
        Profiles.append(Profile)
    if HasLoopTouch(Profiles):
        return ()
    return tuple(Profile for Ignored, Profile, Ignored in sorted(Profiles))


# this binding exists because shared behavior needs one stable value
KOriginPlaneFrames = {
    "XY_Plane": (0, Transform(), Transform()),
    "XZ_Plane": (
        1,
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
    ),
    "YZ_Plane": (
        2,
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
    ),
}


# this definition exists because focused behavior needs one stable owner
def IsTransformNear(
    First: Transform, Second: Transform, Tolerance: float = 1e-09
) -> bool:
    return all(
        (
            MathValue.isclose(LeftValue, Right, rel_tol=0.0, abs_tol=Tolerance)
            for FirstVector, SecondVector in (
                (First.origin, Second.origin),
                (First.x_axis, Second.x_axis),
                (First.y_axis, Second.y_axis),
                (First.z_axis, Second.z_axis),
            )
            for LeftValue, Right in zip(
                (FirstVector.x, FirstVector.y, FirstVector.z),
                (SecondVector.x, SecondVector.y, SecondVector.z),
                strict=True,
            )
        )
    )


# this definition exists because focused behavior needs one stable owner
def OriginPlane(
    ObjValue: _NativeObject, Transform: Transform
) -> tuple[int, Transform] | None:
    Value = KOriginPlaneFrames.get(ObjValue.name)
    if (
        Value is None
        or ObjValue.type_id != "App::Plane"
        or String(ObjValue, "Role") != ObjValue.name
        or (not IsTransformNear(Transform, Value[1]))
    ):
        return None
    return (Value[0], Value[2])


# this definition exists because focused behavior needs one stable owner
def DotAction(First: Vector3, Second: Vector3) -> float:
    return First.x * Second.x + First.y * Second.y + First.z * Second.z


# this definition exists because focused behavior needs one stable owner
def PlaneReframe(
    Source: Transform, Target: Transform
) -> tuple[float, float, float, float, float, float]:
    Delta = VectorThree(
        Source.origin.x - Target.origin.x,
        Source.origin.y - Target.origin.y,
        Source.origin.z - Target.origin.z,
    )
    return (
        DotAction(Source.x_axis, Target.x_axis),
        DotAction(Source.y_axis, Target.x_axis),
        DotAction(Delta, Target.x_axis),
        DotAction(Source.x_axis, Target.y_axis),
        DotAction(Source.y_axis, Target.y_axis),
        DotAction(Delta, Target.y_axis),
    )


# this definition applies an affine reframe to one sketch point
def ReframePoint(
    Value: Vector2, Reframe: tuple[float, float, float, float, float, float]
) -> VectorTwo:
    XxValue, XyValue, TxValue, YxValue, YyValue, TyValue = Reframe
    return VectorTwo(
        XxValue * Value.x + XyValue * Value.y + TxValue,
        YxValue * Value.x + YyValue * Value.y + TyValue,
    )


# this definition applies the linear portion of a reframe to one direction
def ReframeDir(
    Value: Vector2, Reframe: tuple[float, float, float, float, float, float]
) -> VectorTwo:
    XxValue, XyValue, Ignored, YxValue, YyValue, Ignored = Reframe
    return VectorTwo(
        XxValue * Value.x + XyValue * Value.y,
        YxValue * Value.x + YyValue * Value.y,
    )


# this definition adjusts circular arc angles for affine reflection and rotation
def CircleAngles(
    Reframe: tuple[float, float, float, float, float, float],
    Start: float,
    EndValue: float,
) -> tuple[float, float]:
    XxValue, XyValue, Ignored, YxValue, YyValue, Ignored = Reframe
    Determinant = XxValue * YyValue - XyValue * YxValue
    Rotation = MathValue.atan2(YxValue, XxValue)
    if Determinant < 0.0:
        return (Rotation - EndValue, Rotation - Start)
    return (Start + Rotation, EndValue + Rotation)


# this definition adjusts conic arc angles for affine reflection
def ConicAngles(
    Reframe: tuple[float, float, float, float, float, float],
    Start: float,
    EndValue: float,
) -> tuple[float, float]:
    XxValue, XyValue, Ignored, YxValue, YyValue, Ignored = Reframe
    Determinant = XxValue * YyValue - XyValue * YxValue
    return (-EndValue, -Start) if Determinant < 0.0 else (Start, EndValue)


# this definition applies an affine frame change to supported sketch geometry
def ReframeGeom(
    GeomValue: Any, Reframe: tuple[float, float, float, float, float, float]
) -> AnyValue:
    if isinstance(GeomValue, PointGeom):
        return Replace(GeomValue, point=ReframePoint(GeomValue.point, Reframe))
    if isinstance(GeomValue, LineGeom):
        return Replace(
            GeomValue,
            start=ReframePoint(GeomValue.start, Reframe),
            end=ReframePoint(GeomValue.end, Reframe),
        )
    if isinstance(GeomValue, CircleGeom):
        return Replace(GeomValue, center=ReframePoint(GeomValue.center, Reframe))
    if isinstance(GeomValue, ArcGeom):
        Start, EndValue = CircleAngles(
            Reframe, GeomValue.start_angle, GeomValue.end_angle
        )
        return Replace(
            GeomValue,
            center=ReframePoint(GeomValue.center, Reframe),
            start_angle=Start,
            end_angle=EndValue,
        )
    if isinstance(GeomValue, EllipseGeom):
        return Replace(
            GeomValue,
            center=ReframePoint(GeomValue.center, Reframe),
            major_axis=ReframeDir(GeomValue.major_axis, Reframe),
        )
    if isinstance(GeomValue, (ArcEllipseGeom, ArcHyperbolaGeom)):
        Start, EndValue = ConicAngles(
            Reframe, GeomValue.start_angle, GeomValue.end_angle
        )
        return Replace(
            GeomValue,
            center=ReframePoint(GeomValue.center, Reframe),
            major_axis=ReframeDir(GeomValue.major_axis, Reframe),
            start_angle=Start,
            end_angle=EndValue,
        )
    if isinstance(GeomValue, HyperbolaGeom):
        return Replace(
            GeomValue,
            center=ReframePoint(GeomValue.center, Reframe),
            major_axis=ReframeDir(GeomValue.major_axis, Reframe),
        )
    if isinstance(GeomValue, ParabolaGeom):
        return Replace(
            GeomValue,
            center=ReframePoint(GeomValue.center, Reframe),
            axis=ReframeDir(GeomValue.axis, Reframe),
        )
    if isinstance(GeomValue, ArcParabolaGeom):
        Start, EndValue = ConicAngles(
            Reframe, GeomValue.start_angle, GeomValue.end_angle
        )
        return Replace(
            GeomValue,
            center=ReframePoint(GeomValue.center, Reframe),
            axis=ReframeDir(GeomValue.axis, Reframe),
            start_angle=Start,
            end_angle=EndValue,
        )
    if isinstance(GeomValue, SplineGeom):
        return Replace(
            GeomValue,
            control_points=tuple(
                ReframePoint(Value, Reframe) for Value in GeomValue.control_points
            ),
        )
    return GeomValue


# this definition exists because focused behavior needs one stable owner
def SupportTarget(ObjValue: _NativeObject) -> str:
    for NameValue in ("AttachmentSupport", "Support"):
        NodeValue = ObjValue.properties.get(NameValue)
        if NodeValue is None:
            continue
        for PathValue, AttrValue in (
            ("./LinkSubList/Link", "obj"),
            ("./LinkSub", "value"),
            ("./Link", "value"),
            ("./XLink", "name"),
        ):
            LinkValue = NodeValue.find(PathValue)
            if LinkValue is not None and LinkValue.get(AttrValue, ""):
                return LinkValue.get(AttrValue, "")
    return ""


# this definition exists because focused behavior needs one stable owner
def IsSupportPlane(ObjValue: _NativeObject, SupportTargets: set[str]) -> bool:
    if ObjValue.type_id in SupportPlaneTypeIds or ObjValue.name in SupportTargets:
        return True
    Marker = f"{ObjValue.type_id} {ProxyClass(ObjValue)}".casefold()
    Properties = set(ObjValue.properties)
    return (
        "plane" in Marker
        and bool({"Placement", "AttachmentOffset"} & Properties)
        and bool(
            {"Support", "AttachmentSupport", "AttachmentOffset", "MapMode"} & Properties
        )
    )


# this definition exists because focused behavior needs one stable owner
def RuleExpression(Expressions: dict[str, str], Index: int, NameValue: str) -> str:
    Candidates = [f"Constraints[{Index}]", f"Constraints.{NameValue}"]
    return next(
        (Expressions[Value] for Value in Candidates if Value in Expressions), ""
    )


# this definition exists because focused behavior needs one stable owner
def RuleElemSlots(NodeValue: ET.Element) -> tuple[tuple[int, int], ...]:
    ElemIds = NodeValue.get("ElementIds")
    ElemPositions = NodeValue.get("ElementPositions")
    Values: list[tuple[int, int]] = []
    if ElemIds is not None and ElemPositions is not None:
        IdsValue = ElemIds.split()
        Positions = ElemPositions.split()
        if len(IdsValue) == len(Positions):
            Values = [
                (Integer(EntityId, -2000), Integer(Position))
                for EntityId, Position in zip(IdsValue, Positions, strict=True)
            ]
    while len(Values) < 3:
        Values.append((-2000, 0))
    for Index, Prefix in enumerate(("First", "Second", "Third")):
        if NodeValue.get(Prefix) is not None:
            Values[Index] = (
                Integer(NodeValue.get(Prefix), -2000),
                Integer(NodeValue.get(Prefix + "Pos")),
            )
    return tuple(Values)


# this definition collects support plane objects transforms and principal frames
def OriginData(
    Objects: tuple[_NativeObject, ...], SupportTargets: set[str]
) -> tuple[
    dict[str, NativeObject], dict[str, Transform], dict[str, tuple[int, Transform]]
]:
    PlaneObjects = {
        ObjValue.name: ObjValue
        for ObjValue in Objects
        if IsSupportPlane(ObjValue, SupportTargets)
    }
    SourcePlaneTransforms: dict[str, Transform] = {}
    OriginFrames: dict[str, tuple[int, Transform]] = {}
    for NameValue, ObjValue in PlaneObjects.items():
        PlaneTransform = TransformA(PlacementElem(ObjValue, "Placement"))
        SourcePlaneTransforms[NameValue] = PlaneTransform
        Frame = OriginPlane(ObjValue, PlaneTransform)
        if Frame is not None:
            OriginFrames[NameValue] = Frame
    return (PlaneObjects, SourcePlaneTransforms, OriginFrames)


# this definition finds principal frames that constrained geometry cannot safely adopt
def BlockedFrames(
    Objects: tuple[_NativeObject, ...],
    OriginFrames: Mapping[str, tuple[int, Transform]],
    SourceTransforms: Mapping[str, Transform],
) -> set[str]:
    BlockedOriginFrames: set[str] = set()
    for ObjValue in Objects:
        if ObjValue.type_id != SketchTypeId:
            continue
        SupportName = SupportTarget(ObjValue)
        Frame = OriginFrames.get(SupportName)
        SourceTransform = SourceTransforms.get(SupportName)
        if (
            Frame is None
            or SourceTransform is None
            or IsTransformNear(SourceTransform, Frame[1])
        ):
            continue
        RuleList = FindChild(ObjValue, "Constraints", "ConstraintList")
        if RuleList is not None and RuleList.findall("./Constrain"):
            BlockedOriginFrames.add(SupportName)
            continue
        GeomList = FindChild(ObjValue, "Geometry", "GeometryList")
        GeomNodes = [] if GeomList is None else GeomList.findall("./Geometry")
        if any(
            (
                isinstance(GeomAction(NodeValue, "")[1], NativeGeom)
                for NodeValue in GeomNodes
            )
        ):
            BlockedOriginFrames.add(SupportName)
    return BlockedOriginFrames


# this definition builds support planes and their selected transform maps
def BuildPlanes(
    PlaneObjects: Mapping[str, NativeObject],
    SourceTransforms: Mapping[str, Transform],
    OriginFrames: Mapping[str, tuple[int, Transform]],
    Blocked: set[str],
) -> tuple[list[SupportPlane], dict[str, str], dict[str, Transform]]:
    Planes: list[SupportPlane] = []
    PlaneIds: dict[str, str] = {}
    PlaneTransforms: dict[str, Transform] = {}
    for NameValue, ObjValue in PlaneObjects.items():
        PlaneId = f"freecad:plane:{ObjValue.name}"
        PlaneIds[ObjValue.name] = PlaneId
        SourceTransform = SourceTransforms[ObjValue.name]
        Frame = OriginFrames.get(ObjValue.name)
        Principal = Frame is not None and ObjValue.name not in Blocked
        PlaneTransform = Frame[1] if Principal else SourceTransform
        PlaneTransforms[ObjValue.name] = PlaneTransform
        Attributes: dict[str, AnyValue] = {"freecad": NativeObjectA(ObjValue)}
        if Principal and Frame is not None:
            Attributes.update(
                {"principal_index": Frame[0], "principal_role": ObjValue.name}
            )
        Planes.append(
            SupportPlane(
                PlaneId,
                String(ObjValue, "Label", ObjValue.name),
                PlaneTransform,
                attributes=Attributes,
            )
        )
    return (Planes, PlaneIds, PlaneTransforms)


# this definition creates a synthetic support plane when a sketch target is absent
def AddSupportMut(
    ObjValue: NativeObject,
    PlaneIds: dict[str, str],
    Planes: list[SupportPlane],
) -> tuple[str, str]:
    SupportName = SupportTarget(ObjValue)
    SupportId = PlaneIds.get(SupportName)
    if SupportId is not None:
        return (SupportName, SupportId)
    SupportId = f"freecad:plane:{ObjValue.name}:support"
    PlaneIds[f"{ObjValue.name}:support"] = SupportId
    OffsetData = (
        ElemData(ObjValue.properties["AttachmentOffset"])
        if "AttachmentOffset" in ObjValue.properties
        else {}
    )
    Planes.append(
        SupportPlane(
            SupportId,
            SupportName or f"{ObjValue.name} support",
            TransformA(PlacementElem(ObjValue, "Placement")),
            attributes={
                "freecad_support": SupportName,
                "freecad_attachment_offset": OffsetData,
            },
        )
    )
    return (SupportName, SupportId)


# this definition identifies construction geometry from native flags
def IsConstruction(NodeValue: ET.Element) -> bool:
    ConstructionNode = NodeValue.find("./Construction")
    if ConstructionNode is not None:
        Value = ConstructionNode.get("value", "0").casefold()
        if Value in XmlTrueValues:
            return True
    Extension = NodeValue.find(
        "./GeoExtensions/GeoExtension[@type='Sketcher::SketchGeometryExtension']"
    )
    Flags = "" if Extension is None else Extension.get("geometryModeFlags", "")
    return bool(Flags and Flags[-2:] == "10")


# this definition decodes all geometry entities owned by one native sketch
def SketchEntities(
    SketchId: str,
    GeomNodes: Sequence[ET.Element],
    RuleNodes: Sequence[ET.Element],
    Reframe: tuple[float, float, float, float, float, float] | None,
) -> list[SketchEntity]:
    FixedIndices = {
        RuleElemSlots(NodeValue)[0][0]
        for NodeValue in RuleNodes
        if Integer(NodeValue.get("Type"), -1) == 17
    }
    Entities: list[SketchEntity] = []
    for Index, NodeValue in enumerate(GeomNodes):
        EntityId = f"{SketchId}:entity:{Index}"
        KindValue, GeomValue = GeomAction(NodeValue, EntityId)
        if Reframe is not None:
            GeomValue = ReframeGeom(GeomValue, Reframe)
        Entities.append(
            SketchEntity(
                EntityId,
                KindValue,
                GeomValue,
                construction=IsConstruction(NodeValue),
                fixed=Index in FixedIndices,
                attributes={
                    "freecad_geometry_id": NodeValue.get("id", ""),
                    "freecad": ElemData(NodeValue),
                },
            )
        )
    return Entities


# this definition resolves rule references and preserves native slot metadata
def RuleRefs(
    NodeValue: ET.Element, Entities: Sequence[SketchEntity]
) -> tuple[list[RuleRef], list[dict[str, AnyValue]]]:
    References: list[RuleRef] = []
    RefSlots: list[dict[str, AnyValue]] = []
    for SlotIndex, (EntityIndex, PointIndex) in enumerate(RuleElemSlots(NodeValue)):
        Point = RulePointByIndex.get(PointIndex, "")
        EntityId = Entities[EntityIndex].id if 0 <= EntityIndex < len(Entities) else ""
        SlotName = (
            ("first", "second", "third")[SlotIndex]
            if SlotIndex < 3
            else f"element_{SlotIndex}"
        )
        RefSlots.append(
            {
                "slot": SlotName,
                "entity_id": EntityId,
                "point": Point,
                "freecad_geometry_index": EntityIndex,
                "freecad_point_index": PointIndex,
            }
        )
        if EntityId:
            References.append(RuleRef(EntityId, Point))
    return (References, RefSlots)


# this definition emits one dimensional rule parameter and records expression use
def RuleParamMut(
    ObjValue: NativeObject,
    SketchId: str,
    Index: int,
    NameValue: str,
    NodeValue: ET.Element,
    Expressions: Mapping[str, str],
    Parameters: list[Parameter],
    Consumed: set[tuple[str, str]],
) -> str | None:
    CodeValue = Integer(NodeValue.get("Type"), -1)
    if CodeValue not in DimensionalRuleCodes:
        return None
    ParamId = f"freecad:parameter:{ObjValue.name}:constraint:{Index}"
    ValueKind, UnitValue = RuleValueKindByCode[CodeValue]
    ExpressionSource = RuleExpression(dict(Expressions), Index, NameValue)
    if ExpressionSource:
        Paths = {f"Constraints[{Index}]", f"Constraints.{NameValue}"}
        Consumed.update(
            (ObjValue.name, PathValue)
            for PathValue, Source in Expressions.items()
            if Source == ExpressionSource and PathValue in Paths
        )
    Parameters.append(
        Param(
            ParamId,
            f"{String(ObjValue, 'Label', ObjValue.name)}.{NameValue}",
            ParamValue(Number(NodeValue.get("Value")), ValueKind, UnitValue),
            expression=(
                Expression(ExpressionSource, language="freecad")
                if ExpressionSource
                else None
            ),
            owner_id=SketchId,
            attributes={
                "freecad_path": f"Constraints[{Index}]",
                "freecad_constraint": dict(NodeValue.attrib),
            },
        )
    )
    return ParamId


# this definition decodes all dimensional and geometric rules for one sketch
def SketchRulesMut(
    ObjValue: NativeObject,
    SketchId: str,
    RuleNodes: Sequence[ET.Element],
    Entities: Sequence[SketchEntity],
    Parameters: list[Parameter],
    Consumed: set[tuple[str, str]],
) -> tuple[list[SketchRule], list[str]]:
    Expressions = ReadExpressions(ObjValue)
    Constraints: list[SketchRule] = []
    ParamIds: list[str] = []
    for Index, NodeValue in enumerate(RuleNodes):
        CodeValue = Integer(NodeValue.get("Type"), -1)
        NameValue = NodeValue.get("Name", "") or str(Index)
        References, RefSlots = RuleRefs(NodeValue, Entities)
        ParamId = RuleParamMut(
            ObjValue,
            SketchId,
            Index,
            NameValue,
            NodeValue,
            Expressions,
            Parameters,
            Consumed,
        )
        if ParamId is not None:
            ParamIds.append(ParamId)
        Constraints.append(
            SketchRule(
                f"{SketchId}:constraint:{Index}",
                RuleKindByCode.get(CodeValue, RuleKind.NATIVE),
                tuple(References),
                parameter_id=ParamId,
                driving=NodeValue.get("IsDriving", "1") != "0",
                suppressed=NodeValue.get("IsActive", "1") == "0",
                attributes={
                    "freecad_type_code": CodeValue,
                    "freecad": dict(NodeValue.attrib),
                    "freecad_reference_slots": RefSlots,
                },
            )
        )
    return (Constraints, ParamIds)


# this definition decodes one native sketch after support planes are established
def NativeSketchMut(
    ObjValue: NativeObject,
    PlaneIds: dict[str, str],
    Planes: list[SupportPlane],
    SourceTransforms: Mapping[str, Transform],
    PlaneTransforms: Mapping[str, Transform],
    Parameters: list[Parameter],
    Consumed: set[tuple[str, str]],
) -> Sketch:
    SketchId = f"freecad:sketch:{ObjValue.name}"
    SupportName, SupportId = AddSupportMut(ObjValue, PlaneIds, Planes)
    GeomList = FindChild(ObjValue, "Geometry", "GeometryList")
    GeomNodes = [] if GeomList is None else GeomList.findall("./Geometry")
    RuleList = FindChild(ObjValue, "Constraints", "ConstraintList")
    RuleNodes = [] if RuleList is None else RuleList.findall("./Constrain")
    SourceTransform = SourceTransforms.get(SupportName)
    TargetTransform = PlaneTransforms.get(SupportName)
    Reframe = (
        PlaneReframe(SourceTransform, TargetTransform)
        if SourceTransform is not None
        and TargetTransform is not None
        and not IsTransformNear(SourceTransform, TargetTransform)
        else None
    )
    Entities = SketchEntities(SketchId, GeomNodes, RuleNodes, Reframe)
    Constraints, ParamIds = SketchRulesMut(
        ObjValue, SketchId, RuleNodes, Entities, Parameters, Consumed
    )
    EntityValues = tuple(Entities)
    ExternalData = (
        ElemData(ObjValue.properties["ExternalGeometry"])
        if "ExternalGeometry" in ObjValue.properties
        else {}
    )
    return Sketch(
        SketchId,
        String(ObjValue, "Label", ObjValue.name),
        SupportId,
        EntityValues,
        constraints=tuple(Constraints),
        parameter_ids=tuple(ParamIds),
        closed_profile_entity_ids=ClosedProfile(EntityValues),
        suppressed=not IsBoolValue(ObjValue, "Visibility", True),
        attributes={
            "freecad": NativeObjectA(ObjValue),
            "fully_constrained": IsBoolValue(ObjValue, "FullyConstrained"),
            "external_geometry": ExternalData,
        },
    )


# this definition coordinates support plane and sketch decoding
def ParseSketchMut(
    Objects: tuple[_NativeObject, ...],
    Parameters: list[Parameter],
    ConsumedExpressions: set[tuple[str, str]],
) -> tuple[tuple[SupportPlane, ...], tuple[Sketch, ...]]:
    SupportTargets = {
        Target
        for ObjValue in Objects
        if ObjValue.type_id == SketchTypeId and (Target := SupportTarget(ObjValue))
    }
    PlaneObjects, SourceTransforms, OriginFrames = OriginData(Objects, SupportTargets)
    Blocked = BlockedFrames(Objects, OriginFrames, SourceTransforms)
    Planes, PlaneIds, PlaneTransforms = BuildPlanes(
        PlaneObjects, SourceTransforms, OriginFrames, Blocked
    )
    Sketches = [
        NativeSketchMut(
            ObjValue,
            PlaneIds,
            Planes,
            SourceTransforms,
            PlaneTransforms,
            Parameters,
            ConsumedExpressions,
        )
        for ObjValue in Objects
        if ObjValue.type_id == SketchTypeId
    ]
    return (tuple(Planes), tuple(Sketches))


# this definition exists because focused behavior needs one stable owner
def HasShapeProp(ObjValue: _NativeObject) -> bool:
    return any(
        (
            NodeValue.find("./Part") is not None
            for NodeValue in ObjValue.properties.values()
        )
    )


# this definition exists because focused behavior needs one stable owner
def IsFeatureObject(ObjValue: _NativeObject) -> bool:
    if ObjValue.type_id in NonFeatureObjectTypeIds or ObjValue.type_id.startswith(
        AsmObjectTypePrefix
    ):
        return False
    if (
        ObjValue.type_id in FeatureKindByTypeId
        or ObjValue.type_id in PrimitiveFeatureTypeIds
    ):
        return True
    return HasShapeProp(ObjValue)


# this definition exists because focused behavior needs one stable owner
def OrderedFeatures(Objects: tuple[_NativeObject, ...]) -> tuple[NativeObject, ...]:
    Candidates = [ObjValue for ObjValue in Objects if IsFeatureObject(ObjValue)]
    Names = {ObjValue.name for ObjValue in Candidates}
    Remaining = list(Candidates)
    Result: list[NativeObject] = []
    Resolved: set[str] = set()
    while Remaining:
        Ready = [
            ObjValue
            for ObjValue in Remaining
            if not {Value for Value in ObjValue.dependencies if Value in Names}
            - Resolved
        ]
        if not Ready:
            raise NativeFreeCad("FreeCAD feature dependency graph contains a cycle")

        # this callback exists because local behavior needs one focused transformation
        Ready.sort(key=lambda ItemValue: ItemValue.index)
        for ObjValue in Ready:
            Result.append(ObjValue)
            Resolved.add(ObjValue.name)
            Remaining.remove(ObjValue)
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def IsBodyContainer(ObjValue: _NativeObject) -> bool:
    return ObjValue.type_id in BodyContainerTypeIds or (
        ObjValue.type_id == "App::DocumentObjectGroup"
        and "SourceBodyJSON" in ObjValue.properties
        and ("Tip" in ObjValue.properties)
    )


# this definition exists because focused behavior needs one stable owner
def FeatureKindA(ObjValue: _NativeObject) -> FeatureKind:
    Declared = String(ObjValue, "FeatureKind").casefold()
    if Declared:
        try:
            DeclaredKind = FeatureKind(Declared)
        except ValueError:
            DeclaredKind = None
        if DeclaredKind is not None:
            return DeclaredKind
    if ObjValue.type_id == "Part::Feature":
        return FeatureKind.IMPORTED
    if ObjValue.type_id in PrimitiveFeatureTypeIds:
        return FeatureKind.PRIMITIVE
    return FeatureKindByTypeId.get(ObjValue.type_id, FeatureKind.NATIVE)


# this definition exists because focused behavior needs one stable owner
def FeatureA(ObjValue: _NativeObject) -> tuple[Selection, ...]:
    Values: list[tuple[str, str, str]] = []
    for PropName, PropElem in ObjValue.properties.items():
        for LinkValue in PropElem.findall("./LinkSub"):
            Target = LinkValue.get("value", "")
            Values.extend(
                (
                    (PropName, Target, SubElem)
                    for Child in LinkValue.findall("./Sub")
                    if (SubElem := Child.get("value", ""))
                )
            )
        for LinkValue in PropElem.findall("./XLink"):
            Target = LinkValue.get("name", "")
            Values.extend(
                (
                    (PropName, Target, SubElem)
                    for Child in LinkValue.findall("./Sub")
                    if (SubElem := Child.get("value", ""))
                )
            )
        for LinkValue in PropElem.findall("./LinkSubList/Link"):
            Target = LinkValue.get("obj", LinkValue.get("value", ""))
            Subelements = [
                Child.get("value", "") for Child in LinkValue.findall("./Sub")
            ]
            if LinkValue.get("sub", ""):
                Subelements.append(LinkValue.get("sub", ""))
            Values.extend(
                ((PropName, Target, SubElem) for SubElem in Subelements if SubElem)
            )
        for LinkValue in PropElem.findall("./XLinkSubList/XLink"):
            Target = LinkValue.get("name", "")
            Values.extend(
                (
                    (PropName, Target, SubElem)
                    for Child in LinkValue.findall("./Sub")
                    if (SubElem := Child.get("value", ""))
                )
            )
    Result: list[Selection] = []
    for Index, (PropName, Target, SubElem) in enumerate(Values):
        Token = SubElem.rsplit(".", 1)[-1]
        EntityKind = next(
            (
                KindValue.value
                for Prefix, KindValue in SubElemKindByPrefix.items()
                if Token.startswith(Prefix)
            ),
            MateEntityKind.NATIVE.value,
        )
        SelectionId = f"freecad:selection:{ObjValue.name}:{PropName}:{Index}"
        Result.append(
            Selection(
                SelectionId,
                f"{String(ObjValue, 'Label', ObjValue.name)}.{PropName}.{SubElem}",
                (SelectionPathElem(EntityKind, Target, SubElem),),
                provenance=Provenance(
                    FormatId, f"{ObjValue.name}.{PropName}.{SubElem}"
                ),
                attributes={
                    "freecad_object": ObjValue.name,
                    "freecad_property": PropName,
                    "freecad_target": Target,
                    "freecad_subelement": SubElem,
                },
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def Explicit(Objects: tuple[_NativeObject, ...]) -> tuple[Selection, ...]:
    Result: list[Selection] = []
    for ObjValue in Objects:
        SelectionId = String(ObjValue, "KitSelectionId")
        NodeValue = ObjValue.properties.get("Selection")
        if not SelectionId or NodeValue is None:
            continue
        KindsNode = ObjValue.properties.get("EntityKinds")
        Kinds = (
            [
                Child.get("value", "")
                for Child in KindsNode.findall("./StringList/String")
            ]
            if KindsNode is not None
            else []
        )
        Paths: list[SelectionPathElem] = []
        for Index, LinkValue in enumerate(NodeValue.findall("./LinkSubList/Link")):
            Target = LinkValue.get("obj", LinkValue.get("value", ""))
            Subelements = [
                Value
                for Child in LinkValue.findall("./Sub")
                if (Value := Child.get("value", ""))
            ]
            if LinkValue.get("sub") is not None:
                Subelements.insert(0, LinkValue.get("sub", ""))
            if not Subelements:
                Subelements.append("")
            for SubElem in Subelements:
                Token = SubElem.rsplit(".", 1)[-1]
                Inferred = next(
                    (
                        KindValue.value
                        for Prefix, KindValue in SubElemKindByPrefix.items()
                        if Token.startswith(Prefix)
                    ),
                    MateEntityKind.NATIVE.value,
                )
                Paths.append(
                    SelectionPathElem(
                        (
                            Kinds[Index]
                            if Index < len(Kinds) and Kinds[Index]
                            else Inferred
                        ),
                        Target,
                        SubElem,
                    )
                )
        PointNode = FindChild(ObjValue, "SelectionPoint", "PropertyVector")
        Point = (
            VectorThree(
                Number(PointNode.get("valueX")),
                Number(PointNode.get("valueY")),
                Number(PointNode.get("valueZ")),
            )
            if PointNode is not None
            else None
        )
        Result.append(
            Selection(
                SelectionId,
                String(ObjValue, "Label", ObjValue.name),
                tuple(Paths),
                point=Point,
                provenance=Provenance(FormatId, ObjValue.name),
                attributes={"freecad": NativeObjectA(ObjValue)},
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def FeatureMut(
    ObjValue: _NativeObject,
    FeatureId: str,
    Parameters: list[Parameter],
    ConsumedExpressions: set[tuple[str, str]],
) -> tuple[str, ...]:
    Result: list[str] = []
    Expressions = ReadExpressions(ObjValue)
    for NameValue, NodeValue in ObjValue.properties.items():
        Value = PropParamValue(NodeValue)
        if Value is None:
            continue
        ParamId = f"freecad:parameter:{ObjValue.name}:{NameValue}"
        ExpressionSource = Expressions.get(NameValue, "")
        if ExpressionSource:
            ConsumedExpressions.add((ObjValue.name, NameValue))
        Parameters.append(
            Param(
                ParamId,
                f"{String(ObjValue, 'Label', ObjValue.name)}.{NameValue}",
                Value,
                expression=(
                    Expression(ExpressionSource, language="freecad")
                    if ExpressionSource
                    else None
                ),
                owner_id=FeatureId,
                attributes={
                    "freecad_path": NameValue,
                    "freecad_property_type": NodeValue.get("type", ""),
                    "freecad_property": ElemData(NodeValue),
                },
            )
        )
        Result.append(ParamId)
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def ExtrusionEnd(TypeCode: int, ObjectTypeId: str) -> ExtrusionEndCondition:
    ExtrusionType = ExtrusionTypeByCode.get(TypeCode)
    if ExtrusionType is None:
        return ExtrusionEndCondition.NATIVE
    if ObjectTypeId == PocketTypeId and ExtrusionType.pocket_end_condition is not None:
        return ExtrusionType.pocket_end_condition
    return ExtrusionType.end_condition


# this definition exists because focused behavior needs one stable owner
def Extrusion(ObjValue: _NativeObject) -> ExtrusionFeature:
    EndCondition = ExtrusionEnd(EnumAction(ObjValue, "Type"), ObjValue.type_id)
    SideType = EnumAction(ObjValue, "SideType", -1)
    SecondEndCondition = (
        ExtrusionEnd(EnumAction(ObjValue, "Type2"), ObjValue.type_id)
        if SideType == 1
        else None
    )
    DirectionNode = FindChild(ObjValue, "Direction", "PropertyVector")
    Direction = None
    if DirectionNode is not None:
        Direction = VectorThree(
            Number(DirectionNode.get("valueX")),
            Number(DirectionNode.get("valueY")),
            Number(DirectionNode.get("valueZ")),
        )
    return ExtrusionFeature(
        ParamValue(Float(ObjValue, "Length"), ValueKind.LENGTH, "mm"),
        end_condition=EndCondition,
        reversed=IsBoolValue(ObjValue, "Reversed"),
        symmetric=SideType == 2 or IsBoolValue(ObjValue, "Midplane"),
        direction=Direction,
        second_length=(
            ParamValue(Float(ObjValue, "Length2"), ValueKind.LENGTH, "mm")
            if "Length2" in ObjValue.properties
            else None
        ),
        second_end_condition=SecondEndCondition,
        offset=(
            ParamValue(Float(ObjValue, "Offset"), ValueKind.LENGTH, "mm")
            if "Offset" in ObjValue.properties
            else None
        ),
        second_offset=(
            ParamValue(Float(ObjValue, "Offset2"), ValueKind.LENGTH, "mm")
            if "Offset2" in ObjValue.properties
            else None
        ),
        draft_angle=(
            ParamValue(Float(ObjValue, "TaperAngle"), ValueKind.ANGLE, "deg")
            if "TaperAngle" in ObjValue.properties
            else None
        ),
        second_draft_angle=(
            ParamValue(Float(ObjValue, "TaperAngle2"), ValueKind.ANGLE, "deg")
            if "TaperAngle2" in ObjValue.properties
            else None
        ),
        up_to_reference=LinkAction(ObjValue, "UpToFace")
        or LinkAction(ObjValue, "UpToShape"),
        second_up_to_reference=LinkAction(ObjValue, "UpToFace2")
        or LinkAction(ObjValue, "UpToShape2"),
    )


# this definition exists because focused behavior needs one stable owner
def PartExtrusion(ObjValue: _NativeObject) -> ExtrusionFeature:
    DirectionNode = FindChild(ObjValue, "Dir", "PropertyVector")
    Direction = None
    if DirectionNode is not None:
        Direction = VectorThree(
            Number(DirectionNode.get("valueX")),
            Number(DirectionNode.get("valueY")),
            Number(DirectionNode.get("valueZ")),
        )
    Forward = Float(ObjValue, "LengthFwd")
    Reverse = Float(ObjValue, "LengthRev")
    return ExtrusionFeature(
        ParamValue(Forward, ValueKind.LENGTH, "mm"),
        end_condition=ExtrusionEndCondition.BLIND,
        reversed=False,
        symmetric=Forward > 0.0 and Reverse > 0.0 and (abs(Forward - Reverse) <= 1e-12),
        direction=Direction,
        second_length=ParamValue(Reverse, ValueKind.LENGTH, "mm"),
    )


# this definition collects auxiliary files referenced by one shape property
def BrepSidecars(
    NodeValue: ET.Element, FileName: str, Entries: Mapping[str, bytes]
) -> list[dict[str, AnyValue]]:
    Sidecars = []
    for Child in NodeValue.findall(".//*[@file]"):
        SidecarName = Child.get("file", "")
        if not SidecarName or SidecarName == FileName:
            continue
        SidecarData = Entries.get(SidecarName)
        if SidecarData is not None:
            Sidecars.append({"source_stream": SidecarName, "data": SidecarData})
    return Sidecars


# this definition builds one native shape payload with exact provenance metadata
def MakeBrepPayload(
    ObjValue: NativeObject,
    PropName: str,
    NodeValue: ET.Element,
    PartValue: ET.Element,
    DataValue: bytes,
    FileName: str,
    Entries: Mapping[str, bytes],
    FeatureIds: Mapping[str, str],
    BodyIds: Mapping[str, str],
) -> BrepPayload:
    PayloadId = f"freecad:brep:{ObjValue.name}:{PropName}"
    Header = DataValue[:256].decode("ascii", "ignore")
    Match = RegexLib.search("CASCADE Topology V\\d+", Header)
    Attributes: dict[str, AnyValue] = {
        "freecad_object": ObjValue.name,
        "freecad_object_type": ObjValue.type_id,
        "freecad_property": PropName,
        "freecad_property_data": ElemData(NodeValue),
        "freecad_part_attributes": dict(PartValue.attrib),
    }
    Sidecars = BrepSidecars(NodeValue, FileName, Entries)
    if Sidecars:
        Attributes["freecad_sidecars"] = Sidecars
    if PropName == "Shape" and ObjValue.name in FeatureIds:
        Attributes["feature_id"] = FeatureIds[ObjValue.name]
    if PropName == "Shape" and ObjValue.name in BodyIds:
        Attributes["body_id"] = BodyIds[ObjValue.name]
    return BrepPayload(
        PayloadId,
        "opencascade",
        "shape",
        Match.group(0) if Match else "FreeCAD PartShape",
        Hashlib.sha256(DataValue).hexdigest(),
        data=DataValue,
        source_stream=FileName,
        provenance=Provenance(FormatId, f"{ObjValue.name}.{PropName}"),
        attributes=Attributes,
        role=PayloadRole.BREP,
        file_extension=".brep",
    )


# this definition collects every native shape payload and owner relationship
def BuildBrep(
    Native: _NativeArchive, FeatureIds: dict[str, str], BodyIds: dict[str, str]
) -> tuple[tuple[BrepPayload, ...], dict[str, list[str]]]:
    Payloads: list[BrepPayload] = []
    OwnerPayloads: dict[str, list[str]] = {}
    for ObjValue in Native.objects:
        for PropName, NodeValue in ObjValue.properties.items():
            PartValue = NodeValue.find("./Part")
            FileName = "" if PartValue is None else PartValue.get("file", "")
            DataValue = Native.entries.get(FileName)
            if PartValue is None or not FileName or DataValue is None:
                continue
            Payload = MakeBrepPayload(
                ObjValue,
                PropName,
                NodeValue,
                PartValue,
                DataValue,
                FileName,
                Native.entries,
                FeatureIds,
                BodyIds,
            )
            Payloads.append(Payload)
            OwnerPayloads.setdefault(ObjValue.name, []).append(Payload.id)
    return (tuple(Payloads), OwnerPayloads)


# this definition exists because focused behavior needs one stable owner
def DecodedDocBrep(
    Payloads: tuple[BrepPayload, ...], Bodies: tuple[Body, ...]
) -> BrepModel | None:
    if not Bodies:
        return None
    Selected: set[str] = set()
    Models: list[BrepModel] = []
    for BodyValue in Bodies:
        BodyMatches = tuple(
            (
                Payload
                for Payload in Payloads
                if Payload.role == PayloadRole.BREP
                and Payload.data is not None
                and (Payload.attributes.get("body_id") == BodyValue.id)
            )
        )
        FeatureMatches = tuple(
            (
                Payload
                for Payload in Payloads
                if Payload.role == PayloadRole.BREP
                and Payload.data is not None
                and (Payload.attributes.get("feature_id") == BodyValue.final_feature_id)
            )
        )
        Matches = BodyMatches or FeatureMatches
        if len(Matches) != 1 or Matches[0].id in Selected:
            return None
        Payload = Matches[0]
        Selected.add(Payload.id)
        Digest = Hashlib.sha256(Payload.id.encode("utf-8")).hexdigest()[:20]
        Model = DecodeAsciiBrep(
            Payload.data,
            id_prefix=f"freecad:occ:{Digest}",
            design_body_id=BodyValue.id,
            attributes={
                "brep_payload_id": Payload.id,
                "feature_id": BodyValue.final_feature_id,
            },
        )
        if Model is None:
            return None
        Models.append(Model)
    return BrepModel(
        curves=tuple((Value for Model in Models for Value in Model.curves)),
        pcurves=tuple((Value for Model in Models for Value in Model.pcurves)),
        surfaces=tuple((Value for Model in Models for Value in Model.surfaces)),
        vertices=tuple((Value for Model in Models for Value in Model.vertices)),
        edges=tuple((Value for Model in Models for Value in Model.edges)),
        coedges=tuple((Value for Model in Models for Value in Model.coedges)),
        loops=tuple((Value for Model in Models for Value in Model.loops)),
        wires=tuple((Value for Model in Models for Value in Model.wires)),
        faces=tuple((Value for Model in Models for Value in Model.faces)),
        face_uses=tuple((Value for Model in Models for Value in Model.face_uses)),
        shells=tuple((Value for Model in Models for Value in Model.shells)),
        shell_uses=tuple((Value for Model in Models for Value in Model.shell_uses)),
        regions=tuple((Value for Model in Models for Value in Model.regions)),
        bodies=tuple((Value for Model in Models for Value in Model.bodies)),
    )


# this definition decodes the native binary mesh sidecar format
def BinaryMesh(
    DataValue: bytes,
) -> tuple[tuple[VectorThree, ...], tuple[tuple[int, int, int], ...]]:
    if len(DataValue) < 296:
        return ((), ())
    try:
        Endian = "<"
        Magic, Version = Struct.unpack_from("<II", DataValue)
        if (Magic, Version) != (2695938256, 65536):
            Magic, Version = Struct.unpack_from(">II", DataValue)
            Endian = ">"
        VertexCount, TriangleCount = Struct.unpack_from(f"{Endian}II", DataValue, 264)
        Expected = 272 + VertexCount * 12 + TriangleCount * 24 + 24
        if Magic != 2695938256 or Version != 65536 or Expected > len(DataValue):
            return ((), ())
        Vertices = tuple(
            VectorThree(
                *Struct.unpack_from(f"{Endian}fff", DataValue, 272 + Index * 12)
            )
            for Index in range(VertexCount)
        )
        TriangleOffset = 272 + VertexCount * 12
        Triangles = tuple(
            Struct.unpack_from(f"{Endian}III", DataValue, TriangleOffset + Index * 24)
            for Index in range(TriangleCount)
        )
        return (Vertices, Triangles)
    except Struct.error:
        return ((), ())


# this definition decodes an xml embedded mesh representation
def XmlMesh(
    Value: ET.Element,
) -> tuple[tuple[VectorThree, ...], tuple[tuple[int, int, int], ...]]:
    if Value.find("./Points") is None:
        return ((), ())
    Vertices = tuple(
        VectorThree(
            Number(Point.get("x")), Number(Point.get("y")), Number(Point.get("z"))
        )
        for Point in Value.findall("./Points/P")
    )
    Triangles = tuple(
        (
            Integer(FaceValue.get("p0"), -1),
            Integer(FaceValue.get("p1"), -1),
            Integer(FaceValue.get("p2"), -1),
        )
        for FaceValue in Value.findall("./Faces/F")
    )
    return (Vertices, Triangles)


# this definition chooses binary or xml mesh decoding for one property
def MeshData(
    Value: ET.Element, Entries: Mapping[str, bytes]
) -> tuple[tuple[VectorThree, ...], tuple[tuple[int, int, int], ...]]:
    DataValue = Entries.get(Value.get("file", ""))
    return BinaryMesh(DataValue) if DataValue is not None else XmlMesh(Value)


# this definition decodes every valid native mesh property
def ParseMeshes(Native: _NativeArchive) -> tuple[MeshValue, ...]:
    Result: list[MeshValue] = []
    for ObjValue in Native.objects:
        for PropName, PropElem in ObjValue.properties.items():
            Value = PropElem.find("./Mesh")
            if Value is None:
                continue
            FileName = Value.get("file", "")
            Vertices, Triangles = MeshData(Value, Native.entries)
            if not Vertices and not Triangles:
                continue
            if any(
                any(Index < 0 or Index >= len(Vertices) for Index in Triangle)
                for Triangle in Triangles
            ):
                continue
            Result.append(
                MeshValue(
                    f"freecad:mesh:{ObjValue.name}:{PropName}",
                    String(ObjValue, "Label", ObjValue.name),
                    Vertices,
                    Triangles,
                    provenance=Provenance(FormatId, f"{ObjValue.name}.{PropName}"),
                    attributes={
                        "freecad": NativeObjectA(ObjValue),
                        "source_stream": FileName,
                    },
                )
            )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def ProxyClass(ObjValue: _NativeObject) -> str:
    NodeValue = ObjValue.properties.get("Proxy")
    if NodeValue is None:
        return ""
    Value = NodeValue.find("./Python")
    return "" if Value is None else Value.get("class", "")


# this definition exists because focused behavior needs one stable owner
def Enumeration(ObjValue: _NativeObject, NameValue: str) -> str:
    NodeValue = ObjValue.properties.get(NameValue)
    if NodeValue is None:
        return ""
    Selected = NodeValue.find("./Integer")
    if Selected is None:
        return ""
    Index = Integer(Selected.get("value"), -1)
    Choices = [
        Child.get("value", "") for Child in NodeValue.findall("./CustomEnumList/Enum")
    ]
    return Choices[Index] if 0 <= Index < len(Choices) else str(Index)


# this definition exists because focused behavior needs one stable owner
def XlinkData(ObjValue: _NativeObject, NameValue: str) -> dict[str, AnyValue]:
    NodeValue = ObjValue.properties.get(NameValue)
    if NodeValue is None:
        return {"file": "", "stamp": "", "name": "", "subelements": []}
    Value = NodeValue.find("./XLink")
    if Value is None:
        return {"file": "", "stamp": "", "name": "", "subelements": []}
    Subelements = [Child.get("value", "") for Child in Value.findall("./Sub")]
    if not Subelements and Value.get("name", ""):
        Subelements.append("")
    return {
        "file": Value.get("file", ""),
        "stamp": Value.get("stamp", ""),
        "name": Value.get("name", ""),
        "subelements": Subelements,
    }


# this definition exists because focused behavior needs one stable owner
def LinkedObjectA(ObjValue: _NativeObject) -> str:
    Linked = ObjValue.properties.get("LinkedObject")
    if Linked is not None and Linked.find("./XLink") is not None:
        return "LinkedObject"
    Marker = " ".join(
        (
            ObjValue.type_id,
            ProxyClass(ObjValue),
            *(Extension.get("type", "") for Extension in ObjValue.extensions),
        )
    ).casefold()
    if "link" not in Marker:
        return ""
    Candidates = [
        NameValue
        for NameValue, NodeValue in ObjValue.properties.items()
        if NodeValue.find("./XLink") is not None and NameValue not in JointReservedLink
    ]
    Named = next(
        (NameValue for NameValue in Candidates if "link" in NameValue.casefold()), ""
    )
    return Named or (Candidates[0] if len(Candidates) == 1 else "")


# this definition exists because focused behavior needs one stable owner
def LinkedObject(ObjValue: _NativeObject) -> dict[str, AnyValue]:
    PropName = LinkedObjectA(ObjValue)
    return XlinkData(ObjValue, PropName) if PropName else XlinkData(ObjValue, "")


# this definition exists because focused behavior needs one stable owner
def IsLinkObject(ObjValue: _NativeObject) -> bool:
    return bool(LinkedObjectA(ObjValue))


# this definition exists because focused behavior needs one stable owner
def IsAsmLinkObject(ObjValue: _NativeObject) -> bool:
    return IsLinkObject(ObjValue) and {"Group", "Rigid"}.issubset(ObjValue.properties)


# this definition exists because focused behavior needs one stable owner
def IsGroundedJoint(ObjValue: _NativeObject) -> bool:
    Proxy = ProxyClass(ObjValue).casefold()
    return "groundedjoint" in Proxy or JointGroundProp in ObjValue.properties


# this definition exists because focused behavior needs one stable owner
def IsJointObject(ObjValue: _NativeObject) -> bool:
    if IsGroundedJoint(ObjValue):
        return True
    Marker = f"{ObjValue.type_id} {ProxyClass(ObjValue)}".casefold()
    HasRef = bool(set(JointRefProperties) & set(ObjValue.properties))
    return (
        "joint" in Marker
        and HasRef
        or (HasRef and bool(JointTypeProperties & set(ObjValue.properties)))
    )


# this definition exists because focused behavior needs one stable owner
def FindJointGroup(
    Objects: tuple[_NativeObject, ...], ByName: dict[str, _NativeObject]
) -> NativeObject | None:
    Exact = next(
        (ObjValue for ObjValue in Objects if ObjValue.type_id == AsmJointGroupTypeId),
        None,
    )
    if Exact is not None:
        return Exact
    Candidates: list[NativeObject] = []
    for ObjValue in Objects:
        Members = [
            ByName[NameValue]
            for NameValue in LinkList(ObjValue, "Group")
            if NameValue in ByName
        ]
        JointMembers = [Member for Member in Members if IsJointObject(Member)]
        Marker = f"{ObjValue.type_id} {ProxyClass(ObjValue)}".casefold()
        if JointMembers and (
            "jointgroup" in Marker or len(JointMembers) == len(Members)
        ):
            Candidates.append(ObjValue)
    return Candidates[0] if len(Candidates) == 1 else None


# this definition exists because focused behavior needs one stable owner
def AsmRootObject(Objects: tuple[_NativeObject, ...]) -> NativeObject | None:
    Exact = next(
        (ObjValue for ObjValue in Objects if ObjValue.type_id == AsmRootTypeId), None
    )
    if Exact is not None:
        return Exact
    ByName = {ObjValue.name: ObjValue for ObjValue in Objects}
    GroupedNames = {
        NameValue
        for ObjValue in Objects
        for NameValue in LinkList(ObjValue, "Group")
        if NameValue in ByName
    }
    Candidates: list[tuple[tuple[int, int, int, int], NativeObject]] = []
    for ObjValue in Objects:
        if IsLinkObject(ObjValue) or IsJointObject(ObjValue):
            continue
        Links = [
            ByName[NameValue]
            for NameValue in LinkList(ObjValue, "Group")
            if NameValue in ByName and IsLinkObject(ByName[NameValue])
        ]
        if not Links:
            continue
        Marker = f"{ObjValue.type_id} {ProxyClass(ObjValue)} {String(ObjValue, 'Type')}".casefold()
        Score = (
            int("assembly" in Marker),
            int(ObjValue.name not in GroupedNames),
            sum((IsAsmLinkObject(LinkValue) for LinkValue in Links)),
            len(Links),
        )
        Candidates.append((Score, ObjValue))
    if not Candidates:
        return None

    # this callback exists because local behavior needs one focused transformation
    return max(Candidates, key=lambda Value: (Value[0], -Value[1].index))[1]


# this definition exists because focused behavior needs one stable owner
def MateEntityKindA(Value: str) -> MateEntityKind:
    Token = Value.rsplit(".", 1)[-1]
    for Prefix, KindValue in SubElemKindByPrefix.items():
        if Token.startswith(Prefix):
            return KindValue
    return MateEntityKind.NATIVE


# this definition exists because focused behavior needs one stable owner
def MateValuesMut(
    ObjValue: _NativeObject,
    KindValue: MateKind | str,
    MateId: str,
    Parameters: list[Parameter],
    ConsumedExpressions: set[tuple[str, str]],
) -> tuple[ParamValue | None, tuple[str, ...]]:
    ValueProperties: list[tuple[str, ValueKind, str]] = []
    PrimaryProp = ""
    if KindValue == MateKind.ANGLE:
        PrimaryProp = "Angle"
        ValueProperties.append(("Angle", ValueKind.ANGLE, "deg"))
    elif KindValue in MateKindsUsingDistance:
        PrimaryProp = "Distance"
        ValueProperties.append(("Distance", ValueKind.LENGTH, "mm"))
    if KindValue in MateKindsUsingSecond:
        ValueProperties.append(("Distance2", ValueKind.LENGTH, "mm"))
    for EnableName, PropName, KindItem, UnitValue in (
        ("EnableLengthMin", "LengthMin", ValueKind.LENGTH, "mm"),
        ("EnableLengthMax", "LengthMax", ValueKind.LENGTH, "mm"),
        ("EnableAngleMin", "AngleMin", ValueKind.ANGLE, "deg"),
        ("EnableAngleMax", "AngleMax", ValueKind.ANGLE, "deg"),
    ):
        if IsBoolValue(ObjValue, EnableName):
            ValueProperties.append((PropName, KindItem, UnitValue))
    Expressions = ReadExpressions(ObjValue)
    PrimaryValue: ParamValue | None = None
    ParamIds: list[str] = []
    for PropName, KindItem, UnitValue in ValueProperties:
        if PropName not in ObjValue.properties:
            continue
        Value = ParamValue(Float(ObjValue, PropName), KindItem, UnitValue)
        if PropName == PrimaryProp:
            PrimaryValue = Value
        ParamId = f"freecad:parameter:{ObjValue.name}:{PropName}"
        ExpressionSource = Expressions.get(PropName, "")
        if ExpressionSource:
            ConsumedExpressions.add((ObjValue.name, PropName))
        Parameters.append(
            Param(
                ParamId,
                f"{String(ObjValue, 'Label', ObjValue.name)}.{PropName}",
                Value,
                expression=(
                    Expression(ExpressionSource, language="freecad")
                    if ExpressionSource
                    else None
                ),
                owner_id=MateId,
                attributes={
                    "freecad_path": PropName,
                    "freecad_property": ElemData(ObjValue.properties[PropName]),
                },
            )
        )
        ParamIds.append(ParamId)
    return (PrimaryValue, tuple(ParamIds))


# this definition exists because focused behavior needs one stable owner
def StoredMateValue(ObjValue: _NativeObject) -> ParamValue | None:
    Source = String(ObjValue, "MateValueJSON")
    if not Source:
        return None
    try:
        Value = JsonValue.loads(Source)
    except (JsonValue.JSONDecodeError, RecursionError):
        return None
    if not isinstance(Value, dict) or "value" not in Value:
        return None
    KindValueA = Value.get("kind", ValueKind.NUMBER)
    if isinstance(KindValueA, dict):
        KindValueA = KindValueA.get("value", ValueKind.NUMBER)
    try:
        KindValue = ValueKind(str(KindValueA))
    except ValueError:
        KindValue = ValueKind.NUMBER
    RawValue = Value.get("value")
    if not isinstance(RawValue, (str, int, float, bool)):
        return None
    return ParamValue(RawValue, KindValue, str(Value.get("unit", "")))


# this definition exists because focused behavior needs one stable owner
def EmbeddedDoc(
    Target: str,
    TargetObj: _NativeObject | None,
    Identity: str,
    Payloads: tuple[BrepPayload, ...],
) -> tuple[str, CadDoc, tuple[str, ...]]:
    Digest = Hashlib.sha256(Identity.encode("utf-8")).hexdigest()[:20]
    DocId = f"freecad:component-document:{Digest}"
    FeatureId = f"freecad:component-feature:{Digest}"
    ComponentPayloads = tuple(
        (
            Replace(
                Payload,
                id=f"{Payload.id}:component:{Digest}",
                attributes={**dict(Payload.attributes), "feature_id": FeatureId},
            )
            for Payload in Payloads
        )
    )
    Label = String(TargetObj, "Label", Target) if TargetObj is not None else Target
    Feature = FeatureStep(
        FeatureId,
        Label,
        FeatureKind.IMPORTED if ComponentPayloads else FeatureKind.NATIVE,
        0,
        provenance=Provenance(FormatId, Target),
        attributes={
            "freecad": NativeObjectA(TargetObj) if TargetObj is not None else {},
            "brep_payload_ids": [Payload.id for Payload in ComponentPayloads],
        },
    )
    Component = CadDoc(
        CadSource(
            FormatId,
            Identity,
            Hashlib.sha256(
                "".join((Payload.sha256 for Payload in ComponentPayloads)).encode(
                    "ascii"
                )
            ).hexdigest(),
        ),
        (Config(f"{DocId}:configuration", "Default", active=True),),
        (),
        (),
        (),
        (),
        (Feature,),
        (),
        brep_payloads=ComponentPayloads,
        metadata={"freecad_component_target": Target, "freecad_identity": Identity},
    )
    Component = Replace(
        Component, capabilities=InferCapabilities(Component, roundtrip_metadata=True)
    )
    Component.assert_valid()
    return (DocId, Component, ())


# this definition exists because focused behavior needs one stable owner
def ResolvedSource(SourcePath: str) -> FilePath | None:
    if not SourcePath:
        return None
    try:
        PathValue = FilePath(SourcePath).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    return PathValue if PathValue.is_file() else None


# this definition exists because focused behavior needs one stable owner
def IsReparsePath(PathValue: FilePath, RootValue: FilePath) -> bool:
    Current = PathValue
    while True:
        try:
            Details = Current.lstat()
        except OSError:
            return True
        if Current.is_symlink() or getattr(Details, "st_file_attributes", 0) & 1024:
            return True
        if Current == RootValue:
            return False
        if RootValue not in Current.parents:
            return True
        Current = Current.parent


# this definition lists unique external document references in stable order
def OuterFileNames(Native: _NativeArchive) -> list[str]:
    return sorted(
        {
            str(Linked["file"])
            for ObjValue in Native.objects
            if IsLinkObject(ObjValue) and (Linked := LinkedObject(ObjValue))["file"]
        }
    )


# this definition resolves one external reference within the guarded document root
def ResolveOuter(
    FileName: str,
    Source: FilePath | None,
    State: OuterState | None,
    Depth: int,
) -> tuple[FilePath | None, str]:
    if Source is None or State is None:
        return (None, "source location is unavailable")
    if Depth >= KMaxOuterDepth:
        return (None, "external reference depth exceeds safe limits")
    if FilePath(FileName).is_absolute():
        return (None, "absolute external paths are not allowed")
    try:
        Choice = (Source.parent / FileName).resolve(strict=True)
        Choice.relative_to(State.root)
    except (OSError, RuntimeError, ValueError):
        return (None, "external reference is missing or outside the document root")
    if IsReparsePath(Choice, State.root):
        return (None, "external reference traverses a reparse point")
    if Choice.suffix.casefold() != Suffix.casefold():
        return (None, "external reference is not an FCStd document")
    if Choice in State.active:
        return (None, "external reference cycle detected")
    return (Choice, "")


# this definition loads one guarded external document and updates shared limits
def ReadOuterMut(Choice: FilePath, State: OuterState, Depth: int) -> CadDoc:
    try:
        SizeValue = Choice.stat().st_size
    except OSError as ErrorInfo:
        raise NativeFreeCad("external reference is unreadable") from ErrorInfo
    if (
        SizeValue < 0
        or SizeValue > MaxEntrySize
        or State.FileCount >= MaxOuterFiles
        or State.TotalBytes + SizeValue > MaxTotalSize
    ):
        raise NativeFreeCad("external reference exceeds safe limits")
    try:
        ChildData = Choice.read_bytes()
    except OSError as ErrorInfo:
        raise NativeFreeCad("external reference is unreadable") from ErrorInfo
    State.FileCount += 1
    State.TotalBytes += len(ChildData)
    State.active.add(Choice)
    try:
        try:
            Manifest = ExtractManifestFromFcstd(ChildData)
        except ValueError as ErrorInfo:
            if (
                str(ErrorInfo)
                != "FCStd archive has no embedded Kit interchange document"
            ):
                raise NativeFreeCad(str(ErrorInfo)) from ErrorInfo
            return ReadNativeFcstd(
                ChildData, str(Choice), StateValue=State, OuterDepth=Depth + 1
            )
        return CadDoc.from_dict(Manifest)
    finally:
        State.active.discard(Choice)


# this definition resolves and loads all guarded external document references
def OuterDocsMut(
    Native: _NativeArchive, SourcePath: str, State: _ExternalState | None, Depth: int
) -> tuple[dict[str, tuple[str, CadDoc]], list[dict[str, str]]]:
    Source = ResolvedSource(SourcePath)
    Resolved: dict[str, tuple[str, CadDoc]] = {}
    Unresolved: list[dict[str, str]] = []
    for FileName in OuterFileNames(Native):
        Choice, Reason = ResolveOuter(FileName, Source, State, Depth)
        if Reason or Choice is None or State is None:
            Unresolved.append(
                {"file": FileName, "reason": Reason or "external reference is invalid"}
            )
            continue
        Identity = Choice.relative_to(State.root).as_posix()
        Cached = State.cache.get(Choice)
        if Cached is not None:
            Resolved[FileName] = (Identity, Cached)
            continue
        try:
            Child = ReadOuterMut(Choice, State, Depth)
        except (NativeFreeCad, TypeError, ValueError, RecursionError) as ErrorInfo:
            Unresolved.append({"file": FileName, "reason": str(ErrorInfo)})
            continue
        State.cache[Choice] = Child
        Resolved[FileName] = (Identity, Child)
    return (Resolved, Unresolved)


# this definition selects ordered component link objects from an assembly root
def AssemblyLinks(
    Native: NativeArchive, Objects: Mapping[str, NativeObject], RootValue: NativeObject
) -> list[NativeObject]:
    RootGroup = LinkList(RootValue, "Group")
    Links = [
        Objects[NameValue]
        for NameValue in RootGroup
        if NameValue in Objects and IsLinkObject(Objects[NameValue])
    ]
    if Links:
        GroupedNames = {ObjValue.name for ObjValue in Links}
        Links.extend(
            (
                ObjValue
                for ObjValue in Native.objects
                if ObjValue.name not in GroupedNames
                and IsLinkObject(ObjValue)
                and LinkedObject(ObjValue)["file"]
            )
        )
    else:
        Links = [ObjValue for ObjValue in Native.objects if IsLinkObject(ObjValue)]
    return Links


# this definition collects joint ordering and grounded target context
def JointContext(
    Native: NativeArchive, Objects: Mapping[str, NativeObject]
) -> tuple[
    NativeObject | None, tuple[str, ...], list[NativeObject], dict[str, NativeObject]
]:
    JointGroup = FindJointGroup(Native.objects, Objects)
    JointNames = LinkList(JointGroup, "Group") if JointGroup is not None else ()
    if not JointNames:
        JointNames = tuple(
            (ObjValue.name for ObjValue in Native.objects if IsJointObject(ObjValue))
        )
    JointObjects = [
        Objects[NameValue] for NameValue in JointNames if NameValue in Objects
    ]
    GroundedByTarget = {
        Target: ObjValue
        for ObjValue in JointObjects
        if IsGroundedJoint(ObjValue)
        and (Target := LinkAction(ObjValue, JointGroundProp))
    }
    return (JointGroup, tuple(JointNames), JointObjects, GroundedByTarget)


# this definition builds a linked or embedded component definition and document
def MakeDefinition(
    LinkObj: NativeObject,
    Target: str,
    SourceFile: str,
    SourceIdentity: str,
    Outer: tuple[str, CadDoc] | None,
    Objects: Mapping[str, NativeObject],
    OwnerPayloads: Mapping[str, list[str]],
    BrepPayloads: tuple[BrepPayload, ...],
) -> tuple[str, ComponentDoc, ComponentDefinition]:
    Identity = f"{SourceIdentity}#{Target}"
    Digest = Hashlib.sha256(Identity.encode("utf-8")).hexdigest()[:20]
    DefinitionId = f"freecad:definition:{Digest}"
    TargetObj = Objects.get(Target)
    PayloadIds = set(OwnerPayloads.get(Target, []))
    TargetPayloads = tuple(
        Payload
        for Payload in BrepPayloads
        if Payload.id in PayloadIds
        and Payload.attributes.get("freecad_property") == "Shape"
    )
    if Outer is not None:
        Component = Outer[1]
        DocId = f"freecad:component-document:{Digest}"
        BodyIds = tuple(BodyValue.id for BodyValue in Component.bodies)
    else:
        DocId, Component, BodyIds = EmbeddedDoc(
            Target, TargetObj, Identity, TargetPayloads
        )
    Definition = ComponentDefinition(
        DefinitionId,
        String(TargetObj, "Label", Target) if TargetObj is not None else Target,
        (
            ComponentKind.ASSEMBLY
            if IsAsmLinkObject(LinkObj) or Component.assembly is not None
            else ComponentKind.PART
        ),
        document_id=DocId,
        body_ids=BodyIds,
        source_path=SourceFile,
        source_format_id=FormatId,
        source_sha256=Component.source.sha256,
        provenance=Provenance(FormatId, Target),
        attributes={
            "freecad": NativeObjectA(TargetObj) if TargetObj is not None else {},
            "brep_payload_ids": OwnerPayloads.get(Target, []),
            "linked_object": LinkedObject(LinkObj),
        },
    )
    return (DefinitionId, ComponentDoc(DocId, Component), Definition)


# this definition builds one component occurrence from a native link object
def MakeInstance(
    LinkObj: NativeObject,
    DefinitionId: str,
    RootDefinitionId: str,
    Order: int,
    GroundedByTarget: Mapping[str, NativeObject],
) -> ComponentInstance:
    Linked = LinkedObject(LinkObj)
    Grounded = GroundedByTarget.get(LinkObj.name)
    return ComponentInstance(
        f"freecad:instance:{LinkObj.name}",
        String(LinkObj, "Label", LinkObj.name),
        DefinitionId,
        RootDefinitionId,
        MatrixFour(PlacementMatrix(PlacementElem(LinkObj, "Placement"))),
        order=Order,
        reference_number=str(Order + 1),
        hidden=not IsBoolValue(LinkObj, "Visibility", True),
        fixed=Grounded is not None,
        provenance=Provenance(FormatId, LinkObj.name),
        attributes={
            "freecad": NativeObjectA(LinkObj),
            "linked_object": Linked,
            "link_placement": list(
                PlacementMatrix(PlacementElem(LinkObj, "LinkPlacement"))
            ),
            "grounded_joint": NativeObjectA(Grounded) if Grounded is not None else {},
        },
    )


# this definition builds component definitions documents instances and lookup ids
def BuildComponents(
    Native: NativeArchive,
    RootValue: NativeObject,
    Objects: Mapping[str, NativeObject],
    OwnerPayloads: Mapping[str, list[str]],
    BrepPayloads: tuple[BrepPayload, ...],
    OuterDocuments: Mapping[str, tuple[str, CadDoc]],
    GroundedByTarget: Mapping[str, NativeObject],
) -> tuple[
    list[ComponentDefinition],
    list[ComponentDoc],
    list[ComponentInstance],
    dict[str, str],
]:
    RootDefinitionId = f"freecad:definition:{RootValue.name}"
    Definitions = [
        ComponentDefinition(
            RootDefinitionId,
            String(RootValue, "Label", RootValue.name),
            ComponentKind.ASSEMBLY,
            provenance=Provenance(FormatId, RootValue.name),
            attributes={"freecad": NativeObjectA(RootValue)},
        )
    ]
    DefinitionIds: dict[tuple[str, str], str] = {}
    Documents: list[ComponentDoc] = []
    Instances: list[ComponentInstance] = []
    InstanceIds: dict[str, str] = {}
    for Order, LinkObj in enumerate(AssemblyLinks(Native, Objects, RootValue)):
        Linked = LinkedObject(LinkObj)
        Target = str(Linked["name"]) or LinkObj.name
        SourceFile = str(Linked["file"]).replace("\\", "/")
        Outer = OuterDocuments.get(str(Linked["file"]))
        SourceIdentity = (
            Outer[0]
            if Outer is not None
            else PurePosixPath(SourceFile).as_posix() if SourceFile else ""
        )
        DefinitionKey = (SourceIdentity, Target)
        DefinitionId = DefinitionIds.get(DefinitionKey)
        if DefinitionId is None:
            DefinitionId, Document, Definition = MakeDefinition(
                LinkObj,
                Target,
                SourceFile,
                SourceIdentity,
                Outer,
                Objects,
                OwnerPayloads,
                BrepPayloads,
            )
            DefinitionIds[DefinitionKey] = DefinitionId
            Documents.append(Document)
            Definitions.append(Definition)
        Instance = MakeInstance(
            LinkObj, DefinitionId, RootDefinitionId, Order, GroundedByTarget
        )
        InstanceIds[LinkObj.name] = Instance.id
        Instances.append(Instance)
    return (Definitions, Documents, Instances, InstanceIds)


# this definition resolves a native joint type to the interchange mate kind
def JointKind(ObjValue: NativeObject) -> MateKind | str:
    StoredKind = String(ObjValue, "MateType")
    if StoredKind:
        try:
            return MateKind(StoredKind)
        except ValueError:
            return StoredKind
    return MateKindByJointType.get(Enumeration(ObjValue, "JointType"), MateKind.NATIVE)


# this definition builds mate entities and preserves native reference metadata
def JointRefsMut(
    ObjValue: NativeObject,
    RootDefinitionId: str,
    InstanceIds: Mapping[str, str],
    MateEntities: list[MateEntity],
) -> tuple[list[str], list[dict[str, AnyValue]]]:
    EntityIds: list[str] = []
    References: list[dict[str, AnyValue]] = []
    for RefIndex, PropName in enumerate(JointRefProperties, start=1):
        RefValue = XlinkData(ObjValue, PropName)
        References.append(RefValue)
        Placement = PlacementElem(ObjValue, f"Placement{RefIndex}")
        Frame = None if Placement is None else MatrixFour(PlacementMatrix(Placement))
        for SubIndex, SubElem in enumerate(RefValue["subelements"]):
            ComponentName, Separator, SourceEntityId = str(SubElem).partition(".")
            if not Separator:
                SourceEntityId = ComponentName
                ComponentName = ""
            EntityId = f"freecad:mate-entity:{ObjValue.name}:{RefIndex}:{SubIndex}"
            EntityIds.append(EntityId)
            MateEntities.append(
                MateEntity(
                    EntityId,
                    RootDefinitionId,
                    (
                        (InstanceIds[ComponentName],)
                        if ComponentName in InstanceIds
                        else ()
                    ),
                    MateEntityKindA(SourceEntityId),
                    source_entity_id=SourceEntityId,
                    frame=Frame,
                    provenance=Provenance(FormatId, f"{ObjValue.name}.{PropName}"),
                    attributes={
                        "freecad_reference": RefValue,
                        "freecad_subelement": SubElem,
                        "reference_property": PropName,
                    },
                )
            )
    return (EntityIds, References)


# this definition builds one native joint mate and its dimensional parameters
def MakeMateMut(
    ObjValue: NativeObject,
    Order: int,
    RootDefinitionId: str,
    InstanceIds: Mapping[str, str],
    MateEntities: list[MateEntity],
    Parameters: list[Parameter],
    Consumed: set[tuple[str, str]],
) -> MateRule | None:
    MateId = f"freecad:mate:{ObjValue.name}"
    KindValue = JointKind(ObjValue)
    EntityIds, References = JointRefsMut(
        ObjValue, RootDefinitionId, InstanceIds, MateEntities
    )
    Value, ParamIds = MateValuesMut(ObjValue, KindValue, MateId, Parameters, Consumed)
    StoredValue = StoredMateValue(ObjValue)
    if StoredValue is not None:
        Value = StoredValue
    if not EntityIds:
        return None
    return MateRule(
        MateId,
        String(ObjValue, "Label", ObjValue.name),
        KindValue,
        RootDefinitionId,
        tuple(EntityIds),
        order=Order,
        value=Value,
        parameter_ids=ParamIds,
        alignment=String(ObjValue, "Alignment", "unknown"),
        suppressed=IsBoolValue(
            ObjValue, "SourceSuppressed", IsBoolValue(ObjValue, "Suppressed")
        ),
        driving=IsBoolValue(ObjValue, "Driving", True),
        provenance=Provenance(FormatId, ObjValue.name),
        attributes={
            "freecad": NativeObjectA(ObjValue),
            "joint_type": Enumeration(ObjValue, "JointType"),
            "references": References,
        },
    )


# this definition builds all non grounded mate rules in native joint order
def BuildMatesMut(
    JointObjects: Sequence[NativeObject],
    RootDefinitionId: str,
    InstanceIds: Mapping[str, str],
    Parameters: list[Parameter],
    Consumed: set[tuple[str, str]],
) -> tuple[list[MateEntity], list[MateRule], dict[str, str]]:
    MateEntities: list[MateEntity] = []
    Mates: list[MateRule] = []
    MateIdsByName: dict[str, str] = {}
    for Order, ObjValue in enumerate(JointObjects):
        if IsGroundedJoint(ObjValue):
            continue
        MateId = f"freecad:mate:{ObjValue.name}"
        MateIdsByName[ObjValue.name] = MateId
        MateValue = MakeMateMut(
            ObjValue,
            Order,
            RootDefinitionId,
            InstanceIds,
            MateEntities,
            Parameters,
            Consumed,
        )
        if MateValue is not None:
            Mates.append(MateValue)
    return (MateEntities, Mates, MateIdsByName)


# this definition builds the optional native mate group with preserved ordering
def MateGroupSet(
    JointGroup: NativeObject | None,
    JointNames: Sequence[str],
    MateIdsByName: Mapping[str, str],
    Mates: Sequence[MateRule],
    RootDefinitionId: str,
) -> tuple[MateGroup, ...]:
    Groups: tuple[MateGroup, ...] = ()
    if Mates and JointGroup is not None:
        GroupId = f"freecad:mate-group:{JointGroup.name}"
        OrderedMateIds = tuple(
            (
                MateIdsByName[NameValue]
                for NameValue in JointNames
                if NameValue in MateIdsByName
                and any(
                    (MateValue.id == MateIdsByName[NameValue] for MateValue in Mates)
                )
            )
        )
        Groups = (
            MateGroup(
                GroupId,
                String(JointGroup, "Label", JointGroup.name),
                RootDefinitionId,
                OrderedMateIds,
                provenance=Provenance(FormatId, JointGroup.name),
                attributes={"freecad": NativeObjectA(JointGroup)},
            ),
        )
    return Groups


# this definition coordinates native assembly component and mate decoding
def ParseAsm(
    Native: _NativeArchive,
    OwnerPayloads: dict[str, list[str]],
    BrepPayloads: tuple[BrepPayload, ...],
    OuterDocuments: dict[str, tuple[str, CadDocument]],
    UnresolvedOuter: list[dict[str, str]],
    Parameters: list[Parameter],
    ConsumedExpressions: set[tuple[str, str]],
) -> AsmData | None:
    RootValue = AsmRootObject(Native.objects)
    if RootValue is None:
        return None
    Objects = {ObjValue.name: ObjValue for ObjValue in Native.objects}
    RootDefinitionId = f"freecad:definition:{RootValue.name}"
    JointGroup, JointNames, JointObjects, GroundedByTarget = JointContext(
        Native, Objects
    )
    Definitions, Documents, Instances, InstanceIds = BuildComponents(
        Native,
        RootValue,
        Objects,
        OwnerPayloads,
        BrepPayloads,
        OuterDocuments,
        GroundedByTarget,
    )
    MateEntities, Mates, MateIdsByName = BuildMatesMut(
        JointObjects,
        RootDefinitionId,
        InstanceIds,
        Parameters,
        ConsumedExpressions,
    )
    Groups = MateGroupSet(
        JointGroup, JointNames, MateIdsByName, Mates, RootDefinitionId
    )
    return AsmData(
        RootDefinitionId,
        tuple(Definitions),
        tuple(Instances),
        documents=tuple(Documents),
        mate_entities=tuple(MateEntities),
        mates=tuple(Mates),
        mate_groups=Groups,
        attributes={
            "freecad": NativeObjectA(RootValue),
            "unresolved_external_documents": UnresolvedOuter,
        },
    )


# this definition exists because focused behavior needs one stable owner
def RemainingMut(
    Objects: tuple[_NativeObject, ...],
    Parameters: list[Parameter],
    Consumed: set[tuple[str, str]],
) -> None:
    ExistingIds = {ParamItem.id for ParamItem in Parameters}
    for ObjValue in Objects:
        for PathValue, Source in ReadExpressions(ObjValue).items():
            if (ObjValue.name, PathValue) in Consumed:
                continue
            BaseValue = (
                RegexLib.sub("[^A-Za-z0-9_.:-]+", "_", PathValue).strip("_")
                or "expression"
            )
            ParamId = f"freecad:parameter:{ObjValue.name}:expression:{BaseValue}"
            Suffix = 2
            while ParamId in ExistingIds:
                ParamId = (
                    f"freecad:parameter:{ObjValue.name}:expression:{BaseValue}:{Suffix}"
                )
                Suffix += 1
            ExistingIds.add(ParamId)
            Parameters.append(
                Param(
                    ParamId,
                    f"{String(ObjValue, 'Label', ObjValue.name)}.{PathValue}",
                    ParamValue(0.0, ValueKind.NUMBER),
                    expression=Expression(Source, language="freecad"),
                    owner_id=f"freecad:object:{ObjValue.name}",
                    attributes={"freecad_path": PathValue},
                )
            )


# this definition exists because focused behavior needs one stable owner
def BuildConfigs(
    Objects: tuple[_NativeObject, ...], FeatureIds: dict[str, str]
) -> tuple[Config, ...]:
    Values = [
        ObjValue for ObjValue in Objects if String(ObjValue, "KitConfigurationId")
    ]
    if not Values:
        return (Config("freecad:configuration:default", "Default", active=True),)
    IdsValue = {
        ObjValue.name: String(ObjValue, "KitConfigurationId") for ObjValue in Values
    }
    return tuple(
        (
            Config(
                IdsValue[ObjValue.name],
                String(ObjValue, "Label", ObjValue.name),
                active=IsBoolValue(ObjValue, "Active"),
                parent_id=IdsValue.get(LinkAction(ObjValue, "ParentConfiguration")),
                suppressed_feature_ids=tuple(
                    (
                        FeatureIds[NameValue]
                        for NameValue in LinkList(ObjValue, "SuppressedFeatures")
                        if NameValue in FeatureIds
                    )
                ),
                attributes={"freecad": NativeObjectA(ObjValue)},
            )
            for ObjValue in Values
        )
    )


# this definition exists because focused behavior needs one stable owner
def ReadNativeFcstd(
    DataValue: bytes,
    SourcePath: str = "",
    *,
    StateValue: _ExternalState | None = None,
    OuterDepth: int = 0,
) -> CadDoc:
    Native = LoadNative(DataValue)
    SourceFile = ResolvedSource(SourcePath)
    OuterStateA = StateValue
    if OuterStateA is None and SourceFile is not None:
        OuterStateA = OuterState(SourceFile.parent, {}, {SourceFile}, 1, len(DataValue))
    ResolvedOuter, UnresolvedOuter = OuterDocsMut(
        Native, SourcePath, OuterStateA, OuterDepth
    )
    Parameters: list[Param] = []
    ConsumedExpressions: set[tuple[str, str]] = set()
    SupportPlanes, Sketches = ParseSketchMut(
        Native.objects, Parameters, ConsumedExpressions
    )
    SketchIds = {
        ObjValue.name: f"freecad:sketch:{ObjValue.name}"
        for ObjValue in Native.objects
        if ObjValue.type_id == SketchTypeId
    }
    FeatureObjects = OrderedFeatures(Native.objects)
    FeatureIds = {
        ObjValue.name: f"freecad:feature:{ObjValue.name}" for ObjValue in FeatureObjects
    }
    BodyIds = {
        ObjValue.name: f"freecad:body:{ObjValue.name}"
        for ObjValue in Native.objects
        if IsBodyContainer(ObjValue)
    }
    BrepPayloads, OwnerPayloads = BuildBrep(Native, FeatureIds, BodyIds)
    NativeDigestText = Hashlib.sha256(DataValue).hexdigest()
    BrepPayloads = tuple(
        (
            Replace(
                Payload,
                attributes={
                    **Payload.attributes,
                    KNativeDocHashAttr: NativeDigestText,
                },
            )
            for Payload in BrepPayloads
        )
    )
    Meshes = ParseMeshes(Native)
    Features: list[FeatureStep] = []
    Selections: list[Selection] = list(Explicit(Native.objects))
    for Order, ObjValue in enumerate(FeatureObjects):
        FeatureId = FeatureIds[ObjValue.name]
        KindValue = FeatureKindA(ObjValue)
        FeatureSelections = FeatureA(ObjValue)
        Selections.extend(FeatureSelections)
        ParamIds = FeatureMut(ObjValue, FeatureId, Parameters, ConsumedExpressions)
        Dependencies = tuple(
            (
                FeatureIds[Value]
                for Value in dict.fromkeys(ObjValue.dependencies)
                if Value in FeatureIds
                and FeatureObjects.index(
                    next(
                        (
                            ItemValue
                            for ItemValue in FeatureObjects
                            if ItemValue.name == Value
                        )
                    )
                )
                < Order
            )
        )
        Profile = LinkAction(ObjValue, "Profile") or LinkAction(ObjValue, "Base")
        SketchId = SketchIds.get(Profile)
        Operation: BoolOperation | str | None = None
        DeclaredOperation = String(ObjValue, "Operation").casefold()
        if DeclaredOperation:
            try:
                Operation = BoolOperation(DeclaredOperation)
            except ValueError:
                Operation = DeclaredOperation
        Definition: FeatureDefinition | None = None
        if KindValue in KSubtractiveCapableKinds:
            if ObjValue.type_id in KSubtractiveTypeIds:
                Operation = BoolOperation.CUT
            elif Dependencies:
                Operation = BoolOperation.JOIN
            else:
                Operation = BoolOperation.CREATE
        if KindValue == FeatureKind.EXTRUSION:
            Definition = (
                PartExtrusion(ObjValue)
                if ObjValue.type_id == "Part::Extrusion"
                else Extrusion(ObjValue)
            )
        elif KindValue == FeatureKind.FILLET:
            Radius = Float(ObjValue, "Radius", Float(ObjValue, "DrivingRadius"))
            Definition = FilletFeature(ParamValue(abs(Radius), ValueKind.LENGTH, "mm"))
        elif KindValue == FeatureKind.CHAMFER:
            ChamferType = EnumAction(ObjValue, "ChamferType")
            ChamferMode = {
                0: "equal_distance",
                1: "two_distances",
                2: "distance_angle",
            }.get(ChamferType, f"native:{ChamferType}")
            Definition = ChamferFeature(
                distance=ParamValue(
                    abs(Float(ObjValue, "Size")), ValueKind.LENGTH, "mm"
                ),
                mode=ChamferMode,
                second_distance=(
                    ParamValue(abs(Float(ObjValue, "Size2")), ValueKind.LENGTH, "mm")
                    if ChamferType == 1
                    else None
                ),
                angle=(
                    ParamValue(abs(Float(ObjValue, "Angle")), ValueKind.ANGLE, "deg")
                    if ChamferType == 2
                    else None
                ),
            )
        elif KindValue == FeatureKind.SHELL:
            Definition = ShellFeature(
                thickness=ParamValue(
                    abs(Float(ObjValue, "Value")), ValueKind.LENGTH, "mm"
                ),
                outward=not IsBoolValue(ObjValue, "Reversed"),
            )
        elif ObjValue.type_id == "PartDesign::LinearPattern":
            ItemCount = EnumAction(ObjValue, "Occurrences", 1)
            LengthValue = abs(Float(ObjValue, "Length"))
            OffsetValue = abs(Float(ObjValue, "Offset"))
            SpacingValue = (
                LengthValue / (ItemCount - 1)
                if EnumAction(ObjValue, "Mode") == 0 and ItemCount > 1
                else OffsetValue
            )
            Definition = LinearPatternFeature(
                spacing=ParamValue(SpacingValue, ValueKind.LENGTH, "mm"),
                instance_count=ItemCount,
                direction_selection_id=(
                    FeatureSelections[0].id if FeatureSelections else ""
                ),
                reversed=IsBoolValue(ObjValue, "Reversed"),
            )
        elif ObjValue.type_id == "PartDesign::PolarPattern":
            Definition = CircularPatternFeature(
                angle=ParamValue(abs(Float(ObjValue, "Angle")), ValueKind.ANGLE, "deg"),
                instance_count=EnumAction(ObjValue, "Occurrences", 1),
                axis_selection_id=FeatureSelections[0].id if FeatureSelections else "",
                reversed=IsBoolValue(ObjValue, "Reversed"),
            )
        else:
            Definition = NativeFeatureDefinition(
                FormatId, ObjValue.type_id, NativeObjectA(ObjValue)
            )
        Features.append(
            FeatureStep(
                FeatureId,
                String(ObjValue, "Label", ObjValue.name),
                KindValue,
                Order,
                input_feature_ids=Dependencies,
                sketch_id=SketchId,
                parameter_ids=ParamIds,
                operation=Operation,
                definition=Definition,
                selection_ids=tuple(
                    (SelectionValue.id for SelectionValue in FeatureSelections)
                ),
                suppressed=IsBoolValue(ObjValue, "Suppressed"),
                provenance=Provenance(FormatId, ObjValue.name),
                attributes={
                    "freecad": NativeObjectA(ObjValue),
                    "brep_payload_ids": OwnerPayloads.get(ObjValue.name, []),
                },
            )
        )
    Bodies: list[BodyValue] = []
    for ObjValue in Native.objects:
        if not IsBodyContainer(ObjValue):
            continue
        FinalName = LinkAction(ObjValue, "Tip")
        if FinalName not in FeatureIds:
            FinalName = next(
                (
                    Value
                    for Value in reversed(LinkList(ObjValue, "Group"))
                    if Value in FeatureIds
                ),
                "",
            )
        if not FinalName:
            continue
        Bodies.append(
            BodyValue(
                BodyIds[ObjValue.name],
                String(ObjValue, "Label", ObjValue.name),
                FeatureIds[FinalName],
                TopologySummary(),
                material_id=String(ObjValue, "MaterialId") or None,
                provenance=Provenance(FormatId, ObjValue.name),
                attributes={
                    "freecad": NativeObjectA(ObjValue),
                    "tip": FinalName,
                    "brep_payload_ids": OwnerPayloads.get(ObjValue.name, []),
                },
            )
        )
    HasAsm = AsmRootObject(Native.objects) is not None
    if not Bodies and Features and (not HasAsm):
        Final = Features[-1]
        Bodies.append(
            BodyValue(
                "freecad:body:default",
                "Body",
                Final.id,
                attributes={"freecad_generated": True},
            )
        )
    DecodedBrep = DecodedDocBrep(BrepPayloads, tuple(Bodies))
    AsmValue = ParseAsm(
        Native,
        OwnerPayloads,
        BrepPayloads,
        ResolvedOuter,
        UnresolvedOuter,
        Parameters,
        ConsumedExpressions,
    )
    NativeDoc, NativeBinding = NativePayloads(Native, DataValue, SourcePath)
    BrepPayloads = (*BrepPayloads, NativeDoc, NativeBinding)
    RemainingMut(Native.objects, Parameters, ConsumedExpressions)
    NativeFeatureTypes = sorted(
        {
            ObjValue.type_id
            for ObjValue in FeatureObjects
            if FeatureKindA(ObjValue) == FeatureKind.NATIVE
        }
    )
    Diagnostics: tuple[DiagValue, ...] = (
        (
            DiagValue(
                "freecad.native_features_preserved",
                "FreeCAD feature types were preserved as native operations",
                Severity.INFO,
                attributes={"type_ids": NativeFeatureTypes},
            ),
        )
        if NativeFeatureTypes
        else ()
    )
    MeshPropCount = sum(
        (
            1
            for ObjValue in Native.objects
            for NodeValue in ObjValue.properties.values()
            if NodeValue.find("./Mesh") is not None
        )
    )
    if MeshPropCount > len(Meshes):
        Diagnostics += (
            DiagValue(
                "freecad.unparsed_mesh_data",
                "FreeCAD mesh data was preserved but could not be normalized",
                Severity.WARNING,
                attributes={
                    "property_count": MeshPropCount,
                    "normalized_count": len(Meshes),
                },
            ),
        )
    if UnresolvedOuter:
        Diagnostics += (
            DiagValue(
                "freecad.unresolved_external_documents",
                "FreeCAD external component documents could not be resolved",
                Severity.WARNING,
                attributes={"references": UnresolvedOuter},
            ),
        )
    Source = CadSource(
        FormatId,
        SourcePath,
        Hashlib.sha256(DataValue).hexdigest(),
        container_version=Native.root.get("FileVersion", ""),
        application_version=Native.root.get("ProgramVersion", ""),
        attributes={"freecad_schema_version": Native.root.get("SchemaVersion", "")},
    )
    FreecadMeta: dict[str, AnyValue] = {
        "schema_version": Native.root.get("SchemaVersion", ""),
        "file_version": Native.root.get("FileVersion", ""),
        "program_version": Native.root.get("ProgramVersion", ""),
        "entry_order": list(Native.entry_order),
        "objects": [NativeObjectA(ObjValue) for ObjValue in Native.objects],
    }
    DocProperties = Native.root.find("./Properties")
    if DocProperties is not None:
        FreecadMeta["document_properties"] = ElemData(DocProperties)
    StringHasher = ReadStringHash(Native)
    if StringHasher is not None:
        FreecadMeta["string_hasher"] = StringHasher
    OtherEntries = OtherEntryData(Native)
    if OtherEntries:
        FreecadMeta["entries"] = OtherEntries
    if AsmValue is None and ResolvedOuter:
        FreecadMeta["external_documents"] = [
            {"file": FileName, "identity": Identity, "document": LinkedDoc}
            for FileName, (Identity, LinkedDoc) in ResolvedOuter.items()
        ]
    Configurations = BuildConfigs(Native.objects, FeatureIds)
    DocValue = CadDoc(
        Source,
        Configurations,
        tuple(Parameters),
        SupportPlanes,
        Sketches,
        tuple(Selections),
        tuple(Features),
        tuple(Bodies),
        meshes=Meshes,
        brep=DecodedBrep,
        brep_payloads=BrepPayloads,
        diagnostics=Diagnostics,
        metadata={"freecad": FreecadMeta},
        assembly=AsmValue,
    )
    Capabilities = InferCapabilities(DocValue, roundtrip_metadata=True)
    if ResolvedOuter or UnresolvedOuter:
        Capabilities |= {Capability.EXTERNAL_REFERENCES}
    DocValue = Replace(DocValue, capabilities=Capabilities)
    DocValue.assert_valid()
    return DocValue


# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_JOINT_GROUP_TYPE_ID"] = AsmJointGroupTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_OBJECT_TYPE_PREFIX"] = AsmObjectTypePrefix

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_ROOT_TYPE_ID"] = AsmRootTypeId

# this binding exists because shared behavior needs one stable value
globals()["Any"] = AnyValue

# this binding exists because shared behavior needs one stable value
globals()["ArcEllipseGeometry"] = ArcEllipseGeom

# this binding exists because shared behavior needs one stable value
globals()["ArcGeometry"] = ArcGeom

# this binding exists because shared behavior needs one stable value
globals()["ArcHyperbolaGeometry"] = ArcHyperbolaGeom

# this binding exists because shared behavior needs one stable value
globals()["ArcParabolaGeometry"] = ArcParabolaGeom

# this binding exists because shared behavior needs one stable value
globals()["AssemblyData"] = AsmData

# this binding exists because shared behavior needs one stable value
globals()["BODY_CONTAINER_TYPE_IDS"] = BodyContainerTypeIds

# this binding exists because shared behavior needs one stable value
globals()["Body"] = BodyValue

# this binding exists because shared behavior needs one stable value
globals()["BooleanOperation"] = BoolOperation

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_KIND_BY_CODE"] = RuleKindByCode

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_POINT_BY_INDEX"] = RulePointByIndex

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_VALUE_KIND_BY_CODE"] = RuleValueKindByCode

# this binding exists because shared behavior needs one stable value
globals()["CadDocument"] = CadDoc

# this binding exists because shared behavior needs one stable value
globals()["CircleGeometry"] = CircleGeom

# this binding exists because shared behavior needs one stable value
globals()["ComponentDocument"] = ComponentDoc

# this binding exists because shared behavior needs one stable value
globals()["Configuration"] = Config

# this binding exists because shared behavior needs one stable value
globals()["ConstraintKind"] = RuleKind

# this binding exists because shared behavior needs one stable value
globals()["ConstraintReference"] = RuleRef

# this binding exists because shared behavior needs one stable value
globals()["DIMENSIONAL_CONSTRAINT_CODES"] = DimensionalRuleCodes

# this binding exists because shared behavior needs one stable value
globals()["DOCUMENT_ENTRY"] = DocEntry

# this binding exists because shared behavior needs one stable value
globals()["Diagnostic"] = DiagValue

# this binding exists because shared behavior needs one stable value
globals()["ET"] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()["EXTRUSION_TYPE_BY_CODE"] = ExtrusionTypeByCode

# this binding exists because shared behavior needs one stable value
globals()["EllipseGeometry"] = EllipseGeom

# this binding exists because shared behavior needs one stable value
globals()["FEATURE_KIND_BY_TYPE_ID"] = FeatureKindByTypeId

# this binding exists because shared behavior needs one stable value
globals()["FORMAT_ID"] = FormatId

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_KIND_BY_TYPE_ID"] = GeomKindByTypeId

# this binding exists because shared behavior needs one stable value
globals()["GeometryKind"] = GeomKind

# this binding exists because shared behavior needs one stable value
globals()["HyperbolaGeometry"] = HyperbolaGeom

# this binding exists because shared behavior needs one stable value
globals()["JOINT_GROUND_PROPERTY"] = JointGroundProp

# this binding exists because shared behavior needs one stable value
globals()["JOINT_REFERENCE_PROPERTIES"] = JointRefProperties

# this binding exists because shared behavior needs one stable value
globals()["JOINT_RESERVED_LINK_PROPERTIES"] = JointReservedLink

# this binding exists because shared behavior needs one stable value
globals()["JOINT_TYPE_PROPERTIES"] = JointTypeProperties

# this binding exists because shared behavior needs one stable value
globals()["LineGeometry"] = LineGeom

# this binding exists because shared behavior needs one stable value
globals()["MATE_KINDS_USING_DISTANCE"] = MateKindsUsingDistance

# this binding exists because shared behavior needs one stable value
globals()["MATE_KINDS_USING_SECOND_DISTANCE"] = MateKindsUsingSecond

# this binding exists because shared behavior needs one stable value
globals()["MATE_KIND_BY_JOINT_TYPE"] = MateKindByJointType

# this binding exists because shared behavior needs one stable value
globals()["MateConstraint"] = MateRule

# this binding exists because shared behavior needs one stable value
globals()["Matrix4"] = MatrixFour

# this binding exists because shared behavior needs one stable value
globals()["Mesh"] = MeshValue

# this binding exists because shared behavior needs one stable value
globals()["NATIVE_DOCUMENT_SHA256_ATTRIBUTE"] = KNativeDocHashAttr

# this binding exists because shared behavior needs one stable value
globals()["NON_FEATURE_OBJECT_TYPE_IDS"] = NonFeatureObjectTypeIds

# this binding exists because shared behavior needs one stable value
globals()["NativeFreeCADError"] = NativeFreeCad

# this binding exists because shared behavior needs one stable value
globals()["NativeGeometry"] = NativeGeom

# this binding exists because shared behavior needs one stable value
globals()["PERMISSIVE_TRUE_VALUES"] = PermissiveTrueValues

# this binding exists because shared behavior needs one stable value
globals()["POCKET_TYPE_ID"] = PocketTypeId

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
globals()["SCALAR_PROPERTY_KINDS"] = ScalarPropKinds

# this binding exists because shared behavior needs one stable value
globals()["SKETCH_TYPE_ID"] = SketchTypeId

# this binding exists because shared behavior needs one stable value
globals()["SPLINE_GEOMETRY_TYPE_IDS"] = SplineGeomTypeIds

# this binding exists because shared behavior needs one stable value
globals()["STRING_HASHER_TAGS"] = StringHasherTags

# this binding exists because shared behavior needs one stable value
globals()["SUBELEMENT_KIND_BY_PREFIX"] = SubElemKindByPrefix

# this binding exists because shared behavior needs one stable value
globals()["SUFFIX"] = Suffix

# this binding exists because shared behavior needs one stable value
globals()["SUPPORT_PLANE_TYPE_IDS"] = SupportPlaneTypeIds

# this binding exists because shared behavior needs one stable value
globals()["SelectionPathElement"] = SelectionPathElem

# this binding exists because shared behavior needs one stable value
globals()["SketchConstraint"] = SketchRule

# this binding exists because shared behavior needs one stable value
globals()["SplineGeometry"] = SplineGeom

# this binding exists because shared behavior needs one stable value
globals()["Vector2"] = VectorTwo

# this binding exists because shared behavior needs one stable value
globals()["Vector3"] = VectorThree

# this binding exists because shared behavior needs one stable value
globals()["XML_TRUE_VALUES"] = XmlTrueValues

# this binding exists because shared behavior needs one stable value
globals()["_ExternalState"] = OuterState

# this binding exists because shared behavior needs one stable value
globals()["_GROOVE_TYPE_ID"] = KGrooveTypeId

# this binding exists because shared behavior needs one stable value
globals()["_MAX_ENTRY_SIZE"] = MaxEntrySize

# this binding exists because shared behavior needs one stable value
globals()["_MAX_EXTERNAL_DEPTH"] = KMaxOuterDepth

# this binding exists because shared behavior needs one stable value
globals()["_MAX_EXTERNAL_FILES"] = MaxOuterFiles

# this binding exists because shared behavior needs one stable value
globals()["_MAX_TOTAL_SIZE"] = MaxTotalSize

# this binding exists because shared behavior needs one stable value
globals()["_MIN_OBJECT_GRAPH_SCHEMA_VERSION"] = KMinObjectGraphSchema

# this binding exists because shared behavior needs one stable value
globals()["_NativeArchive"] = NativeArchive

# this binding exists because shared behavior needs one stable value
globals()["_NativeObject"] = NativeObject

# this binding exists because shared behavior needs one stable value
globals()["_ORIGIN_PLANE_FRAMES"] = KOriginPlaneFrames

# this binding exists because shared behavior needs one stable value
globals()["_SUBTRACTIVE_CAPABLE_KINDS"] = KSubtractiveCapableKinds

# this binding exists because shared behavior needs one stable value
globals()["_SUBTRACTIVE_TYPE_IDS"] = KSubtractiveTypeIds

# this binding exists because shared behavior needs one stable value
globals()["_archive_members"] = ArchiveMembers

# this binding exists because shared behavior needs one stable value
globals()["_assembly_root_object"] = AsmRootObject

# this binding exists because shared behavior needs one stable value
globals()["_bool"] = IsBoolValue

# this binding exists because shared behavior needs one stable value
globals()["_build_brep_payloads"] = BuildBrep

# this binding exists because shared behavior needs one stable value
globals()["_child"] = FindChild

# this binding exists because shared behavior needs one stable value
globals()["_closed_profile_entity_ids"] = ClosedProfile

# this binding exists because shared behavior needs one stable value
globals()["_constraint_element_slots"] = RuleElemSlots

# this binding exists because shared behavior needs one stable value
globals()["_constraint_expression"] = RuleExpression

# this binding exists because shared behavior needs one stable value
globals()["_declared_count"] = DeclaredCount

# this binding exists because shared behavior needs one stable value
globals()["_decoded_document_brep"] = DecodedDocBrep

# this binding exists because shared behavior needs one stable value
globals()["_dot"] = DotAction

# this binding exists because shared behavior needs one stable value
globals()["_element_data"] = ElemData

# this binding exists because shared behavior needs one stable value
globals()["_embedded_component_document"] = EmbeddedDoc

# this binding exists because shared behavior needs one stable value
globals()["_entry_name"] = EntryName

# this binding exists because shared behavior needs one stable value
globals()["_enum"] = EnumAction

# this binding exists because shared behavior needs one stable value
globals()["_enumeration_choice"] = Enumeration

# this binding exists because shared behavior needs one stable value
globals()["_explicit_selections"] = Explicit

# this binding exists because shared behavior needs one stable value
globals()["_expressions"] = ReadExpressions

# this binding exists because shared behavior needs one stable value
globals()["_external_documents"] = OuterDocsMut

# this binding exists because shared behavior needs one stable value
globals()["_extrusion_definition"] = Extrusion

# this binding exists because shared behavior needs one stable value
globals()["_extrusion_end_condition"] = ExtrusionEnd

# this binding exists because shared behavior needs one stable value
globals()["_feature_kind"] = FeatureKindA

# this binding exists because shared behavior needs one stable value
globals()["_feature_parameters"] = FeatureMut

# this binding exists because shared behavior needs one stable value
globals()["_feature_selections"] = FeatureA

# this binding exists because shared behavior needs one stable value
globals()["_float"] = Float

# this binding exists because shared behavior needs one stable value
globals()["_geometry"] = GeomAction

# this binding exists because shared behavior needs one stable value
globals()["_geometry_axis"] = GeomAxis

# this binding exists because shared behavior needs one stable value
globals()["_has_shape_property"] = HasShapeProp

# this binding exists because shared behavior needs one stable value
globals()["_integer"] = Integer

# this binding exists because shared behavior needs one stable value
globals()["_is_assembly_link_object"] = IsAsmLinkObject

# this binding exists because shared behavior needs one stable value
globals()["_is_body_container"] = IsBodyContainer

# this binding exists because shared behavior needs one stable value
globals()["_is_feature_object"] = IsFeatureObject

# this binding exists because shared behavior needs one stable value
globals()["_is_grounded_joint_object"] = IsGroundedJoint

# this binding exists because shared behavior needs one stable value
globals()["_is_joint_object"] = IsJointObject

# this binding exists because shared behavior needs one stable value
globals()["_is_link_object"] = IsLinkObject

# this binding exists because shared behavior needs one stable value
globals()["_is_reparse_path"] = IsReparsePath

# this binding exists because shared behavior needs one stable value
globals()["_is_support_plane_object"] = IsSupportPlane

# this binding exists because shared behavior needs one stable value
globals()["_joint_group_object"] = FindJointGroup

# this binding exists because shared behavior needs one stable value
globals()["_link"] = LinkAction

# this binding exists because shared behavior needs one stable value
globals()["_link_list"] = LinkList

# this binding exists because shared behavior needs one stable value
globals()["_linked_object_data"] = LinkedObject

# this binding exists because shared behavior needs one stable value
globals()["_linked_object_property"] = LinkedObjectA

# this binding exists because shared behavior needs one stable value
globals()["_load_native_archive"] = LoadNative

# this binding exists because shared behavior needs one stable value
globals()["_mate_entity_kind"] = MateEntityKindA

# this binding exists because shared behavior needs one stable value
globals()["_mate_values"] = MateValuesMut

# this binding exists because shared behavior needs one stable value
globals()["_native_configurations"] = BuildConfigs

# this binding exists because shared behavior needs one stable value
globals()["_native_document_payloads"] = NativePayloads

# this binding exists because shared behavior needs one stable value
globals()["_native_object_data"] = NativeObjectA

# this binding exists because shared behavior needs one stable value
globals()["_number"] = Number

# this binding exists because shared behavior needs one stable value
globals()["_ordered_features"] = OrderedFeatures

# this binding exists because shared behavior needs one stable value
globals()["_origin_plane_frame"] = OriginPlane

# this binding exists because shared behavior needs one stable value
globals()["_other_entry_data"] = OtherEntryData

# this binding exists because shared behavior needs one stable value
globals()["_parse_assembly"] = ParseAsm

# this binding exists because shared behavior needs one stable value
globals()["_parse_meshes"] = ParseMeshes

# this binding exists because shared behavior needs one stable value
globals()["_parse_objects"] = ParseObjects

# this binding exists because shared behavior needs one stable value
globals()["_parse_sketches"] = ParseSketchMut

# this binding exists because shared behavior needs one stable value
globals()["_part_extrusion_definition"] = PartExtrusion

# this binding exists because shared behavior needs one stable value
globals()["_placement_element"] = PlacementElem

# this binding exists because shared behavior needs one stable value
globals()["_placement_matrix"] = PlacementMatrix

# this binding exists because shared behavior needs one stable value
globals()["_plane_reframe"] = PlaneReframe

# this binding exists because shared behavior needs one stable value
globals()["_point_on_segment"] = IsPointOnSeg

# this binding exists because shared behavior needs one stable value
globals()["_points_close"] = IsPointClose

# this binding exists because shared behavior needs one stable value
globals()["_property_parameter_value"] = PropParamValue

# this binding exists because shared behavior needs one stable value
globals()["_proxy_class"] = ProxyClass

# this binding exists because shared behavior needs one stable value
globals()["_reframe_geometry"] = ReframeGeom

# this binding exists because shared behavior needs one stable value
globals()["_remaining_expressions"] = RemainingMut

# this binding exists because shared behavior needs one stable value
globals()["_resolved_source_path"] = ResolvedSource

# this binding exists because shared behavior needs one stable value
globals()["_segment_orientation"] = Segment

# this binding exists because shared behavior needs one stable value
globals()["_segments_intersect_or_touch"] = HasSegmentTouch

# this binding exists because shared behavior needs one stable value
globals()["_stored_count"] = StoredCount

# this binding exists because shared behavior needs one stable value
globals()["_stored_mate_value"] = StoredMateValue

# this binding exists because shared behavior needs one stable value
globals()["_string"] = String

# this binding exists because shared behavior needs one stable value
globals()["_string_hasher_data"] = ReadStringHash

# this binding exists because shared behavior needs one stable value
globals()["_support_target"] = SupportTarget

# this binding exists because shared behavior needs one stable value
globals()["_transform"] = TransformA

# this binding exists because shared behavior needs one stable value
globals()["_transform_close"] = IsTransformNear

# this binding exists because shared behavior needs one stable value
globals()["_validated_archive_members"] = ValidatedArchiveMembers

# this binding exists because shared behavior needs one stable value
globals()["_validated_document_xml"] = ValidatedDocXml

# this binding exists because shared behavior needs one stable value
globals()["_validated_entry_name"] = ValidatedEntryName

# this binding exists because shared behavior needs one stable value
globals()["_validated_object_name"] = ValidatedObjectName

# this binding exists because shared behavior needs one stable value
globals()["_xlink_data"] = XlinkData

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["dataclass"] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()["decode_ascii_brep"] = DecodeAsciiBrep

# this binding exists because shared behavior needs one stable value
globals()["extract_manifest_from_fcstd"] = ExtractManifestFromFcstd

# this binding exists because shared behavior needs one stable value
globals()["hashlib"] = Hashlib

# this binding exists because shared behavior needs one stable value
globals()["infer_capabilities"] = InferCapabilities

# this binding exists because shared behavior needs one stable value
globals()["json"] = JsonValue

# this binding exists because shared behavior needs one stable value
globals()["math"] = MathValue

# this binding exists because shared behavior needs one stable value
globals()["probe_native_fcstd"] = ProbeNative

# this binding exists because shared behavior needs one stable value
globals()["re"] = RegexLib

# this binding exists because shared behavior needs one stable value
globals()["read_native_fcstd"] = ReadNativeFcstd

# this binding exists because shared behavior needs one stable value
globals()["replace"] = Replace

# this binding exists because shared behavior needs one stable value
globals()["struct"] = Struct

# this binding exists because shared behavior needs one stable value
globals()["zipfile"] = Zipfile
