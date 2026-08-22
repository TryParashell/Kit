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
from interchange.geometry.models.Transform import Transform


# support planes retain sketch attachment and offset relationships across systems
@ModelDataMut(
    DefaultMap={
        "support_selection_id": None,
        "offset_parameter_id": None,
        "provenance": None,
    },
    FactoryMap={"attributes": FreezeMapping},
)
class SupportPlane(ModelBase):
    id: str
    name: str
    transform: Transform
    support_selection_id: str | None
    offset_parameter_id: str | None
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        Transform: ClassVar[Transform]
        SupportSelectionId: ClassVar[str | None]
        OffsetParameterId: ClassVar[str | None]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
