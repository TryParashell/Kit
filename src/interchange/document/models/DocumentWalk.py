# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING as TypeChecking
from typing import Iterator as ValueIterator

if TypeChecking:
    from interchange.document.models.DocumentModel import CadDocument


# nested assembly documents need cycle safe traversal for aggregate operations
def WalkDocuments(DocumentValue: CadDocument) -> ValueIterator[CadDocument]:
    from interchange.document.validation.DocumentBoundary import GetDocument

    PendingValues = [DocumentValue]
    SeenValues: set[int] = set()
    while PendingValues:
        ItemValue = PendingValues.pop()
        IdentityValue = id(ItemValue)
        if IdentityValue in SeenValues:
            continue
        SeenValues.add(IdentityValue)
        yield ItemValue
        if ItemValue.assembly is None:
            continue
        for ComponentValue in reversed(ItemValue.assembly.Documents):
            NestedValue = GetDocument(ComponentValue.Document)
            if NestedValue is not None:
                PendingValues.append(NestedValue)
