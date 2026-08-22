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

from interchange.assembly.AssemblyEnums import MateAlignment, MateKind
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordParameter import ParameterValue
from interchange.records.RecordProvenance import Provenance


# mate constraints preserve relationships values and bindings across systems
@ModelDataMut(
    DefaultMap={
        "order": 0,
        "value": None,
        "parameter_ids": (),
        "alignment": MateAlignment.KUnknown,
        "suppressed": False,
        "driving": True,
        "provenance": None,
    },
    FactoryMap={"attributes": FreezeMapping},
)
class MateConstraint(ModelBase):
    id: str
    name: str
    kind: MateKind | str
    owner_definition_id: str
    entity_ids: tuple[str, ...]
    order: int
    value: ParameterValue | None
    parameter_ids: tuple[str, ...]
    alignment: MateAlignment | str
    suppressed: bool
    driving: bool
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        EntityKind: ClassVar[MateKind | str]
        OwnerDefinitionId: ClassVar[str]
        EntityIds: ClassVar[tuple[str, ...]]
        Order: ClassVar[int]
        Value: ClassVar[ParameterValue | None]
        ParameterIds: ClassVar[tuple[str, ...]]
        Alignment: ClassVar[MateAlignment | str]
        IsSuppressed: ClassVar[bool]
        IsDriving: ClassVar[bool]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
