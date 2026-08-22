# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# mate groups retain source ordering and hierarchy for editable organization
@ModelDataMut
class MateGroup(ModelBase):
    id: str
    name: str
    owner_definition_id: str
    mate_ids: tuple[str, ...]
    parent_group_id: str = ""
    order: int = 0
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def EntityName(self) -> str:
        return self.name

    @property
    def OwnerDefinitionId(self) -> str:
        return self.owner_definition_id

    @property
    def MateIds(self) -> tuple[str, ...]:
        return self.mate_ids

    @property
    def ParentGroupId(self) -> str:
        return self.parent_group_id

    @property
    def Order(self) -> int:
        return self.order

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
