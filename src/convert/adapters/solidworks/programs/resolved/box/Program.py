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

from convert.adapters.solidworks.programs.Common.FieldEncoder import (
    KPrimitiveFormats,
    ReplayResolved,
)

from .Registry import (
    FieldOwners,
    ResolvedOps,
)


# legacy format access remains available while shared encoding owns the mapping
globals()["PrimitiveFormats"] = KPrimitiveFormats


# callers can replace semantic fields while retaining recovered object framing
def EncodeProgram(Overrides: Mapping[int, AnyValue] | None = None) -> bytes:
    ExpectedLength = ResolvedOps[-1][0] + ResolvedOps[-1][1]
    return ReplayResolved(ResolvedOps, ExpectedLength, Overrides)
