# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue

from convert.engine.Compatibility.EngineCall import MakeCallSig, MakeEngineCall
from convert.engine.EngineReader import EngineRead


# engine reads retain historical keywords while registry delegation stays independently testable
def MakeReadCall() -> AnyValue:
    DefaultsMap = {"format_id": None, "options": None}
    return MakeEngineCall(
        EngineRead.ReadSource,
        "read",
        {
            "source": "SourceData",
            "format_id": "FormatId",
            "options": "ReadOpts",
        },
        {
            "source": "Source",
            "format_id": "str | None",
            "options": "ReadOptions | None",
            "return": "CadDocument",
        },
        MakeCallSig(
            (("self", None), ("source", "Source")),
            (
                ("format_id", "str | None", None),
                ("options", "ReadOptions | None", None),
            ),
            "CadDocument",
        ),
        DefaultsMap,
    )
