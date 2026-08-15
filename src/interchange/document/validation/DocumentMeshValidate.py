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
    for MeshValue in DocumentValue.Meshes:
        if any(
            not all(
                IsFiniteNum(SourceValue)
                for SourceValue in (
                    VertexValue.XCoord,
                    VertexValue.YCoord,
                    VertexValue.ZCoord,
                )
            )
            for VertexValue in MeshValue.Vertices
        ):
            ErrorValues.append(
                f"mesh {MeshValue.EntityId} contains a non-finite vertex"
            )
        if MeshValue.Normals and len(MeshValue.Normals) != len(MeshValue.Vertices):
            ErrorValues.append(
                f"mesh {MeshValue.EntityId} has a mismatched normal count"
            )
        if any(
            not all(
                IsFiniteNum(SourceValue)
                for SourceValue in (
                    NormalValue.XCoord,
                    NormalValue.YCoord,
                    NormalValue.ZCoord,
                )
            )
            for NormalValue in MeshValue.Normals
        ):
            ErrorValues.append(
                f"mesh {MeshValue.EntityId} contains a non-finite normal"
            )
        for TriangleValue in MeshValue.Triangles:
            if (
                len(TriangleValue) != 3
                or any(type(IndexValue) is not int for IndexValue in TriangleValue)
                or any(
                    IndexValue < 0 or IndexValue >= len(MeshValue.Vertices)
                    for IndexValue in TriangleValue
                )
            ):
                ErrorValues.append(
                    f"mesh {MeshValue.EntityId} contains an invalid triangle"
                )
                break
    return tuple(ErrorValues)
