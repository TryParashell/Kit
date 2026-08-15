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
        "curves": (),
        "pcurves": (),
        "surfaces": (),
        "vertices": (),
        "edges": (),
        "coedges": (),
        "loops": (),
        "wires": (),
        "faces": (),
        "face_uses": (),
        "shells": (),
        "shell_uses": (),
        "regions": (),
        "bodies": (),
        "schema_version": "1.0",
    }
)
class BrepModel(ModelBase):
    curves: tuple[BrepCurve, ...]
    pcurves: tuple[BrepPcurve, ...]
    surfaces: tuple[BrepSurface, ...]
    vertices: tuple[BrepVertex, ...]
    edges: tuple[BrepEdge, ...]
    coedges: tuple[BrepCoedge, ...]
    loops: tuple[BrepLoop, ...]
    wires: tuple[BrepWire, ...]
    faces: tuple[BrepFace, ...]
    face_uses: tuple[BrepFaceUse, ...]
    shells: tuple[BrepShell, ...]
    shell_uses: tuple[BrepShellUse, ...]
    regions: tuple[BrepRegion, ...]
    bodies: tuple[BrepBody, ...]
    schema_version: str
    if TYPE_CHECKING:
        Curves: ClassVar[tuple[BrepCurve, ...]]
        Pcurves: ClassVar[tuple[BrepPcurve, ...]]
        Surfaces: ClassVar[tuple[BrepSurface, ...]]
        Vertices: ClassVar[tuple[BrepVertex, ...]]
        Edges: ClassVar[tuple[BrepEdge, ...]]
        Coedges: ClassVar[tuple[BrepCoedge, ...]]
        Loops: ClassVar[tuple[BrepLoop, ...]]
        Wires: ClassVar[tuple[BrepWire, ...]]
        Faces: ClassVar[tuple[BrepFace, ...]]
        FaceUses: ClassVar[tuple[BrepFaceUse, ...]]
        Shells: ClassVar[tuple[BrepShellUse, ...]]
        ShellUses: ClassVar[tuple[BrepShellUse, ...]]
        Regions: ClassVar[tuple[BrepRegion, ...]]
        Bodies: ClassVar[tuple[BrepBody, ...]]
        SchemaVersion: ClassVar[str]

    # model validation delegates because topology checks change independently from storage
    def GetErrors(self, DesignBodyIds: frozenset[str] = frozenset()) -> tuple[str, ...]:
        from interchange.brep.validation.BrepValidate import GetBrepErrors

        return GetBrepErrors(self, DesignBodyIds)
