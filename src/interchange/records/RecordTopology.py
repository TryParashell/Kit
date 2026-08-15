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
    SolidCount: int = 0
    ShellCount: int = 0
    FaceCount: int = 0
    EdgeCount: int = 0
    VertexCount: int = 0
    Volume: float | None = None
    SurfaceArea: float | None = None
    BoundingBox: BoundingBox | None = None
    IsValid: bool | None = None
