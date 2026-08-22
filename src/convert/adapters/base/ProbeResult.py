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
    format_id: str
    confidence: float
    reason: str = ""

    # historical format access remains typed because selector diagnostics consume this public field
    @property
    def FormatId(self) -> str:
        return self.format_id

    # historical confidence access remains typed because selectors rank this public field
    @property
    def Confidence(self) -> float:
        return self.confidence

    # historical reason access remains typed because selector diagnostics expose this public field
    @property
    def ReasonText(self) -> str:
        return self.reason

    # confidence validation prevents malformed adapters from corrupting reader ordering
    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("probe confidence must be between zero and one")
