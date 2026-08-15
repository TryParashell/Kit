# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass
from typing import TYPE_CHECKING as IsTypeCheck
from typing import overload as Overload

from convert.adapters.base.ContractCompat import ContractBase


# probe results keep reader selection evidence deterministic and bounded
@DataClass(frozen=True, slots=True)
class ProbeResult(ContractBase):
    FormatId: str
    Confidence: float
    ReasonText: str = ""

    if IsTypeCheck:

        # historical keywords remain typed because reader plugins construct this public evidence record
        @Overload
        def __init__(
            self,
            format_id: str,
            confidence: float,
            reason: str = "",
        ) -> None: ...

        # canonical keywords remain typed because dataclass replacement reconstructs evidence from storage fields
        @Overload
        def __init__(
            self,
            FormatId: str,
            Confidence: float,
            ReasonText: str = "",
        ) -> None: ...

        # broad implementation parameters exist only to connect both statically checked constructor forms
        def __init__(self, *ArgValues: object, **NamedValues: object) -> None: ...

    # historical format access remains typed because selector diagnostics consume this public field
    @property
    def format_id(self) -> str:
        return self.FormatId

    # historical confidence access remains typed because selectors rank this public field
    @property
    def confidence(self) -> float:
        return self.Confidence

    # historical reason access remains typed because selector diagnostics expose this public field
    @property
    def reason(self) -> str:
        return self.ReasonText

    # confidence validation prevents malformed adapters from corrupting reader ordering
    def __post_init__(self) -> None:
        if not 0.0 <= self.Confidence <= 1.0:
            raise ValueError("probe confidence must be between zero and one")
