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
from interchange.geometry.models.VectorSpace import SpaceVector


# path elements preserve hierarchical topology references across assemblies and bodies
@ModelDataMut
class SelectPathElem(ModelBase):
    entity_kind: str
    entity_id: str
    subelement: str = ""

     # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> str:
        return self.entity_kind

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.entity_id

     # subelement token addresses faces and edges inside one entity pick
    @property
    def Subelement(self) -> str:
        return self.subelement


# selections retain semantic queries and resolved paths instead of display strings
@ModelDataMut
class Selection(ModelBase):
    id: str
    name: str
    path: tuple[SelectPathElem, ...]
    query: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    point: SpaceVector | None = None
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

     # path segments disambiguate nested hits inside assemblies reliably
    @property
    def SelectionPath(self) -> tuple[SelectPathElem, ...]:
        return self.path

     # structured query keeps filters serializable and diff friendly
    @property
    def Query(self) -> TypeMap[str, object]:
        return self.query

     # stored position keeps vertices self contained without coordinate lookups
    @property
    def Point(self) -> SpaceVector | None:
        return self.point

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
