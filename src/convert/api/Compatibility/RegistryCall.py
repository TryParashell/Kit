# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue

from convert.api.ApiContext import GetRegistry
from convert.api.Compatibility.ApiCall import MakeApiCall, MakeCallSig


# registry lookup retains its historical private hook for direct module consumers
def MakeRegCall() -> AnyValue:
    return MakeApiCall(
        GetRegistry,
        "_build_registry",
        {},
        {"return": "AdapterRegistry"},
        MakeCallSig((), (), "AdapterRegistry"),
        None,
    )
