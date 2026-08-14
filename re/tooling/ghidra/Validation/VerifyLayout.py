# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json as JsonData
import math as MathInfo
import pathlib as Pathlib
import struct as Struct
import sys as System

# ghidra tooling root exposes the shared layout reader to standalone validators
KToolRoot = Pathlib.Path(__file__).resolve().parent.parent
System.path.insert(0, str(KToolRoot))
from Layout import FindItem, FindGaps, LoadData

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = Pathlib.Path(__file__).resolve().parents[4] / "re/data"

# needed to keep reverse engineering responsibilities isolated and maintainable
KLabels = [
    "baseline",
    "circle",
    "planetop",
    "twopad",
    "padplane",
    "cutbase",
    "three",
    "vendor_ring",
    "vendor_cojinete",
]

# the leading end specification fields describe direction and paired termination controls
KMoEndHead = [
    ("obj", "dirSpec@0x138"),
    ("i32", "singleEnd@0x08"),
    ("i32", "reverse1@0x88"),
    ("i32", "reverse0@0x8c"),
    ("obj", "keepPiece@0x90"),
    ("i32", "type0@0x0c"),
    ("i32", "type1@0x10"),
    ("obj", "distanceDim0@0x18"),
    ("obj", "distanceDim1@0x20"),
    ("u8", "surfArrayPresent0"),
    ("u16", "surfArray0@0x28"),
    ("u8", "surfArrayPresent1"),
    ("u16", "surfArray1@0x48"),
    ("f64", "f64@0xa0"),
    ("i32", "draftCheck0@0xb8"),
    ("i32", "draftCheck1@0xbc"),
    ("i32", "draftDir0@0xc0"),
    ("i32", "draftDir1@0xc4"),
    ("i32", "translateSurf0@0xb0"),
    ("i32", "translateSurf1@0xb4"),
]

# the trailing end specification fields describe angles flags subobjects and source linkage
KMoEndTail = [
    ("obj", "angleDim0@0xc8"),
    ("obj", "angleDim1@0xd0"),
    ("i32", "f@0xa8"),
    ("i32", "f@0xac"),
    ("i32", "f@0xd8"),
    ("i32", "f@0xdc"),
    ("u16", "sub@0xe0"),
    ("u16", "sub@0x100"),
    ("i32", "f@0x128"),
    ("i32", "f@0x12c"),
    ("i32", "f@0x130"),
    ("obj", "fromEndSpec@0x140"),
]

# the complete end specification preserves the native scalar traversal order
KMoEndSpec = KMoEndHead + KMoEndTail

# needed to keep reverse engineering responsibilities isolated and maintainable
KMoRevEndSpec = [
    ("i32", "singleEnd@0x08"),
    ("i32", "f@0x138"),
    ("i32", "f@0x13c"),
    ("i32", "type0@0x0c"),
    ("i32", "type1@0x10"),
    ("obj", "iSurfRef0@0x118"),
    ("obj", "iSurfRef1@0x120"),
    ("obj", "upToPointRef0@0x128"),
    ("obj", "upToPointRef1@0x130"),
    ("f64", "f64@0x38"),
    ("f64", "f64@0x40"),
    ("i32", "offsetReverse0@0x140"),
    ("i32", "offsetReverse1@0x144"),
    ("obj", "angleDim0@0x18"),
    ("obj", "angleDim1@0x20"),
    ("obj", "offsetDim0@0x28"),
    ("obj", "offsetDim1@0x30"),
]

# needed to keep reverse engineering responsibilities isolated and maintainable
KWidths = {"u8": 1, "i8": 1, "u16": 2, "i16": 2, "u32": 4, "i32": 4, "f32": 4, "f64": 8}


# scalar gap decoding stays isolated so tree traversal owns only object ordering
def ReadGapMut(ByteBlob, OffInfo, ByteSize, SpecInfo, Cursor, Values):
    UsedInfo = 0
    while UsedInfo < ByteSize:
        if Cursor >= len(SpecInfo):
            return (
                False,
                f"spec exhausted with {ByteSize - UsedInfo} bytes left at {OffInfo + UsedInfo}",
                Cursor,
            )
        KindNameInfo, NameTextInfo = SpecInfo[Cursor]
        if KindNameInfo == "obj":
            return (
                False,
                f"expected scalar at {OffInfo + UsedInfo}, spec says obj {NameTextInfo}",
                Cursor,
            )
        WidthInfo = KWidths[KindNameInfo]
        if UsedInfo + WidthInfo > ByteSize:
            return (
                False,
                f"field {NameTextInfo} ({KindNameInfo}) overruns gap at {OffInfo + UsedInfo}",
                Cursor,
            )
        RawData = ByteBlob[OffInfo + UsedInfo : OffInfo + UsedInfo + WidthInfo]
        if KindNameInfo == "f64":
            ValueInfo = Struct.unpack("<d", RawData)[0]
        elif KindNameInfo in ("i32", "u32"):
            ValueInfo = Struct.unpack("<i" if KindNameInfo == "i32" else "<I", RawData)[
                0
            ]
        elif KindNameInfo in ("u16", "i16"):
            ValueInfo = Struct.unpack("<H", RawData)[0]
        else:
            ValueInfo = RawData[0]
        Values.append((NameTextInfo, ValueInfo))
        UsedInfo += WidthInfo
        Cursor += 1
    return True, "ok", Cursor


# tree traversal remains focused on archive object ordering and delegates scalar decoding
def WalkTree(SegsInfo, ByteBlob, IndexData, SpecInfo):
    Cursor = 0
    Values = []
    for ItemData in FindGaps(SegsInfo, IndexData):
        if ItemData[0] == "object":
            if Cursor >= len(SpecInfo) or SpecInfo[Cursor][0] != "obj":
                return (
                    False,
                    f"expected obj, spec[{Cursor}]={SpecInfo[Cursor:Cursor + 1]}",
                    Values,
                )
            Values.append((SpecInfo[Cursor][1], "obj:" + ItemData[2]))
            Cursor += 1
            continue
        SpareValue, OffInfo, ByteSize = ItemData
        OkInfo, Message, Cursor = ReadGapMut(
            ByteBlob, OffInfo, ByteSize, SpecInfo, Cursor, Values
        )
        if not OkInfo:
            return False, Message, Values
    if Cursor != len(SpecInfo):
        return (False, f"{len(SpecInfo) - Cursor} spec items unconsumed", Values)
    return (True, "ok", Values)


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishTail(ByteBlob, LastInfo):
    StartRun = LastInfo["offset"] + LastInfo["header"]
    ByteSize = LastInfo["scope_end"] - StartRun
    RawData = ByteBlob[StartRun : StartRun + ByteSize]
    Candidates = []
    for EndSpecBytes in (20, 16):
        NeedInfo = 4 + EndSpecBytes + 12
        if ByteSize not in (NeedInfo, NeedInfo + 4):
            continue
        Cursor = 0
        OutputDataInfo = {
            "run_size": ByteSize,
            "end_spec_tail_bytes": EndSpecBytes,
            "driver_trailer": ByteSize - NeedInfo,
            "fromEndSpec_type": Struct.unpack_from("<i", RawData, 0)[0],
        }
        Cursor = 4
        Labels = [
            "capEnd0@0x148",
            "capEnd1@0x14c",
            "delInitFace@0x150",
            "knitRes@0x154",
        ]
        if EndSpecBytes == 20:
            Labels.append("createSolid@0x158")
        for LabelInfo in Labels:
            OutputDataInfo[LabelInfo] = Struct.unpack_from("<I", RawData, Cursor)[0]
            Cursor += 4
        ValueInfo = Struct.unpack_from("<d", RawData, Cursor)[0]
        OutputDataInfo["extrusion_f64@0x7d0"] = ValueInfo
        Cursor += 8
        OutputDataInfo["extrusion_long@0x7a8"] = Struct.unpack_from(
            "<I", RawData, Cursor
        )[0]
        OutputDataInfo["plausible"] = (
            not MathInfo.isnan(ValueInfo) and abs(ValueInfo) < 1000000.0
        )
        Candidates.append(OutputDataInfo)
    for OutputDataInfo in Candidates:
        if OutputDataInfo["plausible"]:
            return OutputDataInfo
    if Candidates:
        return Candidates[0]
    return {"run_size": ByteSize, "error": "no budget fits"}


# needed to keep reverse engineering responsibilities isolated and maintainable
def TailInfo(SegsInfo, ByteBlob, IndexData):
    KidsInfo = [
        SourceData for SourceData in SegsInfo if SourceData["parent"] == IndexData
    ]
    if not KidsInfo:
        return None
    LastInfo = KidsInfo[-1]
    return FinishTail(ByteBlob, LastInfo)


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    Report = {}
    Total = 0
    Passed = 0
    for LabelInfo in KLabels:
        DocInfo, SegsInfo, ByteBlob, PartInfoInfo = LoadData(LabelInfo)
        GetRows = []
        Indices = FindItem(SegsInfo, "moEndSpec_c", "definition") + FindItem(
            SegsInfo, "moEndSpec_c", "classref"
        )
        for IndexData in Indices:
            OkInfo, Message, Values = WalkTree(
                SegsInfo, ByteBlob, IndexData, KMoEndSpec
            )
            Total += 1
            Passed += 1 if OkInfo else 0
            Named = {KeyIndex: ValueData for KeyIndex, ValueData in Values}
            GetRows.append(
                {
                    "node": IndexData,
                    "offset": SegsInfo[IndexData]["offset"],
                    "ok": OkInfo,
                    "message": Message,
                    "type0": Named.get("type0@0x0c"),
                    "type1": Named.get("type1@0x10"),
                    "reverse0": Named.get("reverse0@0x8c"),
                    "singleEnd": Named.get("singleEnd@0x08"),
                    "fields": [[KeyIndex, ValueData] for KeyIndex, ValueData in Values],
                }
            )
            print(
                f"{LabelInfo:16s} {PartInfoInfo.name[:28]:28s} moEndSpec_c node={IndexData:4d} {('PASS' if OkInfo else 'FAIL')} {Message} type0={Named.get('type0@0x0c')} type1={Named.get('type1@0x10')} rev={Named.get('reverse0@0x8c')} single={Named.get('singleEnd@0x08')}"
            )
        Tails = []
        for IndexData in FindItem(SegsInfo, "moEndSpec_c", "definition"):
            InfoInfo = TailInfo(SegsInfo, ByteBlob, IndexData)
            Tails.append({"node": IndexData, **(InfoInfo or {})})
            print(f"{LabelInfo:16s} tail node={IndexData:4d} {InfoInfo}")
        Report[LabelInfo] = {
            "part": PartInfoInfo.name,
            "moEndSpec_c": GetRows,
            "tails": Tails,
        }
    print(f"moEndSpec_c: {Passed}/{Total} objects reproduce the traced spans exactly")
    KOutInfo.mkdir(parents=True, exist_ok=True)
    (KOutInfo / "VerifyLayout.json").write_text(JsonData.dumps(Report, indent=1))
    return 0 if Passed == Total else 1


if __name__ == "__main__":
    System.exit(MainRun())
