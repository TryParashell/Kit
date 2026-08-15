# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import dataclass as Dataclass, field as Field
import struct as Struct
from convert.adapters.solidworks.container.Archive import (
    encode_class_definition as EncodeClassDefinition,
    encode_class_reference as EncodeClassRef,
    encode_object_reference as EncodeObjectRef,
    encode_string as EncodeString,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError


# this definition exists because focused behavior needs one stable owner
@Dataclass(slots=True)
class ResolveWriter:
    KBufferData: bytearray = Field(default_factory=bytearray)
    KMapCounter: int = 109
    KObjectCount: int = 0
    KClassIndex: dict[str, int] = Field(default_factory=dict)

    # this definition exists because focused behavior needs one stable owner
    def PutValues(Instance, FormatText: str, *FieldValues: object) -> None:
        Instance.KBufferData.extend(Struct.pack(FormatText, *FieldValues))

    # this definition exists because focused behavior needs one stable owner
    def PutClass(Instance, ClassName: str, SchemaCode: int = 1) -> int:
        return PutClassMut(Instance, ClassName, SchemaCode)

    # this definition exists because focused behavior needs one stable owner
    def PutExtern(Instance, ClassIndex: int) -> None:
        Instance.KBufferData.extend(EncodeClassRef(ClassIndex))
        Instance.KMapCounter += 1
        Instance.KObjectCount += 1

    # this definition exists because focused behavior needs one stable owner
    def PutNull(Instance) -> None:
        Instance.KBufferData.extend(Struct.pack("<H", 0))
        Instance.KObjectCount += 1

    # this definition exists because focused behavior needs one stable owner
    def PutObjRef(Instance, ObjectIndex: int) -> None:
        Instance.KBufferData.extend(EncodeObjectRef(ObjectIndex))
        Instance.KObjectCount += 1

    # this definition exists because focused behavior needs one stable owner
    def PutString(Instance, TextValue: str) -> None:
        Instance.KBufferData.extend(EncodeString(TextValue))

    # this definition exists because focused behavior needs one stable owner
    def EmitData(Instance) -> bytes:
        if Instance.KObjectCount < 1:
            raise SldprtFormatError("resolved features must contain an object")
        StreamHead = Struct.pack("<IH", 109, Instance.KObjectCount - 1)
        return StreamHead + bytes(Instance.KBufferData)


# this definition exists because class emission owns map and object counter updates
def PutClassMut(Writer: ResolveWriter, ClassName: str, SchemaCode: int = 1) -> int:
    KnownIndex = Writer.KClassIndex.get(ClassName)
    if KnownIndex is None:
        KnownIndex = Writer.KMapCounter
        ObjectIndex = Writer.KMapCounter + 1
        Writer.KClassIndex[ClassName] = KnownIndex
        Writer.KBufferData.extend(EncodeClassDefinition(ClassName, SchemaCode))
        Writer.KMapCounter += 2
    else:
        ObjectIndex = Writer.KMapCounter
        Writer.KBufferData.extend(EncodeClassRef(KnownIndex))
        Writer.KMapCounter += 1
    Writer.KObjectCount += 1
    return ObjectIndex


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class FeatureState:
    KNodeIdent: int
    KNodeName: str
    KNodeFlags: int
    KUpdateStamp: int = 101
    KVersionStamp: int = 2025268
    KCreatedHigh: int = 31269705
    KCreatedLow: int = 1613040660
    KAuthored: bool = False
    KHiddenCode: int = 0


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class PlaneState:
    KFeatureData: FeatureState
    KPickPoint: tuple[float, float, float]
    KNormalVec: tuple[float, float, float]
    KBasisMatrix: tuple[float, ...]
    KViewBounds: tuple[float, float, float, float]
    KLabelPoint: tuple[float, float, float]


# this definition exists because focused behavior needs one stable owner
def WriteVisProps(Writer: ResolveWriter) -> None:
    Writer.PutValues("<HHBIHhf", 65535, 0, 3, 4294967295, 65535, -1, -1.0)


# this definition exists because focused behavior needs one stable owner
def WriteNodeData(Writer: ResolveWriter, StateData: FeatureState) -> None:
    Writer.PutExtern(4)
    Writer.PutString(StateData.NodeName)
    Writer.PutValues("<IIII", 0, StateData.NodeFlags, StateData.NodeIdent, 0)
    Writer.PutString("")
    Writer.PutValues("<i", 0)


# this definition exists because focused behavior needs one stable owner
def WriteFeatData(Writer: ResolveWriter, StateData: FeatureState) -> None:
    Writer.PutNull()
    Writer.PutValues("<H", 0)
    WriteFeatTail(Writer, StateData)


# this definition exists because focused behavior needs one stable owner
def WriteFeatTail(Writer: ResolveWriter, StateData: FeatureState) -> None:
    Writer.PutValues("<i", 0)
    Writer.PutValues(
        "<iiIBiiiidi",
        0,
        0,
        StateData.UpdateStamp,
        0,
        0,
        18000 if StateData.Authored else 0,
        StateData.VersionStamp if StateData.Authored else 0,
        18000,
        0.0,
        StateData.VersionStamp,
    )
    Writer.PutNull()
    Writer.PutString("")
    Writer.PutValues("<B", 0)
    WriteVisProps(Writer)
    Writer.PutValues("<ii", 0, 0)
    Writer.PutNull()
    Writer.PutValues(
        "<IBBiiiIIHii",
        0,
        5,
        0,
        0,
        StateData.HiddenCode,
        -1,
        StateData.CreatedHigh,
        StateData.CreatedLow,
        2,
        360108,
        1,
    )


# this definition exists because focused behavior needs one stable owner
def WriteFolder(
    Writer: ResolveWriter,
    ClassName: str,
    StateData: FeatureState,
    FolderFlags: int = 0,
    FolderState: int = 0,
) -> None:
    Writer.PutClass(ClassName)
    WriteNodeData(Writer, StateData)
    WriteFeatData(Writer, StateData)
    Writer.PutValues("<ii", FolderFlags, FolderState)


# this definition exists because focused behavior needs one stable owner
def WriteSysFolder(
    Writer: ResolveWriter, ClassName: str, StateData: FeatureState
) -> None:
    SimpleClasses = {
        "moCommentsFolder_c",
        "moFavoriteFolder_c",
        "moSelectionSetFolder_c",
        "moSensorFolder_c",
        "moDocsFolder_c",
        "moSurfaceBodyFolder_c",
        "moSolidBodyFolder_c",
        "moInkMarkupFolder_c",
        "moEqnFolder_c",
        "moMaterialFolder_c",
    }
    if ClassName not in SimpleClasses:
        raise SldprtFormatError(f"unsupported simple folder class {ClassName!r}")
    FolderFlags = 0 if ClassName == "moCommentsFolder_c" else 1
    WriteFolder(Writer, ClassName, StateData, FolderFlags)
    if ClassName == "moFavoriteFolder_c":
        Writer.PutValues("<HHi", 0, 0, 1)
    elif ClassName == "moSelectionSetFolder_c":
        Writer.PutValues("<Hi", 0, 1)
    elif ClassName in {"moSurfaceBodyFolder_c", "moSolidBodyFolder_c"}:
        Writer.PutNull()
        Writer.PutNull()
        Writer.PutValues("<ii", 0, 0)
    elif ClassName == "moMaterialFolder_c":
        Writer.PutString("")
        Writer.PutValues("<i", 0)


# this definition exists because focused behavior needs one stable owner
def WriteHistItem(Writer: ResolveWriter, FeatureIdent: int, FeatureStamp: int) -> None:
    Writer.PutClass("moHistoryFeatItemData_c")
    Writer.PutNull()
    Writer.PutValues("<iiii", 1, 1073741824, -1, 0)
    Writer.PutString("")
    Writer.PutClass("moCompFeature_c")
    Writer.PutExtern(43)
    Writer.PutObjRef(2)
    Writer.PutValues(
        "<B10I4i5iIiI",
        0,
        *[0] * 10,
        *[-1] * 4,
        *[0] * 5,
        18000,
        FeatureIdent,
        FeatureStamp,
    )


# this definition exists because focused behavior needs one stable owner
def WriteHistory(
    Writer: ResolveWriter, StateData: FeatureState, FirstStamp: int
) -> None:
    WriteFolder(Writer, "moHistoryFolder_c", StateData, 1)
    Writer.PutValues("<H", 2)
    WriteHistItem(Writer, 26, FirstStamp)
    WriteHistItem(Writer, 32, FirstStamp + 1)


# this definition exists because focused behavior needs one stable owner
def WriteNotePair(
    Writer: ResolveWriter, FirstState: FeatureState, SecondState: FeatureState
) -> tuple[int, int]:
    FirstIndex = Writer.PutClass("moNotesAreaFtrFolder_c")
    WriteNodeData(Writer, FirstState)
    WriteFeatData(Writer, FirstState)
    Writer.PutValues("<ii", 1, 0)
    SecondIndex = Writer.PutClass("moNotesAreaFtrFolder_c")
    WriteNodeData(Writer, SecondState)
    WriteFeatData(Writer, SecondState)
    Writer.PutValues("<ii", 1, 0)
    Writer.PutObjRef(FirstIndex)
    Writer.PutValues("<iiii", 0, 0, 1, 1)
    Writer.PutValues("<iiii", 1, 0, 1, 1)
    return (FirstIndex, SecondIndex)


# this definition exists because focused behavior needs one stable owner
def WriteDetailTree(
    Writer: ResolveWriter,
    CabinetState: FeatureState,
    FirstState: FeatureState,
    SecondState: FeatureState,
) -> None:
    Writer.PutClass("moDetailCabinet_c")
    WriteNodeData(Writer, CabinetState)
    Writer.PutNull()
    Writer.PutValues("<H", 2)
    Ignored, SecondIndex = WriteNotePair(Writer, FirstState, SecondState)
    Writer.PutObjRef(SecondIndex)
    WriteFeatTail(Writer, CabinetState)
    Writer.PutValues("<iHddHii", 0, 0, 1.0, 1.0, 0, 0, 0)


# this definition exists because focused behavior needs one stable owner
def WriteEmpty(Writer: ResolveWriter) -> None:
    WriteEmptyHead(Writer)
    WriteEmptyTail(Writer)


# this definition exists because empty sketch headers form one native record section
def WriteEmptyHead(Writer: ResolveWriter) -> None:
    Writer.PutClass("sgSketch")
    Writer.PutValues("<iHii", 1, 0, 0, 1)
    Writer.PutValues("<HHBIHhf", 65535, 31, 3, 4294967295, 65535, -1, -1.0)
    Writer.PutValues("<i4Hhf", 1, 0, 4, 2, 1, 0, -1.0)
    Writer.PutNull()
    Writer.PutValues("<HHi", 4, 0, 0)
    Writer.PutNull()
    Writer.PutValues("<BdIIHddHH", 0, 1.0, 0, 0, 31, 0.0, 0.0, 1, 0)
    Writer.PutNull()
    Writer.PutNull()
    Writer.PutValues("<Hi4dHH", 0, -2, 0.0, 0.0, 0.0, 0.0, 0, 0)
    Writer.PutValues("<12i5Hi", *[0] * 12, 0, 0, 0, 0, 1, 0)
    Writer.PutNull()
    Writer.PutNull()
    Writer.PutValues("<4i", -1, 0, 0, 0)
    Writer.PutNull()


# this definition exists because empty sketch handles form one native record section
def WriteEmptyTail(Writer: ResolveWriter) -> None:
    Writer.PutValues("<HBi4H", 0, 0, 17, 2, 0, 0, 65534)
    Writer.PutValues("<H", 0)
    Writer.PutClass("sgPointHandle")
    Writer.PutValues("<Hii", 0, -1, 0)
    Writer.PutValues("<7H", *[0] * 7)
    Writer.PutExtern(82)
    Writer.PutValues("<7H", *[0] * 7)
    Writer.PutValues("<HHi", 2, 1, 1)
    Writer.PutValues("<15i", 2, *[1] * 12, 0, 1)
    Writer.PutValues("<4H", 0, 0, 0, 0)
    Writer.PutString("")
    Writer.PutValues(
        "<hfiii3dIiiHH5i",
        -1,
        -1.0,
        -1,
        1,
        -1,
        0.0,
        0.0,
        0.0,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    Writer.PutExtern(82)
    Writer.PutValues("<HH9i", 0, 0, *[0] * 9)
    Writer.PutValues("<iBiHIIH", 3, 1, 0, 0, 0, 100000, 0)


# this definition exists because focused behavior needs one stable owner
def WriteCompPlane(Writer: ResolveWriter, FeatureStamp: int) -> None:
    Writer.PutClass("moCompRefPlane_c")
    Writer.PutExtern(43)
    Writer.PutObjRef(2)
    Writer.PutValues(
        "<B10I4i5iIiI", 0, *[0] * 10, *[-1] * 4, *[0] * 5, 18000, 2, FeatureStamp
    )
    Writer.PutNull()
    Writer.PutValues("<iB4dBHH", 3, 0, 0.0, 0.0, 0.0, 1.0, 0, 0, 4)


# this definition exists because focused behavior needs one stable owner
def WriteOrigin(
    Writer: ResolveWriter, StateData: FeatureState, FeatureStamp: int
) -> None:
    Writer.PutClass("moOriginProfileFeature_c")
    WriteNodeData(Writer, StateData)
    WriteFeatData(Writer, StateData)
    Writer.PutValues("<ii", 0, 0)
    Writer.PutNull()
    Writer.PutValues("<i", 0)
    WriteEmpty(Writer)
    Writer.PutNull()
    WriteCompPlane(Writer, FeatureStamp)
    Writer.PutNull()
    Writer.PutValues("<iiIH", -7, 0, StateData.UpdateStamp, 0)
    Writer.PutNull()
    Writer.PutValues("<HHi", 0, 0, 0)


# this definition exists because focused behavior needs one stable owner
def WriteStockData(Writer: ResolveWriter, PlaneData: PlaneState) -> None:
    Writer.PutValues("<iHHHii", 0, 0, 0, 0, 0, 0)
    Writer.PutNull()
    Writer.PutValues("<iiiiHHHiHHi", 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    Writer.PutValues("<ii", 0, 1)
    Writer.PutNull()
    Writer.PutValues("<13i", *[0] * 13)
    Writer.PutValues("<3dii", *PlaneData.PickPoint, 5, 0)
    Writer.PutNull()
    Writer.PutValues("<i", 0)


# this definition exists because focused behavior needs one stable owner
def WritePlaneData(Writer: ResolveWriter, PlaneData: PlaneState) -> None:
    Writer.PutClass("moDefaultRefPlnData_c")
    Writer.PutValues("<3d3d", 0.0, 0.0, 0.0, *PlaneData.NormalVec)
    HasMatrix = bool(PlaneData.BasisMatrix)
    Writer.PutValues("<B", int(HasMatrix))
    if HasMatrix:
        if len(PlaneData.BasisMatrix) != 9:
            raise SldprtFormatError("reference plane basis must contain nine values")
        Writer.PutValues("<9d", *PlaneData.BasisMatrix)
    Writer.PutValues("<4dB", 0.0, 0.0, 0.0, 1.0, 0)
    Writer.PutValues("<4d", *PlaneData.ViewBounds)
    Writer.PutNull()
    Writer.PutValues("<iiiB", 0, -4, -4, 0)
    Writer.PutValues("<3diiH", *PlaneData.LabelPoint, 1, 0, 0)
    Writer.PutNull()
    Writer.PutNull()
    Writer.PutNull()


# this definition exists because focused behavior needs one stable owner
def WriteRefPlane(Writer: ResolveWriter, PlaneData: PlaneState) -> None:
    Writer.PutClass("moRefPlane_c")
    WriteNodeData(Writer, PlaneData.FeatureData)
    WriteFeatData(Writer, PlaneData.FeatureData)
    WriteStockData(Writer, PlaneData)
    WritePlaneData(Writer, PlaneData)


# this binding exists because shared behavior needs one stable value
globals()["WriteEmptySketch"] = WriteEmpty

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["dataclass"] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()["encode_class_definition"] = EncodeClassDefinition

# this binding exists because shared behavior needs one stable value
globals()["encode_class_reference"] = EncodeClassRef

# this binding exists because shared behavior needs one stable value
globals()["encode_object_reference"] = EncodeObjectRef

# this binding exists because shared behavior needs one stable value
globals()["encode_string"] = EncodeString

# this binding exists because shared behavior needs one stable value
globals()["field"] = Field

# this binding exists because shared behavior needs one stable value
globals()["struct"] = Struct
