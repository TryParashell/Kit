# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass

from convert.adapters.base.ContractCompat import ContractBase


# probe results keep reader selection evidence deterministic and bounded
@DataClass(frozen=True, slots=True)
class ProbeResult(ContractBase):
    FormatId: str
    Confidence: float
    ReasonText: str = ""

    # confidence validation prevents malformed adapters from corrupting reader ordering
    def __post_init__(SelfValue) -> None:
        if not 0.0 <= SelfValue.Confidence <= 1.0:
            raise ValueError("probe confidence must be between zero and one")
