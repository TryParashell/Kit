# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange import Capability

from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.TransferContract import CarrierReason
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WriteValidate import GetCarrierCaps
from convert.adapters.base.WriteValidate import GetNativeCaps


# preservation evidence and verdicts stay readable through one typed capability view
class CapabilityView:
    __slots__ = ()

    # callers need one complete preservation view independent from representation mode
    @property
    def TransferCaps(self) -> frozenset[Capability]:
        Transfers = CastValue(tuple[CapTransfer, ...], getattr(self, "transfers"))
        return frozenset(TransferData.capability for TransferData in Transfers)

    # canonical native capability access supports both modern and historical result consumers
    @property
    def NativeCaps(self) -> frozenset[Capability]:
        Transfers = CastValue(tuple[CapTransfer, ...], getattr(self, "transfers"))
        return GetNativeCaps(Transfers)

    # canonical carrier capability access keeps reversible preservation evidence directly typed
    @property
    def CarrierCaps(self) -> frozenset[Capability]:
        Transfers = CastValue(tuple[CapTransfer, ...], getattr(self, "transfers"))
        return GetCarrierCaps(Transfers)

    # roundtrip safety means no source capability was discarded regardless of dependencies
    @property
    def IsRoundtripSafe(self) -> bool:
        return not getattr(self, "dropped")

    # near losslessness requires usable output and only intrinsic target format limitations
    @property
    def IsNearLossless(self) -> bool:
        ApplicationUsable = CastValue(bool, getattr(self, "application_usable"))
        VendorLoadable = CastValue(bool, getattr(self, "vendor_loadable"))
        Requirements = CastValue(tuple[str, ...], getattr(self, "requirements"))
        Dropped = CastValue(frozenset[Capability], getattr(self, "dropped"))
        Transfers = CastValue(tuple[CapTransfer, ...], getattr(self, "transfers"))
        return (
            ApplicationUsable
            and VendorLoadable
            and not Requirements
            and not Dropped
            and all(
                TransferData.carrier_reason is CarrierReason.KTargetGap
                for TransferData in Transfers
                if TransferData.mode in {TransferMode.KCarrier, TransferMode.KMixed}
            )
        )
