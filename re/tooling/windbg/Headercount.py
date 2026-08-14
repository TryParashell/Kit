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
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / "harness"
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Streamlib as Streamlib


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
KModelHeader = "Contents/Config-0-ModelHeader"

# needed to keep reverse engineering responsibilities isolated and maintainable
KHeaderTwo = "Header2"

# needed to keep reverse engineering responsibilities isolated and maintainable
KCmgrInfo = "Contents/CMgr"

# needed to keep reverse engineering responsibilities isolated and maintainable
KNodeOffset = 77

# needed to keep reverse engineering responsibilities isolated and maintainable
KCmgrOffset = 1414

# needed to keep reverse engineering responsibilities isolated and maintainable
KBaseNodes = 24


# needed to keep reverse engineering responsibilities isolated and maintainable
@DataClass(frozen=True, slots=True)
class Field:
    Stream: str
    Offset: int
    WidthInfo: int
    LabelInfo: str

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def ReadData(SelfRef, ByteBlob: bytes) -> int:
        return int.from_bytes(
            ByteBlob[SelfRef.Offset : SelfRef.Offset + SelfRef.WidthInfo], "little"
        )

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def Write(SelfRef, ByteBlob: bytes, ValueInfo: int) -> bytes:
        Output = bytearray(ByteBlob)
        Output[SelfRef.Offset : SelfRef.Offset + SelfRef.WidthInfo] = (
            ValueInfo.to_bytes(SelfRef.WidthInfo, "little")
        )
        return bytes(Output)

    # needed to keep reverse engineering responsibilities isolated and maintainable
    def Expect(SelfRef, FeatInfoInfo: int) -> int:
        if SelfRef.LabelInfo == "24+2n":
            return KBaseNodes + 2 * FeatInfoInfo
        if SelfRef.LabelInfo == "n":
            return FeatInfoInfo
        raise KeyError(SelfRef.LabelInfo)

    KAliasNames = {
        "stream": "Stream",
        "offset": "Offset",
        "width": "WidthInfo",
        "label": "LabelInfo",
        "read": "ReadData",
        "write": "Write",
        "expected": "Expect",
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
Field.__getattr__ = GetLegacyAttr

# needed to keep reverse engineering responsibilities isolated and maintainable
KFields = (
    Field(KModelHeader, KNodeOffset, 2, "24+2n"),
    Field(KHeaderTwo, KNodeOffset, 2, "24+2n"),
    Field(KCmgrInfo, KCmgrOffset, 2, "n"),
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KGroups = {
    "header": (KFields[0], KFields[1]),
    "cmgr": (KFields[2],),
    "all": KFields,
    "none": (),
}


# needed to keep reverse engineering responsibilities isolated and maintainable
def NodeCount(ByteBlob: bytes) -> int:
    return KFields[0].read(ByteBlob)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Patch(ByteBlob: bytes, ValueInfo: int) -> bytes:
    return KFields[0].write(ByteBlob, ValueInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def PatchedStreams(
    DonorInfo: Streamlib.Donor, FeatInfoInfo: int, Group: str
) -> dict[str, bytes]:
    Result: dict[str, bytes] = {}
    for FieldInfo in KGroups[Group]:
        Source = Result.get(FieldInfo.stream, DonorInfo.streams[FieldInfo.stream])
        Result[FieldInfo.stream] = FieldInfo.write(
            Source, FieldInfo.expected(FeatInfoInfo)
        )
    return Result


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    for ItemData in System.argv[1:]:
        PartInfoInfo = PathInfo(ItemData).resolve()
        DonorInfo = Streamlib.LoadDonor(PartInfoInfo)
        FeatInfoInfo = len(Streamlib.CompFeatEntries(DonorInfo.resolved)) // 2
        RowDataInfo = [f"{PartInfoInfo.stem:30s} features={FeatInfoInfo}"]
        for FieldInfo in KFields:
            ByteBlob = DonorInfo.streams[FieldInfo.stream]
            RowDataInfo.append(
                f"{FieldInfo.stream.split('/')[-1]}[{FieldInfo.offset}]={FieldInfo.read(ByteBlob)}/{FieldInfo.expected(FeatInfoInfo)}"
            )
        print(" ".join(RowDataInfo))
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
