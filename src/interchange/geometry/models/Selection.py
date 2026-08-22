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

    @property
    def EntityKind(self) -> str:
        return self.entity_kind

    @property
    def EntityId(self) -> str:
        return self.entity_id

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

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def EntityName(self) -> str:
        return self.name

    @property
    def SelectionPath(self) -> tuple[SelectPathElem, ...]:
        return self.path

    @property
    def Query(self) -> TypeMap[str, object]:
        return self.query

    @property
    def Point(self) -> SpaceVector | None:
        return self.point

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
