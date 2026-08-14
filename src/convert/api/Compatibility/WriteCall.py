# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue

from convert.api.ApiWrite import WriteDocument
from convert.api.Compatibility.ApiCall import MakeApiCall, MakeCallSig


# document writes retain historical keywords while portable output policy stays centralized
def MakeWriteCall() -> AnyValue:
    DefaultsMap = {
        "destination_format": None,
        "configuration": None,
        "overwrite": False,
        "validate": True,
        "allow_carrier": True,
        "values": None,
    }
    return MakeApiCall(
        WriteDocument,
        "write_document",
        {
            "document": "DocumentData",
            "destination": "TargetData",
            "destination_format": "DestFormat",
            "configuration": "Configuration",
            "overwrite": "Overwrite",
            "validate": "ValidateData",
            "allow_carrier": "AllowCarrier",
            "values": "InputValues",
        },
        {
            "document": "CadDocument",
            "destination": "Destination",
            "destination_format": "str | None",
            "configuration": "str | None",
            "overwrite": "bool",
            "validate": "bool",
            "allow_carrier": "bool",
            "values": "Mapping[str, Any] | None",
            "return": "WriteResult",
        },
        MakeCallSig(
            (("document", "CadDocument"), ("destination", "Destination")),
            (
                ("destination_format", "str | None", None),
                ("configuration", "str | None", None),
                ("overwrite", "bool", False),
                ("validate", "bool", True),
                ("allow_carrier", "bool", True),
                ("values", "Mapping[str, Any] | None", None),
            ),
            "WriteResult",
        ),
        DefaultsMap,
    )
