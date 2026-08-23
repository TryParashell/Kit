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

from interchange.assembly.AssemblyEnums import MateEntityKind
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.assembly.TransformMatrix import TransformMatrix


# mate entities resolve constraint geometry through occurrence paths and optional frames
@ModelDataMut
class MateEntity(ModelBase):
    id: str
    owner_definition_id: str
    instance_path: tuple[str, ...]
    kind: MateEntityKind | str
    source_entity_id: str = ""
    selection_id: str = ""
    frame: TransformMatrix | None = None
    radius: float | None = None
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # owner link keeps nested placement resolvable during assembly walks
    @property
    def OwnerDefinitionId(self) -> str:
        return self.owner_definition_id

     # path tuple addresses entities nested inside sub assemblies unambiguously
    @property
    def InstancePath(self) -> tuple[str, ...]:
        return self.instance_path

     # kind tag lets consumers branch on semantics without importing concrete classes
    @property
    def EntityKind(self) -> MateEntityKind | str:
        return self.kind

     # native entity id keeps mate targets traceable into vendor documents
    @property
    def SourceEntityId(self) -> str:
        return self.source_entity_id

     # selection id mirrors how users picked geometry so replays stay faithful
    @property
    def SelectionId(self) -> str:
        return self.selection_id

     # local frame keeps mate math independent of global coordinate guesses
    @property
    def Frame(self) -> TransformMatrix | None:
        return self.frame

     # radius keeps circles arcs and cylinders sized without sampling geometry
    @property
    def Radius(self) -> float | None:
        return self.radius

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
