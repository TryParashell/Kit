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
from typing import Any as AnyValue

from convert.adapters import AdapterInfo, WriteResult
from convert.adapters.json import JsonAdapter
from interchange import CadDocument, Capability
from tests.interchange.test_document import BuildDocument


# configurable results let registry tests provoke contract mismatches without duplicating adapters
class ResultAdapter(JsonAdapter):

    # injected metadata and result names isolate each registry policy under test
    def __init__(
        SelfValue,
        InfoData: AdapterInfo,
        *,
        ProbeFormat: str | None = None,
        WriteFormat: str | None = None,
    ) -> None:
        SelfValue.InfoData = InfoData
        SelfValue.ProbeFormat = ProbeFormat
        SelfValue.WriteFormat = WriteFormat

    # injected metadata keeps tests independent from the json adapter singleton
    @property
    def GetInfo(SelfValue) -> AdapterInfo:
        return SelfValue.InfoData

    # probe rewriting exercises registry validation while retaining real json recognition
    def ProbeData(SelfValue, SourceData: AnyValue):
        ResultData = super().probe(SourceData)
        return ReplaceValue(
            ResultData,
            format_id=SelfValue.ProbeFormat or SelfValue.info.format_id,
        )

    # write rewriting exercises registry validation while retaining real output behavior
    def WriteData(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: AnyValue,
        OptionsData: AnyValue = None,
    ) -> WriteResult:
        ResultData = super().write(DocumentData, TargetData, OptionsData)
        return ReplaceValue(
            ResultData,
            adapter=SelfValue.WriteFormat or SelfValue.info.format_id,
        )


for LegacyName, MethodName in {
    "info": "GetInfo",
    "probe": "ProbeData",
    "write": "WriteData",
}.items():
    setattr(ResultAdapter, LegacyName, getattr(ResultAdapter, MethodName))


# path only carrier output lets staging tests inspect rollback without format specific writers
class CarrierAdapter(ResultAdapter):

    # path restriction forces registry staging through its transactional filesystem branch
    def CanWrite(SelfValue, DocumentData: CadDocument, TargetData: AnyValue) -> bool:
        return isinstance(TargetData, (str, FilePath))

    # unusable output exercises rollback after a writer creates the staged artifact
    def WriteData(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: AnyValue,
        OptionsData: AnyValue = None,
    ) -> WriteResult:
        OutputPath = FilePath(TargetData).expanduser().resolve()
        OutputPath.parent.mkdir(parents=True, exist_ok=True)
        OutputPath.write_bytes(b"carrier")
        return WriteResult(
            OutputPath,
            SelfValue.info.format_id,
            len(b"carrier"),
            application_usable=False,
            vendor_loadable=False,
        )


setattr(CarrierAdapter, "supports", CarrierAdapter.CanWrite)
setattr(CarrierAdapter, "write", CarrierAdapter.WriteData)


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
