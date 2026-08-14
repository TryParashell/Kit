# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from .adapters import Destination, ReadOptions, Source, WriteOptions
from .api_context import KConvertEngine
from .api_values import BuildWriteVals
from .engine import ConversionResult as ConvertResult


# public conversion keeps independent adapters separated by one neutral document boundary
def ConvertFile(
    SourceData: Source,
    TargetData: Destination,
    *,
    SourceFormat: str | None = None,
    DestFormat: str | None = None,
    Configuration: str | None = None,
    IncludeBrep: bool = True,
    IncludeTess: bool = True,
    StrictMode: bool = True,
    Overwrite: bool = False,
    AllowCarrier: bool = True,
    WriteValues: TypeMap[str, AnyValue] | None = None,
) -> ConvertResult:
    EngineCall = getattr(KConvertEngine, "convert", None)
    ReadOpts = ReadOptions(
        configuration=Configuration,
        include_brep=IncludeBrep,
        include_tessellation=IncludeTess,
        strict=StrictMode,
    )
    WriteOpts = WriteOptions(
        configuration=Configuration,
        overwrite=Overwrite,
        validate=True,
        values=BuildWriteVals(WriteValues, AllowCarrier),
    )
    if EngineCall is not None:
        return EngineCall(
            SourceData,
            TargetData,
            source_format=SourceFormat,
            destination_format=DestFormat,
            read_options=ReadOpts,
            write_options=WriteOpts,
        )
    return KConvertEngine.ConvertData(
        SourceData,
        TargetData,
        SourceFormat=SourceFormat,
        DestFormat=DestFormat,
        ReadOpts=ReadOpts,
        WriteOpts=WriteOpts,
    )
