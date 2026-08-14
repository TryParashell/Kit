# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from bisect import bisect_right as BisectRight
from dataclasses import dataclass as Dataclass
import math as MathValue
from pathlib import PureWindowsPath
import struct as Struct
from interchange import (
    Mesh as MeshValue,
    Provenance,
    ProvenanceSpan,
    Vector3 as VectorThree,
    frozen_mapping as FrozenMapping,
)
from convert.adapters.solidworks.container.Format import (
    ASSEMBLY_FORMAT_ID as AsmFormatId,
    DISPLAY_LISTS_STREAM as DisplayListsStream,
    SERIALIZED_STRING_MARKER as SerializedStringMarker,
    is_cad_path as IsCadPath,
    is_component_path as IsComponentPath,
)

# this binding exists because shared behavior needs one stable value
KArrayMarker = Struct.pack("<I", 4)


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeFace:
    locals().setdefault("__annotations__", {})
    __annotations__["offset"] = "int"
    __annotations__["record_length"] = "int"
    __annotations__["face_id"] = "int"
    __annotations__["strip_lengths"] = "tuple[int, ...]"
    __annotations__["positions_mm"] = "tuple[tuple[float, float, float], ...]"
    __annotations__["normals"] = "tuple[tuple[float, float, float], ...]"
    __annotations__["triangle_indices"] = "tuple[tuple[int, int, int], ...]"

    # this definition exists because focused behavior needs one stable owner
    @property
    def Positions(Instance) -> tuple[tuple[float, float, float], ...]:
        return Instance.positions_mm

    # this definition exists because focused behavior needs one stable owner
    def Triangles(Instance) -> tuple[tuple[int, int, int], ...]:
        return Instance.triangle_indices

    locals()["positions"] = Positions
    locals()["triangles"] = Triangles


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class NativeDisplay:
    locals().setdefault("__annotations__", {})
    __annotations__["occurrence_path"] = "str"
    __annotations__["source_path"] = "str"
    __annotations__["record_offset"] = "int"
    __annotations__["record_length"] = "int"
    __annotations__["faces"] = "tuple[NativeTessellationFace, ...]"


# this definition exists because focused behavior needs one stable owner
def DecodeFaces(DataValue: bytes) -> tuple[NativeFace, ...]:
    Result: list[NativeFace] = []
    Cursor = 8
    while True:
        Header = DataValue.find(KArrayMarker, Cursor)
        if Header < 0:
            break
        FaceValue = DecodeFace(DataValue, Header - 8)
        if FaceValue is None:
            Cursor = Header + len(KArrayMarker)
            continue
        Result.append(FaceValue)
        Cursor = FaceValue.offset + FaceValue.record_length
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def DecodeDisplay(DataValue: bytes) -> tuple[NativeDisplay, ...]:
    Faces = DecodeFaces(DataValue)
    Strings = Serialized(DataValue)
    Records: list[tuple[int, str, str]] = []
    for Index, (Offset, Value, Ignored) in enumerate(Strings):
        if not IsComponentPath(Value):
            continue
        NextComponent = next(
            (
                OtherOffset
                for OtherOffset, OtherValue, Ignored in Strings[Index + 1 :]
                if IsComponentPath(OtherValue)
            ),
            len(DataValue),
        )
        SourcePath = next(
            (
                OtherValue
                for OtherOffset, OtherValue, Ignored in Strings[Index + 1 :]
                if OtherOffset < NextComponent and IsCadPath(OtherValue)
            ),
            "",
        )
        Records.append((Offset, Value, SourcePath))
    Offsets = [Record[0] for Record in Records]
    Grouped: list[list[NativeFace]] = [[] for Ignored in Records]
    for FaceValue in Faces:
        Index = BisectRight(Offsets, FaceValue.offset) - 1
        if Index >= 0:
            Grouped[Index].append(FaceValue)
    Result: list[NativeDisplay] = []
    for Index, ((Offset, ItemPath, SourcePath), ComponentFaces) in enumerate(
        zip(Records, Grouped)
    ):
        if not ComponentFaces:
            continue
        EndValue = Records[Index + 1][0] if Index + 1 < len(Records) else len(DataValue)
        Result.append(
            NativeDisplay(
                occurrence_path=ItemPath,
                source_path=SourcePath,
                record_offset=Offset,
                record_length=EndValue - Offset,
                faces=tuple(ComponentFaces),
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def NeutralMeshes(
    Components: tuple[NativeDisplayComponent, ...],
) -> tuple[MeshValue, ...]:
    Result: list[MeshValue] = []
    for Component in Components:
        ComponentName = (
            PureWindowsPath(Component.source_path).stem
            if Component.source_path
            else Component.occurrence_path.split("@", 1)[0]
        )
        for FaceValue in Component.faces:
            MeshId = f"sldasm:mesh:{FaceValue.offset}"
            Result.append(
                MeshValue(
                    id=MeshId,
                    name=f"{ComponentName} face {FaceValue.face_id}",
                    vertices=tuple(
                        (VectorThree(*Point) for Point in FaceValue.positions_mm)
                    ),
                    triangles=FaceValue.triangle_indices,
                    normals=tuple(
                        (VectorThree(*Normal) for Normal in FaceValue.normals)
                    ),
                    provenance=Provenance(
                        adapter=AsmFormatId,
                        native_id=str(FaceValue.face_id),
                        spans=(
                            ProvenanceSpan(
                                DisplayListsStream,
                                FaceValue.offset,
                                FaceValue.record_length,
                                "tessellation-face",
                            ),
                        ),
                    ),
                    attributes=FrozenMapping(
                        {
                            "occurrence_path": Component.occurrence_path,
                            "source_path": Component.source_path,
                            "face_id": FaceValue.face_id,
                            "strip_lengths": FaceValue.strip_lengths,
                        }
                    ),
                )
            )
    return tuple(Result)


# channel extraction stays isolated because every array carries independent bounds and shape metadata
def ReadFaceChans(
    DataValue: bytes, Start: int, StripCount: int
) -> tuple[list[tuple[tuple[int, int, int, int], bytes]], int] | None:
    Channels: list[tuple[tuple[int, int, int, int], bytes]] = []
    Cursor = Start + 8
    for Ignored in range(6):
        if Cursor + 16 > len(DataValue):
            return None
        Header = Struct.unpack_from("<IIII", DataValue, Cursor)
        ItemSize, Ignored, Ignored, Count = Header
        if not 0 < ItemSize <= 64 or Count > 10000000:
            return None
        PayloadStart = Cursor + 16
        PayloadEnd = PayloadStart + ItemSize * Count
        if PayloadEnd > len(DataValue):
            return None
        Channels.append((Header, DataValue[PayloadStart:PayloadEnd]))
        Cursor = PayloadEnd
    return (Channels, Cursor)


# strip validation owns cross channel counts so decoding cannot trust inconsistent array headers
def GetStripLayout(
    Channels: list[tuple[tuple[int, int, int, int], bytes]], StripCount: int
) -> tuple[tuple[int, ...], int] | None:
    FirstHeader, FirstData = Channels[0]
    if FirstHeader != (4, 8, 2, StripCount):
        return None
    StripLengths = Struct.unpack(f"<{StripCount}I", FirstData)
    if min(StripLengths) < 3:
        return None
    VertexCount = sum(StripLengths)
    if VertexCount > 10000000:
        return None
    ThirdCount = Channels[3][0][3]
    ExpectedHeaders = (
        (4, 8, 2, StripCount),
        (12, 100, 2, VertexCount),
        (12, 100, 2, VertexCount),
        (4, 8, 2, ThirdCount),
        (4, 8, 2, StripCount),
        (1, 8, 2, ThirdCount),
    )
    if tuple((Channel[0] for Channel in Channels)) != ExpectedHeaders:
        return None
    return (StripLengths, VertexCount)


# face decoding composes bounded channel extraction shape validation and finite vector conversion
def DecodeFace(DataValue: bytes, Start: int) -> NativeFace | None:
    if Start < 0 or Start + 8 > len(DataValue):
        return None
    FaceId, StripCount = Struct.unpack_from("<II", DataValue, Start)
    if not 0 < StripCount <= 100000:
        return None
    ChannelResult = ReadFaceChans(DataValue, Start, StripCount)
    if ChannelResult is None:
        return None
    Channels, Cursor = ChannelResult
    StripLayout = GetStripLayout(Channels, StripCount)
    if StripLayout is None:
        return None
    StripLengths, VertexCount = StripLayout
    PositionValues = Struct.unpack(f"<{VertexCount * 3}f", Channels[1][1])
    NormalValues = Struct.unpack(f"<{VertexCount * 3}f", Channels[2][1])
    if not all(
        (MathValue.isfinite(Value) for Value in (*PositionValues, *NormalValues))
    ):
        return None
    PositionsMm = Vectors(PositionValues, 1000.0)
    Normals = Vectors(NormalValues, 1.0)
    return NativeFace(
        offset=Start,
        record_length=Cursor - Start,
        face_id=FaceId,
        strip_lengths=StripLengths,
        positions_mm=PositionsMm,
        normals=Normals,
        triangle_indices=Triangles(StripLengths),
    )


# this definition exists because focused behavior needs one stable owner
def Triangles(StripLengths: tuple[int, ...]) -> tuple[tuple[int, int, int], ...]:
    Result: list[tuple[int, int, int]] = []
    First = 0
    for Length in StripLengths:
        for Index in range(Length - 2):
            if Index % 2:
                Result.append((First + Index + 1, First + Index, First + Index + 2))
            else:
                Result.append((First + Index, First + Index + 1, First + Index + 2))
        First += Length
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def Vectors(
    Values: tuple[float, ...], Scale: float
) -> tuple[tuple[float, float, float], ...]:
    return tuple(
        (
            (
                Values[Index] * Scale,
                Values[Index + 1] * Scale,
                Values[Index + 2] * Scale,
            )
            for Index in range(0, len(Values), 3)
        )
    )


# this definition exists because focused behavior needs one stable owner
def Serialized(DataValue: bytes) -> tuple[tuple[int, str, int], ...]:
    Result: list[tuple[int, str, int]] = []
    Cursor = 0
    while True:
        Offset = DataValue.find(SerializedStringMarker, Cursor)
        if Offset < 0:
            break
        Cursor = Offset + 1
        LengthOffset = Offset + len(SerializedStringMarker)
        if LengthOffset >= len(DataValue):
            continue
        Length = DataValue[LengthOffset]
        StringStart = LengthOffset + 1
        StringEnd = StringStart + Length * 2
        if StringEnd > len(DataValue):
            continue
        try:
            Value = DataValue[StringStart:StringEnd].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if any((ord(Character) < 32 for Character in Value)):
            continue
        Result.append((Offset, Value, StringEnd))
    return tuple(Result)


# this binding exists because shared behavior needs one stable value
globals()["ASSEMBLY_FORMAT_ID"] = AsmFormatId

# this binding exists because shared behavior needs one stable value
globals()["DISPLAY_LISTS_STREAM"] = DisplayListsStream

# this binding exists because shared behavior needs one stable value
globals()["Mesh"] = MeshValue

# this binding exists because shared behavior needs one stable value
globals()["NativeDisplayComponent"] = NativeDisplay

# this binding exists because shared behavior needs one stable value
globals()["NativeTessellationFace"] = NativeFace

# this binding exists because shared behavior needs one stable value
globals()["SERIALIZED_STRING_MARKER"] = SerializedStringMarker

# this binding exists because shared behavior needs one stable value
globals()["Vector3"] = VectorThree

# this binding exists because shared behavior needs one stable value
globals()["_ARRAY_MARKER"] = KArrayMarker

# this binding exists because shared behavior needs one stable value
globals()["_decode_face"] = DecodeFace

# this binding exists because shared behavior needs one stable value
globals()["_serialized_strings"] = Serialized

# this binding exists because shared behavior needs one stable value
globals()["_triangles"] = Triangles

# this binding exists because shared behavior needs one stable value
globals()["_vectors"] = Vectors

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["bisect_right"] = BisectRight

# this binding exists because shared behavior needs one stable value
globals()["dataclass"] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()["decode_display_lists"] = DecodeDisplay

# this binding exists because shared behavior needs one stable value
globals()["decode_tessellation_faces"] = DecodeFaces

# this binding exists because shared behavior needs one stable value
globals()["frozen_mapping"] = FrozenMapping

# this binding exists because shared behavior needs one stable value
globals()["is_cad_path"] = IsCadPath

# this binding exists because shared behavior needs one stable value
globals()["is_component_path"] = IsComponentPath

# this binding exists because shared behavior needs one stable value
globals()["math"] = MathValue

# this binding exists because shared behavior needs one stable value
globals()["neutral_meshes"] = NeutralMeshes

# this binding exists because shared behavior needs one stable value
globals()["struct"] = Struct
