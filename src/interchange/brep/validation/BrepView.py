# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Protocol as TypeProtocol

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


# the validation view decouples topology storage from independent diagnostic passes
class BrepView(TypeProtocol):
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
