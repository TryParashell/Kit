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
from typing import Any as AnyValue
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
    OutputPath: FilePath | None
    AdapterName: str
    ByteCount: int
    Diagnostics: tuple[Diagnostic, ...] = ()
    MetadataMap: TypeMap[str, AnyValue] = DataField(default_factory=FreezeMapping)
    Transfers: tuple[CapTransfer, ...] = ()
    DroppedCaps: frozenset[Capability] = frozenset()
    Requirements: tuple[str, ...] = ()
    IsAppUsable: bool = False
    IsVendorLoadable: bool = False

    # construction rejects contradictory evidence before registry policy can trust it
    def __post_init__(SelfValue) -> None:
        if SelfValue.ByteCount < 0:
            raise ValueError("bytes written cannot be negative")
        CheckDropped(SelfValue.DroppedCaps)
        CheckTransfers(SelfValue.Transfers, SelfValue.DroppedCaps)
        CheckNeeds(SelfValue.Requirements)
        CheckUsability(
            SelfValue.IsAppUsable,
            SelfValue.IsVendorLoadable,
            SelfValue.MetadataMap,
        )

    # callers need one complete preservation view independent from representation mode
    @property
    def TransferCaps(SelfValue) -> frozenset[Capability]:
        return frozenset(
            TransferData.CapabilityData for TransferData in SelfValue.Transfers
        )

    # roundtrip safety means no source capability was discarded regardless of dependencies
    @property
    def IsRoundtripSafe(SelfValue) -> bool:
        return not SelfValue.DroppedCaps

    # near losslessness requires usable output and only intrinsic target format limitations
    @property
    def IsNearLossless(SelfValue) -> bool:
        return (
            SelfValue.IsAppUsable
            and SelfValue.IsVendorLoadable
            and not SelfValue.Requirements
            and not SelfValue.DroppedCaps
            and all(
                TransferData.CarrierCause is CarrierReason.KTargetGap
                for TransferData in SelfValue.Transfers
                if TransferData.TransferModeData
                in {TransferMode.KCarrier, TransferMode.KMixed}
            )
        )


for LegacyName, PropertyName in {
    "transferred_capabilities": "TransferCaps",
    "roundtrip_safe": "IsRoundtripSafe",
    "near_lossless": "IsNearLossless",
}.items():
    setattr(WriteResult, LegacyName, getattr(WriteResult, PropertyName))


# native view stays focused because target representation is independently useful
def GetNativeView(SelfValue: WriteResult) -> frozenset[Capability]:
    return GetNativeCaps(SelfValue.Transfers)


# carrier view stays focused because reversible preservation is independently useful
def GetCarrierView(SelfValue: WriteResult) -> frozenset[Capability]:
    return GetCarrierCaps(SelfValue.Transfers)


setattr(WriteResult, "NativeCaps", property(GetNativeView))
setattr(WriteResult, "CarrierCaps", property(GetCarrierView))
setattr(WriteResult, "native_capabilities", getattr(WriteResult, "NativeCaps"))
setattr(WriteResult, "carrier_capabilities", getattr(WriteResult, "CarrierCaps"))
