# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass, field
import struct

from .archive import (
    encode_class_definition,
    encode_class_reference,
    encode_object_reference,
    encode_string,
)
from .container import SldprtFormatError


# archive state belongs together so object framing cannot drift from payloads
@dataclass(slots=True)
class ResolveWriter:
    BufferData: bytearray = field(default_factory=bytearray)
    MapCounter: int = 109
    ObjectCount: int = 0
    ClassIndex: dict[str, int] = field(default_factory=dict)

    # callers need typed scalar writes without constructing binary fragments
    def PutValues(self, FormatText: str, *FieldValues: object) -> None:
        self.BufferData.extend(struct.pack(FormatText, *FieldValues))

    # class framing must update both archive maps exactly once
    def PutClass(self, ClassName: str, SchemaCode: int = 1) -> int:
        KnownIndex = self.ClassIndex.get(ClassName)
        if KnownIndex is None:
            KnownIndex = self.MapCounter
            ObjectIndex = self.MapCounter + 1
            self.ClassIndex[ClassName] = KnownIndex
            self.BufferData.extend(encode_class_definition(ClassName, SchemaCode))
            self.MapCounter += 2
        else:
            ObjectIndex = self.MapCounter
            self.BufferData.extend(encode_class_reference(KnownIndex))
            self.MapCounter += 1
        self.ObjectCount += 1
        return ObjectIndex

    # externally registered classes must still advance the local object map
    def PutExtern(self, ClassIndex: int) -> None:
        self.BufferData.extend(encode_class_reference(ClassIndex))
        self.MapCounter += 1
        self.ObjectCount += 1

    # optional object fields need an explicit archive object token
    def PutNull(self) -> None:
        self.BufferData.extend(struct.pack("<H", 0))
        self.ObjectCount += 1

    # shared archive objects preserve identity through their assigned index
    def PutObjRef(self, ObjectIndex: int) -> None:
        self.BufferData.extend(encode_object_reference(ObjectIndex))
        self.ObjectCount += 1

    # serialized strings need one canonical length implementation everywhere
    def PutString(self, TextValue: str) -> None:
        self.BufferData.extend(encode_string(TextValue))

    # callers need completed stream framing after all objects are known
    def EmitData(self) -> bytes:
        if self.ObjectCount < 1:
            raise SldprtFormatError("resolved features must contain an object")
        StreamHead = struct.pack("<IH", 109, self.ObjectCount - 1)
        return StreamHead + bytes(self.BufferData)


# feature defaults separate semantic state from binary field ordering
@dataclass(frozen=True, slots=True)
class FeatureState:
    NodeIdent: int
    NodeName: str
    NodeFlags: int
    UpdateStamp: int = 101
    VersionStamp: int = 2025268
    CreatedHigh: int = 31269705
    CreatedLow: int = 1613040660
    Authored: bool = False
    HiddenCode: int = 0


# plane display and basis fields vary independently from feature identity
@dataclass(frozen=True, slots=True)
class PlaneState:
    FeatureData: FeatureState
    PickPoint: tuple[float, float, float]
    NormalVec: tuple[float, float, float]
    BasisMatrix: tuple[float, ...]
    ViewBounds: tuple[float, float, float, float]
    LabelPoint: tuple[float, float, float]


# visibility defaults are shared by every ordinary feature tree node
def WriteVisProps(Writer: ResolveWriter) -> None:
    Writer.PutValues("<HHBIHhf", 0xFFFF, 0, 3, 0xFFFFFFFF, 0xFFFF, -1, -1.0)


# node identity must precede all inherited feature state in this archive
def WriteNodeData(Writer: ResolveWriter, StateData: FeatureState) -> None:
    Writer.PutExtern(4)
    Writer.PutString(StateData.NodeName)
    Writer.PutValues(
        "<IIII",
        0,
        StateData.NodeFlags,
        StateData.NodeIdent,
        0,
    )
    Writer.PutString("")
    Writer.PutValues("<i", 0)


# inherited feature fields need one implementation across every concrete class
def WriteFeatData(Writer: ResolveWriter, StateData: FeatureState) -> None:
    Writer.PutNull()
    Writer.PutValues("<H", 0)
    WriteFeatTail(Writer, StateData)


# feature list owners resume inherited fields after their nested object list
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


# ordinary folders share one fully recovered inherited record
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


# system folders need their concrete empty collection fields after shared state
def WriteSysFolder(
    Writer: ResolveWriter,
    ClassName: str,
    StateData: FeatureState,
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


# history records keep feature identifiers stable before authored nodes
def WriteHistItem(
    Writer: ResolveWriter,
    FeatureIdent: int,
    FeatureStamp: int,
) -> None:
    Writer.PutClass("moHistoryFeatItemData_c")
    Writer.PutNull()
    Writer.PutValues("<iiii", 1, 0x40000000, -1, 0)
    Writer.PutString("")
    Writer.PutClass("moCompFeature_c")
    Writer.PutExtern(43)
    Writer.PutObjRef(2)
    Writer.PutValues(
        "<B10I4i5iIiI",
        0,
        *([0] * 10),
        *([-1] * 4),
        *([0] * 5),
        18000,
        FeatureIdent,
        FeatureStamp,
    )


# the history folder reserves native identifiers used by the first feature pair
def WriteHistory(
    Writer: ResolveWriter,
    StateData: FeatureState,
    FirstStamp: int,
) -> None:
    WriteFolder(Writer, "moHistoryFolder_c", StateData, 1)
    Writer.PutValues("<H", 2)
    WriteHistItem(Writer, 26, FirstStamp)
    WriteHistItem(Writer, 32, FirstStamp + 1)


# paired note folders keep their native linked list without a donor payload
def WriteNotePair(
    Writer: ResolveWriter,
    FirstState: FeatureState,
    SecondState: FeatureState,
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
    return FirstIndex, SecondIndex


# annotation cabinet state owns the note pair and display arrow defaults
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
    _, SecondIndex = WriteNotePair(Writer, FirstState, SecondState)
    Writer.PutObjRef(SecondIndex)
    WriteFeatTail(Writer, CabinetState)
    Writer.PutValues("<iHddHii", 0, 0, 1.0, 1.0, 0, 0, 0)


# origin sketches need a complete empty constraint system for native editing
def WriteEmptySketch(Writer: ResolveWriter) -> None:
    Writer.PutClass("sgSketch")
    Writer.PutValues("<iHii", 1, 0, 0, 1)
    Writer.PutValues("<HHBIHhf", 0xFFFF, 31, 3, 0xFFFFFFFF, 0xFFFF, -1, -1.0)
    Writer.PutValues("<i4Hhf", 1, 0, 4, 2, 1, 0, -1.0)
    Writer.PutNull()
    Writer.PutValues("<HHi", 4, 0, 0)
    Writer.PutNull()
    Writer.PutValues("<BdIIHddHH", 0, 1.0, 0, 0, 31, 0.0, 0.0, 1, 0)
    Writer.PutNull()
    Writer.PutNull()
    Writer.PutValues("<Hi4dHH", 0, -2, 0.0, 0.0, 0.0, 0.0, 0, 0)
    Writer.PutValues("<12i5Hi", *([0] * 12), 0, 0, 0, 0, 1, 0)
    Writer.PutNull()
    Writer.PutNull()
    Writer.PutValues("<4i", -1, 0, 0, 0)
    Writer.PutNull()
    Writer.PutValues("<HBi4H", 0, 0, 17, 2, 0, 0, 0xFFFE)
    Writer.PutValues("<H", 0)
    Writer.PutClass("sgPointHandle")
    Writer.PutValues("<Hii", 0, -1, 0)
    Writer.PutValues("<7H", *([0] * 7))
    Writer.PutExtern(82)
    Writer.PutValues("<7H", *([0] * 7))
    Writer.PutValues("<HHi", 2, 1, 1)
    Writer.PutValues("<15i", 2, *([1] * 12), 0, 1)
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
    Writer.PutValues("<HH9i", 0, 0, *([0] * 9))
    Writer.PutValues("<iBiHIIH", 3, 1, 0, 0, 0, 100000, 0)


# sketch support references need native component identity and transform state
def WriteCompPlane(Writer: ResolveWriter, FeatureStamp: int) -> None:
    Writer.PutClass("moCompRefPlane_c")
    Writer.PutExtern(43)
    Writer.PutObjRef(2)
    Writer.PutValues(
        "<B10I4i5iIiI",
        0,
        *([0] * 10),
        *([-1] * 4),
        *([0] * 5),
        18000,
        2,
        FeatureStamp,
    )
    Writer.PutNull()
    Writer.PutValues("<iB4dBHH", 3, 0, 0.0, 0.0, 0.0, 1.0, 0, 0, 4)


# the origin owns an empty editable sketch and its principal plane reference
def WriteOrigin(
    Writer: ResolveWriter,
    StateData: FeatureState,
    FeatureStamp: int,
) -> None:
    Writer.PutClass("moOriginProfileFeature_c")
    WriteNodeData(Writer, StateData)
    WriteFeatData(Writer, StateData)
    Writer.PutValues("<ii", 0, 0)
    Writer.PutNull()
    Writer.PutValues("<i", 0)
    WriteEmptySketch(Writer)
    Writer.PutNull()
    WriteCompPlane(Writer, FeatureStamp)
    Writer.PutNull()
    Writer.PutValues("<iiIH", -7, 0, StateData.UpdateStamp, 0)
    Writer.PutNull()
    Writer.PutValues("<HHi", 0, 0, 0)


# reference geometry retains stable stock state before its plane definition
def WriteStockData(Writer: ResolveWriter, PlaneData: PlaneState) -> None:
    Writer.PutValues("<iHHHii", 0, 0, 0, 0, 0, 0)
    Writer.PutNull()
    Writer.PutValues("<iiiiHHHiHHi", 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    Writer.PutValues("<ii", 0, 1)
    Writer.PutNull()
    Writer.PutValues("<13i", *([0] * 13))
    Writer.PutValues("<3dii", *PlaneData.PickPoint, 5, 0)
    Writer.PutNull()
    Writer.PutValues("<i", 0)


# principal planes need authored bases so sketches preserve support orientation
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


# every generated part needs editable principal reference planes
def WriteRefPlane(Writer: ResolveWriter, PlaneData: PlaneState) -> None:
    Writer.PutClass("moRefPlane_c")
    WriteNodeData(Writer, PlaneData.FeatureData)
    WriteFeatData(Writer, PlaneData.FeatureData)
    WriteStockData(Writer, PlaneData)
    WritePlaneData(Writer, PlaneData)
