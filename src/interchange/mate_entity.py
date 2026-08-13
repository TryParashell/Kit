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

from .assembly_enums import MateEntityKind
from .common import FreezeMapping
from .model_base import ModelBase, ModelDataMut
from .record_provenance import Provenance
from .transform_matrix import TransformMatrix


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
