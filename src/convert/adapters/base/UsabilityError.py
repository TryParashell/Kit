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
from types import MappingProxyType
from typing import Mapping as TypeMap
from typing import TypedDict

from interchange import Capability

from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.base.TransferContract import CarrierReason
from convert.adapters.base.WriteResult import WriteResult
from convert.adapters.base.WriteValidate import GetCarrierCaps


# structured payload typing keeps compatibility fields useful without weakening dictionary values
class ErrorPayload(TypedDict):
    code: str
    format_id: str
    issues: tuple[str, ...]
    application_usable: bool
    vendor_loadable: bool
    requirements: tuple[str, ...]
    dropped: tuple[str, ...]
    carrier_capabilities: tuple[str, ...]
    carrier_reasons: dict[str, str]
    unimplemented_capabilities: tuple[str, ...]
    source_opaque_capabilities: tuple[str, ...]


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
    FormatId: object,
    ResultData: object,
    NamedValues: dict[str, object],
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
    AppUsable: bool
    CarrierCaps: frozenset[Capability]
    CarrierReasons: TypeMap[Capability, CarrierReason]
    ErrorCode: str
    DroppedCaps: frozenset[Capability]
    FormatId: str
    IssueValues: tuple[str, ...]
    Requirements: tuple[str, ...]
    OpaqueCaps: frozenset[Capability]
    MissingCaps: frozenset[Capability]
    VendorLoadable: bool
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
        self,
        FormatId: str | None = None,
        ResultData: WriteResult | None = None,
        **NamedValues: object,
    ) -> None:
        FormatId, ResultData = GetErrorArgs(FormatId, ResultData, NamedValues)
        self.ErrorCode = "output_not_application_usable"
        self.FormatId = FormatId
        self.IssueValues = GetIssues(ResultData)
        self.AppUsable = ResultData.IsAppUsable
        self.VendorLoadable = ResultData.IsVendorLoadable
        self.Requirements = ResultData.Requirements
        self.DroppedCaps = ResultData.DroppedCaps
        self.CarrierCaps = GetCarrierCaps(ResultData.Transfers)
        self.CarrierReasons = MappingProxyType(
            {
                TransferData.CapabilityData: TransferData.CarrierCause
                for TransferData in ResultData.Transfers
                if TransferData.CarrierCause is not None
            }
        )
        self.MissingCaps = GetReasonCaps(ResultData, CarrierReason.KWriterGap)
        self.OpaqueCaps = GetReasonCaps(ResultData, CarrierReason.KSourceOpaque)
        DetailText = ", ".join(self.IssueValues) or "unverified_output"
        super().__init__(
            f"{FormatId} output failed application usability: {DetailText}"
        )

    # historical usability access remains typed because api consumers inspect this public error field
    @property
    def application_usable(self) -> bool:
        return self.AppUsable

    # historical carrier access remains typed because api consumers inspect this public error field
    @property
    def carrier_capabilities(self) -> frozenset[Capability]:
        return self.CarrierCaps

    # historical reason access remains typed because api consumers inspect this public error field
    @property
    def carrier_reasons(self) -> TypeMap[Capability, CarrierReason]:
        return self.CarrierReasons

    # historical code access remains typed because api consumers dispatch on this public error field
    @property
    def code(self) -> str:
        return self.ErrorCode

    # historical loss access remains typed because api consumers inspect this public error field
    @property
    def dropped(self) -> frozenset[Capability]:
        return self.DroppedCaps

    # historical format access remains typed because api consumers inspect this public error field
    @property
    def format_id(self) -> str:
        return self.FormatId

    # historical issue access remains typed because api consumers inspect this public error field
    @property
    def issues(self) -> tuple[str, ...]:
        return self.IssueValues

    # historical requirement access remains typed because api consumers inspect this public error field
    @property
    def requirements(self) -> tuple[str, ...]:
        return self.Requirements

    # historical opaque capability access remains typed because api consumers inspect this public error field
    @property
    def source_opaque_capabilities(self) -> frozenset[Capability]:
        return self.OpaqueCaps

    # historical missing capability access remains typed because api consumers inspect this public error field
    @property
    def unimplemented_capabilities(self) -> frozenset[Capability]:
        return self.MissingCaps

    # historical vendor access remains typed because api consumers inspect this public error field
    @property
    def vendor_loadable(self) -> bool:
        return self.VendorLoadable

    # historical mapping method remains typed because api consumers serialize this public error contract
    def to_dict(self) -> ErrorPayload:
        return BuildErrorMap(self)

    # legacy attributes remain readable because error fields are established public behavior
    def __getattr__(self, FieldName: str) -> object:
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
            ResultValue: object = object.__getattribute__(self, AliasMap[FieldName])
            return ResultValue
        raise AttributeError(FieldName)

    # dictionary output remains wire compatible for api error serialization
    def ToMapping(self) -> ErrorPayload:
        return BuildErrorMap(self)


# deterministic sorting keeps the legacy error payload byte stable across executions
def SortCaps(CapValues: frozenset[Capability]) -> tuple[str, ...]:
    return tuple(sorted(CapabilityData.value for CapabilityData in CapValues))


# payload construction stays independent because error representation changes separately from collection
def BuildErrorMap(ErrorData: UsabilityError) -> ErrorPayload:
    ReasonMap: dict[str, str] = {
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


# public usability exception name remains stable because api consumers import it directly
ApplicationUsabilityError = UsabilityError

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
