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
from interchange.enums.EnumValues import ParameterRole, ValueKind
from interchange.core.ModelBase import ModelBase, ModelDataMut
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
class Parameter(ModelBase):
    id: str
    name: str
    value: ParameterValue
    role: ParameterRole = ParameterRole.KDriving
    expression: Expression | None = None
    owner_id: str = ""
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return self.name

     # typed value keeps configuration usable without parsing conventions
    @property
    def Value(self) -> ParameterValue:
        return self.value

     # role tags separate driven driving and reference usages cleanly
    @property
    def ValueRole(self) -> ParameterRole:
        return self.role

     # optional formula keeps derived values live instead of frozen snapshots
    @property
    def Expression(self) -> Expression | None:
        return self.expression

     # owner link ties parameters to features without back references
    @property
    def OwnerId(self) -> str:
        return self.owner_id

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
