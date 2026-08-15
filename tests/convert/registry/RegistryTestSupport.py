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

from convert.adapters import (
    AdapterInfo,
    Destination,
    ProbeResult,
    Source,
    WriteOptions,
    WriteResult,
)
from convert.adapters.json import JsonAdapter
from interchange import CadDocument, Capability
from tests.interchange.document.DocumentTests import BuildDocument


# configurable results let registry tests provoke contract mismatches without duplicating adapters
class ResultAdapter(JsonAdapter):

    # injected metadata and result names isolate each registry policy under test
    def __init__(
        self,
        InfoData: AdapterInfo,
        *,
        ProbeFormat: str | None = None,
        WriteFormat: str | None = None,
    ) -> None:
        self.InfoData = InfoData
        self.ProbeFormat = ProbeFormat
        self.WriteFormat = WriteFormat

    # injected metadata keeps tests independent from the json adapter singleton
    @property
    def info(self) -> AdapterInfo:
        return self.InfoData

    # probe rewriting exercises registry validation while retaining real json recognition
    def probe(self, SourceData: Source) -> ProbeResult:
        ResultData = super().probe(SourceData)
        return ReplaceValue(
            ResultData,
            format_id=self.ProbeFormat or self.info.format_id,
        )

    # write rewriting exercises registry validation while retaining real output behavior
    def write(
        self,
        DocumentData: CadDocument,
        TargetData: Destination,
        OptionsData: WriteOptions | None = None,
    ) -> WriteResult:
        ResultData = super().write(DocumentData, TargetData, OptionsData)
        return ReplaceValue(
            ResultData,
            adapter=self.WriteFormat or self.info.format_id,
        )


# path only carrier output lets staging tests inspect rollback without format specific writers
class CarrierAdapter(ResultAdapter):

    # path restriction forces registry staging through its transactional filesystem branch
    def supports(
        self,
        DocumentData: CadDocument,
        TargetData: Destination,
    ) -> bool:
        return isinstance(TargetData, (str, FilePath))

    # unusable output exercises rollback after a writer creates the staged artifact
    def write(
        self,
        DocumentData: CadDocument,
        TargetData: Destination,
        OptionsData: WriteOptions | None = None,
    ) -> WriteResult:
        if not isinstance(TargetData, (str, FilePath)):
            raise TypeError("carrier adapter requires a filesystem destination")
        OutputPath = FilePath(TargetData).expanduser().resolve()
        OutputPath.parent.mkdir(parents=True, exist_ok=True)
        OutputPath.write_bytes(b"carrier")
        return WriteResult(
            OutputPath,
            self.info.format_id,
            len(b"carrier"),
            application_usable=False,
            vendor_loadable=False,
        )


# uniform metadata construction keeps registry policy tests focused on their behavioral difference
def BuildAdapter(FormatId: str, **NamedValues: str) -> ResultAdapter:
    return ResultAdapter(
        AdapterInfo(
            FormatId,
            FormatId,
            "1",
            (f".{FormatId}",),
            capabilities=frozenset(Capability),
            native_capabilities=frozenset(Capability),
        ),
        **NamedValues,
    )


# shared fixture ownership prevents structural refactors from leaking old helper names here
def BuildSource() -> CadDocument:
    return BuildDocument()
