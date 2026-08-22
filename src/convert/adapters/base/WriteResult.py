# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from pathlib import Path as FilePath
from typing import Mapping as TypeMap

from interchange import Capability
from interchange import Diagnostic
from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.ContractCompat import ContractBase
from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.TransferContract import CarrierReason
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WriteValidate import CheckDropped
from convert.adapters.base.WriteValidate import CheckNeeds
from convert.adapters.base.WriteValidate import CheckTransfers
from convert.adapters.base.WriteValidate import CheckUsability
from convert.adapters.base.WriteValidate import GetCarrierCaps
from convert.adapters.base.WriteValidate import GetNativeCaps


# writer outcomes centralize transactional output and preservation evidence for callers
@DataClass(frozen=True, slots=True)
class WriteResult(ContractBase):
    path: FilePath | None
    adapter: str
    bytes_written: int
    diagnostics: tuple[Diagnostic, ...] = ()
    metadata: TypeMap[str, object] = DataField(default_factory=FreezeMapping)
    transfers: tuple[CapTransfer, ...] = ()
    dropped: frozenset[Capability] = frozenset()
    requirements: tuple[str, ...] = ()
    application_usable: bool = False
    vendor_loadable: bool = False

    # construction rejects contradictory evidence before registry policy can trust it
    def __post_init__(self) -> None:
        if self.bytes_written < 0:
            raise ValueError("bytes written cannot be negative")
        CheckDropped(self.dropped)
        CheckTransfers(self.transfers, self.dropped)
        CheckNeeds(self.requirements)
        CheckUsability(
            self.application_usable,
            self.vendor_loadable,
            self.metadata,
        )

    # callers need one complete preservation view independent from representation mode
    @property
    def TransferCaps(self) -> frozenset[Capability]:
        return frozenset(TransferData.capability for TransferData in self.transfers)

    # roundtrip safety means no source capability was discarded regardless of dependencies
    @property
    def IsRoundtripSafe(self) -> bool:
        return not self.dropped

    # near losslessness requires usable output and only intrinsic target format limitations
    @property
    def IsNearLossless(self) -> bool:
        return (
            self.application_usable
            and self.vendor_loadable
            and not self.requirements
            and not self.dropped
            and all(
                TransferData.carrier_reason is CarrierReason.KTargetGap
                for TransferData in self.transfers
                if TransferData.mode
                in {TransferMode.KCarrier, TransferMode.KMixed}
            )
        )

    # legacy callers need the output path without losing its path type
    @property
    def OutputPath(self) -> FilePath | None:
        return self.path

    # legacy callers need the adapter identity without losing its string type
    @property
    def AdapterName(self) -> str:
        return self.adapter

    # legacy callers need byte accounting without losing its integer type
    @property
    def ByteCount(self) -> int:
        return self.bytes_written

    # legacy callers need diagnostics to retain their public record type
    @property
    def Diagnostics(self) -> tuple[Diagnostic, ...]:
        return self.diagnostics

    # legacy callers need metadata indexing without degrading the mapping to object
    @property
    def MetadataMap(self) -> TypeMap[str, object]:
        return self.metadata

    # legacy callers need transfer iteration to retain capability evidence types
    @property
    def Transfers(self) -> tuple[CapTransfer, ...]:
        return self.transfers

    # legacy callers need dropped capability access as a typed set
    @property
    def DroppedCaps(self) -> frozenset[Capability]:
        return self.dropped

    # legacy callers need output requirements to retain their immutable sequence type
    @property
    def Requirements(self) -> tuple[str, ...]:
        return self.requirements

    # legacy callers need application usability as a statically visible predicate
    @property
    def IsAppUsable(self) -> bool:
        return self.application_usable

    # legacy callers need vendor loadability as a statically visible predicate
    @property
    def IsVendorLoadable(self) -> bool:
        return self.vendor_loadable

    # legacy callers need losslessness policy exposed as a typed predicate
    @property
    def near_lossless(self) -> bool:
        return self.IsNearLossless

    # legacy callers need the full transferred capability set without reflection
    @property
    def transferred_capabilities(self) -> frozenset[Capability]:
        return self.TransferCaps

    # canonical native capability access supports both modern and historical result consumers
    @property
    def NativeCaps(self) -> frozenset[Capability]:
        return GetNativeCaps(self.transfers)

    # canonical carrier capability access keeps reversible preservation evidence directly typed
    @property
    def CarrierCaps(self) -> frozenset[Capability]:
        return GetCarrierCaps(self.transfers)

    # legacy callers need native capability accounting without reflection
    @property
    def native_capabilities(self) -> frozenset[Capability]:
        return self.NativeCaps

    # legacy callers need carrier capability accounting without reflection
    @property
    def carrier_capabilities(self) -> frozenset[Capability]:
        return self.CarrierCaps
