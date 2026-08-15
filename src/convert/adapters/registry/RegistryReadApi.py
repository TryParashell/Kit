# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Protocol

from interchange import CadDocument

from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.registry.RegistrySelect import SelectReader
from convert.adapters.staging.SourceReplay import GetReplayMut
from convert.adapters.staging.SourceReplay import ReplaySource as SeekableSource

# historical source annotations need local resolution after public methods move to the registry facade
Source = KSourceType


# selection mixins need a concrete reader catalog boundary without depending on registry composition
class ReadCatalog(Protocol):

    # selection requires deterministic access to every registered reader
    def GetReaders(self) -> tuple[CadReaderAdapter, ...]: ...


# read orchestration needs only lookup selection and adapter aware reading from its host
class ReadLookup(Protocol):

    # explicit format requests need canonical reader lookup from the composed registry
    def GetReader(self, FormatId: str) -> CadReaderAdapter: ...

    # implicit format requests need probe based selection from the composed registry
    def PickReader(self, SourceData: KSourceType) -> CadReaderAdapter: ...

    # document convenience reads delegate to the adapter aware operation on the same host
    def ReadAdapter(
        self,
        SourceData: KSourceType,
        **NamedValues: object,
    ) -> tuple[CadDocument, CadReaderAdapter]: ...


# historical read keywords stay centralized because callers pass explicit source format and options
def GetReadArgs(
    NamedValues: dict[str, object],
) -> tuple[str | None, ReadOptions | None]:
    AllowedNames = {
        "format_id",
        "FormatId",
        "options",
        "OptionsData",
        "ReadOpts",
    }
    UnknownNames = tuple(
        NameText for NameText in NamedValues if NameText not in AllowedNames
    )
    if UnknownNames:
        raise TypeError(
            f"read() got an unexpected keyword argument {UnknownNames[0]!r}"
        )
    if "format_id" in NamedValues and "FormatId" in NamedValues:
        raise TypeError("read() got multiple values for 'format_id'")
    OptionNames = {"options", "OptionsData", "ReadOpts"} & NamedValues.keys()
    if len(OptionNames) > 1:
        raise TypeError("read() got multiple values for 'options'")
    FormatId = NamedValues.get("format_id", NamedValues.get("FormatId"))
    OptionsData = NamedValues.get(
        "options",
        NamedValues.get("OptionsData", NamedValues.get("ReadOpts")),
    )
    if FormatId is not None and not isinstance(FormatId, str):
        raise TypeError("format id must be a string")
    if OptionsData is not None and not isinstance(OptionsData, ReadOptions):
        raise TypeError("options must be ReadOptions")
    return FormatId, OptionsData


# reader selection remains separate because probing and lookup change independently from reading
class ReadSelectApi(ReadCatalog):

    # probing delegates to a focused selector while retaining the established registry method
    def PickReader(self, SourceData: KSourceType) -> CadReaderAdapter:
        return SelectReader(self.GetReaders(), SourceData)


# document reading owns replayable stream handling and post read validation
class ReadApi(ReadLookup):

    # convenience reading returns only the document while preserving adapter aware behavior
    def ReadDocument(
        self,
        SourceData: KSourceType,
        **NamedValues: object,
    ) -> CadDocument:
        return self.ReadAdapter(SourceData, **NamedValues)[0]

    # replayable inputs ensure probing never consumes one shot sources before reading
    def ReadAdapter(
        self,
        SourceData: KSourceType,
        **NamedValues: object,
    ) -> tuple[CadDocument, CadReaderAdapter]:
        FormatId, OptionsData = GetReadArgs(NamedValues)
        ReplaySource = GetReplayMut(SourceData)
        StreamPos = 0
        if isinstance(ReplaySource, SeekableSource):
            StreamPos = ReplaySource.tell()
        AdapterData = (
            self.GetReader(FormatId) if FormatId else self.PickReader(ReplaySource)
        )
        if isinstance(ReplaySource, SeekableSource):
            ReplaySource.seek(StreamPos)
        DocumentData = AdapterData.read(ReplaySource, OptionsData)
        DocumentData.AssertValid()
        return DocumentData, AdapterData
