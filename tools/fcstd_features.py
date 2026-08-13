# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
from typing import Any as AnyValue


# feature identity exposes unsupported grammar without relying on unstable source filenames
def FeatureTypes(DocumentData: AnyValue) -> tuple[str, ...]:
    TypeNames: set[str] = set()
    for FeatureData in DocumentData.feature_timeline:
        FreecadData = FeatureData.attributes.get("freecad")
        TypeName = (
            FreecadData.get("type_id", "") if isinstance(FreecadData, Mapping) else ""
        )
        TypeNames.add(str(TypeName or FeatureData.kind))
    return tuple(sorted(TypeNames))
