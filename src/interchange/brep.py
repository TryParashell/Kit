# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .brep_curves import (
    BrepCurve,
    BrepEntity,
    CircleCurve,
    EllipseCurve,
    IntersectCurve,
    LineCurve,
    NativeCurve,
    NurbsCurve,
)
from .brep_exports import KBrepExports
from .brep_model import BrepModel
from .brep_pcurves import (
    BrepPcurve,
    CirclePcurve,
    LinePcurve,
    NativePcurve,
    NurbsPcurve,
)
from .brep_surfaces import (
    BrepSurface,
    ConeSurface,
    CylinderSurface,
    NativeSurface,
    NurbsSurface,
    OffsetSurface,
    PlaneSurface,
    SphereSurface,
    TorusSurface,
)
from .brep_topology import (
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
from .python_compat import BindCompatMut
from .python_compat_brep_methods import BindBrepMut

BindCompatMut(
    (
        BrepEntity,
        BrepCurve,
        LineCurve,
        CircleCurve,
        EllipseCurve,
        NurbsCurve,
        IntersectCurve,
        NativeCurve,
        BrepPcurve,
        LinePcurve,
        CirclePcurve,
        NurbsPcurve,
        NativePcurve,
        BrepSurface,
        PlaneSurface,
        CylinderSurface,
        ConeSurface,
        SphereSurface,
        TorusSurface,
        NurbsSurface,
        OffsetSurface,
        NativeSurface,
        BrepVertex,
        BrepEdge,
        BrepCoedge,
        BrepLoop,
        BrepWire,
        BrepFace,
        BrepFaceUse,
        BrepShell,
        BrepShellUse,
        BrepRegion,
        BrepBody,
        BrepModel,
    ),
    {__name__: globals()},
)
BindBrepMut(BrepModel)

# brep consumers need one intentional historical public contract
__all__ = KBrepExports
