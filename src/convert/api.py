# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path
import re as Regex
from typing import Any, Mapping

from interchange import CadDocument, PayloadRole
from interchange import frozen_mapping as FreezeMapping

from .adapters import (
    AdapterInfo,
    AdapterRegistry,
    Destination,
    ReadOptions,
    Source,
    WriteOptions,
    WriteResult,
)
from .adapters import is_windows_device_name as IsDeviceName
from .api_available import ListAdapters
from .api_brep import ExtractBrep
from .api_context import KAdapterRegistry, KConvertEngine
from .api_convert import ConvertFile
from .api_open import OpenDocument
from .api_write import WriteDocument
from .engine import ConversionEngine, ConversionResult


# historical registry construction stays stable because direct module consumers may replace the returned registry
def _build_registry() -> AdapterRegistry:
    return KAdapterRegistry


# historical registry naming remains public because integrations inspect and replace the shared registry
registry = _build_registry()

# historical engine naming remains public because integrations inspect the initialized coordinator
_engine = KConvertEngine


# historical discovery naming stays stable because sdk consumers inspect and pickle this public function
def available_adapters() -> tuple[AdapterInfo, ...]:
    return ListAdapters()


# historical read naming stays stable because sdk consumers inspect and pickle this public function
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


# historical write naming stays stable because sdk consumers inspect and pickle this public function
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


# historical conversion naming stays stable because sdk consumers inspect and pickle this public function
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


# historical extraction naming stays stable because sdk consumers inspect and pickle this public function
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


# historical mapping helper remains public because direct module consumers imported it before the refactor
globals()["frozen_mapping"] = FreezeMapping

# historical device helper remains public because direct module consumers imported it before the refactor
globals()["is_windows_device_name"] = IsDeviceName

# historical regex module remains public because direct module consumers imported it before the refactor
globals()["re"] = Regex

# historical payload enum remains public because the module intentionally has no restricted export list
globals()["PayloadRole"] = PayloadRole
