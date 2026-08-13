# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath

from interchange import CadDocument

from .adapter_protocols import CadReaderAdapter
from .contract_types import KSourceType
from .read_options import ReadOptions
from .registry_select import SelectReader
from .source_replay import GetReplayMut

# historical source annotations need local resolution after public methods move to the registry facade
globals()["Source"] = KSourceType


# historical read keywords stay centralized because callers pass explicit source format and options
def GetReadArgs(
    NamedValues: dict[str, object],
) -> tuple[str | None, ReadOptions | None]:
    AllowedNames = {"format_id", "FormatId", "options", "OptionsData"}
    UnknownNames = tuple(
        NameText for NameText in NamedValues if NameText not in AllowedNames
    )
    if UnknownNames:
        raise TypeError(
            f"read() got an unexpected keyword argument {UnknownNames[0]!r}"
        )
    if "format_id" in NamedValues and "FormatId" in NamedValues:
        raise TypeError("read() got multiple values for 'format_id'")
    if "options" in NamedValues and "OptionsData" in NamedValues:
        raise TypeError("read() got multiple values for 'options'")
    FormatId = NamedValues.get("format_id", NamedValues.get("FormatId"))
    OptionsData = NamedValues.get("options", NamedValues.get("OptionsData"))
    if FormatId is not None and not isinstance(FormatId, str):
        raise TypeError("format id must be a string")
    if OptionsData is not None and not isinstance(OptionsData, ReadOptions):
        raise TypeError("options must be ReadOptions")
    return FormatId, OptionsData


# reader selection remains separate because probing and lookup change independently from reading
class ReadSelectApi:

    # probing delegates to a focused selector while retaining the established registry method
    def PickReader(SelfValue, SourceData: KSourceType) -> CadReaderAdapter:
        return SelectReader(SelfValue.GetReaders(), SourceData)


# document reading owns replayable stream handling and post read validation
class ReadApi:

    # convenience reading returns only the document while preserving adapter aware behavior
    def ReadDocument(
        SelfValue,
        SourceData: KSourceType,
        **NamedValues: object,
    ) -> CadDocument:
        DocumentData, AdapterData = SelfValue.ReadAdapter(SourceData, **NamedValues)
        return DocumentData

    # replayable inputs ensure probing never consumes one shot sources before reading
    def ReadAdapter(
        SelfValue,
        SourceData: KSourceType,
        **NamedValues: object,
    ) -> tuple[CadDocument, CadReaderAdapter]:
        FormatId, OptionsData = GetReadArgs(NamedValues)
        ReplaySource = GetReplayMut(SourceData)
        StreamPos = 0
        if not isinstance(ReplaySource, (str, FilePath, bytes, bytearray)):
            StreamPos = ReplaySource.tell()
        AdapterData = (
            SelfValue.GetReader(FormatId)
            if FormatId
            else SelfValue.PickReader(ReplaySource)
        )
        if not isinstance(ReplaySource, (str, FilePath, bytes, bytearray)):
            ReplaySource.seek(StreamPos)
        DocumentData = AdapterData.read(ReplaySource, OptionsData)
        DocumentData.assert_valid()
        return DocumentData, AdapterData
