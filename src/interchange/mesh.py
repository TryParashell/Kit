# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .types import Provenance, Vector3, frozen_mapping


@dataclass(frozen=True, slots=True)
class Mesh:
    id: str
    name: str
    vertices: tuple[Vector3, ...]
    triangles: tuple[tuple[int, int, int], ...]
    normals: tuple[Vector3, ...] = ()
    provenance: Provenance | None = None
    attributes: Mapping[str, Any] = field(default_factory=frozen_mapping)
