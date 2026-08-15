# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace as ReplaceValue

from interchange import CadDocument
from interchange import Capability
from interchange import frozen_mapping as FreezeMapping
from interchange import infer_capabilities as InferCaps

from convert.adapters.base.AdapterInfo import AdapterInfo
from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.registry.RegistryErrors import CapLossError
from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.TransferContract import CarrierReason
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.UsabilityError import UsabilityError
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult


# case folding stays centralized because aliases and format ids share lookup semantics
def GetFormatKey(ValueText: str) -> str:
    return ValueText.casefold()


# result format validation accepts canonical ids and aliases without case sensitivity
def GetFormatKeys(InfoData: AdapterInfo) -> frozenset[str]:
    return frozenset(
        GetFormatKey(ValueText)
        for ValueText in (InfoData.FormatId, *InfoData.AliasNames)
    )


# inferred document capabilities ensure writers account for semantics beyond declared flags
def GetDocumentCaps(DocumentData: CadDocument) -> frozenset[Capability]:
    RoundtripCap = next(
        CapabilityData
        for CapabilityData in Capability
        if CapabilityData.value == "roundtrip_metadata"
    )
    InferredCaps = InferCaps(
        DocumentData,
        roundtrip_metadata=(RoundtripCap in DocumentData.capabilities),
    )
    return DocumentData.capabilities | InferredCaps


# explicit transfer validation ensures writers report every source capability exactly once
def CheckTransfers(
    DocumentData: CadDocument,
    InfoData: AdapterInfo,
    ResultData: WriteResult,
) -> tuple[CapTransfer, ...]:
    CapabilityValues = GetDocumentCaps(DocumentData)
    if ResultData.DroppedCaps:
        raise CapLossError(InfoData.FormatId, ResultData.DroppedCaps)
    if not ResultData.Transfers:
        IsNativeExact = ResultData.MetadataMap.get("compatibility") == "native-exact"
        NativeCaps = (
            CapabilityValues
            if IsNativeExact
            else CapabilityValues & InfoData.NativeCaps
        )
        return tuple(
            CapTransfer(
                CapabilityData,
                (
                    TransferMode.KNative
                    if CapabilityData in NativeCaps
                    else TransferMode.KCarrier
                ),
            )
            for CapabilityData in sorted(
                CapabilityValues,
                key=GetCapValue,
            )
        )
    TransferCaps = frozenset(
        TransferData.CapabilityData for TransferData in ResultData.Transfers
    )
    if TransferCaps != CapabilityValues:
        MissingCaps = CapabilityValues - TransferCaps
        if MissingCaps:
            raise CapLossError(InfoData.FormatId, MissingCaps)
        raise RegistryError(
            f"{InfoData.FormatId} reported capabilities absent from the source"
        )
    return ResultData.Transfers


# capability ordering follows wire values so generated transfer evidence stays deterministic
def GetCapValue(CapData: Capability) -> str:
    return CapData.value


# option policy normalizes carrier flags before writers receive the complete intent
def GetWriteOptions(OptionsData: WriteOptions) -> tuple[WriteOptions, bool, bool]:
    AllowCarrier = OptionsData.OptionValues.get("allow_carrier", False)
    NeedSelfContained = OptionsData.OptionValues.get("require_self_contained", True)
    if not isinstance(AllowCarrier, bool):
        raise TypeError("allow_carrier must be a boolean")
    if not isinstance(NeedSelfContained, bool):
        raise TypeError("require_self_contained must be a boolean")
    OptionValues = dict(OptionsData.OptionValues)
    OptionValues["allow_carrier"] = AllowCarrier
    OptionValues["require_self_contained"] = NeedSelfContained
    OptionValues["allow_non_native"] = True
    return (
        ReplaceValue(OptionsData, OptionValues=FreezeMapping(OptionValues)),
        AllowCarrier,
        NeedSelfContained,
    )


# carrier blockers identify implementation gaps while permitting intrinsic target limitations
def GetBlockers(ResultData: WriteResult) -> tuple[CapTransfer, ...]:
    return tuple(
        TransferData
        for TransferData in ResultData.Transfers
        if TransferData.CarrierCause is not None
        and TransferData.CarrierCause is not CarrierReason.KTargetGap
    )


# false usability claims are normalized because carrier only implementation gaps cannot be vendor output
def NormalizeUsable(ResultData: WriteResult) -> WriteResult:
    BlockerValues = GetBlockers(ResultData)
    IsCarrierOnly = bool(ResultData.Transfers) and not ResultData.NativeCaps
    if not (
        IsCarrierOnly
        and BlockerValues
        and (ResultData.IsAppUsable or ResultData.IsVendorLoadable)
    ):
        return ResultData
    MetadataMap = dict(ResultData.MetadataMap)
    MetadataMap["application_usable"] = False
    MetadataMap["vendor_loadable"] = False
    return ReplaceValue(
        ResultData,
        MetadataMap=FreezeMapping(MetadataMap),
        IsAppUsable=False,
        IsVendorLoadable=False,
    )


# writer outcomes cross plugin boundaries so policy needs one concrete runtime result gate
def GetWriteResult(ResultValue: object) -> WriteResult:
    if not isinstance(ResultValue, WriteResult):
        raise RegistryError("writer returned an invalid write result")
    return ResultValue


# checked writer invocation protects registry policy from malformed adapter outcomes
def RunCheckedMut(
    DocumentData: CadDocument,
    AdapterData: CadWriterAdapter,
    TargetData: KTargetType,
    OptionsData: WriteOptions,
    AllowCarrier: bool,
    NeedSelfContained: bool,
) -> WriteResult:
    ResultData = GetWriteResult(
        AdapterData.write(DocumentData, TargetData, OptionsData)
    )
    if GetFormatKey(ResultData.AdapterName) not in GetFormatKeys(AdapterData.info):
        raise RegistryError(
            f"writer {AdapterData.info.FormatId} returned write format {ResultData.AdapterName}"
        )
    TransferValues = CheckTransfers(DocumentData, AdapterData.info, ResultData)
    CheckedResult = NormalizeUsable(
        ReplaceValue(ResultData, Transfers=TransferValues, DroppedCaps=frozenset())
    )
    if NeedSelfContained and CheckedResult.Requirements:
        raise UsabilityError(AdapterData.info.FormatId, CheckedResult)
    if not AllowCarrier and (
        not CheckedResult.IsAppUsable
        or not CheckedResult.IsVendorLoadable
        or bool(CheckedResult.Requirements)
        or bool(CheckedResult.DroppedCaps)
        or bool(GetBlockers(CheckedResult))
    ):
        raise UsabilityError(AdapterData.info.FormatId, CheckedResult)
    return CheckedResult
