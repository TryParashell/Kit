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
from typing import TYPE_CHECKING as IsTypeCheck
from typing import overload as Overload

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
    CapabilityData: Capability
    TransferModeData: TransferMode
    CarrierCause: CarrierReason | None = None

    if IsTypeCheck:

        # historical keywords remain typed because writer plugins construct this public evidence record
        @Overload
        def __init__(
            self,
            capability: Capability,
            mode: TransferMode,
            carrier_reason: CarrierReason | None = None,
        ) -> None: ...

        # canonical keywords remain typed because dataclass replacement reconstructs evidence from storage fields
        @Overload
        def __init__(
            self,
            CapabilityData: Capability,
            TransferModeData: TransferMode,
            CarrierCause: CarrierReason | None = None,
        ) -> None: ...

        # broad implementation parameters exist only to connect both statically checked constructor forms
        def __init__(self, *ArgValues: object, **NamedValues: object) -> None: ...

    # invalid combinations are rejected here so every writer result stays truthful
    def __post_init__(self) -> None:
        GetCapability(self.CapabilityData)
        ModeValue = GetTransferMode(self.TransferModeData)
        if ModeValue is TransferMode.KNative:
            if self.CarrierCause is not None:
                raise ValueError("native transfers cannot have a carrier reason")
            return
        if self.CarrierCause is None:
            object.__setattr__(self, "CarrierCause", CarrierReason.KWriterGap)
        else:
            GetCarrierCause(self.CarrierCause)

    # legacy callers need statically typed access to the preserved capability
    @property
    def capability(self) -> Capability:
        return self.CapabilityData

    # legacy callers need statically typed access to the representation mode
    @property
    def mode(self) -> TransferMode:
        return self.TransferModeData

    # legacy callers need statically typed access to degradation evidence
    @property
    def carrier_reason(self) -> CarrierReason | None:
        return self.CarrierCause


# public transfer name stays stable because external adapters construct this record directly
CapabilityTransfer = CapTransfer
