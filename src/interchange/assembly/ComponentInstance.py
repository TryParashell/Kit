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

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def EntityName(self) -> str:
        return self.name

    @property
    def DefinitionId(self) -> str:
        return self.definition_id

    @property
    def OwnerDefinitionId(self) -> str:
        return self.owner_definition_id

    @property
    def Transform(self) -> TransformMatrix:
        return self.transform

    @property
    def Order(self) -> int:
        return self.order

    @property
    def ReferenceNumber(self) -> str:
        return self.reference_number

    @property
    def ConfigurationName(self) -> str:
        return self.configuration_name

    @property
    def ConfigurationId(self) -> str:
        return self.configuration_id

    @property
    def IsSuppressed(self) -> bool:
        return self.suppressed

    @property
    def IsHidden(self) -> bool:
        return self.hidden

    @property
    def IsFixed(self) -> bool:
        return self.fixed

    @property
    def IsFlexible(self) -> bool:
        return self.flexible

    @property
    def IsExcludedBom(self) -> bool:
        return self.exclude_from_bom

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
