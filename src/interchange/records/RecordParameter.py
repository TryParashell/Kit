# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import field as MakeDataField
from typing import ClassVar, TYPE_CHECKING
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance


# typed values retain dimensional and primitive meaning alongside source text
@ModelDataMut
class ParameterValue(ModelBase):
    value: str | int | float | bool
    kind: ValueKind = ValueKind.KNumber
    unit: str = ""
    if TYPE_CHECKING:
        Value: ClassVar[str | int | float | bool]
        EntityKind: ClassVar[ValueKind]
        UnitName: ClassVar[str]


# expressions preserve editable relationships instead of reducing every parameter to literals
@ModelDataMut(DefaultMap={"parameter_ids": (), "language": "kit"})
class Expression(ModelBase):
    source: str
    parameter_ids: tuple[str, ...]
    language: str
    if TYPE_CHECKING:
        Source: ClassVar[str]
        ParameterIds: ClassVar[tuple[str, ...]]
        Language: ClassVar[str]


# parameters retain editable values ownership and source evidence across format boundaries
@ModelDataMut
class Parameter(ModelBase):
    id: str
    name: str
    value: ParameterValue
    role: ParameterRole = ParameterRole.KDriving
    expression: Expression | None = None
    owner_id: str = ""
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        Value: ClassVar[ParameterValue]
        ValueRole: ClassVar[ParameterRole]
        Expression: ClassVar[Expression | None]
        OwnerId: ClassVar[str]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
