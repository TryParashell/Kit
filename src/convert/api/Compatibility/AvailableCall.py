# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue

from convert.api.ApiAvailable import ListAdapters
from convert.api.Compatibility.ApiCall import MakeApiCall, MakeCallSig


# adapter discovery keeps its historical callable identity for schema and pickle consumers
def MakeAvailable() -> AnyValue:
    return MakeApiCall(
        ListAdapters,
        "available_adapters",
        {},
        {"return": "tuple[AdapterInfo, ...]"},
        MakeCallSig((), (), "tuple[AdapterInfo, ...]"),
        None,
    )
