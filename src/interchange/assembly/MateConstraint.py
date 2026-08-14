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

from interchange.assembly.AssemblyEnums import MateAlignment, MateKind
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordParameter import ParameterValue
from interchange.records.RecordProvenance import Provenance


# mate constraints preserve relationships values and bindings across systems
@ModelDataMut(
    DefaultMap={
        "Order": 0,
        "Value": None,
        "ParameterIds": (),
        "Alignment": MateAlignment.KUnknown,
        "IsSuppressed": False,
        "IsDriving": True,
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class MateConstraint(ModelBase):
    EntityId: str
    EntityName: str
    EntityKind: MateKind | str
    OwnerDefinitionId: str
    EntityIds: tuple[str, ...]
    Order: int
    Value: ParameterValue | None
    ParameterIds: tuple[str, ...]
    Alignment: MateAlignment | str
    IsSuppressed: bool
    IsDriving: bool
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
