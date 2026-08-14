# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace as ReplaceValue
from pathlib import Path as FilePath

from interchange import CadDocument

from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.staging.PathStaging import WritePathStaged
from convert.adapters.registry.RegistryErrors import CapLossError
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.registry.RegistrySelect import SelectWriter
from convert.adapters.staging.StreamStaging import WriteStreamMut
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.base.WritePolicy import GetWriteOptions
from convert.adapters.base.WriteResult import WriteResult

# historical destination annotations need local resolution after public methods move to the registry facade
globals()["Destination"] = KTargetType


# historical write keywords stay centralized because callers pass explicit target format and options
def GetWriteArgs(
    NamedValues: dict[str, object],
) -> tuple[str | None, WriteOptions | None]:
    AllowedNames = {"format_id", "FormatId", "options", "OptionsData"}
    UnknownNames = tuple(
        NameText for NameText in NamedValues if NameText not in AllowedNames
    )
    if UnknownNames:
        raise TypeError(
            f"write() got an unexpected keyword argument {UnknownNames[0]!r}"
        )
    if "format_id" in NamedValues and "FormatId" in NamedValues:
        raise TypeError("write() got multiple values for 'format_id'")
    if "options" in NamedValues and "OptionsData" in NamedValues:
        raise TypeError("write() got multiple values for 'options'")
    FormatId = NamedValues.get("format_id", NamedValues.get("FormatId"))
    OptionsData = NamedValues.get("options", NamedValues.get("OptionsData"))
    if FormatId is not None and not isinstance(FormatId, str):
        raise TypeError("format id must be a string")
    if OptionsData is not None and not isinstance(OptionsData, WriteOptions):
        raise TypeError("options must be WriteOptions")
    return FormatId, OptionsData


# writer selection remains separate because destination matching changes independently from staging
class WriteSelectApi:

    # destination matching delegates to a focused selector while retaining registry ownership
    def PickWriter(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: KTargetType,
    ) -> CadWriterAdapter:
        return SelectWriter(SelfValue.GetWriters(), DocumentData, TargetData)


# write orchestration owns validation policy before transactional output staging
class WriteApi:

    # complete orchestration prevents unsupported capabilities from mutating any destination
    def WriteDocument(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: KTargetType,
        **NamedValues: object,
    ) -> WriteResult:
        FormatId, OptionsData = GetWriteArgs(NamedValues)
        AdapterData = (
            SelfValue.GetWriter(FormatId)
            if FormatId
            else SelfValue.PickWriter(DocumentData, TargetData)
        )
        SelectedOpts = OptionsData or WriteOptions()
        if FormatId is not None:
            SelectedOpts = ReplaceValue(SelectedOpts, TargetFormat=FormatId)
        SelectedOpts, AllowCarrier, NeedSelfContained = GetWriteOptions(SelectedOpts)
        if not AdapterData.supports(DocumentData, TargetData):
            raise NotFoundError(
                f"{AdapterData.info.format_id} does not support the destination"
            )
        if SelectedOpts.Validate:
            DocumentData.assert_valid()
        UnsupportedCaps = GetDocumentCaps(DocumentData) - AdapterData.info.capabilities
        if UnsupportedCaps:
            raise CapLossError(AdapterData.info.format_id, UnsupportedCaps)
        if isinstance(TargetData, (str, FilePath)):
            return WritePathStaged(
                DocumentData,
                AdapterData,
                TargetData,
                SelectedOpts,
                AllowCarrier,
                NeedSelfContained,
            )
        return WriteStreamMut(
            DocumentData,
            AdapterData,
            TargetData,
            SelectedOpts,
            AllowCarrier,
            NeedSelfContained,
        )
