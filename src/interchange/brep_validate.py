# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .brep_body_validate import GetBodyErrors
from .brep_curve_validate import GetCurveErrors
from .brep_edge_validate import GetEdgeErrors
from .brep_face_validate import GetFaceErrors
from .brep_identity_validate import GetBrepIds
from .brep_loop_validate import GetLoopErrors
from .brep_model import BrepModel
from .brep_pcurve_validate import GetPcurveErrors
from .brep_shell_validate import GetShellErrors
from .brep_surface_validate import GetSurfErrors


# validation orchestration preserves deterministic diagnostics across focused topology checks
def GetBrepErrors(
    ModelValue: BrepModel, DesignBodyIds: frozenset[str]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    if (
        not isinstance(ModelValue.SchemaVersion, str)
        or not ModelValue.SchemaVersion.strip()
        or ModelValue.SchemaVersion != ModelValue.SchemaVersion.strip()
    ):
        ErrorValues.append("B-rep schema version must be a non-empty string")
    IdentitySets, IdentityErrors = GetBrepIds(ModelValue)
    ErrorValues.extend(IdentityErrors)
    for CurveValue in ModelValue.Curves:
        ErrorValues.extend(GetCurveErrors(CurveValue, IdentitySets["Surfaces"]))
    for PcurveValue in ModelValue.Pcurves:
        ErrorValues.extend(GetPcurveErrors(PcurveValue))
    for SurfaceValue in ModelValue.Surfaces:
        ErrorValues.extend(GetSurfErrors(SurfaceValue, IdentitySets["Surfaces"]))
    ErrorValues.extend(GetEdgeErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetLoopErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetFaceErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetShellErrors(ModelValue, IdentitySets))
    ErrorValues.extend(GetBodyErrors(ModelValue, IdentitySets, DesignBodyIds))
    return tuple(ErrorValues)
