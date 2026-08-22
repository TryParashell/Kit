# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import ast as AstLib
import sys as System
from collections.abc import Iterable
from pathlib import Path as FilePath

from tools.Policy.BuildParser import BuildParser
from tools.Policy.GitFailure import GitFailure
from tools.Policy.LoadChanged import LoadChanged
from tools.Policy.ParseGitPaths import ParseGitPaths
from tools.Policy.RunGitCommand import RunGitCommand
from tools.steering.SteeringCompliance import (
    BuildParents,
    CheckReasons,
    Finding,
    FormatFinding,
    GetNewFindings,
    LoadBaseline,
    ReadSource,
)

# vendored and generated trees stay out of scope because steering governs owned sources only
KSkipParts = frozenset({"examples", "modules", "parashell", "re"})

# baseline location stays fixed so every mode shares one accepted debt record
KBaselineRel = FilePath("tools/steering/SteeringBaseline.txt")


# path selection keeps every mode focused on owned python sources worth reviewing
def SelectPaths(PathNames: Iterable[str]) -> list[FilePath]:
    SelectedPaths: list[FilePath] = []
    for PathName in PathNames:
        CandidatePath = FilePath(PathName)
        if CandidatePath.suffix != ".py":
            continue
        if any(PartText.casefold() in KSkipParts for PartText in CandidatePath.parts):
            continue
        SelectedPaths.append(CandidatePath)
    return sorted(set(SelectedPaths))


# revision content loading keeps comparisons independent from dirty worktree state
def LoadRevText(RootPath: FilePath, RefText: str, RepoPath: FilePath) -> str:
    OutputData = RunGitCommand(RootPath, ["show", f"{RefText}:{RepoPath.as_posix()}"])
    return OutputData.decode("utf-8")


# tolerant base loading lets newly added files compare against empty prior state
def LoadBaseText(RootPath: FilePath, RefText: str, RepoPath: FilePath) -> str | None:
    try:
        return LoadRevText(RootPath, RefText, RepoPath)
    except GitFailure:
        return None


# rationale extraction stays delegated because one predicate owns every placement rule
def FindReasons(RepoPath: FilePath, SourceText: str) -> list[Finding]:
    SyntaxTree = AstLib.parse(SourceText, filename=RepoPath.as_posix())
    ParentMap = BuildParents(SyntaxTree)
    return CheckReasons(RepoPath, SourceText, SyntaxTree, ParentMap)


# surplus subtraction reports only violations the reviewed change introduces or deepens
def CollectDiff(
    RootPath: FilePath,
    BaseRef: str,
    HeadRef: str,
    RepoPaths: Iterable[FilePath],
) -> list[Finding]:
    FindingList: list[Finding] = []
    for RepoPath in RepoPaths:
        HeadFindings = FindReasons(RepoPath, LoadRevText(RootPath, HeadRef, RepoPath))
        BaseFindings: list[Finding] = []
        BaseText = LoadBaseText(RootPath, BaseRef, RepoPath)
        if BaseText is not None:
            BaseFindings = FindReasons(RepoPath, BaseText)
        FindingList.extend(GetNewFindings(HeadFindings, BaseFindings))
    return FindingList


# whole tree runs stay aligned with steering because both share one accepted baseline
def CollectFull(RootPath: FilePath, RepoPaths: Iterable[FilePath]) -> list[Finding]:
    FindingList = CollectAll(RootPath, RepoPaths)
    BaselinePath = RootPath / KBaselineRel
    if BaselinePath.exists():
        return GetNewFindings(FindingList, LoadBaseline(BaselinePath))
    return FindingList


# raw collection stays separate because diff comparisons never consult accepted debt
def CollectAll(RootPath: FilePath, RepoPaths: Iterable[FilePath]) -> list[Finding]:
    FindingList: list[Finding] = []
    for RepoPath in RepoPaths:
        FindingList.extend(FindReasons(RepoPath, ReadSource(RootPath / RepoPath)))
    return FindingList


# command orchestration gives local and continuous integration runs identical exit semantics
def MainRun(ArgList: list[str] | None = None) -> int:
    ParserInfo = BuildParser()
    ArgsInfo = ParserInfo.parse_args(ArgList)
    if (ArgsInfo.BaseRef is None) != (ArgsInfo.HeadRef is None):
        ParserInfo.error("--base and --head must be provided together")
    RootPath = ArgsInfo.RootPath.resolve()
    try:
        if ArgsInfo.BaseRef is None:
            TrackedData = RunGitCommand(RootPath, ["ls-files", "-z", "--", "*.py"])
            TargetPaths = SelectPaths(ParseGitPaths(TrackedData))
            FindingList = CollectFull(RootPath, TargetPaths)
            ModeText = "full tree"
        else:
            ChangedPaths = LoadChanged(RootPath, ArgsInfo.BaseRef, ArgsInfo.HeadRef)
            TargetPaths = SelectPaths(ChangedPaths)
            FindingList = CollectDiff(
                RootPath, ArgsInfo.BaseRef, ArgsInfo.HeadRef, TargetPaths
            )
            ModeText = "changed destination"
    except (OSError, UnicodeError, SyntaxError, ValueError, GitFailure) as ErrorInfo:
        print(f"rationale compliance input error: {ErrorInfo}", file=System.stderr)
        return 2
    for FindingInfo in sorted(FindingList):
        print(FormatFinding(FindingInfo))
    if FindingList:
        print(
            f"rationale compliance failed with {len(FindingList)} violations",
            file=System.stderr,
        )
        return 1
    print(
        f"rationale compliance passed in {ModeText} mode "
        f"for {len(TargetPaths)} python files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
