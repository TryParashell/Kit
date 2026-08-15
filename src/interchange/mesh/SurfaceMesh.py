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

from interchange.core.Common import FreezeMapping
from interchange.core.ModelBase import ModelBase, ModelDataMut
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordProvenance import Provenance


# surface meshes retain triangulation normals and source evidence for preview and exchange
@ModelDataMut(
    DefaultMap={"Normals": (), "Provenance": None},
    FactoryMap={"Attributes": FreezeMapping},
)
class SurfaceMesh(ModelBase):
    EntityId: str
    EntityName: str
    Vertices: tuple[SpaceVector, ...]
    Triangles: tuple[tuple[int, int, int], ...]
    Normals: tuple[SpaceVector, ...]
    Provenance: Provenance | None
    Attributes: TypeMap[str, AnyValue]
