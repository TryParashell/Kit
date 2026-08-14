# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import json as JsonData
from typing import Any as AnyValue


# worker mode isolates risky documents while retaining one public command entry point
def RunWorker(ArgumentsData: AnyValue) -> int:
    from tools.audit.FcstdAudit import AuditSource

    WorkerSource = ArgumentsData.worker_source
    WorkerOutput = ArgumentsData.worker_output
    WorkerIndex = ArgumentsData.worker_index
    if WorkerOutput is None or WorkerIndex is None:
        raise SystemExit("audit worker arguments are incomplete")
    ResultData = AuditSource(
        WorkerSource.resolve(),
        WorkerOutput.resolve(),
        WorkerIndex,
    )
    print(JsonData.dumps(ResultData, separators=(",", ":")))
    return 0
