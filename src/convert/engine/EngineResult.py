# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import dataclass as DataClass

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability

from convert.adapters.base.TransferContract import CapTransfer as CapabilityTransfer
from convert.adapters.base.WriteResult import WriteResult


# conversion outcomes need a stable static record for callers and type checkers
@DataClass(frozen=True, slots=True)
class ConversionResult:
    document: CadDocument
    output: WriteResult
    source_format: str
    destination_format: str

    # transfer evidence stays beside the conversion outcome for direct caller policy checks
    @property
    def transfers(self) -> tuple[CapabilityTransfer, ...]:
        return self.output.Transfers

    # loss evidence remains direct because callers gate conversion success on it
    @property
    def dropped(self) -> frozenset[Capability]:
        return self.output.DroppedCaps

    # output requirements stay visible without exposing writer implementation details
    @property
    def requirements(self) -> tuple[str, ...]:
        return self.output.Requirements

    # usability remains a conversion level predicate because clients consume conversion results
    @property
    def application_usable(self) -> bool:
        return self.output.IsAppUsable

    # vendor readability remains separate from broader application usability
    @property
    def vendor_loadable(self) -> bool:
        return self.output.IsVendorLoadable

    # loss status stays explicit because output evidence can be independently inspected
    @property
    def roundtrip_safe(self) -> bool:
        return self.output.IsRoundtripSafe

    # near losslessness remains direct because it is a primary conversion guarantee
    @property
    def near_lossless(self) -> bool:
        return self.output.IsNearLossless


ConversionResult.__module__ = "convert.engine"
ConversionResult.__annotations__ = {
    "document": "CadDocument",
    "output": "WriteResult",
    "source_format": "str",
    "destination_format": "str",
}
ConversionResult.__init__.__annotations__ = {
    "document": "CadDocument",
    "output": "WriteResult",
    "source_format": "str",
    "destination_format": "str",
    "return": None,
}
ConversionResult.transfers.fget.__module__ = "convert.engine"
ConversionResult.transfers.fget.__annotations__ = {
    "return": "tuple[CapabilityTransfer, ...]"
}
ConversionResult.dropped.fget.__module__ = "convert.engine"
ConversionResult.dropped.fget.__annotations__ = {"return": "frozenset[Capability]"}
ConversionResult.requirements.fget.__module__ = "convert.engine"
ConversionResult.requirements.fget.__annotations__ = {"return": "tuple[str, ...]"}
ConversionResult.application_usable.fget.__module__ = "convert.engine"
ConversionResult.application_usable.fget.__annotations__ = {"return": "bool"}
ConversionResult.vendor_loadable.fget.__module__ = "convert.engine"
ConversionResult.vendor_loadable.fget.__annotations__ = {"return": "bool"}
ConversionResult.roundtrip_safe.fget.__module__ = "convert.engine"
ConversionResult.roundtrip_safe.fget.__annotations__ = {"return": "bool"}
ConversionResult.near_lossless.fget.__module__ = "convert.engine"
ConversionResult.near_lossless.fget.__annotations__ = {"return": "bool"}
