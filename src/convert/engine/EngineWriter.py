# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from interchange import CadDocument

from convert.adapters import Destination, WriteOptions, WriteResult


# write delegation stays isolated because output staging belongs entirely to the registry
class EngineWrite:

    # registry delegation preserves one validation path for every public document write
    def WriteTarget(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: Destination,
        *,
        FormatId: str | None = None,
        WriteOpts: WriteOptions | None = None,
    ) -> WriteResult:
        return getattr(SelfValue, "registry").write(
            DocumentData,
            TargetData,
            format_id=FormatId,
            options=WriteOpts or WriteOptions(),
        )
