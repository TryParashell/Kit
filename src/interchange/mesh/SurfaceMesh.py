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
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordProvenance import Provenance


# surface meshes retain triangulation normals and source evidence for preview and exchange
@ModelDataMut
class SurfaceMesh(ModelBase):
    id: str
    name: str
    vertices: tuple[SpaceVector, ...]
    triangles: tuple[tuple[int, int, int], ...]
    normals: tuple[SpaceVector, ...] = ()
    provenance: Provenance | None = None
    attributes: TypeMap[str, object] = MakeDataField(default_factory=FreezeMapping)

    @property
    def EntityId(self) -> str:
        return self.id

    @property
    def EntityName(self) -> str:
        return self.name

    @property
    def Vertices(self) -> tuple[SpaceVector, ...]:
        return self.vertices

    @property
    def Triangles(self) -> tuple[tuple[int, int, int], ...]:
        return self.triangles

    @property
    def Normals(self) -> tuple[SpaceVector, ...]:
        return self.normals

    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
