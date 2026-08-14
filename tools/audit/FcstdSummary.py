# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections import Counter
from typing import Any as AnyValue


# aggregate verdicts retain unsupported families so research can prioritize measured gaps
def BuildSummary(ResultsData: tuple[dict[str, AnyValue], ...]) -> dict[str, AnyValue]:
    UnsupportedTypes = Counter(
        TypeName
        for ResultData in ResultsData
        if not ResultData["vendor_loadable"]
        for TypeName in ResultData["feature_types"]
    )
    VendorOnlyTypes = Counter(
        TypeName
        for ResultData in ResultsData
        if ResultData["vendor_loadable"] and not ResultData["application_usable"]
        for TypeName in ResultData["feature_types"]
    )
    return {
        "files": len(ResultsData),
        "application_usable": sum(
            bool(ResultData["application_usable"]) for ResultData in ResultsData
        ),
        "vendor_loadable": sum(
            bool(ResultData["vendor_loadable"]) for ResultData in ResultsData
        ),
        "vendor_only": sum(
            bool(ResultData["vendor_loadable"])
            and not bool(ResultData["application_usable"])
            for ResultData in ResultsData
        ),
        "near_lossless": sum(
            bool(ResultData["near_lossless"]) for ResultData in ResultsData
        ),
        "errors": sum(bool(ResultData["error"]) for ResultData in ResultsData),
        "unsupported_feature_types": dict(sorted(UnsupportedTypes.items())),
        "vendor_only_feature_types": dict(sorted(VendorOnlyTypes.items())),
    }
