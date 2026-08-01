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
