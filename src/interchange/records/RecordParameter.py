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
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# typed values retain dimensional and primitive meaning alongside source text
@ModelDataMut(DefaultMap={"EntityKind": ValueKind.KNumber, "UnitName": ""})
class ParameterValue(ModelBase):
    Value: str | int | float | bool
    EntityKind: ValueKind
    UnitName: str


# expressions preserve editable relationships instead of reducing every parameter to literals
@ModelDataMut(DefaultMap={"ParameterIds": (), "Language": "kit"})
class Expression(ModelBase):
    Source: str
    ParameterIds: tuple[str, ...]
    Language: str


# parameters retain editable values ownership and source evidence across format boundaries
@ModelDataMut(
    DefaultMap={
        "ValueRole": ParameterRole.KDriving,
        "Expression": None,
        "OwnerId": "",
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class Parameter(ModelBase):
    EntityId: str
    EntityName: str
    Value: ParameterValue
    ValueRole: ParameterRole
    Expression: Expression | None
    OwnerId: str
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
