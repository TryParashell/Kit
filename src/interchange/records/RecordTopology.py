# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as MakeDataClass
from typing import ClassVar, TYPE_CHECKING

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
    if TYPE_CHECKING:
        SolidCount: ClassVar[int]
        ShellCount: ClassVar[int]
        FaceCount: ClassVar[int]
        EdgeCount: ClassVar[int]
        VertexCount: ClassVar[int]
        Volume: ClassVar[float | None]
        SurfaceArea: ClassVar[float | None]
        BoundingBox: ClassVar[BoundingBox | None]
        IsValid: ClassVar[bool | None]
