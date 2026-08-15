# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING
from typing import Mapping as TypeMap

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.assembly.TransformMatrix import TransformMatrix


# component instances preserve placement order suppression and configuration choices
@ModelDataMut(
    DefaultMap={
        "transform": TransformMatrix(),
        "order": 0,
        "reference_number": "",
        "configuration_name": "",
        "configuration_id": "",
        "suppressed": False,
        "hidden": False,
        "fixed": False,
        "flexible": False,
        "exclude_from_bom": False,
        "provenance": None,
    },
    FactoryMap={"attributes": FreezeMapping},
)
class ComponentInst(ModelBase):
    id: str
    name: str
    definition_id: str
    owner_definition_id: str
    transform: TransformMatrix
    order: int
    reference_number: str
    configuration_name: str
    configuration_id: str
    suppressed: bool
    hidden: bool
    fixed: bool
    flexible: bool
    exclude_from_bom: bool
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        EntityName: ClassVar[str]
        DefinitionId: ClassVar[str]
        OwnerDefinitionId: ClassVar[str]
        Transform: ClassVar[TransformMatrix]
        Order: ClassVar[int]
        ReferenceNumber: ClassVar[str]
        ConfigurationName: ClassVar[str]
        ConfigurationId: ClassVar[str]
        IsSuppressed: ClassVar[bool]
        IsHidden: ClassVar[bool]
        IsFixed: ClassVar[bool]
        IsFlexible: ClassVar[bool]
        IsExcludedBom: ClassVar[bool]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
