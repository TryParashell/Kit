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


# transfer modes distinguish native representation from reversible carrier preservation
class TransferMode(StringEnum):
    KNative = "native"
    KMixed = "mixed"
    KCarrier = "carrier"


for LegacyName, MemberName in {
    "NATIVE": "KNative",
    "MIXED": "KMixed",
    "CARRIER": "KCarrier",
}.items():
    setattr(TransferMode, LegacyName, getattr(TransferMode, MemberName))


# carrier reasons preserve truthful degradation reporting across format boundaries
class CarrierReason(StringEnum):
    KTargetGap = "target_unsupported"
    KWriterGap = "writer_unimplemented"
    KSourceOpaque = "source_opaque"


for LegacyName, MemberName in {
    "TARGET_UNSUPPORTED": "KTargetGap",
    "WRITER_UNIMPLEMENTED": "KWriterGap",
    "SOURCE_OPAQUE": "KSourceOpaque",
}.items():
    setattr(CarrierReason, LegacyName, getattr(CarrierReason, MemberName))


# each preserved capability needs explicit native or carrier attribution
@DataClass(frozen=True, slots=True)
class CapTransfer(ContractBase):
    CapabilityData: Capability
    TransferModeData: TransferMode
    CarrierCause: CarrierReason | None = None

    # invalid combinations are rejected here so every writer result stays truthful
    def __post_init__(SelfValue) -> None:
        if not isinstance(SelfValue.CapabilityData, Capability):
            raise TypeError("transfer capability must be a Capability")
        if not isinstance(SelfValue.TransferModeData, TransferMode):
            raise TypeError("transfer mode must be a TransferMode")
        if SelfValue.TransferModeData is TransferMode.KNative:
            if SelfValue.CarrierCause is not None:
                raise ValueError("native transfers cannot have a carrier reason")
            return
        if SelfValue.CarrierCause is None:
            object.__setattr__(SelfValue, "CarrierCause", CarrierReason.KWriterGap)
        elif not isinstance(SelfValue.CarrierCause, CarrierReason):
            raise TypeError("carrier reason must be a CarrierReason")


# public transfer name stays stable because external adapters construct this record directly
globals()["CapabilityTransfer"] = CapTransfer
