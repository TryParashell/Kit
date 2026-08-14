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
    if RegexLib.search(r"[^A-Za-z0-9_.,+\-*/%<>=!&|() \t]", Translated):
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
        return SheetProps(Instance)

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
        setattr(ElemValue, "text", TextValue)
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


# this definition exists because native geometry can arrive through either carrier representation
def NativeGeomData(
    Entity: Mapping[str, Any],
) -> tuple[str, Mapping[str, Any], XmlTree.Element | None, bool]:
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
        SourceFormat = TextAction(GeomValue.get("format_id")).casefold()
        EntityType = TextAction(GeomValue.get("entity_type"))
        Choice = ElemFromData(GeomValue.get("data"))
        if (
            SourceFormat == FormatId
            and Choice is not None
            and (Choice.tag == "Geometry")
            and (Choice.get("type", "") == EntityType)
        ):
            ElemValue = Choice
    return (KindValue, GeomValue, ElemValue, NativeGeom)


# this definition exists because geometry carriers must match the declared neutral kind
def IsValidGeom(KindValue: str, ElemValue: XmlTree.Element | None) -> bool:
    if ElemValue is None or ElemValue.tag != "Geometry":
        return False
    ExpectedTypeIds = GeomTypeIdsByKind.get(KindValue)
    if ExpectedTypeIds is not None and ElemValue.get("type", "") not in ExpectedTypeIds:
        return False
    return KindValue == "native" or ExpectedTypeIds is not None


# this definition exists because line carriers must reflect current neutral endpoints
def PatchLineMut(ElemValue: XmlTree.Element, GeomValue: Mapping[str, Any]) -> None:
    Value = ElemValue.find("./LineSegment")
    if Value is None:
        return
    Start = PointTwo(GeomValue.get("start"))
    EndValue = PointTwo(GeomValue.get("end"))
    Value.set("StartX", FmtAction(Start[0]))
    Value.set("StartY", FmtAction(Start[1]))
    Value.set("EndX", FmtAction(EndValue[0]))
    Value.set("EndY", FmtAction(EndValue[1]))


# this definition exists because circular carriers must reflect current neutral dimensions
def PatchCircleMut(
    ElemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
    Value = ElemValue.find("./Circle" if KindValue == "circle" else "./ArcOfCircle")
    if Value is None:
        return
    Center = PointTwo(GeomValue.get("center"))
    Value.set("CenterX", FmtAction(Center[0]))
    Value.set("CenterY", FmtAction(Center[1]))
    Value.set("Radius", FmtAction(GeomValue.get("radius")))
    if KindValue == "arc":
        Value.set("StartAngle", FmtAction(GeomValue.get("start_angle")))
        Value.set("EndAngle", FmtAction(GeomValue.get("end_angle")))


# this definition exists because point carriers must reflect the current neutral location
def PatchPointMut(ElemValue: XmlTree.Element, GeomValue: Mapping[str, Any]) -> None:
    Value = ElemValue.find("./GeomPoint")
    if Value is None:
        Value = ElemValue.find("./Point")
    if Value is None:
        return
    Point = PointTwo(GeomValue.get("point"))
    Value.set("X", FmtAction(Point[0]))
    Value.set("Y", FmtAction(Point[1]))


# this definition exists because ellipse carriers must reflect current neutral axes
def PatchEllipseMut(
    ElemValue: XmlTree.Element, GeomValue: Mapping[str, Any]
) -> None:
    Value = ElemValue.find("./Ellipse")
    if Value is None:
        return
    Center = PointTwo(GeomValue.get("center"))
    MajorAxis = PointTwo(GeomValue.get("major_axis"))
    Value.set("CenterX", FmtAction(Center[0]))
    Value.set("CenterY", FmtAction(Center[1]))
    if Value.get("AngleXU") is not None:
        Value.set("AngleXU", FmtAction(MathValue.atan2(MajorAxis[1], MajorAxis[0])))
    else:
        Value.set("MajorAxisX", FmtAction(MajorAxis[0]))
        Value.set("MajorAxisY", FmtAction(MajorAxis[1]))
    Value.set("MajorRadius", FmtAction(GeomValue.get("major_radius")))
    Value.set("MinorRadius", FmtAction(GeomValue.get("minor_radius")))


# this definition exists because conic carriers must reflect current neutral parameters
def PatchConicMut(
    ElemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
    TagValue = {
        "arc_ellipse": "ArcOfEllipse",
        "hyperbola": "Hyperbola",
        "arc_hyperbola": "ArcOfHyperbola",
    }[KindValue]
    Value = ElemValue.find(f"./{TagValue}")
    if Value is None:
        return
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


# this definition exists because parabola carriers must reflect current neutral parameters
def PatchParabMut(
    ElemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
    TagValue = "Parabola" if KindValue == "parabola" else "ArcOfParabola"
    Value = ElemValue.find(f"./{TagValue}")
    if Value is None:
        return
    Center = PointTwo(GeomValue.get("center"))
    AxisValue = PointTwo(GeomValue.get("axis"))
    Value.set("CenterX", FmtAction(Center[0]))
    Value.set("CenterY", FmtAction(Center[1]))
    Value.set("AngleXU", FmtAction(MathValue.atan2(AxisValue[1], AxisValue[0])))
    Value.set("Focal", FmtAction(GeomValue.get("focal_length")))
    if KindValue == "arc_parabola":
        Value.set("StartAngle", FmtAction(GeomValue.get("start_angle")))
        Value.set("EndAngle", FmtAction(GeomValue.get("end_angle")))


# this definition exists because spline poles need one canonical weighted encoding
def SplinePoints(
    GeomValue: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[float]]:
    Points = Items(GeomValue.get("control_points", []))
    Weights = [Number(Value, 1.0) for Value in Sequence(GeomValue.get("weights", []))]
    if len(Weights) != len(Points):
        Weights = [1.0] * len(Points)
    return (Points, Weights)


# this definition exists because spline knot defaults must remain deterministic
def SplineKnots(
    GeomValue: Mapping[str, Any], PointCount: int
) -> tuple[int, list[float], list[int]]:
    Degree = max(
        1, min(int(Number(GeomValue.get("degree"), 3)), max(1, PointCount - 1))
    )
    Knots = [Number(Value) for Value in Sequence(GeomValue.get("knots", []))]
    Multiplicities = [
        int(Number(Value, 1))
        for Value in Sequence(GeomValue.get("multiplicities", []))
    ]
    if not Knots or len(Multiplicities) != len(Knots):
        InteriorCount = max(0, PointCount - Degree - 1)
        Knots = [float(Value) for Value in range(InteriorCount + 2)]
        Multiplicities = [Degree + 1] + [1] * InteriorCount + [Degree + 1]
    return (Degree, Knots, Multiplicities)


# this definition exists because spline poles must retain their original ordering
def AddPolesMut(
    Curve: XmlTree.Element, Points: list[dict[str, Any]], Weights: list[float]
) -> None:
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


# this definition exists because spline knots must retain their original ordering
def AddKnotsMut(
    Curve: XmlTree.Element, Knots: list[float], Multiplicities: list[int]
) -> None:
    for KnotValue, Multiplicity in zip(Knots, Multiplicities, strict=True):
        XmlTree.SubElement(
            Curve,
            "Knot",
            {"Value": FmtAction(KnotValue), "Mult": str(Multiplicity)},
        )


# this definition exists because spline carriers must reflect current neutral controls
def PatchSplineMut(
    ElemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
    Curve = ElemValue.find(
        "./BezierCurve" if KindValue == "bezier" else "./BSplineCurve"
    )
    if Curve is None:
        return
    Points, Weights = SplinePoints(GeomValue)
    Curve[:] = [Child for Child in Curve if Child.tag not in SplineControlTags]
    Curve.set("PolesCount", str(len(Points)))
    AddPolesMut(Curve, Points, Weights)
    if KindValue != "spline":
        return
    Degree, Knots, Multiplicities = SplineKnots(GeomValue, len(Points))
    Curve.set("KnotsCount", str(len(Knots)))
    Curve.set("Degree", str(Degree))
    Curve.set("IsPeriodic", "1" if bool(GeomValue.get("periodic")) else "0")
    AddKnotsMut(Curve, Knots, Multiplicities)


# this definition exists because carrier patching dispatches each geometry family explicitly
def PatchNativeMut(
    ElemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
    if KindValue == "line":
        PatchLineMut(ElemValue, GeomValue)
    elif KindValue in CircularGeomKinds:
        PatchCircleMut(ElemValue, GeomValue, KindValue)
    elif KindValue == "point":
        PatchPointMut(ElemValue, GeomValue)
    elif KindValue == "ellipse":
        PatchEllipseMut(ElemValue, GeomValue)
    elif KindValue in {"arc_ellipse", "hyperbola", "arc_hyperbola"}:
        PatchConicMut(ElemValue, GeomValue, KindValue)
    elif KindValue in {"parabola", "arc_parabola"}:
        PatchParabMut(ElemValue, GeomValue, KindValue)
    elif KindValue in SplineGeomKinds:
        PatchSplineMut(ElemValue, GeomValue, KindValue)


# this definition exists because native sketch geometry must preserve valid vendor markup
def NativeGeomElem(Entity: Mapping[str, Any]) -> XmlTree.Element | None:
    KindValue, GeomValue, ElemValue, NativeGeom = NativeGeomData(Entity)
    if not IsValidGeom(KindValue, ElemValue):
        return None
    assert ElemValue is not None
    if not NativeGeom:
        PatchNativeMut(ElemValue, GeomValue, KindValue)
    Construction = ElemValue.find("./Construction")
    if Construction is not None:
        Construction.set("value", "1" if bool(Entity.get("construction")) else "0")
    return ElemValue


# this definition exists because profile geometry needs a reusable closed membership index
def ClosedGeomIds(Sketch: Mapping[str, Any]) -> set[str]:
    return {
        TextAction(EntityId)
        for Profile in Sequence(Sketch.get("closed_profile_entity_ids", []))
        for EntityId in Sequence(Profile)
        if TextAction(EntityId)
    }


# this definition exists because unsupported sketch geometry needs structured transfer evidence
def GeomDiagnostic(
    EntityId: str, KindValue: str, GeomType: str, TypeId: str | None
) -> dict[str, AnyValue]:
    ExpectedType = NeutralGeomTypeByKind.get(KindValue)
    SourceOpaque = GeomType == "NativeGeometry" or bool(
        TypeId is not None and GeomType and GeomType != ExpectedType
    )
    return {
        "carrier_reason": "source_opaque" if SourceOpaque else "writer_unimplemented",
        "code": "freecad.sketch_geometry_carrier_only",
        "entity_id": EntityId,
        "kind": KindValue,
        "mode": "carrier_only",
        "reason": "native FreeCAD geometry data is unavailable",
        "severity": "warning",
    }


# this definition exists because neutral line geometry needs canonical freecad coordinates
def AddLineGeomMut(ItemValue: XmlTree.Element, GeomValue: Mapping[str, Any]) -> None:
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


# this definition exists because neutral circle geometry needs canonical freecad coordinates
def AddCircleMut(
    ItemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
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
    XmlTree.SubElement(
        ItemValue, "ArcOfCircle" if KindValue == "arc" else "Circle", Attributes
    )


# this definition exists because neutral ellipse geometry needs canonical freecad coordinates
def AddEllipseMut(ItemValue: XmlTree.Element, GeomValue: Mapping[str, Any]) -> None:
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


# this definition exists because neutral conic geometry needs canonical freecad coordinates
def AddConicGeomMut(
    ItemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
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


# this definition exists because neutral parabola geometry needs canonical freecad coordinates
def AddParabGeomMut(
    ItemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
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


# this definition exists because neutral spline geometry needs canonical freecad controls
def AddSplineMut(
    ItemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
    Points, Weights = SplinePoints(GeomValue)
    if KindValue == "bezier":
        Curve = XmlTree.SubElement(
            ItemValue, "BezierCurve", {"PolesCount": str(len(Points))}
        )
        AddPolesMut(Curve, Points, Weights)
        return
    Degree, Knots, Multiplicities = SplineKnots(GeomValue, len(Points))
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
    AddPolesMut(Curve, Points, Weights)
    AddKnotsMut(Curve, Knots, Multiplicities)


# this definition exists because neutral point geometry needs canonical freecad coordinates
def AddPointGeomMut(ItemValue: XmlTree.Element, GeomValue: Mapping[str, Any]) -> None:
    Point = PointTwo(GeomValue.get("point", GeomValue.get("center")))
    XmlTree.SubElement(
        ItemValue,
        "GeomPoint",
        {"X": FmtAction(Point[0]), "Y": FmtAction(Point[1]), "Z": FmtAction(0)},
    )


# this definition exists because neutral geometry dispatch must remain explicit and exhaustive
def AddGeomBodyMut(
    ItemValue: XmlTree.Element, GeomValue: Mapping[str, Any], KindValue: str
) -> None:
    if KindValue == "line":
        AddLineGeomMut(ItemValue, GeomValue)
    elif KindValue in CircularGeomKinds:
        AddCircleMut(ItemValue, GeomValue, KindValue)
    elif KindValue == "ellipse":
        AddEllipseMut(ItemValue, GeomValue)
    elif KindValue in {"arc_ellipse", "hyperbola", "arc_hyperbola"}:
        AddConicGeomMut(ItemValue, GeomValue, KindValue)
    elif KindValue in {"parabola", "arc_parabola"}:
        AddParabGeomMut(ItemValue, GeomValue, KindValue)
    elif KindValue in SplineGeomKinds:
        AddSplineMut(ItemValue, GeomValue, KindValue)
    elif KindValue == "point":
        AddPointGeomMut(ItemValue, GeomValue)


# this definition exists because every neutral geometry item needs canonical extension metadata
def AddNeutralMut(
    GeomList: XmlTree.Element,
    Entity: Mapping[str, Any],
    EntityId: str,
    KindValue: str,
    GeomValue: Mapping[str, Any],
    TypeId: str,
    ClosedIds: set[str],
) -> None:
    Index = len(GeomList)
    ItemValue = XmlTree.SubElement(
        GeomList, "Geometry", {"type": TypeId, "id": str(Index + 1), "migrated": "1"}
    )
    Extensions = XmlTree.SubElement(ItemValue, "GeoExtensions", {"count": "1"})
    Construction = bool(Entity.get("construction")) or (
        bool(ClosedIds) and EntityId not in ClosedIds
    )
    Flags = "00000000000000000000000000000010" if Construction else "0" * 32
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
    AddGeomBodyMut(ItemValue, GeomValue, KindValue)
    XmlTree.SubElement(
        ItemValue, "Construction", {"value": "1" if Construction else "0"}
    )


# this definition exists because one geometry transfer should update all correlated indexes
def AppendGeomMut(
    GeomList: XmlTree.Element,
    IndicesMut: dict[str, int],
    DiagnosticsMut: list[dict[str, AnyValue]],
    ClosedIds: set[str],
    SourceIndex: int,
    Entity: Mapping[str, Any],
) -> None:
    EntityId = TextAction(Entity.get("id"), str(SourceIndex))
    KindValue = TextAction(EnumAction(Entity.get("kind"))).lower()
    NativeItem = NativeGeomElem(Entity)
    if NativeItem is not None:
        IndicesMut[EntityId] = len(GeomList)
        GeomList.append(NativeItem)
        return
    GeomValue = Entity.get("geometry", {})
    if not isinstance(GeomValue, Mapping):
        GeomValue = {}
    GeomType = TextAction(GeomValue.get("$type"))
    TypeId = NeutralGeomTypeIdByKind.get(KindValue)
    ExpectedType = NeutralGeomTypeByKind.get(KindValue)
    if TypeId is None or GeomType == "NativeGeometry" or (
        GeomType and GeomType != ExpectedType
    ):
        DiagnosticsMut.append(GeomDiagnostic(EntityId, KindValue, GeomType, TypeId))
        return
    IndicesMut[EntityId] = len(GeomList)
    AddNeutralMut(GeomList, Entity, EntityId, KindValue, GeomValue, TypeId, ClosedIds)


# this definition exists because sketch geometry property assembly coordinates native and neutral items
def GeomProp(
    Sketch: Mapping[str, Any],
) -> tuple[XmlTree.Element, dict[str, int], list[dict[str, AnyValue]]]:
    Result = PropAction("Geometry", "Part::PropertyGeometryList", Status="8192")
    GeomList = XmlTree.SubElement(Result, "GeometryList", {"count": "0"})
    Indices: dict[str, int] = {}
    Diagnostics: list[dict[str, AnyValue]] = []
    ClosedIds = ClosedGeomIds(Sketch)
    for SourceIndex, Entity in enumerate(Items(Sketch.get("entities", []))):
        AppendGeomMut(
            GeomList, Indices, Diagnostics, ClosedIds, SourceIndex, Entity
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


# this definition exists because two reference midpoint rules need directional line detection
def MidpointPair(
    References: list[dict[str, Any]],
    Indices: Mapping[str, int],
    Entities: Mapping[str, Mapping[str, Any]],
) -> list[tuple[int, int]] | None:
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
            or LineId not in Indices
            or PointId not in Indices
        ):
            continue
        PointPosition = RefPoint(PointRef.get("point"))
        if PointPosition == 0 and TextAction(
            EnumAction(Point.get("kind"))
        ).casefold() == "point":
            PointPosition = 1
        if PointPosition:
            return [
                (Indices[LineId], 1),
                (Indices[LineId], 2),
                (Indices[PointId], PointPosition),
            ]
    return None


# this definition exists because three reference midpoint rules need explicit endpoint grouping
def MidpointTriple(
    References: list[dict[str, Any]],
    Indices: Mapping[str, int],
    Entities: Mapping[str, Mapping[str, Any]],
) -> list[tuple[int, int]] | None:
    Resolved = [
        (TextAction(RefValue.get("entity_id")), RefPoint(RefValue.get("point")))
        for RefValue in References
    ]
    for LineId, LineValue in Entities.items():
        if TextAction(EnumAction(LineValue.get("kind"))).casefold() != "line" or (
            LineId not in Indices
        ):
            continue
        LinePoints = [Point for EntityId, Point in Resolved if EntityId == LineId]
        Others = [(EntityId, Point) for EntityId, Point in Resolved if EntityId != LineId]
        if sorted(LinePoints) != [1, 2] or len(Others) != 1:
            continue
        PointId, PointPosition = Others[0]
        Point = Entities.get(PointId, {})
        if PointPosition == 0 and TextAction(
            EnumAction(Point.get("kind"))
        ).casefold() == "point":
            PointPosition = 1
        if PointId in Indices and PointPosition:
            return [
                (Indices[LineId], 1),
                (Indices[LineId], 2),
                (Indices[PointId], PointPosition),
            ]
    return None


# this definition exists because midpoint constraints accept two native reference layouts
def MidpointSlots(
    RuleValue: Mapping[str, Any],
    Indices: Mapping[str, int],
    Entities: Mapping[str, Mapping[str, Any]],
) -> list[tuple[int, int]] | None:
    References = Items(RuleValue.get("references", []))
    if len(References) == 2:
        return MidpointPair(References, Indices, Entities)
    if len(References) == 3:
        return MidpointTriple(References, Indices, Entities)
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


# this class exists because constraint conversion coordinates correlated mutable collections
@Dataclass
class RuleState:
    EntityItems: list[dict[str, Any]]
    Entities: dict[str, Mapping[str, Any]]
    Encoded: list[dict[str, AnyValue]]
    Expressions: list[tuple[str, str]]
    Dependencies: list[str]
    Diagnostics: list[dict[str, AnyValue]]
    RuleNames: set[str]
    FixedEntities: set[str]
    ProfileIds: set[str]
    Indices: Mapping[str, int]
    Parameters: _Parameters
    ProfileOnly: bool


# this definition exists because constraint conversion state must share one entity index
def CreateRuleState(
    Sketch: Mapping[str, Any],
    Indices: Mapping[str, int],
    Parameters: _Parameters,
    ProfileOnly: bool,
) -> RuleState:
    EntityItems = Items(Sketch.get("entities", []))
    Entities = {TextAction(Entity.get("id")): Entity for Entity in EntityItems}
    ProfileIds = {
        TextAction(EntityId)
        for Profile in Sequence(Sketch.get("closed_profile_entity_ids", []))
        for EntityId in Sequence(Profile)
        if TextAction(EntityId)
    }
    return RuleState(
        EntityItems,
        Entities,
        [],
        [],
        [],
        [],
        set(),
        set(),
        ProfileIds,
        Indices,
        Parameters,
        ProfileOnly,
    )


# this definition exists because profile replay activates only statically proven constraints
def IsProfileRule(
    RuleValue: Mapping[str, Any],
    KindValue: str,
    References: list[dict[str, Any]],
    State: RuleState,
) -> bool:
    if not State.ProfileOnly:
        return True
    RefEntities = [
        State.Entities.get(TextAction(RefValue.get("entity_id")), {})
        for RefValue in References
    ]
    RefKinds = [
        TextAction(EnumAction(Entity.get("kind"))).casefold()
        for Entity in RefEntities
    ]
    RefPoints = [TextAction(Value.get("point")).casefold() for Value in References]
    ProfileRefs = bool(References) and all(
        TextAction(Value.get("entity_id")) in State.ProfileIds for Value in References
    )
    Linear = (
        KindValue in {"horizontal", "vertical"}
        and len(References) == 1
        and RefKinds == ["line"]
        and RefPoints == [""]
    )
    Coincident = KindValue == "coincident" and len(References) == 2 and all(RefPoints)
    Radial = (
        KindValue in {"radius", "diameter"}
        and len(References) == 1
        and RefKinds == ["circle"]
        and RefPoints == [""]
    )
    return ProfileRefs and (Linear or Coincident or Radial)


# this definition exists because native constraint metadata has two supported layouts
def RuleSources(
    RuleValue: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any], Any, bool]:
    SourceAttrs = RuleValue.get("attributes", {})
    if not isinstance(SourceAttrs, Mapping):
        SourceAttrs = {}
    RawAttrs = SourceAttrs.get("freecad", {})
    if not isinstance(RawAttrs, Mapping):
        RawAttrs = {}
    SourceCode = SourceAttrs.get("freecad_type_code", RawAttrs.get("Type"))
    return (SourceAttrs, RawAttrs, SourceCode, SourceCode is not None or bool(RawAttrs))


# this definition exists because constraint carrier diagnostics share one stable schema
def AddRuleDiagMut(
    State: RuleState,
    RuleValue: Mapping[str, Any],
    KindValue: str,
    Reason: str,
    NativeRule: bool,
) -> None:
    State.Diagnostics.append(
        RuleDiag(
            RuleValue,
            KindValue,
            "freecad.sketch_constraint_carrier_only",
            "carrier_only",
            Reason,
            "warning",
            CarrierReason=RuleCarrier(RuleValue, NativeRule),
        )
    )


# this definition exists because midpoint rules require a composed native type
def RuleCodeData(
    RuleValue: Mapping[str, Any],
    KindValue: str,
    SourceCode: Any,
    State: RuleState,
) -> tuple[int | None, list[tuple[int, int]] | None, tuple[str, str] | None, str]:
    if KindValue == "midpoint" and SourceCode is None:
        Resolved = MidpointSlots(RuleValue, State.Indices, State.Entities)
        Composition = (
            "Symmetric",
            "encoded as symmetry between a line's endpoints and the referenced point",
        )
        Reason = (
            ""
            if Resolved is not None
            else "the midpoint relationship cannot be expressed as a sound FreeCAD symmetry constraint"
        )
        return (14, Resolved, Composition, Reason)
    CodeValue = (
        int(Number(SourceCode, -1))
        if SourceCode is not None
        else RuleCodeByKind.get(KindValue)
    )
    Reason = (
        "no equivalent FreeCAD constraint type is available"
        if CodeValue is None or CodeValue < 0
        else ""
    )
    return (CodeValue, None, None, Reason)


# this definition exists because stored reference slots need one normalized tuple representation
def StoredRuleSlots(
    SourceAttrs: Mapping[str, Any], RawAttrs: Mapping[str, Any]
) -> list[tuple[int, int, str]]:
    SourceSlots = Items(SourceAttrs.get("freecad_reference_slots", []))
    if SourceSlots:
        return [
            (
                int(Number(Value.get("freecad_geometry_index"), -2000)),
                int(Number(Value.get("freecad_point_index"))),
                TextAction(Value.get("entity_id")),
            )
            for Value in SourceSlots
        ]
    if RawAttrs:
        return [
            (EntityIndex, PointIndex, "")
            for EntityIndex, PointIndex in RawRuleSlots(RawAttrs)
        ]
    return []


# this definition exists because stored native slots must map through reordered geometry
def ResolveStored(
    Slots: list[tuple[int, int, str]], State: RuleState
) -> list[tuple[int, int]]:
    Resolved: list[tuple[int, int]] = []
    for EntityIndex, PointIndex, EntityId in Slots:
        if EntityIndex < 0:
            Resolved.append((EntityIndex, PointIndex))
            continue
        TargetId = EntityId
        if not TargetId and EntityIndex < len(State.EntityItems):
            TargetId = TextAction(State.EntityItems[EntityIndex].get("id"))
        TargetIndex = State.Indices.get(TargetId)
        if TargetIndex is None:
            return []
        Resolved.append((TargetIndex, PointIndex))
    return Resolved


# this definition exists because neutral references must map through the emitted geometry index
def ResolveNeutral(
    References: list[dict[str, Any]], KindValue: str, State: RuleState
) -> list[tuple[int, int]]:
    Resolved: list[tuple[int, int]] = []
    for RefValue in References:
        EntityId = TextAction(RefValue.get("entity_id"))
        EntityIndex = State.Indices.get(EntityId)
        if EntityIndex is None:
            return []
        PointIndex = NeutralRefPoint(
            KindValue, State.Entities.get(EntityId, {}), RefValue.get("point")
        )
        Resolved.append((EntityIndex, PointIndex))
    return Resolved


# this definition exists because composed constraints need sound reference cardinality
def ComposeRule(
    KindValue: str,
    NativeRule: bool,
    Resolved: list[tuple[int, int]],
    Composition: tuple[str, str] | None,
) -> tuple[list[tuple[int, int]], tuple[str, str] | None]:
    if KindValue == "concentric" and not NativeRule:
        if len(Resolved) != 2:
            return ([], Composition)
        Resolved = [(Resolved[0][0], 3), (Resolved[1][0], 3)]
        Composition = (
            "Coincident",
            "encoded as coincidence between the referenced curve centers",
        )
    elif KindValue == "fixed" and not NativeRule:
        if len(Resolved) != 1 or Resolved[0][1] != 0:
            return ([], Composition)
        Composition = ("Block", "encoded using FreeCAD's block constraint")
    return (Resolved, Composition)


# this definition exists because every encoded constraint needs a collision free name
def RuleNameMut(
    RuleValue: Mapping[str, Any],
    RawAttrs: Mapping[str, Any],
    NativeRule: bool,
    RuleNamesMut: set[str],
) -> str:
    if NativeRule and "Name" in RawAttrs:
        NameValue = TextAction(RawAttrs.get("Name"))
    else:
        NameBase = SafeAction(RuleValue.get("id"), "Constraint")
        NameValue = NameBase
        Suffix = 2
        while NameValue in RuleNamesMut:
            NameValue = f"{NameBase}_{Suffix}"
            Suffix += 1
    if NameValue:
        RuleNamesMut.add(NameValue)
    return NameValue


# this definition exists because encoded rule records feed both xml and expression assembly
def RuleRecord(
    RuleValue: Mapping[str, Any],
    CodeValue: int,
    Value: float,
    NameValue: str,
    Resolved: list[tuple[int, int]],
    RawAttrs: Mapping[str, Any],
) -> dict[str, AnyValue]:
    Elements = Resolved + [(-2000, 0)] * max(0, 3 - len(Resolved))
    Values = Elements[:3]
    return {
        "name": NameValue,
        "type": CodeValue,
        "value": Value,
        "driving": bool(RuleValue.get("driving", True)),
        "active": not bool(RuleValue.get("suppressed")),
        "first": Values[0],
        "second": Values[1],
        "third": Values[2],
        "elements": Elements,
        "attributes": RawAttrs,
    }


# this definition exists because dimensional rules can remain linked to parameter expressions
def AddRuleExprMut(
    State: RuleState,
    RuleValue: Mapping[str, Any],
    ParamId: str,
    CodeValue: int,
    NameValue: str,
    NativeRule: bool,
) -> None:
    Expression = (
        State.Parameters.expression(ParamId)
        if not NativeRule or State.Parameters.has_source_expression(ParamId)
        else None
    )
    if not Expression or not bool(RuleValue.get("driving", True)) or (
        CodeValue not in DimensionalRuleCodes
    ):
        return
    SourcePath = State.Parameters.source_path(ParamId)
    PathValue = (
        f".{SourcePath}" if NativeRule and SourcePath else f".Constraints.{NameValue}"
    )
    State.Expressions.append((PathValue, Expression))
    State.Dependencies.append("Parameters")


# this definition exists because one source constraint updates all correlated transfer state
def AppendRuleMut(State: RuleState, RuleValue: Mapping[str, Any]) -> None:
    KindValue = TextAction(EnumAction(RuleValue.get("kind"))).lower()
    References = Items(RuleValue.get("references", []))
    if not IsProfileRule(RuleValue, KindValue, References, State):
        AddRuleDiagMut(
            State,
            RuleValue,
            KindValue,
            "the source relationship is preserved without activating an unproven solver encoding",
            True,
        )
        return
    SourceAttrs, RawAttrs, SourceCode, NativeRule = RuleSources(RuleValue)
    CodeValue, Resolved, Composition, Reason = RuleCodeData(
        RuleValue, KindValue, SourceCode, State
    )
    if Reason:
        AddRuleDiagMut(State, RuleValue, KindValue, Reason, NativeRule)
        return
    assert CodeValue is not None
    if Resolved is None:
        Stored = StoredRuleSlots(SourceAttrs, RawAttrs)
        Resolved = (
            ResolveStored(Stored, State)
            if Stored
            else ResolveNeutral(References, KindValue, State)
        )
        Resolved, Composition = ComposeRule(
            KindValue, NativeRule, Resolved, Composition
        )
    if not Resolved:
        AddRuleDiagMut(
            State,
            RuleValue,
            KindValue,
            "the constraint has no sound native reference encoding",
            NativeRule,
        )
        return
    AddEncodedMut(
        State,
        RuleValue,
        KindValue,
        SourceAttrs,
        RawAttrs,
        NativeRule,
        CodeValue,
        Resolved,
        Composition,
    )


# this definition exists because successful constraint encoding updates values diagnostics and links
def AddEncodedMut(
    State: RuleState,
    RuleValue: Mapping[str, Any],
    KindValue: str,
    SourceAttrs: Mapping[str, Any],
    RawAttrs: Mapping[str, Any],
    NativeRule: bool,
    CodeValue: int,
    Resolved: list[tuple[int, int]],
    Composition: tuple[str, str] | None,
) -> None:
    ParamId = TextAction(RuleValue.get("parameter_id"))
    DefaultValue = Number(
        RuleValue.get("value"),
        Number(SourceAttrs.get("native_value"), Number(RawAttrs.get("Value"))),
    )
    Value = State.Parameters.value(ParamId, DefaultValue)
    NameValue = RuleNameMut(RuleValue, RawAttrs, NativeRule, State.RuleNames)
    State.Encoded.append(
        RuleRecord(RuleValue, CodeValue, Value, NameValue, Resolved, RawAttrs)
    )
    if KindValue in FixedRuleKinds:
        State.FixedEntities.update(
            TextAction(Value.get("entity_id")) for Value in Items(RuleValue.get("references", []))
        )
    if Composition is not None:
        State.Diagnostics.append(
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
    AddRuleExprMut(State, RuleValue, ParamId, CodeValue, NameValue, NativeRule)


# this definition exists because fixed entities need a fallback block constraint
def AddFixedMut(State: RuleState) -> None:
    for Entity in State.EntityItems:
        EntityId = TextAction(Entity.get("id"))
        if State.ProfileOnly or not bool(Entity.get("fixed")) or (
            EntityId in State.FixedEntities or EntityId not in State.Indices
        ):
            continue
        FirstSlot = (State.Indices[EntityId], 0)
        State.Encoded.append(
            {
                "name": f"fixed_{EntityId}",
                "type": 17,
                "value": 0.0,
                "driving": True,
                "active": True,
                "first": FirstSlot,
                "second": (-2000, 0),
                "third": (-2000, 0),
                "elements": [FirstSlot, (-2000, 0), (-2000, 0)],
                "attributes": {},
            }
        )


# this definition exists because constraint records need canonical freecad xml attributes
def RuleXmlAttrs(ItemValue: Mapping[str, Any]) -> dict[str, str]:
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
            "ElementIds": " ".join(str(Value[0]) for Value in Elements),
            "ElementPositions": " ".join(str(Value[1]) for Value in Elements),
        }
    )
    return Attributes


# this definition exists because encoded constraints need one ordered property container
def BuildRuleProp(Encoded: list[dict[str, AnyValue]]) -> XmlTree.Element:
    Result = PropAction("Constraints", "Sketcher::PropertyConstraintList")
    RuleList = XmlTree.SubElement(
        Result, "ConstraintList", {"count": str(len(Encoded))}
    )
    for ItemValue in Encoded:
        XmlTree.SubElement(RuleList, "Constrain", RuleXmlAttrs(ItemValue))
    return Result


# this definition exists because sketch constraints coordinate native encoding diagnostics and links
def ConstraintsProp(
    Sketch: Mapping[str, Any],
    Indices: Mapping[str, int],
    Parameters: _Parameters,
    ProfileOnly: bool = False,
) -> tuple[
    XmlTree.Element, list[tuple[str, str]], list[str], list[dict[str, AnyValue]]
]:
    State = CreateRuleState(Sketch, Indices, Parameters, ProfileOnly)
    for RuleValue in Items(Sketch.get("constraints", [])):
        AppendRuleMut(State, RuleValue)
    AddFixedMut(State)
    return (
        BuildRuleProp(State.Encoded),
        State.Expressions,
        State.Dependencies,
        State.Diagnostics,
    )


# this definition exists because native sketch metadata may be absent or malformed
def SketchCarrier(Sketch: Mapping[str, Any]) -> Mapping[str, Any]:
    SketchAttrs = Sketch.get("attributes", {})
    NativeObject = (
        SketchAttrs.get("freecad", {}) if isinstance(SketchAttrs, Mapping) else {}
    )
    return NativeObject if isinstance(NativeObject, Mapping) else {}


# this definition exists because sketch transfer warnings share one optional property
def SketchDiagProp(
    GeomDiagnostics: list[dict[str, AnyValue]],
    RuleDiagnostics: list[dict[str, AnyValue]],
) -> XmlTree.Element | None:
    Diagnostics = [*GeomDiagnostics, *RuleDiagnostics]
    return JsonProp("KitSketchDiagnosticsJSON", Diagnostics) if Diagnostics else None


# this definition exists because native sketch links must track rewritten object names
def SketchLinks(Properties: list[XmlTree.Element], PlaneName: str) -> list[str]:
    Attachment = next(
        (Value for Value in Properties if Value.get("name") == "AttachmentSupport"),
        None,
    )
    if Attachment is not None and PlaneName:
        for LinkValue in Attachment.findall(".//Link"):
            LinkValue.set("obj", PlaneName)
    Dependencies = [PlaneName]
    Outer = next(
        (Value for Value in Properties if Value.get("name") == "ExternalGeometry"),
        None,
    )
    if Outer is not None:
        Dependencies.extend(
            Target
            for LinkValue in Outer.findall(".//Link")
            if (Target := TextAction(LinkValue.get("obj")))
        )
    return Dependencies


# this definition exists because native sketch properties need selective semantic replacement
def PatchSketchMut(
    Sketch: Mapping[str, Any],
    NativeObject: Mapping[str, Any],
    PlaneName: str,
    Transform: Mapping[str, Any],
    GeomValue: XmlTree.Element,
    Constraints: XmlTree.Element,
    DiagnosticsProp: XmlTree.Element | None,
    PreserveNative: bool,
) -> tuple[list[XmlTree.Element], list[str]]:
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
    Dependencies = SketchLinks(Properties, PlaneName)
    if not PreserveNative:
        Properties.extend(
            [
                LinkProp("SupportPlane", PlaneName, Dynamic=True),
                StringProp("KitId", Sketch.get("id"), Dynamic=True),
                JsonProp("ClosedProfilesJSON", Sketch.get("closed_profile_entity_ids", [])),
                JsonProp("SourceSketchJSON", Sketch),
            ]
        )
    return (Properties, Dependencies)


# this definition exists because neutral sketches need one canonical property sequence
def NeutralSketch(
    Sketch: Mapping[str, Any],
    PlaneName: str,
    Transform: Mapping[str, Any],
    GeomValue: XmlTree.Element,
    Constraints: XmlTree.Element,
    Expressions: list[tuple[str, str]],
    DiagnosticsProp: XmlTree.Element | None,
) -> list[XmlTree.Element]:
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
    return Properties


# this definition exists because sketch assembly coordinates geometry constraints and plane links
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
    DiagnosticsProp = SketchDiagProp(GeomDiagnostics, RuleDiagnostics)
    NativeObject = SketchCarrier(Sketch)
    NativeProperties = (
        NativeObject.get("properties", {}) if isinstance(NativeObject, Mapping) else {}
    )
    if isinstance(NativeProperties, Mapping) and NativeProperties:
        return PatchSketchMut(
            Sketch,
            NativeObject,
            PlaneName,
            Transform,
            GeomValue,
            Constraints,
            DiagnosticsProp,
            PreserveNative,
        )
    Expressions.append(("Placement", f"{PlaneName}.Placement"))
    Dependencies.append(PlaneName)
    return (
        NeutralSketch(
            Sketch,
            PlaneName,
            Transform,
            GeomValue,
            Constraints,
            Expressions,
            DiagnosticsProp,
        ),
        Dependencies,
    )


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


# this definition exists because profile lines need validated nondegenerate endpoints
def ProfileSegments(
    Entities: list[Mapping[str, Any]],
) -> list[tuple[tuple[float, float], tuple[float, float]]] | None:
    Segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for Entity in Entities:
        GeomValue = Entity.get("geometry", {})
        if not isinstance(GeomValue, Mapping):
            return None
        Start = PointTwo(GeomValue.get("start"))
        EndValue = PointTwo(GeomValue.get("end"))
        if IsPointClose(Start, EndValue):
            return None
        Segments.append((Start, EndValue))
    return Segments


# this definition exists because unordered profile lines need one continuous vertex loop
def OrderedProfile(
    Segments: list[tuple[tuple[float, float], tuple[float, float]]],
) -> list[tuple[float, float]] | None:
    Remaining = list(Segments)
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
    return Points


# this definition exists because degenerate profile loops cannot define a solid face
def HasProfileArea(Points: list[tuple[float, float]]) -> bool:
    AreaValue = sum(
        First[0] * Second[1] - Second[0] * First[1]
        for First, Second in zip(Points, Points[1:] + Points[:1], strict=True)
    )
    return abs(AreaValue) > 1e-09


# this definition exists because self intersecting profile loops cannot define a solid face
def HasProfileCross(Points: list[tuple[float, float]]) -> bool:
    Segments = list(zip(Points, Points[1:] + Points[:1], strict=True))
    for FirstIndex, First in enumerate(Segments):
        for SecondIndex in range(FirstIndex + 1, len(Segments)):
            if SecondIndex in {FirstIndex + 1, (FirstIndex - 1) % len(Segments)}:
                continue
            if HasSegmentTouch(*First, *Segments[SecondIndex]):
                return True
    return False


# this definition exists because profile validation must reject gaps degeneracy and intersections
def LineProfile(
    Entities: list[Mapping[str, Any]],
) -> tuple[tuple[float, float], ...] | None:
    Segments = ProfileSegments(Entities)
    if Segments is None:
        return None
    Points = OrderedProfile(Segments)
    if Points is None or not HasProfileArea(Points) or HasProfileCross(Points):
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
def BuildBrepKey(
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
    TrustedNativeBreps: frozenset[KNativeBrepKey] = frozenset(),
) -> bytes | None:
    if TextAction(Payload.get("format_id")).casefold() not in FreecadBrepFormatIds:
        return None
    PayloadNativeDocShaTwoSix = PayloadNative(Payload)
    if PayloadNativeDocShaTwoSix:
        NativeDocShaTwoFiveSix = PayloadNativeDocShaTwoSix
    if BuildBrepKey(Payload, DataValue, NativeDocShaTwoFiveSix) in TrustedNativeBreps:
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


# this definition exists because mesh triangles need deterministic manifold adjacency metadata
def MeshNeighbors(Triangles: list[tuple[int, int, int]]) -> list[list[int]]:
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
    return Neighbors


# this definition exists because freecad mesh payloads require adjacency bounds and stable framing
def MeshKernelData(
    Vertices: list[tuple[float, float, float]], Triangles: list[tuple[int, int, int]]
) -> bytes:
    Neighbors = MeshNeighbors(Triangles)
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


# this definition exists because imported components must be rendered through the same document writer
def ImportArchive(
    DocValue: Mapping[str, Any], TrustedNativeBreps: frozenset[KNativeBrepKey]
) -> tuple[XmlTree.Element, dict[str, bytes]]:
    Canonical = JsonValue.dumps(
        DocValue, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    Digest = Hashlib.sha256(Canonical.encode("utf-8")).hexdigest()
    DocXml, ChildPayloads = BuildDocXml(
        DocValue, "", Digest, TrustedNativeBreps=TrustedNativeBreps
    )
    return (XmlTree.fromstring(DocXml), ChildPayloads)


# this definition exists because imported document nodes need indexed data and dependency lookup
def ImportNodes(
    RootValue: XmlTree.Element,
) -> tuple[
    list[XmlTree.Element], dict[str, XmlTree.Element], dict[str, list[str]]
]:
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
    return (ObjectNodes, DataNodes, Dependencies)


# this definition exists because imported metadata identifies preferred visible shape targets
def ImportTargets(DataNodes: Mapping[str, XmlTree.Element]) -> tuple[str, str]:
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
    return (OuterOld, FinalOld)


# this definition exists because imported object names must remain unique within the parent graph
def ImportNamesMut(
    Graph: _Graph, Included: list[XmlTree.Element], Prefix: str
) -> dict[str, str]:
    return {
        NodeValue.get("name", ""): Graph.unique(
            f"{Prefix}_{NodeValue.get('name', '')}", "Component"
        )
        for NodeValue in Included
    }


# this definition exists because imported payload names must remain unique within the parent archive
def MovePayloadsMut(
    ChildPayloads: Mapping[str, bytes],
    Prefix: str,
    PayloadEntriesMut: dict[str, bytes],
) -> dict[str, str]:
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
        Renamed = UniquePayload(PayloadEntriesMut, Requested)
        PayloadEntriesMut[Renamed] = DataValue
        Files[FileName] = Renamed
    return Files


# this definition exists because imported nodes need rewritten links and preserved native metadata
def AddImportsMut(
    Graph: _Graph,
    Included: list[XmlTree.Element],
    DataNodes: Mapping[str, XmlTree.Element],
    Dependencies: Mapping[str, list[str]],
    Names: Mapping[str, str],
    Files: Mapping[str, str],
) -> list[str]:
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
    return Imported


# this definition exists because imported components need a deterministic preferred shape target
def ImportTarget(
    Included: list[XmlTree.Element],
    DataNodes: Mapping[str, XmlTree.Element],
    Names: Mapping[str, str],
    OuterOld: str,
    FinalOld: str,
) -> str:
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
    return Target


# this definition exists because component import coordinates names payloads links and target selection
def ImportCompMut(
    Graph: _Graph,
    DocValue: Mapping[str, Any],
    Prefix: str,
    PayloadEntries: dict[str, bytes],
    TrustedNativeBreps: frozenset[KNativeBrepKey] = frozenset(),
) -> tuple[str, list[str]]:
    RootValue, ChildPayloads = ImportArchive(DocValue, TrustedNativeBreps)
    ObjectNodes, DataNodes, Dependencies = ImportNodes(RootValue)
    OuterOld, FinalOld = ImportTargets(DataNodes)
    Included = [Value for Value in ObjectNodes if Value.get("name") != "KitMetadata"]
    Names = ImportNamesMut(Graph, Included, Prefix)
    Files = MovePayloadsMut(ChildPayloads, Prefix, PayloadEntries)
    Imported = AddImportsMut(
        Graph, Included, DataNodes, Dependencies, Names, Files
    )
    return (ImportTarget(Included, DataNodes, Names, OuterOld, FinalOld), Imported)


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


# this definition exists because grounded joints need a canonical component link property
def GroundLinkMut(Joint: Object, Component: str) -> None:
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


# this definition exists because grounded joints need a canonical placement property
def GroundPlaceMut(Joint: Object, Placement: tuple[float, ...]) -> None:
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


# this definition exists because grounded joints require standard python feature properties
def GroundPropsMut(Joint: Object) -> None:
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


# this definition exists because grounded joint assembly coordinates source metadata links and placement
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
    GroundLinkMut(Joint, Component)
    GroundPlaceMut(Joint, Placement)
    GroundPropsMut(Joint)
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


# this class exists because assembly source indexes must remain synchronized across phases
@Dataclass
class AsmContext:
    Graph: _Graph
    Manifest: Mapping[str, Any]
    PayloadEntries: dict[str, bytes]
    OuterLinks: Mapping[str, Mapping[str, Any]]
    TrustedBreps: frozenset[KNativeBrepKey]
    Assembly: Mapping[str, Any]
    Parameters: _Parameters
    Definitions: list[dict[str, Any]]
    Documents: dict[str, Any]
    RootDefId: str
    DefinitionsById: dict[str, dict[str, Any]]
    InstancesById: dict[str, dict[str, Any]]


# this class exists because assembly root objects share native source metadata
@Dataclass
class AsmRoot:
    RootLabel: str
    NativeRoot: Mapping[str, Any]
    GroupItems: list[dict[str, Any]]
    NativeJointGroup: Mapping[str, Any] | None
    NativeJoint: Mapping[str, Any]
    RootObject: Object
    RootOrigin: str
    DefinitionsGroup: Object
    ComponentsGroup: Object
    EntitiesGroup: Object
    MatesGroup: Object


# this class exists because component transfer produces correlated names paths and groups
@Dataclass
class AsmItems:
    DefinitionObjects: list[str]
    DefinitionTargets: dict[str, str]
    DefinitionOuter: dict[str, Mapping[str, AnyValue]]
    DirectInstances: list[dict[str, Any]]
    ItemObjects: list[str]
    ItemByPath: dict[tuple[str, ...], str]
    ItemByNativeName: dict[str, str]
    ProxyChainByPath: dict[tuple[str, ...], tuple[str, ...]]
    AsmLinkRecords: list[tuple[tuple[str, ...], Object, Mapping[str, AnyValue]]]
    RigidInstanceIds: set[str]
    GroundedObjects: list[str]


# this class exists because mate transfer shares entity component and object indexes
@Dataclass
class AsmMates:
    EntityItems: list[dict[str, Any]]
    EntityObjects: list[str]
    EntityNames: dict[str, str]
    EntityComponents: dict[str, str]
    EntityPrefixes: dict[str, str]
    MateItems: list[dict[str, Any]]
    MateObjects: list[str]
    MateNames: dict[str, str]


# this definition exists because assembly item indexes need independent mutable collections
def CreateAsmItems() -> AsmItems:
    return AsmItems([], {}, {}, [], [], {}, {}, {}, [], set(), [])


# this definition exists because assembly conversion needs one validated indexed source context
def BuildAsmContext(
    Graph: _Graph,
    Manifest: Mapping[str, Any],
    PayloadEntries: dict[str, bytes],
    OuterLinks: Mapping[str, Mapping[str, Any]],
    TrustedBreps: frozenset[KNativeBrepKey],
) -> AsmContext | None:
    Assembly = AsmData(Manifest)
    if Assembly is None:
        return None
    Definitions = Items(Assembly.get("definitions", []))
    Documents = {
        TextAction(Value.get("id")): Value.get("document")
        for Value in Items(Assembly.get("documents", []))
        if isinstance(Value.get("document"), Mapping)
    }
    RootDefId = TextAction(Assembly.get("root_definition_id"))
    DefinitionsById = {
        TextAction(Value.get("id")): Value for Value in Definitions
    }
    InstancesById = {
        TextAction(Value.get("id")): Value
        for Value in Items(Assembly.get("instances", Assembly.get("components", [])))
    }
    return AsmContext(
        Graph,
        Manifest,
        PayloadEntries,
        OuterLinks,
        TrustedBreps,
        Assembly,
        ParamCatalog(Items(Manifest.get("parameters", []))),
        Definitions,
        Documents,
        RootDefId,
        DefinitionsById,
        InstancesById,
    )


# this definition exists because ordered assembly records share the same stable sort key
def OrderedSource(Value: Mapping[str, Any]) -> tuple[int, str]:
    return (int(Number(Value.get("order"))), TextAction(Value.get("id")))


# this definition exists because root mate groups require deterministic source ordering
def RootGroupItems(Context: AsmContext) -> list[dict[str, Any]]:
    return sorted(
        (
            Group
            for Group in Items(
                Context.Assembly.get("mate_groups", Context.Assembly.get("groups", []))
            )
            if TextAction(Group.get("owner_definition_id")) == Context.RootDefId
        ),
        key=OrderedSource,
    )


# this definition exists because root objects must preserve native assembly and joint metadata
def BuildAsmRootMut(Context: AsmContext) -> AsmRoot:
    RootDefinition = Context.DefinitionsById.get(Context.RootDefId, {})
    RootLabel = TextAction(RootDefinition.get("name"), "Assembly")
    AsmAttrs = Context.Assembly.get("attributes", {})
    NativeRoot = AsmAttrs.get("freecad", {}) if isinstance(AsmAttrs, Mapping) else {}
    NativeRoot = NativeRoot if isinstance(NativeRoot, Mapping) else {}
    GroupItems = RootGroupItems(Context)
    NativeGroup = next(
        (
            Group
            for Group in GroupItems
            if isinstance(Group.get("attributes"), Mapping)
            and isinstance(Group["attributes"].get("freecad"), Mapping)
        ),
        None,
    )
    NativeJoint = NativeGroup["attributes"]["freecad"] if NativeGroup else {}
    RootObject = Context.Graph.add(
        TextAction(NativeRoot.get("type_id"), AsmRootTypeId),
        NativeRoot.get("name", RootLabel),
        "Assembly",
        Touched=bool(NativeRoot.get("touched")),
        Extensions=Native(NativeRoot) or ("App::OriginGroupExtension",),
    )
    RootObject.properties.extend(NativeA(NativeRoot))
    RootOrigin = AddOriginMut(Context.Graph, RootObject)
    DefinitionsGroup = Context.Graph.add(
        "App::DocumentObjectGroup", f"{RootLabel}_Definitions", "Definitions"
    )
    ComponentsGroup = Context.Graph.add(
        "App::DocumentObjectGroup", f"{RootLabel}_Components", "Components"
    )
    EntitiesGroup = Context.Graph.add(
        "App::DocumentObjectGroup", f"{RootLabel}_MateEntities", "MateEntities"
    )
    MatesGroup = Context.Graph.add(
        TextAction(NativeJoint.get("type_id"), AsmJointGroupTypeId),
        NativeJoint.get("name", f"{RootLabel}_Joints"),
        "Joints",
        Touched=bool(NativeJoint.get("touched")),
        Extensions=Native(NativeJoint) or ("App::GroupExtension",),
    )
    return AsmRoot(
        RootLabel,
        NativeRoot,
        GroupItems,
        NativeGroup,
        NativeJoint,
        RootObject,
        RootOrigin,
        DefinitionsGroup,
        ComponentsGroup,
        EntitiesGroup,
        MatesGroup,
    )


# this definition exists because embedded component documents need isolated object and payload import
def ImportDefMut(
    Context: AsmContext,
    Definition: Mapping[str, Any],
    DefinitionPrefix: str,
    ComponentKind: str,
) -> tuple[str, list[str]]:
    DocValue = Context.Documents.get(TextAction(Definition.get("document_id")))
    if not isinstance(DocValue, Mapping):
        return ("", [])
    ImportedDoc = DocValue
    if ComponentKind == "assembly":
        ImportedDoc = dict(DocValue)
        ImportedDoc["assembly"] = None
    ImportedTarget, Imported = ImportCompMut(
        Context.Graph,
        ImportedDoc,
        DefinitionPrefix,
        Context.PayloadEntries,
        Context.TrustedBreps,
    )
    TargetObject = next(
        (Value for Value in Context.Graph.Objects if Value.name == ImportedTarget),
        None,
    )
    if TargetObject is not None:
        ReplaceNameMut(
            TargetObject.properties, "Visibility", BoolProp("Visibility", False)
        )
    return (ImportedTarget, Imported)


# this definition exists because component meshes aggregate every declared tessellation source
def DefMeshData(
    Context: AsmContext, Definition: Mapping[str, Any]
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    Vertices: list[tuple[float, float, float]] = []
    Triangles: list[tuple[int, int, int]] = []
    for MeshSource in DefinitionMesh(Context.Manifest, Definition):
        MeshVertices, MeshTriangles = Tessellation(MeshSource)
        Offset = len(Vertices)
        Vertices.extend(MeshVertices)
        Triangles.extend(
            tuple(Index + Offset for Index in Triangle) for Triangle in MeshTriangles
        )
    return (Vertices, Triangles)


# this definition exists because component display meshes need deterministic archive payload names
def AddDefMeshMut(
    Context: AsmContext,
    DefinitionName: str,
    DefinitionId: str,
    Vertices: list[tuple[float, float, float]],
    Triangles: list[tuple[int, int, int]],
) -> str:
    if not Vertices or not Triangles:
        return ""
    MeshValue = Context.Graph.add(
        "Mesh::Feature", f"{DefinitionName}_Mesh", "ComponentMesh"
    )
    FileName = UniquePayload(
        Context.PayloadEntries, f"{MeshValue.name}.MeshKernel.bms"
    )
    Context.PayloadEntries[FileName] = MeshKernelData(Vertices, Triangles)
    MeshValue.properties.extend(
        [
            StringProp("Label", f"{DefinitionName} geometry"),
            MeshProp(FileName),
            MakePlacement("Placement", MatrixTransform(KIdentityMatrix)),
            StringProp("DefinitionId", DefinitionId, Dynamic=True),
            BoolProp("Visibility", False),
        ]
    )
    return MeshValue.name


# this definition exists because component definition groups need complete source provenance
def AsmDefProps(
    Definition: Mapping[str, Any], DefinitionId: str, DefinitionName: str, DocId: str
) -> list[XmlTree.Element]:
    return [
        StringProp("Label", DefinitionName),
        StringProp("DefinitionId", DefinitionId, Dynamic=True),
        StringProp(
            "ComponentKind", TextAction(EnumAction(Definition.get("kind"))), Dynamic=True
        ),
        StringProp("DocumentId", DocId, Dynamic=True),
        StringProp(
            "ConfigurationName", Definition.get("configuration_name", ""), Dynamic=True
        ),
        StringProp(
            "ConfigurationId", Definition.get("configuration_id", ""), Dynamic=True
        ),
        StringProp("SourcePath", Definition.get("source_path", ""), Dynamic=True),
        StringProp(
            "SourceFormat", Definition.get("source_format_id", ""), Dynamic=True
        ),
        StringProp("SourceSHA256", Definition.get("source_sha256", ""), Dynamic=True),
        JsonProp("DefinitionDataJSON", Without(Definition)),
        BoolProp("Visibility", False),
    ]


# this definition exists because one component definition coordinates import mesh and group state
def AddDefMut(
    Context: AsmContext, ItemsState: AsmItems, Definition: Mapping[str, Any]
) -> None:
    DefinitionId = TextAction(Definition.get("id"))
    DefinitionName = TextAction(Definition.get("name"), DefinitionId)
    DefinitionPrefix = SafeAction(f"Definition_{DefinitionId}", "Definition")
    DocId = TextAction(Definition.get("document_id"))
    ComponentKind = TextAction(EnumAction(Definition.get("kind"))).lower()
    Outer = Context.OuterLinks.get(DefinitionId)
    ImportedTarget = ""
    Imported: list[str] = []
    if Outer is not None:
        ItemsState.DefinitionOuter[DefinitionId] = Outer
    else:
        ImportedTarget, Imported = ImportDefMut(
            Context, Definition, DefinitionPrefix, ComponentKind
        )
    Vertices, Triangles = (
        ([], []) if Outer is not None else DefMeshData(Context, Definition)
    )
    MeshName = AddDefMeshMut(
        Context, DefinitionName, DefinitionId, Vertices, Triangles
    )
    DefinitionObject = Context.Graph.add(
        "App::DocumentObjectGroup",
        f"{DefinitionName}_Definition",
        "ComponentDefinition",
    )
    Children = [*Imported, *([MeshName] if MeshName else [])]
    Properties = AsmDefProps(Definition, DefinitionId, DefinitionName, DocId)
    DefinitionObject.properties.extend(
        [
            Properties[0],
            LinkListProp("Group", Children),
            *Properties[1:],
        ]
    )
    DefinitionObject.dependencies.extend(Children)
    ItemsState.DefinitionObjects.append(DefinitionObject.name)
    ItemsState.DefinitionTargets[DefinitionId] = (
        MeshName or ImportedTarget or DefinitionObject.name
    )


# this definition exists because definitions must preserve their source ordering in the archive
def AddDefsMut(Context: AsmContext, ItemsState: AsmItems) -> None:
    for Definition in Context.Definitions:
        AddDefMut(Context, ItemsState, Definition)


# this definition exists because direct component occurrences require deterministic source ordering
def DirectAsmItems(Context: AsmContext) -> list[dict[str, Any]]:
    return sorted(
        (
            Instance
            for Instance in Items(
                Context.Assembly.get(
                    "instances", Context.Assembly.get("components", [])
                )
            )
            if TextAction(Instance.get("owner_definition_id")) == Context.RootDefId
        ),
        key=OrderedSource,
    )


# this definition exists because occurrence metadata may omit or malformed native data
def InstanceNative(Instance: Mapping[str, Any]) -> Mapping[str, Any]:
    Attributes = Instance.get("attributes", {})
    NativeValue = Attributes.get("freecad", {}) if isinstance(Attributes, Mapping) else {}
    return NativeValue if isinstance(NativeValue, Mapping) else {}


# this definition exists because native link metadata selects the compatible component object type
def AsmLinkData(
    NativeValue: Mapping[str, Any],
    Outer: Mapping[str, Any] | None,
    ComponentKind: str,
) -> tuple[str, bool, str]:
    NativeProps = NativeValue.get("properties", {})
    LinkFields = (
        {TextAction(NameValue) for NameValue in NativeProps if TextAction(NameValue)}
        if isinstance(NativeProps, Mapping)
        else set()
    )
    LinkPropName = FindLinkProp(NativeValue)
    HasNativeLink = bool(LinkPropName)
    IsAssembly = Outer is not None and (
        {"Group", "Rigid"}.issubset(LinkFields)
        or (not HasNativeLink and ComponentKind == "assembly")
    )
    NativeType = TextAction(NativeValue.get("type_id"))
    TypeId = (
        NativeType
        if HasNativeLink and NativeType
        else AsmLinkTypeId if IsAssembly else AppLinkTypeId
    )
    return (LinkPropName, IsAssembly, TypeId)


# this definition exists because direct occurrence links need canonical native component properties
def InstanceProps(
    Instance: Mapping[str, Any],
    Label: str,
    InstanceId: str,
    DefinitionId: str,
    PathValue: tuple[str, ...],
    Target: str,
    Outer: Mapping[str, Any] | None,
    LinkPropName: str,
    IsAssembly: bool,
    PlacementMatrix: tuple[float, ...],
    Fixed: bool,
    Hidden: bool,
) -> list[XmlTree.Element]:
    LinkedObject = (
        XlinkProp(
            LinkPropName or "LinkedObject",
            TextAction(Outer.get("target")),
            FileValue=TextAction(Outer.get("file")),
            Stamp=TextAction(Outer.get("stamp")),
            Status=None if IsAssembly else "256",
        )
        if Outer is not None
        else XlinkProp(LinkPropName or "LinkedObject", Target)
    )
    Placement = MakePlacement(
        "Placement",
        MatrixTransform(PlacementMatrix),
        Status=(
            "8388612"
            if IsAssembly and Fixed
            else "8388608" if IsAssembly else "268" if Fixed else "264"
        ),
    )
    LinkProperties = (
        [
            BoolProp("Rigid", not bool(Instance.get("flexible"))),
            LinkListProp("Group", []),
            StringProp("Type", ""),
        ]
        if IsAssembly
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
    return [
        StringProp("Label", Label),
        LinkedObject,
        Placement,
        *LinkProperties,
        StringProp("InstanceId", InstanceId, Dynamic=True),
        StringProp("DefinitionId", DefinitionId, Dynamic=True),
        StringProp(
            "OwnerDefinitionId", Instance.get("owner_definition_id", ""), Dynamic=True
        ),
        StringListProp("InstancePath", list(PathValue), Dynamic=True),
        StringProp("ReferenceNumber", Instance.get("reference_number", ""), Dynamic=True),
        StringProp(
            "ConfigurationName", Instance.get("configuration_name", ""), Dynamic=True
        ),
        StringProp(
            "ConfigurationId", Instance.get("configuration_id", ""), Dynamic=True
        ),
        BoolProp("Suppressed", bool(Instance.get("suppressed")), Dynamic=True),
        BoolProp("Hidden", bool(Instance.get("hidden")), Dynamic=True),
        BoolProp("Flexible", bool(Instance.get("flexible")), Dynamic=True),
        BoolProp("ExcludeFromBOM", bool(Instance.get("exclude_from_bom")), Dynamic=True),
        JsonProp("InstanceDataJSON", Instance),
        BoolProp("Visibility", not Hidden),
    ]


# this definition exists because occurrence creation updates component path and grounding indexes
def RecordItemMut(
    Context: AsmContext,
    ItemsState: AsmItems,
    Instance: Mapping[str, Any],
    NativeValue: Mapping[str, Any],
    Component: Object,
    PathValue: tuple[str, ...],
    Outer: Mapping[str, Any] | None,
    IsAssembly: bool,
    Fixed: bool,
    Label: str,
    PlacementMatrix: tuple[float, ...],
) -> None:
    ItemsState.ItemObjects.append(Component.name)
    ItemsState.ItemByPath[PathValue] = Component.name
    NativeName = TextAction(NativeValue.get("name"))
    if NativeName:
        ItemsState.ItemByNativeName[NativeName] = Component.name
    if IsAssembly and Outer is not None:
        ItemsState.AsmLinkRecords.append((PathValue, Component, Outer))
    if not Fixed:
        return
    Attributes = Instance.get("attributes", {})
    GroundedSource = (
        Attributes.get("grounded_joint", {}) if isinstance(Attributes, Mapping) else {}
    )
    Grounded = GroundJointMut(
        Context.Graph, Component.name, Label, PlacementMatrix, GroundedSource
    )
    ItemsState.GroundedObjects.append(Grounded.name)


# this definition exists because one direct occurrence coordinates link placement visibility and state
def AddInstanceMut(
    Context: AsmContext, ItemsState: AsmItems, Instance: Mapping[str, Any]
) -> None:
    InstanceId = TextAction(Instance.get("id"))
    PathValue = (InstanceId,)
    DefinitionId = TextAction(Instance.get("definition_id"))
    Target = ItemsState.DefinitionTargets.get(DefinitionId, "")
    Outer = ItemsState.DefinitionOuter.get(DefinitionId)
    if not Target and Outer is None:
        return
    Label = TextAction(Instance.get("name"), InstanceId)
    NativeValue = InstanceNative(Instance)
    ComponentKind = TextAction(
        EnumAction(Context.DefinitionsById.get(DefinitionId, {}).get("kind"))
    ).lower()
    LinkPropName, IsAssembly, TypeId = AsmLinkData(
        NativeValue, Outer, ComponentKind
    )
    PlacementMatrix = MatrixValues(Instance.get("transform", {}))
    Component = Context.Graph.add(
        TypeId,
        f"{Label}_{'_'.join(PathValue)}",
        "Component",
        Touched=IsAssembly,
        Extensions=Native(NativeValue)
        or (("App::OriginGroupExtension",) if IsAssembly else ("App::LinkExtension",)),
    )
    Component.properties.extend(NativeA(NativeValue))
    if IsAssembly:
        AddOriginMut(Context.Graph, Component)
    if ComponentKind == "assembly" and not bool(Instance.get("flexible")):
        ItemsState.RigidInstanceIds.add(InstanceId)
    Suppressed = bool(Instance.get("suppressed"))
    Hidden = bool(Instance.get("hidden")) or Suppressed
    Fixed = bool(Instance.get("fixed")) and not Suppressed
    for PropElem in InstanceProps(
        Instance,
        Label,
        InstanceId,
        DefinitionId,
        PathValue,
        Target,
        Outer,
        LinkPropName,
        IsAssembly,
        PlacementMatrix,
        Fixed,
        Hidden,
    ):
        ReplaceNameMut(Component.properties, PropElem.get("name", ""), PropElem)
    if Outer is None and Target:
        Component.dependencies.append(Target)
    RecordItemMut(
        Context,
        ItemsState,
        Instance,
        NativeValue,
        Component,
        PathValue,
        Outer,
        IsAssembly,
        Fixed,
        Label,
        PlacementMatrix,
    )


# this definition exists because direct occurrences must preserve their source ordering
def AddInstancesMut(Context: AsmContext, ItemsState: AsmItems) -> None:
    ItemsState.DirectInstances = DirectAsmItems(Context)
    for Instance in ItemsState.DirectInstances:
        AddInstanceMut(Context, ItemsState, Instance)


# this definition exists because outer occurrence data overrides neutral occurrence fields selectively
def OuterField(
    Record: Mapping[str, Any],
    Neutral: Mapping[str, Any],
    NameValue: str,
    Default: Any = "",
) -> AnyValue:
    return Record.get(NameValue) if NameValue in Record else Neutral.get(NameValue, Default)


# this definition exists because outer occurrence paths may be absolute or parent relative
def OuterSourcePath(
    Record: Mapping[str, Any],
    InstanceId: str,
    ParentSource: tuple[str, ...],
) -> tuple[str, ...]:
    SourcePath = tuple(
        TextAction(Value)
        for Value in Sequence(Record.get("instance_path", []))
        if TextAction(Value)
    )
    if not SourcePath:
        return (*ParentSource, InstanceId)
    if ParentSource and SourcePath[: len(ParentSource)] != ParentSource:
        return (*ParentSource, *SourcePath)
    return SourcePath


# this definition exists because outer proxy links need canonical placement and occurrence metadata
def OuterProps(
    Record: Mapping[str, Any],
    Neutral: Mapping[str, Any],
    Outer: Mapping[str, Any],
    Label: str,
    InstanceId: str,
    FullPath: tuple[str, ...],
    PlacementMatrix: tuple[float, ...],
    IsAssembly: bool,
) -> list[XmlTree.Element]:
    LinkedObject = XlinkProp(
        "LinkedObject",
        TextAction(Record.get("target")),
        FileValue=TextAction(Outer.get("file")),
        Stamp=TextAction(Outer.get("stamp")),
        Status=None if IsAssembly else "256",
    )
    LinkProperties = (
        [
            BoolProp(
                "Rigid",
                bool(OuterField(Record, Neutral, "rigid", not bool(OuterField(Record, Neutral, "flexible")))),
            ),
            LinkListProp("Group", []),
            StringProp("Type", ""),
        ]
        if IsAssembly
        else [
            MakePlacement(
                "LinkPlacement", MatrixTransform(PlacementMatrix), Status="256"
            ),
            BoolProp("LinkTransform", True),
            VectorProp(
                "ScaleVector",
                Vector(
                    OuterField(Record, Neutral, "scale", MatrixScale(PlacementMatrix)),
                    MatrixScale(PlacementMatrix),
                ),
            ),
        ]
    )
    Visibility = bool(
        OuterField(
            Record,
            Neutral,
            "visibility",
            not bool(OuterField(Record, Neutral, "hidden"))
            and not bool(OuterField(Record, Neutral, "suppressed")),
        )
    )
    return [
        StringProp("Label", Label),
        LinkedObject,
        MakePlacement(
            "Placement",
            MatrixTransform(PlacementMatrix),
            Status="8388608" if IsAssembly else "264",
        ),
        *LinkProperties,
        StringProp("InstanceId", InstanceId, Dynamic=True),
        StringProp("DefinitionId", OuterField(Record, Neutral, "definition_id"), Dynamic=True),
        StringProp(
            "OwnerDefinitionId",
            OuterField(Record, Neutral, "owner_definition_id"),
            Dynamic=True,
        ),
        StringListProp("InstancePath", list(FullPath), Dynamic=True),
        StringProp(
            "ReferenceNumber", OuterField(Record, Neutral, "reference_number"), Dynamic=True
        ),
        StringProp(
            "ConfigurationName",
            OuterField(Record, Neutral, "configuration_name"),
            Dynamic=True,
        ),
        StringProp(
            "ConfigurationId",
            OuterField(Record, Neutral, "configuration_id"),
            Dynamic=True,
        ),
        BoolProp("Suppressed", bool(OuterField(Record, Neutral, "suppressed")), Dynamic=True),
        BoolProp("Hidden", bool(OuterField(Record, Neutral, "hidden")), Dynamic=True),
        BoolProp("Fixed", bool(OuterField(Record, Neutral, "fixed")), Dynamic=True),
        BoolProp("Flexible", bool(OuterField(Record, Neutral, "flexible")), Dynamic=True),
        BoolProp(
            "ExcludeFromBOM",
            bool(OuterField(Record, Neutral, "exclude_from_bom")),
            Dynamic=True,
        ),
        JsonProp("InstanceDataJSON", OuterField(Record, Neutral, "instance_data", Neutral)),
        BoolProp("Visibility", Visibility),
    ]


# this definition exists because one outer occurrence creates a typed proxy with stable paths
def CreateOuterMut(
    Context: AsmContext,
    RootPath: tuple[str, ...],
    Parent: Object,
    Outer: Mapping[str, Any],
    Record: Mapping[str, Any],
    ParentSource: tuple[str, ...],
) -> tuple[Object, tuple[str, ...], tuple[str, ...], bool] | None:
    Target = TextAction(Record.get("target"))
    TypeId = TextAction(Record.get("type_id"))
    InstanceId = TextAction(Record.get("instance_id"))
    if not Target or not InstanceId or not TypeId:
        return None
    SourcePath = OuterSourcePath(Record, InstanceId, ParentSource)
    FullPath = (*RootPath, *SourcePath)
    Neutral = Context.InstancesById.get(InstanceId, {})
    Label = TextAction(
        OuterField(Record, Neutral, "label", OuterField(Record, Neutral, "name", InstanceId)),
        InstanceId,
    )
    PlacementMatrix = MatrixValues(OuterField(Record, Neutral, "transform", {}))
    LinkFields = {
        TextAction(NameValue)
        for NameValue in Sequence(Record.get("link_fields", []))
        if TextAction(NameValue)
    }
    IsAssembly = {"Group", "Rigid"}.issubset(LinkFields)
    Proxy = Context.Graph.add(
        TypeId,
        f"{Parent.name}_{Target}",
        "Component",
        Touched=IsAssembly,
        Extensions=(
            ("App::OriginGroupExtension",)
            if IsAssembly
            else ("App::LinkExtension",)
        ),
    )
    if IsAssembly:
        AddOriginMut(Context.Graph, Proxy)
    Proxy.properties.extend(
        OuterProps(
            Record,
            Neutral,
            Outer,
            Label,
            InstanceId,
            FullPath,
            PlacementMatrix,
            IsAssembly,
        )
    )
    return (Proxy, FullPath, SourcePath, IsAssembly)


# this definition exists because outer occurrence trees need recursive proxy group assembly
def AddOuterMut(
    Context: AsmContext,
    ItemsState: AsmItems,
    RootPath: tuple[str, ...],
    Parent: Object,
    Outer: Mapping[str, Any],
    Records: Any,
    ParentSource: tuple[str, ...] = (),
    ParentChain: tuple[str, ...] = (),
) -> list[str]:
    Children: list[str] = []
    for Record in Items(Records):
        Created = CreateOuterMut(
            Context, RootPath, Parent, Outer, Record, ParentSource
        )
        if Created is None:
            continue
        Proxy, FullPath, SourcePath, IsAssembly = Created
        Children.append(Proxy.name)
        ItemsState.ItemByPath[FullPath] = Proxy.name
        Chain = (*ParentChain, Proxy.name)
        ItemsState.ProxyChainByPath[FullPath] = Chain
        if IsAssembly:
            AddOuterMut(
                Context,
                ItemsState,
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


# this definition exists because every external assembly link needs its occurrence proxy tree
def AddOutersMut(Context: AsmContext, ItemsState: AsmItems) -> None:
    for RootPath, Component, Outer in ItemsState.AsmLinkRecords:
        AddOuterMut(
            Context,
            ItemsState,
            RootPath,
            Component,
            Outer,
            Outer.get("occurrences", []),
        )


# this definition exists because mate entities and constraints require deterministic source subsets
def CreateAsmMates(Context: AsmContext) -> AsmMates:
    EntityItems = [
        Entity
        for Entity in Items(
            Context.Assembly.get("mate_entities", Context.Assembly.get("entities", []))
        )
        if TextAction(Entity.get("owner_definition_id")) == Context.RootDefId
    ]
    MateItems = sorted(
        (
            MateValue
            for MateValue in Items(
                Context.Assembly.get("mates", Context.Assembly.get("constraints", []))
            )
            if TextAction(MateValue.get("owner_definition_id")) == Context.RootDefId
        ),
        key=OrderedSource,
    )
    return AsmMates(EntityItems, [], {}, {}, {}, MateItems, [], {})


# this definition exists because rigid subassemblies resolve mate components at their direct link
def ComponentFor(
    ItemsState: AsmItems, RootData: AsmRoot, PathValue: tuple[str, ...]
) -> str:
    if not PathValue:
        return RootData.RootOrigin
    Direct = ItemsState.ItemByPath.get((PathValue[0],), "")
    if len(PathValue) == 1 or PathValue[0] in ItemsState.RigidInstanceIds:
        return Direct
    return ""


# this definition exists because rigid nested connectors need the longest emitted proxy chain
def PrefixForPath(ItemsState: AsmItems, PathValue: tuple[str, ...]) -> str:
    if len(PathValue) <= 1 or PathValue[0] not in ItemsState.RigidInstanceIds:
        return ""
    for Length in range(len(PathValue), 1, -1):
        Chain = ItemsState.ProxyChainByPath.get(PathValue[:Length])
        if Chain:
            return ".".join(Chain)
    return ""


# this definition exists because mate entity objects preserve connector geometry and component routing
def AddEntityMut(
    Context: AsmContext,
    RootData: AsmRoot,
    ItemsState: AsmItems,
    MatesState: AsmMates,
    Entity: Mapping[str, Any],
) -> None:
    EntityId = TextAction(Entity.get("id"))
    OwnerId = TextAction(Entity.get("owner_definition_id"))
    PathValue = tuple(
        TextAction(Value) for Value in Sequence(Entity.get("instance_path", []))
    )
    ComponentName = ComponentFor(ItemsState, RootData, PathValue)
    ComponentPrefix = PrefixForPath(ItemsState, PathValue)
    ObjValue = Context.Graph.add("App::FeaturePython", EntityId, "MateEntity")
    Properties = [
        StringProp("Label", EntityId),
        StringProp("EntityId", EntityId, Dynamic=True),
        StringProp("OwnerDefinitionId", OwnerId, Dynamic=True),
        StringListProp("OwnerOccurrencePath", [], Dynamic=True),
        StringListProp("InstancePath", list(PathValue), Dynamic=True),
        StringProp("EntityKind", TextAction(EnumAction(Entity.get("kind"))), Dynamic=True),
        StringProp("SourceEntityId", Entity.get("source_entity_id", ""), Dynamic=True),
        StringProp("SelectionId", Entity.get("selection_id", ""), Dynamic=True),
        JsonProp("EntityDataJSON", Entity),
        BoolProp("Visibility", False),
    ]
    Frame = Entity.get("frame")
    if isinstance(Frame, Mapping):
        Properties.append(
            MakePlacement("ConnectorFrame", MatrixTransform(MatrixValues(Frame)), Dynamic=True)
        )
    if Entity.get("radius") is not None:
        Properties.append(
            FloatProp("Radius", Entity.get("radius"), "App::PropertyLength", Dynamic=True)
        )
    if ComponentName:
        Properties.append(StringProp("ComponentName", ComponentName, Dynamic=True))
        MatesState.EntityComponents[EntityId] = ComponentName
    if ComponentPrefix:
        Properties.append(StringProp("ComponentSubpath", ComponentPrefix, Dynamic=True))
        MatesState.EntityPrefixes[EntityId] = ComponentPrefix
    ObjValue.properties.extend(Properties)
    MatesState.EntityObjects.append(ObjValue.name)
    MatesState.EntityNames[EntityId] = ObjValue.name


# this definition exists because mate entities must preserve their source ordering
def AddEntitiesMut(
    Context: AsmContext,
    RootData: AsmRoot,
    ItemsState: AsmItems,
    MatesState: AsmMates,
) -> None:
    for Entity in MatesState.EntityItems:
        AddEntityMut(Context, RootData, ItemsState, MatesState, Entity)


# this definition exists because mate metadata supports native properties and connector references
def MateAttributes(
    MateValue: Mapping[str, Any],
) -> tuple[Mapping[str, Any], Mapping[str, Any], list[dict[str, Any]]]:
    Attributes = MateValue.get("attributes", {})
    if not isinstance(Attributes, Mapping):
        Attributes = {}
    NativeMate = Attributes.get("freecad", {})
    if not isinstance(NativeMate, Mapping):
        NativeMate = {}
    return (Attributes, NativeMate, Items(Attributes.get("references", [])))


# this definition exists because connector references may declare their native side explicitly
def MateRefGroups(
    EntityIds: list[str], EntityById: Mapping[str, Mapping[str, Any]]
) -> list[list[str]]:
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
    return RefEntityIds


# this definition exists because neutral mate entities resolve to emitted component objects
def ConnectorTarget(
    EntityId: str,
    EntityById: Mapping[str, Mapping[str, Any]],
    RootData: AsmRoot,
    ItemsState: AsmItems,
    MatesState: AsmMates,
) -> str:
    Target = MatesState.EntityComponents.get(EntityId, "")
    if Target:
        return Target
    PathValue = tuple(
        TextAction(Value)
        for Value in Sequence(EntityById.get(EntityId, {}).get("instance_path", []))
    )
    return ComponentFor(ItemsState, RootData, PathValue)


# this definition exists because native connector references need rewritten object and subelement names
def NativeRefData(
    NativeRef: Mapping[str, Any], RootData: AsmRoot, ItemsState: AsmItems
) -> tuple[str, list[str]]:
    SourceTarget = TextAction(NativeRef.get("name"))
    NativeRootName = TextAction(RootData.NativeRoot.get("name"))
    Target = (
        RootData.RootObject.name
        if SourceTarget == NativeRootName
        else ItemsState.ItemByNativeName.get(SourceTarget, SourceTarget)
    )
    Subelements = []
    for Value in Sequence(NativeRef.get("subelements", [])):
        SourceValue = TextAction(Value)
        Prefix, Separator, Suffix = SourceValue.partition(".")
        Mapped = ItemsState.ItemByNativeName.get(Prefix, Prefix)
        Subelements.append(f"{Mapped}.{Suffix}" if Separator else Mapped)
    return (Target, Subelements)


# this definition exists because neutral connector references need geometric subelement reconstruction
def NeutralRefData(
    GroupedIds: list[str],
    EntityById: Mapping[str, Mapping[str, Any]],
    RootData: AsmRoot,
    ItemsState: AsmItems,
    MatesState: AsmMates,
) -> tuple[str, list[str]]:
    Target = (
        ConnectorTarget(
            GroupedIds[0], EntityById, RootData, ItemsState, MatesState
        )
        if GroupedIds
        else ""
    )
    Subelements: list[str] = []
    for EntityId in GroupedIds:
        Values = MateSubelements(EntityById.get(EntityId, {}))
        if len(GroupedIds) == 1:
            Subelements.extend(Values)
        elif Values:
            Subelements.append(Values[0])
    return (Target, Subelements)


# this definition exists because each mate needs two resolved connector sides
def MateConnectors(
    NativeReferences: list[dict[str, Any]],
    RefEntityIds: list[list[str]],
    EntityById: Mapping[str, Mapping[str, Any]],
    RootData: AsmRoot,
    ItemsState: AsmItems,
    MatesState: AsmMates,
) -> tuple[list[str], list[list[str]]]:
    ConnectorTargets: list[str] = []
    ConnectorSubelements: list[list[str]] = []
    for Index, GroupedIds in enumerate(RefEntityIds):
        NativeRef = NativeReferences[Index] if Index < len(NativeReferences) else {}
        Target, Subelements = (
            NativeRefData(NativeRef, RootData, ItemsState)
            if NativeRef
            else NeutralRefData(
                GroupedIds, EntityById, RootData, ItemsState, MatesState
            )
        )
        ConnectorTargets.append(Target)
        ConnectorSubelements.append(Subelements)
    return (ConnectorTargets, ConnectorSubelements)


# this definition exists because connector sides need linked subelements placements offsets and detachment
def ConnectorProps(
    RefEntityIds: list[list[str]],
    ConnectorTargets: list[str],
    ConnectorSubelements: list[list[str]],
    EntityById: Mapping[str, Mapping[str, Any]],
    MatesState: AsmMates,
) -> list[XmlTree.Element]:
    Properties: list[XmlTree.Element] = []
    for Index in range(1, 3):
        GroupedIds = RefEntityIds[Index - 1]
        EntityId = GroupedIds[0] if GroupedIds else ""
        ComponentName = ConnectorTargets[Index - 1] if Index <= len(ConnectorTargets) else ""
        Entity = EntityById.get(EntityId, {})
        Subelements = ConnectorSubelements[Index - 1]
        HasRealSubelements = bool(Subelements)
        ComponentPrefix = MatesState.EntityPrefixes.get(EntityId, "")
        if ComponentPrefix:
            Subelements = [
                f"{ComponentPrefix}.{Value}" if Value else f"{ComponentPrefix}."
                for Value in Subelements or ["", ""]
            ]
        elif ComponentName and not Subelements:
            Subelements = ["", ""]
        Properties.append(
            XlinkSubProp(f"Reference{Index}", ComponentName, Subelements, Dynamic=True)
        )
        Frame = Entity.get("frame")
        Matrix = MatrixValues(Frame) if isinstance(Frame, Mapping) else KIdentityMatrix
        Properties.extend(
            [
                MakePlacement(f"Placement{Index}", MatrixTransform(Matrix), Dynamic=True),
                MakePlacement(
                    f"Offset{Index}", MatrixTransform(KIdentityMatrix), Dynamic=True
                ),
                BoolProp(
                    f"Detach{Index}",
                    isinstance(Frame, Mapping) and not HasRealSubelements,
                    Dynamic=True,
                ),
            ]
        )
    return Properties


# this definition exists because mate carriers need complete neutral provenance and links
def MateMetaProps(
    MateValue: Mapping[str, Any],
    MateId: str,
    OwnerId: str,
    EntityIds: list[str],
    LinkedEntities: list[str],
    LinkedComponents: list[str],
) -> list[XmlTree.Element]:
    return [
        StringProp("MateId", MateId, Dynamic=True),
        StringListProp("OwnerOccurrencePath", [], Dynamic=True),
        StringProp("MateType", TextAction(EnumAction(MateValue.get("kind"))), Dynamic=True),
        StringProp("OwnerDefinitionId", OwnerId, Dynamic=True),
        StringListProp("EntityLinks", LinkedEntities, Dynamic=True),
        StringListProp("ComponentLinks", LinkedComponents, Dynamic=True),
        StringListProp("EntityIds", EntityIds, Dynamic=True),
        StringListProp(
            "ParameterIds",
            [TextAction(Value) for Value in Sequence(MateValue.get("parameter_ids", []))],
            Dynamic=True,
        ),
        StringProp("Alignment", TextAction(EnumAction(MateValue.get("alignment"))), Dynamic=True),
        BoolProp("SourceSuppressed", bool(MateValue.get("suppressed")), Dynamic=True),
        BoolProp("Driving", bool(MateValue.get("driving", True)), Dynamic=True),
        JsonProp("MateValueJSON", MateValue.get("value")),
        JsonProp("MateDataJSON", MateValue),
    ]


# this definition exists because mate dimensions may originate from several named parameters
def MateParamValues(
    MateValue: Mapping[str, Any], Parameters: _Parameters
) -> dict[str, float]:
    return {
        PathValue: Parameters.value(ParamId)
        for ParamId in (
            TextAction(Value)
            for Value in Sequence(MateValue.get("parameter_ids", []))
        )
        if (PathValue := Parameters.source_path(ParamId))
    }


# this definition exists because unsupported mates must remain editable carrier objects
def AddCarrierMut(
    ObjValue: Object,
    NativeMate: Mapping[str, Any],
    MateName: str,
    JointType: str | None,
    MetaProperties: list[XmlTree.Element],
    ConnectorProperties: list[XmlTree.Element],
) -> None:
    ObjValue.properties.extend(NativeA(NativeMate))
    for PropElem in (
        StringProp("Label", MateName),
        BoolProp("KitMateCarrier", True, Dynamic=True),
        StringProp(
            "NativeExecutionReason",
            "unsupported_mate_kind" if JointType is None else "missing_connector_pair",
            Dynamic=True,
        ),
        *MetaProperties,
        *ConnectorProperties,
        BoolProp("Visibility", False),
    ):
        ReplaceNameMut(ObjValue.properties, PropElem.get("name", ""), PropElem)


# this definition exists because native joint objects need selective property replacement
def NativeMateProps(
    NativeMate: Mapping[str, Any],
    MateValue: Mapping[str, Any],
    MateName: str,
    JointType: str,
    HasConnectorPair: bool,
    ParamValues: Mapping[str, float],
    AngleValue: float,
    DistanceValue: float,
    MetaProperties: list[XmlTree.Element],
    ConnectorProperties: list[XmlTree.Element],
) -> list[XmlTree.Element]:
    NativeProperties = NativeMate.get("properties", {})
    Properties = [
        ElemValue
        for Value in NativeProperties.values()
        if (ElemValue := ElemFromData(Value)) is not None and ElemValue.tag == "Property"
    ]
    Replacements = [
        StringProp("Label", MateName),
        EnumerationProp("JointType", JointTypes, JointTypes.index(JointType)),
        BoolProp("Suppressed", bool(MateValue.get("suppressed")) or not HasConnectorPair),
        FloatProp("Angle", AngleValue, "App::PropertyAngle"),
        FloatProp("Distance", DistanceValue, "App::PropertyLength"),
        *[
            Value
            for Value in ConnectorProperties
            if Value.get("name", "").startswith(AsmConnectorPropPrefixes)
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
            Replacements.append(FloatProp(PropName, ParamValues[PropName], PropType))
    for Replacement in Replacements:
        MergeNamedMut(Properties, Replacement)
    Properties.extend(MetaProperties)
    return Properties


# this definition exists because neutral joints need the complete standard assembly property set
def NeutralJoint(
    MateValue: Mapping[str, Any],
    MateName: str,
    JointType: str,
    HasConnectorPair: bool,
    ParamValues: Mapping[str, float],
    AngleValue: float,
    DistanceValue: float,
    MetaProperties: list[XmlTree.Element],
    ConnectorProperties: list[XmlTree.Element],
) -> list[XmlTree.Element]:
    return [
        StringProp("Label", MateName),
        *MetaProperties,
        EnumerationProp("JointType", JointTypes, JointTypes.index(JointType), Dynamic=True),
        BoolProp("Suppressed", bool(MateValue.get("suppressed")) or not HasConnectorPair),
        FloatProp("Angle", AngleValue, "App::PropertyAngle", Dynamic=True),
        FloatProp("Distance", DistanceValue, "App::PropertyLength", Dynamic=True),
        FloatProp(
            "Distance2",
            ParamValues.get("Distance2", 0.0) if JointType in JointTypesUsingSecond else 0.0,
            "App::PropertyLength",
            Dynamic=True,
        ),
        FloatProp("LengthMin", ParamValues.get("LengthMin", 0.0), "App::PropertyLength", Dynamic=True),
        FloatProp("LengthMax", ParamValues.get("LengthMax", 0.0), "App::PropertyLength", Dynamic=True),
        FloatProp("AngleMin", ParamValues.get("AngleMin", 0.0), "App::PropertyAngle", Dynamic=True),
        FloatProp("AngleMax", ParamValues.get("AngleMax", 0.0), "App::PropertyAngle", Dynamic=True),
        BoolProp("EnableLengthMin", "LengthMin" in ParamValues, Dynamic=True),
        BoolProp("EnableLengthMax", "LengthMax" in ParamValues, Dynamic=True),
        BoolProp("EnableAngleMin", "AngleMin" in ParamValues, Dynamic=True),
        BoolProp("EnableAngleMax", "AngleMax" in ParamValues, Dynamic=True),
        *ConnectorProperties,
        PythonProxyProp("JointObject", "Joint"),
        BoolProp("Visibility", False),
    ]


# this definition exists because mate object indexes and dependencies must update together
def RecordMateMut(
    MatesState: AsmMates,
    ObjValue: Object,
    MateId: str,
    ConnectorTargets: list[str],
) -> None:
    ObjValue.dependencies.extend(ConnectorTargets)
    MatesState.MateObjects.append(ObjValue.name)
    MatesState.MateNames[MateId] = ObjValue.name


# this definition exists because one mate coordinates references properties execution and diagnostics
def AddMateMut(
    Context: AsmContext,
    RootData: AsmRoot,
    ItemsState: AsmItems,
    MatesState: AsmMates,
    EntityById: Mapping[str, Mapping[str, Any]],
    MateValue: Mapping[str, Any],
) -> None:
    MateId = TextAction(MateValue.get("id"))
    MateName = TextAction(MateValue.get("name"), MateId)
    OwnerId = TextAction(MateValue.get("owner_definition_id"))
    EntityIds = [TextAction(Value) for Value in Sequence(MateValue.get("entity_ids", []))]
    Ignored, NativeMate, NativeReferences = MateAttributes(MateValue)
    LinkedEntities = [MatesState.EntityNames[Value] for Value in EntityIds if Value in MatesState.EntityNames]
    LinkedComponents = list(
        dict.fromkeys(
            MatesState.EntityComponents[Value]
            for Value in EntityIds
            if Value in MatesState.EntityComponents
        )
    )
    RefEntityIds = MateRefGroups(EntityIds, EntityById)
    ConnectorTargets, ConnectorSubelements = MateConnectors(
        NativeReferences,
        RefEntityIds,
        EntityById,
        RootData,
        ItemsState,
        MatesState,
    )
    HasConnectorPair = len(ConnectorTargets) == 2 and all(ConnectorTargets)
    JointType = MateJointType(MateValue.get("kind"))
    NativeSupported = JointType is not None and HasConnectorPair
    ObjValue = Context.Graph.add(
        TextAction(NativeMate.get("type_id"), "App::FeaturePython"),
        NativeMate.get("name", MateName),
        "Mate",
        Touched=bool(NativeMate.get("touched")),
        Extensions=Native(NativeMate)
        or (("App::SuppressibleExtensionPython",) if NativeSupported else ()),
    )
    ConnectorProperties = ConnectorProps(
        RefEntityIds,
        ConnectorTargets,
        ConnectorSubelements,
        EntityById,
        MatesState,
    )
    MetaProperties = MateMetaProps(
        MateValue, MateId, OwnerId, EntityIds, LinkedEntities, LinkedComponents
    )
    if not NativeSupported:
        AddCarrierMut(
            ObjValue,
            NativeMate,
            MateName,
            JointType,
            MetaProperties,
            ConnectorProperties,
        )
        RecordMateMut(MatesState, ObjValue, MateId, ConnectorTargets)
        return
    assert JointType is not None
    ParamValues = MateParamValues(MateValue, Context.Parameters)
    NumericValue = MateScalar(MateValue.get("value"))
    AngleValue = ParamValues.get("Angle", NumericValue if JointType == "Angle" else 0.0)
    DistanceValue = ParamValues.get(
        "Distance", NumericValue if JointType in JointTypesUsingDistance else 0.0
    )
    NativeProperties = NativeMate.get("properties", {})
    Properties = (
        NativeMateProps(
            NativeMate,
            MateValue,
            MateName,
            JointType,
            HasConnectorPair,
            ParamValues,
            AngleValue,
            DistanceValue,
            MetaProperties,
            ConnectorProperties,
        )
        if isinstance(NativeProperties, Mapping) and NativeProperties
        else NeutralJoint(
            MateValue,
            MateName,
            JointType,
            HasConnectorPair,
            ParamValues,
            AngleValue,
            DistanceValue,
            MetaProperties,
            ConnectorProperties,
        )
    )
    ObjValue.properties.extend(Properties)
    RecordMateMut(MatesState, ObjValue, MateId, ConnectorTargets)


# this definition exists because mates must preserve their source ordering
def AddMatesMut(
    Context: AsmContext,
    RootData: AsmRoot,
    ItemsState: AsmItems,
    MatesState: AsmMates,
) -> None:
    EntityById = {
        TextAction(Value.get("id")): Value for Value in MatesState.EntityItems
    }
    for MateValue in MatesState.MateItems:
        AddMateMut(
            Context,
            RootData,
            ItemsState,
            MatesState,
            EntityById,
            MateValue,
        )


# this definition exists because nested mate groups need a stable parent lookup
def GroupParent(GroupId: str, GroupItems: list[dict[str, Any]]) -> str:
    return TextAction(
        next(
            (
                Value.get("parent_group_id")
                for Value in GroupItems
                if TextAction(Value.get("id")) == GroupId
            ),
            "",
        )
    )


# this definition exists because mate groups preserve nesting and source membership metadata
def AddGroupsMut(
    Context: AsmContext, RootData: AsmRoot, MatesState: AsmMates
) -> None:
    GroupItems = [
        Group for Group in RootData.GroupItems if Group is not RootData.NativeJointGroup
    ]
    GroupNames: dict[str, str] = {}
    GroupObjects: list[Object] = []
    for Group in GroupItems:
        GroupId = TextAction(Group.get("id"))
        ObjValue = Context.Graph.add(
            "App::DocumentObjectGroup", Group.get("name", GroupId), "MateGroup"
        )
        GroupNames[GroupId] = ObjValue.name
        GroupObjects.append(ObjValue)
    for Group, ObjValue in zip(GroupItems, GroupObjects):
        Members = [
            MatesState.MateNames[Value]
            for Value in (
                TextAction(ItemValue)
                for ItemValue in Sequence(Group.get("mate_ids", []))
            )
            if Value in MatesState.MateNames
        ]
        GroupId = TextAction(Group.get("id"))
        Children = [
            NameValue
            for ChildId, NameValue in GroupNames.items()
            if GroupParent(ChildId, GroupItems) == GroupId
        ]
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


# this definition exists because assembly support groups need their canonical memberships and labels
def SetAsmGroupsMut(
    RootData: AsmRoot, ItemsState: AsmItems, MatesState: AsmMates
) -> None:
    RootData.DefinitionsGroup.properties.extend(
        [
            StringProp("Label", "Component Definitions"),
            LinkListProp("Group", ItemsState.DefinitionObjects),
            BoolProp("Visibility", False),
        ]
    )
    RootData.DefinitionsGroup.dependencies.extend(ItemsState.DefinitionObjects)
    RootData.ComponentsGroup.properties.extend(
        [
            StringProp("Label", "Components"),
            LinkListProp("Group", []),
            StringListProp("ComponentObjects", ItemsState.ItemObjects, Dynamic=True),
            BoolProp("Visibility", True),
        ]
    )
    RootData.EntitiesGroup.properties.extend(
        [
            StringProp("Label", "Mate Entities"),
            LinkListProp("Group", MatesState.EntityObjects),
            BoolProp("Visibility", False),
        ]
    )
    RootData.EntitiesGroup.dependencies.extend(MatesState.EntityObjects)


# this definition exists because native joint groups need their emitted child link list replaced
def GroupLinksMut(MatesGroup: Object, MateChildren: list[str]) -> None:
    GroupProp = next(
        (Value for Value in MatesGroup.properties if Value.get("name") == "Group"),
        None,
    )
    if GroupProp is None:
        MatesGroup.properties.append(LinkListProp("Group", MateChildren))
        return
    LinkList = GroupProp.find("./LinkList")
    if LinkList is None:
        LinkList = XmlTree.SubElement(GroupProp, "LinkList")
    LinkList.clear()
    LinkList.set("count", str(len(MateChildren)))
    for Target in MateChildren:
        XmlTree.SubElement(LinkList, "Link", {"value": Target})


# this definition exists because joint groups require standard label expression and visibility properties
def JointPropsMut(MatesGroup: Object) -> None:
    if not any(Value.get("name") == "ExpressionEngine" for Value in MatesGroup.properties):
        MatesGroup.properties.insert(0, ExpressionProp([]))
    if not any(Value.get("name") == "Label" for Value in MatesGroup.properties):
        LabelProp = PropAction("Label", "App::PropertyString", Status="134217728")
        XmlTree.SubElement(LabelProp, "String", {"value": "Joints"})
        MatesGroup.properties.append(LabelProp)
    if not any(Value.get("name") == "Label2" for Value in MatesGroup.properties):
        LabelTwoProp = PropAction("Label2", "App::PropertyString", Status="67108992")
        XmlTree.SubElement(LabelTwoProp, "String", {"value": ""})
        MatesGroup.properties.append(LabelTwoProp)
    if not any(Value.get("name") == "Visibility" for Value in MatesGroup.properties):
        VisibilityProp = PropAction("Visibility", "App::PropertyBool", Status="648")
        XmlTree.SubElement(VisibilityProp, "Bool", {"value": "true"})
        MatesGroup.properties.append(VisibilityProp)


# this definition exists because assembly finalization synchronizes groups root properties and counts
def FinalizeAsmMut(
    Context: AsmContext,
    RootData: AsmRoot,
    ItemsState: AsmItems,
    MatesState: AsmMates,
) -> tuple[str, int, int]:
    SetAsmGroupsMut(RootData, ItemsState, MatesState)
    MateChildren = [*ItemsState.GroundedObjects, *MatesState.MateObjects]
    RootData.MatesGroup.properties.extend(NativeA(RootData.NativeJoint))
    GroupLinksMut(RootData.MatesGroup, MateChildren)
    JointPropsMut(RootData.MatesGroup)
    RootData.MatesGroup.transient_properties.append(
        XmlTree.Element(
            "_Property",
            {
                "name": "_GroupTouched",
                "type": "App::PropertyBool",
                "status": "100663424",
            },
        )
    )
    RootData.MatesGroup.dependencies.extend(MateChildren)
    RootChildren = [
        RootData.MatesGroup.name,
        *ItemsState.ItemObjects,
        *ItemsState.GroundedObjects,
        *MatesState.MateObjects,
    ]
    for PropElem in (
        StringProp("Label", RootData.RootLabel),
        StringProp("Type", "Assembly"),
        LinkListProp("Group", RootChildren),
        MakePlacement("Placement", MatrixTransform(KIdentityMatrix)),
        StringProp("RootDefinitionId", Context.RootDefId, Dynamic=True),
        IntegerProp("DefinitionCount", len(Context.Definitions), Dynamic=True),
        IntegerProp("OccurrenceCount", len(ItemsState.DirectInstances), Dynamic=True),
        IntegerProp("MateCount", len(MatesState.MateObjects), Dynamic=True),
        BoolProp("Visibility", True),
    ):
        ReplaceNameMut(
            RootData.RootObject.properties, PropElem.get("name", ""), PropElem
        )
    RootData.RootObject.dependencies.extend(RootChildren)
    return (
        RootData.RootObject.name,
        len(ItemsState.DirectInstances),
        len(MatesState.MateObjects),
    )


# this definition exists because assembly conversion coordinates each ordered transfer phase
def AddAsmMut(
    Graph: _Graph,
    Manifest: Mapping[str, Any],
    PayloadEntries: dict[str, bytes],
    OuterLinks: Mapping[str, Mapping[str, Any]],
    TrustedNativeBreps: frozenset[KNativeBrepKey] = frozenset(),
) -> tuple[str, int, int]:
    Context = BuildAsmContext(
        Graph, Manifest, PayloadEntries, OuterLinks, TrustedNativeBreps
    )
    if Context is None:
        return ("", 0, 0)
    RootData = BuildAsmRootMut(Context)
    ItemsState = CreateAsmItems()
    AddDefsMut(Context, ItemsState)
    AddInstancesMut(Context, ItemsState)
    AddOutersMut(Context, ItemsState)
    MatesState = CreateAsmMates(Context)
    AddEntitiesMut(Context, RootData, ItemsState, MatesState)
    AddMatesMut(Context, RootData, ItemsState, MatesState)
    AddGroupsMut(Context, RootData, MatesState)
    return FinalizeAsmMut(Context, RootData, ItemsState, MatesState)


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


# this class exists because document phases share source native graph and root objects
@Dataclass
class DocContext:
    Manifest: Mapping[str, Any]
    ManifestData: str
    ManifestHash: str
    OuterLinks: Mapping[str, Mapping[str, Any]]
    NativeOuterLinks: Mapping[str, str]
    Timestamp: str
    TrustedBreps: frozenset[KNativeBrepKey]
    NativeDocHash: str
    SourceFormat: str
    FreecadMeta: Mapping[str, Any]
    NativeValues: list[dict[str, Any]]
    NativeReplay: bool
    ReplayValues: list[dict[str, Any]]
    Graph: ObjectGraph
    NativeGraph: dict[str, Object]
    NativeTargets: dict[str, str]
    ParametersData: list[dict[str, Any]]
    Parameters: _Parameters
    ParamSheet: Object
    MetaObject: Object
    PlanesGroup: Object
    SketchesGroup: Object
    SelectionsGroup: Object
    ConfigsGroup: Object
    TimelineGroup: Object
    BodiesGroup: Object


# this class exists because planes and sketches share support and profile indexes
@Dataclass
class DocGeometry:
    PlaneItems: list[dict[str, Any]]
    PlaneById: dict[str, dict[str, Any]]
    PlaneNames: dict[str, str]
    PlaneObjects: list[str]
    SketchItems: list[dict[str, Any]]
    SketchNames: dict[str, str]
    SketchProfCounts: dict[str, int]
    SketchProfSound: dict[str, bool]
    SketchObjects: list[str]
    SelectionItems: dict[str, dict[str, Any]]


# this class exists because document feature phases share emitted names payloads and representations
@Dataclass
class DocFeatures:
    FeatureItems: list[dict[str, Any]]
    FeatureNames: dict[str, str]
    SolidNames: dict[str, str]
    FeatureObjects: list[str]
    CurrentName: str
    FinalShapeFile: str
    PayloadEntries: dict[str, bytes]
    BodyObjects: list[str]
    BodyNames: dict[str, str]
    BodyTargets: dict[str, str]
    SelectionNames: dict[str, str]
    SelectionObjects: list[str]
    ConfigItems: list[dict[str, Any]]
    ConfigNames: dict[str, str]
    ConfigObjects: list[str]
    DocBreps: list[str]
    DocMeshes: list[str]
    AssemblyRoot: str
    AssemblyItems: int
    AssemblyMates: int
    OuterTarget: str


# this definition exists because native replay objects need stable source ordering
def NativeOrder(Value: Mapping[str, Any]) -> int:
    return int(Number(Value.get("order")))


# this definition exists because partial native replay must retain a dependency closed object set
def ReplaySubset(
    Manifest: Mapping[str, Any],
    NativeValues: list[dict[str, Any]],
    AsmValue: Mapping[str, Any] | None,
) -> tuple[bool, list[dict[str, Any]]]:
    NativeReplay = bool(NativeValues) and AsmValue is None
    if NativeReplay:
        return (True, NativeValues)
    RepresentedNames = Represented(Manifest, AsmValue) if AsmValue is not None else set()
    ReplayValues = [
        Value
        for Value in NativeValues
        if TextAction(Value.get("name")) not in RepresentedNames
    ]
    while True:
        ReplayNames = {TextAction(Value.get("name")) for Value in ReplayValues}
        ClosedValues = [
            Value
            for Value in ReplayValues
            if all(
                TextAction(Dependency) in ReplayNames
                for Dependency in Sequence(Value.get("dependencies", []))
            )
        ]
        if len(ClosedValues) == len(ReplayValues):
            return (False, ReplayValues)
        ReplayValues = ClosedValues


# this definition exists because replay objects must seed graph names before generated objects
def AddReplayMut(
    Graph: ObjectGraph, ReplayValues: list[dict[str, Any]]
) -> dict[str, Object]:
    NativeGraph: dict[str, Object] = {}
    for Value in sorted(ReplayValues, key=NativeOrder):
        ObjValue = NativeObject(Value)
        if ObjValue.name in NativeGraph:
            raise ValueError(f"duplicate native FreeCAD object metadata: {ObjValue.name}")
        NativeGraph[ObjValue.name] = ObjValue
        Graph.Names.add(ObjValue.name)
        Graph.Objects.append(ObjValue)
    return NativeGraph


# this definition exists because freecad metadata may be absent or malformed
def FreecadMetaData(Manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    ManifestMeta = Manifest.get("metadata", {})
    FreecadMeta = (
        ManifestMeta.get("freecad", {}) if isinstance(ManifestMeta, Mapping) else {}
    )
    return FreecadMeta if isinstance(FreecadMeta, Mapping) else {}


# this definition exists because document root groups require a stable creation order
def AddDocBaseMut(
    Graph: ObjectGraph,
    Manifest: Mapping[str, Any],
    ManifestData: str,
    ManifestHash: str,
    Parameters: _Parameters,
) -> tuple[Object, Object, Object, Object, Object, Object, Object, Object]:
    ParamSheet = Graph.add("Spreadsheet::Sheet", "Parameters", "Parameters")
    ParamSheet.properties.extend(Parameters.sheet_properties())
    MetaObject = Graph.add("App::FeaturePython", "KitMetadata", "Metadata")
    MetaObject.properties.extend(
        [
            StringProp("Label", "Kit Metadata"),
            StringProp(KManifestEncodingProp, KManifestEncoding, Dynamic=True),
            StringProp(KManifestShaTwoFiveSixPrA, ManifestHash, Dynamic=True),
            StringProp(KManifestDataProp, ManifestData, Dynamic=True),
            StringProp("SchemaVersion", Manifest.get("schema_version", "1.0"), Dynamic=True),
            JsonProp("ParameterAliasesJSON", Parameters.Aliases),
            BoolProp("Visibility", False),
        ]
    )
    PlanesGroup = Graph.add("App::DocumentObjectGroup", "SupportPlanes", "Group")
    SketchesGroup = Graph.add("App::DocumentObjectGroup", "Sketches", "Group")
    SelectionsGroup = Graph.add("App::DocumentObjectGroup", "Selections", "Group")
    ConfigsGroup = Graph.add("App::DocumentObjectGroup", "Configurations", "Group")
    TimelineGroup = Graph.add("App::DocumentObjectGroup", "FeatureTimeline", "Group")
    BodiesGroup = Graph.add("App::DocumentObjectGroup", "Bodies", "Group")
    return (
        ParamSheet,
        MetaObject,
        PlanesGroup,
        SketchesGroup,
        SelectionsGroup,
        ConfigsGroup,
        TimelineGroup,
        BodiesGroup,
    )


# this definition exists because document conversion needs one initialized shared context
def BuildDocContext(
    Manifest: Mapping[str, Any],
    ManifestData: str,
    ManifestHash: str,
    OuterLinks: Mapping[str, Mapping[str, Any]] | None,
    NativeOuterLinks: Mapping[str, str] | None,
    Timestamp: str,
    TrustedBreps: frozenset[KNativeBrepKey],
) -> DocContext:
    SourceData = Manifest.get("source", {})
    SourceFormat = (
        TextAction(SourceData.get("format_id")) if isinstance(SourceData, Mapping) else ""
    )
    FreecadMeta = FreecadMetaData(Manifest)
    NativeValues = Items(FreecadMeta.get("objects", []))
    NativeReplay, ReplayValues = ReplaySubset(Manifest, NativeValues, AsmData(Manifest))
    Graph = ObjectGraph()
    NativeGraph = AddReplayMut(Graph, ReplayValues)
    NativeTargets = {NameValue: Value.name for NameValue, Value in NativeGraph.items()}
    ParametersData = Items(Manifest.get("parameters", []))
    Parameters = ParamCatalog(ParametersData)
    BaseObjects = AddDocBaseMut(
        Graph, Manifest, ManifestData, ManifestHash, Parameters
    )
    return DocContext(
        Manifest,
        ManifestData,
        ManifestHash,
        OuterLinks or {},
        NativeOuterLinks or {},
        Timestamp,
        TrustedBreps,
        NativeDocShaTwo(Manifest),
        SourceFormat,
        FreecadMeta,
        NativeValues,
        NativeReplay,
        ReplayValues,
        Graph,
        NativeGraph,
        NativeTargets,
        ParametersData,
        Parameters,
        *BaseObjects,
    )


# this definition exists because plane sketch and selection indexes need independent collections
def BuildDocGeom(Context: DocContext) -> DocGeometry:
    PlaneItems = Items(
        Context.Manifest.get("support_planes", Context.Manifest.get("planes", []))
    )
    PlaneById = {TextAction(Value.get("id")): Value for Value in PlaneItems}
    SketchItems = Items(Context.Manifest.get("sketches", []))
    SelectionItems = {
        TextAction(Value.get("id")): Value
        for Value in Items(Context.Manifest.get("selections", []))
    }
    return DocGeometry(
        PlaneItems,
        PlaneById,
        {},
        [],
        SketchItems,
        {},
        {},
        {},
        [],
        SelectionItems,
    )


# this definition exists because feature timeline entries need stable source ordering
def FeatureOrder(Value: Mapping[str, Any]) -> int:
    return int(Number(Value.get("order")))


# this definition exists because document feature state needs independent mutable collections
def BuildDocItems(Context: DocContext) -> DocFeatures:
    FeatureItems = sorted(
        Items(
            Context.Manifest.get(
                "feature_timeline", Context.Manifest.get("timeline", [])
            )
        ),
        key=FeatureOrder,
    )
    ConfigItems = Items(Context.Manifest.get("configurations", []))
    return DocFeatures(
        FeatureItems,
        {},
        {},
        [],
        "",
        "",
        {},
        [],
        {},
        {},
        {},
        [],
        ConfigItems,
        {},
        [],
        [],
        [],
        "",
        0,
        0,
        "",
    )


# this definition exists because partial replay imports only payloads referenced by replay objects
def ReplayEntrySet(Context: DocContext) -> set[str] | None:
    if Context.NativeReplay:
        return None
    return {
        FileName
        for Value in Context.ReplayValues
        for PropElem in NativeA(Value)
        for NodeValue in PropElem.iter()
        if NodeValue.tag != "XLink" and (FileName := NodeValue.get("file", ""))
    }


# this definition exists because native entry metadata must remain conflict free and complete
def AddEntryDataMut(Context: DocContext, Features: DocFeatures) -> None:
    if not Context.NativeValues:
        return
    ReplayEntries = ReplayEntrySet(Context)
    for ItemValue in Items(Context.FreecadMeta.get("entries", [])):
        SourceStream = TextAction(ItemValue.get("source_stream"))
        DataValue = PayloadBytes(ItemValue)
        if not SourceStream or DataValue is None:
            raise ValueError("native FreeCAD entry metadata is incomplete")
        if ReplayEntries is not None and SourceStream not in ReplayEntries:
            continue
        Entry = ValidatedEntry(SourceStream)
        if Entry in {KDocEntry, KManifestEntry} or Entry in Features.PayloadEntries:
            raise ValueError("native FreeCAD entry metadata conflicts with the archive")
        Features.PayloadEntries[Entry] = DataValue


# this definition exists because neutral records may carry optional freecad object metadata
def FreecadAttrs(Value: Mapping[str, Any]) -> Mapping[str, Any]:
    Attributes = Value.get("attributes", {})
    NativeValue = Attributes.get("freecad", {}) if isinstance(Attributes, Mapping) else {}
    return NativeValue if isinstance(NativeValue, Mapping) else {}


# this definition exists because offset planes can retain a direct parameter expression
def PlaneExpressions(
    Plane: Mapping[str, Any], Transform: Mapping[str, Any], Parameters: _Parameters
) -> list[tuple[str, str]]:
    ParamId = TextAction(Plane.get("offset_parameter_id"))
    if not ParamId:
        return []
    Expression = Parameters.expression(ParamId)
    Origin = Vector(Transform.get("origin"), (0.0, 0.0, 0.0))
    Normal = Normalize(Vector(Transform.get("z_axis"), (0.0, 0.0, 1.0)))
    ParamValue = Parameters.value(ParamId)
    Result: list[tuple[str, str]] = []
    for Coordinate, Component, OriginValue in zip(("x", "y", "z"), Normal, Origin):
        if abs(Component) > 0.999999 and MathValue.isclose(
            abs(OriginValue), abs(ParamValue), rel_tol=1e-09, abs_tol=1e-09
        ):
            SignValue = "-" if OriginValue * ParamValue < 0 else ""
            Result.append(
                (f"Placement.Base.{Coordinate}", SignValue + TextAction(Expression))
            )
    return Result


# this definition exists because one support plane coordinates native replay placement and indexes
def AddPlaneMut(
    Context: DocContext, Geometry: DocGeometry, Plane: Mapping[str, Any]
) -> None:
    PlaneId = TextAction(Plane.get("id"))
    NativePlane = FreecadAttrs(Plane)
    NativeName = TextAction(NativePlane.get("name"))
    ObjValue = Context.NativeGraph.get(NativeName) if Context.NativeReplay else None
    if ObjValue is None:
        ObjValue = Context.Graph.add(
            TextAction(NativePlane.get("type_id"), "App::Plane"),
            NativePlane.get("name", Plane.get("name", PlaneId)),
            "Plane",
        )
    if NativeName:
        Context.NativeTargets[NativeName] = ObjValue.name
    Geometry.PlaneNames[PlaneId] = ObjValue.name
    Geometry.PlaneObjects.append(ObjValue.name)
    Transform = (
        Plane.get("transform", {})
        if isinstance(Plane.get("transform"), Mapping)
        else {}
    )
    Expressions = PlaneExpressions(Plane, Transform, Context.Parameters)
    NativeProperties = NativePlane.get("properties", {})
    if isinstance(NativeProperties, Mapping) and NativeProperties:
        Properties = NativeA(NativePlane)
        for Replacement in (
            StringProp("Label", Plane.get("name", PlaneId)),
            MakePlacement("Placement", Transform),
            BoolProp("Visibility", False),
        ):
            MergeNamedMut(Properties, Replacement)
        if not Context.NativeReplay:
            Properties.extend(
                [
                    StringProp("KitId", PlaneId, Dynamic=True),
                    JsonProp("SourcePlaneJSON", Plane),
                ]
            )
        setattr(ObjValue, "properties", Properties)
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
    if Expressions and not Context.NativeReplay:
        ObjValue.dependencies.append(Context.ParamSheet.name)


# this definition exists because support planes must preserve their source ordering
def AddPlanesMut(Context: DocContext, Geometry: DocGeometry) -> None:
    for Plane in Geometry.PlaneItems:
        AddPlaneMut(Context, Geometry, Plane)


# this definition exists because one sketch coordinates profile evidence support and native replay
def AddSketchMut(
    Context: DocContext, Geometry: DocGeometry, Sketch: Mapping[str, Any]
) -> None:
    SketchId = TextAction(Sketch.get("id"))
    Geometry.SketchProfCounts[SketchId] = NativeClosed(Sketch)
    Geometry.SketchProfSound[SketchId] = HasNativeProf(Sketch)
    PlaneId = TextAction(Sketch.get("support_plane_id"))
    Plane = Geometry.PlaneById.get(PlaneId, {"transform": {}})
    PlaneName = Geometry.PlaneNames.get(PlaneId, "")
    NativeSketch = FreecadAttrs(Sketch)
    NativeName = TextAction(NativeSketch.get("name"))
    ObjValue = Context.NativeGraph.get(NativeName) if Context.NativeReplay else None
    if ObjValue is None:
        ObjValue = Context.Graph.add(
            TextAction(NativeSketch.get("type_id"), SketchTypeId),
            NativeSketch.get("name", Sketch.get("name", SketchId)),
            "Sketch",
            Touched=True,
            Extensions=("Part::AttachExtension",),
        )
    Geometry.SketchNames[SketchId] = ObjValue.name
    if NativeName:
        Context.NativeTargets[NativeName] = ObjValue.name
    Geometry.SketchObjects.append(ObjValue.name)
    Properties, Dependencies = BuildSketch(
        Sketch,
        Plane,
        PlaneName,
        Context.Parameters,
        Context.NativeReplay,
        Context.SourceFormat == "solidworks.sldprt",
    )
    if Context.NativeReplay and NativeSketch:
        setattr(ObjValue, "properties", Properties)
    else:
        ObjValue.properties.extend(Properties)
    if NativeSketch and not Context.NativeReplay:
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
    ObjValue.dependencies.extend(Value for Value in Dependencies if Value)


# this definition exists because sketches must preserve their source ordering
def AddSketchesMut(Context: DocContext, Geometry: DocGeometry) -> None:
    for Sketch in Geometry.SketchItems:
        AddSketchMut(Context, Geometry, Sketch)


# this class exists because one feature branch shares parsed source and native metadata
@Dataclass
class FeatureData:
    Source: Mapping[str, Any]
    FeatureId: str
    FeatureName: str
    KindValue: str
    Operation: str
    Attributes: Mapping[str, Any]
    Definition: Mapping[str, Any]
    NativeDef: Mapping[str, Any]
    InputBase: str
    BaseName: str
    SketchId: str
    SketchName: str
    NativeFeature: Mapping[str, Any]
    NativeName: str


# this definition exists because feature writers need one normalized source record
def BuildFeatureData(
    Geometry: DocGeometry, Features: DocFeatures, Feature: Mapping[str, Any]
) -> FeatureData:
    FeatureId = TextAction(Feature.get("id"))
    Attributes = Feature.get("attributes", {})
    Attributes = Attributes if isinstance(Attributes, Mapping) else {}
    Definition = Feature.get("definition", {})
    Definition = Definition if isinstance(Definition, Mapping) else {}
    NativeDef = (
        Definition.get("object_data", {})
        if TextAction(Definition.get("$type")) == "NativeFeatureDefinition"
        and TextAction(Definition.get("format_id")) == FormatId
        and isinstance(Definition.get("object_data"), Mapping)
        else {}
    )
    Inputs = [TextAction(Value) for Value in Sequence(Feature.get("input_feature_ids", []))]
    InputBase = next(
        (Features.SolidNames[Value] for Value in reversed(Inputs) if Value in Features.SolidNames),
        "",
    )
    SketchId = TextAction(Feature.get("sketch_id"))
    NativeFeature = Attributes.get("freecad", {})
    NativeFeature = NativeFeature if isinstance(NativeFeature, Mapping) else {}
    return FeatureData(
        Feature,
        FeatureId,
        TextAction(Feature.get("name"), FeatureId),
        TextAction(EnumAction(Feature.get("kind"))).lower(),
        TextAction(EnumAction(Feature.get("operation"))).lower(),
        Attributes,
        Definition,
        NativeDef,
        InputBase,
        InputBase or Features.CurrentName,
        SketchId,
        Geometry.SketchNames.get(SketchId, ""),
        NativeFeature,
        TextAction(NativeFeature.get("name")),
    )


# this definition exists because replayed feature properties need current semantic parameter values
def PatchReplayMut(Data: FeatureData, Properties: list[XmlTree.Element]) -> None:
    PropNames = {Value.get("name", "") for Value in Properties}
    if "Label" in PropNames:
        MergeNamedMut(Properties, StringProp("Label", Data.FeatureName))
    if Data.KindValue == "extrusion":
        Length = abs(
            Number(Data.Definition.get("length"), Number(Data.Attributes.get("length_mm")))
        )
        Replacements = [
            FloatProp("Length", Length, "App::PropertyLength"),
            FloatProp(
                "Length2",
                abs(Number(Data.Definition.get("second_length"))),
                "App::PropertyLength",
            ),
            BoolProp("Midplane", bool(Data.Definition.get("symmetric"))),
            BoolProp("Reversed", bool(Data.Definition.get("reversed"))),
        ]
        Direction = Data.Definition.get("direction")
        if Direction is not None:
            Replacements.append(VectorProp("Direction", Vector(Direction, (0.0, 0.0, 1.0))))
        for Replacement in Replacements:
            if Replacement.get("name", "") in PropNames:
                MergeNamedMut(Properties, Replacement)
    elif Data.KindValue == "fillet":
        Radius = abs(
            Number(Data.Definition.get("radius"), Number(Data.Attributes.get("radius_mm")))
        )
        for NameValue in ("Radius", "DrivingRadius"):
            if NameValue in PropNames:
                MergeNamedMut(Properties, FloatProp(NameValue, Radius, "App::PropertyLength"))
    if "Suppressed" in PropNames or bool(Data.Source.get("suppressed")):
        MergeNamedMut(
            Properties,
            BoolProp(
                "Suppressed",
                bool(Data.Source.get("suppressed")),
                Dynamic="Suppressed" not in PropNames,
            ),
        )


# this definition exists because native replay should short circuit generated feature construction
def HasReplayMut(
    Context: DocContext, Features: DocFeatures, Data: FeatureData
) -> bool:
    if not Context.NativeReplay or Data.NativeName not in Context.NativeGraph:
        return False
    Final = Context.NativeGraph[Data.NativeName]
    NativeSource = Data.NativeDef or Data.NativeFeature
    Properties = NativeA(NativeSource)
    NativeType = TextAction(Data.Definition.get("type_id"))
    if Data.NativeDef and NativeType:
        setattr(Final, "type_id", NativeType)
    PatchReplayMut(Data, Properties)
    setattr(Final, "properties", Properties)
    Features.FeatureNames[Data.FeatureId] = Final.name
    Features.SolidNames[Data.FeatureId] = Final.name
    Features.FeatureObjects.append(Final.name)
    Features.CurrentName = Final.name
    Context.NativeTargets[Data.NativeName] = Final.name
    return True


# this definition exists because unproven solidworks profiles require nonexecuting feature carriers
def IsRawExtrude(
    Context: DocContext, Geometry: DocGeometry, Data: FeatureData
) -> bool:
    if Data.KindValue != "extrusion":
        return False
    ProfileCount = Geometry.SketchProfCounts.get(Data.SketchId, 0)
    ProfileSound = Geometry.SketchProfSound.get(Data.SketchId, False)
    return (
        Context.SourceFormat == "solidworks.sldprt" and (not ProfileCount or not ProfileSound)
    ) or bool(Data.Source.get("suppressed"))


# this definition exists because extrusion carriers need a precise nonexecution reason
def ExtrudeReason(Geometry: DocGeometry, Data: FeatureData) -> str:
    if bool(Data.Source.get("suppressed")):
        return "suppressed"
    if not Geometry.SketchProfCounts.get(Data.SketchId, 0):
        return "no_native_closed_profile"
    return "profile_topology_not_statically_sound"


# this definition exists because unsafe extrusions must preserve parameters without native execution
def AddRawExtMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    Data: FeatureData,
) -> None:
    Length = abs(
        Number(Data.Definition.get("length"), Number(Data.Attributes.get("length_mm")))
    )
    SecondLength = abs(Number(Data.Definition.get("second_length")))
    ParamId = FeatureParam(Data.Source, Context.Parameters, Length)
    Expression = Context.Parameters.expression(ParamId)
    Final = Context.Graph.add("Part::Feature", Data.FeatureName, "Feature")
    Final.properties.extend(
        [
            StringProp("Label", Data.FeatureName),
            ExpressionProp([("Length", Expression)] if Expression else []),
            FloatProp("Length", Length, "App::PropertyLength", Dynamic=True),
            FloatProp("SecondLength", SecondLength, "App::PropertyLength", Dynamic=True),
            BoolProp("Midplane", bool(Data.Definition.get("symmetric")), Dynamic=True),
            BoolProp("Reversed", bool(Data.Definition.get("reversed")), Dynamic=True),
            VectorProp(
                "Direction",
                Vector(Data.Definition.get("direction"), (0.0, 0.0, 1.0)),
                Dynamic=True,
            ),
            *FeatureMeta(Data.Source, "feature-data"),
            BoolProp("NativeExecutable", False, Dynamic=True),
            StringProp("NativeExecutionReason", ExtrudeReason(Geometry, Data), Dynamic=True),
            *DefinitionProps(Data.Definition),
            JsonProp("NativeDefinitionJSON", Data.Definition),
            ShapeProp(),
            BoolProp("Visibility", False),
        ]
    )
    if Data.SketchName:
        Final.properties.append(LinkProp("Profile", Data.SketchName, Dynamic=True))
        Final.dependencies.append(Data.SketchName)
    if Expression:
        Final.dependencies.append(Context.ParamSheet.name)
    Features.FeatureNames[Data.FeatureId] = Final.name
    Features.FeatureObjects.append(Final.name)
    if Data.InputBase:
        Features.SolidNames[Data.FeatureId] = Data.InputBase
        Features.CurrentName = Data.InputBase


# this definition exists because extrusion direction follows its support plane and reversal semantics
def ExtrudeDirection(
    Geometry: DocGeometry, Data: FeatureData
) -> tuple[float, float, float]:
    PlaneId = TextAction(
        next(
            (
                Value.get("support_plane_id")
                for Value in Geometry.SketchItems
                if TextAction(Value.get("id")) == Data.SketchId
            ),
            "",
        )
    )
    Plane = Geometry.PlaneById.get(PlaneId, {})
    Transform = Plane.get("transform", {}) if isinstance(Plane.get("transform"), Mapping) else {}
    Normal = Normalize(Vector(Transform.get("z_axis"), (0.0, 0.0, 1.0)))
    Reversed = bool(
        Data.Definition.get(
            "reversed",
            Number(
                Data.Attributes.get("direction_multiplier"),
                -1.0 if Data.Operation == "cut" else 1.0,
            )
            < 0,
        )
    )
    Explicit = Data.Definition.get("direction")
    if Explicit is not None:
        return Normalize(Vector(Explicit, Normal))
    return tuple(Component * (-1.0 if Reversed else 1.0) for Component in Normal)


# this definition exists because extrusion tools need canonical profile length and expression properties
def AddExtrudeToolMut(
    Context: DocContext,
    Data: FeatureData,
    Direction: tuple[float, float, float],
    Length: float,
    SecondLength: float,
    Symmetric: bool,
    Expression: str | None,
) -> Object:
    ToolType = BoolOperationTypeByKind["create"]
    ToolRequested = Data.FeatureName if not Data.BaseName else f"{Data.FeatureName}_Profile"
    ToolValue = Context.Graph.add(
        ToolType.type_id, ToolRequested, ToolType.label, Touched=True
    )
    ToolValue.properties.extend(
        [
            StringProp(
                "Label",
                Data.FeatureName
                if ToolRequested == Data.FeatureName
                else f"{Data.FeatureName} profile extrusion",
            ),
            LinkProp("Base", Data.SketchName),
            VectorProp("Dir", Direction),
            EnumerationProA("DirMode", 0),
            FloatProp("LengthFwd", Length, "App::PropertyDistance"),
            FloatProp("LengthRev", SecondLength, "App::PropertyDistance"),
            BoolProp("Solid", True),
            BoolProp("Reversed", False),
            BoolProp("Symmetric", Symmetric),
            StringProp(
                "EndCondition",
                TextAction(EnumAction(Data.Definition.get("end_condition")), "blind"),
                Dynamic=True,
            ),
            ExpressionProp([("LengthFwd", Expression)] if Expression else []),
            ShapeProp(),
            *FeatureMeta(Data.Source, "profile-extrusion" if Data.BaseName else "feature"),
            BoolProp("Visibility", not Data.BaseName),
        ]
    )
    ToolValue.dependencies.append(Data.SketchName)
    if Expression:
        ToolValue.dependencies.append(Context.ParamSheet.name)
    return ToolValue


# this definition exists because boolean extrusion results need the protocol selected input layout
def AddBoolResultMut(Context: DocContext, Data: FeatureData, ToolValue: Object) -> Object:
    OperationKind = (
        "join"
        if Data.BaseName and Data.Operation in CreateOperationNames
        else Data.Operation or "create"
    )
    OperationType = BoolOperationTypeByKind.get(OperationKind)
    if not Data.BaseName or OperationType is None:
        return ToolValue
    InputProp = (
        [LinkProp("Base", Data.BaseName), LinkProp("Tool", ToolValue.name)]
        if OperationType.input_mode == "base_tool"
        else [LinkListProp("Shapes", [Data.BaseName, ToolValue.name])]
        if OperationType.input_mode == "shapes"
        else []
    )
    if not InputProp:
        return ToolValue
    Final = Context.Graph.add(
        OperationType.type_id, Data.FeatureName, OperationType.label, Touched=True
    )
    Final.properties.extend(
        [
            StringProp("Label", Data.FeatureName),
            *InputProp,
            BoolProp("Refine", True),
            ExpressionProp([]),
            ShapeProp(),
            *FeatureMeta(Data.Source, "feature"),
            BoolProp("Visibility", True),
        ]
    )
    Final.dependencies.extend([Data.BaseName, ToolValue.name])
    ToolValue.properties[-1] = BoolProp("Visibility", False)
    return Final


# this definition exists because executable extrusions coordinate tool boolean and solid state
def AddExtrudeMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    Data: FeatureData,
) -> Object:
    Direction = ExtrudeDirection(Geometry, Data)
    Length = abs(
        Number(Data.Definition.get("length"), Number(Data.Attributes.get("length_mm")))
    )
    SecondLength = abs(Number(Data.Definition.get("second_length")))
    Symmetric = bool(Data.Definition.get("symmetric"))
    ParamId = FeatureParam(Data.Source, Context.Parameters, Length)
    Expression = Context.Parameters.expression(ParamId)
    ToolValue = AddExtrudeToolMut(
        Context, Data, Direction, Length, SecondLength, Symmetric, Expression
    )
    Final = AddBoolResultMut(Context, Data, ToolValue)
    Features.FeatureNames[Data.FeatureId] = Final.name
    Features.SolidNames[Data.FeatureId] = Final.name
    Features.FeatureObjects.append(Final.name)
    Features.CurrentName = Final.name
    return Final


# this definition exists because solidworks fillets require nonexecuting topology carriers
def AddRawFilletMut(
    Context: DocContext, Features: DocFeatures, Data: FeatureData
) -> Object:
    Radius = abs(
        Number(Data.Definition.get("radius"), Number(Data.Attributes.get("radius_mm")))
    )
    ParamId = FeatureParam(Data.Source, Context.Parameters, Radius)
    Expression = Context.Parameters.expression(ParamId)
    Final = Context.Graph.add("Part::Feature", Data.FeatureName, "Feature")
    Final.properties.extend(
        [
            StringProp("Label", Data.FeatureName),
            ExpressionProp([("DrivingRadius", Expression)] if Expression else []),
            FloatProp("DrivingRadius", Radius, "App::PropertyLength", Dynamic=True),
            *FeatureMeta(Data.Source, "feature-data"),
            BoolProp("NativeExecutable", False, Dynamic=True),
            StringProp(
                "NativeExecutionReason",
                "topology_selection_not_statically_provable",
                Dynamic=True,
            ),
            *DefinitionProps(Data.Definition),
            JsonProp("NativeDefinitionJSON", Data.Definition),
            ShapeProp(),
            BoolProp("Visibility", False),
        ]
    )
    if Data.InputBase:
        Final.properties.append(LinkProp("InputFeature", Data.InputBase, Dynamic=True))
        Final.dependencies.append(Data.InputBase)
    if Expression:
        Final.dependencies.append(Context.ParamSheet.name)
    Features.FeatureNames[Data.FeatureId] = Final.name
    Features.FeatureObjects.append(Final.name)
    if Data.InputBase:
        Features.SolidNames[Data.FeatureId] = Data.InputBase
        Features.CurrentName = Data.InputBase
    return Final


# this definition exists because fillet selections need deterministic native edge indexes
def FilletIndices(Data: FeatureData, Geometry: DocGeometry) -> list[int]:
    EdgeIndices: list[int] = []
    SemanticIndices: list[int] = []
    for KeyValue in (
        "selected_native_local_edge_ids",
        "native_local_edge_ids",
        "edge_ids",
        "edges",
    ):
        EdgeIndices.extend(
            int(Number(Value))
            for Value in Sequence(Data.Attributes.get(KeyValue, []))
            if Number(Value) > 0
        )
    for SelectionId in Sequence(Data.Source.get("selection_ids", [])):
        Selection = Geometry.SelectionItems.get(TextAction(SelectionId), {})
        for PathItem in Items(Selection.get("path", [])):
            Match = RegexLib.fullmatch(
                "(?:Edge|edge:)(\\d+)",
                TextAction(PathItem.get("subelement")),
                RegexLib.IGNORECASE,
            )
            if Match:
                EdgeIndices.append(int(Match.group(1)))
        Query = Selection.get("query", {})
        Query = Query if isinstance(Query, Mapping) else {}
        if TextAction(Query.get("topology_role")) == "extrusion_terminal_profile_boundary":
            SemanticIndices.append(3)
        for KeyValue in ("edge_index", "native_local_id", "index"):
            if Number(Query.get(KeyValue)) > 0:
                EdgeIndices.append(int(Number(Query.get(KeyValue))))
    return list(dict.fromkeys(SemanticIndices or EdgeIndices)) or [1]


# this definition exists because executable fillets need edge payload radius and source links
def AddFilletMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    Data: FeatureData,
) -> Object:
    Radius = abs(
        Number(Data.Definition.get("radius"), Number(Data.Attributes.get("radius_mm")))
    )
    ParamId = FeatureParam(Data.Source, Context.Parameters, Radius)
    Expression = Context.Parameters.expression(ParamId)
    EdgeIndices = FilletIndices(Data, Geometry)
    Final = Context.Graph.add("Part::Fillet", Data.FeatureName, "Fillet", Touched=True)
    EdgeFileName = f"{Final.name}.Edges"
    Features.PayloadEntries[EdgeFileName] = FilletEdgesData(EdgeIndices, Radius)
    Expressions = [("DrivingRadius", Expression)] if Expression else []
    Final.properties.extend(
        [
            StringProp("Label", Data.FeatureName),
            LinkProp("Base", Data.BaseName),
            FilletEdgesProp(EdgeFileName),
            EdgeLinkProp(Data.BaseName, EdgeIndices),
            ExpressionProp(Expressions),
            FloatProp("DrivingRadius", Radius, "App::PropertyLength", Dynamic=True),
            ShapeProp(),
            *FeatureMeta(Data.Source, "feature"),
            BoolProp("Visibility", True),
        ]
    )
    Final.dependencies.extend(
        [Data.BaseName] + ([Context.ParamSheet.name] if Expression else [])
    )
    Features.FeatureNames[Data.FeatureId] = Final.name
    Features.SolidNames[Data.FeatureId] = Final.name
    Features.FeatureObjects.append(Final.name)
    Features.CurrentName = Final.name
    return Final


# this definition exists because generic features preserve complete definitions and dependency links
def AddGenericMut(
    Context: DocContext, Features: DocFeatures, Data: FeatureData
) -> Object:
    Imported = Data.KindValue == "imported"
    Final = Context.Graph.add("Part::Feature", Data.FeatureName, "Feature", Touched=True)
    Final.properties.extend(
        [
            StringProp("Label", Data.FeatureName),
            ExpressionProp([]),
            *FeatureMeta(Data.Source, "imported" if Imported else "feature-data"),
            StringProp("NativeTypeId", Data.Definition.get("type_id", ""), Dynamic=True),
            *DefinitionProps(Data.Definition),
            JsonProp("NativeDefinitionJSON", Data.Definition),
            BoolProp("Visibility", not bool(Data.Source.get("suppressed"))),
            ShapeProp(),
        ]
    )
    if Data.BaseName:
        Final.properties.append(LinkProp("InputFeature", Data.BaseName, Dynamic=True))
        Final.dependencies.append(Data.BaseName)
    if Data.SketchName:
        Final.properties.append(LinkProp("Profile", Data.SketchName, Dynamic=True))
        Final.dependencies.append(Data.SketchName)
    if Context.ParametersData:
        Final.properties.extend(
            [
                LinkProp("Parameters", Context.ParamSheet.name, Dynamic=True),
                StringListProp(
                    "ParameterIds",
                    [TextAction(Value) for Value in Sequence(Data.Source.get("parameter_ids", []))],
                    Dynamic=True,
                ),
            ]
        )
        Final.dependencies.append(Context.ParamSheet.name)
    Features.FeatureNames[Data.FeatureId] = Final.name
    Features.FeatureObjects.append(Final.name)
    if Context.SourceFormat == "solidworks.sldprt":
        if Data.InputBase:
            Features.SolidNames[Data.FeatureId] = Data.InputBase
            Features.CurrentName = Data.InputBase
    elif Data.KindValue not in {"native", "reference"}:
        Features.SolidNames[Data.FeatureId] = Final.name
        Features.CurrentName = Final.name
    return Final


# this definition exists because one timeline feature selects exactly one semantic writer branch
def AddFeatureMut(
    Context: DocContext,
    Geometry: DocGeometry,
    Features: DocFeatures,
    Feature: Mapping[str, Any],
) -> None:
    Data = BuildFeatureData(Geometry, Features, Feature)
    if HasReplayMut(Context, Features, Data):
        return
    if IsRawExtrude(Context, Geometry, Data):
        AddRawExtMut(Context, Geometry, Features, Data)
        return
    if Data.KindValue == "extrusion":
        Final = AddExtrudeMut(Context, Geometry, Features, Data)
    elif Data.KindValue == "fillet" and Context.SourceFormat == "solidworks.sldprt":
        Final = AddRawFilletMut(Context, Features, Data)
    elif Data.KindValue == "fillet" and Data.InputBase:
        Final = AddFilletMut(Context, Geometry, Features, Data)
    else:
        Final = AddGenericMut(Context, Features, Data)
    if bool(Data.Source.get("suppressed")) and not Context.NativeReplay:
        ReplaceNameMut(Final.properties, "Visibility", BoolProp("Visibility", False))
    if Data.NativeName:
        Context.NativeTargets[Data.NativeName] = Final.name


# this definition exists because timeline features must preserve their source ordering
def AddFeaturesMut(
    Context: DocContext, Geometry: DocGeometry, Features: DocFeatures
) -> None:
    for Feature in Features.FeatureItems:
        AddFeatureMut(Context, Geometry, Features, Feature)


# this definition exists because focused behavior needs one stable owner
def BuildDocXml(
    Manifest: Mapping[str, Any],
    ManifestData: str,
    ManifestShaTwoFiveSix: str,
    OuterLinks: Mapping[str, Mapping[str, Any]] | None = None,
    NativeOuterLinks: Mapping[str, str] | None = None,
    DocTimestamp: str = "1980-01-01T00:00:00Z",
    TrustedNativeBreps: frozenset[KNativeBrepKey] = frozenset(),
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
            setattr(ObjValue, "properties", Properties)
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
            setattr(ObjValue, "properties", Properties)
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
                setattr(Final, "type_id", NativeDefinitionType)
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
            setattr(Final, "properties", Properties)
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
            setattr(ObjValue, "properties", Properties)
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
    setattr(InfoValue, "compress_type", Zipfile.ZIP_DEFLATED)
    setattr(InfoValue, "external_attr", 384 << 16)
    setattr(InfoValue, "create_system", 3)
    return (InfoValue, DataValue)


# this definition exists because focused behavior needs one stable owner
def BuildFcstd(
    Manifest: Mapping[str, Any],
    OuterLinks: Mapping[str, Mapping[str, Any]] | None = None,
    NativeOuterLinks: Mapping[str, str] | None = None,
    DocTimestamp: str | None = None,
    TrustedNativeBreps: frozenset[KNativeBrepKey] = frozenset(),
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
    TrustedNativeBreps: frozenset[KNativeBrepKey] = frozenset(),
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
globals()["_native_brep_key"] = BuildBrepKey

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
