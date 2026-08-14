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
import json as JsonData
import re as Regex
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / 'grammar'
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Streamlib as Streamlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KEvent = Regex.compile('^(RO|RC) ([0-9a-fA-F]+) ([0-9a-fA-F]+) (\\d+)\\s*$')

# needed to keep reverse engineering responsibilities isolated and maintainable
KNewClassTag = 65535

# needed to keep reverse engineering responsibilities isolated and maintainable
KClassTagBit = 32768

# needed to keep reverse engineering responsibilities isolated and maintainable
KBigObjectTag = 32767

# needed to keep reverse engineering responsibilities isolated and maintainable
KNullTag = 0


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Event:
    KindNameInfo: str
    Buffer: int
    Offset: int
    CounterInfo: int
    KAliasNames = {'kind': 'KindNameInfo', 'buffer': 'Buffer', 'offset': 'Offset', 'counter': 'CounterInfo'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class TagInfo:
    Offset: int
    Token: int
    KindNameInfo: str
    Header: int
    Schema: int
    NameTextInfo: str
    IndexData: int
    KAliasNames = {'offset': 'Offset', 'token': 'Token', 'kind': 'KindNameInfo', 'header': 'Header', 'schema': 'Schema', 'name': 'NameTextInfo', 'index': 'IndexData'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadEvents(PathInfoData: PathInfo) -> tuple[Event, ...]:
    OutputDataInfo: list[Event] = []
    for RawData in PathInfoData.read_text(errors='replace').splitlines():
        Match = KEvent.match(RawData.strip())
        if Match is None:
            continue
        OutputDataInfo.append(Event(KindNameInfo=Match.group(1), Buffer=int(Match.group(2), 16), Offset=int(Match.group(3), 16), CounterInfo=int(Match.group(4))))
    return tuple(OutputDataInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def DecodeTag(ByteBlob: bytes, Offset: int) -> TagInfo:
    Token = Struct.unpack_from('<H', ByteBlob, Offset)[0]
    if Token == KNewClassTag:
        Schema, Length = Struct.unpack_from('<HH', ByteBlob, Offset + 2)
        NameTextInfo = ByteBlob[Offset + 6:Offset + 6 + Length].decode('ascii', 'replace')
        return TagInfo(Offset, Token, 'definition', 6 + Length, Schema, NameTextInfo, -1)
    if Token == KNullTag:
        return TagInfo(Offset, Token, 'null', 2, 0, '', -1)
    if Token == KBigObjectTag:
        IndexData = Struct.unpack_from('<I', ByteBlob, Offset + 2)[0]
        return TagInfo(Offset, Token, 'big', 6, 0, '', IndexData)
    if Token & KClassTagBit:
        return TagInfo(Offset, Token, 'classref', 2, 0, '', Token & ~KClassTagBit)
    return TagInfo(Offset, Token, 'objectref', 2, 0, '', Token)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Objects(Events: tuple[Event, ...]) -> tuple[Event, ...]:
    return tuple((EventInfo for EventInfo in Events if EventInfo.kind == 'RO'))


# needed to keep reverse engineering responsibilities isolated and maintainable
def DominantBuffer(Events: tuple[Event, ...]) -> int:
    Counts: dict[int, int] = {}
    for EventInfo in Events:
        Counts[EventInfo.buffer] = Counts.get(EventInfo.buffer, 0) + 1

    # needed to keep reverse engineering responsibilities isolated and maintainable
    return max(Counts, key=lambda KeyName: Counts[KeyName])


# needed to keep reverse engineering responsibilities isolated and maintainable
def DeltaFor(KindNameInfo: str) -> int:
    if KindNameInfo == 'definition':
        return 2
    if KindNameInfo in {'classref', 'big'}:
        return 1
    return 0


# needed to keep reverse engineering responsibilities isolated and maintainable
def Analyse(ByteBlob: bytes, LogInfo: PathInfo) -> dict[str, object]:
    Events = Objects(ReadEvents(LogInfo))
    Buffer = DominantBuffer(Events)
    Events = tuple((EventInfo for EventInfo in Events if EventInfo.buffer == Buffer))
    TagsInfo = [DecodeTag(ByteBlob, EventInfo.offset) for EventInfo in Events]
    Mismatch: list[str] = []
    for PosInfoInfo in range(len(Events) - 1):
        Expect = Events[PosInfoInfo].counter + DeltaFor(TagsInfo[PosInfoInfo].kind)
        ActualInfo = Events[PosInfoInfo + 1].counter
        if Expect != ActualInfo:
            Mismatch.append(f'{Events[PosInfoInfo].offset:#x} {TagsInfo[PosInfoInfo].kind} counter {Events[PosInfoInfo].counter} -> {ActualInfo} expected {Expect}')
    Monotonic = all((Events[PosInfoInfo].offset < Events[PosInfoInfo + 1].offset for PosInfoInfo in range(len(Events) - 1)))
    return {'log': LogInfo.name, 'buffer': f'{Buffer:#x}', 'stream_length': len(ByteBlob), 'events': len(Events), 'base_counter': Events[0].counter if Events else 0, 'monotonic_offsets': Monotonic, 'counter_rule_mismatches': Mismatch, 'kinds': {KindNameInfo: sum((1 for TagInfoInfo in TagsInfo if TagInfoInfo.kind == KindNameInfo)) for KindNameInfo in ('definition', 'classref', 'objectref', 'null', 'big')}, 'items': [{'offset': EventInfo.offset, 'counter': EventInfo.counter, 'kind': TagInfoInfo.kind, 'token': TagInfoInfo.token, 'index': TagInfoInfo.index, 'name': TagInfoInfo.name, 'schema': TagInfoInfo.schema, 'header': TagInfoInfo.header} for EventInfo, TagInfoInfo in zip(Events, TagsInfo)]}


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRunInfo() -> None:
    PartInfoInfo = PathInfo(System.argv[1]).resolve()
    LogInfo = PathInfo(System.argv[2]).resolve()
    Destination = PathInfo(System.argv[3]).resolve()
    ByteBlob = Streamlib.LoadDonor(PartInfoInfo).resolved
    Report = Analyse(ByteBlob, LogInfo)
    Destination.parent.mkdir(parents=True, exist_ok=True)
    Destination.write_text(JsonData.dumps(Report, indent=2), encoding='utf-8')
    print(f"stream={Report['stream_length']} events={Report['events']}")
    print(f"base_counter={Report['base_counter']}")
    print(f"monotonic_offsets={Report['monotonic_offsets']}")
    print(f"kinds={Report['kinds']}")
    print(f"counter_rule_mismatches={len(Report['counter_rule_mismatches'])}")
    for TextValueData in Report['counter_rule_mismatches'][:20]:
        print(f'  {TextValueData}')
if __name__ == '__main__':
    MainRunInfo()
