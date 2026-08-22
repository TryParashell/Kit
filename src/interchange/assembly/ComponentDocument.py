# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING as IsTypeCheck

from interchange.core.ModelBase import ModelBase, ModelDataMut

if IsTypeCheck:
    from interchange.document.models.DocumentModel import (
        CadDocument,  # lgtm[py/unsafe-cyclic-import]
    )


# component documents embed linked portable documents without weakening graph typing
@ModelDataMut
class ComponentDoc(ModelBase):
    id: str
    document: CadDocument
    if IsTypeCheck:
        EntityId: ClassVar[str]
        Document: ClassVar[CadDocument]
