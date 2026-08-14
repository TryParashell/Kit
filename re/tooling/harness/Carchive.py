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
KRootInfo = PathInfo(__file__).resolve().parents[3]
for CandInfo in (KRootInfo, KRootInfo / "src"):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
from convert.adapters.solidworks.container.Container import SldprtArchive


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
KNewClassTag = 65535

# needed to keep reverse engineering responsibilities isolated and maintainable
KClassTagBit = 32768

# needed to keep reverse engineering responsibilities isolated and maintainable
KBigObjectTag = 32767

# needed to keep reverse engineering responsibilities isolated and maintainable
KNullTag = 0

# needed to keep reverse engineering responsibilities isolated and maintainable
KStringInfo = bytes.fromhex("fffeff")

# needed to keep reverse engineering responsibilities isolated and maintainable
KMaxClassName = 64


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class ClassDefinition:
    TagOffset: int
    Schema: int
    NameTextInfo: str
    NameOffset: int
    DataOffset: int
    KAliasNames = {
        "tag_offset": "TagOffset",
        "schema": "Schema",
        "name": "NameTextInfo",
        "name_offset": "NameOffset",
        "data_offset": "DataOffset",
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
ClassDefinition.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class ClassReference:
    Offset: int
    IndexData: int
    KAliasNames = {"offset": "Offset", "index": "IndexData"}


# needed to keep reverse engineering responsibilities isolated and maintainable
ClassReference.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
def Stream(PathInfoData: PathInfo, NameTextInfo: str = KResolved) -> bytes:
    return SldprtArchive.open(PathInfoData).require(NameTextInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def StreamsInfo(PathInfoData: PathInfo) -> dict[str, bytes]:
    return SldprtArchive.open(PathInfoData).streams


# needed to keep reverse engineering responsibilities isolated and maintainable
def ClassDefns(ByteBlob: bytes) -> tuple[ClassDefinition, ...]:
    Result: list[ClassDefinition] = []
    Cursor = 0
    Limit = len(ByteBlob)
    while True:
        Offset = ByteBlob.find(b"\xff\xff", Cursor)
        if Offset < 0 or Offset + 6 > Limit:
            break
        Cursor = Offset + 1
        Schema, Length = Struct.unpack_from("<HH", ByteBlob, Offset + 2)
        if not 0 < Length <= KMaxClassName:
            continue
        StartRun = Offset + 6
        EndIndex = StartRun + Length
        if EndIndex > Limit:
            continue
        RawData = ByteBlob[StartRun:EndIndex]
        try:
            NameTextInfo = RawData.decode("ascii")
        except UnicodeDecodeError:
            continue
        if not NameTextInfo.replace("_", "").isalnum():
            continue
        Result.append(ClassDefinition(Offset, Schema, NameTextInfo, StartRun, EndIndex))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ClassIndexMap(ByteBlob: bytes) -> dict[str, int]:
    Defns = ClassDefns(ByteBlob)
    RefsInfo = ClassRefs(ByteBlob, Defns)
    Counts: dict[int, int] = {}
    for RefInfo in RefsInfo:
        Counts[RefInfo.index] = Counts.get(RefInfo.index, 0) + 1
    return {DefnInfo.name: DefnInfo.tag_offset for DefnInfo in Defns} | {
        f"#ref:{IndexData}": CountInfo
        for IndexData, CountInfo in sorted(Counts.items())
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def ClassRefs(
    ByteBlob: bytes, Defns: tuple[ClassDefinition, ...]
) -> tuple[ClassReference, ...]:
    Boundaries = DefnSpans(Defns)
    Result: list[ClassReference] = []
    for Offset in range(0, len(ByteBlob) - 1):
        if IsInside(Boundaries, Offset):
            continue
        Token = Struct.unpack_from("<H", ByteBlob, Offset)[0]
        if Token == KNewClassTag or not Token & KClassTagBit:
            continue
        Result.append(ClassReference(Offset, Token & ~KClassTagBit))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def NamedTokens(ByteBlob: bytes) -> dict[int, int]:
    Counts: dict[int, int] = {}
    Cursor = 0
    while True:
        Offset = ByteBlob.find(KStringInfo, Cursor)
        if Offset < 2:
            if Offset < 0:
                break
            Cursor = Offset + 1
            continue
        Cursor = Offset + 1
        Token = Struct.unpack_from("<H", ByteBlob, Offset - 2)[0]
        Counts[Token] = Counts.get(Token, 0) + 1
    return dict(sorted(Counts.items()))


# needed to keep reverse engineering responsibilities isolated and maintainable
def UnicodeStrings(ByteBlob: bytes) -> tuple[tuple[int, int, str], ...]:
    Result: list[tuple[int, int, str]] = []
    Cursor = 0
    while True:
        Offset = ByteBlob.find(KStringInfo, Cursor)
        if Offset < 0:
            break
        Cursor = Offset + 1
        UnitsOffset = Offset + 3
        if UnitsOffset >= len(ByteBlob):
            continue
        Units = ByteBlob[UnitsOffset]
        if Units == 0 or Units == 255:
            continue
        StartRun = UnitsOffset + 1
        EndIndex = StartRun + Units * 2
        if EndIndex > len(ByteBlob):
            continue
        try:
            TextValueData = ByteBlob[StartRun:EndIndex].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if any((not Character.isprintable() for Character in TextValueData)):
            continue
        Token = (
            Struct.unpack_from("<H", ByteBlob, Offset - 2)[0]
            if Offset >= 2
            else KNullTag
        )
        Result.append((Offset, Token, TextValueData))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def DefnSpans(Defns: tuple[ClassDefinition, ...]) -> tuple[tuple[int, int], ...]:
    return tuple(((DefnInfo.tag_offset, DefnInfo.data_offset) for DefnInfo in Defns))


# needed to keep reverse engineering responsibilities isolated and maintainable
def IsInside(Spans: tuple[tuple[int, int], ...], Offset: int) -> bool:
    for StartRun, EndIndex in Spans:
        if StartRun <= Offset < EndIndex:
            return True
    return False


# needed to keep reverse engineering responsibilities isolated and maintainable
def Hexdump(ByteBlob: bytes, Offset: int, WidthInfo: int = 64) -> str:
    StartRun = max(0, Offset)
    EndIndex = min(len(ByteBlob), Offset + WidthInfo)
    return ByteBlob[StartRun:EndIndex].hex(" ")
