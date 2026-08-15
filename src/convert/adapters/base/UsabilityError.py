# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from inspect import Parameter as SigParam
from inspect import Signature as CallSignature
from typing import Any as AnyValue

from interchange import Capability
from interchange import frozen_mapping as FreezeMapping

from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.base.TransferContract import CarrierReason
from convert.adapters.base.WriteResult import WriteResult


# issue collection stays focused because structured usability failures serve api consumers directly
def GetIssues(ResultData: WriteResult) -> tuple[str, ...]:
    IssueList: list[str] = []
    if not ResultData.IsAppUsable:
        IssueList.append("application_unusable")
    if not ResultData.IsVendorLoadable:
        IssueList.append("vendor_unloadable")
    if ResultData.Requirements:
        IssueList.append("external_requirements")
    if ResultData.DroppedCaps:
        IssueList.append("capability_loss")
    if ResultData.Transfers and not ResultData.NativeCaps:
        IssueList.append("carrier_only")
    if GetReasonCaps(ResultData, CarrierReason.KWriterGap):
        IssueList.append("unimplemented_translation")
    if GetReasonCaps(ResultData, CarrierReason.KSourceOpaque):
        IssueList.append("opaque_source_data")
    return tuple(IssueList)


# reason filtering supports structured diagnostics without duplicating transfer scans
def GetReasonCaps(
    ResultData: WriteResult, ReasonData: CarrierReason
) -> frozenset[Capability]:
    return frozenset(
        TransferData.CapabilityData
        for TransferData in ResultData.Transfers
        if TransferData.CarrierCause is ReasonData
    )


# legacy constructor aliases need one strict translation point before structured collection begins
def GetErrorArgs(
    FormatId: str | None,
    ResultData: WriteResult | None,
    NamedValues: dict[str, AnyValue],
) -> tuple[str, WriteResult]:
    AllowedNames = {"format_id", "result"}
    UnknownNames = tuple(
        NameText for NameText in NamedValues if NameText not in AllowedNames
    )
    if UnknownNames:
        raise TypeError(
            "ApplicationUsabilityError() got an unexpected keyword argument "
            f"{UnknownNames[0]!r}"
        )
    if FormatId is not None and "format_id" in NamedValues:
        raise TypeError(
            "ApplicationUsabilityError() got multiple values for 'format_id'"
        )
    if ResultData is not None and "result" in NamedValues:
        raise TypeError("ApplicationUsabilityError() got multiple values for 'result'")
    FormatId = NamedValues.get("format_id", FormatId)
    ResultData = NamedValues.get("result", ResultData)
    if FormatId is None:
        raise TypeError(
            "ApplicationUsabilityError() missing required argument 'format_id'"
        )
    if ResultData is None:
        raise TypeError(
            "ApplicationUsabilityError() missing required argument 'result'"
        )
    if not isinstance(FormatId, str):
        raise TypeError("format id must be a string")
    if not isinstance(ResultData, WriteResult):
        raise TypeError("result must be WriteResult")
    return FormatId, ResultData


# usability failures expose every gate reason so callers never parse message text
class UsabilityError(RegistryError):
    locals()["__slots__"] = (
        "AppUsable",
        "CarrierCaps",
        "CarrierReasons",
        "ErrorCode",
        "DroppedCaps",
        "FormatId",
        "IssueValues",
        "Requirements",
        "OpaqueCaps",
        "MissingCaps",
        "VendorLoadable",
    )

    # structured evidence preserves every historical error field and message
    def __init__(
        SelfValue,
        FormatId: str | None = None,
        ResultData: WriteResult | None = None,
        **NamedValues: AnyValue,
    ) -> None:
        FormatId, ResultData = GetErrorArgs(FormatId, ResultData, NamedValues)
        SelfValue.ErrorCode = "output_not_application_usable"
        SelfValue.FormatId = FormatId
        SelfValue.IssueValues = GetIssues(ResultData)
        SelfValue.AppUsable = ResultData.IsAppUsable
        SelfValue.VendorLoadable = ResultData.IsVendorLoadable
        SelfValue.Requirements = ResultData.Requirements
        SelfValue.DroppedCaps = ResultData.DroppedCaps
        SelfValue.CarrierCaps = ResultData.CarrierCaps
        SelfValue.CarrierReasons = FreezeMapping(
            {
                TransferData.CapabilityData: TransferData.CarrierCause
                for TransferData in ResultData.Transfers
                if TransferData.CarrierCause is not None
            }
        )
        SelfValue.MissingCaps = GetReasonCaps(ResultData, CarrierReason.KWriterGap)
        SelfValue.OpaqueCaps = GetReasonCaps(ResultData, CarrierReason.KSourceOpaque)
        DetailText = ", ".join(SelfValue.IssueValues) or "unverified_output"
        super().__init__(
            f"{FormatId} output failed application usability: {DetailText}"
        )

    # legacy attributes remain readable because error fields are established public behavior
    def __getattr__(SelfValue, FieldName: str) -> AnyValue:
        AliasMap = {
            "application_usable": "AppUsable",
            "carrier_capabilities": "CarrierCaps",
            "carrier_reasons": "CarrierReasons",
            "code": "ErrorCode",
            "dropped": "DroppedCaps",
            "format_id": "FormatId",
            "issues": "IssueValues",
            "requirements": "Requirements",
            "source_opaque_capabilities": "OpaqueCaps",
            "unimplemented_capabilities": "MissingCaps",
            "vendor_loadable": "VendorLoadable",
        }
        if FieldName in AliasMap:
            return object.__getattribute__(SelfValue, AliasMap[FieldName])
        raise AttributeError(FieldName)

    # dictionary output remains wire compatible for api error serialization
    def ToMapping(SelfValue) -> dict[str, object]:
        return BuildErrorMap(SelfValue)


# deterministic sorting keeps the legacy error payload byte stable across executions
def SortCaps(CapValues: frozenset[Capability]) -> tuple[str, ...]:
    return tuple(sorted(CapabilityData.value for CapabilityData in CapValues))


# payload construction stays independent because error representation changes separately from collection
def BuildErrorMap(ErrorData: UsabilityError) -> dict[str, object]:
    ReasonMap = {
        CapabilityData.value: ReasonData.value
        for CapabilityData, ReasonData in sorted(
            ErrorData.CarrierReasons.items(),
            key=GetReasonKey,
        )
    }
    return {
        "code": ErrorData.ErrorCode,
        "format_id": ErrorData.FormatId,
        "issues": ErrorData.IssueValues,
        "application_usable": ErrorData.AppUsable,
        "vendor_loadable": ErrorData.VendorLoadable,
        "requirements": ErrorData.Requirements,
        "dropped": SortCaps(ErrorData.DroppedCaps),
        "carrier_capabilities": SortCaps(ErrorData.CarrierCaps),
        "carrier_reasons": ReasonMap,
        "unimplemented_capabilities": SortCaps(ErrorData.MissingCaps),
        "source_opaque_capabilities": SortCaps(ErrorData.OpaqueCaps),
    }


# carrier reason ordering follows capability wire values for deterministic dictionaries
def GetReasonKey(ItemData: tuple[Capability, CarrierReason]) -> str:
    return ItemData[0].value


setattr(UsabilityError, "to_dict", UsabilityError.ToMapping)


# public usability exception name remains stable because api consumers import it directly
globals()["ApplicationUsabilityError"] = UsabilityError

setattr(
    UsabilityError,
    "__signature__",
    CallSignature(
        (
            SigParam(
                "format_id",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="str",
            ),
            SigParam(
                "result",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="WriteResult",
            ),
        ),
        return_annotation="None",
    ),
)
