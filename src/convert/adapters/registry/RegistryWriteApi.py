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
from typing import Protocol

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
Destination = KTargetType


# selection mixins need a concrete writer catalog boundary without depending on registry composition
class WriteCatalog(Protocol):

    # selection requires deterministic access to every registered writer
    def GetWriters(self) -> tuple[CadWriterAdapter, ...]: ...  # lgtm[py/ineffectual-statement]


# write orchestration needs only lookup and destination selection from its composed host
class WriteLookup(Protocol):

    # explicit format requests need canonical writer lookup from the composed registry
    def GetWriter(self, FormatId: str) -> CadWriterAdapter: ...  # lgtm[py/ineffectual-statement]

    # implicit format requests need destination selection from the composed registry
    def PickWriter(
        self,
        DocumentData: CadDocument,
        TargetData: KTargetType,
    ) -> CadWriterAdapter: ...  # lgtm[py/ineffectual-statement]


# historical write keywords stay centralized because callers pass explicit target format and options
def GetWriteArgs(
    NamedValues: dict[str, object],
) -> tuple[str | None, WriteOptions | None]:
    AllowedNames = {
        "format_id",
        "FormatId",
        "options",
        "OptionsData",
        "WriteOpts",
    }
    UnknownNames = tuple(
        NameText for NameText in NamedValues if NameText not in AllowedNames
    )
    if UnknownNames:
        raise TypeError(
            f"write() got an unexpected keyword argument {UnknownNames[0]!r}"
        )
    if "format_id" in NamedValues and "FormatId" in NamedValues:
        raise TypeError("write() got multiple values for 'format_id'")
    OptionNames = {"options", "OptionsData", "WriteOpts"} & NamedValues.keys()
    if len(OptionNames) > 1:
        raise TypeError("write() got multiple values for 'options'")
    FormatId = NamedValues.get("format_id", NamedValues.get("FormatId"))
    OptionsData = NamedValues.get(
        "options",
        NamedValues.get("OptionsData", NamedValues.get("WriteOpts")),
    )
    if FormatId is not None and not isinstance(FormatId, str):
        raise TypeError("format id must be a string")
    if OptionsData is not None and not isinstance(OptionsData, WriteOptions):
        raise TypeError("options must be WriteOptions")
    return FormatId, OptionsData


# writer selection remains separate because destination matching changes independently from staging
class WriteSelectApi(WriteCatalog):

    # destination matching delegates to a focused selector while retaining registry ownership
    def PickWriter(
        self,
        DocumentData: CadDocument,
        TargetData: KTargetType,
    ) -> CadWriterAdapter:
        return SelectWriter(self.GetWriters(), DocumentData, TargetData)


# write orchestration owns validation policy before transactional output staging
class WriteApi(WriteLookup):

    # complete orchestration prevents unsupported capabilities from mutating any destination
    def WriteDocument(
        self,
        DocumentData: CadDocument,
        TargetData: KTargetType,
        **NamedValues: object,
    ) -> WriteResult:
        FormatId, OptionsData = GetWriteArgs(NamedValues)
        AdapterData = (
            self.GetWriter(FormatId)
            if FormatId
            else self.PickWriter(DocumentData, TargetData)
        )
        SelectedOpts = OptionsData or WriteOptions()
        if FormatId is not None:
            SelectedOpts = ReplaceValue(SelectedOpts, TargetFormat=FormatId)
        SelectedOpts, AllowCarrier, NeedSelfContained = GetWriteOptions(SelectedOpts)
        if not AdapterData.supports(DocumentData, TargetData):
            raise NotFoundError(
                f"{AdapterData.info.FormatId} does not support the destination"
            )
        if SelectedOpts.Validate:
            DocumentData.AssertValid()
        UnsupportedCaps = GetDocumentCaps(DocumentData) - AdapterData.info.Capabilities
        if UnsupportedCaps:
            raise CapLossError(AdapterData.info.FormatId, UnsupportedCaps)
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
