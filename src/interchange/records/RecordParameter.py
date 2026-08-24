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
from interchange.core.ModelExtras import ModelExtras
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.records.ParameterView import ParameterView
from interchange.records.RecordProvenance import Provenance


# typed values retain dimensional and primitive meaning alongside source text
@ModelDataMut
class ParameterValue(ModelBase):
    value: str | int | float | bool
    kind: ValueKind = ValueKind.KNumber
    unit: str = ""

    # typed value keeps configuration usable without parsing conventions
    @property
    def Value(self) -> str | int | float | bool:
        return self.value

    # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> ValueKind:
        return self.kind

    # unit spelling keeps quantities unambiguous across metric and imperial sources
    @property
    def UnitName(self) -> str:
        return self.unit


# expressions preserve editable relationships instead of reducing every parameter to literals
@ModelDataMut
class Expression(ModelBase):
    source: str
    parameter_ids: tuple[str, ...] = ()
    language: str = "kit"

    # original text keeps expressions debuggable without reformatting
    @property
    def Source(self) -> str:
        return self.source

    # parameter links keep mate values driven by configurable expressions
    @property
    def ParameterIds(self) -> tuple[str, ...]:
        return self.parameter_ids

    # language tag routes expression evaluation to matching syntax rules
    @property
    def Language(self) -> str:
        return self.language


# parameters retain editable values ownership and source evidence across format boundaries
@ModelDataMut
class Parameter(ParameterView, ModelExtras, ModelBase):
    id: str
    name: str
    value: ParameterValue
    role: ParameterRole = ParameterRole.KDriving
    expression: Expression | None = None
    owner_id: str = ""
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)
