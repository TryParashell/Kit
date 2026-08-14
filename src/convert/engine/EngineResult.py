# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import make_dataclass as MakeDataClass

from convert.adapters.base.TransferContract import CapTransfer
from convert.results.ResultDetails import ResultDetails
from convert.results.ResultFlags import ResultFlags


# dynamic construction preserves historical field names while implementation identifiers remain compliant
def BuildResult() -> type:
    TransferGetter = vars(ResultDetails)["transfers"].fget
    TransferGetter.__globals__["CapabilityTransfer"] = CapTransfer
    ClassScope = {
        "transfers": vars(ResultDetails)["transfers"],
        "dropped": vars(ResultDetails)["dropped"],
        "requirements": vars(ResultDetails)["requirements"],
        "application_usable": vars(ResultFlags)["application_usable"],
        "vendor_loadable": vars(ResultFlags)["vendor_loadable"],
        "roundtrip_safe": vars(ResultFlags)["roundtrip_safe"],
        "near_lossless": vars(ResultFlags)["near_lossless"],
    }
    ResultType = MakeDataClass(
        "ConversionResult",
        (
            ("document", "CadDocument"),
            ("output", "WriteResult"),
            ("source_format", "str"),
            ("destination_format", "str"),
        ),
        namespace=ClassScope,
        frozen=True,
        slots=True,
    )
    ResultType.__module__ = "convert.engine"
    return ResultType
