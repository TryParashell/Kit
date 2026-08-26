# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import json as JsonData

from tools.audit.FcstdResult import AuditRecord
from tools.audit.FcstdSummary import AuditSummary


# state classification keeps human output aligned with machine readable verdict fields
def GetState(ResultData: AuditRecord) -> str:
    if ResultData["application_usable"]:
        return "usable"
    if ResultData["vendor_loadable"]:
        return "vendor-only"
    if ResultData["error"]:
        return "error"
    return "unsupported"


# detail selection gives failures priority while retaining feature or requirement evidence
def GetDetail(ResultData: AuditRecord) -> str:
    return (
        ResultData["error"]
        or ",".join(ResultData["feature_types"])
        or ",".join(ResultData["requirements"])
    )


# report rendering keeps json and concise terminal formats semantically equivalent
def PrintReport(
    ResultsData: tuple[AuditRecord, ...],
    SummaryData: AuditSummary,
    IsJson: bool,
) -> None:
    if IsJson:
        print(JsonData.dumps({"summary": SummaryData, "files": ResultsData}, indent=2))
        return
    for ResultData in ResultsData:
        StateValue = GetState(ResultData)
        DetailValue = GetDetail(ResultData)
        print(f"{StateValue:11} {ResultData['path']} {DetailValue}")
    print(JsonData.dumps(SummaryData, sort_keys=True))
