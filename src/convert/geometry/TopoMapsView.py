# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import TYPE_CHECKING as IsTypeCheck
from typing import Protocol as TypeProtocol

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
)

if IsTypeCheck:
    from convert.geometry.Parasolid import (
        ParaCurve,  # lgtm[py/unsafe-cyclic-import]
        ParaSurface,  # lgtm[py/unsafe-cyclic-import]
    )


# parasolid traversal needs one declared map surface so ownership passes stay typed
class TopoMapsView(TypeProtocol):
    bodies: dict[str, BrepBody]
    coedge_loop: dict[str, str]
    coedges: dict[str, BrepCoedge]
    edge_coedges: dict[str, list[str]]
    edges: dict[str, BrepEdge]
    face_face_use: dict[str, str]
    face_uses: dict[str, BrepFaceUse]
    faces: dict[str, BrepFace]
    loop_face: dict[str, str]
    loops: dict[str, BrepLoop]
    region_body: dict[str, str]
    regions: dict[str, BrepRegion]
    shell_face_use: dict[str, str]
    shell_shell_use: dict[str, str]
    shell_use_region: dict[str, str]
    shell_uses: dict[str, BrepShellUse]
    shells: dict[str, BrepShell]
    surface_by_id: dict[str, ParaSurface]
    curve_by_id: dict[str, ParaCurve]
    vertex_by_id: dict[str, BrepVertex]
