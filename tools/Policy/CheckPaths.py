# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import sys as System

from tools.Policy.BuildParser import BuildParser
from tools.Policy.CheckPathPolicy import CheckPathPolicy
from tools.Policy.FormatFinding import FormatFinding
from tools.Policy.GitFailure import GitFailure
from tools.Policy.LoadChanged import LoadChanged
from tools.Policy.LoadTracked import LoadTracked
from tools.Policy.LoadTree import LoadTree


# command orchestration gives local and pull request checks identical exit semantics
def MainRun(ArgList: list[str] | None = None) -> int:
    ParserInfo = BuildParser()
    ArgsInfo = ParserInfo.parse_args(ArgList)
    if (ArgsInfo.BaseRef is None) != (ArgsInfo.HeadRef is None):
        ParserInfo.error("--base and --head must be provided together")
    RootPath = ArgsInfo.RootPath.resolve()
    try:
        if ArgsInfo.BaseRef is None:
            TrackedPaths = LoadTracked(RootPath)
            TargetPaths = None
            ModeText = "full tree"
        else:
            TrackedPaths = LoadTree(RootPath, ArgsInfo.HeadRef)
            TargetPaths = LoadChanged(RootPath, ArgsInfo.BaseRef, ArgsInfo.HeadRef)
            ModeText = "changed destination"
        FindingList = CheckPathPolicy(TrackedPaths, TargetPaths)
    except GitFailure as ErrorInfo:
        print(f"path policy input error: {ErrorInfo}", file=System.stderr)
        return 2
    for FindingInfo in FindingList:
        print(FormatFinding(FindingInfo))
    if FindingList:
        print(
            f"path policy failed with {len(FindingList)} violations",
            file=System.stderr,
        )
        return 1
    CheckedCount = len(TrackedPaths if TargetPaths is None else TargetPaths)
    print(f"path policy passed in {ModeText} mode for {CheckedCount} paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
