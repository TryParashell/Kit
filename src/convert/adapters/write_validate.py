# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Mapping as TypeMap

from interchange import Capability

from .transfer_contract import CapTransfer
from .transfer_contract import TransferMode


# transfer validation prevents duplicate or contradictory preservation claims from escaping writers
def CheckTransfers(
    TransferValues: tuple[CapTransfer, ...], DroppedCaps: frozenset[Capability]
) -> None:
    if not isinstance(TransferValues, tuple) or any(
        not isinstance(TransferData, CapTransfer) for TransferData in TransferValues
    ):
        raise TypeError("transfers must be CapabilityTransfer values")
    CapabilityValues = tuple(
        TransferData.CapabilityData for TransferData in TransferValues
    )
    if len(CapabilityValues) != len(set(CapabilityValues)):
        raise ValueError("transfer capabilities must be unique")
    if set(CapabilityValues) & DroppedCaps:
        raise ValueError("transferred capabilities cannot also be dropped")


# dropped capability validation keeps loss reporting limited to known enum values
def CheckDropped(DroppedCaps: frozenset[Capability]) -> None:
    if not isinstance(DroppedCaps, frozenset) or any(
        not isinstance(CapabilityData, Capability) for CapabilityData in DroppedCaps
    ):
        raise TypeError("dropped capabilities must be Capability values")


# requirement validation keeps application dependencies precise and deterministic
def CheckNeeds(RequirementValues: tuple[str, ...]) -> None:
    if not isinstance(RequirementValues, tuple) or any(
        not isinstance(RequirementText, str)
        or not RequirementText.strip()
        or RequirementText != RequirementText.strip()
        for RequirementText in RequirementValues
    ):
        raise TypeError("requirements must be non-empty strings")
    if len(set(RequirementValues)) != len(RequirementValues):
        raise ValueError("requirements must be unique")


# usability validation prevents logically impossible output claims from escaping writers
def CheckUsability(
    IsAppUsable: bool,
    IsVendorLoadable: bool,
    MetadataMap: TypeMap[str, object],
) -> None:
    if not isinstance(IsAppUsable, bool):
        raise TypeError("application usable must be a boolean")
    if not isinstance(IsVendorLoadable, bool):
        raise TypeError("vendor loadable must be a boolean")
    if IsAppUsable and not IsVendorLoadable:
        raise ValueError("application-usable output must be vendor-loadable")
    ExpectedMap = {
        "application_usable": IsAppUsable,
        "vendor_loadable": IsVendorLoadable,
    }
    for FieldName, ExpectedValue in ExpectedMap.items():
        if FieldName not in MetadataMap:
            continue
        FieldValue = MetadataMap[FieldName]
        if not isinstance(FieldValue, bool):
            raise TypeError(f"metadata {FieldName} must be a boolean")
        if FieldValue is not ExpectedValue:
            raise ValueError(f"metadata {FieldName} contradicts the write result")


# native view includes mixed transfers because both contain target format representation
def GetNativeCaps(TransferValues: tuple[CapTransfer, ...]) -> frozenset[Capability]:
    return frozenset(
        TransferData.CapabilityData
        for TransferData in TransferValues
        if TransferData.TransferModeData in {TransferMode.KNative, TransferMode.KMixed}
    )


# carrier view includes mixed transfers because both retain reversible auxiliary semantics
def GetCarrierCaps(TransferValues: tuple[CapTransfer, ...]) -> frozenset[Capability]:
    return frozenset(
        TransferData.CapabilityData
        for TransferData in TransferValues
        if TransferData.TransferModeData in {TransferMode.KCarrier, TransferMode.KMixed}
    )
