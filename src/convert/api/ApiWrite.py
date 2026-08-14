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

from interchange import CadDocument

from convert.adapters import Destination, WriteOptions, WriteResult
from convert.api.ApiContext import KConvertEngine
from convert.api.ApiValues import BuildWriteVals


# public writes enforce portable self containment before registry staging begins
def WriteDocument(
    DocumentData: CadDocument,
    TargetData: Destination,
    *,
    DestFormat: str | None = None,
    Configuration: str | None = None,
    Overwrite: bool = False,
    ValidateData: bool = True,
    AllowCarrier: bool = True,
    InputValues: TypeMap[str, AnyValue] | None = None,
) -> WriteResult:
    EngineCall = getattr(KConvertEngine, "write", None)
    WriteOpts = WriteOptions(
        configuration=Configuration,
        overwrite=Overwrite,
        validate=ValidateData,
        values=BuildWriteVals(InputValues, AllowCarrier),
    )
    if EngineCall is not None:
        return EngineCall(
            DocumentData,
            TargetData,
            format_id=DestFormat,
            options=WriteOpts,
        )
    return KConvertEngine.WriteTarget(
        DocumentData,
        TargetData,
        FormatId=DestFormat,
        WriteOpts=WriteOpts,
    )
