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

from interchange.assembly.AssemblyEnums import MateEntityKind
from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.records.RecordProvenance import Provenance
from interchange.assembly.TransformMatrix import TransformMatrix


# mate entities resolve constraint geometry through occurrence paths and optional frames
@ModelDataMut(
    DefaultMap={
        "source_entity_id": "",
        "selection_id": "",
        "frame": None,
        "radius": None,
        "provenance": None,
    },
    FactoryMap={"attributes": FreezeMapping},
)
class MateEntity(ModelBase):
    id: str
    owner_definition_id: str
    instance_path: tuple[str, ...]
    kind: MateEntityKind | str
    source_entity_id: str
    selection_id: str
    frame: TransformMatrix | None
    radius: float | None
    provenance: Provenance | None
    attributes: TypeMap[str, object]
    if TYPE_CHECKING:
        EntityId: ClassVar[str]
        OwnerDefinitionId: ClassVar[str]
        InstancePath: ClassVar[tuple[str, ...]]
        EntityKind: ClassVar[MateEntityKind | str]
        SourceEntityId: ClassVar[str]
        SelectionId: ClassVar[str]
        Frame: ClassVar[TransformMatrix | None]
        Radius: ClassVar[float | None]
        Provenance: ClassVar[Provenance | None]
        Attributes: ClassVar[TypeMap[str, object]]
