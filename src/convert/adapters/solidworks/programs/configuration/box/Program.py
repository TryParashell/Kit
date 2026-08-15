# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping
from convert.adapters.solidworks.programs.Common.ProgramContract import (
    FieldValue as FieldType,
)

from convert.adapters.solidworks.programs.Common.FieldEncoder import ReplayFixed

from .Registry import (
    KFieldOwners,
    ConfigOps,
)


# compatibility binding preserves the generated owner catalog facade
FieldOwners = KFieldOwners

# exact closure proves the fixed program accounts for the complete stream
KReferenceLength = 25158

# legacy length access remains available while the invariant uses constant naming
ReferenceLength = KReferenceLength


# typed replay emits the fixed configuration without retaining vendor byte spans
def EncodeProgram(Overrides: Mapping[int, FieldType] | None = None) -> bytes:
    return ReplayFixed(ConfigOps, KReferenceLength, "Config-0", Overrides)
