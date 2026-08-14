# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from inspect import Signature as FuncSig
from typing import Any as AnyValue

from convert.engine.Compatibility.EngineCall import MakeCallSig, MakeEngineCall
from convert.engine.EngineInit import InitEngineMut


# engine construction retains its historical dependency injection signature for custom registries
def MakeConstructor() -> AnyValue:
    return MakeEngineCall(
        InitEngineMut,
        "__init__",
        {"registry": "RegistryData"},
        {"registry": "AdapterRegistry"},
        MakeCallSig(
            (("self", None), ("registry", "AdapterRegistry")),
            (),
            FuncSig.empty,
        ),
        None,
    )
