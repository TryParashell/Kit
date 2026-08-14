# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import pathlib as Pathlib
import struct as Struct
import sys as System
from Generation.GenSignatureTable import (
    KBlockOffset,
    KEntryCount,
    HostDll,
    Extract as ExtractRows,
)

# needed to keep reverse engineering responsibilities isolated and maintainable
KHostInfo = HostDll(None)

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[3]


# needed to keep reverse engineering responsibilities isolated and maintainable
def Extract(PathInfoData=None):
    GetRows = ExtractRows(PathInfoData or KHostInfo)
    return [
        (IndexData, FileId, (Triplet[0:4], Triplet[4:8], Triplet[8:12]))
        for IndexData, (FileId, Triplet) in enumerate(GetRows)
    ]


# needed to keep reverse engineering responsibilities isolated and maintainable
def Locate(PathInfoData=KHostInfo):
    ByteBlob = PathInfoData.read_bytes()
    FirstValue = ByteBlob.find(Struct.pack(">I", 3966641030))
    SecondValue = ByteBlob.find(Struct.pack("<I", 1691877445))
    return (FirstValue, SecondValue)


# needed to keep reverse engineering responsibilities isolated and maintainable
def ScanParts(Roots):
    System.path.insert(0, str(KRootInfo / "src"))
    from convert.adapters.solidworks.container.Container import (
        SldprtArchive,
        _template_fields as TemplateFields,
    )

    Found = []
    for RootPath in Roots:
        for PathInfoData in sorted((KRootInfo / RootPath).rglob("*")):
            if PathInfoData.suffix.upper() not in (".SLDPRT", ".SLDASM", ".SLDDRW"):
                continue
            try:
                ByteBlob = PathInfoData.read_bytes()
            except OSError:
                continue
            if len(ByteBlob) < 32:
                continue
            try:
                ArchiveInfo = SldprtArchive.from_bytes(ByteBlob, PathInfoData)
                Signatures, SpareValue = TemplateFields(ByteBlob, ArchiveInfo)
            except Exception as Problem:
                Found.append((PathInfoData, -1, 0, repr(Problem)))
                continue
            Found.append(
                (
                    PathInfoData,
                    ArchiveInfo.file_id,
                    ArchiveInfo.format_version,
                    Signatures,
                )
            )
    return Found


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMain(FileId, GetRows, IndexInfo, Table, TripInfo):
    print("host", KHostInfo, "block", hex(KBlockOffset), "count", KEntryCount)
    print("anchors", [hex(ValueData) for ValueData in Locate()])
    print("distinct file_ids", len(Table), "of", KEntryCount)
    for IndexInfo, FileId, TripInfo in GetRows[709:714] + GetRows[748:753]:
        print(IndexInfo, f"0x{FileId:08x}", [TextData.hex() for TextData in TripInfo])
    Roots = System.argv[1:] or [
        "examples",
        ".rescratch/corpus/parts",
        ".rescratch/corpus2",
        ".rescratch/trace/parts",
        ".rescratch/re/parts",
    ]
    Parts = ScanParts(Roots)
    OkInfo = 0
    BadInfo = 0
    Unknown = 0
    Broken = 0
    for PathInfoData, FileId, Version, Signatures in Parts:
        NameTextInfo = PathInfoData.name.encode("ascii", "replace").decode("ascii")
        if FileId < 0:
            Broken += 1
            print("UNREADABLE", NameTextInfo, Signatures)
            continue
        HitInfo = Table.get(FileId)
        if HitInfo is None:
            Unknown += 1
            print("NO TABLE ENTRY", NameTextInfo, f"0x{FileId:08x}")
            continue
        if tuple(HitInfo[1]) == tuple(Signatures):
            OkInfo += 1
        else:
            BadInfo += 1
            print(
                "MISMATCH",
                NameTextInfo,
                f"0x{FileId:08x}",
                f"index={HitInfo[0]}",
                [SourceData.hex() for SourceData in Signatures],
                [TextData.hex() for TextData in HitInfo[1]],
            )
    print(
        f"parts={len(Parts)} match={OkInfo} mismatch={BadInfo} unknown={Unknown} unreadable={Broken}"
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    GetRows = Extract()
    Table = {}
    for IndexInfo, FileId, TripInfo in GetRows:
        Table.setdefault(FileId, (IndexInfo, TripInfo))
    return FinishMain(FileId, GetRows, IndexInfo, Table, TripInfo)


if __name__ == "__main__":
    MainRun()
