# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import cast as CastValue

from interchange.geometry.models.BoundingBox import BoundingBox


# topology summaries stay readable through typed accessors without storage coupling
class TopologySummary:
    __slots__ = ()

    # quick counts let callers sanity check complexity before deep parsing
    @property
    def SolidCount(self) -> int:
        return CastValue(int, getattr(self, "solid_count"))

    # quick counts let callers sanity check complexity before deep parsing
    @property
    def ShellCount(self) -> int:
        return CastValue(int, getattr(self, "shell_count"))

    # quick counts let callers sanity check complexity before deep parsing
    @property
    def FaceCount(self) -> int:
        return CastValue(int, getattr(self, "face_count"))

    # quick counts let callers sanity check complexity before deep parsing
    @property
    def EdgeCount(self) -> int:
        return CastValue(int, getattr(self, "edge_count"))

    # quick counts let callers sanity check complexity before deep parsing
    @property
    def VertexCount(self) -> int:
        return CastValue(int, getattr(self, "vertex_count"))

    # volume summary supports mass property estimates without kernel calls
    @property
    def Volume(self) -> float | None:
        return CastValue(float | None, getattr(self, "volume"))

    # area summary supports coating estimates without tessellation work
    @property
    def SurfaceArea(self) -> float | None:
        return CastValue(float | None, getattr(self, "surface_area"))

    # cached bounds keep spatial filtering cheap for large assemblies
    @property
    def BoundingBox(self) -> BoundingBox | None:
        return CastValue(BoundingBox | None, getattr(self, "bounding_box"))

    # validity hint lets pipelines short circuit obviously broken inputs early
    @property
    def IsValid(self) -> bool | None:
        return CastValue(bool | None, getattr(self, "valid"))
