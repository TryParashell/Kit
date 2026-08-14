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

from .common import FreezeMapping
from .model_base import ModelBase, ModelDataMut
from .record_provenance import Provenance


# mate groups retain source ordering and hierarchy for editable organization
@ModelDataMut(
    DefaultMap={"ParentGroupId": "", "Order": 0, "Provenance": None},
    FactoryMap={"Attributes": FreezeMapping},
)
class MateGroup(ModelBase):
    EntityId: str
    EntityName: str
    OwnerDefinitionId: str
    MateIds: tuple[str, ...]
    ParentGroupId: str
    Order: int
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
