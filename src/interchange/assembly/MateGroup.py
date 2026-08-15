# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# mate groups retain source ordering and hierarchy for editable organization
@ModelDataMut(
    DefaultMap={"parent_group_id": "", "order": 0, "provenance": None},
    FactoryMap={"attributes": FreezeMapping},
)
class MateGroup(ModelBase):
    id: str
    name: str
    owner_definition_id: str
    mate_ids: tuple[str, ...]
    parent_group_id: str
    order: int
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        OwnerDefinitionId: ClassVar[str]
        MateIds: ClassVar[tuple[str, ...]]
        ParentGroupId: ClassVar[str]
        Order: ClassVar[int]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
