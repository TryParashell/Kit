# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from collections.abc import Mapping as RuntimeMap
from typing import Mapping as TypeMap
from typing import TypeGuard

from interchange import Capability

from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.TransferContract import TransferMode


# tuple narrowing keeps untyped constructor values inspectable without unknown members
def IsObjectTuple(FieldValue: object) -> TypeGuard[tuple[object, ...]]:
    return isinstance(FieldValue, tuple)


# frozen set narrowing preserves immutable capability validation across runtime boundaries
def IsObjectSet(FieldValue: object) -> TypeGuard[frozenset[object]]:
    return isinstance(FieldValue, frozenset)


# mapping narrowing permits metadata checks without accepting unknown key or value contracts
def IsObjectMap(FieldValue: object) -> TypeGuard[RuntimeMap[object, object]]:
    return isinstance(FieldValue, RuntimeMap)


# transfer collection parsing gives later validation one fully typed sequence
def GetTransfers(TransferValues: object) -> tuple[CapTransfer, ...]:
    if not IsObjectTuple(TransferValues):
        raise TypeError("transfers must be CapabilityTransfer values")
    CheckedValues: list[CapTransfer] = []
    for TransferData in TransferValues:
        if not isinstance(TransferData, CapTransfer):
            raise TypeError("transfers must be CapabilityTransfer values")
        CheckedValues.append(TransferData)
    return tuple(CheckedValues)


# dropped capability parsing gives overlap checks a trusted immutable enum set
def GetDropped(DroppedCaps: object) -> frozenset[Capability]:
    if not IsObjectSet(DroppedCaps):
        raise TypeError("dropped capabilities must be Capability values")
    CheckedValues: set[Capability] = set()
    for CapabilityData in DroppedCaps:
        if not isinstance(CapabilityData, Capability):
            raise TypeError("dropped capabilities must be Capability values")
        CheckedValues.add(CapabilityData)
    return frozenset(CheckedValues)


# metadata parsing keeps usability evidence limited to textual field names
def GetMetadata(MetadataMap: object) -> TypeMap[str, object]:
    if not IsObjectMap(MetadataMap):
        raise TypeError("metadata must be a mapping")
    CheckedValues: dict[str, object] = {}
    for FieldName, FieldValue in MetadataMap.items():
        if not isinstance(FieldName, str):
            raise TypeError("metadata field names must be strings")
        CheckedValues[FieldName] = FieldValue
    return CheckedValues


# transfer validation prevents duplicate or contradictory preservation claims from escaping writers
def CheckTransfers(TransferValues: object, DroppedCaps: object) -> None:
    CheckedTransfers = GetTransfers(TransferValues)
    CheckedDropped = GetDropped(DroppedCaps)
    CapabilityValues = tuple(
        TransferData.CapabilityData for TransferData in CheckedTransfers
    )
    if len(CapabilityValues) != len(set(CapabilityValues)):
        raise ValueError("transfer capabilities must be unique")
    if set(CapabilityValues) & CheckedDropped:
        raise ValueError("transferred capabilities cannot also be dropped")


# dropped capability validation keeps loss reporting limited to known enum values
def CheckDropped(DroppedCaps: object) -> None:
    GetDropped(DroppedCaps)


# requirement validation keeps application dependencies precise and deterministic
def CheckNeeds(RequirementValues: object) -> None:
    if not IsObjectTuple(RequirementValues) or any(
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
    IsAppUsable: object,
    IsVendorLoadable: object,
    MetadataMap: object,
) -> None:
    if not isinstance(IsAppUsable, bool):
        raise TypeError("application usable must be a boolean")
    if not isinstance(IsVendorLoadable, bool):
        raise TypeError("vendor loadable must be a boolean")
    if IsAppUsable and not IsVendorLoadable:
        raise ValueError("application-usable output must be vendor-loadable")
    CheckedMetadata = GetMetadata(MetadataMap)
    ExpectedMap = {
        "application_usable": IsAppUsable,
        "vendor_loadable": IsVendorLoadable,
    }
    for FieldName, ExpectedValue in ExpectedMap.items():
        if FieldName not in CheckedMetadata:
            continue
        FieldValue = CheckedMetadata[FieldName]
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
