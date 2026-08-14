# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from dataclasses import dataclass as DataClass
import struct as Struct


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
KNewClassTag = 65535

# needed to keep reverse engineering responsibilities isolated and maintainable
KClassTagBit = 32768

# needed to keep reverse engineering responsibilities isolated and maintainable
KBigObjectTag = 32767

# needed to keep reverse engineering responsibilities isolated and maintainable
KNullTag = 0

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefnInfo = "definition"

# needed to keep reverse engineering responsibilities isolated and maintainable
KClassref = "classref"

# needed to keep reverse engineering responsibilities isolated and maintainable
KObjectref = "objectref"

# needed to keep reverse engineering responsibilities isolated and maintainable
KNullInfo = "null"

# needed to keep reverse engineering responsibilities isolated and maintainable
KBigInfo = "big"

# needed to keep reverse engineering responsibilities isolated and maintainable
KMaxClassName = 64


# needed to keep reverse engineering responsibilities isolated and maintainable
class ArchiveError(Exception):
    pass


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
    KAliasNames = {
        "offset": "Offset",
        "token": "Token",
        "kind": "KindNameInfo",
        "header": "Header",
        "schema": "Schema",
        "name": "NameTextInfo",
        "index": "IndexData",
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
TagInfo.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Object:
    Order: int
    Offset: int
    EndIndex: int
    KindNameInfo: str
    Token: int
    ClassSlot: int
    ObjectSlot: int
    ClassNameData: str
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

    KAliasNames = {
        "order": "Order",
        "offset": "Offset",
        "end": "EndIndex",
        "kind": "KindNameInfo",
        "token": "Token",
        "class_slot": "ClassSlot",
        "object_slot": "ObjectSlot",
        "class_name": "ClassNameData",
        "header": "Header",
        "length": "Length",
        "body_offset": "BodyOffset",
        "body_length": "BodyLength",
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
Object.__getattr__ = GetLegacyAttr


# needed to keep reverse engineering responsibilities isolated and maintainable
def DecodeTag(ByteBlob: bytes, Offset: int) -> TagInfo:
    if Offset + 2 > len(ByteBlob):
        raise ArchiveError(f"tag at {Offset} runs past end of stream {len(ByteBlob)}")
    Token = Struct.unpack_from("<H", ByteBlob, Offset)[0]
    if Token == KNewClassTag:
        Schema, Length = Struct.unpack_from("<HH", ByteBlob, Offset + 2)
        if not 0 < Length <= KMaxClassName:
            raise ArchiveError(f"class name length {Length} at {Offset} is implausible")
        RawData = ByteBlob[Offset + 6 : Offset + 6 + Length]
        return TagInfo(
            Offset, Token, KDefnInfo, 6 + Length, Schema, RawData.decode("ascii"), -1
        )
    if Token == KNullTag:
        return TagInfo(Offset, Token, KNullInfo, 2, 0, "", -1)
    if Token == KBigObjectTag:
        IndexData = Struct.unpack_from("<I", ByteBlob, Offset + 2)[0]
        KindNameInfo = KClassref if IndexData & 2147483648 else KObjectref
        return TagInfo(Offset, Token, KBigInfo, 6, 0, "", IndexData & 2147483647)
    if Token & KClassTagBit:
        return TagInfo(Offset, Token, KClassref, 2, 0, "", Token & ~KClassTagBit)
    return TagInfo(Offset, Token, KObjectref, 2, 0, "", Token)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SlotsConsumed(KindNameInfo: str) -> int:
    if KindNameInfo == KDefnInfo:
        return 2
    if KindNameInfo in (KClassref, KBigInfo):
        return 1
    return 0


# needed to keep reverse engineering responsibilities isolated and maintainable
def Allocate(
    TagsInfo: tuple[TagInfo, ...], BaseInfo: int, EndsInfo: tuple[int, ...]
) -> tuple[Object, ...]:
    CounterInfo = BaseInfo
    Result: list[Object] = []
    Names: dict[int, str] = {}
    for Order, (TagInfoInfo, EndIndex) in enumerate(zip(TagsInfo, EndsInfo)):
        if TagInfoInfo.kind == KDefnInfo:
            ClassSlot = CounterInfo
            ObjectSlot = CounterInfo + 1
            Names[ClassSlot] = TagInfoInfo.name
            CounterInfo += 2
            NameTextInfo = TagInfoInfo.name
        elif TagInfoInfo.kind in (KClassref, KBigInfo):
            ClassSlot = TagInfoInfo.index
            ObjectSlot = CounterInfo
            CounterInfo += 1
            NameTextInfo = Names.get(TagInfoInfo.index, "")
        else:
            ClassSlot = -1
            ObjectSlot = -1
            NameTextInfo = TagInfoInfo.kind
        Result.append(
            Object(
                Order=Order,
                Offset=TagInfoInfo.offset,
                EndIndex=EndIndex,
                KindNameInfo=TagInfoInfo.kind,
                Token=TagInfoInfo.token,
                ClassSlot=ClassSlot,
                ObjectSlot=ObjectSlot,
                ClassNameData=NameTextInfo,
                Header=TagInfoInfo.header,
            )
        )
    return tuple(Result)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ClassTable(Objects: tuple[Object, ...]) -> dict[int, str]:
    return {
        ItemData.class_slot: ItemData.class_name
        for ItemData in Objects
        if ItemData.kind == KDefnInfo
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def NextSlot(Objects: tuple[Object, ...], BaseInfo: int) -> int:
    CounterInfo = BaseInfo
    for ItemData in Objects:
        CounterInfo += SlotsConsumed(ItemData.kind)
    return CounterInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def EncodeRef(KindNameInfo: str, IndexData: int) -> bytes:
    if KindNameInfo == KClassref:
        if IndexData >= KBigObjectTag:
            raise ArchiveError(f"class index {IndexData} needs the big-object escape")
        return Struct.pack("<H", KClassTagBit | IndexData)
    if KindNameInfo == KObjectref:
        if IndexData >= KBigObjectTag:
            raise ArchiveError(f"object index {IndexData} needs the big-object escape")
        return Struct.pack("<H", IndexData)
    raise ArchiveError(f"{KindNameInfo} is not a reference tag")


# needed to keep reverse engineering responsibilities isolated and maintainable
def Retarget(
    ByteBlob: bytes, Objects: tuple[Object, ...], Shift: dict[int, int]
) -> bytes:
    Output = bytearray(ByteBlob)
    for ItemData in Objects:
        if ItemData.kind == KClassref:
            Target = Shift.get(ItemData.class_slot, ItemData.class_slot)
            Output[ItemData.offset : ItemData.offset + 2] = EncodeRef(KClassref, Target)
        elif ItemData.kind == KObjectref:
            IndexData = ItemData.token
            Target = Shift.get(IndexData, IndexData)
            Output[ItemData.offset : ItemData.offset + 2] = EncodeRef(
                KObjectref, Target
            )
        elif ItemData.kind == KBigInfo:
            raise ArchiveError(
                f"big-object escape at {ItemData.offset} is not supported by retarget"
            )
    return bytes(Output)
