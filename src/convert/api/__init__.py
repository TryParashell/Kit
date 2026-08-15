# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath
import re as Regex
from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange import CadDocument as KCadDocument
from interchange import PayloadRole as KPayloadRole
from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.AdapterInfo import AdapterInfo as KAdapterInfo
from convert.adapters.base.ContractTypes import (
    IsDeviceName,
    KSourceType as KSourceType,
    KTargetType as KTargetType,
)
from convert.adapters.base.ReadOptions import ReadOptions as KReadOptions
from convert.adapters.base.WriteOptions import WriteOptions as KWriteOptions
from convert.adapters.base.WriteResult import WriteResult as KWriteResult
from convert.adapters.registry import AdapterRegistry as KAdapterRegistryType
from convert.api.ApiAvailable import ListAdapters
from convert.api.ApiBrep import ExtractBrep
from convert.api.ApiContext import GetRegistry
from convert.api.ApiConvert import ConvertFile
from convert.api.ApiOpen import OpenDocument
from convert.api.ApiWrite import WriteDocument
from convert.engine import ConversionResult as KConversionResult

AdapterInfo = KAdapterInfo
AdapterRegistry = KAdapterRegistryType
CadDocument = KCadDocument
ConversionResult = KConversionResult
Destination = KTargetType
ReadOptions = KReadOptions
Source = KSourceType
WriteOptions = KWriteOptions
WriteResult = KWriteResult


# public discovery keeps the historical callable while exposing a concrete static signature
def available_adapters() -> tuple[AdapterInfo, ...]:
    return ListAdapters()


# public conversion maps historical keyword names onto the canonical orchestration contract
def convert(
    source: Source,
    destination: Destination,
    *,
    source_format: str | None = None,
    destination_format: str | None = None,
    configuration: str | None = None,
    include_brep: bool = True,
    include_tessellation: bool = True,
    strict: bool = True,
    overwrite: bool = False,
    allow_carrier: bool = True,
    write_values: Mapping[str, Any] | None = None,
) -> ConversionResult:
    return ConvertFile(
        source,
        destination,
        SourceFormat=source_format,
        DestFormat=destination_format,
        Configuration=configuration,
        IncludeBrep=include_brep,
        IncludeTess=include_tessellation,
        StrictMode=strict,
        Overwrite=overwrite,
        AllowCarrier=allow_carrier,
        WriteValues=write_values,
    )


# brep extraction retains the public path names while delegating all payload handling
def extract_brep(
    source: Source | CadDocument,
    directory: str | Path,
    *,
    source_format: str | None = None,
    overwrite: bool = False,
) -> tuple[Path, ...]:
    return ExtractBrep(
        source,
        directory,
        SourceFormat=source_format,
        Overwrite=overwrite,
    )


# document opening keeps compatibility options explicit rather than manufacturing a callable
def open_document(
    source: Source,
    *,
    source_format: str | None = None,
    configuration: str | None = None,
    include_brep: bool = True,
    include_tessellation: bool = True,
    strict: bool = True,
) -> CadDocument:
    return OpenDocument(
        source,
        SourceFormat=source_format,
        Configuration=configuration,
        IncludeBrep=include_brep,
        IncludeTess=include_tessellation,
        StrictMode=strict,
    )


# document writing keeps compatibility options explicit rather than manufacturing a callable
def write_document(
    document: CadDocument,
    destination: Destination,
    *,
    destination_format: str | None = None,
    configuration: str | None = None,
    overwrite: bool = False,
    validate: bool = True,
    allow_carrier: bool = True,
    values: Mapping[str, Any] | None = None,
) -> WriteResult:
    return WriteDocument(
        document,
        destination,
        DestFormat=destination_format,
        Configuration=configuration,
        Overwrite=overwrite,
        ValidateData=validate,
        AllowCarrier=allow_carrier,
        InputValues=values,
    )


# private construction remains available for integrations that own their own registry lifecycle
def _build_registry() -> AdapterRegistry:
    return GetRegistry()


registry = _build_registry()

Any = AnyValue
Mapping = TypeMap
Path = FilePath
PayloadRole = KPayloadRole
frozen_mapping = FreezeMapping
is_windows_device_name = IsDeviceName
re = Regex
