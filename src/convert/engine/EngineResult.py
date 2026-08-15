# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass as DataClass
from typing import TypeVar

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability

from convert.adapters.base.TransferContract import CapTransfer as CapabilityTransfer
from convert.adapters.base.WriteResult import WriteResult

# reflected getters need their public package owner without replacing concrete descriptors
GetterType = TypeVar("GetterType", bound=Callable[..., object])


# public schema ownership differs from the focused implementation module by design
def SetResultOwner(GetterValue: GetterType) -> GetterType:
    GetterValue.__module__ = "convert.engine"
    return GetterValue


# conversion outcomes need a stable static record for callers and type checkers
@DataClass(frozen=True, slots=True)
class ConversionResult:
    document: CadDocument
    output: WriteResult
    source_format: str
    destination_format: str

    # transfer evidence stays beside the conversion outcome for direct caller policy checks
    @property
    @SetResultOwner
    def transfers(self) -> tuple[CapabilityTransfer, ...]:
        return self.output.Transfers

    # loss evidence remains direct because callers gate conversion success on it
    @property
    @SetResultOwner
    def dropped(self) -> frozenset[Capability]:
        return self.output.DroppedCaps

    # output requirements stay visible without exposing writer implementation details
    @property
    @SetResultOwner
    def requirements(self) -> tuple[str, ...]:
        return self.output.Requirements

    # usability remains a conversion level predicate because clients consume conversion results
    @property
    @SetResultOwner
    def application_usable(self) -> bool:
        return self.output.IsAppUsable

    # vendor readability remains separate from broader application usability
    @property
    @SetResultOwner
    def vendor_loadable(self) -> bool:
        return self.output.IsVendorLoadable

    # loss status stays explicit because output evidence can be independently inspected
    @property
    @SetResultOwner
    def roundtrip_safe(self) -> bool:
        return self.output.IsRoundtripSafe

    # near losslessness remains direct because it is a primary conversion guarantee
    @property
    @SetResultOwner
    def near_lossless(self) -> bool:
        return self.output.IsNearLossless


ConversionResult.__module__ = "convert.engine"
