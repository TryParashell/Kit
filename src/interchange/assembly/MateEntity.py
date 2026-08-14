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

from interchange.assembly.AssemblyEnums import MateEntityKind
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.assembly.TransformMatrix import TransformMatrix


# mate entities resolve constraint geometry through occurrence paths and optional frames
@ModelDataMut(
    DefaultMap={
        "SourceEntityId": "",
        "SelectionId": "",
        "Frame": None,
        "Radius": None,
        "Provenance": None,
    },
    FactoryMap={"Attributes": FreezeMapping},
)
class MateEntity(ModelBase):
    EntityId: str
    OwnerDefinitionId: str
    InstancePath: tuple[str, ...]
    EntityKind: MateEntityKind | str
    SourceEntityId: str
    SelectionId: str
    Frame: TransformMatrix | None
    Radius: float | None
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
