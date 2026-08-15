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
import Cdbdrive as Cdbdrive
import Tracelog as Tracelog
import Streamlib as Streamlib

# needed to keep reverse engineering responsibilities isolated and maintainable
KOutInfo = KScratch / "trace" / "out"

# needed to keep reverse engineering responsibilities isolated and maintainable
KControl = (KScratch / "corpus" / "parts" / "BASELINE_40x20x10.SLDPRT").resolve()

# needed to keep reverse engineering responsibilities isolated and maintainable
KScript = '.symopt+0x4000\n.symopt-0x20000\n.exepath+ {solidworks}\n.reload /f swccu.dll\nr $t0 = 0\nbp swccu!su_CArchive::ReadClass "r $t0 = @$t0+1; .printf \\"CALIB %d this=%p\\\\n\\", @$t0, @rcx; dq @rcx L18; .if (@$t0 >= {hits}) {{ bc * }}; g"\nbl\ng\n'

# needed to keep reverse engineering responsibilities isolated and maintainable
KMinBuffer = 256

# needed to keep reverse engineering responsibilities isolated and maintainable
KMaxBuffer = 1 << 26


# needed to keep reverse engineering responsibilities isolated and maintainable
class Calibration(RuntimeError):
    __slots__ = ()


# needed to keep reverse engineering responsibilities isolated and maintainable
def WriteScript(PathInfoData: PathInfo, HitsInfo: int) -> None:
    PathInfoData.write_text(
        KScript.format(solidworks=Cdbdrive.KSolidworksDir, hits=HitsInfo),
        encoding="ascii",
    )


# needed to keep reverse engineering responsibilities isolated and maintainable
def Group(
    Dumps: tuple[Tracelog.DumpRecord, ...],
) -> dict[int, list[Tracelog.DumpRecord]]:
    Table: dict[int, list[Tracelog.DumpRecord]] = {}
    for DumpData in Dumps:
        Table.setdefault(DumpData.this, []).append(DumpData)
    return Table


# needed to keep reverse engineering responsibilities isolated and maintainable
def IsGlobally(
    Dumps: tuple[Tracelog.DumpRecord, ...], KeyName: tuple[int, int, int]
) -> bool:
    Cursor, IsTopInfo, StartRun = KeyName
    for DumpData in Dumps:
        BaseInfo = DumpData.u64(StartRun)
        if BaseInfo == 0:
            continue
        if not BaseInfo <= DumpData.u64(Cursor) <= DumpData.u64(IsTopInfo):
            return False
    return True


# one starting slot vote stays isolated so pointer candidate rules remain reviewable
def VoteStartMut(
    Series: list[Tracelog.DumpRecord],
    Slots: range,
    Expect: int,
    StartRun: int,
    Votes: dict[tuple[int, int, int], int],
    Anchored: set[tuple[int, int, int]],
) -> None:
    FixedStart = {DumpData.u64(StartRun) for DumpData in Series}
    if len(FixedStart) != 1:
        return
    BaseInfo = next(iter(FixedStart))
    if BaseInfo == 0:
        return
    for IsTopInfo in Slots:
        if IsTopInfo == StartRun:
            continue
        FixedTop = {DumpData.u64(IsTopInfo) for DumpData in Series}
        if len(FixedTop) != 1:
            continue
        SpanInfo = next(iter(FixedTop)) - BaseInfo
        if not KMinBuffer <= SpanInfo <= KMaxBuffer:
            continue
        for Cursor in Slots:
            if Cursor in (StartRun, IsTopInfo):
                continue
            Values = [DumpData.u64(Cursor) for DumpData in Series]
            if len(set(Values)) < 2:
                continue
            if any((LeftInfo > Right for LeftInfo, Right in zip(Values, Values[1:]))):
                continue
            if any(
                (
                    ValueInfo < BaseInfo or ValueInfo > BaseInfo + SpanInfo
                    for ValueInfo in Values
                )
            ):
                continue
            KeyName = (Cursor, IsTopInfo, StartRun)
            Votes[KeyName] = Votes.get(KeyName, 0) + 1
            if SpanInfo == Expect:
                Anchored.add(KeyName)


# solver orchestration aggregates independent slot votes before selecting a stable layout
def Solve(Dumps: tuple[Tracelog.DumpRecord, ...], Expect: int) -> dict[str, int]:
    WidthInfo = min((len(DumpData.raw) for DumpData in Dumps))
    Slots = range(0, WidthInfo - 7, 8)
    Votes: dict[tuple[int, int, int], int] = {}
    Anchored: set[tuple[int, int, int]] = set()
    for Series in Group(Dumps).values():
        if len(Series) < 2:
            continue
        for StartRun in Slots:
            VoteStartMut(Series, Slots, Expect, StartRun, Votes, Anchored)
    Votes = {
        KeyName: Score for KeyName, Score in Votes.items() if IsGlobally(Dumps, KeyName)
    }
    if not Votes:
        raise Calibration("no self-consistent buffer pointer triple was observed")
    PoolInfo = {KeyName for KeyName in Anchored if KeyName in Votes} or set(Votes)

    # needed to keep reverse engineering responsibilities isolated and maintainable
    BestInfo = max(PoolInfo, key=lambda KeyName: Votes[KeyName])
    Cursor, IsTopInfo, StartRun = BestInfo
    return {
        "cur": Cursor,
        "max": IsTopInfo,
        "start": StartRun,
        "map": StartRun + 8,
        "votes": Votes[BestInfo],
        "candidates": len(Votes),
        "anchored_candidates": len(Anchored),
        "anchor_span": Expect,
    }


# needed to keep reverse engineering responsibilities isolated and maintainable
def Verify(
    Dumps: tuple[Tracelog.DumpRecord, ...], Layout: dict[str, int]
) -> dict[str, object]:
    Monotonic = 0
    Breaks = 0
    for Series in Group(Dumps).values():
        Values = [DumpData.u32(Layout["map"]) for DumpData in Series]
        for LeftInfo, Right in zip(Values, Values[1:]):
            if Right >= LeftInfo:
                Monotonic += 1
            else:
                Breaks += 1
    return {"map_non_decreasing": Monotonic, "map_decreases": Breaks}


# needed to keep reverse engineering responsibilities isolated and maintainable
def MainRun() -> int:
    HitsInfo = int(System.argv[1]) if len(System.argv) > 1 else 200
    ModeInfo = System.argv[2] if len(System.argv) > 2 else "run"
    KOutInfo.mkdir(parents=True, exist_ok=True)
    Script = KHereInfo / "CdbCalibrate.txt"
    LogInfo = KOutInfo / "cdb_calibrate.log"
    WriteScript(Script, HitsInfo)
    if ModeInfo == "run":
        Result = Cdbdrive.RunTask(
            Script,
            LogInfo,
            KControl,
            Marker="^CALIB ",
            TargetMarkers=HitsInfo,
            HardDeadline=420.0,
            QuietSeconds=40.0,
        )
        print(
            f"cdb finished reason={Result.reason} CALIB={Result.markers} seconds={Result.seconds:.1f}"
        )
    Dumps = Tracelog.ReadDumps(LogInfo)
    print(f"dumps={len(Dumps)} archives={len(Group(Dumps))}")
    Expect = len(Streamlib.LoadDonor(KControl).resolved)
    Layout = Solve(Dumps, Expect)
    Checks = Verify(Dumps, Layout)
    PayloadInfo = {
        "log": str(LogInfo),
        "script": str(Script),
        "dumps": len(Dumps),
        "archives": len(Group(Dumps)),
        "layout": Layout,
        "checks": Checks,
    }
    (KOutInfo / "Calibrate.json").write_text(
        JsonData.dumps(PayloadInfo, indent=2), encoding="utf-8"
    )
    print(JsonData.dumps(PayloadInfo, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
