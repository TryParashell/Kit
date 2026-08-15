# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue

from convert.api.ApiOpen import OpenDocument
from convert.api.Compatibility.ApiCall import MakeApiCall, MakeCallSig


# document reads retain historical keyword spelling without weakening canonical option construction
def MakeOpenCall() -> AnyValue:
    DefaultsMap = {
        "source_format": None,
        "configuration": None,
        "include_brep": True,
        "include_tessellation": True,
        "strict": True,
    }
    return MakeApiCall(
        OpenDocument,
        "open_document",
        {
            "source": "SourceData",
            "source_format": "SourceFormat",
            "configuration": "Configuration",
            "include_brep": "IncludeBrep",
            "include_tessellation": "IncludeTess",
            "strict": "StrictMode",
        },
        {
            "source": "Source",
            "source_format": "str | None",
            "configuration": "str | None",
            "include_brep": "bool",
            "include_tessellation": "bool",
            "strict": "bool",
            "return": "CadDocument",
        },
        MakeCallSig(
            (("source", "Source"),),
            (
                ("source_format", "str | None", None),
                ("configuration", "str | None", None),
                ("include_brep", "bool", True),
                ("include_tessellation", "bool", True),
                ("strict", "bool", True),
            ),
            "CadDocument",
        ),
        DefaultsMap,
    )
