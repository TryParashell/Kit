# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations


from interchange.core.ModelBase import ModelBase, ModelDataMut


# component documents embed linked portable documents without weakening graph typing
@ModelDataMut
class ComponentDoc(ModelBase):
    id: str
    document: CadDocument

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def Document(self) -> CadDocument:
        return self.document


# the linked document type binds at the bottom so the recursive assembly and
# document graph resolves completely no matter which module is imported first;
# runtime hint resolution requires this name while the graph stays recursive
from interchange.document.models.DocumentModel import (  # lgtm[py/cyclic-import]
    CadDocument,
)
