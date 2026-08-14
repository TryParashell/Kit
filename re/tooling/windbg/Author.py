# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import json as JsonData
from pathlib import Path as PathInfo
import struct as Struct
import sys as System

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KScratch = KHereInfo.parents[2] / ".rescratch"

# needed to keep reverse engineering responsibilities isolated and maintainable
KGrammar = KHereInfo.parent / "harness"
for CandInfo in (KHereInfo, KGrammar):
    if str(CandInfo) not in System.path:
        System.path.insert(0, str(CandInfo))
import Headercount as Headercount
import Renumber as Renumber
import Serialize as Serial
import Streamlib as Streamlib
from convert.adapters.solidworks import resolved as Resolvedlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / "trace" / "out"

# needed to keep reverse engineering responsibilities isolated and maintainable
KParts = KScratch / "trace" / "parts"

# needed to keep reverse engineering responsibilities isolated and maintainable
KBossRectPlane = ("boss", "rectangle", "plane", True)

# needed to keep reverse engineering responsibilities isolated and maintainable
KDonor = (KScratch / "corpus2" / "parts" / "PADPLANE_rev_d5.SLDPRT").resolve()

# needed to keep reverse engineering responsibilities isolated and maintainable
KLogInfo = (KScratch / "trace" / "out" / "cdb_trace_padplane.log").resolve()


# needed to keep reverse engineering responsibilities isolated and maintainable
class AuthorError(RuntimeError):
    __slots__ = ()


# needed to keep reverse engineering responsibilities isolated and maintainable
def BossInfo(
    WidthInfo: float,
    Height: float,
    Depth: float,
    Xcoord: float,
    Ycoord: float,
    BackInfo: bool,
) -> Serial.Extrude:
    return Serial.Extrude(
        Profile=Serial.Rectangle(WidthInfo, Height, Xcoord, Ycoord),
        DepthMm=Depth,
        OpInfo="boss",
        Plane="front",
        EndCondition="blind",
        Reversed=BackInfo,
        Support="plane",
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
KBaseInfo = BossInfo(100.0, 30.0, 12.0, 0.0, 0.0, False)

# needed to keep reverse engineering responsibilities isolated and maintainable
KStuds = (
    BossInfo(10.0, 10.0, 8.0, -30.0, 0.0, True),
    BossInfo(10.0, 10.0, 6.0, -10.0, 0.0, True),
    BossInfo(10.0, 10.0, 7.0, 10.0, 0.0, True),
    BossInfo(10.0, 10.0, 5.0, 30.0, 0.0, True),
)


# needed to keep reverse engineering responsibilities isolated and maintainable
def RenameTree(ByteBlob: bytes, CountInfo: int) -> bytes:
    if CountInfo > 9:
        raise AuthorError(
            f"{CountInfo} features exceeds the single-digit name convention"
        )
    Output = bytearray(ByteBlob)
    Nodes = Resolvedlib.tree_nodes(bytes(Output))
    Sketches = [ItemData for ItemData in Nodes if ItemData.name.startswith("Sketch")]
    FeatInfoInfo = [
        ItemData
        for ItemData in Nodes
        if Resolvedlib.feature_kind(ItemData.flags) is not None
    ]
    if len(Sketches) != CountInfo or len(FeatInfoInfo) != CountInfo:
        raise AuthorError(
            f"grown stream exposes {len(Sketches)} sketches and {len(FeatInfoInfo)} features, {CountInfo} of each expected"
        )
    for Ordinal in range(CountInfo):
        Wanted = ord(str(Ordinal + 1))
        for ItemData in (Sketches[Ordinal], FeatInfoInfo[Ordinal]):
            Struct.pack_into("<H", Output, ItemData.text_end - 2, Wanted)
    return bytes(Output)


# needed to keep reverse engineering responsibilities isolated and maintainable
def SkeletonFor(CountInfo: int) -> tuple[Serial.Skeleton, dict[str, object]]:
    Copies = CountInfo - 2
    if Copies < 1:
        raise AuthorError(
            f"{CountInfo} features needs no growth from a 2-feature donor"
        )
    SpareValue, PayloadInfo, SpareValue, Facts = Renumber.GrowInfo(
        KDonor, KLogInfo, Copies
    )
    PayloadInfo = RenameTree(PayloadInfo, CountInfo)
    DonorInfo = Streamlib.LoadDonor(KDonor)
    Shape = tuple((KBossRectPlane for SpareValue in range(CountInfo)))
    SkeletonInfo = Serial.Skeleton(
        Shape=Shape,
        Source=KDonor,
        Resolved=PayloadInfo,
        Keywords=DonorInfo.streams[Streamlib.KEYWORDS],
        FeatXml=DonorInfo.streams[Streamlib.KFeatInfo],
        DonorInfo=DonorInfo,
        Grown=True,
        LabelInfo=f"{KDonor.stem}+{Copies}",
    )
    return (SkeletonInfo, Facts)


# needed to keep reverse engineering responsibilities isolated and maintainable
def Specification(CountInfo: int) -> Serial.PartInfo:
    return Serial.PartInfo(
        FeatInfoInfo=(KBaseInfo,) + KStuds[: CountInfo - 1],
        NameTextInfo=f"KitTrace{CountInfo}",
        DocumentName=f"Trace{CountInfo}",
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def Build(CountInfo: int, Group: str) -> dict[str, object]:
    SkeletonInfo, Facts = SkeletonFor(CountInfo)
    SpecInfo = Specification(CountInfo)
    Target = KParts / f"T{CountInfo}{Group}_{CountInfo}_boss.SLDPRT"
    EmissionInfo = Serial.EmitData(SpecInfo, (SkeletonInfo,))
    Replacements = {
        Streamlib.KResolved: EmissionInfo.resolved,
        Streamlib.KEYWORDS: EmissionInfo.keywords,
        Streamlib.KFeatInfo: EmissionInfo.features_xml,
    }
    Replacements.update(
        Headercount.PatchedStreams(SkeletonInfo.donor, CountInfo, Group)
    )
    Contain = Streamlib.Rebuild(SkeletonInfo.donor, Replacements)
    Target.parent.mkdir(parents=True, exist_ok=True)
    Target.write_bytes(Contain)
    Record = {
        "label": Target.stem,
        "path": str(Target),
        "features": CountInfo,
        "skeleton": EmissionInfo.skeleton,
        "resolved_length": len(EmissionInfo.resolved),
        "container_length": len(Contain),
        "expected_volume_mm3": Serial.SolidThree(SpecInfo),
        "history_count_after": Facts["history_count_after"],
        "comp_entries_after": Facts["comp_entries_after"],
        "map_indices_after": Facts["map_indices_after"],
        "count_group": Group,
        "patched_streams": sorted(
            Headercount.PatchedStreams(SkeletonInfo.donor, CountInfo, Group)
        ),
        "writes": EmissionInfo.writes,
    }
    print(
        f"{Record['label']:20s} features={CountInfo} resolved={len(EmissionInfo.resolved):6d} container={len(Contain):6d} group={Group} expected={Record['expected_volume_mm3']}"
    )
    return Record


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    KParts.mkdir(parents=True, exist_ok=True)
    KOutInfo.mkdir(parents=True, exist_ok=True)
    Group = System.argv[1]
    Counts = [int(ItemData) for ItemData in System.argv[2:]] or [4]
    RecordsInfo = [Build(CountInfo, Group) for CountInfo in Counts]
    (KOutInfo / "Author.json").write_text(
        JsonData.dumps(RecordsInfo, indent=2), encoding="utf-8"
    )
    for Record in RecordsInfo:
        print(f"{Record['label']}: {Record['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
