# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import argparse as Argparse
import collections as Collects
import json as JsonData
from pathlib import Path as PathInfo
import struct as Struct
import sys as System
from typing import Dict as DictInfo, List as ListInfo, Mapping, Tuple

# needed to keep reverse engineering responsibilities isolated and maintainable
KHereInfo = PathInfo(__file__).resolve().parent

# needed to keep reverse engineering responsibilities isolated and maintainable
KRootInfo = KHereInfo.parents[2]
for CandInfo in (str(KRootInfo / "src"),):
    if CandInfo not in System.path:
        System.path.insert(0, CandInfo)
from convert.adapters.solidworks.container.Archive import (
    BaseResolution,
    ContainerMo,
    KMoVersionPrefix,
    KStreamHeaderSize,
    LayoutTable,
    ResolveBase,
    Verify,
)
from convert.adapters.solidworks.container.Container import SldprtArchive

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefaultData = KRootInfo / "tests" / "fixtures" / "solidworks" / "donors"

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefaultLayouts = KRootInfo / "re" / "data" / "Layouts" / "ClassLayouts.json"

# needed to keep reverse engineering responsibilities isolated and maintainable
KDefaultValue = KRootInfo / "re" / "data" / "segments"

# needed to keep reverse engineering responsibilities isolated and maintainable
KFirstFeatBase = 109

# needed to keep reverse engineering responsibilities isolated and maintainable
KVendorPrefix = "vendor_"

# needed to keep reverse engineering responsibilities isolated and maintainable
KClassMarker = b"\xff\xff\x01\x00"


# needed to keep reverse engineering responsibilities isolated and maintainable
def ScannedNames(ByteBlob: bytes) -> ListInfo[str]:
    Found: ListInfo[str] = []
    Cursor = ByteBlob.find(KClassMarker)
    while Cursor >= 0:
        Units = Struct.unpack_from("<H", ByteBlob, Cursor + 4)[0]
        EndIndex = Cursor + 6 + Units
        if 0 < Units < 64 and EndIndex <= len(ByteBlob):
            RawData = ByteBlob[Cursor + 6 : EndIndex]
            if all((32 <= ByteInfo < 127 for ByteInfo in RawData)):
                NameTextInfo = RawData.decode("ascii")
                if NameTextInfo not in Found:
                    Found.append(NameTextInfo)
        Cursor = ByteBlob.find(KClassMarker, Cursor + 1)
    return Found


# needed to keep reverse engineering responsibilities isolated and maintainable
def FixtureCount(DonorInfo: PathInfo) -> int:
    MetaInfo = DonorInfo / "meta.json"
    if not MetaInfo.is_file():
        return -1
    PayloadInfo = JsonData.loads(MetaInfo.read_text(encoding="utf-8"))
    FeatInfoInfo = PayloadInfo.get("features")
    return len(FeatInfoInfo) if isinstance(FeatInfoInfo, list) else -1


# needed to keep reverse engineering responsibilities isolated and maintainable
def DonorNames(DonorInfo: PathInfo) -> ListInfo[str]:
    Names: ListInfo[str] = []
    MetaInfo = DonorInfo / "meta.json"
    if MetaInfo.is_file():
        PayloadInfo = JsonData.loads(MetaInfo.read_text(encoding="utf-8"))
        Listed = PayloadInfo.get("container_streams")
        if isinstance(Listed, list):
            for ItemData in Listed:
                if isinstance(ItemData, dict) and isinstance(ItemData.get("name"), str):
                    Names.append(str(ItemData["name"]))
    return Names


# needed to keep reverse engineering responsibilities isolated and maintainable
def DonorMoVersion(DonorInfo: PathInfo) -> Tuple[int | None, str]:
    MetaInfo = DonorInfo / "meta.json"
    if MetaInfo.is_file():
        PayloadInfo = JsonData.loads(MetaInfo.read_text(encoding="utf-8"))
        Recorded = PayloadInfo.get("mo_version")
        if isinstance(Recorded, int) and (not isinstance(Recorded, bool)):
            return (int(Recorded), "mo_version field in the fixture meta.json")
    Names = DonorNames(DonorInfo)
    Found = ContainerMo(Names)
    if Found is not None:
        return (
            Found,
            f"{KMoVersionPrefix}{Found} among the {len(Names)} container stream names in the fixture meta.json",
        )
    return (
        None,
        f"neither an mo_version field nor a {KMoVersionPrefix}* storage among the {len(Names)} container stream names in the fixture meta.json",
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def TracedVersions(SegmentsDir: PathInfo) -> DictInfo[str, int]:
    Table: DictInfo[str, int] = {}
    for PathInfoData in sorted(SegmentsDir.glob("segments_*.json")):
        PayloadInfo = JsonData.loads(PathInfoData.read_text(encoding="utf-8"))
        PartInfoInfo = PathInfo(str(PayloadInfo["part"]))
        if not PartInfoInfo.is_file():
            continue
        ArchiveInfo = SldprtArchive.from_bytes(PartInfoInfo.read_bytes())
        Found = ContainerMo(ArchiveInfo.streams)
        if Found is not None:
            Table[str(PayloadInfo["label"])] = Found
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def AuthoredVersion(Traced: Mapping[str, int]) -> Tuple[int | None, str]:
    Authored = {
        LabelInfo: Version
        for LabelInfo, Version in Traced.items()
        if not LabelInfo.startswith(KVendorPrefix)
    }
    if not Authored:
        return (
            None,
            "no authored traced part is present in this checkout, so no document version can be read for the donor corpus",
        )
    Found = sorted(set(Authored.values()))
    if len(Found) != 1:
        return (
            None,
            f"the {len(Authored)} authored traced parts disagree on the document version {Found}",
        )
    return (
        Found[0],
        f"{KMoVersionPrefix}{Found[0]} read from the {len(Authored)} authored traced parts, which the same writer produced as the donor corpus",
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def RecordedBases(SegmentsDir: PathInfo) -> DictInfo[str, int]:
    Table: DictInfo[str, int] = {}
    for PathInfoData in sorted(SegmentsDir.glob("segments_*.json")):
        PayloadInfo = JsonData.loads(PathInfoData.read_text(encoding="utf-8"))
        Table[str(PayloadInfo["label"])] = int(PayloadInfo["base_map_index"])
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def SeedBase(DonorInfo: PathInfo) -> Tuple[int, str]:
    FeatInfoInfo = FixtureCount(DonorInfo)
    if FeatInfoInfo > 0:
        return (
            KFirstFeatBase + FeatInfoInfo - 1,
            f"{KFirstFeatBase} + {FeatInfoInfo} - 1 from the features array of the fixture meta.json",
        )
    return (
        KFirstFeatBase,
        f"{KFirstFeatBase}, the base of the smallest traced document, because the fixture meta.json names no features array",
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def ResolvedBase(
    ByteBlob: bytes, Layouts: LayoutTable, SeedInfo: int, MoVersion: int | None
) -> BaseResolution:
    return ResolveBase(
        ByteBlob, SeedInfo, Layouts, header_size=KStreamHeaderSize, MoVersion=MoVersion
    )


# donor row construction stays isolated so segmentation evidence and aggregate reporting remain independent
def BuildDonorMut(
    DonorInfo: PathInfo,
    Layouts: LayoutTable,
    Partial: set[str],
    CorpusVersion: int | None,
    CorpusRule: str,
    Required: Collects.Counter,
    Versions: Collects.Counter,
) -> tuple[dict, str | None]:
    ByteBlob = (DonorInfo / "resolved.bin").read_bytes()
    SeedInfo, RuleInfo = SeedBase(DonorInfo)
    MoVersion, VersionRule = DonorMoVersion(DonorInfo)
    if MoVersion is None:
        MoVersion, VersionRule = (CorpusVersion, CorpusRule)
    Versions[MoVersion if MoVersion is not None else -1] += 1
    Resolve = ResolvedBase(ByteBlob, Layouts, SeedInfo, MoVersion)
    BaseInfo = Resolve.base
    Report = Verify(
        ByteBlob, BaseInfo, Layouts, header_size=KStreamHeaderSize, MoVersion=MoVersion
    )
    Scanned = ScannedNames(ByteBlob)
    Outstanding = sorted(
        (NameTextInfo for NameTextInfo in Scanned if NameTextInfo in Partial)
    )
    for NameTextInfo in Outstanding:
        Required[NameTextInfo] += 1
    RowDataInfo = {
        "donor": DonorInfo.name,
        "base_rule": RuleInfo,
        "base_method": "seed" if BaseInfo == SeedInfo else "refined",
        "mo_version": MoVersion if MoVersion is not None else -1,
        "mo_version_rule": VersionRule,
    }
    RowDataInfo.update(Report.as_dict())
    RowDataInfo.update(
        {
            "base": BaseInfo,
            "base_resolution": Resolve.as_dict(),
            "meta_feature_count": FixtureCount(DonorInfo),
            "meta_base": SeedInfo,
            "base_agrees_with_meta": SeedInfo == BaseInfo,
            "scanned_class_count": len(Scanned),
            "outstanding_partial_classes": Outstanding,
            "classes_absent_from_layout_table": sorted(
                (
                    NameTextInfo
                    for NameTextInfo in Scanned
                    if NameTextInfo not in Layouts.classes
                )
            ),
        }
    )
    Blocker = None
    if not Report.identical:
        Blocker = (
            f"{Report.blocking_class}@{Report.blocking_slot}"
            if Report.blocking_class
            else "<none>"
        )
    return RowDataInfo, Blocker


# report orchestration aggregates focused donor rows without owning segmentation mechanics
def RunTask(Fixtures: PathInfo, LayoutsPath: PathInfo, SegmentsDir: PathInfo) -> dict:
    Layouts = LayoutTable.load(LayoutsPath)
    Donors = sorted(
        (
            PathInfoData
            for PathInfoData in Fixtures.iterdir()
            if (PathInfoData / "resolved.bin").is_file()
        )
    )
    if not Donors:
        raise ValueError(f"no donor fixtures with resolved.bin under {Fixtures}")
    Partial = {
        NameTextInfo
        for NameTextInfo, Entry in Layouts.classes.items()
        if Entry.confidence != "confirmed"
    }
    GetRows: ListInfo[dict] = []
    Blockers: Collects.Counter = Collects.Counter()
    Required: Collects.Counter = Collects.Counter()
    Versions: Collects.Counter = Collects.Counter()
    Traced = TracedVersions(SegmentsDir)
    CorpusVersion, CorpusRule = AuthoredVersion(Traced)
    for DonorInfo in Donors:
        RowDataInfo, Blocker = BuildDonorMut(
            DonorInfo, Layouts, Partial, CorpusVersion, CorpusRule, Required, Versions
        )
        GetRows.append(RowDataInfo)
        if Blocker is not None:
            Blockers[Blocker] += 1
    Verified = [RowDataInfo for RowDataInfo in GetRows if RowDataInfo["identical"]]

    # needed to keep reverse engineering responsibilities isolated and maintainable
    return {
        "fixtures": str(Fixtures),
        "layouts": str(LayoutsPath),
        "layout_source": Layouts.source,
        "mo_versions": dict(sorted(Versions.items())),
        "mo_version_derivation": "a run length recorded under runs_by_version is selected by the document generation, which is the _MO_VERSION_<n> storage name in the containing SLDPRT; a donor fixture records only its Contents and Header2 streams, so none carries that storage and no meta.json holds an mo_version field, and the generation is therefore taken from the authored traced parts, whose writer also produced the donor corpus; -1 marks a donor whose generation could not be established, and such a donor is segmented with no version so a version gated run is refused rather than guessed",
        "mo_version_of_traced_parts": dict(sorted(Traced.items())),
        "class_count": len(Layouts.classes),
        "confirmed_classes": sum(
            (1 for Entry in Layouts.classes.values() if Entry.confidence == "confirmed")
        ),
        "donor_count": len(GetRows),
        "segmented_count": sum(
            (1 for RowDataInfo in GetRows if RowDataInfo["segmented"])
        ),
        "tiled_count": sum((1 for RowDataInfo in GetRows if RowDataInfo["tiled"])),
        "identical_count": len(Verified),
        "identical_donors": [RowDataInfo["donor"] for RowDataInfo in Verified],
        "blocking_runs": dict(
            sorted(Blockers.items(), key=lambda PairInfo: -PairInfo[1])
        ),
        "partial_classes": sorted(Partial),
        "outstanding_classes_by_donor_count": dict(
            sorted(Required.items(), key=lambda PairInfo: (-PairInfo[1], PairInfo[0]))
        ),
        "class_scan_caveat": "the per donor class name list comes from a static ff ff 01 00 scan, which over approximates because the marker also occurs inside object bodies; it is a lower bound on the layout work each donor needs, not a segmentation",
        "recorded_trace_bases": RecordedBases(SegmentsDir),
        "bases_taken_from_the_metadata_seed": sum(
            (1 for RowDataInfo in GetRows if RowDataInfo["base_agrees_with_meta"])
        ),
        "bases_refined_away_from_the_metadata_seed": [
            {
                "donor": RowDataInfo["donor"],
                "resolved": RowDataInfo["base"],
                "seed": RowDataInfo["meta_base"],
                "objects_reached": RowDataInfo["base_resolution"]["progress"],
                "tried": RowDataInfo["base_resolution"]["tried"],
            }
            for RowDataInfo in GetRows
            if not RowDataInfo["base_agrees_with_meta"]
        ],
        "base_derivation": "the base is seeded at 109 + feature_count - 1 from the features array of the fixture meta.json and then refined against the stream: when the walk stops on a class or object reference at or above the trial base that no definition has produced, the reference index minus the counter offset of every definition already reached names the bases that would resolve it, and each is walked in turn until one segments or the candidates run out; the base that reaches the most objects wins and the method column records whether that was the seed or a refinement; the seed is only a seed, because 109 + feature_count - 1 is refuted by the fixtures whose Contents/Config-0 node population differs from the traced boss family: a revolve feature adds one counter unit (boss_disjoint_revolve, boss_revcut and arcboss_cut_cut_cut_through_rev resolve one above the seed), a mid-plane end condition removes one (boss_midplane resolves one below), and the extra document metadata of arcboss_cut_cut_cut_through_rev_meta moves it to 337, far outside any fixed window",
        "donors": GetRows,
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    ParserInfo = Argparse.ArgumentParser()
    ParserInfo.add_argument("--fixtures", default=str(KDefaultData))
    ParserInfo.add_argument("--layouts", default=str(KDefaultLayouts))
    ParserInfo.add_argument("--segments", default=str(KDefaultValue))
    ParserInfo.add_argument("--out", required=True)
    ArgsInfo = ParserInfo.parse_args()
    PayloadInfo = RunTask(
        PathInfo(ArgsInfo.fixtures),
        PathInfo(ArgsInfo.layouts),
        PathInfo(ArgsInfo.segments),
    )
    Destination = PathInfo(ArgsInfo.out)
    Destination.parent.mkdir(parents=True, exist_ok=True)
    with Destination.open("w", encoding="utf-8") as Handle:
        JsonData.dump(PayloadInfo, Handle, indent=1)
        Handle.write("\n")
    print(
        "donors=%d segmented=%d tiled=%d identical=%d"
        % (
            PayloadInfo["donor_count"],
            PayloadInfo["segmented_count"],
            PayloadInfo["tiled_count"],
            PayloadInfo["identical_count"],
        )
    )
    for NameTextInfo, Tally in PayloadInfo["blocking_runs"].items():
        print("  blocked by %-38s %d" % (NameTextInfo, Tally))
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
