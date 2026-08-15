# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.document.models.DocumentModel import CadDocument


# nested records can be malformed at runtime so validators narrow them before use
def GetDocument(SourceValue: object) -> CadDocument | None:
    return SourceValue if isinstance(SourceValue, CadDocument) else None
