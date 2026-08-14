# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from interchange import CadDocument

from .adapters import CadReaderAdapter as ReaderAdapter


# source aliases survive conversion because readers may report a canonical family format
def ResolveFormat(DocumentData: CadDocument, ReaderData: ReaderAdapter) -> str:
    SourceIds = {
        ValueText.casefold()
        for ValueText in (ReaderData.info.format_id, *ReaderData.info.aliases)
    }
    if DocumentData.source.format_id.casefold() in SourceIds:
        return DocumentData.source.format_id
    return ReaderData.info.format_id
