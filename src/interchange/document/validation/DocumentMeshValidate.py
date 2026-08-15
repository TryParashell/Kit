# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite as IsFiniteNum

from interchange.document.models.DocumentModel import CadDocument


# mesh validation protects assembly geometry consumers from malformed numeric topology
def GetMeshErrors(DocumentValue: CadDocument) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for MeshValue in DocumentValue.meshes:
        if any(
            not all(
                IsFiniteNum(SourceValue)
                for SourceValue in (
                    VertexValue.x,
                    VertexValue.y,
                    VertexValue.z,
                )
            )
            for VertexValue in MeshValue.vertices
        ):
            ErrorValues.append(
                f"mesh {MeshValue.id} contains a non-finite vertex"
            )
        if MeshValue.normals and len(MeshValue.normals) != len(MeshValue.vertices):
            ErrorValues.append(
                f"mesh {MeshValue.id} has a mismatched normal count"
            )
        if any(
            not all(
                IsFiniteNum(SourceValue)
                for SourceValue in (
                    NormalValue.x,
                    NormalValue.y,
                    NormalValue.z,
                )
            )
            for NormalValue in MeshValue.normals
        ):
            ErrorValues.append(
                f"mesh {MeshValue.id} contains a non-finite normal"
            )
        for TriangleValue in MeshValue.triangles:
            if (
                len(TriangleValue) != 3
                or any(type(IndexValue) is not int for IndexValue in TriangleValue)
                or any(
                    IndexValue < 0 or IndexValue >= len(MeshValue.vertices)
                    for IndexValue in TriangleValue
                )
            ):
                ErrorValues.append(
                    f"mesh {MeshValue.id} contains an invalid triangle"
                )
                break
    return tuple(ErrorValues)
