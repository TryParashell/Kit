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
from typing import TYPE_CHECKING as IsTypeCheck
from typing import overload as Overload

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
    OutputPath: FilePath | None
    AdapterName: str
    ByteCount: int
    Diagnostics: tuple[Diagnostic, ...] = ()
    MetadataMap: TypeMap[str, object] = DataField(default_factory=FreezeMapping)
    Transfers: tuple[CapTransfer, ...] = ()
    DroppedCaps: frozenset[Capability] = frozenset()
    Requirements: tuple[str, ...] = ()
    IsAppUsable: bool = False
    IsVendorLoadable: bool = False

    if IsTypeCheck:

        # historical keywords remain typed because writer plugins construct this public result directly
        @Overload
        def __init__(
            self,
            path: FilePath | None,
            adapter: str,
            bytes_written: int,
            diagnostics: tuple[Diagnostic, ...] = (),
            metadata: TypeMap[str, object] = FreezeMapping(),
            transfers: tuple[CapTransfer, ...] = (),
            dropped: frozenset[Capability] = frozenset(),
            requirements: tuple[str, ...] = (),
            application_usable: bool = False,
            vendor_loadable: bool = False,
        ) -> None: ...  # lgtm[py/ineffectual-statement]

        # canonical keywords remain typed because dataclass replacement reconstructs results from storage fields
        @Overload
        def __init__(
            self,
            OutputPath: FilePath | None,
            AdapterName: str,
            ByteCount: int,
            Diagnostics: tuple[Diagnostic, ...] = (),
            MetadataMap: TypeMap[str, object] = FreezeMapping(),
            Transfers: tuple[CapTransfer, ...] = (),
            DroppedCaps: frozenset[Capability] = frozenset(),
            Requirements: tuple[str, ...] = (),
            IsAppUsable: bool = False,
            IsVendorLoadable: bool = False,
        ) -> None: ...  # lgtm[py/ineffectual-statement]

        # broad implementation parameters exist only to connect both statically checked constructor forms
        def __init__(self, *ArgValues: object, **NamedValues: object) -> None: ...  # lgtm[py/ineffectual-statement]

    # historical path access remains typed because staging consumers inspect this public field
    @property
    def path(self) -> FilePath | None:
        return self.OutputPath

    # historical byte count access remains typed because conversion reports expose this public field
    @property
    def bytes_written(self) -> int:
        return self.ByteCount

    # historical dropped capability access remains typed because api consumers inspect this public field
    @property
    def dropped(self) -> frozenset[Capability]:
        return self.DroppedCaps

    # historical roundtrip access remains typed because api consumers inspect this preservation claim
    @property
    def roundtrip_safe(self) -> bool:
        return self.IsRoundtripSafe

    # construction rejects contradictory evidence before registry policy can trust it
    def __post_init__(self) -> None:
        if self.ByteCount < 0:
            raise ValueError("bytes written cannot be negative")
        CheckDropped(self.DroppedCaps)
        CheckTransfers(self.Transfers, self.DroppedCaps)
        CheckNeeds(self.Requirements)
        CheckUsability(
            self.IsAppUsable,
            self.IsVendorLoadable,
            self.MetadataMap,
        )

    # callers need one complete preservation view independent from representation mode
    @property
    def TransferCaps(self) -> frozenset[Capability]:
        return frozenset(TransferData.CapabilityData for TransferData in self.Transfers)

    # roundtrip safety means no source capability was discarded regardless of dependencies
    @property
    def IsRoundtripSafe(self) -> bool:
        return not self.DroppedCaps

    # near losslessness requires usable output and only intrinsic target format limitations
    @property
    def IsNearLossless(self) -> bool:
        return (
            self.IsAppUsable
            and self.IsVendorLoadable
            and not self.Requirements
            and not self.DroppedCaps
            and all(
                TransferData.CarrierCause is CarrierReason.KTargetGap
                for TransferData in self.Transfers
                if TransferData.TransferModeData
                in {TransferMode.KCarrier, TransferMode.KMixed}
            )
        )

    # legacy callers need the adapter identity without losing its string type
    @property
    def adapter(self) -> str:
        return self.AdapterName

    # legacy callers need diagnostics to retain their public record type
    @property
    def diagnostics(self) -> tuple[Diagnostic, ...]:
        return self.Diagnostics

    # legacy callers need metadata indexing without degrading the mapping to object
    @property
    def metadata(self) -> TypeMap[str, object]:
        return self.MetadataMap

    # legacy callers need transfer iteration to retain capability evidence types
    @property
    def transfers(self) -> tuple[CapTransfer, ...]:
        return self.Transfers

    # legacy callers need output requirements to retain their immutable sequence type
    @property
    def requirements(self) -> tuple[str, ...]:
        return self.Requirements

    # legacy callers need application usability as a statically visible predicate
    @property
    def application_usable(self) -> bool:
        return self.IsAppUsable

    # legacy callers need vendor loadability as a statically visible predicate
    @property
    def vendor_loadable(self) -> bool:
        return self.IsVendorLoadable

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
        return GetNativeCaps(self.Transfers)

    # canonical carrier capability access keeps reversible preservation evidence directly typed
    @property
    def CarrierCaps(self) -> frozenset[Capability]:
        return GetCarrierCaps(self.Transfers)

    # legacy callers need native capability accounting without reflection
    @property
    def native_capabilities(self) -> frozenset[Capability]:
        return self.NativeCaps

    # legacy callers need carrier capability accounting without reflection
    @property
    def carrier_capabilities(self) -> frozenset[Capability]:
        return self.CarrierCaps
