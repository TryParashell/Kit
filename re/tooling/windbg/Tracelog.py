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

# needed to keep reverse engineering responsibilities isolated and maintainable
KEvent = Regex.compile('^(RO|RC) ([0-9a-fA-F`]+) ([0-9a-fA-F]+) (\\d+) ([0-9a-fA-F`]+)(?: ([0-9a-fA-F`]+))?\\s*$')

# needed to keep reverse engineering responsibilities isolated and maintainable
KCalib = Regex.compile('^CALIB (\\d+) this=([0-9a-fA-F`]+)\\s*$')

# needed to keep reverse engineering responsibilities isolated and maintainable
KDumpInfo = Regex.compile('^([0-9a-fA-F`]+)\\s+((?:[0-9a-fA-F`]{17}\\s*)+)$')

# needed to keep reverse engineering responsibilities isolated and maintainable
KQword = Regex.compile('([0-9a-fA-F]{8})`([0-9a-fA-F]{8})')


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Event:
    KindNameInfo: str
    Buffer: int
    Offset: int
    CounterInfo: int
    RspInfo: int
    SpanInfo: int = 0
    KAliasNames = {'kind': 'KindNameInfo', 'buffer': 'Buffer', 'offset': 'Offset', 'counter': 'CounterInfo', 'rsp': 'RspInfo', 'span': 'SpanInfo'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class DumpRecord:
    IndexData: int
    ThisValue: int
    Words: tuple[int, ...]


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def UintWide(SelfRef, Offset: int) -> int:
        return int.from_bytes(SelfRef.RawData[Offset:Offset + 8], 'little')


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def UintLong(SelfRef, Offset: int) -> int:
        return int.from_bytes(SelfRef.RawData[Offset:Offset + 4], 'little')


    # needed to keep reverse engineering responsibilities isolated and maintainable
    @property
    def RawData(SelfRef) -> bytes:
        OutputDataInfo = bytearray()
        for WordDataInfo in SelfRef.Words:
            OutputDataInfo += WordDataInfo.to_bytes(8, 'little')
        return bytes(OutputDataInfo)
    KAliasNames = {'index': 'IndexData', 'this': 'ThisValue', 'words': 'Words', 'u64': 'UintWide', 'u32': 'UintLong', 'raw': 'RawData'}


    # needed to keep reverse engineering responsibilities isolated and maintainable
    def __getattr__(SelfRef, NameText):
        AliasName = SelfRef.KAliasNames.get(NameText)
        if AliasName is None:
            raise AttributeError(NameText)
        return getattr(SelfRef, AliasName)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Hexint(TextValueData: str) -> int:
    return int(TextValueData.replace('`', ''), 16)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadEvents(LogInfo: PathInfo) -> tuple[Event, ...]:
    Result: list[Event] = []
    for RawData in LogInfo.read_text(errors='replace').splitlines():
        Match = KEvent.match(RawData.strip())
        if Match is None:
            continue
        Result.append(Event(KindNameInfo=Match.group(1), Buffer=Hexint(Match.group(2)), Offset=int(Match.group(3), 16), CounterInfo=int(Match.group(4)), RspInfo=Hexint(Match.group(5)), SpanInfo=Hexint(Match.group(6)) if Match.group(6) else 0))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def BuffersForSpan(Events: tuple[Event, ...], SpanInfo: int) -> dict[int, int]:
    Counts: dict[int, int] = {}
    for EventInfo in Events:
        if EventInfo.kind != 'RO' or EventInfo.span != SpanInfo:
            continue
        Counts[EventInfo.buffer] = Counts.get(EventInfo.buffer, 0) + 1
    return Counts


# needed to keep reverse engineering responsibilities isolated and maintainable
def BusiestBuffer(Events: tuple[Event, ...], SpanInfo: int) -> int:
    Counts = BuffersForSpan(Events, SpanInfo)
    if not Counts:
        raise ValueError(f'no ReadObject events for span {SpanInfo}')

    # needed to keep reverse engineering responsibilities isolated and maintainable
    return max(Counts, key=lambda KeyName: Counts[KeyName])


# needed to keep reverse engineering responsibilities isolated and maintainable
def ReadDumps(LogInfo: PathInfo) -> tuple[DumpRecord, ...]:
    Result: list[DumpRecord] = []
    IndexData = 0
    ThisValue = 0
    Words: list[int] = []
    Active = False
    for RawData in LogInfo.read_text(errors='replace').splitlines():
        LineText = RawData.strip()
        HeadInfo = KCalib.match(LineText)
        if HeadInfo is not None:
            if Active:
                Result.append(DumpRecord(IndexData, ThisValue, tuple(Words)))
            IndexData = int(HeadInfo.group(1))
            ThisValue = Hexint(HeadInfo.group(2))
            Words = []
            Active = True
            continue
        if not Active:
            continue
        RowDataInfo = KDumpInfo.match(LineText)
        if RowDataInfo is None:
            continue
        for HighValue, LowValue in KQword.findall(RowDataInfo.group(2)):
            Words.append(int(HighValue + LowValue, 16))
    if Active:
        Result.append(DumpRecord(IndexData, ThisValue, tuple(Words)))
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def DominantBuffer(Events: tuple[Event, ...]) -> int:
    Counts: dict[int, int] = {}
    for EventInfo in Events:
        Counts[EventInfo.buffer] = Counts.get(EventInfo.buffer, 0) + 1
    if not Counts:
        raise ValueError('no trace events in log')

    # needed to keep reverse engineering responsibilities isolated and maintainable
    return max(Counts, key=lambda KeyName: Counts[KeyName])
