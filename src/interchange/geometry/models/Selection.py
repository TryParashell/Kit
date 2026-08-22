# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import ClassVar
from typing import Mapping as TypeMap
from typing import TYPE_CHECKING

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
    if TYPE_CHECKING:
        EntityKind: ClassVar[str]
        EntityId: ClassVar[str]
        Subelement: ClassVar[str]


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
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        SelectionPath: ClassVar[tuple[SelectPathElem, ...]]
        Query: ClassVar[TypeMap[str, object]]
        Point: ClassVar[SpaceVector | None]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
