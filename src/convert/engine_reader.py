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


# read delegation stays isolated because format discovery belongs entirely to the registry
class EngineRead:

    # registry delegation preserves one validation path for every public document read
    def ReadSource(
        SelfValue,
        SourceData: Source,
        *,
        FormatId: str | None = None,
        ReadOpts: ReadOptions | None = None,
    ) -> CadDocument:
        return getattr(SelfValue, "registry").read(
            SourceData,
            format_id=FormatId,
            options=ReadOpts or ReadOptions(),
        )
