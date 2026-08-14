# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath
from tempfile import TemporaryDirectory

from tools.audit.FcstdArgs import ParseArguments
from tools.audit.FcstdDiscovery import DiscoverSources
from tools.audit.FcstdOutput import PrintReport
from tools.audit.FcstdSummary import BuildSummary
from tools.audit.FcstdWorker import RunWorker


# top level orchestration keeps discovery isolation reporting and failure policy synchronized
def MainRun() -> int:
    ArgumentsData = ParseArguments()
    if ArgumentsData.worker_source is not None:
        return RunWorker(ArgumentsData)
    from tools.audit.FcstdIsolate import AuditIsolated

    SourcePaths = DiscoverSources(tuple(ArgumentsData.roots))
    with TemporaryDirectory(prefix="kit-fcstd-audit-") as TemporaryPath:
        OutputRoot = FilePath(TemporaryPath)
        ResultsData = tuple(
            AuditIsolated(SourcePath, OutputRoot, SourceIndex)
            for SourceIndex, SourcePath in enumerate(SourcePaths)
        )
    SummaryData = BuildSummary(ResultsData)
    PrintReport(ResultsData, SummaryData, ArgumentsData.json)
    HasFailures = any(not ResultData["vendor_loadable"] for ResultData in ResultsData)
    return int(ArgumentsData.require_vendor_loadable and HasFailures)
