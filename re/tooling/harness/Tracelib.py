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
import re as Regex
import struct as Struct
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
KEvent = Regex.compile('^(RO|RC) ([0-9a-fA-F]+) ([0-9a-fA-F]+) (\\d+)\\s*$')

# needed to keep reverse engineering responsibilities isolated and maintainable
KNewClassTag = 65535

# needed to keep reverse engineering responsibilities isolated and maintainable
KClassTagBit = 32768

# needed to keep reverse engineering responsibilities isolated and maintainable
KNullTag = 0

# needed to keep reverse engineering responsibilities isolated and maintainable
KBigObjectTag = 32767


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Event:
    KindNameInfo: str
    Buffer: int
    Offset: int
    CounterInfo: int
    KAliasNames = {'kind': 'KindNameInfo', 'buffer': 'Buffer', 'offset': 'Offset', 'counter': 'CounterInfo'}

# needed to keep reverse engineering responsibilities isolated and maintainable
Event.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Segment:
    IndexData: int
    Offset: int
    EndIndex: int
    TagInfoInfo: int
    TagKind: str
    ClassIndex: int
    ClassNameData: str
    CounterInfo: int
    Header: int


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def Length(SelfRef) -> int:
        return SelfRef.EndIndex - SelfRef.Offset


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def BodyOffset(SelfRef) -> int:
        return SelfRef.Offset + SelfRef.Header


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def BodyLength(SelfRef) -> int:
        return SelfRef.EndIndex - SelfRef.Offset - SelfRef.Header
    KAliasNames = {'index': 'IndexData', 'offset': 'Offset', 'end': 'EndIndex', 'tag': 'TagInfoInfo', 'tag_kind': 'TagKind', 'class_index': 'ClassIndex', 'class_name': 'ClassNameData', 'counter': 'CounterInfo', 'header': 'Header', 'length': 'Length', 'body_offset': 'BodyOffset', 'body_length': 'BodyLength'}

# needed to keep reverse engineering responsibilities isolated and maintainable
Segment.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadEvents(PathInfoData: PathInfo) -> tuple[Event, ...]:
    Result: list[Event] = []
    for RawData in PathInfoData.read_text(errors='replace').splitlines():
        Match = KEvent.match(RawData.strip())
        if not Match:
            continue
        Result.append(Event(KindNameInfo=Match.group(1), Buffer=int(Match.group(2), 16), Offset=int(Match.group(3), 16), CounterInfo=int(Match.group(4))))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ObjectEvents(Events: tuple[Event, ...]) -> tuple[Event, ...]:
    return tuple((EventInfo for EventInfo in Events if EventInfo.kind == 'RO'))


# needed to keep reverse engineering responsibilities isolated and maintainable
def DominantBuffer(Events: tuple[Event, ...]) -> int:
    Counts: dict[int, int] = {}
    for EventInfo in Events:
        Counts[EventInfo.buffer] = Counts.get(EventInfo.buffer, 0) + 1

    # needed to keep reverse engineering responsibilities isolated and maintainable
    return max(Counts, key=lambda KeyName: Counts[KeyName])


# needed to keep reverse engineering responsibilities isolated and maintainable
def TagAt(ByteBlob: bytes, Offset: int) -> tuple[int, str, int]:
    Token = Struct.unpack_from('<H', ByteBlob, Offset)[0]
    if Token == KNewClassTag:
        Length = Struct.unpack_from('<H', ByteBlob, Offset + 4)[0]
        return (Token, 'definition', 6 + Length)
    if Token == KNullTag:
        return (Token, 'null', 2)
    if Token == KBigObjectTag:
        return (Token, 'big', 6)
    if Token & KClassTagBit:
        return (Token, 'classref', 2)
    return (Token, 'objectref', 2)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SegmentInfo(ByteBlob: bytes, Events: tuple[Event, ...], *, Buffer: int | None=None) -> tuple[Segment, ...]:
    Objects = ObjectEvents(Events)
    if not Objects:
        return ()
    Target = DominantBuffer(Objects) if Buffer is None else Buffer
    Offsets = sorted({EventInfo.offset for EventInfo in Objects if EventInfo.buffer == Target})
    Counters = {}
    for EventInfo in Objects:
        if EventInfo.buffer == Target:
            Counters.setdefault(EventInfo.offset, EventInfo.counter)
    Result: list[Segment] = []
    Names: dict[int, str] = {}
    CounterInfo = 0
    for PosInfoInfo, Offset in enumerate(Offsets):
        EndIndex = Offsets[PosInfoInfo + 1] if PosInfoInfo + 1 < len(Offsets) else len(ByteBlob)
        Token, KindNameInfo, Header = TagAt(ByteBlob, Offset)
        if KindNameInfo == 'definition':
            Length = Struct.unpack_from('<H', ByteBlob, Offset + 4)[0]
            NameTextInfo = ByteBlob[Offset + 6:Offset + 6 + Length].decode('ascii', 'replace')
            CounterInfo += 1
            Names[CounterInfo] = NameTextInfo
            ClassIndex = CounterInfo
            CounterInfo += 1
        elif KindNameInfo == 'classref':
            ClassIndex = Token & ~KClassTagBit
            NameTextInfo = Names.get(ClassIndex, f'#{ClassIndex}')
            CounterInfo += 1
        else:
            ClassIndex = 0
            NameTextInfo = KindNameInfo
        Result.append(Segment(IndexData=PosInfoInfo, Offset=Offset, EndIndex=EndIndex, TagInfoInfo=Token, TagKind=KindNameInfo, ClassIndex=ClassIndex, ClassNameData=NameTextInfo, CounterInfo=Counters[Offset], Header=Header))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def DefnNames(ByteBlob: bytes) -> dict[int, str]:
    return {DefnInfo.tag_offset: DefnInfo.name for DefnInfo in Carchive.ClassDefns(ByteBlob)}
