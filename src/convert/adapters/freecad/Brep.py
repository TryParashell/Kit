# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from collections import deque as Deque
from collections.abc import Sequence
from dataclasses import dataclass as Dataclass
import math as MathValue
from typing import Any as AnyValue, Mapping
from interchange import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
    BrepWire,
    CircleCurve,
    CirclePcurve,
    ConeSurface,
    CylinderSurface,
    EllipseCurve,
    IntersectionCurve,
    LineCurve,
    LinePcurve,
    NativeCurve,
    NativePcurve,
    NativeSurface,
    NurbsCurve,
    NurbsPcurve,
    NurbsSurface,
    OffsetSurface,
    PlaneSurface,
    SphereSurface,
    TorusSurface,
    Transform,
    Vector2 as VectorTwo,
    Vector3 as VectorThree,
)
from convert.adapters.freecad.BrepGraph import (
    BindOnceMut,
    FreeCadBrep,
    ModelGraph,
    RequireOwned,
    Unsupported,
)

# this binding exists because shared behavior needs one stable value
KPoint = tuple[float, float, float]

# this binding exists because shared behavior needs one stable value
KTriangle = tuple[int, int, int]

# this binding exists because shared behavior needs one stable value
KGeomValue = tuple[
    tuple[KPoint, KPoint, KPoint], tuple[float, float, float], KPoint, KPoint, KPoint
]


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class ShapeRecord:
    locals().setdefault("__annotations__", {})
    __annotations__["key"] = "str"
    __annotations__["kind"] = "str"
    __annotations__["geometry"] = "tuple[str, ...]"
    __annotations__["flags"] = "str"
    __annotations__["children"] = "tuple[tuple[str, bool], ...]"


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class EdgePcurve:
    locals().setdefault("__annotations__", {})
    __annotations__["index"] = "int"
    __annotations__["first"] = "float"
    __annotations__["last"] = "float"


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class GeneratedPcurve:
    locals().setdefault("__annotations__", {})
    __annotations__["record"] = "str"
    __annotations__["first"] = "float"
    __annotations__["last"] = "float"
    __annotations__["start"] = "tuple[float, float]"
    __annotations__["end"] = "tuple[float, float]"


# this definition exists because focused behavior needs one stable owner
@Dataclass(frozen=True, slots=True)
class SeamBand:
    locals().setdefault("__annotations__", {})
    __annotations__["face_id"] = "str"
    __annotations__["loop_ids"] = "tuple[str, str]"
    __annotations__["low_coedge_id"] = "str"
    __annotations__["high_coedge_id"] = "str"
    __annotations__["low_reversed"] = "bool"
    __annotations__["high_reversed"] = "bool"
    __annotations__["low_vertex_id"] = "str"
    __annotations__["high_vertex_id"] = "str"
    __annotations__["curve_record"] = "str"
    __annotations__["length"] = "float"
    __annotations__["first_pcurve_index"] = "int"
    __annotations__["second_pcurve_index"] = "int"


# native write state stays immutable because every emission phase must share one proven index map
@Dataclass(frozen=True, slots=True)
class BrepWriteState:
    Graph: ModelGraph
    BaseCurveCount: int
    CurveRecords: tuple[tuple[str, float], ...]
    SurfaceRecords: tuple[str, ...]
    PcurveRecords: tuple[str, ...]
    EdgePcurves: Mapping[str, EdgePcurve]
    SeamBands: Mapping[str, SeamBand]
    LoopReversals: Mapping[str, bool]
    FaceUseReversals: Mapping[str, bool]
    ShellUseReversals: Mapping[str, bool]
    CurveIndexes: Mapping[str, int]
    CurveScales: Mapping[str, float]
    SurfaceIndexes: Mapping[str, int]
    HeaderLines: tuple[str, ...]


# this definition exists because focused behavior needs one stable owner
def Number(Value: float) -> str:
    if Value == 0.0:
        return "0"
    return format(Value, ".17g")


# this definition exists because focused behavior needs one stable owner
def Point(Value: Any) -> KPoint:
    if all((hasattr(Value, AxisValue) for AxisValue in ("x", "y", "z"))):
        Point = (float(Value.x), float(Value.y), float(Value.z))
    else:
        try:
            Point = tuple((float(Component) for Component in Value))
        except (TypeError, ValueError) as ErrorInfo:
            raise ValueError(
                "each vertex must contain three finite coordinates"
            ) from ErrorInfo
        if len(Point) != 3:
            raise ValueError("each vertex must contain three finite coordinates")
    if not all((MathValue.isfinite(Component) for Component in Point)):
        raise ValueError("each vertex must contain three finite coordinates")
    return Point


# this definition exists because focused behavior needs one stable owner
def Subtract(LeftValue: Point, Right: Point) -> KPoint:
    return tuple((LeftValue[Index] - Right[Index] for Index in range(3)))


# this definition exists because focused behavior needs one stable owner
def Cross(LeftValue: Point, Right: Point) -> KPoint:
    return (
        LeftValue[1] * Right[2] - LeftValue[2] * Right[1],
        LeftValue[2] * Right[0] - LeftValue[0] * Right[2],
        LeftValue[0] * Right[1] - LeftValue[1] * Right[0],
    )


# this definition exists because focused behavior needs one stable owner
def DotAction(LeftValue: Point, Right: Point) -> float:
    return sum((LeftValue[Index] * Right[Index] for Index in range(3)))


# this definition exists because focused behavior needs one stable owner
def GetLength(Vector: Point) -> float:
    return MathValue.sqrt(DotAction(Vector, Vector))


# this definition exists because focused behavior needs one stable owner
def ScaleVector(Vector: Point, Factor: float) -> KPoint:
    return tuple((Component * Factor for Component in Vector))


# this definition exists because focused behavior needs one stable owner
def Values(Values: Sequence[float]) -> str:
    return " ".join((Number(Value) for Value in Values))


# this definition exists because focused behavior needs one stable owner
def ParseTriangle(Value: Any, VertexCount: int) -> KTriangle:
    try:
        Indices = tuple(Value)
    except TypeError as ErrorInfo:
        raise ValueError(
            "each triangle must contain three vertex indices"
        ) from ErrorInfo
    if len(Indices) != 3 or any(
        (isinstance(Index, bool) or not isinstance(Index, int) for Index in Indices)
    ):
        raise ValueError("each triangle must contain three vertex indices")
    if len(set(Indices)) != 3 or any(
        (Index < 0 or Index >= VertexCount for Index in Indices)
    ):
        raise ValueError("triangle vertex indices must be distinct and in range")
    return Indices


# this definition exists because focused behavior needs one stable owner
def IsFacetBad(Points: tuple[Point, ...], Facet: Triangle, Tolerance: float) -> bool:
    Corners = tuple((Points[Index] for Index in Facet))
    Edges = tuple(
        (Subtract(Corners[(Index + 1) % 3], Corners[Index]) for Index in range(3))
    )
    Lengths = tuple((GetLength(EdgeValue) for EdgeValue in Edges))
    if min(Lengths) <= Tolerance:
        return True
    NormalLength = GetLength(Cross(Edges[0], Subtract(Corners[2], Corners[0])))
    return NormalLength <= Tolerance * max(Lengths)


# this definition exists because focused behavior needs one stable owner
def GeomAction(
    Points: tuple[Point, ...], Facets: tuple[Triangle, ...], Tolerance: float
):
    Result: list[KGeomValue] = []
    for Triangle in Facets:
        Corners = tuple((Points[Index] for Index in Triangle))
        Edges = tuple(
            (Subtract(Corners[(Index + 1) % 3], Corners[Index]) for Index in range(3))
        )
        Lengths = tuple((GetLength(EdgeValue) for EdgeValue in Edges))
        if min(Lengths) <= Tolerance:
            raise ValueError("triangle edges must exceed the BRep tolerance")
        NormalVector = Cross(Edges[0], Subtract(Corners[2], Corners[0]))
        NormalLength = GetLength(NormalVector)
        if NormalLength <= Tolerance * max(Lengths):
            raise ValueError("triangle area must exceed the BRep tolerance")
        Normal = ScaleVector(NormalVector, 1.0 / NormalLength)
        XDirection = ScaleVector(Edges[0], 1.0 / Lengths[0])
        YDirection = Cross(Normal, XDirection)
        Result.append((Corners, Lengths, Normal, XDirection, YDirection))
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def EdgeUses(Facets: tuple[Triangle, ...]):
    Result: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for FacetIndex, Facet in enumerate(Facets):
        for Index in range(3):
            PairValue = (Facet[Index], Facet[(Index + 1) % 3])
            KeyValue = tuple(sorted(PairValue))
            Result.setdefault(KeyValue, []).append(
                (FacetIndex, 1 if PairValue == KeyValue else -1)
            )
    return Result


# facet adjacency stays isolated because manifold validation precedes orientation traversal
def BuildNeighbors(Facets: tuple[Triangle, ...]):
    UsesValue = EdgeUses(Facets)
    if any(len(EdgeFaces) > 2 for EdgeFaces in UsesValue.values()):
        return None
    Neighbors: dict[int, list[tuple[int, int]]] = {
        Index: [] for Index in range(len(Facets))
    }
    for EdgeFaces in UsesValue.values():
        if len(EdgeFaces) != 2:
            continue
        (LeftValue, LeftSign), (Right, RightSign) = EdgeFaces
        Relation = -LeftSign * RightSign
        Neighbors[LeftValue].append((Right, Relation))
        Neighbors[Right].append((LeftValue, Relation))
    return Neighbors


# component traversal stays isolated because contradictory facet parity invalidates the whole mesh
def GetComponents(FacetCount: int, Neighbors: Mapping[int, list[tuple[int, int]]]):
    Flips = [0] * FacetCount
    Components: list[tuple[int, ...]] = []
    for StartIndex in range(FacetCount):
        if Flips[StartIndex]:
            continue
        Flips[StartIndex] = 1
        Pending = Deque([StartIndex])
        Component: list[int] = []
        while Pending:
            CurrentIndex = Pending.popleft()
            Component.append(CurrentIndex)
            for NeighborIndex, Relation in Neighbors[CurrentIndex]:
                Expected = Flips[CurrentIndex] * Relation
                if Flips[NeighborIndex] and Flips[NeighborIndex] != Expected:
                    return None
                if not Flips[NeighborIndex]:
                    Flips[NeighborIndex] = Expected
                    Pending.append(NeighborIndex)
        Components.append(tuple(sorted(Component)))
    return Flips, tuple(Components)


# parity application mutates one working copy because input facet order must remain untouched
def ApplyFlipsMut(Oriented: list[Triangle], Flips: list[int]) -> None:
    for Index, FlipValue in enumerate(Flips):
        if FlipValue < 0:
            LeftValue, Middle, Right = Oriented[Index]
            Oriented[Index] = (LeftValue, Right, Middle)


# closure classification mutates orientation because negative closed volumes must face outward
def GetClosedMut(
    Points: tuple[Point, ...],
    Oriented: list[Triangle],
    Components: tuple[tuple[int, ...], ...],
    Tolerance: float,
) -> tuple[bool, ...]:
    ComponentByFacet = [0] * len(Oriented)
    for ComponentIndex, Component in enumerate(Components):
        for FacetIndex in Component:
            ComponentByFacet[FacetIndex] = ComponentIndex
    Closed = [True] * len(Components)
    for EdgeFaces in EdgeUses(tuple(Oriented)).values():
        if len(EdgeFaces) != 2:
            for FacetIndex, Ignored in EdgeFaces:
                Closed[ComponentByFacet[FacetIndex]] = False
    for ComponentIndex, Component in enumerate(Components):
        IsClosed = Closed[ComponentIndex]
        if IsClosed:
            Volume = (
                sum(
                    (
                        DotAction(
                            Points[Oriented[Index][0]],
                            Cross(
                                Points[Oriented[Index][1]],
                                Points[Oriented[Index][2]],
                            ),
                        )
                        for Index in Component
                    )
                )
                / 6.0
            )
            if abs(Volume) <= Tolerance**3:
                IsClosed = False
            elif Volume < 0.0:
                for Index in Component:
                    LeftValue, Middle, Right = Oriented[Index]
                    Oriented[Index] = (LeftValue, Right, Middle)
        Closed[ComponentIndex] = IsClosed
    return tuple(Closed)


# facet orientation composes adjacency parity and volume phases because each has one failure mode
def OrientFacets(
    Points: tuple[Point, ...], Facets: tuple[Triangle, ...], Tolerance: float
):
    Neighbors = BuildNeighbors(Facets)
    if Neighbors is None:
        return None
    ComponentData = GetComponents(len(Facets), Neighbors)
    if ComponentData is None:
        return None
    Flips, Components = ComponentData
    Oriented = list(Facets)
    ApplyFlipsMut(Oriented, Flips)
    Closed = GetClosedMut(Points, Oriented, Components, Tolerance)
    return (tuple(Oriented), tuple(Components), tuple(Closed))


# this definition exists because focused behavior needs one stable owner
def Header(
    Points: tuple[Point, ...],
    Facets: tuple[Triangle, ...],
    Edges: tuple[tuple[int, int], ...],
    GeomValue: tuple[Geometry, ...],
):
    Lines = [
        "DBRep_DrawableShape",
        "",
        "CASCADE Topology V1, (c) Matra-Datavision",
        "Locations 0",
        "Curve2ds 0",
        f"Curves {len(Edges)}",
    ]
    for Start, EndValue in Edges:
        Vector = Subtract(Points[EndValue], Points[Start])
        Direction = ScaleVector(Vector, 1.0 / GetLength(Vector))
        Lines.append(f"1 {Values(Points[Start] + Direction)} ")
    Lines.extend(
        ["Polygon3D 0", "PolygonOnTriangulations 0", f"Surfaces {len(Facets)}"]
    )
    for Corners, Ignored, Normal, XDirection, YDirection in GeomValue:
        Lines.append(f"1 {Values(Corners[0] + Normal + XDirection + YDirection)} ")
    Lines.extend(["Triangulations 0", ""])
    return Lines


# this definition exists because focused behavior needs one stable owner
def VertexRecord(Point: Point, Tolerance: str) -> list[str]:
    return ["Ve", Tolerance, Values(Point), "0 0", "", "0101101", "*"]


# this definition exists because focused behavior needs one stable owner
def EdgeRecord(
    Tolerance: str, CurveIndex: int, Length: float, Start: int, EndValue: int
) -> list[str]:
    return [
        "Ed",
        f" {Tolerance} 1 1 0",
        f"1  {CurveIndex} 0 0 {Number(Length)}",
        "0",
        "",
        "0101000",
        f"+{Start} 0 -{EndValue} 0 *",
    ]


# shape counting stays isolated because topology references depend on one exact record total
def GetShapeCount(
    VertexCount: int,
    EdgeCount: int,
    FacetCount: int,
    ComponentCount: int,
    Closed: tuple[bool, ...],
) -> int:
    return (
        VertexCount
        + EdgeCount
        + 2 * FacetCount
        + ComponentCount
        + sum(Closed)
        + int(ComponentCount > 1)
    )


# ordinal allocation stays isolated because every native record reference uses reverse numbering
def BuildOrdinals(
    VertexIndices: tuple[int, ...],
    Edges: tuple[tuple[int, int], ...],
    FacetCount: int,
    Components: tuple[tuple[int, ...], ...],
    Closed: tuple[bool, ...],
):
    Ordinal = 1
    VertexOrdinals: dict[int, int] = {}
    for Index in VertexIndices:
        VertexOrdinals[Index] = Ordinal
        Ordinal += 1
    EdgeOrdinals: dict[tuple[int, int], int] = {}
    for EdgeValue in Edges:
        EdgeOrdinals[EdgeValue] = Ordinal
        Ordinal += 1
    WireOrdinals = tuple(range(Ordinal, Ordinal + 2 * FacetCount, 2))
    FaceOrdinals = tuple(Value + 1 for Value in WireOrdinals)
    Ordinal += 2 * FacetCount
    ShellOrdinals = tuple(range(Ordinal, Ordinal + len(Components)))
    Ordinal += len(Components)
    SolidOrdinals: dict[int, int] = {}
    for ComponentIndex, IsClosed in enumerate(Closed):
        if IsClosed:
            SolidOrdinals[ComponentIndex] = Ordinal
            Ordinal += 1
    Ordinal += int(len(Components) > 1)
    ShapeCount = GetShapeCount(
        len(VertexIndices), len(Edges), FacetCount, len(Components), Closed
    )
    if Ordinal != ShapeCount + 1:
        raise ValueError("BRep topology record count is inconsistent")
    return (
        VertexOrdinals,
        EdgeOrdinals,
        WireOrdinals,
        FaceOrdinals,
        ShellOrdinals,
        SolidOrdinals,
        ShapeCount,
    )


# reverse references stay centralized because native shape records are numbered from the tail
def GetRecordRef(ShapeCount: int, RecordNum: int) -> int:
    return ShapeCount - RecordNum + 1


# vertex and edge emission stays isolated because geometric records precede all topology parents
def AddBaseLinesMut(
    Lines: list[str],
    Points: tuple[Point, ...],
    VertexIndices: tuple[int, ...],
    Edges: tuple[tuple[int, int], ...],
    VertexOrdinals: Mapping[int, int],
    ShapeCount: int,
    ToleranceText: str,
) -> None:
    for Index in VertexIndices:
        Lines.extend(VertexRecord(Points[Index], ToleranceText))
    for CurveIndex, EdgeValue in enumerate(Edges, 1):
        Start, EndValue = EdgeValue
        Lines.extend(
            EdgeRecord(
                ToleranceText,
                CurveIndex,
                GetLength(Subtract(Points[EndValue], Points[Start])),
                GetRecordRef(ShapeCount, VertexOrdinals[Start]),
                GetRecordRef(ShapeCount, VertexOrdinals[EndValue]),
            )
        )


# facet emission stays isolated because each triangle owns one wire and one face record
def AddFacetsMut(
    Lines: list[str],
    Facets: tuple[Triangle, ...],
    EdgeOrdinals: Mapping[tuple[int, int], int],
    WireOrdinals: tuple[int, ...],
    ShapeCount: int,
    ToleranceText: str,
) -> None:
    for FacetIndex, Facet in enumerate(Facets):
        EdgeValues: list[str] = []
        for Index in range(3):
            PairValue = (Facet[Index], Facet[(Index + 1) % 3])
            EdgeValue = tuple(sorted(PairValue))
            SignValue = "+" if PairValue == EdgeValue else "-"
            RecordRef = GetRecordRef(ShapeCount, EdgeOrdinals[EdgeValue])
            EdgeValues.append(f"{SignValue}{RecordRef} 0")
        Lines.extend(
            [
                "Wi",
                "",
                "0101100",
                " ".join(EdgeValues) + " *",
                "Fa",
                f"0  {ToleranceText} {FacetIndex + 1} 0",
                "",
                "0101000",
                f"+{GetRecordRef(ShapeCount, WireOrdinals[FacetIndex])} 0 *",
            ]
        )


# shell emission stays isolated because each connected component owns one closure flag
def AddShellsMut(
    Lines: list[str],
    Components: tuple[tuple[int, ...], ...],
    Closed: tuple[bool, ...],
    FaceOrdinals: tuple[int, ...],
    ShapeCount: int,
) -> None:
    for ComponentIndex, Component in enumerate(Components):
        FaceRefs = " ".join(
            f"+{GetRecordRef(ShapeCount, FaceOrdinals[Index])} 0" for Index in Component
        )
        Lines.extend(
            [
                "Sh",
                "",
                "0101100" if Closed[ComponentIndex] else "0101000",
                FaceRefs + " *",
            ]
        )


# root emission stays isolated because solids and compounds depend only on component closure
def AddRootLinesMut(
    Lines: list[str],
    ComponentCount: int,
    SolidOrdinals: Mapping[int, int],
    ShellOrdinals: tuple[int, ...],
    ShapeCount: int,
) -> None:
    for ComponentIndex in SolidOrdinals:
        Lines.extend(
            [
                "So",
                "",
                "1100000" if ComponentCount == 1 else "0100000",
                f"+{GetRecordRef(ShapeCount, ShellOrdinals[ComponentIndex])} 0 *",
            ]
        )
    if ComponentCount > 1:
        Roots = [
            SolidOrdinals.get(Index, ShellOrdinals[Index])
            for Index in range(ComponentCount)
        ]
        RootRefs = " ".join(
            f"+{GetRecordRef(ShapeCount, RecordNum)} 0" for RecordNum in Roots
        )
        Lines.extend(["Co", "", "1100000", RootRefs + " *"])


# shared mesh writing composes focused record phases because ordering defines every native reference
def SharedBrep(
    Points: tuple[Point, ...],
    Facets: tuple[Triangle, ...],
    Components: tuple[tuple[int, ...], ...],
    Closed: tuple[bool, ...],
    Tolerance: float,
) -> bytes:
    GeomValue = GeomAction(Points, Facets, Tolerance)
    VertexIndices = tuple(sorted({Index for Facet in Facets for Index in Facet}))
    Edges = tuple(sorted(EdgeUses(Facets)))
    OrdinalData = BuildOrdinals(VertexIndices, Edges, len(Facets), Components, Closed)
    VertexOrdinals, EdgeOrdinals, WireOrdinals = OrdinalData[:3]
    FaceOrdinals, ShellOrdinals, SolidOrdinals, ShapeCount = OrdinalData[3:]
    ToleranceText = Number(Tolerance)
    Lines = Header(Points, Facets, Edges, GeomValue)
    Lines.append(f"TShapes {ShapeCount}")
    AddBaseLinesMut(
        Lines,
        Points,
        VertexIndices,
        Edges,
        VertexOrdinals,
        ShapeCount,
        ToleranceText,
    )
    AddFacetsMut(Lines, Facets, EdgeOrdinals, WireOrdinals, ShapeCount, ToleranceText)
    AddShellsMut(Lines, Components, Closed, FaceOrdinals, ShapeCount)
    AddRootLinesMut(Lines, len(Components), SolidOrdinals, ShellOrdinals, ShapeCount)
    Lines.extend(["", "+1 0 "])
    return ("\n".join(Lines) + "\n").encode("ascii")


# this definition exists because focused behavior needs one stable owner
def IndependentBrep(
    Points: tuple[Point, ...], Facets: tuple[Triangle, ...], Tolerance: float
) -> bytes:
    GeomValue = GeomAction(Points, Facets, Tolerance)
    DirectedEdges = tuple(
        (
            (Facet[Index], Facet[(Index + 1) % 3])
            for Facet in Facets
            for Index in range(3)
        )
    )
    Lines = Header(Points, Facets, DirectedEdges, GeomValue)
    ShapeCount = len(Facets) * 8 + 1
    Lines.append(f"TShapes {ShapeCount}")
    ToleranceText = Number(Tolerance)
    FaceReferences = []
    CurveIndex = 1
    RecordIndex = 1
    for Facet, FacetGeom in zip(Facets, GeomValue):
        Corners, Lengths, Ignored, Ignored, Ignored = FacetGeom
        References = tuple(
            (ShapeCount - (RecordIndex + Offset) + 1 for Offset in range(8))
        )
        VertexReferences = (References[0], References[1], References[3])
        Lines.extend(VertexRecord(Corners[0], ToleranceText))
        Lines.extend(VertexRecord(Corners[1], ToleranceText))
        Lines.extend(
            EdgeRecord(
                ToleranceText,
                CurveIndex,
                Lengths[0],
                VertexReferences[0],
                VertexReferences[1],
            )
        )
        CurveIndex += 1
        Lines.extend(VertexRecord(Corners[2], ToleranceText))
        for EdgeIndex in (1, 2):
            Lines.extend(
                EdgeRecord(
                    ToleranceText,
                    CurveIndex,
                    Lengths[EdgeIndex],
                    VertexReferences[EdgeIndex],
                    VertexReferences[(EdgeIndex + 1) % 3],
                )
            )
            CurveIndex += 1
        Lines.extend(
            [
                "Wi",
                "",
                "0101100",
                f"+{References[2]} 0 +{References[4]} 0 +{References[5]} 0 *",
                "Fa",
                f"0  {ToleranceText} {(RecordIndex - 1) // 8 + 1} 0",
                "",
                "0101000",
                f"+{References[6]} 0 *",
            ]
        )
        FaceReferences.append(References[7])
        RecordIndex += 8
    Lines.extend(
        [
            "Co",
            "",
            "1100000",
            " ".join((f"+{RefValue} 0" for RefValue in FaceReferences)) + " *",
            "",
            "+1 0 ",
        ]
    )
    return ("\n".join(Lines) + "\n").encode("ascii")


# this definition exists because focused behavior needs one stable owner
def VectorTwoA(Value: Vector2) -> tuple[float, float]:
    return (Value.x, Value.y)


# this definition exists because focused behavior needs one stable owner
def VectorThreeA(Value: Vector3) -> KPoint:
    return (Value.x, Value.y, Value.z)


# this definition exists because focused behavior needs one stable owner
def UnitTwo(Value: Vector2, Label: str) -> tuple[tuple[float, float], float]:
    Length = MathValue.hypot(Value.x, Value.y)
    if not MathValue.isfinite(Length) or Length <= 0.0:
        Unsupported(f"{Label} has an invalid direction")
    return ((Value.x / Length, Value.y / Length), Length)


# this definition exists because focused behavior needs one stable owner
def UnitThree(Value: Vector3, Label: str) -> tuple[KPoint, float]:
    RawValue = VectorThreeA(Value)
    Length = GetLength(RawValue)
    if not MathValue.isfinite(Length) or Length <= 0.0:
        Unsupported(f"{Label} has an invalid direction")
    return (ScaleVector(RawValue, 1.0 / Length), Length)


# this definition exists because focused behavior needs one stable owner
def Frame(
    AxisValue: Vector3, RefValue: Vector3, Label: str
) -> tuple[KPoint, KPoint, KPoint]:
    NormalizedAxis, Ignored = UnitThree(AxisValue, Label)
    NormalizedRef, Ignored = UnitThree(RefValue, Label)
    if abs(DotAction(NormalizedAxis, NormalizedRef)) > 1e-09:
        Unsupported(f"{Label} axis and reference direction are not orthogonal")
    YDirection = Cross(NormalizedAxis, NormalizedRef)
    if abs(GetLength(YDirection) - 1.0) > 1e-09:
        Unsupported(f"{Label} has an invalid coordinate frame")
    return (NormalizedAxis, NormalizedRef, YDirection)


# this definition exists because focused behavior needs one stable owner
def BsplineLayout(
    Degree: int,
    PoleCount: int,
    Knots: Sequence[float],
    Multiplicities: Sequence[int],
    Periodic: bool,
    Label: str,
) -> None:
    if (
        type(Degree) is not int
        or not 0 < Degree <= 25
        or PoleCount < 2
        or (len(Knots) != len(Multiplicities))
        or (len(Knots) < 2)
        or any((not MathValue.isfinite(Value) for Value in Knots))
        or any((LeftValue >= Right for LeftValue, Right in zip(Knots, Knots[1:])))
    ):
        Unsupported(f"{Label} has an invalid B-spline layout")
    for Index, Value in enumerate(Multiplicities):
        Maximum = Degree
        if not Periodic and Index in {0, len(Multiplicities) - 1}:
            Maximum = Degree + 1
        if type(Value) is not int or not 1 <= Value <= Maximum:
            Unsupported(f"{Label} has an invalid knot multiplicity")
    if Periodic:
        if Multiplicities[0] != Multiplicities[-1]:
            Unsupported(f"{Label} has inconsistent periodic multiplicities")
        Expected = sum(Multiplicities[:-1])
    else:
        Expected = sum(Multiplicities) - Degree - 1
    if Expected != PoleCount:
        Unsupported(f"{Label} pole and knot counts are inconsistent")


# this definition exists because focused behavior needs one stable owner
def CurveRecord(Value: object) -> tuple[str, float]:
    if isinstance(Value, LineCurve):
        Direction, Scale = UnitThree(Value.direction, f"line curve {Value.id}")
        return (f"1 {Values(VectorThreeA(Value.origin) + Direction)} ", Scale)
    if isinstance(Value, CircleCurve):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"circle curve {Value.id}"
        )
        return (
            f"2 {Values(VectorThreeA(Value.center) + AxisValue + RefValue + YDirection + (Value.radius,))} ",
            1.0,
        )
    if isinstance(Value, EllipseCurve):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"ellipse curve {Value.id}"
        )
        return (
            f"3 {Values(VectorThreeA(Value.center) + AxisValue + RefValue + YDirection + (Value.major_radius, Value.minor_radius))} ",
            1.0,
        )
    if isinstance(Value, NurbsCurve):
        BsplineLayout(
            Value.degree,
            len(Value.control_points),
            Value.knots,
            Value.multiplicities,
            Value.periodic,
            f"NURBS curve {Value.id}",
        )
        Rational = bool(Value.weights)
        if Rational and (
            len(Value.weights) != len(Value.control_points)
            or any(
                (
                    not MathValue.isfinite(Weight) or Weight <= 0.0
                    for Weight in Value.weights
                )
            )
        ):
            Unsupported(f"NURBS curve {Value.id} has invalid weights")
        Fields = [
            "7",
            "1" if Rational else "0",
            "1" if Value.periodic else "0",
            str(Value.degree),
            str(len(Value.control_points)),
            str(len(Value.knots)),
        ]
        for Index, Point in enumerate(Value.control_points):
            Fields.extend((Number(Component) for Component in VectorThreeA(Point)))
            if Rational:
                Fields.append(Number(Value.weights[Index]))
        for KnotValue, Multiplicity in zip(Value.knots, Value.multiplicities):
            Fields.extend((Number(KnotValue), str(Multiplicity)))
        return (" ".join(Fields) + " ", 1.0)
    if isinstance(Value, (IntersectionCurve, NativeCurve)):
        Unsupported(f"curve {Value.id} of type {type(Value).__name__} is unsupported")
    Unsupported(f"curve type {type(Value).__name__} is unsupported")


# this definition exists because focused behavior needs one stable owner
def PcurveRecord(Value: object) -> tuple[str, float]:
    if isinstance(Value, LinePcurve):
        Direction, Scale = UnitTwo(Value.direction, f"line pcurve {Value.id}")
        return (f"1 {Values(VectorTwoA(Value.origin) + Direction)} ", Scale)
    if isinstance(Value, CirclePcurve):
        return (
            f"2 {Values(VectorTwoA(Value.center) + (1.0, 0.0, 0.0, 1.0, Value.radius))} ",
            1.0,
        )
    if isinstance(Value, NurbsPcurve):
        BsplineLayout(
            Value.degree,
            len(Value.control_points),
            Value.knots,
            Value.multiplicities,
            Value.periodic,
            f"NURBS pcurve {Value.id}",
        )
        Rational = bool(Value.weights)
        if Rational and (
            len(Value.weights) != len(Value.control_points)
            or any(
                (
                    not MathValue.isfinite(Weight) or Weight <= 0.0
                    for Weight in Value.weights
                )
            )
        ):
            Unsupported(f"NURBS pcurve {Value.id} has invalid weights")
        Fields = [
            "7",
            "1" if Rational else "0",
            "1" if Value.periodic else "0",
            str(Value.degree),
            str(len(Value.control_points)),
            str(len(Value.knots)),
        ]
        for Index, Point in enumerate(Value.control_points):
            Fields.extend((Number(Component) for Component in VectorTwoA(Point)))
            if Rational:
                Fields.append(Number(Value.weights[Index]))
        for KnotValue, Multiplicity in zip(Value.knots, Value.multiplicities):
            Fields.extend((Number(KnotValue), str(Multiplicity)))
        return (" ".join(Fields) + " ", 1.0)
    if isinstance(Value, NativePcurve):
        Unsupported(f"pcurve {Value.id} of type NativePcurve is unsupported")
    Unsupported(f"pcurve type {type(Value).__name__} is unsupported")


# elementary surface encoding stays isolated because analytic frames share one compact dispatch
def EncodeBasic(Value: object) -> str | None:
    if isinstance(Value, PlaneSurface):
        AxisValue, RefValue, YDirection = Frame(
            Value.normal, Value.reference_direction, f"plane surface {Value.id}"
        )
        return f"1 {Values(VectorThreeA(Value.origin) + AxisValue + RefValue + YDirection)} "
    if isinstance(Value, CylinderSurface):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"cylinder surface {Value.id}"
        )
        return f"2 {Values(VectorThreeA(Value.origin) + AxisValue + RefValue + YDirection + (Value.radius,))} "
    if isinstance(Value, ConeSurface):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"cone surface {Value.id}"
        )
        if not 0.0 < abs(Value.half_angle) < MathValue.pi / 2.0:
            Unsupported(f"cone surface {Value.id} has an invalid half angle")
        return f"3 {Values(VectorThreeA(Value.origin) + AxisValue + RefValue + YDirection + (Value.radius, Value.half_angle))} "
    if isinstance(Value, SphereSurface):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"sphere surface {Value.id}"
        )
        return f"4 {Values(VectorThreeA(Value.center) + AxisValue + RefValue + YDirection + (Value.radius,))} "
    if isinstance(Value, TorusSurface):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"torus surface {Value.id}"
        )
        if Value.major_radius < 0.0:
            Unsupported(f"torus surface {Value.id} has a negative major radius")
        return f"5 {Values(VectorThreeA(Value.center) + AxisValue + RefValue + YDirection + (Value.major_radius, Value.minor_radius))} "
    return None


# nurbs validation stays isolated because pole knot and weight dimensions form one invariant
def GetNurbsShape(Value: NurbsSurface) -> tuple[int, int, bool]:
    UCount = len(Value.control_points)
    VCount = len(Value.control_points[0]) if Value.control_points else 0
    if (
        not UCount
        or not VCount
        or any(len(RowValue) != VCount for RowValue in Value.control_points)
    ):
        Unsupported(f"NURBS surface {Value.id} has an invalid pole grid")
    BsplineLayout(
        Value.degree_u,
        UCount,
        Value.knots_u,
        Value.multiplicities_u,
        Value.periodic_u,
        f"NURBS surface {Value.id} U direction",
    )
    BsplineLayout(
        Value.degree_v,
        VCount,
        Value.knots_v,
        Value.multiplicities_v,
        Value.periodic_v,
        f"NURBS surface {Value.id} V direction",
    )
    IsRational = bool(Value.weights)
    HasBadWeights = (
        len(Value.weights) != UCount
        or any(len(RowValue) != VCount for RowValue in Value.weights)
        or any(
            not MathValue.isfinite(Weight) or Weight <= 0.0
            for RowValue in Value.weights
            for Weight in RowValue
        )
    )
    if IsRational and HasBadWeights:
        Unsupported(f"NURBS surface {Value.id} has invalid weights")
    return UCount, VCount, IsRational


# nurbs encoding stays isolated because validated poles and knot vectors have deterministic order
def EncodeNurbs(Value: NurbsSurface) -> str:
    UCount, VCount, IsRational = GetNurbsShape(Value)
    Fields = [
        "9",
        "1" if IsRational else "0",
        "1" if IsRational else "0",
        "1" if Value.periodic_u else "0",
        "1" if Value.periodic_v else "0",
        str(Value.degree_u),
        str(Value.degree_v),
        str(UCount),
        str(VCount),
        str(len(Value.knots_u)),
        str(len(Value.knots_v)),
    ]
    for UIndex, RowValue in enumerate(Value.control_points):
        for VIndex, PointValue in enumerate(RowValue):
            Fields.extend(Number(Component) for Component in VectorThreeA(PointValue))
            if IsRational:
                Fields.append(Number(Value.weights[UIndex][VIndex]))
    for KnotValue, Multiplicity in zip(Value.knots_u, Value.multiplicities_u):
        Fields.extend((Number(KnotValue), str(Multiplicity)))
    for KnotValue, Multiplicity in zip(Value.knots_v, Value.multiplicities_v):
        Fields.extend((Number(KnotValue), str(Multiplicity)))
    return " ".join(Fields) + " "


# surface dispatch stays small because each representation owns its focused encoder and validation
def SurfaceRecord(
    Value: object, Surfaces: Mapping[str, object], Active: frozenset[str] = frozenset()
) -> str:
    BasicRecord = EncodeBasic(Value)
    if BasicRecord is not None:
        return BasicRecord
    if isinstance(Value, NurbsSurface):
        return EncodeNurbs(Value)
    if isinstance(Value, OffsetSurface):
        if Value.id in Active:
            Unsupported(f"offset surface {Value.id} has a cyclic basis")
        BaseValue = Surfaces.get(Value.base_surface_id)
        if BaseValue is None:
            Unsupported(f"offset surface {Value.id} has no basis surface")
        Nested = SurfaceRecord(BaseValue, Surfaces, Active | {Value.id})
        return f"11 {Number(Value.distance)} {Nested}"
    if isinstance(Value, NativeSurface):
        Unsupported(f"surface {Value.id} of type NativeSurface is unsupported")
    Unsupported(f"surface type {type(Value).__name__} is unsupported")


# this definition exists because focused behavior needs one stable owner
def CurvePoint(Value: object, Param: float) -> KPoint | None:
    if isinstance(Value, LineCurve):
        return tuple(
            (
                Origin + Param * Direction
                for Origin, Direction in zip(
                    VectorThreeA(Value.origin), VectorThreeA(Value.direction)
                )
            )
        )
    if isinstance(Value, (CircleCurve, EllipseCurve)):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"curve {Value.id}"
        )
        Major = Value.radius if isinstance(Value, CircleCurve) else Value.major_radius
        Minor = Value.radius if isinstance(Value, CircleCurve) else Value.minor_radius
        Center = VectorThreeA(Value.center)
        return tuple(
            (
                Center[Index]
                + Major * MathValue.cos(Param) * RefValue[Index]
                + Minor * MathValue.sin(Param) * YDirection[Index]
                for Index in range(3)
            )
        )
    return None


# this definition exists because focused behavior needs one stable owner
def SurfacePeriods(Value: object) -> tuple[float | None, float | None]:
    if isinstance(Value, (CylinderSurface, ConeSurface, SphereSurface)):
        return (MathValue.tau, None)
    if isinstance(Value, TorusSurface):
        return (MathValue.tau, MathValue.tau)
    return (None, None)


# this definition exists because focused behavior needs one stable owner
def UnwrapPeriodic(
    Values: Sequence[tuple[float, float]], Periods: tuple[float | None, float | None]
) -> tuple[tuple[float, float], ...]:
    if not Values:
        return ()
    Result = [Values[0]]
    for Value in Values[1:]:
        Adjusted = list(Value)
        Previous = Result[-1]
        for AxisValue, Period in enumerate(Periods):
            if Period is None:
                continue
            Adjusted[AxisValue] += (
                round((Previous[AxisValue] - Adjusted[AxisValue]) / Period) * Period
            )
        Result.append((Adjusted[0], Adjusted[1]))
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def UnwrapSurfaceUv(
    Values: Sequence[tuple[float, float]], Surface: object
) -> tuple[tuple[float, float], ...]:
    if not isinstance(Surface, SphereSurface) or not Values:
        return UnwrapPeriodic(Values, SurfacePeriods(Surface))
    Resolved = list(Values)
    for Index, (UValue, VValue) in enumerate(Resolved):
        if abs(abs(VValue) - MathValue.pi / 2.0) > 1e-10:
            continue
        Neighbor = next(
            (
                Resolved[Choice][0]
                for Distance in range(1, len(Resolved))
                for Choice in (Index - Distance, Index + Distance)
                if 0 <= Choice < len(Resolved)
                and abs(abs(Resolved[Choice][1]) - MathValue.pi / 2.0) > 1e-10
            ),
            UValue,
        )
        Resolved[Index] = (Neighbor, VValue)
    Result = [Resolved[0]]
    for UValue, VValue in Resolved[1:]:
        Candidates = []
        for UTurn in range(-3, 4):
            ChoiceU = UValue + UTurn * MathValue.pi
            BaseV = VValue if UTurn % 2 == 0 else MathValue.pi - VValue
            for VTurn in range(-2, 3):
                Candidates.append((ChoiceU, BaseV + VTurn * MathValue.tau))
        Previous = Result[-1]

        # this callback exists because local behavior needs one focused transformation
        Result.append(
            min(
                Candidates,
                key=lambda Value: (Value[0] - Previous[0]) ** 2
                + (Value[1] - Previous[1]) ** 2,
            )
        )
    return tuple(Result)


# this definition exists because focused behavior needs one stable owner
def SurfaceUv(Value: object, Point: Point) -> tuple[float, float] | None:
    if isinstance(Value, PlaneSurface):
        AxisValue, RefValue, YDirection = Frame(
            Value.normal, Value.reference_direction, f"plane surface {Value.id}"
        )
        Delta = Subtract(Point, VectorThreeA(Value.origin))
        return (DotAction(Delta, RefValue), DotAction(Delta, YDirection))
    if isinstance(Value, (CylinderSurface, ConeSurface)):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"surface {Value.id}"
        )
        Delta = Subtract(Point, VectorThreeA(Value.origin))
        FirstParam = MathValue.atan2(
            DotAction(Delta, YDirection), DotAction(Delta, RefValue)
        )
        if isinstance(Value, CylinderSurface):
            return (FirstParam, DotAction(Delta, AxisValue))
        Cosine = MathValue.cos(Value.half_angle)
        if abs(Cosine) <= 1e-15:
            return None
        return (FirstParam, DotAction(Delta, AxisValue) / Cosine)
    if isinstance(Value, SphereSurface):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"sphere surface {Value.id}"
        )
        Delta = Subtract(Point, VectorThreeA(Value.center))
        return (
            MathValue.atan2(DotAction(Delta, YDirection), DotAction(Delta, RefValue)),
            MathValue.atan2(
                DotAction(Delta, AxisValue),
                MathValue.hypot(
                    DotAction(Delta, RefValue), DotAction(Delta, YDirection)
                ),
            ),
        )
    if isinstance(Value, TorusSurface):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"torus surface {Value.id}"
        )
        Delta = Subtract(Point, VectorThreeA(Value.center))
        XValue = DotAction(Delta, RefValue)
        YValue = DotAction(Delta, YDirection)
        ZValue = DotAction(Delta, AxisValue)
        return (
            MathValue.atan2(YValue, XValue),
            MathValue.atan2(
                ZValue, MathValue.hypot(XValue, YValue) - Value.major_radius
            ),
        )
    return None


# this definition exists because focused behavior needs one stable owner
def SurfaceResidual(Value: object, Point: Point) -> float | None:
    if isinstance(Value, PlaneSurface):
        AxisValue, Ignored, Ignored = Frame(
            Value.normal, Value.reference_direction, f"plane surface {Value.id}"
        )
        return abs(DotAction(Subtract(Point, VectorThreeA(Value.origin)), AxisValue))
    if isinstance(Value, (CylinderSurface, ConeSurface)):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"surface {Value.id}"
        )
        Delta = Subtract(Point, VectorThreeA(Value.origin))
        Radial = MathValue.hypot(
            DotAction(Delta, RefValue), DotAction(Delta, YDirection)
        )
        Axial = DotAction(Delta, AxisValue)
        if isinstance(Value, CylinderSurface):
            return abs(Radial - Value.radius)
        Cosine = MathValue.cos(Value.half_angle)
        if abs(Cosine) <= 1e-15:
            return None
        Expected = Value.radius + Axial / Cosine * MathValue.sin(Value.half_angle)
        return abs(Radial - abs(Expected))
    if isinstance(Value, SphereSurface):
        return abs(
            GetLength(Subtract(Point, VectorThreeA(Value.center))) - Value.radius
        )
    if isinstance(Value, TorusSurface):
        AxisValue, RefValue, YDirection = Frame(
            Value.axis, Value.reference_direction, f"torus surface {Value.id}"
        )
        Delta = Subtract(Point, VectorThreeA(Value.center))
        Radial = MathValue.hypot(
            DotAction(Delta, RefValue), DotAction(Delta, YDirection)
        )
        Axial = DotAction(Delta, AxisValue)
        return abs(
            MathValue.hypot(Radial - Value.major_radius, Axial) - Value.minor_radius
        )
    return None


# this definition exists because focused behavior needs one stable owner
def PlaneConic(
    Curve: object, Surface: PlaneSurface, EdgeValue: BrepEdge, Tolerance: float
) -> GeneratedPcurve | None:
    if not isinstance(Curve, (CircleCurve, EllipseCurve)):
        return None
    Normal, SurfaceX, SurfaceY = Frame(
        Surface.normal, Surface.reference_direction, f"plane surface {Surface.id}"
    )
    CurveAxis, CurveX, CurveY = Frame(
        Curve.axis, Curve.reference_direction, f"curve {Curve.id}"
    )
    Allowed = max(Tolerance, EdgeValue.tolerance, 1e-07) * 10.0
    if abs(abs(DotAction(Normal, CurveAxis)) - 1.0) > Allowed:
        return None
    Center = SurfaceUv(Surface, VectorThreeA(Curve.center))
    if Center is None:
        return None
    XDirection = (DotAction(CurveX, SurfaceX), DotAction(CurveX, SurfaceY))
    YDirection = (DotAction(CurveY, SurfaceX), DotAction(CurveY, SurfaceY))
    if (
        abs(MathValue.hypot(*XDirection) - 1.0) > Allowed
        or abs(MathValue.hypot(*YDirection) - 1.0) > Allowed
        or abs(XDirection[0] * YDirection[0] + XDirection[1] * YDirection[1]) > Allowed
    ):
        return None
    First, LastValue = sorted((EdgeValue.start_parameter, EdgeValue.end_parameter))
    KindValue = "2" if isinstance(Curve, CircleCurve) else "3"
    Radii = (
        (Curve.radius,)
        if isinstance(Curve, CircleCurve)
        else (Curve.major_radius, Curve.minor_radius)
    )
    Start = (
        Center[0]
        + Radii[0] * MathValue.cos(First) * XDirection[0]
        + Radii[-1] * MathValue.sin(First) * YDirection[0],
        Center[1]
        + Radii[0] * MathValue.cos(First) * XDirection[1]
        + Radii[-1] * MathValue.sin(First) * YDirection[1],
    )
    EndValue = (
        Center[0]
        + Radii[0] * MathValue.cos(LastValue) * XDirection[0]
        + Radii[-1] * MathValue.sin(LastValue) * YDirection[0],
        Center[1]
        + Radii[0] * MathValue.cos(LastValue) * XDirection[1]
        + Radii[-1] * MathValue.sin(LastValue) * YDirection[1],
    )
    return GeneratedPcurve(
        f"{KindValue} {Values(Center + XDirection + YDirection + Radii)} ",
        First,
        LastValue,
        Start,
        EndValue,
    )


# linearity checking stays isolated because sampled surface coordinates must follow one affine path
def IsLinearUv(
    Parameters: tuple[float, ...],
    UvValues: tuple[tuple[float, float], ...],
    Origin: tuple[float, float],
    Direction: tuple[float, float],
    Allowed: float,
) -> bool:
    for Param, UvValue in zip(Parameters, UvValues, strict=True):
        Expected = (
            Origin[0] + Param * Direction[0],
            Origin[1] + Param * Direction[1],
        )
        if (
            MathValue.hypot(UvValue[0] - Expected[0], UvValue[1] - Expected[1])
            > Allowed
        ):
            return False
    return True


# this definition exists because focused behavior needs one stable owner
def LinearSurface(
    Curve: object,
    Surface: object,
    EdgeValue: BrepEdge,
    Tolerance: float,
    Offset: tuple[float, float],
) -> GeneratedPcurve | None:
    LowValue, HighValue = sorted((EdgeValue.start_parameter, EdgeValue.end_parameter))
    if HighValue == LowValue:
        return None
    Parameters = tuple(
        (LowValue + (HighValue - LowValue) * Index / 8.0 for Index in range(9))
    )
    Points = tuple((CurvePoint(Curve, Param) for Param in Parameters))
    if any((Point is None for Point in Points)):
        return None
    ConcretePoints = tuple((Point for Point in Points if Point is not None))
    Allowed = max(Tolerance, EdgeValue.tolerance, 1e-07) * 10.0
    Residuals = tuple((SurfaceResidual(Surface, Point) for Point in ConcretePoints))
    if any((Value is None or Value > Allowed for Value in Residuals)):
        return None
    RawUv = tuple((SurfaceUv(Surface, Point) for Point in ConcretePoints))
    if any((Value is None for Value in RawUv)):
        return None
    UvValue = UnwrapSurfaceUv(
        tuple((Value for Value in RawUv if Value is not None)), Surface
    )
    DeltaParam = HighValue - LowValue
    Direction = (
        (UvValue[-1][0] - UvValue[0][0]) / DeltaParam,
        (UvValue[-1][1] - UvValue[0][1]) / DeltaParam,
    )
    Magnitude = MathValue.hypot(*Direction)
    if Magnitude <= 1e-15:
        return None
    Origin = (
        UvValue[0][0] - LowValue * Direction[0],
        UvValue[0][1] - LowValue * Direction[1],
    )
    if not IsLinearUv(Parameters, UvValue, Origin, Direction, Allowed):
        return None
    Origin = (Origin[0] + Offset[0], Origin[1] + Offset[1])
    UnitValue = (Direction[0] / Magnitude, Direction[1] / Magnitude)
    First = LowValue * Magnitude
    LastValue = HighValue * Magnitude
    return GeneratedPcurve(
        f"1 {Values(Origin + UnitValue)} ",
        First,
        LastValue,
        (Origin[0] + UnitValue[0] * First, Origin[1] + UnitValue[1] * First),
        (Origin[0] + UnitValue[0] * LastValue, Origin[1] + UnitValue[1] * LastValue),
    )


# this definition exists because focused behavior needs one stable owner
def GeneratedPcurvA(
    Curve: object,
    Surface: object,
    EdgeValue: BrepEdge,
    Tolerance: float,
    Offset: tuple[float, float],
) -> GeneratedPcurve:
    Result = (
        PlaneConic(Curve, Surface, EdgeValue, Tolerance)
        if isinstance(Surface, PlaneSurface)
        else None
    )
    if Result is None:
        Result = LinearSurface(Curve, Surface, EdgeValue, Tolerance, Offset)
    if Result is None:
        Unsupported(
            f"edge {EdgeValue.id} has no exact pcurve on surface {getattr(Surface, 'id', '')}"
        )
    return Result


# seam inputs stay isolated because only paired circular loops on ruled surfaces qualify
def GetSeamInputs(FaceValue: BrepFace, Graph: _ModelGraph, Tolerance: float):
    Surface = Graph.surfaces[FaceValue.surface_id]
    if not isinstance(Surface, (CylinderSurface, ConeSurface)):
        return None
    if len(FaceValue.loop_ids) != 2:
        return None
    Loops = tuple(Graph.loops[LoopId] for LoopId in FaceValue.loop_ids)
    if any(len(LoopValue.coedge_ids) != 1 for LoopValue in Loops):
        return None
    Coedges = tuple(Graph.coedges[LoopValue.coedge_ids[0]] for LoopValue in Loops)
    if any(Coedge.pcurve_id for Coedge in Coedges):
        return None
    Edges = tuple(Graph.edges[Coedge.edge_id] for Coedge in Coedges)
    Curves = tuple(Graph.curves[EdgeValue.curve_id] for EdgeValue in Edges)
    if any(not isinstance(Curve, CircleCurve) for Curve in Curves):
        return None
    Allowed = (
        max(
            Tolerance,
            *(EdgeValue.tolerance for EdgeValue in Edges),
            *(
                Graph.vertices[EdgeValue.start_vertex_id].tolerance
                for EdgeValue in Edges
            ),
            1e-07,
        )
        * 10.0
    )
    IsInvalid = any(
        EdgeValue.start_vertex_id != EdgeValue.end_vertex_id
        or abs(abs(EdgeValue.end_parameter - EdgeValue.start_parameter) - MathValue.tau)
        > Allowed
        for EdgeValue in Edges
    )
    return None if IsInvalid else (Surface, Coedges, Edges, Curves, Allowed)


# seam alignment stays isolated because periodic pcurves must meet at matching unwrapped endpoints
def AlignSeam(
    Curves: tuple[object, ...],
    Surface: object,
    Edges: tuple[BrepEdge, ...],
    Tolerance: float,
    Allowed: float,
):
    Generated = tuple(
        GeneratedPcurvA(Curve, Surface, EdgeValue, Tolerance, (0.0, 0.0))
        for Curve, EdgeValue in zip(Curves, Edges, strict=True)
    )
    HasBadSpan = any(
        abs(abs(Value.end[0] - Value.start[0]) - MathValue.tau) > Allowed
        or abs(Value.end[1] - Value.start[1]) > Allowed
        for Value in Generated
    )
    Means = tuple((Value.start[1] + Value.end[1]) / 2.0 for Value in Generated)
    if HasBadSpan or abs(Means[0] - Means[1]) <= Allowed:
        return None
    LowIndex = 0 if Means[0] < Means[1] else 1
    HighIndex = 1 - LowIndex
    LowGenerated = Generated[LowIndex]
    HighGenerated = Generated[HighIndex]
    LowReversed = LowGenerated.end[0] < LowGenerated.start[0]
    HighReversed = HighGenerated.end[0] > HighGenerated.start[0]
    LowStart = LowGenerated.end if LowReversed else LowGenerated.start
    LowEnd = LowGenerated.start if LowReversed else LowGenerated.end
    HighStart = HighGenerated.end if HighReversed else HighGenerated.start
    Offset = round((LowEnd[0] - HighStart[0]) / MathValue.tau) * MathValue.tau
    HighGenerated = GeneratedPcurvA(
        Curves[HighIndex], Surface, Edges[HighIndex], Tolerance, (Offset, 0.0)
    )
    HighStart = HighGenerated.end if HighReversed else HighGenerated.start
    HighEnd = HighGenerated.start if HighReversed else HighGenerated.end
    if (
        abs(LowEnd[0] - HighStart[0]) > Allowed
        or abs(HighEnd[0] - LowStart[0]) > Allowed
    ):
        return None
    return (
        LowIndex,
        HighIndex,
        LowGenerated,
        HighGenerated,
        LowReversed,
        HighReversed,
        Means,
    )


# seam span validation stays isolated because connector geometry must remain on the supporting surface
def GetSeamSpan(
    Graph: _ModelGraph,
    Edges: tuple[BrepEdge, ...],
    Surface: object,
    LowIndex: int,
    HighIndex: int,
    Means: tuple[float, ...],
    Allowed: float,
):
    LowPoint = VectorThreeA(Graph.vertices[Edges[LowIndex].start_vertex_id].point)
    HighPoint = VectorThreeA(Graph.vertices[Edges[HighIndex].start_vertex_id].point)
    SpanVector = Subtract(HighPoint, LowPoint)
    Length = GetLength(SpanVector)
    if (
        Length <= Allowed
        or abs(Length - (Means[HighIndex] - Means[LowIndex])) > Allowed
    ):
        return None
    Residuals = (
        SurfaceResidual(
            Surface,
            tuple(
                LowPoint[AxisValue] + SpanVector[AxisValue] * Ratio
                for AxisValue in range(3)
            ),
        )
        or 0.0
        for Ratio in (0.25, 0.5, 0.75)
    )
    return (
        None
        if any(Value > Allowed for Value in Residuals)
        else (LowPoint, HighPoint, Length)
    )


# this definition exists because focused behavior needs one stable owner
def SeamBandA(FaceValue: BrepFace, Graph: _ModelGraph, Tolerance: float) -> (
    tuple[
        BrepCoedge,
        BrepCoedge,
        GeneratedPcurve,
        GeneratedPcurve,
        bool,
        bool,
        KPoint,
        KPoint,
        float,
    ]
    | None
):
    InputData = GetSeamInputs(FaceValue, Graph, Tolerance)
    if InputData is None:
        return None
    Surface, Coedges, Edges, Curves, Allowed = InputData
    AlignData = AlignSeam(Curves, Surface, Edges, Tolerance, Allowed)
    if AlignData is None:
        return None
    LowIndex, HighIndex, LowGenerated, HighGenerated = AlignData[:4]
    LowReversed, HighReversed, Means = AlignData[4:]
    SpanData = GetSeamSpan(Graph, Edges, Surface, LowIndex, HighIndex, Means, Allowed)
    if SpanData is None:
        return None
    LowPoint, HighPoint, Length = SpanData
    return (
        Coedges[LowIndex],
        Coedges[HighIndex],
        LowGenerated,
        HighGenerated,
        LowReversed,
        HighReversed,
        LowPoint,
        HighPoint,
        Length,
    )


# seam record emission stays isolated because one detected band expands into coordinated edge records
def AddSeamMut(
    Records: list[str],
    Result: dict[str, EdgePcurve],
    SeamBands: dict[str, SeamBand],
    FaceValue: BrepFace,
    Graph: _ModelGraph,
    SeamValue: tuple,
) -> None:
    LowCoedge, HighCoedge, LowGenerated, HighGenerated = SeamValue[:4]
    LowReversed, HighReversed, LowPoint, HighPoint, Length = SeamValue[4:]
    for CoedgeValue, Generated in (
        (LowCoedge, LowGenerated),
        (HighCoedge, HighGenerated),
    ):
        Records.append(Generated.record)
        Result[CoedgeValue.id] = EdgePcurve(
            len(Records), Generated.first, Generated.last
        )
    LowStart = LowGenerated.end if LowReversed else LowGenerated.start
    LowEnd = LowGenerated.start if LowReversed else LowGenerated.end
    Records.append(f"1 {Values((LowEnd[0], LowStart[1], 0.0, 1.0))} ")
    FirstIndex = len(Records)
    Records.append(f"1 {Values((LowStart[0], LowStart[1], 0.0, 1.0))} ")
    Direction = ScaleVector(Subtract(HighPoint, LowPoint), 1.0 / Length)
    SeamBands[FaceValue.id] = SeamBand(
        FaceValue.id,
        (FaceValue.loop_ids[0], FaceValue.loop_ids[1]),
        LowCoedge.id,
        HighCoedge.id,
        LowReversed,
        HighReversed,
        Graph.edges[LowCoedge.edge_id].start_vertex_id,
        Graph.edges[HighCoedge.edge_id].start_vertex_id,
        f"1 {Values(LowPoint + Direction)} ",
        Length,
        FirstIndex,
        len(Records),
    )


# periodic offset calculation stays isolated because adjacent pcurves must share an unwrapped endpoint
def GetUvOffset(
    PreviousEnd: tuple[float, float] | None,
    StartPoint: tuple[float, float],
    Periods: tuple[float | None, float | None],
) -> tuple[float, float]:
    Offset = [0.0, 0.0]
    if PreviousEnd is not None:
        for AxisValue, PeriodValue in enumerate(Periods):
            if PeriodValue is not None:
                DeltaValue = PreviousEnd[AxisValue] - StartPoint[AxisValue]
                Offset[AxisValue] = round(DeltaValue / PeriodValue) * PeriodValue
    return Offset[0], Offset[1]


# coedge pcurve emission stays isolated because explicit and generated records have distinct contracts
def AddCoedgeMut(
    Records: list[str],
    Result: dict[str, EdgePcurve],
    Graph: _ModelGraph,
    Surface: object,
    Coedge: BrepCoedge,
    Tolerance: float,
    ExplicitIndexes: Mapping[str, int],
    ExplicitScales: Mapping[str, float],
    Periods: tuple[float | None, float | None],
    PreviousEnd: tuple[float, float] | None,
) -> tuple[float, float] | None:
    EdgeValue = Graph.edges[Coedge.edge_id]
    if Coedge.pcurve_id:
        Scale = ExplicitScales[Coedge.pcurve_id]
        First, LastValue = sorted(
            (EdgeValue.start_parameter * Scale, EdgeValue.end_parameter * Scale)
        )
        Result[Coedge.id] = EdgePcurve(
            ExplicitIndexes[Coedge.pcurve_id], First, LastValue
        )
        return None
    CurveValue = Graph.curves[EdgeValue.curve_id]
    Generated = GeneratedPcurvA(CurveValue, Surface, EdgeValue, Tolerance, (0.0, 0.0))
    IsReversed = Coedge.reversed != (
        EdgeValue.end_parameter < EdgeValue.start_parameter
    )
    StartPoint = Generated.end if IsReversed else Generated.start
    Offset = GetUvOffset(PreviousEnd, StartPoint, Periods)
    if Offset != (0.0, 0.0):
        Generated = GeneratedPcurvA(CurveValue, Surface, EdgeValue, Tolerance, Offset)
    Records.append(Generated.record)
    Result[Coedge.id] = EdgePcurve(len(Records), Generated.first, Generated.last)
    return Generated.start if IsReversed else Generated.end


# loop pcurve emission stays isolated because endpoint continuity is scoped to one ordered loop
def AddLoopMut(
    Records: list[str],
    Result: dict[str, EdgePcurve],
    Graph: _ModelGraph,
    LoopId: str,
    Surface: object,
    Tolerance: float,
    ExplicitIndexes: Mapping[str, int],
    ExplicitScales: Mapping[str, float],
) -> None:
    PreviousEnd: tuple[float, float] | None = None
    Periods = SurfacePeriods(Surface)
    for CoedgeId in Graph.loops[LoopId].coedge_ids:
        PreviousEnd = AddCoedgeMut(
            Records,
            Result,
            Graph,
            Surface,
            Graph.coedges[CoedgeId],
            Tolerance,
            ExplicitIndexes,
            ExplicitScales,
            Periods,
            PreviousEnd,
        )


# edge pcurve assembly composes focused seam and loop writers because their continuity rules differ
def EdgePcurveA(
    Model: BrepModel, Graph: _ModelGraph, Tolerance: float
) -> tuple[tuple[str, ...], Mapping[str, EdgePcurve], Mapping[str, SeamBand]]:
    PcurveData = tuple(PcurveRecord(ItemValue) for ItemValue in Model.pcurves)
    Records = [RecordText for RecordText, ScaleValue in PcurveData]
    ExplicitIndexes = {
        ItemValue.id: Index for Index, ItemValue in enumerate(Model.pcurves, 1)
    }
    ExplicitScales = {
        ItemValue.id: PcurveData[Index][1]
        for Index, ItemValue in enumerate(Model.pcurves)
    }
    Result: dict[str, EdgePcurve] = {}
    SeamBands: dict[str, SeamBand] = {}
    for FaceValue in Model.faces:
        Surface = Graph.surfaces[FaceValue.surface_id]
        SeamValue = SeamBandA(FaceValue, Graph, Tolerance)
        if SeamValue is not None:
            AddSeamMut(Records, Result, SeamBands, FaceValue, Graph, SeamValue)
            continue
        for LoopId in FaceValue.loop_ids:
            AddLoopMut(
                Records,
                Result,
                Graph,
                LoopId,
                Surface,
                Tolerance,
                ExplicitIndexes,
                ExplicitScales,
            )
    return tuple(Records), Result, SeamBands


# this definition exists because focused behavior needs one stable owner
def LoopUvPoints(
    Graph: _ModelGraph, FaceValue: BrepFace, LoopValue: BrepLoop
) -> tuple[tuple[float, float], ...] | None:
    Surface = Graph.surfaces[FaceValue.surface_id]
    Values: list[tuple[float, float]] = []
    for CoedgeId in LoopValue.coedge_ids:
        Coedge = Graph.coedges[CoedgeId]
        EdgeValue = Graph.edges[Coedge.edge_id]
        GeomValue = Graph.curves.get(EdgeValue.curve_id)
        if GeomValue is None:
            return None
        First, LastValue = (EdgeValue.start_parameter, EdgeValue.end_parameter)
        if Coedge.reversed:
            First, LastValue = (LastValue, First)
        for Index in range(16):
            Point = CurvePoint(GeomValue, First + (LastValue - First) * Index / 16.0)
            if Point is None:
                return None
            UvValue = SurfaceUv(Surface, Point)
            if UvValue is None:
                return None
            Values.append(UvValue)
    return UnwrapSurfaceUv(Values, Surface)


# this definition exists because focused behavior needs one stable owner
def FaceLoop(
    Graph: _ModelGraph, FaceValue: BrepFace, Tolerance: float
) -> dict[str, bool]:
    AreaTolerance = max(Tolerance * Tolerance, 1e-10)
    LoopPoints = {
        LoopId: LoopUvPoints(Graph, FaceValue, Graph.loops[LoopId])
        for LoopId in FaceValue.loop_ids
    }
    LoopAreas = {
        LoopId: (
            None
            if Points is None or len(Points) < 3
            else sum(
                (
                    LeftValue[0] * Right[1] - Right[0] * LeftValue[1]
                    for LeftValue, Right in zip(Points, (*Points[1:], Points[0]))
                )
            )
            / 2.0
        )
        for LoopId, Points in LoopPoints.items()
    }
    Measurable = {
        LoopId: AreaValue
        for LoopId, AreaValue in LoopAreas.items()
        if AreaValue is not None and abs(AreaValue) > AreaTolerance
    }
    if len(Measurable) != len(FaceValue.loop_ids):
        Unsupported(f"face {FaceValue.id} has an unprovable loop orientation")

    # this callback exists because local behavior needs one focused transformation
    OuterLoopId = max(Measurable, key=lambda LoopId: abs(Measurable[LoopId]))
    return {
        LoopId: (AreaValue > 0.0) != (LoopId == OuterLoopId)
        for LoopId, AreaValue in Measurable.items()
    }


# this definition exists because focused behavior needs one stable owner
def HasCoedgeShape(Coedge: BrepCoedge, EdgeValue: BrepEdge) -> bool:
    return Coedge.reversed != (EdgeValue.end_parameter < EdgeValue.start_parameter)


# planar point extraction stays isolated because line and surface evidence must precede polygon tests
def GetPlanarPoints(
    Graph: _ModelGraph, FaceValue: BrepFace, LoopValue: BrepLoop, Tolerance: float
):
    if len(LoopValue.coedge_ids) < 3:
        return None
    Surface = Graph.surfaces[FaceValue.surface_id]
    if not isinstance(Surface, PlaneSurface):
        return None
    Points: list[tuple[float, float]] = []
    Allowed = max(Tolerance, FaceValue.tolerance, 1e-07) * 10.0
    for CoedgeId in LoopValue.coedge_ids:
        Coedge = Graph.coedges[CoedgeId]
        EdgeValue = Graph.edges[Coedge.edge_id]
        Curve = Graph.curves[EdgeValue.curve_id]
        if not isinstance(Curve, LineCurve):
            return None
        First = (
            EdgeValue.end_parameter if Coedge.reversed else EdgeValue.start_parameter
        )
        LastValue = (
            EdgeValue.start_parameter if Coedge.reversed else EdgeValue.end_parameter
        )
        Start = CurvePoint(Curve, First)
        EndValue = CurvePoint(Curve, LastValue)
        Middle = CurvePoint(Curve, (First + LastValue) / 2.0)
        if Start is None or EndValue is None or Middle is None:
            return None
        if any(
            (
                Residual is None or Residual > Allowed
                for Residual in (
                    SurfaceResidual(Surface, Start),
                    SurfaceResidual(Surface, Middle),
                    SurfaceResidual(Surface, EndValue),
                )
            )
        ):
            return None
        UvValue = SurfaceUv(Surface, Start)
        if UvValue is None:
            return None
        Points.append(UvValue)
    return (tuple(Points), Allowed) if len(Points) >= 3 else None


# planar cross products stay centralized because convexity and intersection tests share exact arithmetic
def GetCrossValue(
    LeftPoint: tuple[float, float],
    RightPoint: tuple[float, float],
    TestPoint: tuple[float, float],
) -> float:
    return (RightPoint[0] - LeftPoint[0]) * (TestPoint[1] - LeftPoint[1]) - (
        RightPoint[1] - LeftPoint[1]
    ) * (TestPoint[0] - LeftPoint[0])


# convexity checking remains a predicate because only consistently signed nonzero turns are proven
def IsConvexLoop(Points: tuple[tuple[float, float], ...], Epsilon: float) -> bool:
    Turns: list[bool] = []
    for Index, MiddlePoint in enumerate(Points):
        LeftPoint = Points[Index - 1]
        RightPoint = Points[(Index + 1) % len(Points)]
        TurnValue = GetCrossValue(LeftPoint, MiddlePoint, RightPoint)
        if abs(TurnValue) <= Epsilon:
            return False
        Turns.append(TurnValue > 0.0)
    return not any(Value != Turns[0] for Value in Turns[1:])


# intersection detection remains a predicate because self crossing loops cannot prove planar topology
def HasCrossings(Points: tuple[tuple[float, float], ...], Epsilon: float) -> bool:
    for FirstIndex, FirstStart in enumerate(Points):
        FirstEnd = Points[(FirstIndex + 1) % len(Points)]
        Adjacent = {
            FirstIndex,
            (FirstIndex + 1) % len(Points),
            (FirstIndex - 1) % len(Points),
        }
        for SecondIndex in range(FirstIndex + 1, len(Points)):
            if SecondIndex in Adjacent:
                continue
            SecondStart = Points[SecondIndex]
            SecondEnd = Points[(SecondIndex + 1) % len(Points)]
            CrossValues = (
                GetCrossValue(FirstStart, FirstEnd, SecondStart),
                GetCrossValue(FirstStart, FirstEnd, SecondEnd),
                GetCrossValue(SecondStart, SecondEnd, FirstStart),
                GetCrossValue(SecondStart, SecondEnd, FirstEnd),
            )
            if any(abs(Value) <= Epsilon for Value in CrossValues):
                return True
            Signs = tuple(Value > 0.0 for Value in CrossValues)
            if Signs[0] != Signs[1] and Signs[2] != Signs[3]:
                return True
    return False


# planar loop proof composes point convexity and crossing evidence because each can reject independently
def IsPlanarLoop(
    Graph: _ModelGraph, FaceValue: BrepFace, LoopValue: BrepLoop, Tolerance: float
) -> bool:
    PointData = GetPlanarPoints(Graph, FaceValue, LoopValue, Tolerance)
    if PointData is None:
        return False
    Points, Allowed = PointData
    SpanValue = max(
        max(Value[AxisValue] for Value in Points)
        - min(Value[AxisValue] for Value in Points)
        for AxisValue in (0, 1)
    )
    Epsilon = Allowed * max(1.0, SpanValue)
    return IsConvexLoop(Points, Epsilon) and not HasCrossings(Points, Epsilon)


# this definition exists because focused behavior needs one stable owner
def PlanarCircle(
    Graph: _ModelGraph, FaceValue: BrepFace, LoopValue: BrepLoop, Tolerance: float
) -> tuple[tuple[float, float], float] | None:
    if len(LoopValue.coedge_ids) != 1:
        return None
    Surface = Graph.surfaces[FaceValue.surface_id]
    if not isinstance(Surface, PlaneSurface):
        return None
    Coedge = Graph.coedges[LoopValue.coedge_ids[0]]
    EdgeValue = Graph.edges[Coedge.edge_id]
    Curve = Graph.curves[EdgeValue.curve_id]
    if not isinstance(Curve, CircleCurve):
        return None
    Allowed = max(Tolerance, FaceValue.tolerance, EdgeValue.tolerance, 1e-07) * 10.0
    if (
        EdgeValue.start_vertex_id != EdgeValue.end_vertex_id
        or abs(abs(EdgeValue.end_parameter - EdgeValue.start_parameter) - MathValue.tau)
        > Allowed
    ):
        return None
    SurfaceAxis, Ignored, Ignored = Frame(
        Surface.normal, Surface.reference_direction, f"plane surface {Surface.id}"
    )
    CurveAxis, Ignored, Ignored = Frame(
        Curve.axis, Curve.reference_direction, f"circle curve {Curve.id}"
    )
    if abs(abs(DotAction(SurfaceAxis, CurveAxis)) - 1.0) > Allowed:
        return None
    Center = SurfaceUv(Surface, VectorThreeA(Curve.center))
    Residual = SurfaceResidual(Surface, VectorThreeA(Curve.center))
    if Center is None or Residual is None or Residual > Allowed:
        return None
    return (Center, Curve.radius)


# this definition exists because focused behavior needs one stable owner
def FaceIsProven(
    Graph: _ModelGraph,
    FaceValue: BrepFace,
    Tolerance: float,
    SeamBands: Mapping[str, _SeamBand],
) -> None:
    if FaceValue.id in SeamBands:
        return
    Surface = Graph.surfaces[FaceValue.surface_id]
    if not isinstance(Surface, PlaneSurface):
        Unsupported(
            f"face {FaceValue.id} on {type(Surface).__name__} lacks a proven native topology"
        )
    Loops = tuple((Graph.loops[LoopId] for LoopId in FaceValue.loop_ids))
    if len(Loops) == 1 and IsPlanarLoop(Graph, FaceValue, Loops[0], Tolerance):
        return
    Circles = tuple(
        (PlanarCircle(Graph, FaceValue, LoopValue, Tolerance) for LoopValue in Loops)
    )
    if len(Circles) not in {1, 2} or any((Value is None for Value in Circles)):
        Unsupported(f"planar face {FaceValue.id} lacks a proven wire arrangement")
    Concrete = tuple((Value for Value in Circles if Value is not None))
    Allowed = max(Tolerance, FaceValue.tolerance, 1e-07) * 10.0
    if len(Concrete) == 2:
        if (
            MathValue.dist(Concrete[0][0], Concrete[1][0]) > Allowed
            or abs(Concrete[0][1] - Concrete[1][1]) <= Allowed
        ):
            Unsupported(f"planar face {FaceValue.id} has unproven circle containment")


# this definition exists because focused behavior needs one stable owner
def FaceEdge(
    Graph: _ModelGraph,
    FaceValue: BrepFace,
    LoopReversals: Mapping[str, bool],
    SeamBands: Mapping[str, _SeamBand],
) -> tuple[tuple[str, bool], ...]:
    BandValue = SeamBands.get(FaceValue.id)
    if BandValue is not None:
        return (
            (Graph.coedges[BandValue.low_coedge_id].edge_id, BandValue.low_reversed),
            (Graph.coedges[BandValue.high_coedge_id].edge_id, BandValue.high_reversed),
        )
    return tuple(
        (
            (
                Graph.coedges[CoedgeId].edge_id,
                HasCoedgeShape(
                    Graph.coedges[CoedgeId],
                    Graph.edges[Graph.coedges[CoedgeId].edge_id],
                )
                != LoopReversals[LoopId],
            )
            for LoopId in FaceValue.loop_ids
            for CoedgeId in Graph.loops[LoopId].coedge_ids
        )
    )


# shell face collection stays isolated because repeated faces invalidate native shell topology
def GetFaceUses(Shell: BrepShell, Graph: _ModelGraph) -> tuple[BrepFaceUse, ...]:
    FaceUses = tuple(Graph.face_uses[ValueId] for ValueId in Shell.face_use_ids)
    FaceIds = tuple(Value.face_id for Value in FaceUses)
    if len(FaceIds) != len(set(FaceIds)):
        Unsupported(f"shell {Shell.id} reuses a face")
    return FaceUses


# shell edge indexing stays isolated because manifold and closure rules depend on edge incidence
def GetShellEdges(
    Shell: BrepShell,
    FaceUses: tuple[BrepFaceUse, ...],
    FaceEdges: Mapping[str, tuple[tuple[str, bool], ...]],
) -> dict[str, list[tuple[str, bool]]]:
    ByEdge: dict[str, list[tuple[str, bool]]] = {}
    for FaceUse in FaceUses:
        for EdgeId, IsReversed in FaceEdges[FaceUse.face_id]:
            ByEdge.setdefault(EdgeId, []).append((FaceUse.id, IsReversed))
    if any(len(Values) > 2 for Values in ByEdge.values()):
        Unsupported(f"shell {Shell.id} is non-manifold")
    if Shell.closed and any(len(Values) != 2 for Values in ByEdge.values()):
        Unsupported(f"closed shell {Shell.id} has a free edge")
    return ByEdge


# face adjacency stays isolated because each shared edge contributes one orientation constraint
def GetAdjacency(
    ShellId: str,
    FaceUses: tuple[BrepFaceUse, ...],
    ByEdge: Mapping[str, list[tuple[str, bool]]],
) -> dict[str, list[tuple[str, bool]]]:
    Adjacency: dict[str, list[tuple[str, bool]]] = {Value.id: [] for Value in FaceUses}
    for EdgeUses in ByEdge.values():
        if len(EdgeUses) != 2:
            continue
        (LeftId, LeftValue), (RightId, RightValue) = EdgeUses
        IsRequired = not (LeftValue != RightValue)
        if LeftId == RightId:
            if IsRequired:
                Unsupported(f"shell {ShellId} is not orientable")
            continue
        Adjacency[LeftId].append((RightId, IsRequired))
        Adjacency[RightId].append((LeftId, IsRequired))
    return Adjacency


# component traversal mutates assignments because each connected face receives one consistent parity
def AddFaceCompMut(
    StartId: str,
    ShellId: str,
    Adjacency: Mapping[str, list[tuple[str, bool]]],
    Assigned: dict[str, bool],
) -> tuple[str, ...]:
    Assigned[StartId] = False
    Component = [StartId]
    Pending = Deque((StartId,))
    while Pending:
        CurrentId = Pending.popleft()
        for NeighborId, Parity in Adjacency[CurrentId]:
            Expected = Assigned[CurrentId] != Parity
            if NeighborId in Assigned:
                if Assigned[NeighborId] != Expected:
                    Unsupported(f"shell {ShellId} is not orientable")
                continue
            Assigned[NeighborId] = Expected
            Component.append(NeighborId)
            Pending.append(NeighborId)
    return tuple(Component)


# preferred orientation mutates one component because geometric face sense chooses global parity
def SetFaceSenseMut(
    Graph: _ModelGraph,
    FaceUses: tuple[BrepFaceUse, ...],
    Component: tuple[str, ...],
    Assigned: dict[str, bool],
) -> None:
    Preferred = {
        Value.id: not Graph.faces[Value.face_id].same_sense != Value.reversed
        for Value in FaceUses
        if Value.id in Component
    }
    DirectScore = sum(Assigned[Value] != Preferred[Value] for Value in Component)
    ReverseScore = sum((not Assigned[Value]) != Preferred[Value] for Value in Component)
    if ReverseScore < DirectScore:
        for ValueId in Component:
            Assigned[ValueId] = not Assigned[ValueId]


# shell orientation composes incidence traversal and geometric sense because each proves one constraint
def OrientShell(
    Shell: BrepShell,
    Graph: _ModelGraph,
    FaceEdges: Mapping[str, tuple[tuple[str, bool], ...]],
) -> dict[str, bool]:
    FaceUses = GetFaceUses(Shell, Graph)
    ByEdge = GetShellEdges(Shell, FaceUses, FaceEdges)
    Adjacency = GetAdjacency(Shell.id, FaceUses, ByEdge)
    Assigned: dict[str, bool] = {}
    for StartId in Adjacency:
        if StartId in Assigned:
            continue
        Component = AddFaceCompMut(StartId, Shell.id, Adjacency, Assigned)
        SetFaceSenseMut(Graph, FaceUses, Component, Assigned)
    return Assigned


# shell face assembly stays small because each shell owns an independent orientation graph
def ShellFace(
    Model: BrepModel,
    Graph: _ModelGraph,
    FaceEdges: Mapping[str, tuple[tuple[str, bool], ...]],
) -> dict[str, bool]:
    Result: dict[str, bool] = {}
    for Shell in Model.shells:
        Result.update(OrientShell(Shell, Graph, FaceEdges))
    return Result


# this definition exists because focused behavior needs one stable owner
def ShellUse(Model: BrepModel, Graph: _ModelGraph) -> dict[str, bool]:
    Result: dict[str, bool] = {}
    for Region in Model.regions:
        if Region.solid:
            if len(Region.shell_use_ids) != 1:
                Unsupported(
                    f"solid region {Region.id} has unproven nested shell containment"
                )
            ShellUse = Graph.shell_uses[Region.shell_use_ids[0]]
            if not Graph.shells[ShellUse.shell_id].closed:
                Unsupported(f"solid region {Region.id} contains an open shell")
            Result[ShellUse.id] = False
            continue
        for ShellUseId in Region.shell_use_ids:
            Result[ShellUseId] = Graph.shell_uses[ShellUseId].reversed
    return Result


# this definition exists because focused behavior needs one stable owner
def CheckEdgeGeom(
    EdgeValue: BrepEdge,
    Curve: object,
    Vertices: Mapping[str, BrepVertex],
    Tolerance: float,
) -> None:
    Start = CurvePoint(Curve, EdgeValue.start_parameter)
    EndValue = CurvePoint(Curve, EdgeValue.end_parameter)
    if Start is None or EndValue is None:
        return
    for Actual, VertexId in (
        (Start, EdgeValue.start_vertex_id),
        (EndValue, EdgeValue.end_vertex_id),
    ):
        Vertex = Vertices[VertexId]
        Allowed = max(Tolerance, EdgeValue.tolerance, Vertex.tolerance)
        if GetLength(Subtract(Actual, VectorThreeA(Vertex.point))) > Allowed:
            Unsupported(
                f"edge {EdgeValue.id} curve endpoint does not match vertex {VertexId}"
            )


# coedge grouping stays isolated because wire and surface uses follow different native contracts
def GroupCoedges(
    EdgeValue: BrepEdge, Graph: _ModelGraph
) -> dict[str, list[BrepCoedge]]:
    Grouped: dict[str, list[BrepCoedge]] = {}
    for CoedgeId in Graph.edge_uses[EdgeValue.id]:
        Coedge = Graph.coedges[CoedgeId]
        FaceValue = Graph.face_for_coedge(CoedgeId)
        if FaceValue is None:
            if Coedge.pcurve_id:
                Unsupported(f"wire coedge {Coedge.id} cannot carry a surface pcurve")
            continue
        Grouped.setdefault(FaceValue.surface_id, []).append(Coedge)
    return Grouped


# pcurve representation encoding stays isolated because open and closed surfaces use distinct records
def GetPcurveReps(
    EdgeId: str,
    Grouped: Mapping[str, list[BrepCoedge]],
    EdgePcurves: Mapping[str, _EdgePcurve],
    SurfaceIndexes: Mapping[str, int],
) -> tuple[str, ...]:
    Representations: list[str] = []
    for SurfaceId, UsesValue in Grouped.items():
        SurfaceIndex = SurfaceIndexes[SurfaceId]
        if len(UsesValue) == 1:
            Pcurve = EdgePcurves[UsesValue[0].id]
            Representations.append(
                f"2  {Pcurve.index} {SurfaceIndex} 0 {Number(Pcurve.first)} {Number(Pcurve.last)}"
            )
            continue
        if len(UsesValue) == 2:
            FirstPcurve = EdgePcurves[UsesValue[0].id]
            SecondPcurve = EdgePcurves[UsesValue[1].id]
            if (
                abs(FirstPcurve.first - SecondPcurve.first) > 1e-09
                or abs(FirstPcurve.last - SecondPcurve.last) > 1e-09
            ):
                Unsupported(
                    f"edge {EdgeId} has inconsistent closed-surface pcurve ranges"
                )
            Representations.append(
                f"3  {FirstPcurve.index} {SecondPcurve.index} C0 {SurfaceIndex} 0 {Number(FirstPcurve.first)} {Number(FirstPcurve.last)}"
            )
            continue
        Unsupported(
            f"edge {EdgeId} has an unsupported closed-surface pcurve arrangement"
        )
    return tuple(Representations)


# edge geometry composition stays small because grouping and pcurve encoding own their validation
def EdgeGeom(
    EdgeValue: BrepEdge,
    Graph: _ModelGraph,
    CurveIndexes: Mapping[str, int],
    CurveScales: Mapping[str, float],
    EdgePcurves: Mapping[str, _EdgePcurve],
    SurfaceIndexes: Mapping[str, int],
    Tolerance: float,
) -> tuple[str, ...]:
    if EdgeValue.degenerate:
        Unsupported(f"degenerate edge {EdgeValue.id} is unsupported")
    if EdgeValue.end_parameter == EdgeValue.start_parameter:
        Unsupported(f"edge {EdgeValue.id} requires a nonzero parameter range")
    CurveScale = CurveScales[EdgeValue.curve_id]
    First, LastValue = sorted(
        (EdgeValue.start_parameter * CurveScale, EdgeValue.end_parameter * CurveScale)
    )
    Grouped = GroupCoedges(EdgeValue, Graph)
    Representations = GetPcurveReps(EdgeValue.id, Grouped, EdgePcurves, SurfaceIndexes)
    SameRange = all(
        (
            abs(Value - Expected) <= 1e-09
            for CoedgeId in Graph.edge_uses[EdgeValue.id]
            if CoedgeId in EdgePcurves
            for Value, Expected in (
                (EdgePcurves[CoedgeId].first, First),
                (EdgePcurves[CoedgeId].last, LastValue),
            )
        )
    )
    Lines = [
        f" {Number(max(Tolerance, EdgeValue.tolerance))} {int(SameRange)} {int(SameRange)} 0",
        f"1  {CurveIndexes[EdgeValue.curve_id]} 0 {Number(First)} {Number(LastValue)}",
        *Representations,
    ]
    Lines.append("0")
    return tuple(Lines)


# this definition exists because focused behavior needs one stable owner
def ShapeLines(
    Records: Sequence[_ShapeRecord], RootValue: tuple[str, bool]
) -> list[str]:
    Ordinals = {Record.key: Index for Index, Record in enumerate(Records, 1)}
    Count = len(Records)

    # this definition exists because focused behavior needs one stable owner
    def RefAction(KeyValue: str) -> int:
        try:
            return Count - Ordinals[KeyValue] + 1
        except KeyError:
            Unsupported(f"native topology references unknown shape {KeyValue}")

    Lines = [f"TShapes {Count}"]
    for Record in Records:
        Lines.append(Record.kind)
        Lines.extend(Record.geometry)
        Lines.append("")
        Lines.append(Record.flags)
        Lines.append(
            " ".join(
                (
                    f"{('-' if ReversedValue else '+')}{RefAction(KeyValue)} 0"
                    for KeyValue, ReversedValue in Record.children
                )
            )
            + (" " if Record.children else "")
            + "*"
        )
    Lines.extend(["", f"{('-' if RootValue[1] else '+')}{RefAction(RootValue[0])} 0 "])
    return Lines


# model validation stays isolated because type geometry and transform failures precede all emission
def ValidateBrep(Model: BrepModel, Tolerance: float) -> None:
    if not isinstance(Model, BrepModel):
        raise TypeError("model must be a BrepModel")
    if not MathValue.isfinite(Tolerance) or Tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")
    DesignIds = frozenset(
        BodyValue.design_body_id
        for BodyValue in Model.bodies
        if BodyValue.design_body_id
    )
    ErrorList = Model.validate(DesignIds)
    if ErrorList:
        Unsupported(ErrorList[0])
    if any(BodyValue.transform != Transform() for BodyValue in Model.bodies):
        Unsupported("native FreeCAD B-rep writing requires identity body transforms")


# write state construction stays isolated because every shape phase consumes the same proven indexes
def BuildBrepState(Model: BrepModel, Tolerance: float) -> BrepWriteState:
    Graph = ModelGraph(Model)
    BaseCurves = tuple(CurveRecord(Value) for Value in Model.curves)
    SurfaceRecords = tuple(
        SurfaceRecord(Value, Graph.surfaces) for Value in Model.surfaces
    )
    PcurveRecords, EdgePcurves, SeamBands = EdgePcurveA(Model, Graph, Tolerance)
    LoopReversals: dict[str, bool] = {}
    for FaceValue in Model.faces:
        FaceIsProven(Graph, FaceValue, Tolerance, SeamBands)
        if FaceValue.id not in SeamBands:
            LoopReversals.update(FaceLoop(Graph, FaceValue, Tolerance))
    FaceEdges = {
        FaceValue.id: FaceEdge(Graph, FaceValue, LoopReversals, SeamBands)
        for FaceValue in Model.faces
    }
    FaceUseReversals = ShellFace(Model, Graph, FaceEdges)
    ShellUseReversals = ShellUse(Model, Graph)
    CurveRecords = BaseCurves + tuple(
        (BandValue.curve_record, 1.0) for BandValue in SeamBands.values()
    )
    CurveIndexes = {Value.id: Index for Index, Value in enumerate(Model.curves, 1)}
    CurveScales = {
        Value.id: CurveRecords[Index][1] for Index, Value in enumerate(Model.curves)
    }
    SurfaceIndexes = {Value.id: Index for Index, Value in enumerate(Model.surfaces, 1)}
    HeaderLines = (
        "DBRep_DrawableShape",
        "",
        "CASCADE Topology V1, (c) Matra-Datavision",
        "Locations 0",
        f"Curve2ds {len(PcurveRecords)}",
        *PcurveRecords,
        f"Curves {len(CurveRecords)}",
        *(Value[0] for Value in CurveRecords),
        "Polygon3D 0",
        "PolygonOnTriangulations 0",
        f"Surfaces {len(SurfaceRecords)}",
        *SurfaceRecords,
        "Triangulations 0",
        "",
    )
    return BrepWriteState(
        Graph,
        len(BaseCurves),
        CurveRecords,
        SurfaceRecords,
        PcurveRecords,
        EdgePcurves,
        SeamBands,
        LoopReversals,
        FaceUseReversals,
        ShellUseReversals,
        CurveIndexes,
        CurveScales,
        SurfaceIndexes,
        HeaderLines,
    )


# vertex emission mutates the ordered shape list because topology references depend on insertion order
def AddVerticesMut(
    Shapes: list[ShapeRecord], Model: BrepModel, Tolerance: float
) -> None:
    for Vertex in Model.vertices:
        Shapes.append(
            ShapeRecord(
                f"vertex:{Vertex.id}",
                "Ve",
                (
                    Number(max(Tolerance, Vertex.tolerance)),
                    Values(VectorThreeA(Vertex.point)),
                    "0 0",
                ),
                "0101101",
                (),
            )
        )


# edge emission mutates the ordered shape list because vertex references must precede parent edges
def AddEdgesMut(
    Shapes: list[ShapeRecord],
    Model: BrepModel,
    State: BrepWriteState,
    Tolerance: float,
) -> None:
    Graph = State.Graph
    for EdgeValue in Model.edges:
        CurveValue = next(
            Value for Value in Model.curves if Value.id == EdgeValue.curve_id
        )
        CheckEdgeGeom(EdgeValue, CurveValue, Graph.vertices, Tolerance)
        IsRangeReversed = EdgeValue.end_parameter < EdgeValue.start_parameter
        FirstVertexId = (
            EdgeValue.end_vertex_id if IsRangeReversed else EdgeValue.start_vertex_id
        )
        LastVertexId = (
            EdgeValue.start_vertex_id if IsRangeReversed else EdgeValue.end_vertex_id
        )
        GeometryLines = EdgeGeom(
            EdgeValue,
            Graph,
            State.CurveIndexes,
            State.CurveScales,
            State.EdgePcurves,
            State.SurfaceIndexes,
            Tolerance,
        )
        Children = (
            (f"vertex:{FirstVertexId}", False),
            (f"vertex:{LastVertexId}", True),
        )
        Shapes.append(
            ShapeRecord(
                f"edge:{EdgeValue.id}", "Ed", GeometryLines, "0101000", Children
            )
        )


# seam edge emission mutates the ordered shape list because generated curves follow base curves
def AddSeamEdgesMut(
    Shapes: list[ShapeRecord], State: BrepWriteState, Tolerance: float
) -> None:
    Graph = State.Graph
    StartIndex = State.BaseCurveCount + 1
    for CurveIndex, BandValue in enumerate(State.SeamBands.values(), StartIndex):
        SurfaceId = Graph.faces[BandValue.face_id].surface_id
        GeometryLines = (
            f" {Number(Tolerance)} 1 1 0",
            f"1  {CurveIndex} 0 0 {Number(BandValue.length)}",
            f"3  {BandValue.first_pcurve_index} {BandValue.second_pcurve_index} CN {State.SurfaceIndexes[SurfaceId]} 0 0 {Number(BandValue.length)}",
            "0",
        )
        Children = (
            (f"vertex:{BandValue.low_vertex_id}", False),
            (f"vertex:{BandValue.high_vertex_id}", True),
        )
        Shapes.append(
            ShapeRecord(
                f"edge:seam:{BandValue.face_id}",
                "Ed",
                GeometryLines,
                "0101000",
                Children,
            )
        )


# coedge children stay centralized because loops and wires share identical orientation semantics
def GetEdgeChildren(
    Graph: ModelGraph, CoedgeIds: Sequence[str]
) -> tuple[tuple[str, bool], ...]:
    Children: list[tuple[str, bool]] = []
    for CoedgeId in CoedgeIds:
        CoedgeValue = Graph.coedges[CoedgeId]
        EdgeValue = Graph.edges[CoedgeValue.edge_id]
        IsReversed = CoedgeValue.reversed != (
            EdgeValue.end_parameter < EdgeValue.start_parameter
        )
        Children.append((f"edge:{EdgeValue.id}", IsReversed))
    return tuple(Children)


# loop emission mutates the ordered shape list because faces reference loop records by identity
def AddLoopsMut(
    Shapes: list[ShapeRecord], Model: BrepModel, State: BrepWriteState
) -> None:
    SeamLoopIds = {
        LoopId
        for BandValue in State.SeamBands.values()
        for LoopId in BandValue.loop_ids
    }
    for LoopValue in Model.loops:
        if LoopValue.id in SeamLoopIds:
            continue
        Children = GetEdgeChildren(State.Graph, LoopValue.coedge_ids)
        Shapes.append(
            ShapeRecord(f"loop:{LoopValue.id}", "Wi", (), "0101100", Children)
        )


# seam loop emission mutates the ordered shape list because one synthetic loop closes each band
def AddSeamLoopsMut(Shapes: list[ShapeRecord], State: BrepWriteState) -> None:
    Graph = State.Graph
    for BandValue in State.SeamBands.values():
        LowEdge = Graph.edges[Graph.coedges[BandValue.low_coedge_id].edge_id]
        HighEdge = Graph.edges[Graph.coedges[BandValue.high_coedge_id].edge_id]
        Children = (
            (f"edge:{LowEdge.id}", BandValue.low_reversed),
            (f"edge:seam:{BandValue.face_id}", False),
            (f"edge:{HighEdge.id}", BandValue.high_reversed),
            (f"edge:seam:{BandValue.face_id}", True),
        )
        Shapes.append(
            ShapeRecord(f"loop:seam:{BandValue.face_id}", "Wi", (), "0101100", Children)
        )


# wire emission mutates the ordered shape list because bodies reference standalone wire records
def AddWiresMut(Shapes: list[ShapeRecord], Model: BrepModel, Graph: ModelGraph) -> None:
    for WireValue in Model.wires:
        FlagsText = "0101100" if WireValue.closed else "0101000"
        Children = GetEdgeChildren(Graph, WireValue.coedge_ids)
        Shapes.append(
            ShapeRecord(f"wire:{WireValue.id}", "Wi", (), FlagsText, Children)
        )


# face emission mutates the ordered shape list because shells consume proven loop orientation
def AddFacesMut(
    Shapes: list[ShapeRecord],
    Model: BrepModel,
    State: BrepWriteState,
    Tolerance: float,
) -> None:
    for FaceValue in Model.faces:
        GeometryLines = (
            f"0  {Number(max(Tolerance, FaceValue.tolerance))} {State.SurfaceIndexes[FaceValue.surface_id]} 0",
        )
        BandValue = State.SeamBands.get(FaceValue.id)
        Children = (
            ((f"loop:seam:{FaceValue.id}", False),)
            if BandValue is not None
            else tuple(
                (f"loop:{LoopId}", State.LoopReversals[LoopId])
                for LoopId in FaceValue.loop_ids
            )
        )
        Shapes.append(
            ShapeRecord(
                f"face:{FaceValue.id}", "Fa", GeometryLines, "0101000", Children
            )
        )


# shell emission mutates the ordered shape list because region records reference oriented shells
def AddShellRecsMut(
    Shapes: list[ShapeRecord], Model: BrepModel, State: BrepWriteState
) -> None:
    Graph = State.Graph
    for ShellValue in Model.shells:
        Children: list[tuple[str, bool]] = []
        for FaceUseId in ShellValue.face_use_ids:
            FaceUse = Graph.face_uses[FaceUseId]
            FaceValue = Graph.faces[FaceUse.face_id]
            Children.append(
                (f"face:{FaceValue.id}", State.FaceUseReversals[FaceUse.id])
            )
        FlagsText = "0101100" if ShellValue.closed else "0101000"
        Shapes.append(
            ShapeRecord(f"shell:{ShellValue.id}", "Sh", (), FlagsText, tuple(Children))
        )


# region emission mutates shapes and returns roots because bodies may reference shells directly
def AddRegionsMut(
    Shapes: list[ShapeRecord], Model: BrepModel, State: BrepWriteState
) -> dict[str, tuple[str, bool]]:
    Graph = State.Graph
    RegionRoots: dict[str, tuple[str, bool]] = {}
    for RegionValue in Model.regions:
        ShellChildren = tuple(
            (
                f"shell:{Graph.shell_uses[ShellUseId].shell_id}",
                State.ShellUseReversals[ShellUseId],
            )
            for ShellUseId in RegionValue.shell_use_ids
        )
        if RegionValue.solid:
            HasOpenShell = any(
                not Graph.shells[Graph.shell_uses[ValueId].shell_id].closed
                for ValueId in RegionValue.shell_use_ids
            )
            if HasOpenShell:
                Unsupported(f"solid region {RegionValue.id} contains an open shell")
            KeyValue = f"region:{RegionValue.id}"
            Shapes.append(ShapeRecord(KeyValue, "So", (), "0100000", ShellChildren))
            RegionRoots[RegionValue.id] = (KeyValue, False)
        elif len(ShellChildren) == 1:
            RegionRoots[RegionValue.id] = ShellChildren[0]
        else:
            KeyValue = f"region:{RegionValue.id}"
            Shapes.append(ShapeRecord(KeyValue, "Co", (), "0100000", ShellChildren))
            RegionRoots[RegionValue.id] = (KeyValue, False)
    return RegionRoots


# body emission mutates shapes and returns one root because the native stream ends with one reference
def AddBodiesMut(
    Shapes: list[ShapeRecord],
    Model: BrepModel,
    RegionRoots: Mapping[str, tuple[str, bool]],
) -> tuple[str, bool]:
    BodyRoots: list[tuple[str, bool]] = []
    for BodyValue in Model.bodies:
        Children = [RegionRoots[ValueId] for ValueId in BodyValue.region_ids]
        Children.extend((f"wire:{ValueId}", False) for ValueId in BodyValue.wire_ids)
        Children.extend(
            (f"vertex:{ValueId}", False) for ValueId in BodyValue.vertex_ids
        )
        if len(Children) == 1:
            BodyRoots.append(Children[0])
        else:
            KeyValue = f"body:{BodyValue.id}"
            Shapes.append(ShapeRecord(KeyValue, "Co", (), "0100000", tuple(Children)))
            BodyRoots.append((KeyValue, False))
    if len(BodyRoots) == 1:
        return BodyRoots[0]
    RootKey = "model:root"
    Shapes.append(ShapeRecord(RootKey, "Co", (), "1100000", tuple(BodyRoots)))
    return RootKey, False


# this definition exists because focused behavior needs one stable owner
def BrepModelBrep(Model: BrepModel, Tolerance: float = 1e-07) -> bytes:
    ValidateBrep(Model, Tolerance)
    State = BuildBrepState(Model, Tolerance)
    Lines = list(State.HeaderLines)
    Shapes: list[ShapeRecord] = []
    AddVerticesMut(Shapes, Model, Tolerance)
    AddEdgesMut(Shapes, Model, State, Tolerance)
    AddSeamEdgesMut(Shapes, State, Tolerance)
    AddLoopsMut(Shapes, Model, State)
    AddSeamLoopsMut(Shapes, State)
    AddWiresMut(Shapes, Model, State.Graph)
    AddFacesMut(Shapes, Model, State, Tolerance)
    AddShellRecsMut(Shapes, Model, State)
    RegionRoots = AddRegionsMut(Shapes, Model, State)
    RootValue = AddBodiesMut(Shapes, Model, RegionRoots)
    Lines.extend(ShapeLines(Shapes, RootValue))
    return ("\n".join(Lines) + "\n").encode("ascii")


# this definition exists because focused behavior needs one stable owner
def ProvenAsciiBrep(DataValue: bytes) -> bytes | None:
    if not isinstance(DataValue, bytes):
        raise TypeError("data must be bytes")
    from convert.geometry.Opencascade import decode_ascii_brep as DecodeAsciiBrep

    Model = DecodeAsciiBrep(DataValue, id_prefix="freecad:proof")
    if Model is None:
        return None
    try:
        return BrepModelBrep(Model)
    except FreeCadBrep:
        return None


# this definition exists because focused behavior needs one stable owner
def TriangleMesh(
    Vertices: Sequence[Any], Triangles: Sequence[Any], Tolerance: float = 1e-07
) -> bytes:
    if not MathValue.isfinite(Tolerance) or Tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")
    Points = tuple((Point(Vertex) for Vertex in Vertices))
    Declared = tuple((ParseTriangle(Triangle, len(Points)) for Triangle in Triangles))
    if not Declared:
        raise ValueError("at least one triangle is required")
    Facets = tuple(
        (Facet for Facet in Declared if not IsFacetBad(Points, Facet, Tolerance))
    )
    if not Facets:
        raise ValueError("at least one triangle area must exceed the BRep tolerance")
    Oriented = OrientFacets(Points, Facets, Tolerance)
    if Oriented is None:
        return IndependentBrep(Points, Facets, Tolerance)
    OrientedFacets, Components, Closed = Oriented
    return SharedBrep(Points, OrientedFacets, Components, Closed, Tolerance)


# this binding exists because shared behavior needs one stable value
globals()["Any"] = AnyValue

# this binding exists because shared behavior needs one stable value
globals()["FreeCADBrepWriteError"] = FreeCadBrep

# this binding exists because shared behavior needs one stable value
globals()["Geometry"] = KGeomValue

# this binding exists because shared behavior needs one stable value
globals()["Point"] = KPoint

# this binding exists because shared behavior needs one stable value
globals()["Triangle"] = KTriangle

# this binding exists because shared behavior needs one stable value
globals()["Vector2"] = VectorTwo

# this binding exists because shared behavior needs one stable value
globals()["Vector3"] = VectorThree

# this binding exists because shared behavior needs one stable value
globals()["_EdgePcurve"] = EdgePcurve

# this binding exists because shared behavior needs one stable value
globals()["_GeneratedPcurve"] = GeneratedPcurve

# this binding exists because shared behavior needs one stable value
globals()["_ModelGraph"] = ModelGraph

# this binding exists because shared behavior needs one stable value
globals()["_SeamBand"] = SeamBand

# this binding exists because shared behavior needs one stable value
globals()["_ShapeRecord"] = ShapeRecord

# this binding exists because shared behavior needs one stable value
globals()["_bind_once"] = BindOnceMut

# this binding exists because shared behavior needs one stable value
globals()["_bspline_layout"] = BsplineLayout

# this binding exists because shared behavior needs one stable value
globals()["_check_edge_geometry"] = CheckEdgeGeom

# this binding exists because shared behavior needs one stable value
globals()["_coedge_shape_reversed"] = HasCoedgeShape

# this binding exists because shared behavior needs one stable value
globals()["_cross"] = Cross

# this binding exists because shared behavior needs one stable value
globals()["_curve_point"] = CurvePoint

# this binding exists because shared behavior needs one stable value
globals()["_curve_record"] = CurveRecord

# this binding exists because shared behavior needs one stable value
globals()["_dot"] = DotAction

# this binding exists because shared behavior needs one stable value
globals()["_edge_geometry"] = EdgeGeom

# this binding exists because shared behavior needs one stable value
globals()["_edge_pcurve_records"] = EdgePcurveA

# this binding exists because shared behavior needs one stable value
globals()["_edge_record"] = EdgeRecord

# this binding exists because shared behavior needs one stable value
globals()["_edge_uses"] = EdgeUses

# this binding exists because shared behavior needs one stable value
globals()["_face_edge_orientations"] = FaceEdge

# this binding exists because shared behavior needs one stable value
globals()["_face_is_proven"] = FaceIsProven

# this binding exists because shared behavior needs one stable value
globals()["_face_loop_reversals"] = FaceLoop

# this binding exists because shared behavior needs one stable value
globals()["_facet_is_degenerate"] = IsFacetBad

# this binding exists because shared behavior needs one stable value
globals()["_frame"] = Frame

# this binding exists because shared behavior needs one stable value
globals()["_generated_pcurve"] = GeneratedPcurvA

# this binding exists because shared behavior needs one stable value
globals()["_geometry"] = GeomAction

# this binding exists because shared behavior needs one stable value
globals()["_header"] = Header

# this binding exists because shared behavior needs one stable value
globals()["_independent_brep"] = IndependentBrep

# this binding exists because shared behavior needs one stable value
globals()["_length"] = GetLength

# this binding exists because shared behavior needs one stable value
globals()["_linear_surface_pcurve"] = LinearSurface

# this binding exists because shared behavior needs one stable value
globals()["_loop_uv_points"] = LoopUvPoints

# this binding exists because shared behavior needs one stable value
globals()["_number"] = Number

# this binding exists because shared behavior needs one stable value
globals()["_oriented_components"] = OrientFacets

# this binding exists because shared behavior needs one stable value
globals()["_pcurve_record"] = PcurveRecord

# this binding exists because shared behavior needs one stable value
globals()["_planar_circle_loop"] = PlanarCircle

# this binding exists because shared behavior needs one stable value
globals()["_planar_line_loop_is_proven"] = IsPlanarLoop

# this binding exists because shared behavior needs one stable value
globals()["_plane_conic_pcurve"] = PlaneConic

# this binding exists because shared behavior needs one stable value
globals()["_point"] = Point

# this binding exists because shared behavior needs one stable value
globals()["_require_owned"] = RequireOwned

# this binding exists because shared behavior needs one stable value
globals()["_scale"] = ScaleVector

# this binding exists because shared behavior needs one stable value
globals()["_seam_band"] = SeamBandA

# this binding exists because shared behavior needs one stable value
globals()["_shape_lines"] = ShapeLines

# this binding exists because shared behavior needs one stable value
globals()["_shared_brep"] = SharedBrep

# this binding exists because shared behavior needs one stable value
globals()["_shell_face_orientations"] = ShellFace

# this binding exists because shared behavior needs one stable value
globals()["_shell_use_orientations"] = ShellUse

# this binding exists because shared behavior needs one stable value
globals()["_subtract"] = Subtract

# this binding exists because shared behavior needs one stable value
globals()["_surface_periods"] = SurfacePeriods

# this binding exists because shared behavior needs one stable value
globals()["_surface_record"] = SurfaceRecord

# this binding exists because shared behavior needs one stable value
globals()["_surface_residual"] = SurfaceResidual

# this binding exists because shared behavior needs one stable value
globals()["_surface_uv"] = SurfaceUv

# this binding exists because shared behavior needs one stable value
globals()["_triangle"] = ParseTriangle

# this binding exists because shared behavior needs one stable value
globals()["_unit2"] = UnitTwo

# this binding exists because shared behavior needs one stable value
globals()["_unit3"] = UnitThree

# this binding exists because shared behavior needs one stable value
globals()["_unsupported"] = Unsupported

# this binding exists because shared behavior needs one stable value
globals()["_unwrap_periodic"] = UnwrapPeriodic

# this binding exists because shared behavior needs one stable value
globals()["_unwrap_surface_uv"] = UnwrapSurfaceUv

# this binding exists because shared behavior needs one stable value
globals()["_values"] = Values

# this binding exists because shared behavior needs one stable value
globals()["_vector2"] = VectorTwoA

# this binding exists because shared behavior needs one stable value
globals()["_vector3"] = VectorThreeA

# this binding exists because shared behavior needs one stable value
globals()["_vertex_record"] = VertexRecord

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["brep_model_brep"] = BrepModelBrep

# this binding exists because shared behavior needs one stable value
globals()["dataclass"] = Dataclass

# this binding exists because shared behavior needs one stable value
globals()["deque"] = Deque

# this binding exists because shared behavior needs one stable value
globals()["math"] = MathValue

# this binding exists because shared behavior needs one stable value
globals()["proven_ascii_brep"] = ProvenAsciiBrep

# this binding exists because shared behavior needs one stable value
globals()["triangle_mesh_brep"] = TriangleMesh
