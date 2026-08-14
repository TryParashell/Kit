# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue

from convert.engine.Compatibility.EngineCall import MakeCallSig, MakeEngineCall
from convert.engine.EngineWriter import EngineWrite


# engine writes retain historical keywords while registry delegation stays independently testable
def MakeWriteCall() -> AnyValue:
    DefaultsMap = {"format_id": None, "options": None}
    return MakeEngineCall(
        EngineWrite.WriteTarget,
        "write",
        {
            "document": "DocumentData",
            "destination": "TargetData",
            "format_id": "FormatId",
            "options": "WriteOpts",
        },
        {
            "document": "CadDocument",
            "destination": "Destination",
            "format_id": "str | None",
            "options": "WriteOptions | None",
            "return": "WriteResult",
        },
        MakeCallSig(
            (
                ("self", None),
                ("document", "CadDocument"),
                ("destination", "Destination"),
            ),
            (
                ("format_id", "str | None", None),
                ("options", "WriteOptions | None", None),
            ),
            "WriteResult",
        ),
        DefaultsMap,
    )
