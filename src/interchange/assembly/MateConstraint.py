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

from interchange.assembly.AssemblyEnums import MateAlignment, MateKind
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordParameter import ParameterValue
from interchange.records.RecordProvenance import Provenance


# mate constraints preserve relationships values and bindings across systems
@ModelDataMut
class MateConstraint(ModelBase):
    id: str
    name: str
    kind: MateKind | str
    owner_definition_id: str
    entity_ids: tuple[str, ...]
    order: int = 0
    value: ParameterValue | None = None
    parameter_ids: tuple[str, ...] = ()
    alignment: MateAlignment | str = MateAlignment.KUnknown
    suppressed: bool = False
    driving: bool = True
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def EntityName(self) -> str:
        return self.name

    @property
    def EntityKind(self) -> MateKind | str:
        return self.kind

    @property
    def OwnerDefinitionId(self) -> str:
        return self.owner_definition_id

    @property
    def EntityIds(self) -> tuple[str, ...]:
        return self.entity_ids

    @property
    def Order(self) -> int:
        return self.order

    @property
    def Value(self) -> ParameterValue | None:
        return self.value

    @property
    def ParameterIds(self) -> tuple[str, ...]:
        return self.parameter_ids

    @property
    def Alignment(self) -> MateAlignment | str:
        return self.alignment

    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

    @property
    def IsDriving(self) -> bool:
        return self.driving

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
