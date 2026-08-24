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

    # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

    # underlying document access keeps assembly views decoupled from storage internals
    @property
    def Document(self) -> CadDocument:
        return self.document


from interchange.document.models.DocumentModel import (  # lgtm[py/cyclic-import]
    CadDocument,
)
