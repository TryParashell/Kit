# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import argparse as Argparse
import json as JsonData
import re as Regex
from typing import Dict as DictInfo, Iterable, List as ListInfo, Optional, Tuple

from convert.Security.PathBoundary import ResolveInput, ResolveOutput

# needed to keep reverse engineering responsibilities isolated and maintainable
KFuncRe = Regex.compile("^=== FUNCTION (.+)$")

# needed to keep reverse engineering responsibilities isolated and maintainable
KAddressRe = Regex.compile("^=== ADDRESS ([0-9a-fA-F]+)$")

# needed to keep reverse engineering responsibilities isolated and maintainable
KMangledRe = Regex.compile("\\?([A-Za-z0-9_]+)@([A-Za-z0-9_]+)@@")

# needed to keep reverse engineering responsibilities isolated and maintainable
KGetReInfo = Regex.compile(
    "return\\s+\\*\\(([A-Za-z0-9_ ]++)\\s*\\*+\\)\\s*\\(this\\s*\\+\\s*(?:\\(longlong\\)(param_\\d+)\\s*\\*\\s*(\\d+)\\s*\\+\\s*)?(0x[0-9a-fA-F]+|\\d+)\\s*\\)\\s*;"
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KGetRe = Regex.compile(
    "return\\s+\\*\\(([A-Za-z0-9_ ]++)\\s*\\*+\\)\\s*\\(\\(longlong\\)(param_\\d+)\\s*\\*\\s*(\\d+)\\s*\\+\\s*this\\s*\\+\\s*(0x[0-9a-fA-F]+|\\d+)\\s*\\)\\s*;"
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KSetRe = Regex.compile(
    "\\*\\(([A-Za-z0-9_ ]++)\\s*\\*+\\)\\s*\\(this\\s*\\+\\s*(?:\\(longlong\\)(param_\\d+)\\s*\\*\\s*(\\d+)\\s*\\+\\s*)?(0x[0-9a-fA-F]+|\\d+)\\s*\\)\\s*=\\s*param_\\d+\\s*;"
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KAddrOfRe = Regex.compile("return\\s+this\\s*\\+\\s*(0x[0-9a-fA-F]+|\\d+)\\s*;")

# needed to keep reverse engineering responsibilities isolated and maintainable
KDerefRe = Regex.compile(
    "\\*\\(([A-Za-z0-9_ ]++)\\s*\\*+\\)\\s*\\((?:\\(longlong\\)(param_\\d+)\\s*\\*\\s*(\\d+)\\s*\\+\\s*)?this\\s*\\+\\s*(?:\\(longlong\\)(param_\\d+)\\s*\\*\\s*(\\d+)\\s*\\+\\s*)?(0x[0-9a-fA-F]+|\\d+)\\s*\\)"
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KWidths = {
    "char": 1,
    "uchar": 1,
    "byte": 1,
    "bool": 1,
    "undefined1": 1,
    "short": 2,
    "ushort": 2,
    "undefined2": 2,
    "wchar_t": 2,
    "int": 4,
    "uint": 4,
    "long": 4,
    "ulong": 4,
    "float": 4,
    "undefined4": 4,
    "double": 8,
    "longlong": 8,
    "ulonglong": 8,
    "undefined8": 8,
    "int64": 8,
    "size_t": 8,
}


# needed to keep reverse engineering responsibilities isolated and maintainable
def WidthOf(Ctype: str) -> Tuple[int, str]:
    TextValueData = Ctype.strip()
    if TextValueData in KWidths:
        return (KWidths[TextValueData], TextValueData)
    Parts = TextValueData.split()
    if Parts and Parts[-1] in KWidths:
        return (KWidths[Parts[-1]], TextValueData)
    return (8, TextValueData)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ParseInt(TextValueData: str) -> int:
    return (
        int(TextValueData, 16)
        if TextValueData.lower().startswith("0x")
        else int(TextValueData)
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def IterBlocks(TextValueData: str) -> Iterable[Tuple[str, str, str]]:
    Lines = TextValueData.splitlines()
    Starts: ListInfo[int] = []
    for IndexInfo, LineText in enumerate(Lines):
        if LineText.startswith("=== FUNCTION "):
            Starts.append(IndexInfo)
    Starts.append(len(Lines))
    for KeyIndex in range(len(Starts) - 1):
        Chunk = Lines[Starts[KeyIndex] : Starts[KeyIndex + 1]]
        NameTextInfo = KFuncRe.match(Chunk[0]).group(1).strip()
        Address = ""
        for LineText in Chunk[:6]:
            Match = KAddressRe.match(LineText)
            if Match:
                Address = Match.group(1)
                break
        yield (NameTextInfo, Address, "\n".join(Chunk))


# needed to keep reverse engineering responsibilities isolated and maintainable
def Classify(BodyInfo: str) -> Optional[dict]:
    Match = KGetRe.search(BodyInfo)
    if Match:
        WidthInfo, Ctype = WidthOf(Match.group(1))
        return {
            "kind": "get",
            "width": WidthInfo,
            "ctype": Ctype,
            "stride": int(Match.group(3)),
            "offset": ParseInt(Match.group(4)),
        }
    Match = KGetReInfo.search(BodyInfo)
    if Match:
        WidthInfo, Ctype = WidthOf(Match.group(1))
        return {
            "kind": "get",
            "width": WidthInfo,
            "ctype": Ctype,
            "stride": int(Match.group(3)) if Match.group(3) else 0,
            "offset": ParseInt(Match.group(4)),
        }
    Match = KSetRe.search(BodyInfo)
    if Match:
        WidthInfo, Ctype = WidthOf(Match.group(1))
        return {
            "kind": "set",
            "width": WidthInfo,
            "ctype": Ctype,
            "stride": int(Match.group(3)) if Match.group(3) else 0,
            "offset": ParseInt(Match.group(4)),
        }
    Match = KAddrOfRe.search(BodyInfo)
    if Match:
        return {
            "kind": "ref",
            "width": 0,
            "ctype": "member",
            "stride": 0,
            "offset": ParseInt(Match.group(1)),
        }
    HitsInfo = KDerefRe.findall(StripComments(BodyInfo))
    SeenInfo: DictInfo[int, dict] = {}
    for Ctype, PreVar, PreStride, PostVar, PostStride, Offset in HitsInfo:
        WidthInfo, Resolved = WidthOf(Ctype)
        ValueInfo = ParseInt(Offset)
        Stride = int(PreStride or PostStride or 0)
        SeenInfo.setdefault(
            ValueInfo,
            {
                "kind": "get_derived",
                "width": WidthInfo,
                "ctype": Resolved,
                "stride": Stride,
                "offset": ValueInfo,
            },
        )
    if len(SeenInfo) == 1:
        return next(iter(SeenInfo.values()))
    return None


# needed to keep reverse engineering responsibilities isolated and maintainable
def StripComments(BodyInfo: str) -> str:
    OutputDataInfo: ListInfo[str] = []
    CursorIndex = 0
    while CursorIndex < len(BodyInfo):
        StartIndex = BodyInfo.find("/*", CursorIndex)
        if StartIndex < 0:
            OutputDataInfo.append(BodyInfo[CursorIndex:])
            break
        OutputDataInfo.append(BodyInfo[CursorIndex:StartIndex])
        EndIndex = BodyInfo.find("*/", StartIndex + 2)
        if EndIndex < 0:
            OutputDataInfo.append(" ")
            break
        OutputDataInfo.append(" ")
        CursorIndex = EndIndex + 2
    return "".join(OutputDataInfo)


# class selection stays isolated so dump mining receives one normalized ownership set
def LoadWanted(ClassPath: str) -> set[str]:
    Wanted = set()
    with ResolveInput(ClassPath).open(encoding="utf-8") as ClassHandle:
        for LineText in ClassHandle:
            TextValueData = LineText.strip()
            if not TextValueData:
                continue
            Parts = TextValueData.split(None, 1)
            Wanted.add(
                Parts[1].strip()
                if len(Parts) == 2 and Parts[0].isdigit()
                else TextValueData
            )
    return Wanted


# one dump scan stays isolated so matching and conflict handling remain locally reviewable
def ScanDumpMut(
    Result: DictInfo[str, DictInfo[str, dict]], Wanted: set[str], PathInfoData: str
) -> tuple[int, int]:
    Scanned = 0
    Matched = 0
    with ResolveInput(PathInfoData).open(
        encoding="utf-8", errors="replace"
    ) as DumpHandle:
        TextValueData = DumpHandle.read()
    for NameTextInfo, Address, BodyInfo in IterBlocks(TextValueData):
        Scanned += 1
        InfoInfo = Classify(BodyInfo)
        if InfoInfo is None:
            continue
        Matched += 1
        Owners: ListInfo[Tuple[str, str]] = []
        if "::" in NameTextInfo:
            ClassRef, Member = NameTextInfo.split("::", 1)
            Owners.append((ClassRef, Member))
        for Member, ClassRef in KMangledRe.findall(BodyInfo):
            Owners.append((ClassRef, Member))
        for ClassRef, Member in Owners:
            if ClassRef not in Wanted:
                continue
            Entry = dict(InfoInfo)
            Entry["address"] = Address
            Entry["source"] = PathInfoData.replace("\\", "/").rsplit("/", 1)[-1]
            Bucket = Result.setdefault(ClassRef, {})
            Previous = Bucket.get(Member)
            if Previous is not None and Previous["offset"] != Entry["offset"]:
                Entry["conflicts_with"] = Previous["offset"]
            Bucket[Member] = Entry
    return Scanned, Matched


# command orchestration remains small so dump scanning can extend without growing the entry point
def MainRun() -> int:
    ParserInfo = Argparse.ArgumentParser()
    ParserInfo.add_argument("dumps", nargs="+")
    ParserInfo.add_argument("--classes", required=True)
    ParserInfo.add_argument("--out", required=True)
    ArgValues = ParserInfo.parse_args()
    Wanted = LoadWanted(ArgValues.classes)
    Result: DictInfo[str, DictInfo[str, dict]] = {}
    Scanned = 0
    Matched = 0
    for PathInfoData in ArgValues.dumps:
        ScanCount, MatchCount = ScanDumpMut(Result, Wanted, PathInfoData)
        Scanned += ScanCount
        Matched += MatchCount
    PayloadInfo = {
        ClassRef: dict(sorted(Members.items()))
        for ClassRef, Members in sorted(Result.items())
    }
    with ResolveOutput(ArgValues.out).open("w", encoding="utf-8") as Handle:
        JsonData.dump(PayloadInfo, Handle, indent=1)
        Handle.write("\n")
    Total = sum((len(ValueData) for ValueData in PayloadInfo.values()))
    print(
        f"blocks={Scanned} recognised={Matched} classes={len(PayloadInfo)} accessors={Total}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
