# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass
from pathlib import Path as PathInfo
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = KHereInfo.parents[2]
for CandInfo in (KHereInfo, KRootInfo, KRootInfo / "src"):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    _template_fields as TemplateFields,
)
from convert.adapters.solidworks import resolved as Resolvedlib
import Carchive as Carchive


# needed to keep reverse engineering responsibilities isolated and maintainable
def GetLegacyAttr(SelfRef, NameText):
    AliasName = SelfRef.KAliasNames.get(NameText)
    if AliasName is None:
        raise AttributeError(NameText)
    return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SetLegacyMut(SelfRef, NameText, ValueData):
    TargetName = SelfRef.KAliasNames.get(NameText, NameText)
    object.__setattr__(SelfRef, TargetName, ValueData)


# needed to keep reverse engineering responsibilities isolated and maintainable
KResolved = "Contents/Config-0-ResolvedFeatures"

# needed to keep reverse engineering responsibilities isolated and maintainable
KEYWORDS = "swXmlContents/KeyWords"

# needed to keep reverse engineering responsibilities isolated and maintainable
KFeatInfo = "swXmlContents/Features"

# needed to keep reverse engineering responsibilities isolated and maintainable
KPartition = "Contents/Config-0-Partition"

# needed to keep reverse engineering responsibilities isolated and maintainable
KCompFeatClass = "moCompFeature_c"

# needed to keep reverse engineering responsibilities isolated and maintainable
KCompStride = 119

# needed to keep reverse engineering responsibilities isolated and maintainable
KCompFirstEntry = 93

# needed to keep reverse engineering responsibilities isolated and maintainable
KCompBack = 8

# needed to keep reverse engineering responsibilities isolated and maintainable
KCompBackInfo = 4

# needed to keep reverse engineering responsibilities isolated and maintainable
KBossFlags = 1073742144

# needed to keep reverse engineering responsibilities isolated and maintainable
KBossFlagsAlt = 1073741888

# needed to keep reverse engineering responsibilities isolated and maintainable
KCutFlags = 1073873354

# needed to keep reverse engineering responsibilities isolated and maintainable
KSketchFlags = 1073741824

# needed to keep reverse engineering responsibilities isolated and maintainable
KPlaneFlags = 3221225472

# needed to keep reverse engineering responsibilities isolated and maintainable
KBlind = 0

# needed to keep reverse engineering responsibilities isolated and maintainable
KThroughAll = 1

# needed to keep reverse engineering responsibilities isolated and maintainable
KMidPlane = 6

# needed to keep reverse engineering responsibilities isolated and maintainable
KFirstBackInfo = 824

# needed to keep reverse engineering responsibilities isolated and maintainable
KFirstBack = 818

# needed to keep reverse engineering responsibilities isolated and maintainable
KLaterBackInfo = 721

# needed to keep reverse engineering responsibilities isolated and maintainable
KLaterBack = 715


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Donor:
    PathInfoData: PathInfo
    ByteBlob: bytes
    FileId: int
    FormatVersion: int
    Signatures: tuple[bytes, bytes, bytes]
    TypeIds: dict[str, int]
    Order: tuple[str, ...]
    StreamsInfo: dict[str, bytes]

    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def Resolved(SelfRef) -> bytes:
        return SelfRef.StreamsInfo[KResolved]

    KAliasNames = {
        "path": "PathInfoData",
        "blob": "ByteBlob",
        "file_id": "FileId",
        "format_version": "FormatVersion",
        "signatures": "Signatures",
        "type_ids": "TypeIds",
        "order": "Order",
        "streams": "StreamsInfo",
        "resolved": "Resolved",
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
Donor.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
def LoadDonor(PathInfoData: str | PathInfo) -> Donor:
    Source = PathInfo(PathInfoData)
    ByteBlob = Source.read_bytes()
    ArchiveInfo = SldprtArchive.from_bytes(ByteBlob)
    Signatures, TypeIds = TemplateFields(ByteBlob, ArchiveInfo)

    # needed to keep reverse engineering responsibilities isolated and maintainable
    Order = tuple(
        (
            Record.name
            for Record in sorted(
                ArchiveInfo.records, key=lambda ItemData: ItemData.offset
            )
        )
    )
    return Donor(
        PathInfoData=Source,
        ByteBlob=ByteBlob,
        FileId=ArchiveInfo.file_id,
        FormatVersion=ArchiveInfo.format_version,
        Signatures=Signatures,
        TypeIds=TypeIds,
        Order=Order,
        StreamsInfo=ArchiveInfo.streams,
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def Rebuild(
    DonorInfo: Donor,
    Replacements: dict[str, bytes],
    *,
    DropInfo: frozenset[str] = frozenset({KPartition}),
) -> bytes:
    from convert.adapters.solidworks.container.Container import (
        build_sldprt as BuildSldprt,
    )

    Items: list[tuple[str, bytes]] = []
    for NameTextInfo in DonorInfo.order:
        if NameTextInfo in DropInfo:
            continue
        Items.append(
            (
                NameTextInfo,
                Replacements.get(NameTextInfo, DonorInfo.streams[NameTextInfo]),
            )
        )
    for NameTextInfo, PayloadInfo in Replacements.items():
        if NameTextInfo not in DonorInfo.order:
            Items.append((NameTextInfo, PayloadInfo))
    return BuildSldprt(Items, template=DonorInfo.blob)


# needed to keep reverse engineering responsibilities isolated and maintainable
def CompFeatSpan(ByteBlob: bytes) -> tuple[int, int]:
    Defns = Carchive.ClassDefns(ByteBlob)
    for IndexData, DefnInfo in enumerate(Defns):
        if DefnInfo.name != KCompFeatClass:
            continue
        EndIndex = (
            Defns[IndexData + 1].tag_offset
            if IndexData + 1 < len(Defns)
            else len(ByteBlob)
        )
        return (DefnInfo.data_offset, EndIndex)
    raise KeyError(KCompFeatClass)


# needed to keep reverse engineering responsibilities isolated and maintainable
def CompFeatEntries(ByteBlob: bytes) -> tuple[tuple[int, int, int, int], ...]:
    StartRun, EndIndex = CompFeatSpan(ByteBlob)
    Total = EndIndex - StartRun
    if Total < KCompFirstEntry:
        raise ValueError("moCompFeature_c record is too short")
    RemainderInfo = Total - KCompFirstEntry
    if RemainderInfo % KCompStride:
        raise ValueError(
            f"moCompFeature_c record length {Total} is not {KCompFirstEntry} + n*{KCompStride}"
        )
    CountInfo = 1 + RemainderInfo // KCompStride
    Result: list[tuple[int, int, int, int]] = []
    Cursor = StartRun
    for IndexData in range(CountInfo):
        WidthInfo = KCompFirstEntry if IndexData == 0 else KCompStride
        EntryEnd = Cursor + WidthInfo
        FeatId = Struct.unpack_from("<I", ByteBlob, EntryEnd - KCompBack)[0]
        Stamp = Struct.unpack_from("<I", ByteBlob, EntryEnd - KCompBackInfo)[0]
        Result.append((Cursor, EntryEnd, FeatId, Stamp))
        Cursor = EntryEnd
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def FeatInfoInfo(ByteBlob: bytes) -> tuple[Resolvedlib.FeatureLayout, ...]:
    return Resolvedlib.locate_features(ByteBlob)


# needed to keep reverse engineering responsibilities isolated and maintainable
def TreeNodes(ByteBlob: bytes) -> tuple[Resolvedlib.NameRecord, ...]:
    return Resolvedlib.tree_nodes(ByteBlob)


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteUThirtyTwo(Output: bytearray, Offset: int, ValueInfo: int) -> None:
    Struct.pack_into("<I", Output, Offset, ValueInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteDouble(Output: bytearray, Offset: int, ValueInfo: float) -> None:
    Struct.pack_into("<d", Output, Offset, ValueInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadUThirtyTwo(ByteBlob: bytes, Offset: int) -> int:
    return Struct.unpack_from("<I", ByteBlob, Offset)[0]


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadDouble(ByteBlob: bytes, Offset: int) -> float:
    return Struct.unpack_from("<d", ByteBlob, Offset)[0]


# needed to keep reverse engineering responsibilities isolated and maintainable
def FlagOffsets(Ordinal: int, DepthOffset: int) -> tuple[int, int]:
    if Ordinal == 0:
        return (DepthOffset - KFirstBackInfo, DepthOffset - KFirstBack)
    return (DepthOffset - KLaterBackInfo, DepthOffset - KLaterBack)
