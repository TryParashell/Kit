# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Any as AnyValue
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.geometry.models.VectorSpace import SpaceVector


# path elements preserve hierarchical topology references across assemblies and bodies
@ModelDataMut(DefaultMap={"Subelement": ""})
class SelectPathElem(ModelBase):
    EntityKind: str
    EntityId: str
    Subelement: str


# selections retain semantic queries and resolved paths instead of display strings
@ModelDataMut(
    DefaultMap={"Point": None, "Provenance": None},
    FactoryMap={"Query": FreezeMapping, "Attributes": FreezeMapping},
)
class Selection(ModelBase):
    EntityId: str
    EntityName: str
    SelectionPath: tuple[SelectPathElem, ...]
    Query: TypeMap[str, AnyValue]
    Point: SpaceVector | None
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
