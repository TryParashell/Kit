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

     # stable identity lets records reference each other without holding full objects
    @property
    def EntityId(self) -> str:
        return self.id

     # human readable label keeps diagnostics and diffs meaningful for reviewers
    @property
    def EntityName(self) -> str:
        return self.name

     # vertex table keeps triangle resolution independent of cad precision
    @property
    def Vertices(self) -> tuple[SpaceVector, ...]:
        return self.vertices

     # indexed triangles avoid repeating coordinates for compact transfer
    @property
    def Triangles(self) -> tuple[tuple[int, int, int], ...]:
        return self.triangles

     # stored normals preserve shading intent without recomputation drift
    @property
    def Normals(self) -> tuple[SpaceVector, ...]:
        return self.normals

     # origin details stay optional so synthesized records can omit source facts safely
    @property
    def Provenance(self) -> Provenance | None:
        return self.provenance

     # open attribute bag preserves vendor extras that typed fields cannot express yet
    @property
    def Attributes(self) -> TypeMap[str, object]:
        return self.attributes
