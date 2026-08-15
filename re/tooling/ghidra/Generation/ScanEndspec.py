# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import collections as Collects
import json as JsonData
import pathlib as Pathlib
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = Pathlib.Path(__file__).resolve().parents[4]
System.path.insert(0, str(KRootInfo / "src"))
from convert.adapters.solidworks.container.Container import SldprtArchive

# needed to keep reverse engineering responsibilities isolated and maintainable
KStream = "Contents/Config-0-ResolvedFeatures"

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = Pathlib.Path(__file__).resolve().parents[4] / "re/data"

# needed to keep reverse engineering responsibilities isolated and maintainable
KNames = {
    0: "Blind",
    1: "ThroughAll",
    2: "ThroughNext",
    3: "UpToVertex",
    4: "UpToSurface",
    5: "OffsetFromSurface",
    6: "MidPlane",
    7: "UpToBody",
    9: "ThroughAllBoth",
    10: "UpToSelection",
    11: "UpToNext",
}


# needed to keep reverse engineering responsibilities isolated and maintainable
def Marker(NameTextInfo):
    BodyInfo = NameTextInfo.encode("ascii")
    return b"\xff\xff\x01\x00" + Struct.pack("<H", len(BodyInfo)) + BodyInfo


# needed to keep reverse engineering responsibilities isolated and maintainable
def Parts(Roots):
    for RootPath in Roots:
        for PathInfoData in sorted((KRootInfo / RootPath).rglob("*")):
            if PathInfoData.suffix.upper() not in (".SLDPRT",):
                continue
            yield PathInfoData


# needed to keep reverse engineering responsibilities isolated and maintainable
def Decode(ByteBlob, PosInfo, Klass):
    DataValue = PosInfo + 6 + len(Klass)
    if Struct.unpack_from("<H", ByteBlob, DataValue)[0] != 0:
        return None
    if Struct.unpack_from("<H", ByteBlob, DataValue + 14)[0] != 0:
        return None
    return {
        "data": DataValue,
        "singleEnd": Struct.unpack_from("<i", ByteBlob, DataValue + 2)[0],
        "reverse1": Struct.unpack_from("<i", ByteBlob, DataValue + 6)[0],
        "reverse0": Struct.unpack_from("<i", ByteBlob, DataValue + 10)[0],
        "type0": Struct.unpack_from("<i", ByteBlob, DataValue + 16)[0],
        "type1": Struct.unpack_from("<i", ByteBlob, DataValue + 20)[0],
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def FinishMainMut(GetRows, Histogram, Klass, Needle, Roots):
    SeenInfo = 0
    Skipped = 0
    for PathInfoData in Parts(Roots):
        try:
            ArchiveInfo = SldprtArchive.open(PathInfoData)
            ByteBlob = ArchiveInfo.get(KStream)
        except Exception:
            continue
        if not ByteBlob:
            continue
        PosInfo = ByteBlob.find(Needle)
        if PosInfo < 0:
            continue
        SeenInfo += 1
        Record = Decode(ByteBlob, PosInfo, Klass)
        if Record is None:
            Skipped += 1
            continue
        Histogram[Record["type0"], Record["type1"], Record["reverse0"]] += 1
        GetRows.append(
            {
                "part": PathInfoData.name.encode("ascii", "replace").decode("ascii"),
                "marker": PosInfo,
                **Record,
            }
        )
    print(
        f"parts with a moEndSpec_c definition: {SeenInfo}, decoded: {len(GetRows)}, rejected: {Skipped}"
    )

    # needed to keep reverse engineering responsibilities isolated and maintainable
    for KeyName, CountInfo in sorted(Histogram.items(), key=lambda KvInfo: -KvInfo[1]):
        TZero, TOneInfo, RevInfo = KeyName
        print(
            f"  type0={TZero:3d} ({KNames.get(TZero, '?'):18s}) type1={TOneInfo:3d} ({KNames.get(TOneInfo, '?'):18s}) reverse={RevInfo} n={CountInfo}"
        )
    for RowDataInfo in GetRows:
        if RowDataInfo["type0"] not in (0, 1, 6) or RowDataInfo["type1"] != 0:
            print(
                f"  NOTABLE {RowDataInfo['part']:44s} type0={RowDataInfo['type0']} type1={RowDataInfo['type1']}"
            )
    KOutInfo.mkdir(parents=True, exist_ok=True)
    (KOutInfo / "ScanEndspec.json").write_text(JsonData.dumps(GetRows, indent=1))


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun():
    Roots = System.argv[1:] or [
        ".rescratch/corpus/parts",
        ".rescratch/corpus2",
        ".rescratch/trace/parts",
        "examples",
    ]
    Klass = "moEndSpec_c"
    Needle = Marker(Klass)
    Histogram = Collects.Counter()
    GetRows = []
    return FinishMainMut(GetRows, Histogram, Klass, Needle, Roots)


if __name__ == "__main__":
    MainRun()
