# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass
from enum import StrEnum as StringEnum

from interchange import Capability

from convert.adapters.base.ContractCompat import ContractBase


# capability checks preserve runtime safety when untyped plugins construct transfer records
def GetCapability(FieldValue: object) -> Capability:
    if not isinstance(FieldValue, Capability):
        raise TypeError("transfer capability must be a Capability")
    return FieldValue


# mode checks keep invalid plugin values outside preservation accounting
def GetTransferMode(FieldValue: object) -> TransferMode:
    if not isinstance(FieldValue, TransferMode):
        raise TypeError("transfer mode must be a TransferMode")
    return FieldValue


# carrier reason checks keep degradation evidence within the public enum contract
def GetCarrierCause(FieldValue: object) -> CarrierReason:
    if not isinstance(FieldValue, CarrierReason):
        raise TypeError("carrier reason must be a CarrierReason")
    return FieldValue


# transfer modes distinguish native representation from reversible carrier preservation
class TransferMode(StringEnum):
    KNative = "native"
    KMixed = "mixed"
    KCarrier = "carrier"
    NATIVE = KNative
    MIXED = KMixed
    CARRIER = KCarrier


# carrier reasons preserve truthful degradation reporting across format boundaries
class CarrierReason(StringEnum):
    KTargetGap = "target_unsupported"
    KWriterGap = "writer_unimplemented"
    KSourceOpaque = "source_opaque"
    TARGET_UNSUPPORTED = KTargetGap
    WRITER_UNIMPLEMENTED = KWriterGap
    SOURCE_OPAQUE = KSourceOpaque


# each preserved capability needs explicit native or carrier attribution
@DataClass(frozen=True, slots=True)
class CapTransfer(ContractBase):
    capability: Capability
    mode: TransferMode
    carrier_reason: CarrierReason | None = None

    # invalid combinations are rejected here so every writer result stays truthful
    def __post_init__(self) -> None:
        _ = GetCapability(self.capability)
        ModeValue = GetTransferMode(self.mode)
        if ModeValue is TransferMode.KNative:
            if self.carrier_reason is not None:
                raise ValueError("native transfers cannot have a carrier reason")
            return
        if self.carrier_reason is None:
            object.__setattr__(self, "carrier_reason", CarrierReason.KWriterGap)
        else:
            _ = GetCarrierCause(self.carrier_reason)

    # canonical capability access keeps the preserved evidence directly typed
    @property
    def CapabilityData(self) -> Capability:
        return self.capability

    # canonical representation access keeps the transfer mode directly typed
    @property
    def TransferModeData(self) -> TransferMode:
        return self.mode

    # canonical degradation access keeps the carrier evidence directly typed
    @property
    def CarrierCause(self) -> CarrierReason | None:
        return self.carrier_reason


# public transfer name stays stable because external adapters construct this record directly
CapabilityTransfer = CapTransfer
