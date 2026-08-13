# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from interchange import CadDocument

from .adapters import ReadOptions, Source
from .api_context import KConvertEngine


# public reads centralize option construction so adapters receive one stable contract
def OpenDocument(
    SourceData: Source,
    *,
    SourceFormat: str | None = None,
    Configuration: str | None = None,
    IncludeBrep: bool = True,
    IncludeTess: bool = True,
    StrictMode: bool = True,
) -> CadDocument:
    return KConvertEngine.read(
        SourceData,
        format_id=SourceFormat,
        options=ReadOptions(
            configuration=Configuration,
            include_brep=IncludeBrep,
            include_tessellation=IncludeTess,
            strict=StrictMode,
        ),
    )
