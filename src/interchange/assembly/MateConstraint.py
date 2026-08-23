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

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return self.name

     # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> MateKind | str:
        return self.kind

     # owner link keeps nested placement resolvable during assembly walks
    @property
    def OwnerDefinitionId(self) -> str:
        return self.owner_definition_id

     # referenced entity ids keep mate scope explicit and verifiable
    @property
    def EntityIds(self) -> tuple[str, ...]:
        return self.entity_ids

     # explicit order keeps sibling sequencing stable across adapter round trips
    @property
    def Order(self) -> int:
        return self.order

     # typed value keeps configuration usable without parsing conventions
    @property
    def Value(self) -> ParameterValue | None:
        return self.value

     # parameter links keep mate values driven by configurable expressions
    @property
    def ParameterIds(self) -> tuple[str, ...]:
        return self.parameter_ids

     # alignment choice keeps orientation intent explicit for export writers
    @property
    def Alignment(self) -> MateAlignment | str:
        return self.alignment

     # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

     # driving flag splits real constraints from reference measurements
    @property
    def IsDriving(self) -> bool:
        return self.driving

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
