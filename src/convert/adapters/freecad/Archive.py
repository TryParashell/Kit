# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
import base64 as BaseSixFour
import copy as CopyValue
from dataclasses import dataclass as Dataclass, field as Field
import hashlib as Hashlib
import io as IoStream
import json as JsonValue
import math as MathValue
from pathlib import PurePosixPath
import re as RegexLib
import struct as Struct
import uuid as UuidValue
import xml.etree.ElementTree as XmlTree
import zipfile as Zipfile
import zlib as ZlibValue
from typing import Any as AnyValue, Mapping
from interchange import CadDocument as CadDoc
from convert.adapters.freecad.Brep import (
    FreeCADBrepWriteError as FreeCadBrepWriteError,
    brep_model_brep as BrepModelBrep,
    proven_ascii_brep as ProvenAsciiBrep,
    triangle_mesh_brep as TriangleMeshBrep,
)
from convert.adapters.freecad.Format import FORMAT_ID as FormatId
from convert.adapters.freecad.Protocol import (
    ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES as AsmConnectorPropPrefixes,
    ASSEMBLY_JOINT_GROUP_TYPE_ID as AsmJointGroupTypeId,
    ASSEMBLY_LINK_TYPE_ID as AsmLinkTypeId,
    ASSEMBLY_ROOT_TYPE_ID as AsmRootTypeId,
    APP_LINK_TYPE_ID as AppLinkTypeId,
    BOOLEAN_OPERATION_TYPE_BY_KIND as BoolOperationTypeByKind,
    CIRCULAR_GEOMETRY_KINDS as CircularGeomKinds,
    CONSTRAINT_CODE_BY_KIND as RuleCodeByKind,
    CONSTRAINT_POINT_INDEX_BY_NAME as RulePointIndexByName,
    CREATE_OPERATION_NAMES as CreateOperationNames,
    DIMENSIONAL_CONSTRAINT_CODES as DimensionalRuleCodes,
    FIXED_CONSTRAINT_KINDS as FixedRuleKinds,
    FREECAD_BREP_FORMAT_IDS as FreecadBrepFormatIds,
    GEOMETRY_TYPE_IDS_BY_KIND as GeomTypeIdsByKind,
    JOINT_GROUND_PROPERTY as JointGroundProp,
    JOINT_REFERENCE_INDEX_BY_PROPERTY as JointRefIndexByProp,
    JOINT_RESERVED_LINK_PROPERTIES as JointReservedLink,
    JOINT_TYPE_BY_MATE_KIND as JointTypeByMateKind,
    JOINT_TYPES as JointTypes,
    JOINT_TYPES_USING_DISTANCE as JointTypesUsingDistance,
    JOINT_TYPES_USING_SECOND_DISTANCE as JointTypesUsingSecond,
    MIDPOINT_REFERENCE_POINT_NAMES as MidpointRefPointNames,
    NEUTRAL_GEOMETRY_TYPE_BY_KIND as NeutralGeomTypeByKind,
    NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND as NeutralGeomTypeIdByKind,
    SKETCH_TYPE_ID as SketchTypeId,
    SPLINE_GEOMETRY_KINDS as SplineGeomKinds,
    SPLINE_CONTROL_TAGS as SplineControlTags,
    STRING_HASHER_TAGS as StringHasherTags,
)

# this binding exists because shared behavior needs one stable value
KManifestEntry = "interchange/document.json"

# this binding exists because shared behavior needs one stable value
KDocEntry = "Document.xml"

# this binding exists because shared behavior needs one stable value
KNativeDocShaTwoFiveSix = "freecad.native_document_sha256"

# this binding exists because shared behavior needs one stable value
KNativeBrepKey = tuple[str, str, str, str, str, str]

# this binding exists because shared behavior needs one stable value
KManifestDataProp = "KitManifestData"

# this binding exists because shared behavior needs one stable value
KManifestEncodingProp = "KitManifestEncoding"

# this binding exists because shared behavior needs one stable value
KManifestShaTwoFiveSixPrA = "KitManifestSHA256"

# this binding exists because shared behavior needs one stable value
KManifestEncoding = "zlib+base64+utf-8"

# this binding exists because shared behavior needs one stable value
KMaxEntries = 16384

# this binding exists because shared behavior needs one stable value
KMaxEntrySize = 512 * 1024 * 1024

# this binding exists because shared behavior needs one stable value
KMaxTotalSize = 1024 * 1024 * 1024

# this binding exists because shared behavior needs one stable value
KMaxDocSize = 512 * 1024 * 1024

# this binding exists because shared behavior needs one stable value
KMaxCompressionRatio = 500

# this binding exists because shared behavior needs one stable value
KMaxOuterFiles = 256

# this binding exists because shared behavior needs one stable value
KMaxManifestJsonDepth = 256

# this binding exists because shared behavior needs one stable value
KMaxXmlDepth = 256

# this binding exists because shared behavior needs one stable value
KMaxXmlNodes = 2000000

# this binding exists because shared behavior needs one stable value
KMinObjectGraphSchema = 2

# this binding exists because shared behavior needs one stable value
KTargetSchemaVersion = "4"

# this binding exists because shared behavior needs one stable value
KTargetProgramVersion = "1.0.2"

# this binding exists because shared behavior needs one stable value
KTargetFileVersion = "1"


# this definition exists because focused behavior needs one stable owner
def ValidatedEntry(NameValue: str) -> str:
    if not NameValue or "\\" in NameValue or "\x00" in NameValue:
        raise ValueError("FCStd archive contains an unsafe entry name")
    if any((PartValue in {"", ".", ".."} for PartValue in NameValue.split("/"))):
        raise ValueError("FCStd archive contains an unsafe entry name")
    PathValue = PurePosixPath(NameValue)
    if PathValue.is_absolute():
        raise ValueError("FCStd archive contains an unsafe entry name")
    if PathValue.parts and ":" in PathValue.parts[0]:
        raise ValueError("FCStd archive contains an unsafe entry name")
    return PathValue.as_posix()


# this definition exists because focused behavior needs one stable owner
def ValidatedObject(NameValue: str) -> str:
    if RegexLib.fullmatch("[A-Za-z_][A-Za-z0-9_]*", NameValue) is None:
        raise ValueError("FreeCAD object name is unsafe or invalid")
    return NameValue


# this definition exists because every archive entry needs the same security gate
def ValidateInfo(
    InfoValue: Zipfile.ZipInfo, Members: Mapping[str, Zipfile.ZipInfo]
) -> tuple[str, int]:
    NameValue = ValidatedEntry(
        InfoValue.filename.rstrip("/") if InfoValue.is_dir() else InfoValue.filename
    )
    if NameValue in Members:
        raise ValueError("FCStd archive contains duplicate entries")
    if InfoValue.flag_bits & 1:
        raise ValueError("FCStd archive contains an encrypted entry")
    ModeValue = InfoValue.external_attr >> 16 & 61440
    if ModeValue == 40960:
        raise ValueError("FCStd archive contains a symbolic link")
    if InfoValue.is_dir():
        return (NameValue, 0)
    if InfoValue.file_size < 0 or InfoValue.file_size > KMaxEntrySize:
        raise ValueError("FCStd archive entry exceeds safe limits")
    if InfoValue.file_size and InfoValue.compress_size <= 0:
        raise ValueError("FCStd archive has an invalid compressed entry")
    if (
        InfoValue.compress_size
        and InfoValue.file_size / InfoValue.compress_size > KMaxCompressionRatio
    ):
        raise ValueError("FCStd archive compression ratio is unsafe")
    return (NameValue, InfoValue.file_size)


# this definition exists because focused behavior needs one stable owner
def Validated(DataValue: bytes) -> tuple[Zipfile.ZipFile, dict[str, Zipfile.ZipInfo]]:
    try:
        Archive = Zipfile.ZipFile(IoStream.BytesIO(DataValue))
    except (OSError, Zipfile.BadZipFile) as ErrorInfo:
        raise ValueError("source is not an FCStd ZIP archive") from ErrorInfo
    Infos = Archive.infolist()
    if not Infos or len(Infos) > KMaxEntries:
        Archive.close()
        raise ValueError("FCStd archive entry count is outside safe limits")
    Members: dict[str, Zipfile.ZipInfo] = {}
    Total = 0
    try:
        for InfoValue in Infos:
            NameValue, FileSize = ValidateInfo(InfoValue, Members)
            Members[NameValue] = InfoValue
            Total += FileSize
            if Total > KMaxTotalSize:
                raise ValueError("FCStd archive exceeds safe limits")
        DocValue = Members.get(KDocEntry)
        if DocValue is not None and DocValue.file_size > KMaxDocSize:
            raise ValueError("FCStd archive has no safe Document.xml")
    except BaseException:
        Archive.close()
        raise
    return (Archive, Members)


# this definition exists because declared counts defend against malformed object graphs
def StoredCount(
    NodeValue: XmlTree.Element, Names: tuple[str, ...], Actual: int, Label: str
) -> None:
    Value = next(
        (
            NodeValue.get(NameValue)
            for NameValue in Names
            if NodeValue.get(NameValue) is not None
        ),
        None,
    )
    if Value is None:
        return
    try:
        Expected = int(Value)
    except ValueError as ErrorInfo:
        raise ValueError(f"FreeCAD {Label} count is invalid") from ErrorInfo
    if Expected != Actual:
        raise ValueError(f"FreeCAD {Label} count does not match its data")


# this definition exists because xml resource limits protect archive parsing
def ValidateXml(RootValue: XmlTree.Element) -> int:
    if RootValue.tag != "Document":
        raise ValueError("FreeCAD Document.xml has an invalid root")
    Count = 0
    Stack = [(RootValue, 1)]
    while Stack:
        NodeValue, Depth = Stack.pop()
        Count += 1
        if Count > KMaxXmlNodes:
            raise ValueError("FreeCAD Document.xml node count exceeds safe limits")
        if Depth > KMaxXmlDepth:
            raise ValueError("FreeCAD Document.xml nesting exceeds safe limits")
        Stack.extend(((Child, Depth + 1) for Child in NodeValue))
    try:
        SchemaVersion = int(RootValue.get("SchemaVersion", ""))
    except ValueError as ErrorInfo:
        raise ValueError(
            "FreeCAD Document.xml schema version is invalid"
        ) from ErrorInfo
    if SchemaVersion < KMinObjectGraphSchema:
        raise ValueError("FreeCAD Document.xml schema version is not supported")
    return SchemaVersion


# this definition exists because legacy documents need the modern graph shape
def GraphNodesMut(
    RootValue: XmlTree.Element, SchemaVersion: int
) -> tuple[XmlTree.Element, XmlTree.Element]:
    if SchemaVersion != 2:
        ObjectsNode = RootValue.find("./Objects")
        DataNode = RootValue.find("./ObjectData")
        if ObjectsNode is None or DataNode is None:
            raise ValueError("FreeCAD Document.xml has no object graph")
        return (ObjectsNode, DataNode)
    FeaturesNode = RootValue.find("./Features")
    FeatureDataNode = RootValue.find("./FeatureData")
    if FeaturesNode is None or FeatureDataNode is None:
        raise ValueError("FreeCAD Document.xml has no object graph")
    Features = FeaturesNode.findall("./Feature")
    FeatureData = FeatureDataNode.findall("./Feature")
    StoredCount(FeaturesNode, ("Count", "count"), len(Features), "feature")
    StoredCount(FeatureDataNode, ("Count", "count"), len(FeatureData), "feature data")
    ObjectsNode = XmlTree.Element(
        "Objects", {"Count": str(len(Features)), "Dependencies": "0"}
    )
    DataNode = XmlTree.Element("ObjectData", {"Count": str(len(FeatureData))})
    for Index, Feature in enumerate(Features, start=1):
        XmlTree.SubElement(
            ObjectsNode,
            "Object",
            {
                "type": Feature.get("type", ""),
                "name": Feature.get("name", ""),
                "id": str(Index),
            },
        )
    for Feature in FeatureData:
        ItemValue = XmlTree.SubElement(
            DataNode, "Object", {"name": Feature.get("name", "")}
        )
        ItemValue.extend(CopyValue.deepcopy(list(Feature)))
    RootValue.append(ObjectsNode)
    RootValue.append(DataNode)
    return (ObjectsNode, DataNode)


# this definition exists because object declarations establish graph identity
def ReadDeclNames(ObjectsNode: XmlTree.Element) -> set[str]:
    Declarations = ObjectsNode.findall("./Object")
    StoredCount(ObjectsNode, ("Count", "count"), len(Declarations), "object")
    DeclaredNames: set[str] = set()
    ObjectIds: set[str] = set()
    for DeclValue in Declarations:
        NameValue = DeclValue.get("name", "")
        TypeId = DeclValue.get("type", "")
        ObjectId = DeclValue.get("id", "")
        if not NameValue or not TypeId or NameValue in DeclaredNames:
            raise ValueError("FreeCAD object declarations are malformed")
        ValidatedObject(NameValue)
        if ObjectId and ObjectId in ObjectIds:
            raise ValueError("FreeCAD object declarations contain duplicate ids")
        DeclaredNames.add(NameValue)
        if ObjectId:
            ObjectIds.add(ObjectId)
    return DeclaredNames


# this definition exists because object data must match declared property counts
def ReadDataNames(DataNode: XmlTree.Element) -> set[str]:
    ObjectData = DataNode.findall("./Object")
    StoredCount(DataNode, ("Count", "count"), len(ObjectData), "object data")
    DataNames: set[str] = set()
    for ObjectElem in ObjectData:
        NameValue = ObjectElem.get("name", "")
        if not NameValue or NameValue in DataNames:
            raise ValueError("FreeCAD object data contains duplicate names")
        DataNames.add(NameValue)
        Properties = ObjectElem.find("./Properties")
        if Properties is None:
            raise ValueError(f"FreeCAD object {NameValue!r} has no properties")
        StoredCount(
            Properties,
            ("Count", "count"),
            len(Properties.findall("./Property")),
            "property",
        )
        StoredCount(
            Properties,
            ("TransientCount",),
            len(Properties.findall("./_Property")),
            "transient property",
        )
    return DataNames


# this definition exists because dependencies may only reference declared objects
def ValidateDeps(ObjectsNode: XmlTree.Element, DeclaredNames: set[str]) -> None:
    DependencyNames: set[str] = set()
    for Dependency in ObjectsNode.findall("./ObjectDeps"):
        NameValue = Dependency.get("Name", "")
        Values = [
            ItemValue.get("Name", "") for ItemValue in Dependency.findall("./Dep")
        ]
        if (
            not NameValue
            or NameValue in DependencyNames
            or NameValue not in DeclaredNames
        ):
            raise ValueError("FreeCAD dependency graph is malformed")
        if any((not Value or Value not in DeclaredNames for Value in Values)):
            raise ValueError("FreeCAD dependency graph has missing objects")
        StoredCount(Dependency, ("Count", "count"), len(Values), "dependency")
        DependencyNames.add(NameValue)


# this definition exists because xml file links must resolve inside the archive
def ValidateFiles(
    RootValue: XmlTree.Element, Members: Mapping[str, Zipfile.ZipInfo]
) -> None:
    Referenced: set[str] = set()
    for NodeValue in RootValue.findall(".//*[@file]"):
        if NodeValue.tag == "XLink":
            continue
        FileName = NodeValue.get("file", "")
        if FileName:
            Referenced.add(ValidatedEntry(FileName))
    Missing = sorted(Referenced.difference(Members))
    if Missing:
        raise ValueError(
            "FCStd archive is missing referenced data: " + ", ".join(Missing)
        )


# this definition exists because focused behavior needs one stable owner
def ValidatedDocXml(
    Archive: Zipfile.ZipFile, Members: Mapping[str, Zipfile.ZipInfo]
) -> tuple[XmlTree.Element, bytes]:
    DocInfo = Members.get(KDocEntry)
    if DocInfo is None or DocInfo.file_size > KMaxDocSize:
        raise ValueError("FCStd archive has no safe Document.xml")
    try:
        DocXml = Archive.read(DocInfo)
        RootValue = XmlTree.fromstring(DocXml)
    except (
        OSError,
        RuntimeError,
        NotImplementedError,
        XmlTree.ParseError,
        Zipfile.BadZipFile,
    ) as ErrorInfo:
        raise ValueError("FCStd archive has no readable Document.xml") from ErrorInfo
    SchemaVersion = ValidateXml(RootValue)
    ObjectsNode, DataNode = GraphNodesMut(RootValue, SchemaVersion)
    DeclaredNames = ReadDeclNames(ObjectsNode)
    if DeclaredNames != ReadDataNames(DataNode):
        raise ValueError("FreeCAD object declarations and data do not match")
    ValidateDeps(ObjectsNode, DeclaredNames)
    ValidateFiles(RootValue, Members)
    return (RootValue, DocXml)


# this definition exists because focused behavior needs one stable owner
def ManifestMapping(RawValue: bytes) -> dict[str, AnyValue]:
    try:
        Value = JsonValue.loads(RawValue)
    except RecursionError as ErrorInfo:
        raise ValueError(
            "embedded Kit interchange document JSON nesting exceeds safe limits"
        ) from ErrorInfo
    except (UnicodeDecodeError, JsonValue.JSONDecodeError) as ErrorInfo:
        raise ValueError("embedded Kit interchange document is corrupt") from ErrorInfo
    if not isinstance(Value, dict):
        raise ValueError("embedded Kit document is not a mapping")
    Stack = [(iter((Value,)), 0)]
    while Stack:
        Values, ParentDepth = Stack[-1]
        try:
            ItemValue = next(Values)
        except StopIteration:
            Stack.pop()
            continue
        if isinstance(ItemValue, dict):
            Depth = ParentDepth + 1
            if Depth > KMaxManifestJsonDepth:
                raise ValueError(
                    "embedded Kit interchange document JSON nesting exceeds safe limits"
                )
            Stack.append((iter(ItemValue.values()), Depth))
        elif isinstance(ItemValue, list):
            Depth = ParentDepth + 1
            if Depth > KMaxManifestJsonDepth:
                raise ValueError(
                    "embedded Kit interchange document JSON nesting exceeds safe limits"
                )
            Stack.append((iter(ItemValue), Depth))
    return Value


# this definition exists because focused behavior needs one stable owner
def EnumAction(Value: Any) -> AnyValue:
    if isinstance(Value, Mapping) and "$enum" in Value:
        return Value.get("value")
    return Value


# this definition exists because focused behavior needs one stable owner
def Items(Value: Any) -> list[dict[str, AnyValue]]:
    if isinstance(Value, Mapping):
        for Marker in ("$tuple", "$frozenset", "$set"):
            if Marker in Value:
                return Items(Value[Marker])
        if "$type" in Value:
            return [dict(Value)]
        return [
            dict(ItemValue)
            for ItemValue in Value.values()
            if isinstance(ItemValue, Mapping)
        ]
    if isinstance(Value, (list, tuple)):
        return [
            dict(ItemValue) for ItemValue in Value if isinstance(ItemValue, Mapping)
        ]
    return []


# this definition exists because focused behavior needs one stable owner
def Sequence(Value: Any) -> list[AnyValue]:
    if isinstance(Value, Mapping):
        for Marker in ("$tuple", "$frozenset", "$set"):
            if Marker in Value:
                return Sequence(Value[Marker])
        return []
    if isinstance(Value, (list, tuple)):
        return list(Value)
    return []


# this definition exists because focused behavior needs one stable owner
def Number(Value: Any, Default: float = 0.0) -> float:
    Value = EnumAction(Value)
    if isinstance(Value, Mapping):
        for KeyValue in ("value", "value_mm", "length_mm", "radius", "radius_mm"):
            if KeyValue in Value:
                return Number(Value[KeyValue], Default)
        return Default
    if isinstance(Value, bool):
        return float(Value)
    try:
        return float(Value)
    except (TypeError, ValueError):
        return Default


# this definition exists because focused behavior needs one stable owner
def TextAction(Value: Any, Default: str = "") -> str:
    Value = EnumAction(Value)
    if Value is None:
        return Default
    return str(Value)


# this definition exists because focused behavior needs one stable owner
def FmtAction(Value: Any) -> str:
    return f"{Number(Value):.16f}"


# this definition exists because focused behavior needs one stable owner
def SafeAction(Value: Any, Prefix: str = "Object") -> str:
    NameValue = RegexLib.sub("[^A-Za-z0-9_]", "_", TextAction(Value)).strip("_")
    if not NameValue:
        NameValue = Prefix
    if NameValue[0].isdigit():
        NameValue = f"{Prefix}_{NameValue}"
    return NameValue


# this definition exists because focused behavior needs one stable owner
def Vector(
    Value: Any, Default: tuple[float, float, float]
) -> tuple[float, float, float]:
    if isinstance(Value, Mapping):
        if "origin" in Value and (
            not any((KeyValue in Value for KeyValue in ("x", "y", "z")))
        ):
            return Vector(Value["origin"], Default)
        return (
            Number(Value.get("x"), Default[0]),
            Number(Value.get("y"), Default[1]),
            Number(Value.get("z"), Default[2]),
        )
    if isinstance(Value, (list, tuple)) and len(Value) >= 3:
        return (Number(Value[0]), Number(Value[1]), Number(Value[2]))
    return Default


# this definition exists because focused behavior needs one stable owner
def PointTwo(Value: Any) -> tuple[float, float]:
    if isinstance(Value, Mapping):
        return (Number(Value.get("x")), Number(Value.get("y")))
    if isinstance(Value, (list, tuple)) and len(Value) >= 2:
        return (Number(Value[0]), Number(Value[1]))
    return (0.0, 0.0)


# this definition exists because focused behavior needs one stable owner
def Normalize(Value: tuple[float, float, float]) -> tuple[float, float, float]:
    Length = MathValue.sqrt(sum((Component * Component for Component in Value)))
    if Length <= 1e-15:
        return (0.0, 0.0, 1.0)
    return tuple((Component / Length for Component in Value))


# this definition exists because axis frames need one normalized rotation matrix
def RotationMatrix(
    Transform: Mapping[str, Any],
) -> tuple[tuple[float, float, float], ...]:
    XAxis = Normalize(Vector(Transform.get("x_axis"), (1.0, 0.0, 0.0)))
    YAxis = Normalize(Vector(Transform.get("y_axis"), (0.0, 1.0, 0.0)))
    ZAxis = Normalize(Vector(Transform.get("z_axis"), (0.0, 0.0, 1.0)))
    return (
        (XAxis[0], YAxis[0], ZAxis[0]),
        (XAxis[1], YAxis[1], ZAxis[1]),
        (XAxis[2], YAxis[2], ZAxis[2]),
    )


# this definition exists because focused behavior needs one stable owner
def Quaternion(Transform: Mapping[str, Any]) -> tuple[float, float, float, float]:
    Matrix = RotationMatrix(Transform)
    Trace = Matrix[0][0] + Matrix[1][1] + Matrix[2][2]
    if Trace > 0.0:
        Scale = MathValue.sqrt(Trace + 1.0) * 2.0
        WidthValue = 0.25 * Scale
        FirstCoord = (Matrix[2][1] - Matrix[1][2]) / Scale
        SecondCoord = (Matrix[0][2] - Matrix[2][0]) / Scale
        ThirdCoord = (Matrix[1][0] - Matrix[0][1]) / Scale
    elif Matrix[0][0] > Matrix[1][1] and Matrix[0][0] > Matrix[2][2]:
        Scale = MathValue.sqrt(1.0 + Matrix[0][0] - Matrix[1][1] - Matrix[2][2]) * 2.0
        WidthValue = (Matrix[2][1] - Matrix[1][2]) / Scale
        FirstCoord = 0.25 * Scale
        SecondCoord = (Matrix[0][1] + Matrix[1][0]) / Scale
        ThirdCoord = (Matrix[0][2] + Matrix[2][0]) / Scale
    elif Matrix[1][1] > Matrix[2][2]:
        Scale = MathValue.sqrt(1.0 + Matrix[1][1] - Matrix[0][0] - Matrix[2][2]) * 2.0
        WidthValue = (Matrix[0][2] - Matrix[2][0]) / Scale
        FirstCoord = (Matrix[0][1] + Matrix[1][0]) / Scale
        SecondCoord = 0.25 * Scale
        ThirdCoord = (Matrix[1][2] + Matrix[2][1]) / Scale
    else:
        Scale = MathValue.sqrt(1.0 + Matrix[2][2] - Matrix[0][0] - Matrix[1][1]) * 2.0
        WidthValue = (Matrix[1][0] - Matrix[0][1]) / Scale
        FirstCoord = (Matrix[0][2] + Matrix[2][0]) / Scale
        SecondCoord = (Matrix[1][2] + Matrix[2][1]) / Scale
        ThirdCoord = 0.25 * Scale
    NormValue = MathValue.sqrt(
        FirstCoord * FirstCoord
        + SecondCoord * SecondCoord
        + ThirdCoord * ThirdCoord
        + WidthValue * WidthValue
    )
    return (
        FirstCoord / NormValue,
        SecondCoord / NormValue,
        ThirdCoord / NormValue,
        WidthValue / NormValue,
    )


# this definition exists because focused behavior needs one stable owner
def PropAction(
    NameValue: str, PropType: str, *, Dynamic: bool = False, Status: str | None = None
) -> XmlTree.Element:
    Attributes = {"name": NameValue, "type": PropType}
    if Dynamic:
        Attributes.update(
            {
                "group": "Kit",
                "doc": "",
                "attr": "0",
                "ro": "0",
                "hide": "0",
                "status": "2097152",
            }
        )
    elif Status is not None:
        Attributes["status"] = Status
    return XmlTree.Element("Property", Attributes)


# this definition exists because focused behavior needs one stable owner
def StringProp(NameValue: str, Value: Any, *, Dynamic: bool = False) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyString", Dynamic=Dynamic)
    XmlTree.SubElement(Result, "String", {"value": TextAction(Value)})
    return Result


# this definition exists because focused behavior needs one stable owner
def StringListProp(
    NameValue: str, Values: list[str], *, Dynamic: bool = False
) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyStringList", Dynamic=Dynamic)
    Child = XmlTree.SubElement(Result, "StringList", {"count": str(len(Values))})
    for Value in Values:
        XmlTree.SubElement(Child, "String", {"value": Value})
    return Result


# this definition exists because focused behavior needs one stable owner
def BoolProp(NameValue: str, Value: Any, *, Dynamic: bool = False) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyBool", Dynamic=Dynamic)
    XmlTree.SubElement(Result, "Bool", {"value": "true" if bool(Value) else "false"})
    return Result


# this definition exists because focused behavior needs one stable owner
def FloatProp(
    NameValue: str,
    Value: Any,
    PropType: str = "App::PropertyFloat",
    *,
    Dynamic: bool = False,
) -> XmlTree.Element:
    Result = PropAction(NameValue, PropType, Dynamic=Dynamic)
    XmlTree.SubElement(Result, "Float", {"value": FmtAction(Value)})
    return Result


# this definition exists because focused behavior needs one stable owner
def IntegerProp(
    NameValue: str, Value: Any, *, Dynamic: bool = False
) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyInteger", Dynamic=Dynamic)
    XmlTree.SubElement(Result, "Integer", {"value": str(int(Number(Value)))})
    return Result


# this definition exists because focused behavior needs one stable owner
def EnumerationProA(NameValue: str, Value: Any) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyEnumeration")
    XmlTree.SubElement(Result, "Integer", {"value": str(int(Number(Value)))})
    return Result


# this definition exists because focused behavior needs one stable owner
def VectorProp(
    NameValue: str, Value: tuple[float, float, float], *, Dynamic: bool = False
) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyVector", Dynamic=Dynamic)
    XmlTree.SubElement(
        Result,
        "PropertyVector",
        {
            "valueX": FmtAction(Value[0]),
            "valueY": FmtAction(Value[1]),
            "valueZ": FmtAction(Value[2]),
        },
    )
    return Result


# this definition exists because focused behavior needs one stable owner
def MakePlacement(
    NameValue: str,
    Transform: Mapping[str, Any],
    *,
    Dynamic: bool = False,
    Status: str | None = None,
) -> XmlTree.Element:
    Result = PropAction(
        NameValue, "App::PropertyPlacement", Dynamic=Dynamic, Status=Status
    )
    Origin = Vector(Transform.get("origin"), (0.0, 0.0, 0.0))
    FirstCoord, SecondCoord, ThirdCoord, WidthValue = Quaternion(Transform)
    Angle = 2.0 * MathValue.acos(max(-1.0, min(1.0, WidthValue)))
    SineValue = MathValue.sqrt(max(0.0, 1.0 - WidthValue * WidthValue))
    AxisValue = (
        (0.0, 0.0, 1.0)
        if SineValue <= 1e-12
        else (FirstCoord / SineValue, SecondCoord / SineValue, ThirdCoord / SineValue)
    )
    XmlTree.SubElement(
        Result,
        "PropertyPlacement",
        {
            "Px": FmtAction(Origin[0]),
            "Py": FmtAction(Origin[1]),
            "Pz": FmtAction(Origin[2]),
            "Q0": FmtAction(FirstCoord),
            "Q1": FmtAction(SecondCoord),
            "Q2": FmtAction(ThirdCoord),
            "Q3": FmtAction(WidthValue),
            "A": FmtAction(Angle),
            "Ox": FmtAction(AxisValue[0]),
            "Oy": FmtAction(AxisValue[1]),
            "Oz": FmtAction(AxisValue[2]),
        },
    )
    return Result


# this definition exists because focused behavior needs one stable owner
def LinkProp(NameValue: str, Target: str, *, Dynamic: bool = False) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyLink", Dynamic=Dynamic)
    XmlTree.SubElement(Result, "Link", {"value": Target})
    return Result


# this definition exists because focused behavior needs one stable owner
def LinkListProp(
    NameValue: str, Targets: list[str], *, Dynamic: bool = False
) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyLinkList", Dynamic=Dynamic)
    Child = XmlTree.SubElement(Result, "LinkList", {"count": str(len(Targets))})
    for Target in Targets:
        XmlTree.SubElement(Child, "Link", {"value": Target})
    return Result


# this definition exists because focused behavior needs one stable owner
def LinkSubListProp(
    NameValue: str, Targets: list[tuple[str, str]], *, Dynamic: bool = False
) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyLinkSubList", Dynamic=Dynamic)
    Child = XmlTree.SubElement(Result, "LinkSubList", {"count": str(len(Targets))})
    for Target, SubElem in Targets:
        XmlTree.SubElement(Child, "Link", {"obj": Target, "sub": SubElem})
    return Result


# this definition exists because focused behavior needs one stable owner
def XlinkProp(
    NameValue: str,
    Target: str,
    *,
    FileValue: str = "",
    Stamp: str = "",
    Status: str | None = "256",
) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyXLink", Status=Status)
    XmlTree.SubElement(
        Result, "XLink", {"file": FileValue, "stamp": Stamp, "name": Target}
    )
    return Result


# this definition exists because focused behavior needs one stable owner
def PythonProxyProp(Module: str, ClassName: str) -> XmlTree.Element:
    Result = PropAction("Proxy", "App::PropertyPythonObject")
    XmlTree.SubElement(
        Result,
        "Python",
        {"value": "bnVsbA==", "encoded": "yes", "module": Module, "class": ClassName},
    )
    return Result


# this definition exists because focused behavior needs one stable owner
def XlinkSubProp(
    NameValue: str, Target: str, Subelements: list[str], *, Dynamic: bool = False
) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyXLinkSub", Dynamic=Dynamic)
    Child = XmlTree.SubElement(
        Result,
        "XLink",
        {"file": "", "stamp": "", "name": Target, "count": str(len(Subelements))},
    )
    for SubElem in Subelements:
        XmlTree.SubElement(Child, "Sub", {"value": SubElem})
    return Result


# this definition exists because focused behavior needs one stable owner
def EnumerationProp(
    NameValue: str, Choices: list[str], Selected: int, *, Dynamic: bool = False
) -> XmlTree.Element:
    Result = PropAction(NameValue, "App::PropertyEnumeration", Dynamic=Dynamic)
    XmlTree.SubElement(
        Result, "Integer", {"value": str(Selected), "CustomEnum": "true"}
    )
    Values = XmlTree.SubElement(Result, "CustomEnumList", {"count": str(len(Choices))})
    for Choice in Choices:
        XmlTree.SubElement(Values, "Enum", {"value": Choice})
    return Result


# this definition exists because focused behavior needs one stable owner
def ExpressionProp(Expressions: list[tuple[str, str]]) -> XmlTree.Element:
    Result = PropAction(
        "ExpressionEngine", "App::PropertyExpressionEngine", Status="67108864"
    )
    Child = XmlTree.SubElement(
        Result, "ExpressionEngine", {"count": str(len(Expressions))}
    )
    for PathValue, Expression in Expressions:
        XmlTree.SubElement(
            Child, "Expression", {"path": PathValue, "expression": Expression}
        )
    return Result


# this definition exists because focused behavior needs one stable owner
def JsonProp(NameValue: str, Value: Any) -> XmlTree.Element:
    return StringProp(
        NameValue,
        JsonValue.dumps(
            Value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
        Dynamic=True,
    )


# this definition exists because focused behavior needs one stable owner
@Dataclass
class Object:
    locals().setdefault("__annotations__", {})
    __annotations__["type_id"] = "str"
    __annotations__["name"] = "str"
    __annotations__["object_id"] = "str"
    locals()["object_id"] = ""
    __annotations__["properties"] = "list[XmlTree.Element]"
    locals()["properties"] = Field(default_factory=list)
    __annotations__["transient_properties"] = "list[XmlTree.Element]"
    locals()["transient_properties"] = Field(default_factory=list)
    __annotations__["dependencies"] = "list[str]"
    locals()["dependencies"] = Field(default_factory=list)
    __annotations__["touched"] = "bool"
    locals()["touched"] = False
    __annotations__["extensions"] = "tuple[str, ...]"
    locals()["extensions"] = ()


# this definition exists because focused behavior needs one stable owner
class ObjectGraph:

    # this definition exists because focused behavior needs one stable owner
    def InitAction(Instance) -> None:
        Instance.Objects: list[Object] = []
        Instance.Names: set[str] = set()

    # this definition exists because focused behavior needs one stable owner
    def Unique(Instance, Requested: Any, Prefix: str = "Object") -> str:
        BaseValue = SafeAction(Requested, Prefix)
        Value = BaseValue
        Suffix = 2
        while Value in Instance.Names:
            Value = f"{BaseValue}_{Suffix}"
            Suffix += 1
        Instance.Names.add(Value)
        return Value

    # this definition exists because focused behavior needs one stable owner
    def AddAction(
        Instance,
        TypeId: str,
        Requested: Any,
        Prefix: str = "Object",
        *,
        Touched: bool = False,
        Extensions: tuple[str, ...] = (),
    ) -> Object:
        Result = Object(
            TypeId,
            Instance.unique(Requested, Prefix),
            touched=Touched,
            extensions=Extensions,
        )
        Instance.Objects.append(Result)
        return Result

    locals()["__init__"] = InitAction
    locals()["add"] = AddAction
    locals()["unique"] = Unique


# this definition exists because parameter aliases need deterministic collision handling
def InitCatalogMut(Instance, Parameters: list[dict[str, Any]]) -> None:
    Instance.Parameters = Parameters
    Instance.ByIdentifier = {
        TextAction(ItemValue.get("id")): ItemValue for ItemValue in Parameters
    }
    Instance.Aliases = {}
    UsedValue: set[str] = set()
    for Index, ItemValue in enumerate(Parameters, start=1):
        ParamId = TextAction(ItemValue.get("id"), f"parameter_{Index}")
        BaseValue = SafeAction(ParamId, "p")
        if BaseValue[0].isdigit():
            BaseValue = f"p_{BaseValue}"
        Alias = BaseValue
        Suffix = 2
        while Alias in UsedValue:
            Alias = f"{BaseValue}_{Suffix}"
            Suffix += 1
        UsedValue.add(Alias)
        Instance.Aliases[ParamId] = Alias


# this definition exists because feature properties reference spreadsheet aliases
def ParamExpression(
    Instance, ParamId: str, Divisor: float | None = None
) -> str | None:
    Alias = Instance.Aliases.get(ParamId)
    if not Alias:
        return None
    Result = f"Parameters.{Alias}"
    if Divisor and Divisor != 1.0:
        Result += f" / {Number(Divisor):.16g}"
    return Result


# this predicate exists because source expressions alter feature carrier behavior
def HasParamSource(Instance, ParamId: str) -> bool:
    Param = Instance.ByIdentifier.get(ParamId, {})
    Expression = Param.get("expression", {}) if isinstance(Param, Mapping) else {}
    return isinstance(Expression, Mapping) and bool(TextAction(Expression.get("source")))


# this definition exists because native expression paths survive neutral translation
def ParamSource(Instance, ParamId: str) -> str:
    Param = Instance.ByIdentifier.get(ParamId, {})
    Attributes = Param.get("attributes", {}) if isinstance(Param, Mapping) else {}
    return (
        TextAction(Attributes.get("freecad_path"))
        if isinstance(Attributes, Mapping)
        else ""
    )


# this definition exists because feature writers need normalized parameter values
def ParamValue(Instance, ParamId: str, Default: float = 0.0) -> float:
    Param = Instance.ByIdentifier.get(ParamId)
    if not Param:
        return Default
    Value = Param.get("value", {})
    if isinstance(Value, Mapping):
        return Number(Value.get("value"), Default)
    return Number(Value, Default)


# this definition exists because feature writers need normalized parameter kinds
def ParamKind(Instance, ParamId: str) -> str:
    Param = Instance.ByIdentifier.get(ParamId, {})
    Value = Param.get("value", {}) if isinstance(Param, Mapping) else {}
    return TextAction(
        EnumAction(Value.get("kind")) if isinstance(Value, Mapping) else "number",
        "number",
    )


# this definition exists because expression validation needs a closed identifier set
def AllowedExpr() -> set[str]:
    return {
        "abs",
        "acos",
        "asin",
        "atan",
        "atan2",
        "ceil",
        "cos",
        "e",
        "exp",
        "false",
        "floor",
        "log",
        "log10",
        "max",
        "min",
        "pi",
        "pow",
        "round",
        "sin",
        "sqrt",
        "tan",
        "true",
    }


# this definition exists because neutral references need spreadsheet alias substitution
def ReplaceRefsMut(
    Instance,
    References: list[str],
    Translated: str,
    AllowedNamesMut: set[str],
) -> str | None:
    for ParamId in References:
        Alias = Instance.Aliases.get(ParamId)
        if not Alias:
            return None
        Param = Instance.ByIdentifier.get(ParamId, {})
        NameValue = TextAction(Param.get("name")) if isinstance(Param, Mapping) else ""
        Replaced = False
        for Token in (ParamId, NameValue):
            if Token and Token in Translated:
                Translated = Translated.replace(Token, Alias)
                Replaced = True
        if not Replaced and Alias not in Translated:
            return None
        AllowedNamesMut.add(Alias)
    return Translated


# this definition exists because safe expressions preserve native parametric behavior
def NativeExpr(Instance, ItemValue: Mapping[str, Any]) -> str | None:
    Expression = ItemValue.get("expression", {})
    if not isinstance(Expression, Mapping):
        return None
    Source = TextAction(Expression.get("source")).strip()
    if not Source or "\n" in Source or "\r" in Source or ";" in Source:
        return None
    Language = TextAction(Expression.get("language"), "kit").casefold()
    if Language == "freecad":
        return Source
    if Language != "kit":
        return None
    References = [
        TextAction(Value) for Value in Sequence(Expression.get("parameter_ids", []))
    ]
    AllowedNames = AllowedExpr()
    Translated = ReplaceRefsMut(Instance, References, Source, AllowedNames)
    if Translated is None:
        return None
    Translated = Translated.replace("^", "**")
    Identifiers = set(RegexLib.findall("[A-Za-z_][A-Za-z0-9_]*", Translated))
    if Identifiers - AllowedNames:
        return None
    if RegexLib.search("[^A-Za-z0-9_.,+\-*/%<>=!&|() \t]", Translated):
        return None
    return Translated


# this definition exists because transfer reporting separates native expressions from carriers
def ExprParts(Instance) -> tuple[int, int]:
    NativeCount = 0
    CarrierCount = 0
    for ItemValue in Instance.Parameters:
        if not isinstance(ItemValue.get("expression"), Mapping):
            continue
        if NativeExpr(Instance, ItemValue) is None:
            CarrierCount += 1
        else:
            NativeCount += 1
    return (NativeCount, CarrierCount)


# this definition exists because spreadsheet cells need normalized value syntax
def ParamContent(Instance, ItemValue: Mapping[str, Any]) -> str:
    ValueData = ItemValue.get("value", {})
    RawValue = ValueData.get("value") if isinstance(ValueData, Mapping) else ValueData
    UnitValue = TextAction(ValueData.get("unit")) if isinstance(ValueData, Mapping) else ""
    if isinstance(RawValue, bool):
        Content = "=true" if RawValue else "=false"
    elif isinstance(RawValue, (int, float)):
        Content = "=" + (
            f"{RawValue:.17g}" if isinstance(RawValue, float) else str(RawValue)
        )
        if UnitValue:
            Content += f" {UnitValue}"
    else:
        Content = "'" + TextAction(RawValue)
    NativeExpression = NativeExpr(Instance, ItemValue)
    return "=" + NativeExpression if NativeExpression is not None else Content


# this definition exists because each parameter owns a label and value cell
def AppendParamMut(
    CellsMut: XmlTree.Element, Instance, RowValue: int, ItemValue: Mapping[str, Any]
) -> None:
    ParamId = TextAction(ItemValue.get("id"), f"parameter_{RowValue}")
    NameValue = TextAction(ItemValue.get("name"), ParamId)
    XmlTree.SubElement(
        CellsMut, "Cell", {"address": f"A{RowValue}", "content": "'" + NameValue}
    )
    XmlTree.SubElement(
        CellsMut,
        "Cell",
        {
            "address": f"B{RowValue}",
            "content": ParamContent(Instance, ItemValue),
            "alias": Instance.Aliases[ParamId],
        },
    )


# this definition exists because parameter spreadsheets need canonical layout properties
def SheetProps(Instance) -> list[XmlTree.Element]:
    Result = [
        StringProp("Label", "Parameters"),
        ExpressionProp([]),
        BoolProp("Visibility", False),
    ]
    Sheet = PropAction("cells", "Spreadsheet::PropertySheet", Status="67108864")
    Cells = XmlTree.SubElement(
        Sheet, "Cells", {"Count": str(len(Instance.Parameters) * 2), "xlink": "1"}
    )
    XmlTree.SubElement(Cells, "XLinks", {"count": "0"})
    for RowValue, ItemValue in enumerate(Instance.Parameters, start=1):
        AppendParamMut(Cells, Instance, RowValue, ItemValue)
    Result.append(Sheet)
    Widths = PropAction(
        "columnWidths", "Spreadsheet::PropertyColumnWidths", Status="218103808"
    )
    XmlTree.SubElement(Widths, "ColumnInfo", {"Count": "0"})
    Result.append(Widths)
    Heights = PropAction(
        "rowHeights", "Spreadsheet::PropertyRowHeights", Status="218103808"
    )
    XmlTree.SubElement(Heights, "RowInfo", {"Count": "0"})
    Result.append(Heights)
    return Result


# this definition exists because focused behavior needs one stable owner
class ParamCatalog:

    # this definition exists because focused behavior needs one stable owner
    def InitAction(Instance, Parameters: list[dict[str, Any]]) -> None:
        InitCatalogMut(Instance, Parameters)

    # this definition exists because focused behavior needs one stable owner
    def Expression(Instance, ParamId: str, Divisor: float | None = None) -> str | None:
        return ParamExpression(Instance, ParamId, Divisor)

    # this definition exists because focused behavior needs one stable owner
    def HasSource(Instance, ParamId: str) -> bool:
        return HasParamSource(Instance, ParamId)

    # this definition exists because focused behavior needs one stable owner
    def SourcePath(Instance, ParamId: str) -> str:
        return ParamSource(Instance, ParamId)

    # this definition exists because focused behavior needs one stable owner
    def Value(Instance, ParamId: str, Default: float = 0.0) -> float:
        return ParamValue(Instance, ParamId, Default)

    # this definition exists because focused behavior needs one stable owner
    def KindAction(Instance, ParamId: str) -> str:
        return ParamKind(Instance, ParamId)

    # this definition exists because focused behavior needs one stable owner
    def Native(Instance, ItemValue: Mapping[str, Any]) -> str | None:
        return NativeExpr(Instance, ItemValue)

    # this definition exists because focused behavior needs one stable owner
    def ExpressionParts(Instance) -> tuple[int, int]:
        return ExprParts(Instance)

    # this definition exists because focused behavior needs one stable owner
    def SheetProperties(Instance) -> list[XmlTree.Element]:
        Result = [
            StringProp("Label", "Parameters"),
            ExpressionProp([]),
            BoolProp("Visibility", False),
        ]
        Sheet = PropAction("cells", "Spreadsheet::PropertySheet", Status="67108864")
        Cells = XmlTree.SubElement(
            Sheet, "Cells", {"Count": str(len(Instance.Parameters) * 2), "xlink": "1"}
        )
        XmlTree.SubElement(Cells, "XLinks", {"count": "0"})
        for RowValue, ItemValue in enumerate(Instance.Parameters, start=1):
            ParamId = TextAction(ItemValue.get("id"), f"parameter_{RowValue}")
            NameValue = TextAction(ItemValue.get("name"), ParamId)
            ValueData = ItemValue.get("value", {})
            RawValue = (
                ValueData.get("value") if isinstance(ValueData, Mapping) else ValueData
            )
            UnitValue = (
                TextAction(ValueData.get("unit"))
                if isinstance(ValueData, Mapping)
                else ""
            )
            KindValue = (
                TextAction(EnumAction(ValueData.get("kind")))
                if isinstance(ValueData, Mapping)
                else "number"
            )
            if isinstance(RawValue, bool):
                Content = "=true" if RawValue else "=false"
            elif isinstance(RawValue, (int, float)):
                Content = "=" + (
                    f"{RawValue:.17g}" if isinstance(RawValue, float) else str(RawValue)
                )
                if UnitValue:
                    Content += f" {UnitValue}"
            else:
                Content = "'" + TextAction(RawValue)
            NativeExpression = Instance.native_expression(ItemValue)
            if NativeExpression is not None:
                Content = "=" + NativeExpression
            XmlTree.SubElement(
                Cells, "Cell", {"address": f"A{RowValue}", "content": "'" + NameValue}
            )
            XmlTree.SubElement(
                Cells,
                "Cell",
                {
                    "address": f"B{RowValue}",
                    "content": Content,
                    "alias": Instance.Aliases[ParamId],
                },
            )
        Result.append(Sheet)
        Widths = PropAction(
            "columnWidths", "Spreadsheet::PropertyColumnWidths", Status="218103808"
        )
        XmlTree.SubElement(Widths, "ColumnInfo", {"Count": "0"})
        Result.append(Widths)
        Heights = PropAction(
            "rowHeights", "Spreadsheet::PropertyRowHeights", Status="218103808"
        )
        XmlTree.SubElement(Heights, "RowInfo", {"Count": "0"})
        Result.append(Heights)
        return Result

    locals()["__init__"] = InitAction
    locals()["expression"] = Expression
    locals()["expression_parts"] = ExpressionParts
    locals()["has_source_expression"] = HasSource
    locals()["kind"] = KindAction
    locals()["native_expression"] = Native
    locals()["sheet_properties"] = SheetProperties
    locals()["source_path"] = SourcePath
    locals()["value"] = Value


# this definition exists because focused behavior needs one stable owner
def NativeParts(Manifest: Mapping[str, Any]) -> tuple[int, int]:
    return ParamCatalog(Items(Manifest.get("parameters", []))).expression_parts()


# this definition exists because focused behavior needs one stable owner
def ElemFromData(Value: Any) -> XmlTree.Element | None:
    if not isinstance(Value, Mapping):
        return None
    TagValue = Value.get("tag")
    Attributes = Value.get("attributes", {})
    if (
        not isinstance(TagValue, str)
        or not TagValue
        or (not isinstance(Attributes, Mapping))
    ):
        return None
    ElemValue = XmlTree.Element(
        TagValue,
        {str(KeyValue): str(ItemValue) for KeyValue, ItemValue in Attributes.items()},
    )
    TextValue = Value.get("text")
    if isinstance(TextValue, str):
        ElemValue.text = TextValue
    Children = Value.get("children", [])
    if not isinstance(Children, (list, tuple)):
        return None
    for ChildData in Children:
        Child = ElemFromData(ChildData)
        if Child is None:
            return None
        ElemValue.append(Child)
    return ElemValue


# this definition exists because focused behavior needs one stable owner
def NativeA(Value: Mapping[str, Any]) -> list[XmlTree.Element]:
    Properties = Value.get("properties", {})
    if not isinstance(Properties, Mapping):
        return []
    Order = [
        TextAction(NameValue)
        for NameValue in Sequence(Value.get("property_order", []))
        if TextAction(NameValue) in Properties
    ]
    Order.extend(
        (str(NameValue) for NameValue in Properties if str(NameValue) not in Order)
    )
    return [
        ElemValue
        for NameValue in Order
        if (ElemValue := ElemFromData(Properties.get(NameValue))) is not None
        and ElemValue.tag == "Property"
    ]


# this definition exists because focused behavior needs one stable owner
def Native(Value: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        (
            ExtensionType
            for ItemValue in Sequence(Value.get("extensions", []))
            if (ElemValue := ElemFromData(ItemValue)) is not None
            and ElemValue.tag == "Extension"
            and (ExtensionType := TextAction(ElemValue.get("type")))
        )
    )


# this definition exists because focused behavior needs one stable owner
def FindLinkProp(Value: Mapping[str, Any]) -> str:
    Properties = Value.get("properties", {})
    if not isinstance(Properties, Mapping):
        return ""
    if "LinkedObject" in Properties:
        return "LinkedObject"
    Elements = {
        TextAction(NameValue): ElemValue
        for NameValue, ItemValue in Properties.items()
        if (ElemValue := ElemFromData(ItemValue)) is not None
        and ElemValue.tag == "Property"
    }
    Proxy = Elements.get("Proxy")
    ProxyValue = Proxy.find("./Python") if Proxy is not None else None
    Marker = " ".join(
        (
            TextAction(Value.get("type_id")),
            "" if ProxyValue is None else ProxyValue.get("class", ""),
            *Native(Value),
        )
    ).casefold()
    if "link" not in Marker:
        return ""
    Candidates = [
        NameValue
        for NameValue, ElemValue in Elements.items()
        if ElemValue.find("./XLink") is not None and NameValue not in JointReservedLink
    ]
    Named = next(
        (NameValue for NameValue in Candidates if "link" in NameValue.casefold()), ""
    )
    return Named or (Candidates[0] if len(Candidates) == 1 else "")


# this definition exists because focused behavior needs one stable owner
def NativeObject(Value: Mapping[str, Any]) -> Object:
    NameValue = TextAction(Value.get("name"))
    TypeId = TextAction(Value.get("type_id"))
    if not NameValue or not TypeId:
        raise ValueError("native FreeCAD object metadata requires name and type_id")
    ValidatedObject(NameValue)
    TransientProperties = [
        ElemValue
        for ItemValue in Sequence(Value.get("transient_properties", []))
        if (ElemValue := ElemFromData(ItemValue)) is not None
        and ElemValue.tag == "_Property"
    ]
    Extensions = Native(Value)
    return Object(
        TypeId,
        NameValue,
        object_id=TextAction(Value.get("object_id")),
        properties=NativeA(Value),
        transient_properties=TransientProperties,
        dependencies=[
            TextAction(ItemValue)
            for ItemValue in Sequence(Value.get("dependencies", []))
            if TextAction(ItemValue)
        ],
        touched=bool(Value.get("touched")),
        extensions=Extensions,
    )


# this definition exists because focused behavior needs one stable owner
def MergeNamedMut(Properties: list[ET.Element], Replacement: ET.Element) -> None:
    NameValue = Replacement.get("name")
    for Current in Properties:
        if Current.get("name") == NameValue:
            Current[:] = [CopyValue.deepcopy(Child) for Child in Replacement]
            return
    Properties.append(Replacement)


# this definition exists because focused behavior needs one stable owner
def NativeGeomElem(Entity: Mapping[str, Any]) -> XmlTree.Element | None:
    KindValue = TextAction(EnumAction(Entity.get("kind"))).lower()
    Attributes = Entity.get("attributes", {})
    GeomValue = Entity.get("geometry", {})
    if not isinstance(GeomValue, Mapping):
        GeomValue = {}
    ElemValue = (
        ElemFromData(Attributes.get("freecad"))
        if isinstance(Attributes, Mapping)
        else None
    )
    NativeGeom = TextAction(GeomValue.get("$type")) == "NativeGeometry" or all(
        (KeyValue in GeomValue for KeyValue in ("format_id", "entity_type", "data"))
    )
    if ElemValue is None and NativeGeom:
        FormatId = TextAction(GeomValue.get("format_id")).casefold()
        EntityType = TextAction(GeomValue.get("entity_type"))
        Choice = ElemFromData(GeomValue.get("data"))
        if (
            FormatId == FormatId
            and Choice is not None
            and (Choice.tag == "Geometry")
            and (Choice.get("type", "") == EntityType)
        ):
            ElemValue = Choice
    if ElemValue is None or ElemValue.tag != "Geometry":
        return None
    ExpectedTypeIds = GeomTypeIdsByKind.get(KindValue)
    if ExpectedTypeIds is not None and ElemValue.get("type", "") not in ExpectedTypeIds:
        return None
    if KindValue != "native" and ExpectedTypeIds is None:
        return None
    if not NativeGeom and KindValue == "line":
        Value = ElemValue.find("./LineSegment")
        if Value is not None:
            Start = PointTwo(GeomValue.get("start"))
            EndValue = PointTwo(GeomValue.get("end"))
            Value.set("StartX", FmtAction(Start[0]))
            Value.set("StartY", FmtAction(Start[1]))
            Value.set("EndX", FmtAction(EndValue[0]))
            Value.set("EndY", FmtAction(EndValue[1]))
    elif not NativeGeom and KindValue in CircularGeomKinds:
        Value = ElemValue.find("./Circle" if KindValue == "circle" else "./ArcOfCircle")
        if Value is not None:
            Center = PointTwo(GeomValue.get("center"))
            Value.set("CenterX", FmtAction(Center[0]))
            Value.set("CenterY", FmtAction(Center[1]))
            Value.set("Radius", FmtAction(GeomValue.get("radius")))
            if KindValue == "arc":
                Value.set("StartAngle", FmtAction(GeomValue.get("start_angle")))
                Value.set("EndAngle", FmtAction(GeomValue.get("end_angle")))
    elif not NativeGeom and KindValue == "point":
        Value = ElemValue.find("./GeomPoint")
        if Value is None:
            Value = ElemValue.find("./Point")
        if Value is not None:
            Point = PointTwo(GeomValue.get("point"))
            Value.set("X", FmtAction(Point[0]))
            Value.set("Y", FmtAction(Point[1]))
    elif not NativeGeom and KindValue == "ellipse":
        Value = ElemValue.find("./Ellipse")
        if Value is not None:
            Center = PointTwo(GeomValue.get("center"))
            MajorAxis = PointTwo(GeomValue.get("major_axis"))
            Value.set("CenterX", FmtAction(Center[0]))
            Value.set("CenterY", FmtAction(Center[1]))
            if Value.get("AngleXU") is not None:
                Value.set(
                    "AngleXU", FmtAction(MathValue.atan2(MajorAxis[1], MajorAxis[0]))
                )
            else:
                Value.set("MajorAxisX", FmtAction(MajorAxis[0]))
                Value.set("MajorAxisY", FmtAction(MajorAxis[1]))
            Value.set("MajorRadius", FmtAction(GeomValue.get("major_radius")))
            Value.set("MinorRadius", FmtAction(GeomValue.get("minor_radius")))
    elif not NativeGeom and KindValue in {"arc_ellipse", "hyperbola", "arc_hyperbola"}:
        TagValue = {
            "arc_ellipse": "ArcOfEllipse",
            "hyperbola": "Hyperbola",
            "arc_hyperbola": "ArcOfHyperbola",
        }[KindValue]
        Value = ElemValue.find(f"./{TagValue}")
        if Value is not None:
            Center = PointTwo(GeomValue.get("center"))
            MajorAxis = PointTwo(GeomValue.get("major_axis"))
            Value.set("CenterX", FmtAction(Center[0]))
            Value.set("CenterY", FmtAction(Center[1]))
            Value.set("AngleXU", FmtAction(MathValue.atan2(MajorAxis[1], MajorAxis[0])))
            Value.set("MajorRadius", FmtAction(GeomValue.get("major_radius")))
            Value.set("MinorRadius", FmtAction(GeomValue.get("minor_radius")))
            if KindValue != "hyperbola":
                Value.set("StartAngle", FmtAction(GeomValue.get("start_angle")))
                Value.set("EndAngle", FmtAction(GeomValue.get("end_angle")))
    elif not NativeGeom and KindValue in {"parabola", "arc_parabola"}:
        TagValue = "Parabola" if KindValue == "parabola" else "ArcOfParabola"
        Value = ElemValue.find(f"./{TagValue}")
        if Value is not None:
            Center = PointTwo(GeomValue.get("center"))
            AxisValue = PointTwo(GeomValue.get("axis"))
            Value.set("CenterX", FmtAction(Center[0]))
            Value.set("CenterY", FmtAction(Center[1]))
            Value.set("AngleXU", FmtAction(MathValue.atan2(AxisValue[1], AxisValue[0])))
            Value.set("Focal", FmtAction(GeomValue.get("focal_length")))
            if KindValue == "arc_parabola":
                Value.set("StartAngle", FmtAction(GeomValue.get("start_angle")))
                Value.set("EndAngle", FmtAction(GeomValue.get("end_angle")))
    elif not NativeGeom and KindValue in SplineGeomKinds:
        Value = ElemValue.find(
            "./BezierCurve" if KindValue == "bezier" else "./BSplineCurve"
        )
        if Value is not None:
            Points = Items(GeomValue.get("control_points", []))
            Weights = [
                Number(ItemValue, 1.0)
                for ItemValue in Sequence(GeomValue.get("weights", []))
            ]
            if len(Weights) != len(Points):
                Weights = [1.0] * len(Points)
            Value[:] = [Child for Child in Value if Child.tag not in SplineControlTags]
            Value.set("PolesCount", str(len(Points)))
            for Point, Weight in zip(Points, Weights, strict=True):
                FirstCoord, SecondCoord = PointTwo(Point)
                XmlTree.SubElement(
                    Value,
                    "Pole",
                    {
                        "X": FmtAction(FirstCoord),
                        "Y": FmtAction(SecondCoord),
                        "Z": FmtAction(0),
                        "Weight": FmtAction(Weight),
                    },
                )
            if KindValue == "spline":
                Degree = max(
                    1,
                    min(
                        int(Number(GeomValue.get("degree"), 3)), max(1, len(Points) - 1)
                    ),
                )
                Knots = [
                    Number(ItemValue)
                    for ItemValue in Sequence(GeomValue.get("knots", []))
                ]
                Multiplicities = [
                    int(Number(ItemValue, 1))
                    for ItemValue in Sequence(GeomValue.get("multiplicities", []))
                ]
                if not Knots or len(Multiplicities) != len(Knots):
                    InteriorCount = max(0, len(Points) - Degree - 1)
                    Knots = [float(ItemValue) for ItemValue in range(InteriorCount + 2)]
                    Multiplicities = [Degree + 1] + [1] * InteriorCount + [Degree + 1]
                Value.set("KnotsCount", str(len(Knots)))
                Value.set("Degree", str(Degree))
                Value.set("IsPeriodic", "1" if bool(GeomValue.get("periodic")) else "0")
                for KnotValue, Multiplicity in zip(Knots, Multiplicities, strict=True):
                    XmlTree.SubElement(
                        Value,
                        "Knot",
                        {"Value": FmtAction(KnotValue), "Mult": str(Multiplicity)},
                    )
    Construction = ElemValue.find("./Construction")
    if Construction is not None:
        Construction.set("value", "1" if bool(Entity.get("construction")) else "0")
    return ElemValue


# this definition exists because focused behavior needs one stable owner
def GeomProp(
    Sketch: Mapping[str, Any],
) -> tuple[XmlTree.Element, dict[str, int], list[dict[str, AnyValue]]]:
    Entities = Items(Sketch.get("entities", []))
    ClosedEntityIds = {
        TextAction(EntityId)
        for Profile in Sequence(Sketch.get("closed_profile_entity_ids", []))
        for EntityId in Sequence(Profile)
        if TextAction(EntityId)
    }
    Result = PropAction("Geometry", "Part::PropertyGeometryList", Status="8192")
    GeomList = XmlTree.SubElement(Result, "GeometryList", {"count": "0"})
    Indices: dict[str, int] = {}
    Diagnostics: list[dict[str, AnyValue]] = []
    for SourceIndex, Entity in enumerate(Entities):
        EntityId = TextAction(Entity.get("id"), str(SourceIndex))
        KindValue = TextAction(EnumAction(Entity.get("kind"))).lower()
        NativeItem = NativeGeomElem(Entity)
        if NativeItem is not None:
            Indices[EntityId] = len(GeomList)
            GeomList.append(NativeItem)
            continue
        GeomValue = Entity.get("geometry", {})
        if not isinstance(GeomValue, Mapping):
            GeomValue = {}
        GeomType = TextAction(GeomValue.get("$type"))
        ExpectedGeomType = NeutralGeomTypeByKind.get(KindValue)
        TypeId = NeutralGeomTypeIdByKind.get(KindValue)
        if TypeId is None or (
            GeomType == "NativeGeometry" or (GeomType and GeomType != ExpectedGeomType)
        ):
            CarrierReason = (
                "source_opaque"
                if GeomType == "NativeGeometry"
                or (TypeId is not None and GeomType and (GeomType != ExpectedGeomType))
                else "writer_unimplemented"
            )
            Diagnostics.append(
                {
                    "carrier_reason": CarrierReason,
                    "code": "freecad.sketch_geometry_carrier_only",
                    "entity_id": EntityId,
                    "kind": KindValue,
                    "mode": "carrier_only",
                    "reason": "native FreeCAD geometry data is unavailable",
                    "severity": "warning",
                }
            )
            continue
        Index = len(GeomList)
        Indices[EntityId] = Index
        ItemValue = XmlTree.SubElement(
            GeomList,
            "Geometry",
            {"type": TypeId, "id": str(Index + 1), "migrated": "1"},
        )
        Extensions = XmlTree.SubElement(ItemValue, "GeoExtensions", {"count": "1"})
        Construction = bool(Entity.get("construction")) or (
            bool(ClosedEntityIds) and EntityId not in ClosedEntityIds
        )
        Flags = (
            "00000000000000000000000000000010"
            if Construction
            else "00000000000000000000000000000000"
        )
        XmlTree.SubElement(
            Extensions,
            "GeoExtension",
            {
                "type": "Sketcher::SketchGeometryExtension",
                "id": str(Index + 1),
                "internalGeometryType": "0",
                "geometryModeFlags": Flags,
                "geometryLayer": "0",
            },
        )
        if KindValue == "line":
            Start = PointTwo(GeomValue.get("start"))
            EndValue = PointTwo(GeomValue.get("end"))
            XmlTree.SubElement(
                ItemValue,
                "LineSegment",
                {
                    "StartX": FmtAction(Start[0]),
                    "StartY": FmtAction(Start[1]),
                    "StartZ": FmtAction(0),
                    "EndX": FmtAction(EndValue[0]),
                    "EndY": FmtAction(EndValue[1]),
                    "EndZ": FmtAction(0),
                },
            )
        elif KindValue in CircularGeomKinds:
            Center = PointTwo(GeomValue.get("center"))
            Attributes = {
                "CenterX": FmtAction(Center[0]),
                "CenterY": FmtAction(Center[1]),
                "CenterZ": FmtAction(0),
                "NormalX": FmtAction(0),
                "NormalY": FmtAction(0),
                "NormalZ": FmtAction(1),
                "AngleXU": FmtAction(0),
                "Radius": FmtAction(GeomValue.get("radius")),
            }
            if KindValue == "arc":
                Attributes["StartAngle"] = FmtAction(GeomValue.get("start_angle"))
                Attributes["EndAngle"] = FmtAction(GeomValue.get("end_angle"))
                XmlTree.SubElement(ItemValue, "ArcOfCircle", Attributes)
            else:
                XmlTree.SubElement(ItemValue, "Circle", Attributes)
        elif KindValue == "ellipse":
            Center = PointTwo(GeomValue.get("center"))
            MajorAxis = PointTwo(GeomValue.get("major_axis"))
            XmlTree.SubElement(
                ItemValue,
                "Ellipse",
                {
                    "CenterX": FmtAction(Center[0]),
                    "CenterY": FmtAction(Center[1]),
                    "CenterZ": FmtAction(0),
                    "NormalX": FmtAction(0),
                    "NormalY": FmtAction(0),
                    "NormalZ": FmtAction(1),
                    "MajorRadius": FmtAction(GeomValue.get("major_radius")),
                    "MinorRadius": FmtAction(GeomValue.get("minor_radius")),
                    "AngleXU": FmtAction(MathValue.atan2(MajorAxis[1], MajorAxis[0])),
                },
            )
        elif KindValue in {"arc_ellipse", "hyperbola", "arc_hyperbola"}:
            Center = PointTwo(GeomValue.get("center"))
            MajorAxis = PointTwo(GeomValue.get("major_axis"))
            TagValue = {
                "arc_ellipse": "ArcOfEllipse",
                "hyperbola": "Hyperbola",
                "arc_hyperbola": "ArcOfHyperbola",
            }[KindValue]
            Attributes = {
                "CenterX": FmtAction(Center[0]),
                "CenterY": FmtAction(Center[1]),
                "CenterZ": FmtAction(0),
                "NormalX": FmtAction(0),
                "NormalY": FmtAction(0),
                "NormalZ": FmtAction(1),
                "MajorRadius": FmtAction(GeomValue.get("major_radius")),
                "MinorRadius": FmtAction(GeomValue.get("minor_radius")),
                "AngleXU": FmtAction(MathValue.atan2(MajorAxis[1], MajorAxis[0])),
            }
            if KindValue != "hyperbola":
                Attributes["StartAngle"] = FmtAction(GeomValue.get("start_angle"))
                Attributes["EndAngle"] = FmtAction(GeomValue.get("end_angle"))
            XmlTree.SubElement(ItemValue, TagValue, Attributes)
        elif KindValue in {"parabola", "arc_parabola"}:
            Center = PointTwo(GeomValue.get("center"))
            AxisValue = PointTwo(GeomValue.get("axis"))
            TagValue = "Parabola" if KindValue == "parabola" else "ArcOfParabola"
            Attributes = {
                "CenterX": FmtAction(Center[0]),
                "CenterY": FmtAction(Center[1]),
                "CenterZ": FmtAction(0),
                "NormalX": FmtAction(0),
                "NormalY": FmtAction(0),
                "NormalZ": FmtAction(1),
                "Focal": FmtAction(GeomValue.get("focal_length")),
                "AngleXU": FmtAction(MathValue.atan2(AxisValue[1], AxisValue[0])),
            }
            if KindValue == "arc_parabola":
                Attributes["StartAngle"] = FmtAction(GeomValue.get("start_angle"))
                Attributes["EndAngle"] = FmtAction(GeomValue.get("end_angle"))
            XmlTree.SubElement(ItemValue, TagValue, Attributes)
        elif KindValue in SplineGeomKinds:
            Points = Items(GeomValue.get("control_points", []))
            Weights = [
                Number(Value, 1.0) for Value in Sequence(GeomValue.get("weights", []))
            ]
            if len(Weights) != len(Points):
                Weights = [1.0] * len(Points)
            if KindValue == "bezier":
                Curve = XmlTree.SubElement(
                    ItemValue, "BezierCurve", {"PolesCount": str(len(Points))}
                )
            else:
                Degree = max(
                    1,
                    min(
                        int(Number(GeomValue.get("degree"), 3)), max(1, len(Points) - 1)
                    ),
                )
                Knots = [
                    Number(Value) for Value in Sequence(GeomValue.get("knots", []))
                ]
                Multiplicities = [
                    int(Number(Value, 1))
                    for Value in Sequence(GeomValue.get("multiplicities", []))
                ]
                if not Knots or len(Multiplicities) != len(Knots):
                    InteriorCount = max(0, len(Points) - Degree - 1)
                    Knots = [float(Value) for Value in range(InteriorCount + 2)]
                    Multiplicities = [Degree + 1] + [1] * InteriorCount + [Degree + 1]
                Curve = XmlTree.SubElement(
                    ItemValue,
                    "BSplineCurve",
                    {
                        "PolesCount": str(len(Points)),
                        "KnotsCount": str(len(Knots)),
                        "Degree": str(Degree),
                        "IsPeriodic": "1" if bool(GeomValue.get("periodic")) else "0",
                    },
                )
            for Point, Weight in zip(Points, Weights, strict=True):
                FirstCoord, SecondCoord = PointTwo(Point)
                XmlTree.SubElement(
                    Curve,
                    "Pole",
                    {
                        "X": FmtAction(FirstCoord),
                        "Y": FmtAction(SecondCoord),
                        "Z": FmtAction(0),
                        "Weight": FmtAction(Weight),
                    },
                )
            if KindValue == "spline":
                for KnotValue, Multiplicity in zip(Knots, Multiplicities, strict=True):
                    XmlTree.SubElement(
                        Curve,
                        "Knot",
                        {"Value": FmtAction(KnotValue), "Mult": str(Multiplicity)},
                    )
        elif KindValue == "point":
            Point = PointTwo(GeomValue.get("point", GeomValue.get("center")))
            XmlTree.SubElement(
                ItemValue,
                "GeomPoint",
                {"X": FmtAction(Point[0]), "Y": FmtAction(Point[1]), "Z": FmtAction(0)},
            )
        XmlTree.SubElement(
            ItemValue, "Construction", {"value": "1" if Construction else "0"}
        )
    GeomList.set("count", str(len(GeomList)))
    return (Result, Indices, Diagnostics)


# this definition exists because focused behavior needs one stable owner
def RefPoint(Value: Any) -> int:
    Point = TextAction(Value).lower()
    return RulePointIndexByName.get(Point, 0)


# this definition exists because focused behavior needs one stable owner
def NeutralRefPoint(RuleKind: str, Entity: Mapping[str, Any], Value: Any) -> int:
    Point = RefPoint(Value)
    if Point:
        return Point
    EntityKind = TextAction(EnumAction(Entity.get("kind"))).casefold()
    if EntityKind == "point":
        return 1
    if EntityKind in CircularGeomKinds and RuleKind in {
        "coincident",
        "concentric",
        "distance",
        "distance_x",
        "distance_y",
    }:
        return 3
    return 0


# this definition exists because focused behavior needs one stable owner
def RawRuleSlots(Attributes: Mapping[str, Any]) -> list[tuple[int, int]]:
    ElemIds = TextAction(Attributes.get("ElementIds"))
    ElemPositions = TextAction(Attributes.get("ElementPositions"))
    Slots: list[tuple[int, int]] = []
    if ElemIds and ElemPositions:
        IdsValue = ElemIds.split()
        Positions = ElemPositions.split()
        if len(IdsValue) == len(Positions):
            Slots = [
                (int(Number(EntityId, -2000)), int(Number(Position)))
                for EntityId, Position in zip(IdsValue, Positions, strict=True)
            ]
    for Index, Prefix in enumerate(("First", "Second", "Third")):
        if Prefix not in Attributes:
            continue
        while len(Slots) <= Index:
            Slots.append((-2000, 0))
        Slots[Index] = (
            int(Number(Attributes.get(Prefix), -2000)),
            int(Number(Attributes.get(Prefix + "Pos"))),
        )
    return Slots


# this definition exists because focused behavior needs one stable owner
def MidpointSlots(
    RuleValue: Mapping[str, Any],
    Indices: Mapping[str, int],
    Entities: Mapping[str, Mapping[str, Any]],
) -> list[tuple[int, int]] | None:
    References = Items(RuleValue.get("references", []))
    if len(References) == 2:
        for LineRef, PointRef in (
            (References[0], References[1]),
            (References[1], References[0]),
        ):
            LineId = TextAction(LineRef.get("entity_id"))
            PointId = TextAction(PointRef.get("entity_id"))
            LineValue = Entities.get(LineId, {})
            Point = Entities.get(PointId, {})
            LineRefPoint = TextAction(LineRef.get("point")).casefold()
            if (
                TextAction(EnumAction(LineValue.get("kind"))).casefold() != "line"
                or LineRefPoint not in MidpointRefPointNames
                or LineId == PointId
                or (LineId not in Indices)
                or (PointId not in Indices)
            ):
                continue
            PointPosition = RefPoint(PointRef.get("point"))
            if (
                PointPosition == 0
                and TextAction(EnumAction(Point.get("kind"))).casefold() == "point"
            ):
                PointPosition = 1
            if PointPosition:
                return [
                    (Indices[LineId], 1),
                    (Indices[LineId], 2),
                    (Indices[PointId], PointPosition),
                ]
    if len(References) == 3:
        Resolved = [
            (TextAction(RefValue.get("entity_id")), RefPoint(RefValue.get("point")))
            for RefValue in References
        ]
        for LineId, LineValue in Entities.items():
            if (
                TextAction(EnumAction(LineValue.get("kind"))).casefold() != "line"
                or LineId not in Indices
            ):
                continue
            LinePoints = [Point for EntityId, Point in Resolved if EntityId == LineId]
            Others = [
                (EntityId, Point) for EntityId, Point in Resolved if EntityId != LineId
            ]
            if sorted(LinePoints) != [1, 2] or len(Others) != 1:
                continue
            PointId, PointPosition = Others[0]
            Point = Entities.get(PointId, {})
            if (
                PointPosition == 0
                and TextAction(EnumAction(Point.get("kind"))).casefold() == "point"
            ):
                PointPosition = 1
            if PointId in Indices and PointPosition:
                return [
                    (Indices[LineId], 1),
                    (Indices[LineId], 2),
                    (Indices[PointId], PointPosition),
                ]
    return None


# this definition exists because focused behavior needs one stable owner
def RuleDiag(
    RuleValue: Mapping[str, Any],
    KindValue: str,
    CodeValue: str,
    ModeValue: str,
    Reason: str,
    Severity: str,
    NativeKind: str = "",
    CarrierReason: str = "",
) -> dict[str, AnyValue]:
    Result = {
        "code": CodeValue,
        "constraint_id": TextAction(RuleValue.get("id")),
        "kind": KindValue,
        "mode": ModeValue,
        "reason": Reason,
        "severity": Severity,
    }
    if NativeKind:
        Result["native_kind"] = NativeKind
    if CarrierReason:
        Result["carrier_reason"] = CarrierReason
    return Result


# this definition exists because focused behavior needs one stable owner
def RuleCarrier(RuleValue: Mapping[str, Any], NativeRule: bool) -> str:
    KindValue = TextAction(EnumAction(RuleValue.get("kind"))).casefold()
    Attributes = RuleValue.get("attributes", {})
    HasNativeAttributes = isinstance(Attributes, Mapping) and any(
        (
            TextAction(KeyValue).casefold().startswith("native_")
            for KeyValue in Attributes
        )
    )
    return (
        "source_opaque"
        if NativeRule or KindValue.startswith("native") or HasNativeAttributes
        else "writer_unimplemented"
    )


# this definition exists because focused behavior needs one stable owner
def ConstraintsProp(
    Sketch: Mapping[str, Any],
    Indices: Mapping[str, int],
    Parameters: _Parameters,
    ProfileOnly: bool = False,
) -> tuple[
    XmlTree.Element, list[tuple[str, str]], list[str], list[dict[str, AnyValue]]
]:
    SourceConstraints = Items(Sketch.get("constraints", []))
    EntityItems = Items(Sketch.get("entities", []))
    Entities = {TextAction(Entity.get("id")): Entity for Entity in EntityItems}
    Encoded: list[dict[str, AnyValue]] = []
    Expressions: list[tuple[str, str]] = []
    Dependencies: list[str] = []
    Diagnostics: list[dict[str, AnyValue]] = []
    RuleNames: set[str] = set()
    FixedEntities: set[str] = set()
    ProfileEntityIds = {
        TextAction(EntityId)
        for Profile in Sequence(Sketch.get("closed_profile_entity_ids", []))
        for EntityId in Sequence(Profile)
        if TextAction(EntityId)
    }
    for RuleValue in SourceConstraints:
        KindValue = TextAction(EnumAction(RuleValue.get("kind"))).lower()
        References = Items(RuleValue.get("references", []))
        if ProfileOnly:
            RefEntities = [
                Entities.get(TextAction(RefValue.get("entity_id")), {})
                for RefValue in References
            ]
            RefKinds = [
                TextAction(EnumAction(Entity.get("kind"))).casefold()
                for Entity in RefEntities
            ]
            RefPoints = [
                TextAction(RefValue.get("point")).casefold() for RefValue in References
            ]
            ProfileReferences = bool(References) and all(
                (
                    TextAction(RefValue.get("entity_id")) in ProfileEntityIds
                    for RefValue in References
                )
            )
            StaticallySound = ProfileReferences and (
                KindValue in {"horizontal", "vertical"}
                and len(References) == 1
                and (RefKinds == ["line"])
                and (RefPoints == [""])
                or (
                    KindValue == "coincident"
                    and len(References) == 2
                    and all(RefPoints)
                )
                or (
                    KindValue in {"radius", "diameter"}
                    and len(References) == 1
                    and (RefKinds == ["circle"])
                    and (RefPoints == [""])
                )
            )
            if not StaticallySound:
                Diagnostics.append(
                    RuleDiag(
                        RuleValue,
                        KindValue,
                        "freecad.sketch_constraint_carrier_only",
                        "carrier_only",
                        "the source relationship is preserved without activating an unproven solver encoding",
                        "warning",
                        CarrierReason="source_opaque",
                    )
                )
                continue
        SourceAttributes = RuleValue.get("attributes", {})
        if not isinstance(SourceAttributes, Mapping):
            SourceAttributes = {}
        RawAttributes = SourceAttributes.get("freecad", {})
        if not isinstance(RawAttributes, Mapping):
            RawAttributes = {}
        SourceCode = SourceAttributes.get(
            "freecad_type_code", RawAttributes.get("Type")
        )
        NativeRule = SourceCode is not None or bool(RawAttributes)
        Composition: tuple[str, str] | None = None
        if KindValue == "midpoint" and SourceCode is None:
            CodeValue = 14
            Resolved = MidpointSlots(RuleValue, Indices, Entities)
            if Resolved is not None:
                Composition = (
                    "Symmetric",
                    "encoded as symmetry between a line's endpoints and the referenced point",
                )
            else:
                Diagnostics.append(
                    RuleDiag(
                        RuleValue,
                        KindValue,
                        "freecad.sketch_constraint_carrier_only",
                        "carrier_only",
                        "the midpoint relationship cannot be expressed as a sound FreeCAD symmetry constraint",
                        "warning",
                        CarrierReason=RuleCarrier(RuleValue, NativeRule),
                    )
                )
                continue
        else:
            CodeValue = (
                int(Number(SourceCode, -1))
                if SourceCode is not None
                else RuleCodeByKind.get(KindValue)
            )
            Resolved = None
        if CodeValue is None or CodeValue < 0:
            Diagnostics.append(
                RuleDiag(
                    RuleValue,
                    KindValue,
                    "freecad.sketch_constraint_carrier_only",
                    "carrier_only",
                    "no equivalent FreeCAD constraint type is available",
                    "warning",
                    CarrierReason=RuleCarrier(RuleValue, NativeRule),
                )
            )
            continue
        if Resolved is None:
            SourceSlots = Items(SourceAttributes.get("freecad_reference_slots", []))
            SlotValues: list[tuple[int, int, str]] = []
            if SourceSlots:
                SlotValues = [
                    (
                        int(Number(SlotValue.get("freecad_geometry_index"), -2000)),
                        int(Number(SlotValue.get("freecad_point_index"))),
                        TextAction(SlotValue.get("entity_id")),
                    )
                    for SlotValue in SourceSlots
                ]
            elif RawAttributes:
                SlotValues = [
                    (EntityIndex, PointIndex, "")
                    for EntityIndex, PointIndex in RawRuleSlots(RawAttributes)
                ]
            Unresolved = False
            if SlotValues:
                Resolved = []
                for EntityIndex, PointIndex, EntityId in SlotValues:
                    if EntityIndex < 0:
                        Resolved.append((EntityIndex, PointIndex))
                        continue
                    TargetId = EntityId
                    if not TargetId and EntityIndex < len(EntityItems):
                        TargetId = TextAction(EntityItems[EntityIndex].get("id"))
                    TargetIndex = Indices.get(TargetId)
                    if TargetIndex is None:
                        Unresolved = True
                        break
                    Resolved.append((TargetIndex, PointIndex))
                if Unresolved:
                    Resolved = []
            else:
                Resolved = []
                for RefValue in References:
                    EntityId = TextAction(RefValue.get("entity_id"))
                    EntityIndex = Indices.get(EntityId)
                    if EntityIndex is None:
                        Unresolved = True
                        break
                    Resolved.append(
                        (
                            EntityIndex,
                            NeutralRefPoint(
                                KindValue,
                                Entities.get(EntityId, {}),
                                RefValue.get("point"),
                            ),
                        )
                    )
                if Unresolved:
                    Resolved = []
            if KindValue == "concentric" and (not NativeRule):
                if len(Resolved) == 2:
                    Resolved = [(Resolved[0][0], 3), (Resolved[1][0], 3)]
                    Composition = (
                        "Coincident",
                        "encoded as coincidence between the referenced curve centers",
                    )
                else:
                    Resolved = []
            elif KindValue == "fixed" and (not NativeRule):
                if len(Resolved) == 1 and Resolved[0][1] == 0:
                    Composition = ("Block", "encoded using FreeCAD's block constraint")
                else:
                    Resolved = []
        if not Resolved:
            Diagnostics.append(
                RuleDiag(
                    RuleValue,
                    KindValue,
                    "freecad.sketch_constraint_carrier_only",
                    "carrier_only",
                    "the constraint has no sound native reference encoding",
                    "warning",
                    CarrierReason=RuleCarrier(RuleValue, NativeRule),
                )
            )
            continue
        ParamId = TextAction(RuleValue.get("parameter_id"))
        Value = Parameters.value(
            ParamId,
            Number(
                RuleValue.get("value"),
                Number(
                    SourceAttributes.get("native_value"),
                    Number(RawAttributes.get("Value")),
                ),
            ),
        )
        Elements = Resolved + [(-2000, 0)] * max(0, 3 - len(Resolved))
        Values = Elements[:3]
        if NativeRule and "Name" in RawAttributes:
            NameValue = TextAction(RawAttributes.get("Name"))
        else:
            NameBase = SafeAction(RuleValue.get("id"), "Constraint")
            NameValue = NameBase
            Suffix = 2
            while NameValue in RuleNames:
                NameValue = f"{NameBase}_{Suffix}"
                Suffix += 1
            RuleNames.add(NameValue)
        if NameValue:
            RuleNames.add(NameValue)
        Encoded.append(
            {
                "name": NameValue,
                "type": CodeValue,
                "value": Value,
                "driving": bool(RuleValue.get("driving", True)),
                "active": not bool(RuleValue.get("suppressed")),
                "first": Values[0],
                "second": Values[1],
                "third": Values[2],
                "elements": Elements,
                "attributes": RawAttributes,
            }
        )
        if KindValue in FixedRuleKinds:
            FixedEntities.update(
                (
                    TextAction(RefValue.get("entity_id"))
                    for RefValue in Items(RuleValue.get("references", []))
                )
            )
        if Composition is not None:
            Diagnostics.append(
                RuleDiag(
                    RuleValue,
                    KindValue,
                    "freecad.sketch_constraint_composed",
                    "native_composition",
                    Composition[1],
                    "info",
                    Composition[0],
                )
            )
        Expression = (
            Parameters.expression(ParamId)
            if not NativeRule or Parameters.has_source_expression(ParamId)
            else None
        )
        if (
            Expression
            and bool(RuleValue.get("driving", True))
            and (CodeValue in DimensionalRuleCodes)
        ):
            SourcePath = Parameters.source_path(ParamId)
            PathValue = (
                f".{SourcePath}"
                if NativeRule and SourcePath
                else f".Constraints.{NameValue}"
            )
            Expressions.append((PathValue, Expression))
            Dependencies.append("Parameters")
    for Entity in EntityItems:
        EntityId = TextAction(Entity.get("id"))
        if (
            not ProfileOnly
            and bool(Entity.get("fixed"))
            and (EntityId not in FixedEntities)
            and (EntityId in Indices)
        ):
            Encoded.append(
                {
                    "name": f"fixed_{EntityId}",
                    "type": 17,
                    "value": 0.0,
                    "driving": True,
                    "active": True,
                    "first": (Indices[EntityId], 0),
                    "second": (-2000, 0),
                    "third": (-2000, 0),
                    "elements": [(Indices[EntityId], 0), (-2000, 0), (-2000, 0)],
                    "attributes": {},
                }
            )
    Result = PropAction("Constraints", "Sketcher::PropertyConstraintList")
    RuleList = XmlTree.SubElement(
        Result, "ConstraintList", {"count": str(len(Encoded))}
    )
    for ItemValue in Encoded:
        First, Second, Third = (
            ItemValue["first"],
            ItemValue["second"],
            ItemValue["third"],
        )
        Elements = ItemValue["elements"]
        Attributes = {
            str(KeyValue): str(Value)
            for KeyValue, Value in ItemValue["attributes"].items()
        }
        if not Attributes:
            Attributes.update(
                {
                    "MetaData": "",
                    "Orientation": "0",
                    "LabelDistance": FmtAction(10),
                    "LabelPosition": FmtAction(0),
                    "IsInVirtualSpace": "0",
                    "IsVisible": "1",
                }
            )
        Attributes.update(
            {
                "Name": ItemValue["name"],
                "Type": str(ItemValue["type"]),
                "Value": FmtAction(ItemValue["value"]),
                "IsDriving": "1" if ItemValue["driving"] else "0",
                "IsActive": "1" if ItemValue["active"] else "0",
                "First": str(First[0]),
                "FirstPos": str(First[1]),
                "Second": str(Second[0]),
                "SecondPos": str(Second[1]),
                "Third": str(Third[0]),
                "ThirdPos": str(Third[1]),
                "ElementIds": " ".join((str(Value[0]) for Value in Elements)),
                "ElementPositions": " ".join((str(Value[1]) for Value in Elements)),
            }
        )
        XmlTree.SubElement(RuleList, "Constrain", Attributes)
    return (Result, Expressions, Dependencies, Diagnostics)


# this definition exists because focused behavior needs one stable owner
def BuildSketch(
    Sketch: Mapping[str, Any],
    Plane: Mapping[str, Any],
    PlaneName: str,
    Parameters: _Parameters,
    PreserveNative: bool = False,
    ProfileConstraintsOnly: bool = False,
) -> tuple[list[XmlTree.Element], list[str]]:
    Transform = (
        Plane.get("transform", {})
        if isinstance(Plane.get("transform"), Mapping)
        else {}
    )
    GeomValue, Indices, GeomDiagnostics = GeomProp(Sketch)
    Constraints, Expressions, Dependencies, RuleDiagnostics = ConstraintsProp(
        Sketch, Indices, Parameters, ProfileOnly=ProfileConstraintsOnly
    )
    SketchDiagnostics = [*GeomDiagnostics, *RuleDiagnostics]
    DiagnosticsProp = (
        JsonProp("KitSketchDiagnosticsJSON", SketchDiagnostics)
        if SketchDiagnostics
        else None
    )
    SketchAttributes = Sketch.get("attributes", {})
    NativeObject = (
        SketchAttributes.get("freecad", {})
        if isinstance(SketchAttributes, Mapping)
        else {}
    )
    NativeProperties = (
        NativeObject.get("properties", {}) if isinstance(NativeObject, Mapping) else {}
    )
    if isinstance(NativeProperties, Mapping) and NativeProperties:
        Properties = NativeA(NativeObject)
        Replacements = [
            StringProp("Label", Sketch.get("name", Sketch.get("id", "Sketch"))),
            GeomValue,
            Constraints,
            ShapeProp("", "InternalShape"),
            ShapeProp(),
            BoolProp("Visibility", not bool(Sketch.get("suppressed"))),
        ]
        if DiagnosticsProp is not None:
            Replacements.append(DiagnosticsProp)
        if not PreserveNative:
            Replacements.insert(1, MakePlacement("Placement", Transform))
        for Replacement in Replacements:
            MergeNamedMut(Properties, Replacement)
        Attachment = next(
            (
                ItemValue
                for ItemValue in Properties
                if ItemValue.get("name") == "AttachmentSupport"
            ),
            None,
        )
        if Attachment is not None and PlaneName:
            for LinkValue in Attachment.findall(".//Link"):
                LinkValue.set("obj", PlaneName)
        Dependencies = [PlaneName]
        Outer = next(
            (
                ItemValue
                for ItemValue in Properties
                if ItemValue.get("name") == "ExternalGeometry"
            ),
            None,
        )
        if Outer is not None:
            Dependencies.extend(
                (
                    Target
                    for LinkValue in Outer.findall(".//Link")
                    if (Target := TextAction(LinkValue.get("obj")))
                )
            )
        if not PreserveNative:
            Properties.extend(
                [
                    LinkProp("SupportPlane", PlaneName, Dynamic=True),
                    StringProp("KitId", Sketch.get("id"), Dynamic=True),
                    JsonProp(
                        "ClosedProfilesJSON",
                        Sketch.get("closed_profile_entity_ids", []),
                    ),
                    JsonProp("SourceSketchJSON", Sketch),
                ]
            )
        return (Properties, Dependencies)
    Expressions.append(("Placement", f"{PlaneName}.Placement"))
    Dependencies.append(PlaneName)
    Properties = [
        StringProp("Label", Sketch.get("name", Sketch.get("id", "Sketch"))),
        MakePlacement("Placement", Transform),
        GeomValue,
        Constraints,
        ExpressionProp(Expressions),
        ShapeProp("", "InternalShape"),
        ShapeProp(),
        LinkSubListProp("AttachmentSupport", [(PlaneName, "")] if PlaneName else []),
        LinkProp("SupportPlane", PlaneName, Dynamic=True),
        StringProp("KitId", Sketch.get("id"), Dynamic=True),
        JsonProp("ClosedProfilesJSON", Sketch.get("closed_profile_entity_ids", [])),
        JsonProp("SourceSketchJSON", Sketch),
        BoolProp("Visibility", False),
    ]
    if DiagnosticsProp is not None:
        Properties.append(DiagnosticsProp)
    return (Properties, Dependencies)


# this definition exists because focused behavior needs one stable owner
def NativeSketch(
    Manifest: Mapping[str, Any],
) -> tuple[tuple[int, int, frozenset[str]], ...]:
    Parameters = ParamCatalog(Items(Manifest.get("parameters", [])))
    Source = Manifest.get("source", {})
    ProfileConstraintsOnly = (
        isinstance(Source, Mapping)
        and TextAction(Source.get("format_id")) == "solidworks.sldprt"
    )
    Result: list[tuple[int, int, frozenset[str]]] = []
    for Sketch in Items(Manifest.get("sketches", [])):
        GeomValue, Indices, GeomDiagnostics = GeomProp(Sketch)
        Constraints, Ignored, Ignored, RuleDiagnostics = ConstraintsProp(
            Sketch, Indices, Parameters, ProfileOnly=ProfileConstraintsOnly
        )
        Diagnostics = (*GeomDiagnostics, *RuleDiagnostics)
        CarrierDiagnostics = tuple(
            (
                ItemValue
                for ItemValue in Diagnostics
                if ItemValue.get("mode") == "carrier_only"
            )
        )
        Result.append(
            (
                1
                + len(GeomValue.findall("./GeometryList/Geometry"))
                + len(Constraints.findall("./ConstraintList/Constrain")),
                len(CarrierDiagnostics),
                frozenset(
                    (
                        TextAction(
                            ItemValue.get("carrier_reason"), "writer_unimplemented"
                        )
                        for ItemValue in CarrierDiagnostics
                    )
                ),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def NativeClosed(Sketch: Mapping[str, Any]) -> int:
    Ignored, Indices, Ignored = GeomProp(Sketch)
    Emitted = set(Indices)
    Result = 0
    for Value in Sequence(Sketch.get("closed_profile_entity_ids", [])):
        Profile = {
            TextAction(ItemValue)
            for ItemValue in Sequence(Value)
            if TextAction(ItemValue)
        }
        if Profile and Profile <= Emitted:
            Result += 1
    return Result


# this definition exists because focused behavior needs one stable owner
def IsPointClose(
    First: tuple[float, float], Second: tuple[float, float], Tolerance: float = 1e-07
) -> bool:
    return MathValue.hypot(First[0] - Second[0], First[1] - Second[1]) <= Tolerance


# this definition exists because focused behavior needs one stable owner
def Segment(
    First: tuple[float, float], Second: tuple[float, float], Third: tuple[float, float]
) -> float:
    return (Second[0] - First[0]) * (Third[1] - First[1]) - (Second[1] - First[1]) * (
        Third[0] - First[0]
    )


# this definition exists because focused behavior needs one stable owner
def IsPointOnSeg(
    Point: tuple[float, float],
    First: tuple[float, float],
    Second: tuple[float, float],
    Tolerance: float = 1e-07,
) -> bool:
    return (
        abs(Segment(First, Second, Point)) <= Tolerance
        and min(First[0], Second[0]) - Tolerance
        <= Point[0]
        <= max(First[0], Second[0]) + Tolerance
        and (
            min(First[1], Second[1]) - Tolerance
            <= Point[1]
            <= max(First[1], Second[1]) + Tolerance
        )
    )


# this definition exists because focused behavior needs one stable owner
def HasSegmentTouch(
    FirstStart: tuple[float, float],
    FirstEnd: tuple[float, float],
    SecondStart: tuple[float, float],
    SecondEnd: tuple[float, float],
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
            abs(Value) <= Tolerance
            and IsPointOnSeg(Point, SegmentStart, SegmentEnd, Tolerance)
            for Value, Point, SegmentStart, SegmentEnd in (
                (FirstA, SecondStart, FirstStart, FirstEnd),
                (FirstB, SecondEnd, FirstStart, FirstEnd),
                (SecondA, FirstStart, SecondStart, SecondEnd),
                (SecondB, FirstEnd, SecondStart, SecondEnd),
            )
        )
    )


# this definition exists because focused behavior needs one stable owner
def LineProfile(
    Entities: list[Mapping[str, Any]],
) -> tuple[tuple[float, float], ...] | None:
    Remaining: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for Entity in Entities:
        GeomValue = Entity.get("geometry", {})
        if not isinstance(GeomValue, Mapping):
            return None
        Start = PointTwo(GeomValue.get("start"))
        EndValue = PointTwo(GeomValue.get("end"))
        if IsPointClose(Start, EndValue):
            return None
        Remaining.append((Start, EndValue))
    if len(Remaining) < 3:
        return None
    FirstStart, FirstEnd = Remaining.pop(0)
    Points = [FirstStart, FirstEnd]
    while Remaining:
        Current = Points[-1]
        NextIndex = next(
            (
                Index
                for Index, (Start, EndValue) in enumerate(Remaining)
                if IsPointClose(Current, Start) or IsPointClose(Current, EndValue)
            ),
            -1,
        )
        if NextIndex < 0:
            return None
        Start, EndValue = Remaining.pop(NextIndex)
        Points.append(EndValue if IsPointClose(Current, Start) else Start)
    if not IsPointClose(Points[-1], Points[0]):
        return None
    Points.pop()
    AreaValue = abs(
        sum(
            (
                First[0] * Second[1] - Second[0] * First[1]
                for First, Second in zip(Points, Points[1:] + Points[:1], strict=True)
            )
        )
    )
    if AreaValue <= 1e-09:
        return None
    Segments = list(zip(Points, Points[1:] + Points[:1], strict=True))
    for FirstIndex, First in enumerate(Segments):
        for SecondIndex in range(FirstIndex + 1, len(Segments)):
            if SecondIndex in {FirstIndex + 1, (FirstIndex - 1) % len(Segments)}:
                continue
            if HasSegmentTouch(*First, *Segments[SecondIndex]):
                return None
    return tuple(Points)


# this definition exists because focused behavior needs one stable owner
def PointSegment(
    Point: tuple[float, float],
    Start: tuple[float, float],
    EndValue: tuple[float, float],
) -> float:
    DeltaX = EndValue[0] - Start[0]
    DeltaY = EndValue[1] - Start[1]
    LengthSquared = DeltaX * DeltaX + DeltaY * DeltaY
    if LengthSquared <= 1e-30:
        return MathValue.hypot(Point[0] - Start[0], Point[1] - Start[1])
    Param = max(
        0.0,
        min(
            1.0,
            ((Point[0] - Start[0]) * DeltaX + (Point[1] - Start[1]) * DeltaY)
            / LengthSquared,
        ),
    )
    Projection = (Start[0] + Param * DeltaX, Start[1] + Param * DeltaY)
    return MathValue.hypot(Point[0] - Projection[0], Point[1] - Projection[1])


# this definition exists because focused behavior needs one stable owner
def IsProfile(
    First: tuple[str, Any], Second: tuple[str, Any], Tolerance: float = 1e-07
) -> bool:
    FirstKind, FirstValue = First
    SecondKind, SecondValue = Second
    if FirstKind == "circle" and SecondKind == "circle":
        FirstCenter, FirstRadius = FirstValue
        SecondCenter, SecondRadius = SecondValue
        Distance = MathValue.hypot(
            FirstCenter[0] - SecondCenter[0], FirstCenter[1] - SecondCenter[1]
        )
        return (
            abs(FirstRadius - SecondRadius) - Tolerance
            <= Distance
            <= FirstRadius + SecondRadius + Tolerance
        )
    if FirstKind == "polygon" and SecondKind == "polygon":
        FirstSegments = list(
            zip(FirstValue, FirstValue[1:] + FirstValue[:1], strict=True)
        )
        SecondSegments = list(
            zip(SecondValue, SecondValue[1:] + SecondValue[:1], strict=True)
        )
        return any(
            (
                HasSegmentTouch(*FirstSegment, *SecondSegment, Tolerance)
                for FirstSegment in FirstSegments
                for SecondSegment in SecondSegments
            )
        )
    Circle = FirstValue if FirstKind == "circle" else SecondValue
    Polygon = FirstValue if FirstKind == "polygon" else SecondValue
    Center, Radius = Circle
    return any(
        (
            PointSegment(Center, Start, EndValue) <= Radius + Tolerance
            and max(
                MathValue.hypot(Center[0] - Start[0], Center[1] - Start[1]),
                MathValue.hypot(Center[0] - EndValue[0], Center[1] - EndValue[1]),
            )
            >= Radius - Tolerance
            for Start, EndValue in zip(Polygon, Polygon[1:] + Polygon[:1], strict=True)
        )
    )


# this definition exists because focused behavior needs one stable owner
def HasNativeProf(Sketch: Mapping[str, Any]) -> bool:
    Ignored, Indices, Ignored = GeomProp(Sketch)
    Entities = {
        TextAction(Entity.get("id")): Entity
        for Entity in Items(Sketch.get("entities", []))
        if TextAction(Entity.get("id"))
    }
    Profiles: list[tuple[str, AnyValue]] = []
    for RawProfile in Sequence(Sketch.get("closed_profile_entity_ids", [])):
        Identifiers = [
            TextAction(Value) for Value in Sequence(RawProfile) if TextAction(Value)
        ]
        if not Identifiers or any((IdValue not in Indices for IdValue in Identifiers)):
            return False
        ProfileEntities = [Entities.get(IdValue, {}) for IdValue in Identifiers]
        Kinds = [
            TextAction(EnumAction(Entity.get("kind"))).lower()
            for Entity in ProfileEntities
        ]
        if Kinds == ["circle"]:
            GeomValue = ProfileEntities[0].get("geometry", {})
            if not isinstance(GeomValue, Mapping):
                return False
            Radius = abs(Number(GeomValue.get("radius")))
            if Radius <= 1e-09:
                return False
            Profiles.append(("circle", (PointTwo(GeomValue.get("center")), Radius)))
            continue
        if Kinds and all((KindValue == "line" for KindValue in Kinds)):
            Polygon = LineProfile(ProfileEntities)
            if Polygon is None:
                return False
            Profiles.append(("polygon", Polygon))
            continue
        return False
    return bool(Profiles) and (
        not any(
            (
                IsProfile(First, Second)
                for Index, First in enumerate(Profiles)
                for Second in Profiles[Index + 1 :]
            )
        )
    )


# this definition exists because focused behavior needs one stable owner
def NativeShape(Manifest: Mapping[str, Any]) -> int:
    Source = Manifest.get("source", {})
    SourceFormatId = (
        TextAction(Source.get("format_id")) if isinstance(Source, Mapping) else ""
    )
    Sketches = {
        TextAction(Sketch.get("id")): Sketch
        for Sketch in Items(Manifest.get("sketches", []))
        if TextAction(Sketch.get("id"))
    }
    Count = 0
    for Feature in Items(
        Manifest.get("feature_timeline", Manifest.get("timeline", []))
    ):
        if TextAction(
            EnumAction(Feature.get("kind"))
        ).casefold() != "extrusion" or bool(Feature.get("suppressed")):
            continue
        Definition = Feature.get("definition", {})
        Attributes = Feature.get("attributes", {})
        if not isinstance(Definition, Mapping):
            Definition = {}
        if not isinstance(Attributes, Mapping):
            Attributes = {}
        if (
            max(
                abs(
                    Number(
                        Definition.get("length"), Number(Attributes.get("length_mm"))
                    )
                ),
                abs(Number(Definition.get("second_length"))),
            )
            <= 1e-12
        ):
            continue
        Sketch = Sketches.get(TextAction(Feature.get("sketch_id")))
        if Sketch is None or not NativeClosed(Sketch):
            continue
        if SourceFormatId == "solidworks.sldprt" and (not HasNativeProf(Sketch)):
            continue
        Count += 1
    return Count


# this definition exists because focused behavior needs one stable owner
def NativeSketchB(Manifest: Mapping[str, Any]) -> tuple[tuple[int, int], ...]:
    return tuple(
        ((Native, Carrier) for Native, Carrier, Ignored in NativeSketch(Manifest))
    )


# this definition exists because focused behavior needs one stable owner
def NativeSketchA(Manifest: Mapping[str, Any]) -> tuple[frozenset[str], ...]:
    return tuple((Reasons for Ignored, Ignored, Reasons in NativeSketch(Manifest)))


# this definition exists because focused behavior needs one stable owner
def FeatureParam(
    Feature: Mapping[str, Any], Parameters: _Parameters, Expected: float
) -> str:
    IdsValue = [
        TextAction(Value) for Value in Sequence(Feature.get("parameter_ids", []))
    ]
    if not IdsValue:
        IdsValue = [
            ParamId
            for ParamId, ItemValue in Parameters.ByIdentifier.items()
            if TextAction(ItemValue.get("owner_id")) == TextAction(Feature.get("id"))
        ]
    LengthIds = [
        ParamId for ParamId in IdsValue if Parameters.kind(ParamId) == "length"
    ]
    for ParamId in LengthIds:
        if MathValue.isclose(
            abs(Parameters.value(ParamId)), abs(Expected), rel_tol=1e-09, abs_tol=1e-09
        ):
            return ParamId
    return LengthIds[0] if LengthIds else IdsValue[0] if IdsValue else ""


# this definition exists because focused behavior needs one stable owner
def FeatureMeta(Feature: Mapping[str, Any], RoleValue: str) -> list[XmlTree.Element]:
    return [
        StringProp("KitId", Feature.get("id"), Dynamic=True),
        StringProp("KitRole", RoleValue, Dynamic=True),
        StringProp("FeatureKind", EnumAction(Feature.get("kind")), Dynamic=True),
        StringProp("Operation", EnumAction(Feature.get("operation")), Dynamic=True),
        IntegerProp("TimelineOrder", Feature.get("order", 0), Dynamic=True),
        BoolProp("Suppressed", bool(Feature.get("suppressed")), Dynamic=True),
        JsonProp("SourceFeatureJSON", Feature),
    ]


# this definition exists because focused behavior needs one stable owner
def DefinitionProp(NameValue: str, Value: Any) -> XmlTree.Element | None:
    PropName = "Definition" + SafeAction(NameValue, "Value")
    if isinstance(Value, bool):
        return BoolProp(PropName, Value, Dynamic=True)
    if isinstance(Value, int):
        return IntegerProp(PropName, Value, Dynamic=True)
    if isinstance(Value, float):
        return FloatProp(PropName, Value, Dynamic=True)
    if isinstance(Value, str):
        return StringProp(PropName, Value, Dynamic=True)
    if isinstance(Value, Mapping):
        ValueType = TextAction(Value.get("$type"))
        if ValueType == "ParameterValue":
            RawValue = Value.get("value")
            KindValue = TextAction(EnumAction(Value.get("kind"))).casefold()
            if isinstance(RawValue, bool):
                return BoolProp(PropName, RawValue, Dynamic=True)
            if isinstance(RawValue, int) and KindValue == "integer":
                return IntegerProp(PropName, RawValue, Dynamic=True)
            if isinstance(RawValue, (int, float)):
                PropType = {
                    "angle": "App::PropertyAngle",
                    "length": "App::PropertyLength",
                }.get(KindValue, "App::PropertyFloat")
                return FloatProp(PropName, RawValue, PropType, Dynamic=True)
            if isinstance(RawValue, str):
                return StringProp(PropName, RawValue, Dynamic=True)
        KeysValue = set(Value)
        if {"x", "y", "z"} <= KeysValue:
            return VectorProp(PropName, Vector(Value, (0.0, 0.0, 0.0)), Dynamic=True)
    if isinstance(Value, (list, tuple)) and all(
        (isinstance(ItemValue, str) for ItemValue in Value)
    ):
        return StringListProp(PropName, list(Value), Dynamic=True)
    return None


# this definition exists because focused behavior needs one stable owner
def DefinitionProps(Definition: Mapping[str, Any]) -> list[XmlTree.Element]:
    Result: list[XmlTree.Element] = []
    for NameValue, Value in Definition.items():
        if NameValue in {"$type", "object_data"}:
            continue
        PropElem = DefinitionProp(NameValue, Value)
        if PropElem is not None:
            Result.append(PropElem)
    return Result


# this definition exists because focused behavior needs one stable owner
def ShapeProp(FileName: str = "", NameValue: str = "Shape") -> XmlTree.Element:
    Result = PropAction(NameValue, "Part::PropertyPartShape")
    Attributes = {"file": FileName} if FileName else {}
    XmlTree.SubElement(Result, "Part", Attributes)
    if FileName:
        XmlTree.SubElement(Result, "ElementMap")
    return Result


# this definition exists because focused behavior needs one stable owner
def FilletEdgesProp(FileName: str) -> XmlTree.Element:
    Result = PropAction("Edges", "Part::PropertyFilletEdges")
    XmlTree.SubElement(Result, "FilletEdges", {"file": FileName})
    return Result


# this definition exists because focused behavior needs one stable owner
def EdgeLinkProp(BaseValue: str, EdgeIndices: list[int]) -> XmlTree.Element:
    Result = PropAction("EdgeLinks", "App::PropertyLinkSub")
    Child = XmlTree.SubElement(
        Result, "LinkSub", {"value": BaseValue, "count": str(len(EdgeIndices))}
    )
    for EdgeIndex in EdgeIndices:
        XmlTree.SubElement(Child, "Sub", {"value": f"Edge{EdgeIndex}"})
    return Result


# this definition exists because focused behavior needs one stable owner
def FilletEdgesData(EdgeIndices: list[int], Radius: float) -> bytes:
    return Struct.pack("<I", len(EdgeIndices)) + b"".join(
        (Struct.pack("<idd", EdgeIndex, Radius, Radius) for EdgeIndex in EdgeIndices)
    )


# this definition exists because focused behavior needs one stable owner
def PayloadBytes(Payload: Mapping[str, Any]) -> bytes | None:
    DataValue = Payload.get("data")
    if isinstance(DataValue, Mapping):
        if "$bytes" in DataValue:
            try:
                return BaseSixFour.b64decode(
                    TextAction(DataValue["$bytes"]), validate=True
                )
            except ValueError:
                return None
        if DataValue.get("encoding") == "base64" and "data" in DataValue:
            try:
                return BaseSixFour.b64decode(
                    TextAction(DataValue["data"]), validate=True
                )
            except ValueError:
                return None
    if isinstance(DataValue, str):
        try:
            return BaseSixFour.b64decode(DataValue, validate=True)
        except ValueError:
            return DataValue.encode("utf-8")
    return bytes(DataValue) if isinstance(DataValue, (bytes, bytearray)) else None


# this definition exists because focused behavior needs one stable owner
def PayloadSuffix(Payload: Mapping[str, Any]) -> str:
    Declared = TextAction(Payload.get("file_extension"))
    if RegexLib.fullmatch("\\.[A-Za-z0-9_]{1,16}", Declared):
        return Declared
    Suffix = PurePosixPath(TextAction(Payload.get("source_stream"))).suffix
    if RegexLib.fullmatch("\\.[A-Za-z0-9_]{1,16}", Suffix):
        return Suffix
    return ".bin"


# this definition exists because focused behavior needs one stable owner
def PayloadRole(Payload: Mapping[str, Any]) -> str:
    return TextAction(EnumAction(Payload.get("role"))).lower()


# this definition exists because focused behavior needs one stable owner
def NativeBrepKey(
    Payload: Mapping[str, Any], DataValue: bytes, NativeDocShaTwoFiveSix: str
) -> KNativeBrepKey | None:
    Provenance = Payload.get("provenance")
    if not isinstance(Provenance, Mapping):
        return None
    NativeId = TextAction(Provenance.get("native_id"))
    if not NativeDocShaTwoFiveSix or not NativeId:
        return None
    Attributes = Payload.get("attributes", {})
    if not isinstance(Attributes, Mapping):
        return None
    Binding = {
        "format_id": Payload.get("format_id"),
        "kind": Payload.get("kind"),
        "schema": Payload.get("schema"),
        "source_stream": Payload.get("source_stream"),
        "provenance": Provenance,
        "role": Payload.get("role"),
        "file_extension": Payload.get("file_extension"),
        "attributes": {
            NameValue: Attributes.get(NameValue)
            for NameValue in (
                "freecad_object",
                "freecad_object_type",
                "freecad_property",
                "freecad_property_data",
                "freecad_part_attributes",
                "freecad_sidecars",
                KNativeDocShaTwoFiveSix,
            )
        },
    }
    try:
        Canonical = JsonValue.dumps(
            Binding, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return (
        NativeDocShaTwoFiveSix,
        Hashlib.sha256(DataValue).hexdigest(),
        TextAction(Payload.get("source_stream")),
        NativeId,
        Hashlib.sha256(Canonical).hexdigest(),
        TextAction(Payload.get("format_id")).casefold(),
    )


# this definition exists because focused behavior needs one stable owner
def NativeDocShaTwo(Manifest: Mapping[str, Any]) -> str:
    Matches = []
    for Payload in Items(
        Manifest.get("brep_payloads", Manifest.get("native_payloads", []))
    ):
        if (
            TextAction(Payload.get("id")) != "freecad:native-document"
            or TextAction(Payload.get("format_id")) != FormatId
            or TextAction(EnumAction(Payload.get("role"))).casefold() != "document"
            or (TextAction(Payload.get("kind")) != "native_document")
        ):
            continue
        DataValue = PayloadBytes(Payload)
        if DataValue is None:
            continue
        Digest = Hashlib.sha256(DataValue).hexdigest()
        if TextAction(Payload.get("sha256")) == Digest:
            Matches.append(Digest)
    return Matches[0] if len(Matches) == 1 else ""


# this definition exists because focused behavior needs one stable owner
def PayloadNative(Payload: Mapping[str, Any]) -> str:
    Attributes = Payload.get("attributes", {})
    if not isinstance(Attributes, Mapping):
        return ""
    Value = TextAction(Attributes.get(KNativeDocShaTwoFiveSix)).casefold()
    return Value if RegexLib.fullmatch("[0-9a-f]{64}", Value) is not None else ""


# this definition exists because focused behavior needs one stable owner
def FreecadBrep(
    Payload: Mapping[str, Any],
    DataValue: bytes,
    NativeDocShaTwoFiveSix: str,
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
) -> bytes | None:
    if TextAction(Payload.get("format_id")).casefold() not in FreecadBrepFormatIds:
        return None
    PayloadNativeDocShaTwoSix = PayloadNative(Payload)
    if PayloadNativeDocShaTwoSix:
        NativeDocShaTwoFiveSix = PayloadNativeDocShaTwoSix
    if NativeBrepKey(Payload, DataValue, NativeDocShaTwoFiveSix) in TrustedNativeBreps:
        return DataValue
    return ProvenAsciiBrep(DataValue)


# this binding exists because shared behavior needs one stable value
KIdentityMatrix = (
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


# this definition exists because focused behavior needs one stable owner
def AsmData(Manifest: Mapping[str, Any]) -> Mapping[str, AnyValue] | None:
    Value = Manifest.get("assembly")
    if isinstance(Value, Mapping):
        return Value
    MetaValue = Manifest.get("metadata", {})
    if isinstance(MetaValue, Mapping):
        Value = MetaValue.get("assembly")
        if isinstance(Value, Mapping):
            return Value
    return None


# this definition exists because focused behavior needs one stable owner
def MatrixValues(Value: Any) -> tuple[float, ...]:
    if isinstance(Value, Mapping):
        Value = Value.get("values", Value.get("matrix", Value))
    Values = tuple((Number(ItemValue) for ItemValue in Sequence(Value)))
    return Values if len(Values) == 16 else KIdentityMatrix


# this definition exists because focused behavior needs one stable owner
def MatrixProduct(
    LeftValue: tuple[float, ...], Right: tuple[float, ...]
) -> tuple[float, ...]:
    return tuple(
        (
            sum(
                (
                    LeftValue[RowValue * 4 + Index] * Right[Index * 4 + Column]
                    for Index in range(4)
                )
            )
            for RowValue in range(4)
            for Column in range(4)
        )
    )


# this definition exists because focused behavior needs one stable owner
def MatrixTransform(Values: tuple[float, ...]) -> dict[str, AnyValue]:
    return {
        "origin": {"x": Values[3], "y": Values[7], "z": Values[11]},
        "x_axis": {"x": Values[0], "y": Values[4], "z": Values[8]},
        "y_axis": {"x": Values[1], "y": Values[5], "z": Values[9]},
        "z_axis": {"x": Values[2], "y": Values[6], "z": Values[10]},
    }


# this definition exists because focused behavior needs one stable owner
def MatrixScale(Values: tuple[float, ...]) -> tuple[float, float, float]:
    return tuple(
        (
            MathValue.sqrt(
                sum((Values[RowValue * 4 + Column] ** 2 for RowValue in range(3)))
            )
            for Column in range(3)
        )
    )


# this definition exists because focused behavior needs one stable owner
def Expanded(
    AsmValue: Mapping[str, Any],
) -> list[tuple[dict[str, AnyValue], tuple[str, ...], tuple[float, ...], bool]]:
    Instances = Items(AsmValue.get("instances", AsmValue.get("components", [])))
    Children: dict[str, list[dict[str, AnyValue]]] = {}
    for Instance in Instances:
        Owner = TextAction(Instance.get("owner_definition_id"))
        Children.setdefault(Owner, []).append(Instance)
    for Values in Children.values():

        # this callback exists because local behavior needs one focused transformation
        Values.sort(
            key=lambda ItemValue: (
                int(Number(ItemValue.get("order"))),
                TextAction(ItemValue.get("id")),
            )
        )
    RootId = TextAction(AsmValue.get("root_definition_id"))
    Result: list[
        tuple[dict[str, AnyValue], tuple[str, ...], tuple[float, ...], bool]
    ] = []

    # this definition exists because focused behavior needs one stable owner
    def Visit(
        OwnerId: str,
        Parent: tuple[float, ...],
        PathValue: tuple[str, ...],
        InheritedSuppression: bool,
        Active: frozenset[str],
    ) -> None:
        if OwnerId in Active:
            return
        NextActive = Active | {OwnerId}
        for Instance in Children.get(OwnerId, []):
            InstanceId = TextAction(Instance.get("id"))
            DefinitionId = TextAction(Instance.get("definition_id"))
            Matrix = MatrixValues(Instance.get("transform", {}))
            World = MatrixProduct(Parent, Matrix)
            InstancePath = (*PathValue, InstanceId)
            Suppressed = InheritedSuppression or bool(Instance.get("suppressed"))
            Result.append((Instance, InstancePath, World, Suppressed))
            Visit(DefinitionId, World, InstancePath, Suppressed, NextActive)

    Visit(RootId, KIdentityMatrix, (), False, frozenset())
    return Result


# this definition exists because focused behavior needs one stable owner
def MeshProp(FileName: str) -> XmlTree.Element:
    Result = PropAction("Mesh", "Mesh::PropertyMeshKernel")
    XmlTree.SubElement(Result, "Mesh", {"file": FileName})
    return Result


# this definition exists because focused behavior needs one stable owner
def Points(Value: Any) -> list[tuple[float, float, float]]:
    Values = Sequence(Value)
    if Values and all((isinstance(ItemValue, (int, float)) for ItemValue in Values)):
        return [
            (
                Number(Values[Index]),
                Number(Values[Index + 1]),
                Number(Values[Index + 2]),
            )
            for Index in range(0, len(Values) - 2, 3)
        ]
    return [Vector(ItemValue, (0.0, 0.0, 0.0)) for ItemValue in Values]


# this definition exists because focused behavior needs one stable owner
def TriangleIndices(Value: Any) -> tuple[int, int, int] | None:
    Marked = Sequence(Value)
    if Marked:
        Values = Marked
    elif isinstance(Value, Mapping):
        Source = Value.get("indices", Value.get("vertices", Value.get("points", [])))
        Values = Sequence(Source)
        if not Values:
            Values = [Value.get("a"), Value.get("b"), Value.get("c")]
    else:
        Values = Sequence(Value)
    if len(Values) < 3:
        return None
    return tuple((int(Number(ItemValue)) for ItemValue in Values[:3]))


# this definition exists because focused behavior needs one stable owner
def IsTriangleValid(
    Vertices: list[tuple[float, float, float]], Triangle: tuple[int, int, int]
) -> bool:
    if len(set(Triangle)) != 3 or any(
        (Index < 0 or Index >= len(Vertices) for Index in Triangle)
    ):
        return False
    First, Second, Third = (Vertices[Index] for Index in Triangle)
    LeftValue = tuple((Second[Index] - First[Index] for Index in range(3)))
    Right = tuple((Third[Index] - First[Index] for Index in range(3)))
    Cross = (
        LeftValue[1] * Right[2] - LeftValue[2] * Right[1],
        LeftValue[2] * Right[0] - LeftValue[0] * Right[2],
        LeftValue[0] * Right[1] - LeftValue[1] * Right[0],
    )
    return sum((Value * Value for Value in Cross)) > 1e-24


# this definition exists because focused behavior needs one stable owner
def Tessellation(
    Value: Any,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    if not isinstance(Value, Mapping):
        return ([], [])
    Vertices = Points(Value.get("vertices", Value.get("positions_mm", [])))
    Triangles = [
        Triangle
        for ItemValue in Sequence(Value.get("triangles", []))
        if (Triangle := TriangleIndices(ItemValue)) is not None
    ]
    if Vertices and Triangles:
        return (
            Vertices,
            [Triangle for Triangle in Triangles if IsTriangleValid(Vertices, Triangle)],
        )
    Vertices = []
    Triangles = []
    Faces = Items(Value.get("faces", []))
    for FaceValue in Faces:
        FaceVertices = Points(
            FaceValue.get("positions_mm", FaceValue.get("vertices", []))
        )
        BaseValue = len(Vertices)
        Vertices.extend(FaceVertices)
        Cursor = 0
        StripLengths = [
            int(Number(ItemValue))
            for ItemValue in Sequence(FaceValue.get("strip_lengths", []))
        ]
        if not StripLengths and FaceVertices:
            StripLengths = [len(FaceVertices)]
        for StripLength in StripLengths:
            for Offset in range(max(0, StripLength - 2)):
                if Offset % 2:
                    Triangle = (
                        BaseValue + Cursor + Offset + 1,
                        BaseValue + Cursor + Offset,
                        BaseValue + Cursor + Offset + 2,
                    )
                else:
                    Triangle = (
                        BaseValue + Cursor + Offset,
                        BaseValue + Cursor + Offset + 1,
                        BaseValue + Cursor + Offset + 2,
                    )
                if IsTriangleValid(Vertices, Triangle):
                    Triangles.append(Triangle)
            Cursor += StripLength
    return (Vertices, Triangles)


# this definition exists because focused behavior needs one stable owner
def DefinitionA(Definition: Mapping[str, Any]) -> AnyValue:
    Direct = Definition.get("tessellation")
    if isinstance(Direct, Mapping):
        return Direct
    Attributes = Definition.get("attributes", {})
    if isinstance(Attributes, Mapping):
        return Attributes.get("tessellation", {})
    return {}


# this definition exists because focused behavior needs one stable owner
def DefinitionMesh(
    Manifest: Mapping[str, Any], Definition: Mapping[str, Any]
) -> list[Mapping[str, AnyValue]]:
    Meshes = {
        TextAction(ItemValue.get("id")): ItemValue
        for ItemValue in Items(Manifest.get("meshes", []))
    }
    Result = [
        Meshes[MeshId]
        for MeshId in (
            TextAction(Value) for Value in Sequence(Definition.get("mesh_ids", []))
        )
        if MeshId in Meshes
    ]
    Inline = DefinitionA(Definition)
    if isinstance(Inline, Mapping) and Inline:
        Result.append(Inline)
    return Result


# this definition exists because focused behavior needs one stable owner
def MeshKernelData(
    Vertices: list[tuple[float, float, float]], Triangles: list[tuple[int, int, int]]
) -> bytes:
    Neighbors = [[-1, -1, -1] for Ignored in Triangles]
    EdgeUses: dict[tuple[int, int], tuple[int, ...] | None] = {}
    for TriangleIndex, Triangle in enumerate(Triangles):
        for EdgeIndex, EdgeValue in enumerate(
            (
                (Triangle[0], Triangle[1]),
                (Triangle[1], Triangle[2]),
                (Triangle[2], Triangle[0]),
            )
        ):
            KeyValue = tuple(sorted(EdgeValue))
            Previous = EdgeUses.get(KeyValue, ())
            if Previous == ():
                EdgeUses[KeyValue] = (TriangleIndex, EdgeIndex)
            elif Previous is None:
                continue
            elif len(Previous) == 2:
                PreviousTriangle, PreviousEdge = Previous
                Neighbors[PreviousTriangle][PreviousEdge] = TriangleIndex
                Neighbors[TriangleIndex][EdgeIndex] = PreviousTriangle
                EdgeUses[KeyValue] = (
                    PreviousTriangle,
                    PreviousEdge,
                    TriangleIndex,
                    EdgeIndex,
                )
            else:
                FirstTriangle, FirstEdge, SecondTriangle, SecondEdge = Previous
                Neighbors[FirstTriangle][FirstEdge] = -1
                Neighbors[SecondTriangle][SecondEdge] = -1
                EdgeUses[KeyValue] = None
    Banner = (b"MESH-" * 52)[:255] + b"\n"
    Result = bytearray(Struct.pack("<II", 2695938256, 65536))
    Result.extend(Banner)
    Result.extend(Struct.pack("<II", len(Vertices), len(Triangles)))
    for Vertex in Vertices:
        Result.extend(Struct.pack("<fff", *Vertex))
    for Triangle, Adjacent in zip(Triangles, Neighbors):
        Result.extend(
            Struct.pack(
                "<IIIIII", *(Value & 4294967295 for Value in (*Triangle, *Adjacent))
            )
        )
    if Vertices:
        Minimum = tuple(
            (min((Vertex[Index] for Vertex in Vertices)) for Index in range(3))
        )
        Maximum = tuple(
            (max((Vertex[Index] for Vertex in Vertices)) for Index in range(3))
        )
    else:
        Minimum = Maximum = (0.0, 0.0, 0.0)
    Result.extend(
        Struct.pack(
            "<ffffff",
            Minimum[0],
            Maximum[0],
            Minimum[1],
            Maximum[1],
            Minimum[2],
            Maximum[2],
        )
    )
    return bytes(Result)


# this definition exists because focused behavior needs one stable owner
def UniquePayload(PayloadEntries: Mapping[str, bytes], Requested: str) -> str:
    PathValue = PurePosixPath(Requested)
    StemValue = PathValue.stem
    Suffix = PathValue.suffix
    Parent = PathValue.parent
    Choice = str(PathValue)
    Index = 2
    while Choice in PayloadEntries:
        Choice = str(Parent / f"{StemValue}_{Index}{Suffix}")
        Index += 1
    return Choice


# this definition exists because focused behavior needs one stable owner
def RenamePropLinks(
    PropElem: ET.Element, Names: Mapping[str, str], Files: Mapping[str, str]
) -> None:
    for ElemValue in PropElem.iter():
        if ElemValue.tag == "Link" and ElemValue.get("value") in Names:
            ElemValue.set("value", Names[ElemValue.get("value", "")])
        elif ElemValue.tag == "XLink" and ElemValue.get("name") in Names:
            ElemValue.set("name", Names[ElemValue.get("name", "")])
        elif ElemValue.tag == "LinkSub" and ElemValue.get("value") in Names:
            ElemValue.set("value", Names[ElemValue.get("value", "")])
        FileName = ElemValue.get("file")
        if FileName in Files:
            ElemValue.set("file", Files[FileName])
        Expression = ElemValue.get("expression")
        if Expression:

            # this callback exists because local behavior needs one focused transformation
            for OldValue, NewValue in sorted(
                Names.items(), key=lambda ItemValue: len(ItemValue[0]), reverse=True
            ):
                Expression = RegexLib.sub(
                    f"\\b{RegexLib.escape(OldValue)}\\b", NewValue, Expression
                )
            ElemValue.set("expression", Expression)


# this definition exists because focused behavior needs one stable owner
def ImportCompMut(
    Graph: _Graph,
    DocValue: Mapping[str, Any],
    Prefix: str,
    PayloadEntries: dict[str, bytes],
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
) -> tuple[str, list[str]]:
    Canonical = JsonValue.dumps(
        DocValue, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    Digest = Hashlib.sha256(Canonical.encode("utf-8")).hexdigest()
    DocXml, ChildPayloads = BuildDocXml(
        DocValue, "", Digest, TrustedNativeBreps=TrustedNativeBreps
    )
    RootValue = XmlTree.fromstring(DocXml)
    ObjectNodes = RootValue.findall("./Objects/Object")
    DataNodes = {
        NodeValue.get("name", ""): NodeValue
        for NodeValue in RootValue.findall("./ObjectData/Object")
    }
    Dependencies = {
        NodeValue.get("Name", ""): [
            Child.get("Name", "") for Child in NodeValue.findall("./Dep")
        ]
        for NodeValue in RootValue.findall("./Objects/ObjectDeps")
    }
    MetaNode = DataNodes.get("KitMetadata")
    OuterOld = ""
    FinalOld = ""
    if MetaNode is not None:
        Outer = MetaNode.find(
            "./Properties/Property[@name='ExternalLinkTarget']/String"
        )
        OuterOld = Outer.get("value", "") if Outer is not None else ""
        Final = MetaNode.find("./Properties/Property[@name='FinalFeature']/String")
        FinalOld = Final.get("value", "") if Final is not None else ""
    Included = [
        NodeValue for NodeValue in ObjectNodes if NodeValue.get("name") != "KitMetadata"
    ]
    Names = {
        NodeValue.get("name", ""): Graph.unique(
            f"{Prefix}_{NodeValue.get('name', '')}", "Component"
        )
        for NodeValue in Included
    }
    Files: dict[str, str] = {}
    for FileName, DataValue in sorted(ChildPayloads.items()):
        if FileName.startswith("interchange/native/"):
            Requested = str(
                PurePosixPath(
                    "interchange", "components", Prefix, PurePosixPath(FileName).name
                )
            )
        else:
            Requested = f"{Prefix}_{PurePosixPath(FileName).name}"
        Renamed = UniquePayload(PayloadEntries, Requested)
        PayloadEntries[Renamed] = DataValue
        Files[FileName] = Renamed
    Imported: list[str] = []
    for NodeValue in Included:
        OldName = NodeValue.get("name", "")
        DataNode = DataNodes.get(OldName)
        if DataNode is None:
            continue
        Properties = [
            CopyValue.deepcopy(Value)
            for Value in DataNode.findall("./Properties/Property")
        ]
        for PropElem in Properties:
            RenamePropLinks(PropElem, Names, Files)
        Extensions = tuple(
            (
                Value.get("type", "")
                for Value in DataNode.findall("./Extensions/Extension")
                if Value.get("type")
            )
        )
        ImportedObject = Object(
            NodeValue.get("type", "App::FeaturePython"),
            Names[OldName],
            properties=Properties,
            dependencies=[
                Names[Value]
                for Value in Dependencies.get(OldName, [])
                if Value in Names
            ],
            touched=NodeValue.get("Touched") == "1",
            extensions=Extensions,
        )
        Graph.Objects.append(ImportedObject)
        Imported.append(ImportedObject.name)
    Target = Names.get(OuterOld, "") or Names.get(FinalOld, "")
    if not Target:
        for NodeValue in reversed(Included):
            OldName = NodeValue.get("name", "")
            DataNode = DataNodes.get(OldName)
            if (
                DataNode is not None
                and DataNode.find("./Properties/Property[@name='Shape']") is not None
            ):
                Target = Names.get(OldName, "")
                break
    return (Target, Imported)


# this definition exists because focused behavior needs one stable owner
def MateJointType(KindValue: Any) -> str | None:
    return JointTypeByMateKind.get(TextAction(EnumAction(KindValue)).lower())


# this definition exists because focused behavior needs one stable owner
def MateScalar(Value: Any) -> float:
    if isinstance(Value, Mapping):
        return Number(Value.get("value"))
    return Number(Value)


# this definition exists because focused behavior needs one stable owner
def MateSubelements(Entity: Mapping[str, Any]) -> list[str]:
    for Value in (
        TextAction(Entity.get("source_entity_id")),
        TextAction(Entity.get("selection_id")),
    ):
        if RegexLib.fullmatch("(?:Face|Edge|Vertex)\\d+", Value):
            return [Value, Value]
    return []


# this definition exists because focused behavior needs one stable owner
def Without(Value: Mapping[str, Any]) -> dict[str, AnyValue]:
    Result = dict(Value)
    Result.pop("tessellation", None)
    Attributes = Result.get("attributes")
    if isinstance(Attributes, Mapping):
        Cleaned = dict(Attributes)
        Cleaned.pop("tessellation", None)
        Result["attributes"] = Cleaned
    return Result


# this definition exists because focused behavior needs one stable owner
def AddOriginMut(Graph: _Graph, AsmValue: _Object) -> str:
    Origin = Graph.add(
        "App::Origin",
        f"{AsmValue.name}_Origin",
        "Origin",
        Extensions=("App::GeoFeatureGroupExtension",),
    )
    Definitions = [
        ("App::Line", "X_Axis", "X-axis", "X_Axis", KIdentityMatrix),
        (
            "App::Line",
            "Y_Axis",
            "Y-axis",
            "Y_Axis",
            (
                0.0,
                0.0,
                1.0,
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
                0.0,
                1.0,
            ),
        ),
        (
            "App::Line",
            "Z_Axis",
            "Z-axis",
            "Z_Axis",
            (
                0.0,
                -1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                -1.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ),
        ),
        ("App::Plane", "XY_Plane", "XY-plane", "XY_Plane", KIdentityMatrix),
        (
            "App::Plane",
            "XZ_Plane",
            "XZ-plane",
            "XZ_Plane",
            (
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                -1.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ),
        ),
        (
            "App::Plane",
            "YZ_Plane",
            "YZ-plane",
            "YZ_Plane",
            (
                0.0,
                0.0,
                1.0,
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
                0.0,
                1.0,
            ),
        ),
        ("App::Point", "Origin_Point", "Origin-Point", "Origin", KIdentityMatrix),
    ]
    Features: list[str] = []
    for TypeId, Suffix, Label, RoleValue, Matrix in Definitions:
        Feature = Graph.add(TypeId, f"{AsmValue.name}_{Suffix}", Suffix)
        Feature.properties.extend(
            [
                StringProp("Label", Label),
                MakePlacement("Placement", MatrixTransform(Matrix)),
                StringProp("Role", RoleValue),
                BoolProp("Visibility", False),
            ]
        )
        Features.append(Feature.name)
    Origin.properties.extend(
        [
            StringProp("Label", "Origin"),
            LinkListProp("OriginFeatures", Features),
            MakePlacement("Placement", MatrixTransform(KIdentityMatrix)),
            BoolProp("Visibility", False),
        ]
    )
    Origin.dependencies.extend(Features)
    AsmValue.properties.append(LinkProp("Origin", Origin.name))
    AsmValue.dependencies.append(Origin.name)
    return Origin.name


# this definition exists because focused behavior needs one stable owner
def GroundJointMut(
    Graph: _Graph,
    Component: str,
    Label: str,
    Placement: tuple[float, ...],
    Source: Mapping[str, Any] | None = None,
) -> Object:
    Source = Source if isinstance(Source, Mapping) else {}
    Joint = Graph.add(
        TextAction(Source.get("type_id"), "App::FeaturePython"),
        Source.get("name", f"Grounded_{Label}"),
        "GroundedJoint",
        Touched=bool(Source.get("touched")),
        Extensions=Native(Source),
    )
    Joint.properties.extend(NativeA(Source))
    ObjectToGround = next(
        (
            ItemValue
            for ItemValue in Joint.properties
            if ItemValue.get("name") == JointGroundProp
        ),
        None,
    )
    if ObjectToGround is None:
        ObjectToGround = PropAction(JointGroundProp, "App::PropertyLink")
        ObjectToGround.attrib.update(
            {
                "group": "Ground",
                "doc": "The object to ground",
                "attr": "0",
                "ro": "0",
                "hide": "0",
                "status": "2097152",
            }
        )
        Joint.properties.append(ObjectToGround)
    LinkValue = ObjectToGround.find("./Link")
    if LinkValue is None:
        LinkValue = XmlTree.SubElement(ObjectToGround, "Link")
    LinkValue.set("value", Component)
    PlacementProp = next(
        (
            ItemValue
            for ItemValue in Joint.properties
            if ItemValue.get("name") == "Placement"
        ),
        None,
    )
    if PlacementProp is None:
        PlacementProp = PropAction("Placement", "App::PropertyPlacement")
        PlacementProp.attrib.update(
            {
                "group": "Ground",
                "doc": "This is where the part is grounded.",
                "attr": "0",
                "ro": "0",
                "hide": "0",
                "status": "2097152",
            }
        )
        Joint.properties.append(PlacementProp)
    PlacementValue = MakePlacement("Placement", MatrixTransform(Placement)).find(
        "./PropertyPlacement"
    )
    CurrentPlacement = PlacementProp.find("./PropertyPlacement")
    if CurrentPlacement is None:
        CurrentPlacement = XmlTree.SubElement(PlacementProp, "PropertyPlacement")
    if PlacementValue is not None:
        CurrentPlacement.attrib.clear()
        CurrentPlacement.attrib.update(PlacementValue.attrib)
    if not Joint.properties:
        raise ValueError("grounded joint properties could not be generated")
    if not any(
        (ItemValue.get("name") == "ExpressionEngine" for ItemValue in Joint.properties)
    ):
        Joint.properties.insert(0, ExpressionProp([]))
    if not any((ItemValue.get("name") == "Label" for ItemValue in Joint.properties)):
        Joint.properties.insert(
            1, PropAction("Label", "App::PropertyString", Status="134217728")
        )
        XmlTree.SubElement(Joint.properties[1], "String", {"value": "GroundedJoint"})
    if not any((ItemValue.get("name") == "Label2" for ItemValue in Joint.properties)):
        LabelTwo = PropAction("Label2", "App::PropertyString", Status="67108992")
        XmlTree.SubElement(LabelTwo, "String", {"value": ""})
        Joint.properties.append(LabelTwo)
    if not any((ItemValue.get("name") == "Proxy" for ItemValue in Joint.properties)):
        Joint.properties.append(PythonProxyProp("JointObject", "GroundedJoint"))
    if not any(
        (ItemValue.get("name") == "Visibility" for ItemValue in Joint.properties)
    ):
        Visibility = PropAction("Visibility", "App::PropertyBool", Status="648")
        XmlTree.SubElement(Visibility, "Bool", {"value": "true"})
        Joint.properties.append(Visibility)
    Joint.dependencies.append(Component)
    return Joint


# this definition exists because focused behavior needs one stable owner
def ReplaceNameMut(
    Properties: list[ET.Element], NameValue: str, Replacement: ET.Element
) -> None:
    for Index, PropElem in enumerate(Properties):
        if PropElem.get("name") == NameValue:
            Properties[Index] = Replacement
            return
    Properties.append(Replacement)


# this definition exists because focused behavior needs one stable owner
def AddAsmMut(
    Graph: _Graph,
    Manifest: Mapping[str, Any],
    PayloadEntries: dict[str, bytes],
    OuterLinks: Mapping[str, Mapping[str, Any]],
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
) -> tuple[str, int, int]:
    AsmValue = AsmData(Manifest)
    if AsmValue is None:
        return ("", 0, 0)
    Parameters = ParamCatalog(Items(Manifest.get("parameters", [])))
    Definitions = Items(AsmValue.get("definitions", []))
    Documents = {
        TextAction(ItemValue.get("id")): ItemValue.get("document")
        for ItemValue in Items(AsmValue.get("documents", []))
        if isinstance(ItemValue.get("document"), Mapping)
    }
    RootDefinitionId = TextAction(AsmValue.get("root_definition_id"))
    DefinitionsById = {
        TextAction(ItemValue.get("id")): ItemValue for ItemValue in Definitions
    }
    InstancesById = {
        TextAction(ItemValue.get("id")): ItemValue
        for ItemValue in Items(
            AsmValue.get("instances", AsmValue.get("components", []))
        )
    }
    RootDefinition = DefinitionsById.get(RootDefinitionId, {})
    RootLabel = TextAction(RootDefinition.get("name"), "Assembly")
    AsmAttributes = AsmValue.get("attributes", {})
    NativeRootSource = (
        AsmAttributes.get("freecad", {}) if isinstance(AsmAttributes, Mapping) else {}
    )
    if not isinstance(NativeRootSource, Mapping):
        NativeRootSource = {}

    # this callback exists because local behavior needs one focused transformation
    GroupItems = sorted(
        (
            Group
            for Group in Items(AsmValue.get("mate_groups", AsmValue.get("groups", [])))
            if TextAction(Group.get("owner_definition_id")) == RootDefinitionId
        ),
        key=lambda ItemValue: (
            int(Number(ItemValue.get("order"))),
            TextAction(ItemValue.get("id")),
        ),
    )
    NativeJointGroup = next(
        (
            Group
            for Group in GroupItems
            if isinstance(Group.get("attributes"), Mapping)
            and isinstance(Group["attributes"].get("freecad"), Mapping)
        ),
        None,
    )
    NativeJointSource = (
        NativeJointGroup["attributes"]["freecad"]
        if NativeJointGroup is not None
        else {}
    )
    RootExtensions = Native(NativeRootSource)
    RootValue = Graph.add(
        TextAction(NativeRootSource.get("type_id"), AsmRootTypeId),
        NativeRootSource.get("name", RootLabel),
        "Assembly",
        Touched=bool(NativeRootSource.get("touched")),
        Extensions=RootExtensions or ("App::OriginGroupExtension",),
    )
    RootValue.properties.extend(NativeA(NativeRootSource))
    RootOrigin = AddOriginMut(Graph, RootValue)
    DefinitionsGroup = Graph.add(
        "App::DocumentObjectGroup", f"{RootLabel}_Definitions", "Definitions"
    )
    ComponentsGroup = Graph.add(
        "App::DocumentObjectGroup", f"{RootLabel}_Components", "Components"
    )
    EntitiesGroup = Graph.add(
        "App::DocumentObjectGroup", f"{RootLabel}_MateEntities", "MateEntities"
    )
    JointExtensions = Native(NativeJointSource)
    MatesGroup = Graph.add(
        TextAction(NativeJointSource.get("type_id"), AsmJointGroupTypeId),
        NativeJointSource.get("name", f"{RootLabel}_Joints"),
        "Joints",
        Touched=bool(NativeJointSource.get("touched")),
        Extensions=JointExtensions or ("App::GroupExtension",),
    )
    DefinitionObjects: list[str] = []
    DefinitionTargets: dict[str, str] = {}
    DefinitionOuter: dict[str, Mapping[str, AnyValue]] = {}
    for Definition in Definitions:
        DefinitionId = TextAction(Definition.get("id"))
        DefinitionName = TextAction(Definition.get("name"), DefinitionId)
        DefinitionPrefix = SafeAction(f"Definition_{DefinitionId}", "Definition")
        Imported: list[str] = []
        ImportedTarget = ""
        DocId = TextAction(Definition.get("document_id"))
        DocValue = Documents.get(DocId)
        ComponentKind = TextAction(EnumAction(Definition.get("kind"))).lower()
        Outer = OuterLinks.get(DefinitionId)
        if Outer is not None:
            DefinitionOuter[DefinitionId] = Outer
        elif isinstance(DocValue, Mapping):
            ImportedDoc = DocValue
            if ComponentKind == "assembly":
                ImportedDoc = dict(DocValue)
                ImportedDoc["assembly"] = None
            ImportedTarget, Imported = ImportCompMut(
                Graph, ImportedDoc, DefinitionPrefix, PayloadEntries, TrustedNativeBreps
            )
            if ImportedTarget:
                TargetObject = next(
                    (
                        ItemValue
                        for ItemValue in Graph.Objects
                        if ItemValue.name == ImportedTarget
                    ),
                    None,
                )
                if TargetObject is not None:
                    ReplaceNameMut(
                        TargetObject.properties,
                        "Visibility",
                        BoolProp("Visibility", False),
                    )
        Vertices: list[tuple[float, float, float]] = []
        Triangles: list[tuple[int, int, int]] = []
        for MeshSource in (
            [] if Outer is not None else DefinitionMesh(Manifest, Definition)
        ):
            MeshVertices, MeshTriangles = Tessellation(MeshSource)
            Offset = len(Vertices)
            Vertices.extend(MeshVertices)
            Triangles.extend(
                (
                    tuple((Index + Offset for Index in Triangle))
                    for Triangle in MeshTriangles
                )
            )
        MeshName = ""
        if Vertices and Triangles:
            MeshValue = Graph.add(
                "Mesh::Feature", f"{DefinitionName}_Mesh", "ComponentMesh"
            )
            FileName = UniquePayload(PayloadEntries, f"{MeshValue.name}.MeshKernel.bms")
            PayloadEntries[FileName] = MeshKernelData(Vertices, Triangles)
            MeshValue.properties.extend(
                [
                    StringProp("Label", f"{DefinitionName} geometry"),
                    MeshProp(FileName),
                    MakePlacement("Placement", MatrixTransform(KIdentityMatrix)),
                    StringProp("DefinitionId", DefinitionId, Dynamic=True),
                    BoolProp("Visibility", False),
                ]
            )
            MeshName = MeshValue.name
        DefinitionObject = Graph.add(
            "App::DocumentObjectGroup",
            f"{DefinitionName}_Definition",
            "ComponentDefinition",
        )
        Children = [*Imported, *([MeshName] if MeshName else [])]
        DefinitionObject.properties.extend(
            [
                StringProp("Label", DefinitionName),
                LinkListProp("Group", Children),
                StringProp("DefinitionId", DefinitionId, Dynamic=True),
                StringProp(
                    "ComponentKind",
                    TextAction(EnumAction(Definition.get("kind"))),
                    Dynamic=True,
                ),
                StringProp("DocumentId", DocId, Dynamic=True),
                StringProp(
                    "ConfigurationName",
                    Definition.get("configuration_name", ""),
                    Dynamic=True,
                ),
                StringProp(
                    "ConfigurationId",
                    Definition.get("configuration_id", ""),
                    Dynamic=True,
                ),
                StringProp(
                    "SourcePath", Definition.get("source_path", ""), Dynamic=True
                ),
                StringProp(
                    "SourceFormat", Definition.get("source_format_id", ""), Dynamic=True
                ),
                StringProp(
                    "SourceSHA256", Definition.get("source_sha256", ""), Dynamic=True
                ),
                JsonProp("DefinitionDataJSON", Without(Definition)),
                BoolProp("Visibility", False),
            ]
        )
        DefinitionObject.dependencies.extend(Children)
        DefinitionObjects.append(DefinitionObject.name)
        DefinitionTargets[DefinitionId] = (
            MeshName or ImportedTarget or DefinitionObject.name
        )

    # this callback exists because local behavior needs one focused transformation
    DirectInstances = sorted(
        (
            Instance
            for Instance in Items(
                AsmValue.get("instances", AsmValue.get("components", []))
            )
            if TextAction(Instance.get("owner_definition_id")) == RootDefinitionId
        ),
        key=lambda ItemValue: (
            int(Number(ItemValue.get("order"))),
            TextAction(ItemValue.get("id")),
        ),
    )
    ItemObjects: list[str] = []
    ItemByPath: dict[tuple[str, ...], str] = {}
    ItemByNativeName: dict[str, str] = {}
    ProxyChainByPath: dict[tuple[str, ...], tuple[str, ...]] = {}
    AsmLinkRecords: list[tuple[tuple[str, ...], Object, Mapping[str, AnyValue]]] = []
    RigidSubassemblyIds: set[str] = set()
    GroundedObjects: list[str] = []
    for Instance in DirectInstances:
        InstanceId = TextAction(Instance.get("id"))
        PathValue = (InstanceId,)
        DefinitionId = TextAction(Instance.get("definition_id"))
        Target = DefinitionTargets.get(DefinitionId)
        Outer = DefinitionOuter.get(DefinitionId)
        if not Target and Outer is None:
            continue
        Label = TextAction(Instance.get("name"), InstanceId)
        InstanceAttributes = Instance.get("attributes", {})
        NativeInstance = (
            InstanceAttributes.get("freecad", {})
            if isinstance(InstanceAttributes, Mapping)
            else {}
        )
        NativeInstanceProperties = NativeInstance.get("properties", {})
        NativeLinkFields = (
            {
                TextAction(NameValue)
                for NameValue in NativeInstanceProperties
                if TextAction(NameValue)
            }
            if isinstance(NativeInstanceProperties, Mapping)
            else set()
        )
        NativeLinkProp = FindLinkProp(NativeInstance)
        HasNativeLink = bool(NativeLinkProp)
        ComponentKind = TextAction(
            EnumAction(DefinitionsById.get(DefinitionId, {}).get("kind"))
        ).lower()
        IsAsmLink = Outer is not None and (
            {"Group", "Rigid"}.issubset(NativeLinkFields)
            or (not HasNativeLink and ComponentKind == "assembly")
        )
        ComponentTypeId = (
            TextAction(NativeInstance.get("type_id"))
            if HasNativeLink and TextAction(NativeInstance.get("type_id"))
            else AsmLinkTypeId if IsAsmLink else AppLinkTypeId
        )
        PlacementMatrix = MatrixValues(Instance.get("transform", {}))
        Component = Graph.add(
            ComponentTypeId,
            f"{Label}_{'_'.join(PathValue)}",
            "Component",
            Touched=IsAsmLink,
            Extensions=Native(NativeInstance)
            or (
                ("App::OriginGroupExtension",) if IsAsmLink else ("App::LinkExtension",)
            ),
        )
        Component.properties.extend(NativeA(NativeInstance))
        if IsAsmLink:
            AddOriginMut(Graph, Component)
        if ComponentKind == "assembly" and (not bool(Instance.get("flexible"))):
            RigidSubassemblyIds.add(InstanceId)
        Suppressed = bool(Instance.get("suppressed"))
        Hidden = bool(Instance.get("hidden")) or Suppressed
        Fixed = bool(Instance.get("fixed")) and (not Suppressed)
        LinkedObject = (
            XlinkProp(
                NativeLinkProp or "LinkedObject",
                TextAction(Outer.get("target")),
                FileValue=TextAction(Outer.get("file")),
                Stamp=TextAction(Outer.get("stamp")),
                Status=None if IsAsmLink else "256",
            )
            if Outer is not None
            else XlinkProp(NativeLinkProp or "LinkedObject", Target)
        )
        Placement = MakePlacement(
            "Placement",
            MatrixTransform(PlacementMatrix),
            Status=(
                "8388612"
                if IsAsmLink and Fixed
                else "8388608" if IsAsmLink else "268" if Fixed else "264"
            ),
        )
        NativeLinkProperties = (
            [
                BoolProp("Rigid", not bool(Instance.get("flexible"))),
                LinkListProp("Group", []),
                StringProp("Type", ""),
            ]
            if IsAsmLink
            else [
                MakePlacement(
                    "LinkPlacement",
                    MatrixTransform(PlacementMatrix),
                    Status="260" if Fixed else "256",
                ),
                BoolProp("LinkTransform", True),
                VectorProp("ScaleVector", MatrixScale(PlacementMatrix)),
            ]
        )
        for PropElem in (
            StringProp("Label", Label),
            LinkedObject,
            Placement,
            *NativeLinkProperties,
            StringProp("InstanceId", InstanceId, Dynamic=True),
            StringProp("DefinitionId", DefinitionId, Dynamic=True),
            StringProp(
                "OwnerDefinitionId",
                Instance.get("owner_definition_id", ""),
                Dynamic=True,
            ),
            StringListProp("InstancePath", list(PathValue), Dynamic=True),
            StringProp(
                "ReferenceNumber", Instance.get("reference_number", ""), Dynamic=True
            ),
            StringProp(
                "ConfigurationName",
                Instance.get("configuration_name", ""),
                Dynamic=True,
            ),
            StringProp(
                "ConfigurationId", Instance.get("configuration_id", ""), Dynamic=True
            ),
            BoolProp("Suppressed", Suppressed, Dynamic=True),
            BoolProp("Hidden", bool(Instance.get("hidden")), Dynamic=True),
            BoolProp("Flexible", bool(Instance.get("flexible")), Dynamic=True),
            BoolProp(
                "ExcludeFromBOM", bool(Instance.get("exclude_from_bom")), Dynamic=True
            ),
            JsonProp("InstanceDataJSON", Instance),
            BoolProp("Visibility", not Hidden),
        ):
            ReplaceNameMut(Component.properties, PropElem.get("name", ""), PropElem)
        if Outer is None and Target:
            Component.dependencies.append(Target)
        ItemObjects.append(Component.name)
        ItemByPath[PathValue] = Component.name
        NativeInstanceName = TextAction(NativeInstance.get("name"))
        if NativeInstanceName:
            ItemByNativeName[NativeInstanceName] = Component.name
        if IsAsmLink and Outer is not None:
            AsmLinkRecords.append((PathValue, Component, Outer))
        if Fixed:
            GroundedSource = (
                InstanceAttributes.get("grounded_joint", {})
                if isinstance(InstanceAttributes, Mapping)
                else {}
            )
            Grounded = GroundJointMut(
                Graph, Component.name, Label, PlacementMatrix, GroundedSource
            )
            GroundedObjects.append(Grounded.name)

    # this definition exists because focused behavior needs one stable owner
    def AddOuterMut(
        RootPath: tuple[str, ...],
        Parent: _Object,
        Outer: Mapping[str, Any],
        Records: Any,
        ParentSourcePath: tuple[str, ...] = (),
        ParentChain: tuple[str, ...] = (),
    ) -> list[str]:
        Children: list[str] = []
        for Record in Items(Records):
            Target = TextAction(Record.get("target"))
            TypeId = TextAction(Record.get("type_id"))
            InstanceId = TextAction(Record.get("instance_id"))
            if not Target or not InstanceId or (not TypeId):
                continue
            SourcePath = tuple(
                (
                    TextAction(Value)
                    for Value in Sequence(Record.get("instance_path", []))
                    if TextAction(Value)
                )
            )
            if not SourcePath:
                SourcePath = (*ParentSourcePath, InstanceId)
            elif (
                ParentSourcePath
                and SourcePath[: len(ParentSourcePath)] != ParentSourcePath
            ):
                SourcePath = (*ParentSourcePath, *SourcePath)
            FullPath = (*RootPath, *SourcePath)
            Neutral = InstancesById.get(InstanceId, {})

            # this definition exists because focused behavior needs one stable owner
            def Value(NameValue: str, Default: Any = "") -> AnyValue:
                if NameValue in Record:
                    return Record.get(NameValue)
                return Neutral.get(NameValue, Default)

            Label = TextAction(Value("label", Value("name", InstanceId)), InstanceId)
            PlacementMatrix = MatrixValues(Value("transform", {}))
            LinkFields = {
                TextAction(FieldName)
                for FieldName in Sequence(Record.get("link_fields", []))
                if TextAction(FieldName)
            }
            IsAsmLink = {"Group", "Rigid"}.issubset(LinkFields)
            Proxy = Graph.add(
                TypeId,
                f"{Parent.name}_{Target}",
                "Component",
                Touched=IsAsmLink,
                Extensions=(
                    ("App::OriginGroupExtension",)
                    if IsAsmLink
                    else ("App::LinkExtension",)
                ),
            )
            if IsAsmLink:
                AddOriginMut(Graph, Proxy)
            LinkedObject = XlinkProp(
                "LinkedObject",
                Target,
                FileValue=TextAction(Outer.get("file")),
                Stamp=TextAction(Outer.get("stamp")),
                Status=None if IsAsmLink else "256",
            )
            NativeLinkProperties = (
                [
                    BoolProp(
                        "Rigid", bool(Value("rigid", not bool(Value("flexible"))))
                    ),
                    LinkListProp("Group", []),
                    StringProp("Type", ""),
                ]
                if IsAsmLink
                else [
                    MakePlacement(
                        "LinkPlacement", MatrixTransform(PlacementMatrix), Status="256"
                    ),
                    BoolProp("LinkTransform", True),
                    VectorProp(
                        "ScaleVector",
                        Vector(
                            Value("scale", MatrixScale(PlacementMatrix)),
                            MatrixScale(PlacementMatrix),
                        ),
                    ),
                ]
            )
            InstanceData = Value("instance_data", Neutral)
            Proxy.properties.extend(
                [
                    StringProp("Label", Label),
                    LinkedObject,
                    MakePlacement(
                        "Placement",
                        MatrixTransform(PlacementMatrix),
                        Status="8388608" if IsAsmLink else "264",
                    ),
                    *NativeLinkProperties,
                    StringProp("InstanceId", InstanceId, Dynamic=True),
                    StringProp("DefinitionId", Value("definition_id"), Dynamic=True),
                    StringProp(
                        "OwnerDefinitionId", Value("owner_definition_id"), Dynamic=True
                    ),
                    StringListProp("InstancePath", list(FullPath), Dynamic=True),
                    StringProp(
                        "ReferenceNumber", Value("reference_number"), Dynamic=True
                    ),
                    StringProp(
                        "ConfigurationName", Value("configuration_name"), Dynamic=True
                    ),
                    StringProp(
                        "ConfigurationId", Value("configuration_id"), Dynamic=True
                    ),
                    BoolProp("Suppressed", bool(Value("suppressed")), Dynamic=True),
                    BoolProp("Hidden", bool(Value("hidden")), Dynamic=True),
                    BoolProp("Fixed", bool(Value("fixed")), Dynamic=True),
                    BoolProp("Flexible", bool(Value("flexible")), Dynamic=True),
                    BoolProp(
                        "ExcludeFromBOM", bool(Value("exclude_from_bom")), Dynamic=True
                    ),
                    JsonProp("InstanceDataJSON", InstanceData),
                    BoolProp(
                        "Visibility",
                        bool(
                            Value(
                                "visibility",
                                not bool(Value("hidden"))
                                and (not bool(Value("suppressed"))),
                            )
                        ),
                    ),
                ]
            )
            Children.append(Proxy.name)
            ItemByPath[FullPath] = Proxy.name
            Chain = (*ParentChain, Proxy.name)
            ProxyChainByPath[FullPath] = Chain
            if IsAsmLink:
                AddOuterMut(
                    RootPath,
                    Proxy,
                    Outer,
                    Record.get("occurrences", []),
                    SourcePath,
                    Chain,
                )
        ReplaceNameMut(Parent.properties, "Group", LinkListProp("Group", Children))
        Parent.dependencies.extend(Children)
        return Children

    for RootPath, Component, Outer in AsmLinkRecords:
        AddOuterMut(RootPath, Component, Outer, Outer.get("occurrences", []))
    EntityItems = [
        Entity
        for Entity in Items(AsmValue.get("mate_entities", AsmValue.get("entities", [])))
        if TextAction(Entity.get("owner_definition_id")) == RootDefinitionId
    ]
    EntityObjects: list[str] = []
    EntityNames: dict[str, str] = {}
    EntityComponents: dict[str, str] = {}
    EntityPrefixes: dict[str, str] = {}

    # this definition exists because focused behavior needs one stable owner
    def ComponentFor(PathValue: tuple[str, ...]) -> str:
        if not PathValue:
            return RootOrigin
        Direct = ItemByPath.get((PathValue[0],), "")
        if len(PathValue) == 1 or PathValue[0] in RigidSubassemblyIds:
            return Direct
        return ""

    # this definition exists because focused behavior needs one stable owner
    def PrefixForPath(PathValue: tuple[str, ...]) -> str:
        if len(PathValue) <= 1 or PathValue[0] not in RigidSubassemblyIds:
            return ""
        for Length in range(len(PathValue), 1, -1):
            Chain = ProxyChainByPath.get(PathValue[:Length])
            if Chain:
                return ".".join(Chain)
        return ""

    for Entity in EntityItems:
        EntityId = TextAction(Entity.get("id"))
        OwnerId = TextAction(Entity.get("owner_definition_id"))
        PathValue = tuple(
            (TextAction(Value) for Value in Sequence(Entity.get("instance_path", [])))
        )
        ComponentName = ComponentFor(PathValue)
        ComponentPrefix = PrefixForPath(PathValue)
        ObjValue = Graph.add("App::FeaturePython", EntityId, "MateEntity")
        Properties = [
            StringProp("Label", EntityId),
            StringProp("EntityId", EntityId, Dynamic=True),
            StringProp("OwnerDefinitionId", OwnerId, Dynamic=True),
            StringListProp("OwnerOccurrencePath", [], Dynamic=True),
            StringListProp("InstancePath", list(PathValue), Dynamic=True),
            StringProp(
                "EntityKind", TextAction(EnumAction(Entity.get("kind"))), Dynamic=True
            ),
            StringProp(
                "SourceEntityId", Entity.get("source_entity_id", ""), Dynamic=True
            ),
            StringProp("SelectionId", Entity.get("selection_id", ""), Dynamic=True),
            JsonProp("EntityDataJSON", Entity),
            BoolProp("Visibility", False),
        ]
        Frame = Entity.get("frame")
        if isinstance(Frame, Mapping):
            Properties.append(
                MakePlacement(
                    "ConnectorFrame", MatrixTransform(MatrixValues(Frame)), Dynamic=True
                )
            )
        if Entity.get("radius") is not None:
            Properties.append(
                FloatProp(
                    "Radius", Entity.get("radius"), "App::PropertyLength", Dynamic=True
                )
            )
        if ComponentName:
            Properties.append(StringProp("ComponentName", ComponentName, Dynamic=True))
            EntityComponents[EntityId] = ComponentName
        if ComponentPrefix:
            Properties.append(
                StringProp("ComponentSubpath", ComponentPrefix, Dynamic=True)
            )
            EntityPrefixes[EntityId] = ComponentPrefix
        ObjValue.properties.extend(Properties)
        EntityObjects.append(ObjValue.name)
        EntityNames[EntityId] = ObjValue.name

    # this callback exists because local behavior needs one focused transformation
    MateItems = sorted(
        (
            MateValue
            for MateValue in Items(
                AsmValue.get("mates", AsmValue.get("constraints", []))
            )
            if TextAction(MateValue.get("owner_definition_id")) == RootDefinitionId
        ),
        key=lambda ItemValue: (
            int(Number(ItemValue.get("order"))),
            TextAction(ItemValue.get("id")),
        ),
    )
    MateObjects: list[str] = []
    MateNames: dict[str, str] = {}
    EntityById = {
        TextAction(ItemValue.get("id")): ItemValue for ItemValue in EntityItems
    }

    # this definition exists because focused behavior needs one stable owner
    def ConnectorTarget(EntityId: str) -> str:
        Target = EntityComponents.get(EntityId, "")
        if Target:
            return Target
        return ComponentFor(
            tuple(
                (
                    TextAction(Value)
                    for Value in Sequence(
                        EntityById.get(EntityId, {}).get("instance_path", [])
                    )
                )
            )
        )

    for MateValue in MateItems:
        MateId = TextAction(MateValue.get("id"))
        MateName = TextAction(MateValue.get("name"), MateId)
        OwnerId = TextAction(MateValue.get("owner_definition_id"))
        EntityIds = [
            TextAction(Value) for Value in Sequence(MateValue.get("entity_ids", []))
        ]
        MateAttributes = MateValue.get("attributes", {})
        if not isinstance(MateAttributes, Mapping):
            MateAttributes = {}
        NativeMate = MateAttributes.get("freecad", {})
        if not isinstance(NativeMate, Mapping):
            NativeMate = {}
        NativeReferences = Items(MateAttributes.get("references", []))
        LinkedEntities = [
            EntityNames[Value] for Value in EntityIds if Value in EntityNames
        ]
        LinkedComponents = list(
            dict.fromkeys(
                (
                    EntityComponents[Value]
                    for Value in EntityIds
                    if Value in EntityComponents
                )
            )
        )
        RefEntityIds: list[list[str]] = [[], []]
        for EntityId in EntityIds:
            Entity = EntityById.get(EntityId, {})
            Attributes = Entity.get("attributes", {})
            PropName = (
                TextAction(Attributes.get("reference_property"))
                if isinstance(Attributes, Mapping)
                else ""
            )
            RefIndex = JointRefIndexByProp.get(PropName)
            if RefIndex is not None:
                RefEntityIds[RefIndex].append(EntityId)
        if not any(RefEntityIds):
            for Index, EntityId in enumerate(EntityIds[:2]):
                RefEntityIds[Index].append(EntityId)
        ConnectorTargets: list[str] = []
        ConnectorSubelements: list[list[str]] = []
        NativeRootName = TextAction(NativeRootSource.get("name"))
        for Index, GroupedIds in enumerate(RefEntityIds):
            NativeRef = NativeReferences[Index] if Index < len(NativeReferences) else {}
            if NativeRef:
                SourceTarget = TextAction(NativeRef.get("name"))
                Target = (
                    RootValue.name
                    if SourceTarget == NativeRootName
                    else ItemByNativeName.get(SourceTarget, SourceTarget)
                )
                Subelements = []
                for Value in Sequence(NativeRef.get("subelements", [])):
                    SourceValue = TextAction(Value)
                    Prefix, Separator, Suffix = SourceValue.partition(".")
                    Mapped = ItemByNativeName.get(Prefix, Prefix)
                    Subelements.append(f"{Mapped}.{Suffix}" if Separator else Mapped)
            else:
                Target = ConnectorTarget(GroupedIds[0]) if GroupedIds else ""
                Subelements = []
                for EntityId in GroupedIds:
                    Entity = EntityById.get(EntityId, {})
                    Values = MateSubelements(Entity)
                    if len(GroupedIds) == 1:
                        Subelements.extend(Values)
                    elif Values:
                        Subelements.append(Values[0])
            ConnectorTargets.append(Target)
            ConnectorSubelements.append(Subelements)
        HasConnectorPair = len(ConnectorTargets) == 2 and all(ConnectorTargets)
        ResolvedJointType = MateJointType(MateValue.get("kind"))
        NativeJointSupported = ResolvedJointType is not None and HasConnectorPair
        NativeMateExtensions = Native(NativeMate)
        ObjValue = Graph.add(
            TextAction(NativeMate.get("type_id"), "App::FeaturePython"),
            NativeMate.get("name", MateName),
            "Mate",
            Touched=bool(NativeMate.get("touched")),
            Extensions=NativeMateExtensions
            or (("App::SuppressibleExtensionPython",) if NativeJointSupported else ()),
        )
        ConnectorProperties: list[XmlTree.Element] = []
        for Index in range(1, 3):
            GroupedIds = RefEntityIds[Index - 1]
            EntityId = GroupedIds[0] if GroupedIds else ""
            ComponentName = (
                ConnectorTargets[Index - 1] if Index <= len(ConnectorTargets) else ""
            )
            Entity = EntityById.get(EntityId, {})
            Subelements = ConnectorSubelements[Index - 1]
            HasRealSubelements = bool(Subelements)
            ComponentPrefix = EntityPrefixes.get(EntityId, "")
            if ComponentPrefix:
                Subelements = [
                    f"{ComponentPrefix}.{Value}" if Value else f"{ComponentPrefix}."
                    for Value in Subelements or ["", ""]
                ]
            elif ComponentName and (not Subelements):
                Subelements = ["", ""]
            ConnectorProperties.append(
                XlinkSubProp(
                    f"Reference{Index}", ComponentName, Subelements, Dynamic=True
                )
            )
            Frame = Entity.get("frame")
            Matrix = (
                MatrixValues(Frame) if isinstance(Frame, Mapping) else KIdentityMatrix
            )
            ConnectorProperties.extend(
                [
                    MakePlacement(
                        f"Placement{Index}", MatrixTransform(Matrix), Dynamic=True
                    ),
                    MakePlacement(
                        f"Offset{Index}", MatrixTransform(KIdentityMatrix), Dynamic=True
                    ),
                    BoolProp(
                        f"Detach{Index}",
                        isinstance(Frame, Mapping) and (not HasRealSubelements),
                        Dynamic=True,
                    ),
                ]
            )
        MetaProperties = [
            StringProp("MateId", MateId, Dynamic=True),
            StringListProp("OwnerOccurrencePath", [], Dynamic=True),
            StringProp(
                "MateType", TextAction(EnumAction(MateValue.get("kind"))), Dynamic=True
            ),
            StringProp("OwnerDefinitionId", OwnerId, Dynamic=True),
            StringListProp("EntityLinks", LinkedEntities, Dynamic=True),
            StringListProp("ComponentLinks", LinkedComponents, Dynamic=True),
            StringListProp("EntityIds", EntityIds, Dynamic=True),
            StringListProp(
                "ParameterIds",
                [
                    TextAction(Value)
                    for Value in Sequence(MateValue.get("parameter_ids", []))
                ],
                Dynamic=True,
            ),
            StringProp(
                "Alignment",
                TextAction(EnumAction(MateValue.get("alignment"))),
                Dynamic=True,
            ),
            BoolProp(
                "SourceSuppressed", bool(MateValue.get("suppressed")), Dynamic=True
            ),
            BoolProp("Driving", bool(MateValue.get("driving", True)), Dynamic=True),
            JsonProp("MateValueJSON", MateValue.get("value")),
            JsonProp("MateDataJSON", MateValue),
        ]
        if not NativeJointSupported:
            ObjValue.properties.extend(NativeA(NativeMate))
            for PropElem in (
                StringProp("Label", MateName),
                BoolProp("KitMateCarrier", True, Dynamic=True),
                StringProp(
                    "NativeExecutionReason",
                    (
                        "unsupported_mate_kind"
                        if ResolvedJointType is None
                        else "missing_connector_pair"
                    ),
                    Dynamic=True,
                ),
                *MetaProperties,
                *ConnectorProperties,
                BoolProp("Visibility", False),
            ):
                ReplaceNameMut(ObjValue.properties, PropElem.get("name", ""), PropElem)
            ObjValue.dependencies.extend(ConnectorTargets)
            MateObjects.append(ObjValue.name)
            MateNames[MateId] = ObjValue.name
            continue
        JointType = ResolvedJointType
        NumericValue = MateScalar(MateValue.get("value"))
        ParamValues = {
            PathValue: Parameters.value(ParamId)
            for ParamId in (
                TextAction(Value)
                for Value in Sequence(MateValue.get("parameter_ids", []))
            )
            if (PathValue := Parameters.source_path(ParamId))
        }
        AngleValue = ParamValues.get(
            "Angle", NumericValue if JointType == "Angle" else 0.0
        )
        DistanceValue = ParamValues.get(
            "Distance", NumericValue if JointType in JointTypesUsingDistance else 0.0
        )
        NativeMateProperties = NativeMate.get("properties", {})
        if isinstance(NativeMateProperties, Mapping) and NativeMateProperties:
            Properties = [
                ElemValue
                for Value in NativeMateProperties.values()
                if (ElemValue := ElemFromData(Value)) is not None
                and ElemValue.tag == "Property"
            ]
            Replacements = [
                StringProp("Label", MateName),
                EnumerationProp("JointType", JointTypes, JointTypes.index(JointType)),
                BoolProp(
                    "Suppressed",
                    bool(MateValue.get("suppressed"))
                    or not HasConnectorPair
                    or (not NativeJointSupported),
                ),
                FloatProp("Angle", AngleValue, "App::PropertyAngle"),
                FloatProp("Distance", DistanceValue, "App::PropertyLength"),
                *[
                    ItemValue
                    for ItemValue in ConnectorProperties
                    if ItemValue.get("name", "").startswith(AsmConnectorPropPrefixes)
                ],
            ]
            for PropName, PropType in (
                ("Distance2", "App::PropertyLength"),
                ("LengthMin", "App::PropertyLength"),
                ("LengthMax", "App::PropertyLength"),
                ("AngleMin", "App::PropertyAngle"),
                ("AngleMax", "App::PropertyAngle"),
            ):
                if PropName in ParamValues:
                    Replacements.append(
                        FloatProp(PropName, ParamValues[PropName], PropType)
                    )
            for Replacement in Replacements:
                MergeNamedMut(Properties, Replacement)
            Properties.extend(MetaProperties)
        else:
            Properties = [
                StringProp("Label", MateName),
                *MetaProperties,
                EnumerationProp(
                    "JointType", JointTypes, JointTypes.index(JointType), Dynamic=True
                ),
                BoolProp(
                    "Suppressed",
                    bool(MateValue.get("suppressed"))
                    or not HasConnectorPair
                    or (not NativeJointSupported),
                ),
                FloatProp("Angle", AngleValue, "App::PropertyAngle", Dynamic=True),
                FloatProp(
                    "Distance", DistanceValue, "App::PropertyLength", Dynamic=True
                ),
                FloatProp(
                    "Distance2",
                    (
                        ParamValues.get("Distance2", 0.0)
                        if JointType in JointTypesUsingSecond
                        else 0.0
                    ),
                    "App::PropertyLength",
                    Dynamic=True,
                ),
                FloatProp(
                    "LengthMin",
                    ParamValues.get("LengthMin", 0.0),
                    "App::PropertyLength",
                    Dynamic=True,
                ),
                FloatProp(
                    "LengthMax",
                    ParamValues.get("LengthMax", 0.0),
                    "App::PropertyLength",
                    Dynamic=True,
                ),
                FloatProp(
                    "AngleMin",
                    ParamValues.get("AngleMin", 0.0),
                    "App::PropertyAngle",
                    Dynamic=True,
                ),
                FloatProp(
                    "AngleMax",
                    ParamValues.get("AngleMax", 0.0),
                    "App::PropertyAngle",
                    Dynamic=True,
                ),
                BoolProp("EnableLengthMin", "LengthMin" in ParamValues, Dynamic=True),
                BoolProp("EnableLengthMax", "LengthMax" in ParamValues, Dynamic=True),
                BoolProp("EnableAngleMin", "AngleMin" in ParamValues, Dynamic=True),
                BoolProp("EnableAngleMax", "AngleMax" in ParamValues, Dynamic=True),
                *ConnectorProperties,
                PythonProxyProp("JointObject", "Joint"),
                BoolProp("Visibility", False),
            ]
        ObjValue.properties.extend(Properties)
        ObjValue.dependencies.extend(ConnectorTargets)
        MateObjects.append(ObjValue.name)
        MateNames[MateId] = ObjValue.name
    GroupItems = [Group for Group in GroupItems if Group is not NativeJointGroup]
    GroupNames: dict[str, str] = {}
    GroupObjects: list[Object] = []
    for Group in GroupItems:
        GroupId = TextAction(Group.get("id"))
        ObjValue = Graph.add(
            "App::DocumentObjectGroup", Group.get("name", GroupId), "MateGroup"
        )
        GroupNames[GroupId] = ObjValue.name
        GroupObjects.append(ObjValue)
    for Group, ObjValue in zip(GroupItems, GroupObjects):
        Members = [
            MateNames[Value]
            for Value in (
                TextAction(ItemValue)
                for ItemValue in Sequence(Group.get("mate_ids", []))
            )
            if Value in MateNames
        ]
        Nested = [
            NameValue
            for GroupId, NameValue in GroupNames.items()
            if TextAction(
                next(
                    (
                        ItemValue.get("parent_group_id")
                        for ItemValue in GroupItems
                        if TextAction(ItemValue.get("id")) == GroupId
                    ),
                    "",
                )
            )
            == TextAction(Group.get("id"))
        ]
        Children = Nested
        ObjValue.properties.extend(
            [
                StringProp("Label", Group.get("name", Group.get("id", ""))),
                LinkListProp("Group", Children),
                StringListProp("MateObjects", Members, Dynamic=True),
                StringProp("MateGroupId", Group.get("id", ""), Dynamic=True),
                BoolProp("Visibility", False),
            ]
        )
        ObjValue.dependencies.extend(Children)
    DefinitionsGroup.properties.extend(
        [
            StringProp("Label", "Component Definitions"),
            LinkListProp("Group", DefinitionObjects),
            BoolProp("Visibility", False),
        ]
    )
    DefinitionsGroup.dependencies.extend(DefinitionObjects)
    ComponentsGroup.properties.extend(
        [
            StringProp("Label", "Components"),
            LinkListProp("Group", []),
            StringListProp("ComponentObjects", ItemObjects, Dynamic=True),
            BoolProp("Visibility", True),
        ]
    )
    EntitiesGroup.properties.extend(
        [
            StringProp("Label", "Mate Entities"),
            LinkListProp("Group", EntityObjects),
            BoolProp("Visibility", False),
        ]
    )
    EntitiesGroup.dependencies.extend(EntityObjects)
    MateChildren = [*GroundedObjects, *MateObjects]
    MatesGroup.properties.extend(NativeA(NativeJointSource))
    GroupProp = next(
        (
            ItemValue
            for ItemValue in MatesGroup.properties
            if ItemValue.get("name") == "Group"
        ),
        None,
    )
    if GroupProp is None:
        GroupProp = LinkListProp("Group", MateChildren)
        MatesGroup.properties.append(GroupProp)
    else:
        LinkList = GroupProp.find("./LinkList")
        if LinkList is None:
            LinkList = XmlTree.SubElement(GroupProp, "LinkList")
        LinkList.clear()
        LinkList.set("count", str(len(MateChildren)))
        for Target in MateChildren:
            XmlTree.SubElement(LinkList, "Link", {"value": Target})
    if not any(
        (
            ItemValue.get("name") == "ExpressionEngine"
            for ItemValue in MatesGroup.properties
        )
    ):
        MatesGroup.properties.insert(0, ExpressionProp([]))
    if not any(
        (ItemValue.get("name") == "Label" for ItemValue in MatesGroup.properties)
    ):
        LabelProp = PropAction("Label", "App::PropertyString", Status="134217728")
        XmlTree.SubElement(LabelProp, "String", {"value": "Joints"})
        MatesGroup.properties.append(LabelProp)
    if not any(
        (ItemValue.get("name") == "Label2" for ItemValue in MatesGroup.properties)
    ):
        LabelTwoProp = PropAction("Label2", "App::PropertyString", Status="67108992")
        XmlTree.SubElement(LabelTwoProp, "String", {"value": ""})
        MatesGroup.properties.append(LabelTwoProp)
    if not any(
        (ItemValue.get("name") == "Visibility" for ItemValue in MatesGroup.properties)
    ):
        VisibilityProp = PropAction("Visibility", "App::PropertyBool", Status="648")
        XmlTree.SubElement(VisibilityProp, "Bool", {"value": "true"})
        MatesGroup.properties.append(VisibilityProp)
    MatesGroup.transient_properties.append(
        XmlTree.Element(
            "_Property",
            {
                "name": "_GroupTouched",
                "type": "App::PropertyBool",
                "status": "100663424",
            },
        )
    )
    MatesGroup.dependencies.extend(MateChildren)
    RootChildren = [MatesGroup.name, *ItemObjects, *GroundedObjects, *MateObjects]
    for PropElem in (
        StringProp("Label", RootLabel),
        StringProp("Type", "Assembly"),
        LinkListProp("Group", RootChildren),
        MakePlacement("Placement", MatrixTransform(KIdentityMatrix)),
        StringProp("RootDefinitionId", RootDefinitionId, Dynamic=True),
        IntegerProp("DefinitionCount", len(Definitions), Dynamic=True),
        IntegerProp("OccurrenceCount", len(DirectInstances), Dynamic=True),
        IntegerProp("MateCount", len(MateObjects), Dynamic=True),
        BoolProp("Visibility", True),
    ):
        ReplaceNameMut(RootValue.properties, PropElem.get("name", ""), PropElem)
    RootValue.dependencies.extend(RootChildren)
    return (RootValue.name, len(DirectInstances), len(MateObjects))


# this definition exists because focused behavior needs one stable owner
def AddMeshesMut(
    Graph: _Graph,
    Manifest: Mapping[str, Any],
    PayloadEntries: dict[str, bytes],
    ParametricTarget: str,
) -> list[str]:
    if AsmData(Manifest) is not None:
        return []
    Result: list[str] = []
    for Index, MeshSource in enumerate(Items(Manifest.get("meshes", []))):
        Vertices, Triangles = Tessellation(MeshSource)
        if not Vertices or not Triangles:
            continue
        Requested = "DisplayMesh" if Index == 0 else f"DisplayMesh_{Index + 1}"
        BrepRequested = "BRep" if Index == 0 else f"BRep_{Index + 1}"
        BrepValue = Graph.add("Part::Feature", BrepRequested, "FacetedBRep")
        BrepFileName = UniquePayload(PayloadEntries, f"{BrepValue.name}.Shape.brp")
        PayloadEntries[BrepFileName] = TriangleMeshBrep(Vertices, Triangles)
        BrepValue.properties.extend(
            [
                StringProp(
                    "Label",
                    f"{MeshSource.get('name', MeshSource.get('id', Requested))} BRep",
                ),
                ShapeProp(BrepFileName),
                MakePlacement("Placement", MatrixTransform(KIdentityMatrix)),
                StringProp("KitMeshId", MeshSource.get("id", ""), Dynamic=True),
                StringProp("Representation", "faceted", Dynamic=True),
                BoolProp("Visibility", False),
            ]
        )
        MeshValue = Graph.add("Mesh::Feature", Requested, "DocumentMesh")
        FileName = UniquePayload(PayloadEntries, f"{MeshValue.name}.MeshKernel.bms")
        PayloadEntries[FileName] = MeshKernelData(Vertices, Triangles)
        MeshValue.properties.extend(
            [
                StringProp(
                    "Label", MeshSource.get("name", MeshSource.get("id", Requested))
                ),
                MeshProp(FileName),
                MakePlacement("Placement", MatrixTransform(KIdentityMatrix)),
                StringProp("KitMeshId", MeshSource.get("id", ""), Dynamic=True),
                LinkProp("BRep", BrepValue.name, Dynamic=True),
                BoolProp("Visibility", True),
            ]
        )
        MeshValue.dependencies.append(BrepValue.name)
        if ParametricTarget:
            BrepValue.properties.append(
                LinkProp("ParametricSource", ParametricTarget, Dynamic=True)
            )
            BrepValue.dependencies.append(ParametricTarget)
            MeshValue.properties.append(
                LinkProp("ParametricSource", ParametricTarget, Dynamic=True)
            )
            MeshValue.dependencies.append(ParametricTarget)
        Result.append(BrepValue.name)
    if Result and ParametricTarget:
        Target = next(
            (
                ItemValue
                for ItemValue in Graph.Objects
                if ItemValue.name == ParametricTarget
            ),
            None,
        )
        if Target is not None:
            ReplaceNameMut(
                Target.properties, "Visibility", BoolProp("Visibility", False)
            )
    return Result


# this definition exists because focused behavior needs one stable owner
def AddBrepMut(
    Graph: _Graph,
    Manifest: Mapping[str, Any],
    PayloadEntries: dict[str, bytes],
    ParametricTarget: str,
) -> tuple[list[str], str]:
    if Manifest.get("brep") is None:
        return ([], "")
    try:
        DocValue = CadDoc.from_dict(Manifest)
    except (KeyError, TypeError, ValueError, RecursionError) as ErrorInfo:
        raise ValueError("neutral B-rep manifest data is invalid") from ErrorInfo
    if DocValue.brep is None:
        return ([], "")
    try:
        DataValue = BrepModelBrep(DocValue.brep)
    except FreeCadBrepWriteError:
        return ([], "")
    ObjValue = Graph.add("Part::Feature", "BRep", "NeutralBRep")
    FileName = UniquePayload(PayloadEntries, f"{ObjValue.name}.Shape.brp")
    PayloadEntries[FileName] = DataValue
    ObjValue.properties.extend(
        [
            StringProp("Label", "Neutral BRep"),
            ShapeProp(FileName),
            MakePlacement("Placement", MatrixTransform(KIdentityMatrix)),
            StringProp("Representation", "neutral-brep", Dynamic=True),
            StringProp("BRepSchemaVersion", DocValue.brep.schema_version, Dynamic=True),
            BoolProp("Visibility", True),
        ]
    )
    if ParametricTarget:
        ObjValue.properties.append(
            LinkProp("ParametricSource", ParametricTarget, Dynamic=True)
        )
        ObjValue.dependencies.append(ParametricTarget)
    return ([ObjValue.name], FileName)


# this definition exists because focused behavior needs one stable owner
def DocProperties(Label: str, DocId: str, DocTimestamp: str) -> XmlTree.Element:
    Properties = XmlTree.Element("Properties", {"Count": "8", "TransientCount": "0"})
    Properties.extend(
        [
            StringProp("Label", Label),
            StringProp("Comment", "Kit by Parashell interchange document"),
            StringProp("CreatedBy", "Kit by Parashell"),
            StringProp("Id", DocId),
            StringProp("License", ""),
        ]
    )
    for NameValue in ("CreationDate", "LastModifiedDate"):
        Timestamp = PropAction(NameValue, "App::PropertyString", Status="16777217")
        XmlTree.SubElement(Timestamp, "String", {"value": DocTimestamp})
        Properties.append(Timestamp)
    UidValue = PropAction("Uid", "App::PropertyUUID", Status="16777217")
    XmlTree.SubElement(
        UidValue,
        "Uuid",
        {"value": str(UuidValue.uuid5(UuidValue.NAMESPACE_URL, DocId))},
    )
    Properties.append(UidValue)
    return Properties


# this definition exists because focused behavior needs one stable owner
def SerializeObject(Parent: ET.Element, ObjValue: _Object) -> None:
    Attributes = {"name": ObjValue.name}
    if ObjValue.extensions:
        Attributes["Extensions"] = "True"
    ElemValue = XmlTree.SubElement(Parent, "Object", Attributes)
    if ObjValue.extensions:
        Extensions = XmlTree.SubElement(
            ElemValue, "Extensions", {"Count": str(len(ObjValue.extensions))}
        )
        for Extension in ObjValue.extensions:
            XmlTree.SubElement(
                Extensions,
                "Extension",
                {"type": Extension, "name": Extension.rsplit("::", 1)[-1]},
            )
    Properties = XmlTree.SubElement(
        ElemValue,
        "Properties",
        {
            "Count": str(len(ObjValue.properties)),
            "TransientCount": str(len(ObjValue.transient_properties)),
        },
    )
    Properties.extend(ObjValue.transient_properties)
    Properties.extend(ObjValue.properties)


# this definition exists because focused behavior needs one stable owner
def SanitizePayload(
    Objects: list[_Object], PayloadEntries: Mapping[str, bytes]
) -> None:
    for ObjValue in Objects:
        for PropElem in ObjValue.properties:
            PartValue = PropElem.find("./Part")
            if PartValue is not None:
                FileName = PartValue.get("file", "")
                if FileName and FileName not in PayloadEntries:
                    PropElem[:] = [XmlTree.Element("Part")]
                    continue
            Stack = [PropElem]
            while Stack:
                Parent = Stack.pop()
                FileName = Parent.get("file", "")
                if Parent.tag != "XLink" and FileName not in PayloadEntries:
                    Parent.attrib.pop("file", None)
                for Child in list(Parent):
                    FileName = Child.get("file", "")
                    if (
                        Child.tag != "XLink"
                        and FileName
                        and (FileName not in PayloadEntries)
                    ):
                        Parent.remove(Child)
                    else:
                        Stack.append(Child)


# this definition exists because focused behavior needs one stable owner
def Represented(Manifest: Mapping[str, Any], AsmValue: Mapping[str, Any]) -> set[str]:
    Result: set[str] = set()

    # this definition exists because focused behavior needs one stable owner
    def Visit(Value: Any) -> None:
        if isinstance(Value, Mapping):
            Attributes = Value.get("attributes", {})
            if isinstance(Attributes, Mapping):
                for KeyValue in ("freecad", "grounded_joint"):
                    Native = Attributes.get(KeyValue, {})
                    if isinstance(Native, Mapping):
                        NameValue = TextAction(Native.get("name"))
                        if NameValue:
                            Result.add(NameValue)
            for Child in Value.values():
                Visit(Child)
        elif isinstance(Value, (list, tuple)):
            for Child in Value:
                Visit(Child)

    Visit(Manifest)
    Visit(AsmValue)
    return Result


# this definition exists because focused behavior needs one stable owner
def BuildDocXml(
    Manifest: Mapping[str, Any],
    ManifestData: str,
    ManifestShaTwoFiveSix: str,
    OuterLinks: Mapping[str, Mapping[str, Any]] | None = None,
    NativeOuterLinks: Mapping[str, str] | None = None,
    DocTimestamp: str = "1980-01-01T00:00:00Z",
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
) -> tuple[bytes, dict[str, bytes]]:
    OuterLinks = OuterLinks or {}
    NativeOuterLinks = NativeOuterLinks or {}
    NativeDocShaTwoFiveSix = NativeDocShaTwo(Manifest)
    SourceData = Manifest.get("source", {})
    SourceFormatId = (
        TextAction(SourceData.get("format_id"))
        if isinstance(SourceData, Mapping)
        else ""
    )
    ManifestMeta = Manifest.get("metadata", {})
    FreecadMeta = (
        ManifestMeta.get("freecad", {}) if isinstance(ManifestMeta, Mapping) else {}
    )
    NativeValues = (
        Items(FreecadMeta.get("objects", []))
        if isinstance(FreecadMeta, Mapping)
        else []
    )
    AsmValue = AsmData(Manifest)
    NativeReplay = bool(NativeValues) and AsmValue is None
    RepresentedNativeNames = (
        Represented(Manifest, AsmValue) if AsmValue is not None else set()
    )
    ReplayValues = NativeValues
    if not NativeReplay:
        ReplayValues = [
            Value
            for Value in NativeValues
            if TextAction(Value.get("name")) not in RepresentedNativeNames
        ]
        while True:
            ReplayNames = {TextAction(Value.get("name")) for Value in ReplayValues}
            ClosedValues = [
                Value
                for Value in ReplayValues
                if all(
                    (
                        TextAction(Dependency) in ReplayNames
                        for Dependency in Sequence(Value.get("dependencies", []))
                    )
                )
            ]
            if len(ClosedValues) == len(ReplayValues):
                break
            ReplayValues = ClosedValues
    Graph = ObjectGraph()
    NativeGraph: dict[str, Object] = {}
    if ReplayValues:

        # this callback exists because local behavior needs one focused transformation
        for Value in sorted(
            ReplayValues, key=lambda ItemValue: int(Number(ItemValue.get("order")))
        ):
            ObjValue = NativeObject(Value)
            if ObjValue.name in NativeGraph:
                raise ValueError(
                    f"duplicate native FreeCAD object metadata: {ObjValue.name}"
                )
            NativeGraph[ObjValue.name] = ObjValue
            Graph.Names.add(ObjValue.name)
            Graph.Objects.append(ObjValue)
    NativeObjectTargets = {
        NameValue: ObjValue.name for NameValue, ObjValue in NativeGraph.items()
    }
    ParametersData = Items(Manifest.get("parameters", []))
    Parameters = ParamCatalog(ParametersData)
    ParamSheet = Graph.add("Spreadsheet::Sheet", "Parameters", "Parameters")
    ParamSheet.properties.extend(Parameters.sheet_properties())
    MetaValue = Graph.add("App::FeaturePython", "KitMetadata", "Metadata")
    MetaValue.properties.extend(
        [
            StringProp("Label", "Kit Metadata"),
            StringProp(KManifestEncodingProp, KManifestEncoding, Dynamic=True),
            StringProp(KManifestShaTwoFiveSixPrA, ManifestShaTwoFiveSix, Dynamic=True),
            StringProp(KManifestDataProp, ManifestData, Dynamic=True),
            StringProp(
                "SchemaVersion", Manifest.get("schema_version", "1.0"), Dynamic=True
            ),
            JsonProp("ParameterAliasesJSON", Parameters.Aliases),
            BoolProp("Visibility", False),
        ]
    )
    PlanesGroup = Graph.add("App::DocumentObjectGroup", "SupportPlanes", "Group")
    SketchesGroup = Graph.add("App::DocumentObjectGroup", "Sketches", "Group")
    SelectionsGroup = Graph.add("App::DocumentObjectGroup", "Selections", "Group")
    ConfigurationsGroup = Graph.add(
        "App::DocumentObjectGroup", "Configurations", "Group"
    )
    TimelineGroup = Graph.add("App::DocumentObjectGroup", "FeatureTimeline", "Group")
    BodiesGroup = Graph.add("App::DocumentObjectGroup", "Bodies", "Group")
    PlaneItems = Items(Manifest.get("support_planes", Manifest.get("planes", [])))
    PlaneById = {TextAction(ItemValue.get("id")): ItemValue for ItemValue in PlaneItems}
    PlaneNames: dict[str, str] = {}
    PlaneObjects: list[str] = []
    for Plane in PlaneItems:
        PlaneId = TextAction(Plane.get("id"))
        PlaneAttributes = Plane.get("attributes", {})
        NativePlane = (
            PlaneAttributes.get("freecad", {})
            if isinstance(PlaneAttributes, Mapping)
            else {}
        )
        NativePlaneName = TextAction(NativePlane.get("name"))
        ObjValue = NativeGraph.get(NativePlaneName) if NativeReplay else None
        if ObjValue is None:
            ObjValue = Graph.add(
                TextAction(NativePlane.get("type_id"), "App::Plane"),
                NativePlane.get("name", Plane.get("name", PlaneId)),
                "Plane",
            )
        if NativePlaneName:
            NativeObjectTargets[NativePlaneName] = ObjValue.name
        PlaneNames[PlaneId] = ObjValue.name
        PlaneObjects.append(ObjValue.name)
        Transform = (
            Plane.get("transform", {})
            if isinstance(Plane.get("transform"), Mapping)
            else {}
        )
        Expressions: list[tuple[str, str]] = []
        OffsetParamId = TextAction(Plane.get("offset_parameter_id"))
        if OffsetParamId:
            Expression = Parameters.expression(OffsetParamId)
            Origin = Vector(Transform.get("origin"), (0.0, 0.0, 0.0))
            Normal = Normalize(Vector(Transform.get("z_axis"), (0.0, 0.0, 1.0)))
            Value = Parameters.value(OffsetParamId)
            for Coordinate, Component, OriginValue in zip(
                ("x", "y", "z"), Normal, Origin
            ):
                if abs(Component) > 0.999999 and MathValue.isclose(
                    abs(OriginValue), abs(Value), rel_tol=1e-09, abs_tol=1e-09
                ):
                    SignValue = "-" if OriginValue * Value < 0 else ""
                    Expressions.append(
                        (
                            f"Placement.Base.{Coordinate}",
                            SignValue + TextAction(Expression),
                        )
                    )
        NativePlaneProperties = (
            NativePlane.get("properties", {})
            if isinstance(NativePlane, Mapping)
            else {}
        )
        if isinstance(NativePlaneProperties, Mapping) and NativePlaneProperties:
            Properties = NativeA(NativePlane)
            Replacements = [
                StringProp("Label", Plane.get("name", PlaneId)),
                MakePlacement("Placement", Transform),
                BoolProp("Visibility", False),
            ]
            for Replacement in Replacements:
                MergeNamedMut(Properties, Replacement)
            if not NativeReplay:
                Properties.extend(
                    [
                        StringProp("KitId", PlaneId, Dynamic=True),
                        JsonProp("SourcePlaneJSON", Plane),
                    ]
                )
            ObjValue.properties = Properties
        else:
            ObjValue.properties.extend(
                [
                    StringProp("Label", Plane.get("name", PlaneId)),
                    MakePlacement("Placement", Transform),
                    ExpressionProp(Expressions),
                    StringProp("KitId", PlaneId, Dynamic=True),
                    JsonProp("SourcePlaneJSON", Plane),
                    BoolProp("Visibility", False),
                ]
            )
        if Expressions and (not NativeReplay):
            ObjValue.dependencies.append(ParamSheet.name)
    SketchItems = Items(Manifest.get("sketches", []))
    SketchNames: dict[str, str] = {}
    SketchNativeProfileCounts: dict[str, int] = {}
    SketchNativeProfileSound: dict[str, bool] = {}
    SketchObjects: list[str] = []
    for Sketch in SketchItems:
        SketchId = TextAction(Sketch.get("id"))
        SketchNativeProfileCounts[SketchId] = NativeClosed(Sketch)
        SketchNativeProfileSound[SketchId] = HasNativeProf(Sketch)
        PlaneId = TextAction(Sketch.get("support_plane_id"))
        Plane = PlaneById.get(PlaneId, {"transform": {}})
        PlaneName = PlaneNames.get(PlaneId, "")
        SketchAttributes = Sketch.get("attributes", {})
        NativeSketch = (
            SketchAttributes.get("freecad", {})
            if isinstance(SketchAttributes, Mapping)
            else {}
        )
        NativeSketchName = TextAction(NativeSketch.get("name"))
        ObjValue = NativeGraph.get(NativeSketchName) if NativeReplay else None
        if ObjValue is None:
            ObjValue = Graph.add(
                TextAction(NativeSketch.get("type_id"), SketchTypeId),
                NativeSketch.get("name", Sketch.get("name", SketchId)),
                "Sketch",
                Touched=True,
                Extensions=("Part::AttachExtension",),
            )
        SketchNames[SketchId] = ObjValue.name
        if NativeSketchName:
            NativeObjectTargets[NativeSketchName] = ObjValue.name
        SketchObjects.append(ObjValue.name)
        Properties, Dependencies = BuildSketch(
            Sketch,
            Plane,
            PlaneName,
            Parameters,
            NativeReplay,
            SourceFormatId == "solidworks.sldprt",
        )
        if NativeReplay and NativeSketch:
            ObjValue.properties = Properties
        else:
            ObjValue.properties.extend(Properties)
        if NativeSketch and (not NativeReplay):
            ObjValue.transient_properties.append(
                XmlTree.Element(
                    "_Property",
                    {
                        "name": "_ElementMapVersion",
                        "type": "App::PropertyString",
                        "status": "234881024",
                    },
                )
            )
        ObjValue.dependencies.extend(
            (Dependency for Dependency in Dependencies if Dependency)
        )
    SelectionItems = {
        TextAction(ItemValue.get("id")): ItemValue
        for ItemValue in Items(Manifest.get("selections", []))
    }

    # this callback exists because local behavior needs one focused transformation
    FeatureItems = sorted(
        Items(Manifest.get("feature_timeline", Manifest.get("timeline", []))),
        key=lambda ItemValue: int(Number(ItemValue.get("order"))),
    )
    FeatureNames: dict[str, str] = {}
    SolidFeatureNames: dict[str, str] = {}
    FeatureObjects: list[str] = []
    CurrentName = ""
    FinalShapeFileName = ""
    PayloadEntries: dict[str, bytes] = {}
    ReplayEntryNames: set[str] | None = None
    if not NativeReplay:
        ReplayEntryNames = {
            FileName
            for Value in ReplayValues
            for PropElem in NativeA(Value)
            for NodeValue in PropElem.iter()
            if NodeValue.tag != "XLink" and (FileName := NodeValue.get("file", ""))
        }
    if NativeValues and isinstance(FreecadMeta, Mapping):
        for ItemValue in Items(FreecadMeta.get("entries", [])):
            SourceStream = TextAction(ItemValue.get("source_stream"))
            DataValue = PayloadBytes(ItemValue)
            if not SourceStream or DataValue is None:
                raise ValueError("native FreeCAD entry metadata is incomplete")
            if ReplayEntryNames is not None and SourceStream not in ReplayEntryNames:
                continue
            Entry = ValidatedEntry(SourceStream)
            if Entry in {KDocEntry, KManifestEntry} or Entry in PayloadEntries:
                raise ValueError(
                    "native FreeCAD entry metadata conflicts with the archive"
                )
            PayloadEntries[Entry] = DataValue
    for Feature in FeatureItems:
        FeatureId = TextAction(Feature.get("id"))
        FeatureName = TextAction(Feature.get("name"), FeatureId)
        KindValue = TextAction(EnumAction(Feature.get("kind"))).lower()
        Operation = TextAction(EnumAction(Feature.get("operation"))).lower()
        Attributes = (
            Feature.get("attributes", {})
            if isinstance(Feature.get("attributes"), Mapping)
            else {}
        )
        Definition = (
            Feature.get("definition", {})
            if isinstance(Feature.get("definition"), Mapping)
            else {}
        )
        NativeDefinitionData = (
            Definition.get("object_data", {})
            if TextAction(Definition.get("$type")) == "NativeFeatureDefinition"
            and TextAction(Definition.get("format_id")) == FormatId
            and isinstance(Definition.get("object_data"), Mapping)
            else {}
        )
        Inputs = [
            TextAction(Value)
            for Value in Sequence(Feature.get("input_feature_ids", []))
        ]
        InputBaseName = next(
            (
                SolidFeatureNames[Value]
                for Value in reversed(Inputs)
                if Value in SolidFeatureNames
            ),
            "",
        )
        BaseName = InputBaseName or CurrentName
        FeatureSketchName = SketchNames.get(TextAction(Feature.get("sketch_id")), "")
        NativeFeature = Attributes.get("freecad", {})
        NativeFeatureName = (
            TextAction(NativeFeature.get("name"))
            if isinstance(NativeFeature, Mapping)
            else ""
        )
        if NativeReplay and NativeFeatureName in NativeGraph:
            Final = NativeGraph[NativeFeatureName]
            NativePropSource = (
                NativeDefinitionData or NativeFeature
                if isinstance(NativeFeature, Mapping)
                else NativeDefinitionData
            )
            Properties = NativeA(NativePropSource)
            NativeDefinitionType = TextAction(Definition.get("type_id"))
            if NativeDefinitionData and NativeDefinitionType:
                Final.type_id = NativeDefinitionType
            PropNames = {ItemValue.get("name", "") for ItemValue in Properties}
            if "Label" in PropNames:
                MergeNamedMut(Properties, StringProp("Label", FeatureName))
            if KindValue == "extrusion":
                Length = abs(
                    Number(
                        Definition.get("length"), Number(Attributes.get("length_mm"))
                    )
                )
                Replacements = [
                    FloatProp("Length", Length, "App::PropertyLength"),
                    FloatProp(
                        "Length2",
                        abs(Number(Definition.get("second_length"))),
                        "App::PropertyLength",
                    ),
                    BoolProp("Midplane", bool(Definition.get("symmetric"))),
                    BoolProp("Reversed", bool(Definition.get("reversed"))),
                ]
                Direction = Definition.get("direction")
                if Direction is not None:
                    Replacements.append(
                        VectorProp("Direction", Vector(Direction, (0.0, 0.0, 1.0)))
                    )
                for Replacement in Replacements:
                    if Replacement.get("name", "") in PropNames:
                        MergeNamedMut(Properties, Replacement)
            elif KindValue == "fillet":
                Radius = abs(
                    Number(
                        Definition.get("radius"), Number(Attributes.get("radius_mm"))
                    )
                )
                for NameValue in ("Radius", "DrivingRadius"):
                    if NameValue in PropNames:
                        MergeNamedMut(
                            Properties,
                            FloatProp(NameValue, Radius, "App::PropertyLength"),
                        )
            if "Suppressed" in PropNames or bool(Feature.get("suppressed")):
                MergeNamedMut(
                    Properties,
                    BoolProp(
                        "Suppressed",
                        bool(Feature.get("suppressed")),
                        Dynamic="Suppressed" not in PropNames,
                    ),
                )
            Final.properties = Properties
            FeatureNames[FeatureId] = Final.name
            SolidFeatureNames[FeatureId] = Final.name
            FeatureObjects.append(Final.name)
            CurrentName = Final.name
            NativeObjectTargets[NativeFeatureName] = Final.name
            continue
        if KindValue == "extrusion" and (
            SourceFormatId == "solidworks.sldprt"
            and (
                not SketchNativeProfileCounts.get(
                    TextAction(Feature.get("sketch_id")), 0
                )
                or not SketchNativeProfileSound.get(
                    TextAction(Feature.get("sketch_id")), False
                )
            )
            or bool(Feature.get("suppressed"))
        ):
            Length = abs(
                Number(Definition.get("length"), Number(Attributes.get("length_mm")))
            )
            SecondLength = abs(Number(Definition.get("second_length")))
            ParamId = FeatureParam(Feature, Parameters, Length)
            Expression = Parameters.expression(ParamId)
            Final = Graph.add("Part::Feature", FeatureName, "Feature")
            Final.properties.extend(
                [
                    StringProp("Label", FeatureName),
                    ExpressionProp([("Length", Expression)] if Expression else []),
                    FloatProp("Length", Length, "App::PropertyLength", Dynamic=True),
                    FloatProp(
                        "SecondLength",
                        SecondLength,
                        "App::PropertyLength",
                        Dynamic=True,
                    ),
                    BoolProp(
                        "Midplane", bool(Definition.get("symmetric")), Dynamic=True
                    ),
                    BoolProp(
                        "Reversed", bool(Definition.get("reversed")), Dynamic=True
                    ),
                    VectorProp(
                        "Direction",
                        Vector(Definition.get("direction"), (0.0, 0.0, 1.0)),
                        Dynamic=True,
                    ),
                    *FeatureMeta(Feature, "feature-data"),
                    BoolProp("NativeExecutable", False, Dynamic=True),
                    StringProp(
                        "NativeExecutionReason",
                        (
                            "suppressed"
                            if bool(Feature.get("suppressed"))
                            else (
                                "no_native_closed_profile"
                                if not SketchNativeProfileCounts.get(
                                    TextAction(Feature.get("sketch_id")), 0
                                )
                                else "profile_topology_not_statically_sound"
                            )
                        ),
                        Dynamic=True,
                    ),
                    *DefinitionProps(Definition),
                    JsonProp("NativeDefinitionJSON", Definition),
                    ShapeProp(),
                    BoolProp("Visibility", False),
                ]
            )
            if FeatureSketchName:
                Final.properties.append(
                    LinkProp("Profile", FeatureSketchName, Dynamic=True)
                )
                Final.dependencies.append(FeatureSketchName)
            if Expression:
                Final.dependencies.append(ParamSheet.name)
            FeatureNames[FeatureId] = Final.name
            FeatureObjects.append(Final.name)
            if InputBaseName:
                SolidFeatureNames[FeatureId] = InputBaseName
                CurrentName = InputBaseName
            continue
        if KindValue == "extrusion":
            SketchId = TextAction(Feature.get("sketch_id"))
            SketchName = SketchNames.get(SketchId, "")
            PlaneId = TextAction(
                next(
                    (
                        ItemValue.get("support_plane_id")
                        for ItemValue in SketchItems
                        if TextAction(ItemValue.get("id")) == SketchId
                    ),
                    "",
                )
            )
            Plane = PlaneById.get(PlaneId, {})
            Transform = (
                Plane.get("transform", {})
                if isinstance(Plane.get("transform"), Mapping)
                else {}
            )
            Normal = Normalize(Vector(Transform.get("z_axis"), (0.0, 0.0, 1.0)))
            ReversedDirection = bool(
                Definition.get(
                    "reversed",
                    Number(
                        Attributes.get("direction_multiplier"),
                        -1.0 if Operation == "cut" else 1.0,
                    )
                    < 0,
                )
            )
            ExplicitDirection = Definition.get("direction")
            Direction = (
                Normalize(Vector(ExplicitDirection, Normal))
                if ExplicitDirection is not None
                else tuple(
                    (
                        Component * (-1.0 if ReversedDirection else 1.0)
                        for Component in Normal
                    )
                )
            )
            Length = abs(
                Number(Definition.get("length"), Number(Attributes.get("length_mm")))
            )
            SecondLength = abs(Number(Definition.get("second_length")))
            Symmetric = bool(Definition.get("symmetric"))
            ParamId = FeatureParam(Feature, Parameters, Length)
            Expression = Parameters.expression(ParamId)
            OperationKind = (
                "join"
                if BaseName and Operation in CreateOperationNames
                else Operation or "create"
            )
            OperationType = BoolOperationTypeByKind.get(OperationKind)
            ToolType = BoolOperationTypeByKind["create"]
            ToolRequested = FeatureName if not BaseName else f"{FeatureName}_Profile"
            ToolValue = Graph.add(
                ToolType.type_id, ToolRequested, ToolType.label, Touched=True
            )
            ToolValue.properties.extend(
                [
                    StringProp(
                        "Label",
                        (
                            FeatureName
                            if ToolRequested == FeatureName
                            else f"{FeatureName} profile extrusion"
                        ),
                    ),
                    LinkProp("Base", SketchName),
                    VectorProp("Dir", Direction),
                    EnumerationProA("DirMode", 0),
                    FloatProp("LengthFwd", Length, "App::PropertyDistance"),
                    FloatProp("LengthRev", SecondLength, "App::PropertyDistance"),
                    BoolProp("Solid", True),
                    BoolProp("Reversed", False),
                    BoolProp("Symmetric", Symmetric),
                    StringProp(
                        "EndCondition",
                        TextAction(
                            EnumAction(Definition.get("end_condition")), "blind"
                        ),
                        Dynamic=True,
                    ),
                    ExpressionProp([("LengthFwd", Expression)] if Expression else []),
                    ShapeProp(),
                    *FeatureMeta(
                        Feature, "profile-extrusion" if BaseName else "feature"
                    ),
                    BoolProp("Visibility", not BaseName),
                ]
            )
            ToolValue.dependencies.append(SketchName)
            if Expression:
                ToolValue.dependencies.append(ParamSheet.name)
            if not BaseName:
                Final = ToolValue
            elif OperationType is not None and OperationType.input_mode == "base_tool":
                Final = Graph.add(
                    OperationType.type_id,
                    FeatureName,
                    OperationType.label,
                    Touched=True,
                )
                Final.properties.extend(
                    [
                        StringProp("Label", FeatureName),
                        LinkProp("Base", BaseName),
                        LinkProp("Tool", ToolValue.name),
                        BoolProp("Refine", True),
                        ExpressionProp([]),
                        ShapeProp(),
                        *FeatureMeta(Feature, "feature"),
                        BoolProp("Visibility", True),
                    ]
                )
                Final.dependencies.extend([BaseName, ToolValue.name])
                ToolValue.properties[-1] = BoolProp("Visibility", False)
            elif OperationType is not None and OperationType.input_mode == "shapes":
                Final = Graph.add(
                    OperationType.type_id,
                    FeatureName,
                    OperationType.label,
                    Touched=True,
                )
                Final.properties.extend(
                    [
                        StringProp("Label", FeatureName),
                        LinkListProp("Shapes", [BaseName, ToolValue.name]),
                        BoolProp("Refine", True),
                        ExpressionProp([]),
                        ShapeProp(),
                        *FeatureMeta(Feature, "feature"),
                        BoolProp("Visibility", True),
                    ]
                )
                Final.dependencies.extend([BaseName, ToolValue.name])
                ToolValue.properties[-1] = BoolProp("Visibility", False)
            else:
                Final = ToolValue
            FeatureNames[FeatureId] = Final.name
            SolidFeatureNames[FeatureId] = Final.name
            FeatureObjects.append(Final.name)
            CurrentName = Final.name
        elif KindValue == "fillet" and SourceFormatId == "solidworks.sldprt":
            Radius = abs(
                Number(Definition.get("radius"), Number(Attributes.get("radius_mm")))
            )
            ParamId = FeatureParam(Feature, Parameters, Radius)
            Expression = Parameters.expression(ParamId)
            Final = Graph.add("Part::Feature", FeatureName, "Feature")
            Final.properties.extend(
                [
                    StringProp("Label", FeatureName),
                    ExpressionProp(
                        [("DrivingRadius", Expression)] if Expression else []
                    ),
                    FloatProp(
                        "DrivingRadius", Radius, "App::PropertyLength", Dynamic=True
                    ),
                    *FeatureMeta(Feature, "feature-data"),
                    BoolProp("NativeExecutable", False, Dynamic=True),
                    StringProp(
                        "NativeExecutionReason",
                        "topology_selection_not_statically_provable",
                        Dynamic=True,
                    ),
                    *DefinitionProps(Definition),
                    JsonProp("NativeDefinitionJSON", Definition),
                    ShapeProp(),
                    BoolProp("Visibility", False),
                ]
            )
            if InputBaseName:
                Final.properties.append(
                    LinkProp("InputFeature", InputBaseName, Dynamic=True)
                )
                Final.dependencies.append(InputBaseName)
            if Expression:
                Final.dependencies.append(ParamSheet.name)
            FeatureNames[FeatureId] = Final.name
            FeatureObjects.append(Final.name)
            if InputBaseName:
                SolidFeatureNames[FeatureId] = InputBaseName
                CurrentName = InputBaseName
        elif KindValue == "fillet" and InputBaseName:
            Radius = abs(
                Number(Definition.get("radius"), Number(Attributes.get("radius_mm")))
            )
            ParamId = FeatureParam(Feature, Parameters, Radius)
            Expression = Parameters.expression(ParamId)
            EdgeIndices: list[int] = []
            SemanticEdgeIndices: list[int] = []
            for KeyValue in (
                "selected_native_local_edge_ids",
                "native_local_edge_ids",
                "edge_ids",
                "edges",
            ):
                Values = Attributes.get(KeyValue, [])
                EdgeIndices.extend(
                    (
                        int(Number(Value))
                        for Value in Sequence(Values)
                        if Number(Value) > 0
                    )
                )
            for SelectionId in Sequence(Feature.get("selection_ids", [])):
                Selection = SelectionItems.get(TextAction(SelectionId), {})
                for PathItem in Items(Selection.get("path", [])):
                    SubElem = TextAction(PathItem.get("subelement"))
                    Match = RegexLib.fullmatch(
                        "(?:Edge|edge:)(\\d+)", SubElem, RegexLib.IGNORECASE
                    )
                    if Match:
                        EdgeIndices.append(int(Match.group(1)))
                Query = (
                    Selection.get("query", {})
                    if isinstance(Selection.get("query"), Mapping)
                    else {}
                )
                if (
                    TextAction(Query.get("topology_role"))
                    == "extrusion_terminal_profile_boundary"
                ):
                    SemanticEdgeIndices.append(3)
                for KeyValue in ("edge_index", "native_local_id", "index"):
                    if Number(Query.get(KeyValue)) > 0:
                        EdgeIndices.append(int(Number(Query.get(KeyValue))))
            if SemanticEdgeIndices:
                EdgeIndices = SemanticEdgeIndices
            EdgeIndices = list(dict.fromkeys(EdgeIndices)) or [1]
            Final = Graph.add("Part::Fillet", FeatureName, "Fillet", Touched=True)
            EdgeFileName = f"{Final.name}.Edges"
            PayloadEntries[EdgeFileName] = FilletEdgesData(EdgeIndices, Radius)
            Expressions = [("DrivingRadius", Expression)] if Expression else []
            Final.properties.extend(
                [
                    StringProp("Label", FeatureName),
                    LinkProp("Base", BaseName),
                    FilletEdgesProp(EdgeFileName),
                    EdgeLinkProp(BaseName, EdgeIndices),
                    ExpressionProp(Expressions),
                    FloatProp(
                        "DrivingRadius", Radius, "App::PropertyLength", Dynamic=True
                    ),
                    ShapeProp(),
                    *FeatureMeta(Feature, "feature"),
                    BoolProp("Visibility", True),
                ]
            )
            Final.dependencies.extend(
                [BaseName] + ([ParamSheet.name] if Expression else [])
            )
            FeatureNames[FeatureId] = Final.name
            SolidFeatureNames[FeatureId] = Final.name
            FeatureObjects.append(Final.name)
            CurrentName = Final.name
        else:
            Imported = KindValue == "imported"
            Final = Graph.add("Part::Feature", FeatureName, "Feature", Touched=True)
            Final.properties.extend(
                [
                    StringProp("Label", FeatureName),
                    ExpressionProp([]),
                    *FeatureMeta(Feature, "imported" if Imported else "feature-data"),
                    StringProp(
                        "NativeTypeId", Definition.get("type_id", ""), Dynamic=True
                    ),
                    *DefinitionProps(Definition),
                    JsonProp("NativeDefinitionJSON", Definition),
                    BoolProp("Visibility", not bool(Feature.get("suppressed"))),
                    ShapeProp(),
                ]
            )
            if BaseName:
                Final.properties.append(
                    LinkProp("InputFeature", BaseName, Dynamic=True)
                )
                Final.dependencies.append(BaseName)
            if FeatureSketchName:
                Final.properties.append(
                    LinkProp("Profile", FeatureSketchName, Dynamic=True)
                )
                Final.dependencies.append(FeatureSketchName)
            if ParametersData:
                Final.properties.extend(
                    [
                        LinkProp("Parameters", ParamSheet.name, Dynamic=True),
                        StringListProp(
                            "ParameterIds",
                            [
                                TextAction(Value)
                                for Value in Sequence(Feature.get("parameter_ids", []))
                            ],
                            Dynamic=True,
                        ),
                    ]
                )
                Final.dependencies.append(ParamSheet.name)
            FeatureNames[FeatureId] = Final.name
            FeatureObjects.append(Final.name)
            if SourceFormatId == "solidworks.sldprt":
                if InputBaseName:
                    SolidFeatureNames[FeatureId] = InputBaseName
                    CurrentName = InputBaseName
            elif KindValue not in {"native", "reference"}:
                SolidFeatureNames[FeatureId] = Final.name
                CurrentName = Final.name
        if bool(Feature.get("suppressed")) and (not NativeReplay):
            ReplaceNameMut(
                Final.properties, "Visibility", BoolProp("Visibility", False)
            )
        if isinstance(NativeFeature, Mapping):
            if NativeFeatureName:
                NativeObjectTargets[NativeFeatureName] = Final.name
    BodyObjects: list[str] = []
    BodyNames: dict[str, str] = {}
    BodyShapeTargets: dict[str, str] = {}
    FeatureById = {
        TextAction(ItemValue.get("id")): ItemValue
        for ItemValue in FeatureItems
        if TextAction(ItemValue.get("id"))
    }

    # this definition exists because focused behavior needs one stable owner
    def BodyMembers(FinalFeatureId: str) -> list[str]:
        Pending = [FinalFeatureId]
        MemberIds: set[str] = set()
        while Pending:
            FeatureId = Pending.pop()
            if FeatureId in MemberIds or FeatureId not in FeatureById:
                continue
            MemberIds.add(FeatureId)
            Pending.extend(
                (
                    TextAction(Value)
                    for Value in Sequence(
                        FeatureById[FeatureId].get("input_feature_ids", [])
                    )
                )
            )
        Members: list[str] = []
        for ItemValue in FeatureItems:
            FeatureId = TextAction(ItemValue.get("id"))
            if FeatureId not in MemberIds:
                continue
            SketchName = SketchNames.get(TextAction(ItemValue.get("sketch_id")), "")
            if SketchName and SketchName not in Members:
                Members.append(SketchName)
            FeatureName = FeatureNames.get(FeatureId, "")
            if FeatureName and FeatureName not in Members:
                Members.append(FeatureName)
        return Members

    for BodyValue in Items(Manifest.get("bodies", [])):
        BodyId = TextAction(BodyValue.get("id"))
        FinalFeatureId = TextAction(BodyValue.get("final_feature_id"))
        FinalFeature = FeatureNames.get(FinalFeatureId, CurrentName)
        Members = BodyMembers(FinalFeatureId)
        BodyAttributes = BodyValue.get("attributes", {})
        NativeBody = (
            BodyAttributes.get("freecad", {})
            if isinstance(BodyAttributes, Mapping)
            else {}
        )
        NativeBodyName = (
            TextAction(NativeBody.get("name"))
            if isinstance(NativeBody, Mapping)
            else ""
        )
        ObjValue = NativeGraph.get(NativeBodyName) if NativeReplay else None
        if ObjValue is not None:
            Properties = NativeA(NativeBody)
            MergeNamedMut(
                Properties, StringProp("Label", BodyValue.get("name", BodyId))
            )
            if FinalFeature:
                MergeNamedMut(Properties, LinkProp("Tip", FinalFeature))
            ObjValue.properties = Properties
            NativeObjectTargets[NativeBodyName] = ObjValue.name
        else:
            ObjValue = Graph.add(
                TextAction(NativeBody.get("type_id"), "App::DocumentObjectGroup"),
                NativeBody.get("name", BodyValue.get("name", BodyId)),
                "Body",
            )
            ObjValue.properties.extend(
                [
                    StringProp("Label", BodyValue.get("name", BodyId)),
                    LinkListProp("Group", Members),
                    LinkProp("Tip", FinalFeature, Dynamic=True),
                    MakePlacement("Placement", MatrixTransform(KIdentityMatrix)),
                    StringProp("KitId", BodyId, Dynamic=True),
                    JsonProp("TopologyJSON", BodyValue.get("topology", {})),
                    JsonProp("SourceBodyJSON", BodyValue),
                    BoolProp("Visibility", True),
                ]
            )
            MaterialId = TextAction(BodyValue.get("material_id"))
            if MaterialId:
                ObjValue.properties.append(
                    StringProp("MaterialId", MaterialId, Dynamic=True)
                )
            ObjValue.dependencies.extend(Members)
        BodyNames[BodyId] = ObjValue.name
        BodyShapeTargets[BodyId] = FinalFeature or ObjValue.name
        BodyObjects.append(ObjValue.name)
    TargetById = {**PlaneNames, **SketchNames, **FeatureNames, **BodyNames}
    TargetById.update({NameValue: NameValue for NameValue in Graph.Names})
    SelectionNames: dict[str, str] = {}
    SelectionObjects: list[str] = []
    for Selection in SelectionItems.values():
        SelectionId = TextAction(Selection.get("id"))
        ObjValue = Graph.add(
            "App::FeaturePython", Selection.get("name", SelectionId), "Selection"
        )
        Targets: list[tuple[str, str]] = []
        EntityKinds: list[str] = []
        for PathItem in Items(Selection.get("path", [])):
            EntityId = TextAction(PathItem.get("entity_id"))
            Target = TargetById.get(EntityId, NativeObjectTargets.get(EntityId, ""))
            if not Target:
                continue
            Targets.append((Target, TextAction(PathItem.get("subelement"))))
            EntityKinds.append(TextAction(PathItem.get("entity_kind")))
        ObjValue.properties.extend(
            [
                StringProp("Label", Selection.get("name", SelectionId)),
                StringProp("KitSelectionId", SelectionId, Dynamic=True),
                LinkSubListProp("Selection", Targets, Dynamic=True),
                StringListProp("EntityKinds", EntityKinds, Dynamic=True),
                JsonProp("QueryJSON", Selection.get("query", {})),
                JsonProp("SourceSelectionJSON", Selection),
                BoolProp("Visibility", False),
            ]
        )
        Point = Selection.get("point")
        if Point is not None:
            ObjValue.properties.append(
                VectorProp(
                    "SelectionPoint", Vector(Point, (0.0, 0.0, 0.0)), Dynamic=True
                )
            )
        ObjValue.dependencies.extend((Target for Target, Ignored in Targets))
        SelectionNames[SelectionId] = ObjValue.name
        SelectionObjects.append(ObjValue.name)
    for Feature in FeatureItems:
        Target = next(
            (
                ItemValue
                for ItemValue in Graph.Objects
                if ItemValue.name == FeatureNames.get(TextAction(Feature.get("id")), "")
            ),
            None,
        )
        LinkedSelections = [
            SelectionNames[SelectionId]
            for Value in Sequence(Feature.get("selection_ids", []))
            if (SelectionId := TextAction(Value)) in SelectionNames
        ]
        if Target is not None and LinkedSelections:
            MergeNamedMut(
                Target.properties,
                LinkListProp("Selections", LinkedSelections, Dynamic=True),
            )
            Target.dependencies.extend(LinkedSelections)
    for Plane in PlaneItems:
        SelectionName = SelectionNames.get(
            TextAction(Plane.get("support_selection_id")), ""
        )
        Target = next(
            (
                ItemValue
                for ItemValue in Graph.Objects
                if ItemValue.name == PlaneNames.get(TextAction(Plane.get("id")), "")
            ),
            None,
        )
        if Target is not None and SelectionName:
            MergeNamedMut(
                Target.properties,
                LinkProp("SupportSelection", SelectionName, Dynamic=True),
            )
            Target.dependencies.append(SelectionName)
    ConfigItems = Items(Manifest.get("configurations", []))
    ConfigNames: dict[str, str] = {}
    ConfigObjects: list[str] = []
    for Config in ConfigItems:
        ConfigId = TextAction(Config.get("id"))
        ObjValue = Graph.add(
            "App::FeaturePython", Config.get("name", ConfigId), "Configuration"
        )
        ConfigNames[ConfigId] = ObjValue.name
        ConfigObjects.append(ObjValue.name)
    for Config, ObjectName in zip(ConfigItems, ConfigObjects, strict=True):
        ObjValue = next(
            (ItemValue for ItemValue in Graph.Objects if ItemValue.name == ObjectName)
        )
        ConfigId = TextAction(Config.get("id"))
        ParentName = ConfigNames.get(TextAction(Config.get("parent_id")), "")
        SuppressedFeatures = [
            FeatureNames[FeatureId]
            for Value in Sequence(Config.get("suppressed_feature_ids", []))
            if (FeatureId := TextAction(Value)) in FeatureNames
        ]
        ObjValue.properties.extend(
            [
                StringProp("Label", Config.get("name", ConfigId)),
                StringProp("KitConfigurationId", ConfigId, Dynamic=True),
                BoolProp("Active", bool(Config.get("active")), Dynamic=True),
                LinkListProp("SuppressedFeatures", SuppressedFeatures, Dynamic=True),
                LinkProp("Parameters", ParamSheet.name, Dynamic=True),
                JsonProp("ParameterOverridesJSON", Config.get("overrides", [])),
                JsonProp("SourceConfigurationJSON", Config),
                BoolProp("Visibility", False),
            ]
        )
        if ParentName:
            ObjValue.properties.append(
                LinkProp("ParentConfiguration", ParentName, Dynamic=True)
            )
        ObjValue.dependencies.extend(
            [ParamSheet.name, *SuppressedFeatures]
            + ([ParentName] if ParentName else [])
        )
    Payloads = Items(Manifest.get("brep_payloads", Manifest.get("native_payloads", [])))
    for Index, Payload in enumerate(Payloads, start=1):
        DataValue = PayloadBytes(Payload)
        if DataValue is None:
            continue
        PayloadId = SafeAction(Payload.get("id", f"payload_{Index}"), "payload")
        Entry = str(
            PurePosixPath("interchange", "native", PayloadId + PayloadSuffix(Payload))
        )
        PayloadEntries[Entry] = DataValue
        Attributes = (
            Payload.get("attributes", {})
            if isinstance(Payload.get("attributes"), Mapping)
            else {}
        )
        TargetFeatureId = TextAction(
            Attributes.get("feature_id", Attributes.get("final_feature_id"))
        )
        TargetBodyId = TextAction(Attributes.get("body_id"))
        SourceObject = TextAction(Attributes.get("freecad_object"))
        PropName = TextAction(Attributes.get("freecad_property"), "Shape")
        TargetName = NativeObjectTargets.get(SourceObject, "")
        if not TargetName and TargetFeatureId:
            TargetName = FeatureNames.get(TargetFeatureId, "")
        if not TargetName and TargetBodyId:
            TargetName = BodyShapeTargets.get(TargetBodyId, "")
        if not TargetName and (not SourceObject):
            TargetName = CurrentName
        NativeBrep = (
            FreecadBrep(Payload, DataValue, NativeDocShaTwoFiveSix, TrustedNativeBreps)
            if PayloadRole(Payload) == "brep"
            else None
        )
        if NativeBrep is not None:
            Target = next(
                (
                    ItemValue
                    for ItemValue in Graph.Objects
                    if ItemValue.name == TargetName
                ),
                None,
            )
            if Target is None:
                Target = Graph.add(
                    "Part::Feature",
                    f"NativeBRep_{Index}",
                    TextAction(Payload.get("id"), f"Native BRep {Index}"),
                )
                Target.properties.extend(
                    [
                        StringProp(
                            "Label",
                            TextAction(Payload.get("id"), f"Native BRep {Index}"),
                        ),
                        StringProp("KitPayloadId", Payload.get("id"), Dynamic=True),
                        BoolProp("Visibility", True),
                    ]
                )
                BodyObjects.append(Target.name)
                TargetName = Target.name
            if Target is not None:
                ShapeEntry = f"{Target.name}.{SafeAction(PropName, 'Shape')}.brp"
                PayloadEntries[ShapeEntry] = NativeBrep
                SidecarEntries: dict[str, str] = {}
                for Sidecar in (
                    Items(Attributes.get("freecad_sidecars", []))
                    if NativeBrep == DataValue
                    else []
                ):
                    SourceStream = TextAction(Sidecar.get("source_stream"))
                    SidecarData = PayloadBytes(Sidecar)
                    if not SourceStream or SidecarData is None:
                        continue
                    Suffix = PurePosixPath(SourceStream).name
                    SourcePrefix = PurePosixPath(
                        TextAction(Payload.get("source_stream"))
                    ).stem
                    if Suffix.startswith(SourcePrefix):
                        Suffix = Suffix[len(SourcePrefix) :]
                    SidecarEntry = (
                        f"{Target.name}.{SafeAction(PropName, 'Shape')}{Suffix}"
                    )
                    SidecarEntries[SourceStream] = SidecarEntry
                    PayloadEntries[SidecarEntry] = SidecarData
                PropElem = (
                    ElemFromData(Attributes.get("freecad_property_data"))
                    if NativeBrep == DataValue
                    else None
                )
                if PropElem is None or PropElem.tag != "Property":
                    PropElem = ShapeProp(ShapeEntry, SafeAction(PropName, "Shape"))
                for Child in PropElem.findall(".//*[@file]"):
                    SourceStream = Child.get("file", "")
                    Child.set(
                        "file",
                        (
                            ShapeEntry
                            if Child.tag == "Part"
                            else SidecarEntries.get(SourceStream, SourceStream)
                        ),
                    )
                MergeNamedMut(Target.properties, PropElem)
                if PropName == "Shape" and Target.name == CurrentName:
                    FinalShapeFileName = ShapeEntry
    DocBreps, NeutralShapeFileName = AddBrepMut(
        Graph, Manifest, PayloadEntries, CurrentName
    )
    if NeutralShapeFileName:
        FinalShapeFileName = NeutralShapeFileName
    DocMeshes = AddMeshesMut(Graph, Manifest, PayloadEntries, CurrentName)
    AsmRoot, ItemCount, MateCount = AddAsmMut(
        Graph, Manifest, PayloadEntries, OuterLinks, TrustedNativeBreps
    )
    PlanesGroup.properties.extend(
        [
            StringProp("Label", "Support Planes"),
            LinkListProp("Group", PlaneObjects),
            BoolProp("Visibility", False),
        ]
    )
    PlanesGroup.dependencies.extend(PlaneObjects)
    SketchesGroup.properties.extend(
        [
            StringProp("Label", "Sketches"),
            LinkListProp("Group", SketchObjects),
            BoolProp("Visibility", False),
        ]
    )
    SketchesGroup.dependencies.extend(SketchObjects)
    SelectionsGroup.properties.extend(
        [
            StringProp("Label", "Selections"),
            LinkListProp("Group", SelectionObjects),
            BoolProp("Visibility", False),
        ]
    )
    SelectionsGroup.dependencies.extend(SelectionObjects)
    ConfigurationsGroup.properties.extend(
        [
            StringProp("Label", "Configurations"),
            LinkListProp("Group", ConfigObjects),
            BoolProp("Visibility", False),
        ]
    )
    ConfigurationsGroup.dependencies.extend(ConfigObjects)
    TimelineGroup.properties.extend(
        [
            StringProp("Label", "Feature Timeline"),
            LinkListProp("Group", FeatureObjects),
            BoolProp("Visibility", True),
        ]
    )
    TimelineGroup.dependencies.extend(FeatureObjects)
    BodiesGroup.properties.extend(
        [
            StringProp("Label", "Bodies"),
            LinkListProp("Group", [*BodyObjects, *DocBreps]),
            BoolProp("Visibility", True),
        ]
    )
    BodiesGroup.dependencies.extend([*BodyObjects, *DocBreps])
    SoleBodyShape = (
        next(iter(BodyShapeTargets.values())) if len(BodyShapeTargets) == 1 else ""
    )
    OuterTarget = (
        DocBreps[0]
        if DocBreps
        else (
            DocMeshes[0]
            if DocMeshes
            else AsmRoot
            or CurrentName
            or SoleBodyShape
            or (BodiesGroup.name if BodyObjects else "")
            or (FeatureObjects[-1] if FeatureObjects else "")
            or BodiesGroup.name
        )
    )
    TargetObject = next(
        (ItemValue for ItemValue in Graph.Objects if ItemValue.name == OuterTarget),
        None,
    )
    if TargetObject is not None and (not NativeReplay):
        TargetObject.properties.append(
            LinkProp("Sketches", SketchesGroup.name, Dynamic=True)
        )
        TargetObject.dependencies.append(SketchesGroup.name)
        if OuterTarget not in FeatureObjects:
            TargetObject.properties.append(
                LinkProp("FeatureTimeline", TimelineGroup.name, Dynamic=True)
            )
            TargetObject.dependencies.append(TimelineGroup.name)
    MetaValue.properties.extend(
        [
            StringProp("FinalFeature", CurrentName, Dynamic=True),
            StringProp("ExternalLinkTarget", OuterTarget, Dynamic=True),
            StringProp("CachedShapeEntry", FinalShapeFileName, Dynamic=True),
            StringProp("AssemblyRoot", AsmRoot, Dynamic=True),
            IntegerProp("AssemblyOccurrenceCount", ItemCount, Dynamic=True),
            IntegerProp("AssemblyMateCount", MateCount, Dynamic=True),
            StringListProp(
                "NativePayloadEntries", sorted(PayloadEntries), Dynamic=True
            ),
        ]
    )
    Source = (
        Manifest.get("source", {})
        if isinstance(Manifest.get("source"), Mapping)
        else {}
    )
    Label = PurePosixPath(TextAction(Source.get("path"), "Kit")).stem or "Kit"
    DocId = TextAction(Source.get("sha256"), ManifestShaTwoFiveSix)
    if NativeReplay and NativeOuterLinks:
        for ObjValue in NativeGraph.values():
            for PropElem in ObjValue.properties:
                for Xlink in PropElem.findall(".//XLink[@file]"):
                    SourceFile = Xlink.get("file", "")
                    if SourceFile in NativeOuterLinks:
                        Xlink.set("file", NativeOuterLinks[SourceFile])
    StringHasher = (
        FreecadMeta.get("string_hasher", {}) if isinstance(FreecadMeta, Mapping) else {}
    )
    RootAttributes = {
        "SchemaVersion": KTargetSchemaVersion,
        "ProgramVersion": (
            TextAction(FreecadMeta.get("program_version"), KTargetProgramVersion)
            if NativeReplay and isinstance(FreecadMeta, Mapping)
            else KTargetProgramVersion
        ),
        "FileVersion": (
            TextAction(FreecadMeta.get("file_version"), KTargetFileVersion)
            if NativeReplay and isinstance(FreecadMeta, Mapping)
            else KTargetFileVersion
        ),
    }
    if isinstance(StringHasher, Mapping):
        AttrValue = TextAction(StringHasher.get("attribute"))
        if AttrValue:
            RootAttributes["StringHasher"] = AttrValue
    RootValue = XmlTree.Element("Document", RootAttributes)
    if isinstance(StringHasher, Mapping):
        for Value in Items(StringHasher.get("nodes", [])):
            NodeValue = ElemFromData(Value)
            if NodeValue is not None and NodeValue.tag in StringHasherTags:
                RootValue.append(NodeValue)
        for Entry in Items(StringHasher.get("entries", [])):
            SourceStream = TextAction(Entry.get("source_stream"))
            DataValue = PayloadBytes(Entry)
            PathValue = PurePosixPath(SourceStream)
            if (
                SourceStream
                and DataValue is not None
                and (not PathValue.is_absolute())
                and (".." not in PathValue.parts)
            ):
                PayloadEntries[SourceStream] = DataValue
    SanitizePayload(Graph.Objects, PayloadEntries)
    NativeDocProperties = (
        ElemFromData(FreecadMeta.get("document_properties"))
        if NativeReplay and isinstance(FreecadMeta, Mapping)
        else None
    )
    RootValue.append(
        NativeDocProperties
        if NativeDocProperties is not None and NativeDocProperties.tag == "Properties"
        else DocProperties(Label, DocId, DocTimestamp)
    )
    Objects = XmlTree.SubElement(
        RootValue, "Objects", {"Count": str(len(Graph.Objects)), "Dependencies": "1"}
    )
    for ObjValue in Graph.Objects:
        Dependencies = [
            Value for Value in dict.fromkeys(ObjValue.dependencies) if Value
        ]
        Dependency = XmlTree.SubElement(
            Objects,
            "ObjectDeps",
            {"Name": ObjValue.name, "Count": str(len(Dependencies))},
        )
        for Target in Dependencies:
            XmlTree.SubElement(Dependency, "Dep", {"Name": Target})
    ObjectIds = {ObjValue.object_id for ObjValue in Graph.Objects if ObjValue.object_id}
    NumericIds = [int(Value) for Value in ObjectIds if Value.isdigit()]
    NextObjectId = max(NumericIds, default=0) + 1
    for ObjValue in Graph.Objects:
        ObjectId = ObjValue.object_id
        if not ObjectId:
            while str(NextObjectId) in ObjectIds:
                NextObjectId += 1
            ObjectId = str(NextObjectId)
            ObjectIds.add(ObjectId)
            NextObjectId += 1
        Attributes = {"type": ObjValue.type_id, "name": ObjValue.name, "id": ObjectId}
        if ObjValue.touched:
            Attributes["Touched"] = "1"
        XmlTree.SubElement(Objects, "Object", Attributes)
    ObjectData = XmlTree.SubElement(
        RootValue, "ObjectData", {"Count": str(len(Graph.Objects))}
    )
    for ObjValue in Graph.Objects:
        SerializeObject(ObjectData, ObjValue)
    XmlTree.indent(RootValue, space="  ")
    XmlValue = XmlTree.tostring(RootValue, encoding="utf-8", xml_declaration=True)
    return (XmlValue + b"\n", PayloadEntries)


# this definition exists because focused behavior needs one stable owner
def ZipEntry(NameValue: str, DataValue: bytes) -> tuple[Zipfile.ZipInfo, bytes]:
    InfoValue = Zipfile.ZipInfo(NameValue, (1980, 1, 1, 0, 0, 0))
    InfoValue.compress_type = Zipfile.ZIP_DEFLATED
    InfoValue.external_attr = 384 << 16
    InfoValue.create_system = 3
    return (InfoValue, DataValue)


# this definition exists because focused behavior needs one stable owner
def BuildFcstd(
    Manifest: Mapping[str, Any],
    OuterLinks: Mapping[str, Mapping[str, Any]] | None = None,
    NativeOuterLinks: Mapping[str, str] | None = None,
    DocTimestamp: str | None = None,
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
) -> bytes:
    Canonical = CanonicalJson(Manifest)
    Digest = Hashlib.sha256(Canonical).hexdigest()
    Embedded = BaseSixFour.b64encode(ZlibValue.compress(Canonical, 9)).decode("ascii")
    DocXml, PayloadEntries = BuildDocXml(
        Manifest,
        Embedded,
        Digest,
        OuterLinks,
        NativeOuterLinks,
        DocTimestamp or "1980-01-01T00:00:00Z",
        TrustedNativeBreps,
    )
    Output = IoStream.BytesIO()
    with Zipfile.ZipFile(Output, "w", allowZip64=True) as Archive:
        Archive.writestr(*ZipEntry(KDocEntry, DocXml))
        MetaValue = Manifest.get("metadata", {})
        FreecadMeta = (
            MetaValue.get("freecad", {}) if isinstance(MetaValue, Mapping) else {}
        )
        EntryOrder = (
            Sequence(FreecadMeta.get("entry_order", []))
            if isinstance(FreecadMeta, Mapping)
            else []
        )
        Written: set[str] = set()
        for Value in EntryOrder:
            Entry = TextAction(Value)
            if Entry in PayloadEntries and Entry not in Written:
                Archive.writestr(*ZipEntry(Entry, PayloadEntries[Entry]))
                Written.add(Entry)
        Archive.writestr(*ZipEntry(KManifestEntry, Canonical + b"\n"))
        for Entry, DataValue in sorted(PayloadEntries.items()):
            if Entry in Written:
                continue
            Archive.writestr(*ZipEntry(Entry, DataValue))
    return Output.getvalue()


# this definition exists because focused behavior needs one stable owner
def BuildFcstdApi(
    Manifest: Mapping[str, Any],
    OuterLinks: Mapping[str, Mapping[str, Any]] | None = None,
    NativeOuterLinks: Mapping[str, str] | None = None,
    DocTimestamp: str | None = None,
    TrustedNativeBreps: frozenset[NativeBrepKey] = frozenset(),
    **LegacyValues: object,
) -> bytes:
    LegacyCopy = dict(LegacyValues)
    OuterLinks = LegacyCopy.pop("external_links", OuterLinks)
    NativeOuterLinks = LegacyCopy.pop("native_external_links", NativeOuterLinks)
    DocTimestamp = LegacyCopy.pop("document_timestamp", DocTimestamp)
    TrustedNativeBreps = LegacyCopy.pop("trusted_native_breps", TrustedNativeBreps)
    if LegacyCopy:
        Unexpected = next(iter(LegacyCopy))
        raise TypeError(
            f"build_fcstd_archive() got an unexpected keyword argument {Unexpected!r}"
        )
    return BuildFcstd(
        Manifest, OuterLinks, NativeOuterLinks, DocTimestamp, TrustedNativeBreps
    )


# this definition exists because focused behavior needs one stable owner
def DocXmlManifest(RootValue: ET.Element) -> bytes | None:
    Names = {KManifestDataProp, KManifestEncodingProp, KManifestShaTwoFiveSixPrA}
    Values: dict[str, list[str]] = {NameValue: [] for NameValue in Names}
    for PropElem in RootValue.findall(".//Property"):
        NameValue = PropElem.get("name", "")
        if NameValue not in Values:
            continue
        String = PropElem.find("String")
        Values[NameValue].append(String.get("value", "") if String is not None else "")
    if not any(Values.values()):
        return None
    if any((len(Items) > 1 for Items in Values.values())):
        raise ValueError("embedded Kit interchange document is corrupt")
    Encoded = next(iter(Values[KManifestDataProp]), "")
    Encoding = next(iter(Values[KManifestEncodingProp]), "")
    Digest = next(iter(Values[KManifestShaTwoFiveSixPrA]), "")
    if not Encoded or Encoding != KManifestEncoding:
        raise ValueError("embedded Kit interchange document is corrupt")
    try:
        Compressed = BaseSixFour.b64decode(Encoded, validate=True)
        Decompressor = ZlibValue.decompressobj()
        Canonical = Decompressor.decompress(Compressed, KMaxEntrySize + 1)
        if (
            len(Canonical) > KMaxEntrySize
            or Decompressor.unconsumed_tail
            or (not Decompressor.eof)
        ):
            raise ValueError
        Canonical += Decompressor.flush()
        if len(Canonical) > KMaxEntrySize or Decompressor.unused_data:
            raise ValueError
    except (ValueError, ZlibValue.error) as ErrorInfo:
        raise ValueError("embedded Kit interchange document is corrupt") from ErrorInfo
    if Digest and Hashlib.sha256(Canonical).hexdigest() != Digest:
        raise ValueError("embedded Kit interchange document hash mismatch")
    return Canonical


# this definition exists because focused behavior needs one stable owner
def CanonicalJson(Value: Mapping[str, Any]) -> bytes:
    return JsonValue.dumps(
        Value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


# this definition exists because focused behavior needs one stable owner
def ExtractManifest(DataValue: bytes) -> dict[str, AnyValue]:
    Archive, Members = Validated(DataValue)
    with Archive:
        RootValue, Ignored = ValidatedDocXml(Archive, Members)
        XmlManifest = DocXmlManifest(RootValue)
        if KManifestEntry not in Members:
            if XmlManifest is None:
                raise ValueError(
                    "FCStd archive has no embedded Kit interchange document"
                )
            return ManifestMapping(XmlManifest)
        try:
            RawManifest = Archive.read(Members[KManifestEntry])
        except (
            OSError,
            RuntimeError,
            NotImplementedError,
            Zipfile.BadZipFile,
        ) as ErrorInfo:
            raise ValueError(
                "embedded Kit interchange document is corrupt"
            ) from ErrorInfo
        Manifest = ManifestMapping(RawManifest)
        if XmlManifest is not None:
            Secondary = ManifestMapping(XmlManifest)
            if CanonicalJson(Manifest) != CanonicalJson(Secondary):
                raise ValueError(
                    "embedded Kit interchange document copies do not match"
                )
        return Manifest


# this binding exists because shared behavior needs one stable value
globals()["APP_LINK_TYPE_ID"] = AppLinkTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_CONNECTOR_PROPERTY_PREFIXES"] = AsmConnectorPropPrefixes

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_JOINT_GROUP_TYPE_ID"] = AsmJointGroupTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_LINK_TYPE_ID"] = AsmLinkTypeId

# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_ROOT_TYPE_ID"] = AsmRootTypeId

# this binding exists because shared behavior needs one stable value
globals()["Any"] = AnyValue

# this binding exists because shared behavior needs one stable value
globals()["BOOLEAN_OPERATION_TYPE_BY_KIND"] = BoolOperationTypeByKind

# this binding exists because shared behavior needs one stable value
globals()["CIRCULAR_GEOMETRY_KINDS"] = CircularGeomKinds

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_CODE_BY_KIND"] = RuleCodeByKind

# this binding exists because shared behavior needs one stable value
globals()["CONSTRAINT_POINT_INDEX_BY_NAME"] = RulePointIndexByName

# this binding exists because shared behavior needs one stable value
globals()["CREATE_OPERATION_NAMES"] = CreateOperationNames

# this binding exists because shared behavior needs one stable value
globals()["CadDocument"] = CadDoc

# this binding exists because shared behavior needs one stable value
globals()["DIMENSIONAL_CONSTRAINT_CODES"] = DimensionalRuleCodes

# this binding exists because shared behavior needs one stable value
globals()["DOCUMENT_ENTRY"] = KDocEntry

# this binding exists because shared behavior needs one stable value
globals()["ET"] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()["FIXED_CONSTRAINT_KINDS"] = FixedRuleKinds

# this binding exists because shared behavior needs one stable value
globals()["FORMAT_ID"] = FormatId

# this binding exists because shared behavior needs one stable value
globals()["FREECAD_BREP_FORMAT_IDS"] = FreecadBrepFormatIds

# this binding exists because shared behavior needs one stable value
globals()["FreeCADBrepWriteError"] = FreeCadBrepWriteError

# this binding exists because shared behavior needs one stable value
globals()["GEOMETRY_TYPE_IDS_BY_KIND"] = GeomTypeIdsByKind

# this binding exists because shared behavior needs one stable value
globals()["JOINT_GROUND_PROPERTY"] = JointGroundProp

# this binding exists because shared behavior needs one stable value
globals()["JOINT_REFERENCE_INDEX_BY_PROPERTY"] = JointRefIndexByProp

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
globals()["MANIFEST_DATA_PROPERTY"] = KManifestDataProp

# this binding exists because shared behavior needs one stable value
globals()["MANIFEST_ENCODING"] = KManifestEncoding

# this binding exists because shared behavior needs one stable value
globals()["MANIFEST_ENCODING_PROPERTY"] = KManifestEncodingProp

# this binding exists because shared behavior needs one stable value
globals()["MANIFEST_ENTRY"] = KManifestEntry

# this binding exists because shared behavior needs one stable value
globals()["MANIFEST_SHA256_PROPERTY"] = KManifestShaTwoFiveSixPrA

# this binding exists because shared behavior needs one stable value
globals()["MIDPOINT_REFERENCE_POINT_NAMES"] = MidpointRefPointNames

# this binding exists because shared behavior needs one stable value
globals()["NATIVE_DOCUMENT_SHA256_ATTRIBUTE"] = KNativeDocShaTwoFiveSix

# this binding exists because shared behavior needs one stable value
globals()["NEUTRAL_GEOMETRY_TYPE_BY_KIND"] = NeutralGeomTypeByKind

# this binding exists because shared behavior needs one stable value
globals()["NEUTRAL_GEOMETRY_TYPE_ID_BY_KIND"] = NeutralGeomTypeIdByKind

# this binding exists because shared behavior needs one stable value
globals()["NativeBrepKey"] = KNativeBrepKey

# this binding exists because shared behavior needs one stable value
globals()["SKETCH_TYPE_ID"] = SketchTypeId

# this binding exists because shared behavior needs one stable value
globals()["SPLINE_CONTROL_TAGS"] = SplineControlTags

# this binding exists because shared behavior needs one stable value
globals()["SPLINE_GEOMETRY_KINDS"] = SplineGeomKinds

# this binding exists because shared behavior needs one stable value
globals()["STRING_HASHER_TAGS"] = StringHasherTags

# this binding exists because shared behavior needs one stable value
globals()["_Graph"] = ObjectGraph

# this binding exists because shared behavior needs one stable value
globals()["_IDENTITY_MATRIX"] = KIdentityMatrix

# this binding exists because shared behavior needs one stable value
globals()["_MAX_COMPRESSION_RATIO"] = KMaxCompressionRatio

# this binding exists because shared behavior needs one stable value
globals()["_MAX_DOCUMENT_SIZE"] = KMaxDocSize

# this binding exists because shared behavior needs one stable value
globals()["_MAX_ENTRIES"] = KMaxEntries

# this binding exists because shared behavior needs one stable value
globals()["_MAX_ENTRY_SIZE"] = KMaxEntrySize

# this binding exists because shared behavior needs one stable value
globals()["_MAX_EXTERNAL_FILES"] = KMaxOuterFiles

# this binding exists because shared behavior needs one stable value
globals()["_MAX_MANIFEST_JSON_DEPTH"] = KMaxManifestJsonDepth

# this binding exists because shared behavior needs one stable value
globals()["_MAX_TOTAL_SIZE"] = KMaxTotalSize

# this binding exists because shared behavior needs one stable value
globals()["_MAX_XML_DEPTH"] = KMaxXmlDepth

# this binding exists because shared behavior needs one stable value
globals()["_MAX_XML_NODES"] = KMaxXmlNodes

# this binding exists because shared behavior needs one stable value
globals()["_MIN_OBJECT_GRAPH_SCHEMA_VERSION"] = KMinObjectGraphSchema

# this binding exists because shared behavior needs one stable value
globals()["_Object"] = Object

# this binding exists because shared behavior needs one stable value
globals()["_Parameters"] = ParamCatalog

# this binding exists because shared behavior needs one stable value
globals()["_TARGET_FILE_VERSION"] = KTargetFileVersion

# this binding exists because shared behavior needs one stable value
globals()["_TARGET_PROGRAM_VERSION"] = KTargetProgramVersion

# this binding exists because shared behavior needs one stable value
globals()["_TARGET_SCHEMA_VERSION"] = KTargetSchemaVersion

# this binding exists because shared behavior needs one stable value
globals()["_add_assembly"] = AddAsmMut

# this binding exists because shared behavior needs one stable value
globals()["_add_assembly_origin"] = AddOriginMut

# this binding exists because shared behavior needs one stable value
globals()["_add_document_brep"] = AddBrepMut

# this binding exists because shared behavior needs one stable value
globals()["_add_document_meshes"] = AddMeshesMut

# this binding exists because shared behavior needs one stable value
globals()["_assembly_data"] = AsmData

# this binding exists because shared behavior needs one stable value
globals()["_bool_property"] = BoolProp

# this binding exists because shared behavior needs one stable value
globals()["_canonical_manifest"] = CanonicalJson

# this binding exists because shared behavior needs one stable value
globals()["_constraint_carrier_reason"] = RuleCarrier

# this binding exists because shared behavior needs one stable value
globals()["_constraint_diagnostic"] = RuleDiag

# this binding exists because shared behavior needs one stable value
globals()["_constraints_property"] = ConstraintsProp

# this binding exists because shared behavior needs one stable value
globals()["_definition_mesh_sources"] = DefinitionMesh

# this binding exists because shared behavior needs one stable value
globals()["_definition_properties"] = DefinitionProps

# this binding exists because shared behavior needs one stable value
globals()["_definition_property"] = DefinitionProp

# this binding exists because shared behavior needs one stable value
globals()["_definition_tessellation"] = DefinitionA

# this binding exists because shared behavior needs one stable value
globals()["_document_properties"] = DocProperties

# this binding exists because shared behavior needs one stable value
globals()["_document_xml"] = BuildDocXml

# this binding exists because shared behavior needs one stable value
globals()["_document_xml_manifest"] = DocXmlManifest

# this binding exists because shared behavior needs one stable value
globals()["_edge_link_property"] = EdgeLinkProp

# this binding exists because shared behavior needs one stable value
globals()["_element_from_data"] = ElemFromData

# this binding exists because shared behavior needs one stable value
globals()["_enum"] = EnumAction

# this binding exists because shared behavior needs one stable value
globals()["_enumeration_choices_property"] = EnumerationProp

# this binding exists because shared behavior needs one stable value
globals()["_enumeration_property"] = EnumerationProA

# this binding exists because shared behavior needs one stable value
globals()["_expanded_instances"] = Expanded

# this binding exists because shared behavior needs one stable value
globals()["_expression_property"] = ExpressionProp

# this binding exists because shared behavior needs one stable value
globals()["_feature_metadata"] = FeatureMeta

# this binding exists because shared behavior needs one stable value
globals()["_feature_parameter"] = FeatureParam

# this binding exists because shared behavior needs one stable value
globals()["_fillet_edges_data"] = FilletEdgesData

# this binding exists because shared behavior needs one stable value
globals()["_fillet_edges_property"] = FilletEdgesProp

# this binding exists because shared behavior needs one stable value
globals()["_float_property"] = FloatProp

# this binding exists because shared behavior needs one stable value
globals()["_fmt"] = FmtAction

# this binding exists because shared behavior needs one stable value
globals()["_freecad_brep_payload"] = FreecadBrep

# this binding exists because shared behavior needs one stable value
globals()["_geometry_property"] = GeomProp

# this binding exists because shared behavior needs one stable value
globals()["_grounded_joint"] = GroundJointMut

# this binding exists because shared behavior needs one stable value
globals()["_import_component_document"] = ImportCompMut

# this binding exists because shared behavior needs one stable value
globals()["_integer_property"] = IntegerProp

# this binding exists because shared behavior needs one stable value
globals()["_items"] = Items

# this binding exists because shared behavior needs one stable value
globals()["_json_property"] = JsonProp

# this binding exists because shared behavior needs one stable value
globals()["_line_profile_polygon"] = LineProfile

# this binding exists because shared behavior needs one stable value
globals()["_link_list_property"] = LinkListProp

# this binding exists because shared behavior needs one stable value
globals()["_link_property"] = LinkProp

# this binding exists because shared behavior needs one stable value
globals()["_link_sub_list_property"] = LinkSubListProp

# this binding exists because shared behavior needs one stable value
globals()["_manifest_mapping"] = ManifestMapping

# this binding exists because shared behavior needs one stable value
globals()["_mate_joint_type"] = MateJointType

# this binding exists because shared behavior needs one stable value
globals()["_mate_subelements"] = MateSubelements

# this binding exists because shared behavior needs one stable value
globals()["_mate_value"] = MateScalar

# this binding exists because shared behavior needs one stable value
globals()["_matrix_product"] = MatrixProduct

# this binding exists because shared behavior needs one stable value
globals()["_matrix_scale"] = MatrixScale

# this binding exists because shared behavior needs one stable value
globals()["_matrix_transform"] = MatrixTransform

# this binding exists because shared behavior needs one stable value
globals()["_matrix_values"] = MatrixValues

# this binding exists because shared behavior needs one stable value
globals()["_merge_named_property"] = MergeNamedMut

# this binding exists because shared behavior needs one stable value
globals()["_mesh_kernel_data"] = MeshKernelData

# this binding exists because shared behavior needs one stable value
globals()["_mesh_property"] = MeshProp

# this binding exists because shared behavior needs one stable value
globals()["_midpoint_slots"] = MidpointSlots

# this binding exists because shared behavior needs one stable value
globals()["_native_brep_key"] = NativeBrepKey

# this binding exists because shared behavior needs one stable value
globals()["_native_closed_profile_count"] = NativeClosed

# this binding exists because shared behavior needs one stable value
globals()["_native_document_sha256"] = NativeDocShaTwo

# this binding exists because shared behavior needs one stable value
globals()["_native_extensions"] = Native

# this binding exists because shared behavior needs one stable value
globals()["_native_geometry_element"] = NativeGeomElem

# this binding exists because shared behavior needs one stable value
globals()["_native_link_property_name"] = FindLinkProp

# this binding exists because shared behavior needs one stable value
globals()["_native_object"] = NativeObject

# this binding exists because shared behavior needs one stable value
globals()["_native_profiles_are_statically_sound"] = HasNativeProf

# this binding exists because shared behavior needs one stable value
globals()["_native_properties"] = NativeA

# this binding exists because shared behavior needs one stable value
globals()["_native_sketch_analysis"] = NativeSketch

# this binding exists because shared behavior needs one stable value
globals()["_neutral_reference_point"] = NeutralRefPoint

# this binding exists because shared behavior needs one stable value
globals()["_normalize"] = Normalize

# this binding exists because shared behavior needs one stable value
globals()["_number"] = Number

# this binding exists because shared behavior needs one stable value
globals()["_payload_bytes"] = PayloadBytes

# this binding exists because shared behavior needs one stable value
globals()["_payload_extension"] = PayloadSuffix

# this binding exists because shared behavior needs one stable value
globals()["_payload_native_document_sha256"] = PayloadNative

# this binding exists because shared behavior needs one stable value
globals()["_payload_role"] = PayloadRole

# this binding exists because shared behavior needs one stable value
globals()["_placement_property"] = MakePlacement

# this binding exists because shared behavior needs one stable value
globals()["_point2"] = PointTwo

# this binding exists because shared behavior needs one stable value
globals()["_point_on_segment"] = IsPointOnSeg

# this binding exists because shared behavior needs one stable value
globals()["_point_segment_distance"] = PointSegment

# this binding exists because shared behavior needs one stable value
globals()["_points"] = Points

# this binding exists because shared behavior needs one stable value
globals()["_points_close"] = IsPointClose

# this binding exists because shared behavior needs one stable value
globals()["_profile_boundaries_intersect"] = IsProfile

# this binding exists because shared behavior needs one stable value
globals()["_property"] = PropAction

# this binding exists because shared behavior needs one stable value
globals()["_python_proxy_property"] = PythonProxyProp

# this binding exists because shared behavior needs one stable value
globals()["_quaternion"] = Quaternion

# this binding exists because shared behavior needs one stable value
globals()["_raw_constraint_slots"] = RawRuleSlots

# this binding exists because shared behavior needs one stable value
globals()["_reference_point"] = RefPoint

# this binding exists because shared behavior needs one stable value
globals()["_rename_property_links"] = RenamePropLinks

# this binding exists because shared behavior needs one stable value
globals()["_replace_named_property"] = ReplaceNameMut

# this binding exists because shared behavior needs one stable value
globals()["_represented_native_object_names"] = Represented

# this binding exists because shared behavior needs one stable value
globals()["_safe"] = SafeAction

# this binding exists because shared behavior needs one stable value
globals()["_sanitize_payload_references"] = SanitizePayload

# this binding exists because shared behavior needs one stable value
globals()["_segment_orientation"] = Segment

# this binding exists because shared behavior needs one stable value
globals()["_segments_intersect_or_touch"] = HasSegmentTouch

# this binding exists because shared behavior needs one stable value
globals()["_sequence"] = Sequence

# this binding exists because shared behavior needs one stable value
globals()["_serialize_object_data"] = SerializeObject

# this binding exists because shared behavior needs one stable value
globals()["_shape_property"] = ShapeProp

# this binding exists because shared behavior needs one stable value
globals()["_sketch_properties"] = BuildSketch

# this binding exists because shared behavior needs one stable value
globals()["_string_list_property"] = StringListProp

# this binding exists because shared behavior needs one stable value
globals()["_string_property"] = StringProp

# this binding exists because shared behavior needs one stable value
globals()["_tessellation_data"] = Tessellation

# this binding exists because shared behavior needs one stable value
globals()["_text"] = TextAction

# this binding exists because shared behavior needs one stable value
globals()["_triangle_indices"] = TriangleIndices

# this binding exists because shared behavior needs one stable value
globals()["_triangle_is_valid"] = IsTriangleValid

# this binding exists because shared behavior needs one stable value
globals()["_unique_payload_name"] = UniquePayload

# this binding exists because shared behavior needs one stable value
globals()["_validated_archive_members"] = Validated

# this binding exists because shared behavior needs one stable value
globals()["_validated_document_xml"] = ValidatedDocXml

# this binding exists because shared behavior needs one stable value
globals()["_validated_entry_name"] = ValidatedEntry

# this binding exists because shared behavior needs one stable value
globals()["_validated_object_name"] = ValidatedObject

# this binding exists because shared behavior needs one stable value
globals()["_vector"] = Vector

# this binding exists because shared behavior needs one stable value
globals()["_vector_property"] = VectorProp

# this binding exists because shared behavior needs one stable value
globals()["_without_tessellation"] = Without

# this binding exists because shared behavior needs one stable value
globals()["_xlink_property"] = XlinkProp

# this binding exists because shared behavior needs one stable value
globals()["_xlink_sub_property"] = XlinkSubProp

# this binding exists because shared behavior needs one stable value
globals()["_zip_entry"] = ZipEntry

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["base64"] = BaseSixFour

# this binding exists because shared behavior needs one stable value
globals()["brep_model_brep"] = BrepModelBrep

# this binding exists because shared behavior needs one stable value
globals()["build_fcstd_archive"] = BuildFcstdApi

# this binding exists because shared behavior needs one stable value
globals()["copy"] = CopyValue

# this binding exists because shared behavior needs one stable value
globals()["dataclass"] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()["extract_manifest_from_fcstd"] = ExtractManifest

# this binding exists because shared behavior needs one stable value
globals()["field"] = Field

# this binding exists because shared behavior needs one stable value
globals()["hashlib"] = Hashlib

# this binding exists because shared behavior needs one stable value
globals()["io"] = IoStream

# this binding exists because shared behavior needs one stable value
globals()["json"] = JsonValue

# this binding exists because shared behavior needs one stable value
globals()["math"] = MathValue

# this binding exists because shared behavior needs one stable value
globals()["native_expression_parts"] = NativeParts

# this binding exists because shared behavior needs one stable value
globals()["native_shape_feature_count"] = NativeShape

# this binding exists because shared behavior needs one stable value
globals()["native_sketch_carrier_reasons"] = NativeSketchA

# this binding exists because shared behavior needs one stable value
globals()["native_sketch_parts"] = NativeSketchB

# this binding exists because shared behavior needs one stable value
globals()["proven_ascii_brep"] = ProvenAsciiBrep

# this binding exists because shared behavior needs one stable value
globals()["re"] = RegexLib

# this binding exists because shared behavior needs one stable value
globals()["struct"] = Struct

# this binding exists because shared behavior needs one stable value
globals()["triangle_mesh_brep"] = TriangleMeshBrep

# this binding exists because shared behavior needs one stable value
globals()["uuid"] = UuidValue

# this binding exists because shared behavior needs one stable value
globals()["zipfile"] = Zipfile

# this binding exists because shared behavior needs one stable value
globals()["zlib"] = ZlibValue
