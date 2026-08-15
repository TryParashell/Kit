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

from convert.adapters.base.ContractTypes import KTargetType as Destination
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult
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
    WriteOpts = WriteOptions(
        configuration=Configuration,
        overwrite=Overwrite,
        validate=ValidateData,
        values=BuildWriteVals(InputValues, AllowCarrier),
    )
    return KConvertEngine.write(
        DocumentData,
        TargetData,
        format_id=DestFormat,
        options=WriteOpts,
    )
