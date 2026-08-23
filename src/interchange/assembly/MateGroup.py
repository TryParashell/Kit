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

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return self.name

     # owner link keeps nested placement resolvable during assembly walks
    @property
    def OwnerDefinitionId(self) -> str:
        return self.owner_definition_id

     # member ids keep grouped constraints enumerable without reverse lookups
    @property
    def MateIds(self) -> tuple[str, ...]:
        return self.mate_ids

     # parent link keeps group nesting reconstructable for hierarchical writers
    @property
    def ParentGroupId(self) -> str:
        return self.parent_group_id

     # explicit order keeps sibling sequencing stable across adapter round trips
    @property
    def Order(self) -> int:
        return self.order

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
