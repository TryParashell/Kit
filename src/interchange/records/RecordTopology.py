# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass

from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.core.ModelBase import ModelBase


# topology summaries expose counts without requiring every caller to inspect boundary data
@MakeDataClass(frozen=True, slots=True)
class TopologyCounts(ModelBase):
    solid_count: int = 0
    shell_count: int = 0
    face_count: int = 0
    edge_count: int = 0
    vertex_count: int = 0
    volume: float | None = None
    surface_area: float | None = None
    bounding_box: BoundingBox | None = None
    valid: bool | None = None

    @property
    def SolidCount(self) -> int:
        return self.solid_count

    @property
    def ShellCount(self) -> int:
        return self.shell_count

    @property
    def FaceCount(self) -> int:
        return self.face_count

    @property
    def EdgeCount(self) -> int:
        return self.edge_count

    @property
    def VertexCount(self) -> int:
        return self.vertex_count

    @property
    def Volume(self) -> float | None:
        return self.volume

    @property
    def SurfaceArea(self) -> float | None:
        return self.surface_area

    @property
    def BoundingBox(self) -> BoundingBox | None:
        return self.bounding_box

    @property
    def IsValid(self) -> bool | None:
        return self.valid
