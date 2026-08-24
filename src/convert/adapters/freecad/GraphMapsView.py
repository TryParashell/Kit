# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

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


# native graph passes need one declared map surface so indexed lookups stay typed
class GraphMapsView(TypeProtocol):
    bodies: dict[str, BrepBody]
    coedge_owner: dict[str, tuple[str, str]]
    coedges: dict[str, BrepCoedge]
    curves: dict[str, BrepCurve]
    edge_uses: dict[str, list[str]]
    edges: dict[str, BrepEdge]
    face_uses: dict[str, BrepFaceUse]
    faces: dict[str, BrepFace]
    loop_face: dict[str, str]
    loops: dict[str, BrepLoop]
    pcurves: dict[str, BrepPcurve]
    region_body: dict[str, str]
    regions: dict[str, BrepRegion]
    shell_owners: dict[str, list[tuple[str, str]]]
    shell_uses: dict[str, BrepShellUse]
    shells: dict[str, BrepShell]
    surfaces: dict[str, BrepSurface]
    vertices: dict[str, BrepVertex]
    wire_body: dict[str, str]
    wires: dict[str, BrepWire]
