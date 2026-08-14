# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .brep_math import IsValidTol
from .brep_model import BrepModel


# face validation protects trimming and surface references before shell traversal
def GetFaceErrors(
    ModelValue: BrepModel, IdentitySets: dict[str, frozenset[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for FaceValue in ModelValue.Faces:
        if FaceValue.SurfaceId not in IdentitySets["Surfaces"]:
            ErrorValues.append(
                f"B-rep face {FaceValue.EntityId} references a missing surface"
            )
        if not FaceValue.LoopIds:
            ErrorValues.append(f"B-rep face {FaceValue.EntityId} has no loops")
        for LoopId in FaceValue.LoopIds:
            if LoopId not in IdentitySets["Loops"]:
                ErrorValues.append(
                    f"B-rep face {FaceValue.EntityId} references a missing loop"
                )
        if not IsValidTol(FaceValue.Tolerance):
            ErrorValues.append(
                f"B-rep face {FaceValue.EntityId} has an invalid tolerance"
            )
    for FaceUseValue in ModelValue.FaceUses:
        if FaceUseValue.FaceId not in IdentitySets["Faces"]:
            ErrorValues.append(
                f"B-rep face use {FaceUseValue.EntityId} references a missing face"
            )
    return tuple(ErrorValues)
