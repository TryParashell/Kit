# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from interchange.brep.curves.BrepCurves import BrepCurve
from interchange.brep.curves.BrepPcurves import BrepPcurve
from interchange.brep.surfaces.BrepSurfaces import BrepSurface
from interchange.brep.topology.BrepTopology import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
    BrepWire,
)
from interchange.core.ModelBase import ModelBase, ModelDataMut


# boundary models aggregate analytic geometry and incidence into one neutral graph
@ModelDataMut(
    DefaultMap={
        "Curves": (),
        "Pcurves": (),
        "Surfaces": (),
        "Vertices": (),
        "Edges": (),
        "Coedges": (),
        "Loops": (),
        "Wires": (),
        "Faces": (),
        "FaceUses": (),
        "Shells": (),
        "ShellUses": (),
        "Regions": (),
        "Bodies": (),
        "SchemaVersion": "1.0",
    }
)
class BrepModel(ModelBase):
    Curves: tuple[BrepCurve, ...]
    Pcurves: tuple[BrepPcurve, ...]
    Surfaces: tuple[BrepSurface, ...]
    Vertices: tuple[BrepVertex, ...]
    Edges: tuple[BrepEdge, ...]
    Coedges: tuple[BrepCoedge, ...]
    Loops: tuple[BrepLoop, ...]
    Wires: tuple[BrepWire, ...]
    Faces: tuple[BrepFace, ...]
    FaceUses: tuple[BrepFaceUse, ...]
    Shells: tuple[BrepShell, ...]
    ShellUses: tuple[BrepShellUse, ...]
    Regions: tuple[BrepRegion, ...]
    Bodies: tuple[BrepBody, ...]
    SchemaVersion: str
    if TYPE_CHECKING:
        curves: ClassVar[tuple[BrepCurve, ...]]
        pcurves: ClassVar[tuple[BrepPcurve, ...]]
        surfaces: ClassVar[tuple[BrepSurface, ...]]
        vertices: ClassVar[tuple[BrepVertex, ...]]
        edges: ClassVar[tuple[BrepEdge, ...]]
        coedges: ClassVar[tuple[BrepCoedge, ...]]
        loops: ClassVar[tuple[BrepLoop, ...]]
        wires: ClassVar[tuple[BrepWire, ...]]
        faces: ClassVar[tuple[BrepFace, ...]]
        face_uses: ClassVar[tuple[BrepFaceUse, ...]]
        shells: ClassVar[tuple[BrepShell, ...]]
        shell_uses: ClassVar[tuple[BrepShellUse, ...]]
        regions: ClassVar[tuple[BrepRegion, ...]]
        bodies: ClassVar[tuple[BrepBody, ...]]
        schema_version: ClassVar[str]

    # model validation delegates because topology checks change independently from storage
    def GetErrors(self, DesignBodyIds: frozenset[str] = frozenset()) -> tuple[str, ...]:
        from interchange.brep.validation.BrepValidate import GetBrepErrors

        return GetBrepErrors(self, DesignBodyIds)
