# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.engine.Compatibility.ConstructorCall import MakeConstructor
from convert.engine.Compatibility.ConvertCall import MakeConvertCall
from convert.engine.Compatibility.EngineCall import SetResultType
from convert.engine.Compatibility.ReadCall import MakeReadCall
from convert.engine.Compatibility.WriteCall import MakeWriteCall


# dynamic composition preserves the historical class surface without merging engine responsibilities
def BuildEngine(ResultType: type) -> type:
    SetResultType(ResultType)
    ClassScope = {
        "__init__": MakeConstructor(),
        "read": MakeReadCall(),
        "write": MakeWriteCall(),
        "convert": MakeConvertCall(),
    }
    EngineType = type("ConversionEngine", (), ClassScope)
    EngineType.__module__ = "convert.engine"
    return EngineType
