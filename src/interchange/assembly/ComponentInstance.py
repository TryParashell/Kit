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
from interchange.records.RecordProvenance import Provenance
from interchange.assembly.TransformMatrix import TransformMatrix, KIdentityMatrix


# component instances preserve placement order suppression and configuration choices
@ModelDataMut
class ComponentInst(ModelBase):
    id: str
    name: str
    definition_id: str
    owner_definition_id: str
    transform: TransformMatrix = KIdentityMatrix
    order: int = 0
    reference_number: str = ""
    configuration_name: str = ""
    configuration_id: str = ""
    suppressed: bool = False
    hidden: bool = False
    fixed: bool = False
    flexible: bool = False
    exclude_from_bom: bool = False
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

    # definition link keeps shared geometry deduplicated across many instances
    @property
    def DefinitionId(self) -> str:
        return self.definition_id

    # owner link keeps nested placement resolvable during assembly walks
    @property
    def OwnerDefinitionId(self) -> str:
        return self.owner_definition_id

    # local transform keeps world placement composable through parent chains
    @property
    def Transform(self) -> TransformMatrix:
        return self.transform

    # explicit order keeps sibling sequencing stable across adapter round trips
    @property
    def Order(self) -> int:
        return self.order

    # bom reference keeps purchased part identities aligned with cad data
    @property
    def ReferenceNumber(self) -> str:
        return self.reference_number

    # configuration label keeps variant identity visible without resolving parameters
    @property
    def ConfigurationName(self) -> str:
        return self.configuration_name

    # configuration id keeps variant references stable across renames
    @property
    def ConfigurationId(self) -> str:
        return self.configuration_id

    # suppression state keeps feature trees honest about what contributes geometry
    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

    # visibility state keeps exports faithful to what users actually see
    @property
    def IsHidden(self) -> bool:
        return self.hidden

    # fixed lock protects user pinned geometry from solver drift
    @property
    def IsFixed(self) -> bool:
        return self.fixed

    # flexibility flag preserves sub assembly motion semantics that rigid treatment loses
    @property
    def IsFlexible(self) -> bool:
        return self.flexible

    # bom exclusion keeps purchased metadata out of quantity rollups silently
    @property
    def IsExcludedBom(self) -> bool:
        return self.exclude_from_bom

    # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
