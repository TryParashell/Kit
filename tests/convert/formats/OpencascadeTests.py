# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import hashlib as Hashlib
from pathlib import Path as PathValue

import pytest as PytestLib

from convert.adapters.freecad.Brep import TriangleMesh as TriangleMeshBrep
from convert.adapters.freecad.Native import (
    DecodedDocBrep,
    ReadNativeFcstd,
)
from convert.geometry.Opencascade import (
    CanonicalVerts,
    DecodeAsciiBrep,
    IsValidBrep as IsSVAB,
    ShapeRecord,
    VertexData,
)
from interchange import (
    Body as BodyValue,
    BrepPayload,
    PayloadRole,
    Vector3 as VectorThree,
)

# this binding exists because shared behavior needs one stable value
KExamples = PathValue(__file__).parents[3] / "examples" / "Random" / "V8_engine"


# this definition exists because focused behavior needs one stable owner
def TestCVRJTR() -> None:
    RecordsData = {
        1: ShapeRecord(
            b"Ve",
            "0101101",
            (),
            VertexData(
                1.0e-7,
                VectorThree(-4.253254041760199, 3.090169943749473, 5.0),
            ),
        ),
        2: ShapeRecord(
            b"Ve",
            "0101101",
            (),
            VertexData(
                1.0e-7,
                VectorThree(-4.253254041760199, 3.0901699437494736, 5.0),
            ),
        ),
    }
    CanonicalData = CanonicalVerts(RecordsData)
    assert CanonicalData[1] == CanonicalData[2]


# this definition exists because focused behavior needs one stable owner
def ReplaceGL(DataValueA: bytes, Table: bytes, Replacement: bytes) -> bytes:
    Lines = DataValueA.splitlines(keepends=True)
    TableIndex = next(
        Index for Index, LineValue in enumerate(Lines) if LineValue.startswith(Table)
    )
    Lines[TableIndex + 1] = Replacement + b"\n"
    return b"".join(Lines)


# this definition exists because focused behavior needs one stable owner
def LocatedTB() -> bytes:
    DataValueA = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0)),
        ((0, 1, 2),),
    )
    DataValueA = DataValueA.replace(
        b"Locations 0\n",
        b"Locations 1\n1\n1 0 0 0\n0 1 0 0\n0 0 1 0\n",
        1,
    )
    HeadValue, Separator, TailValue = DataValueA.rpartition(b"+1 0")
    assert Separator
    return HeadValue + b"+1 1" + TailValue


# this definition exists because focused behavior needs one stable owner
def FaceTF(Surface: int, TailValue: bytes) -> bytes:
    Surfaces = (
        b"Surfaces 0\n" if Surface == 0 else b"Surfaces 1\n1 0 0 0 0 0 1 1 0 0 0 1 0\n"
    )
    return b"".join(
        (
            b"DBRep_DrawableShape\n\n"
            b"CASCADE Topology V1, (c) Matra-Datavision\n"
            b"Locations 0\nCurve2ds 0\nCurves 0\nPolygon3D 0\n"
            b"PolygonOnTriangulations 0\n",
            Surfaces,
            b"Triangulations 1\n3 1 0 0\n0 0 0 1 0 0 0 1 0 1 2 3\nTShapes 1\nFa\n",
            f"0 0 {Surface} 0".encode("ascii"),
            TailValue,
            b"0101000\n*\n+1 0\n",
        )
    )


# this definition exists because focused behavior needs one stable owner
def PolygonTF() -> bytes:
    return b"".join(
        (
            b"DBRep_DrawableShape\n\n"
            b"CASCADE Topology V1, (c) Matra-Datavision\n"
            b"Locations 0\nCurve2ds 0\nCurves 0\nPolygon3D 0\n"
            b"PolygonOnTriangulations 1\n"
            b"2 1 4\np 0 0\n"
            b"Surfaces 0\nTriangulations 2\n"
            b"4 1 0 0\n"
            b"0 0 0 1 0 0 1 1 0 0 1 0 1 2 3\n"
            b"3 1 0 0\n"
            b"0 0 0 1 0 0 0 1 0 1 2 3\n"
            b"TShapes 3\n"
            b"Ve\n0 0 0 0 0 0\n0101101\n*\n"
            b"Ve\n0 1 0 0 0 0\n0101101\n*\n"
            b"Ed\n0 1 1 0\n6 1 1 0\n0\n0101000\n+3 0 -2 0 *\n"
            b"+1 0\n",
        )
    )


# this definition exists because focused behavior needs one stable owner
def TestABDNOST() -> None:
    DataValueA = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0)),
        ((0, 1, 2),),
    )
    Model = DecodeAsciiBrep(DataValueA, IdPrefix="test:triangle")
    assert Model is not None
    assert len(Model.curves) == 3
    assert len(Model.surfaces) == 1
    assert len(Model.vertices) == 3
    assert len(Model.edges) == 3
    assert len(Model.faces) == 1
    assert len(Model.shells) == 1
    assert len(Model.regions) == 1
    assert not Model.regions[0].solid
    assert Model.validate() == ()


# this definition exists because focused behavior needs one stable owner
def TestABDNCST() -> None:
    DataValueA = TriangleMeshBrep(
        ((0, 0, 0), (2, 0, 0), (0, 3, 0), (0, 0, 4)),
        ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )
    Model = DecodeAsciiBrep(DataValueA, IdPrefix="test:solid")
    assert Model is not None
    assert len(Model.faces) == 4
    assert len(Model.shells) == 1
    assert Model.shells[0].closed
    assert len(Model.regions) == 1
    assert Model.regions[0].solid
    assert Model.validate() == ()


# this definition exists because focused behavior needs one stable owner
def TestABDRNULD() -> None:
    DataValueA = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    Malformed = ReplaceGL(DataValueA, b"Curves ", b"1 0 0 0 2 0 0 ")
    assert DecodeAsciiBrep(Malformed) is None


# this definition exists because focused behavior needs one stable owner
def TestABDAIPF() -> None:
    DataValueA = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    Indirect = ReplaceGL(
        DataValueA,
        b"Surfaces ",
        b"1 0 0 0 0 0 1 1 0 0 0 -1 0 ",
    )
    assert DecodeAsciiBrep(Indirect) is not None


# this definition exists because focused behavior needs one stable owner
def TestABDRNPF() -> None:
    DataValueA = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    Malformed = ReplaceGL(
        DataValueA,
        b"Surfaces ",
        b"1 0 0 0 0 0 1 1 0 0 1 0 0 ",
    )
    assert DecodeAsciiBrep(Malformed) is None


# this definition exists because focused behavior needs one stable owner
def TestABDRUCF() -> None:
    DataValueA = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    Malformed = ReplaceGL(
        DataValueA,
        b"Curves ",
        b"3 0 0 0 0 0 1 1 0 0 0 1 0 2 1 ",
    )
    assert DecodeAsciiBrep(Malformed) is None


# this definition exists because focused behavior needs one stable owner
def TestABDACNL() -> None:
    DataValueA = LocatedTB()
    assert IsSVAB(DataValueA)
    Model = DecodeAsciiBrep(DataValueA)
    assert Model is not None
    assert Model.validate() == ()
    assert {
        (VertexA.point.x, VertexA.point.y, VertexA.point.z)
        for VertexA in Model.vertices
    } == {
        (0.0, 0.0, 0.0),
        (2.0, 0.0, 0.0),
        (0.0, 3.0, 0.0),
    }


# this definition exists because focused behavior needs one stable owner
def TestABDALT() -> None:
    DataValueA = LocatedTB().replace(
        b"1 0 0 0\n0 1 0 0\n0 0 1 0\n",
        b"1 0 0 11\n0 1 0 -7\n0 0 1 5\n",
        1,
    )
    Model = DecodeAsciiBrep(DataValueA)
    assert Model is not None
    assert {
        (VertexA.point.x, VertexA.point.y, VertexA.point.z)
        for VertexA in Model.vertices
    } == {
        (11.0, -7.0, 5.0),
        (13.0, -7.0, 5.0),
        (11.0, -4.0, 5.0),
    }
    ChildData = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0)),
        ((0, 1, 2),),
    ).replace(
        b"Locations 0\n",
        b"Locations 1\n1\n1 0 0 11\n0 1 0 -7\n0 0 1 5\n",
        1,
    )
    ShellHead, ShellMarker, ShellTail = ChildData.rpartition(b"+2 0 *")
    assert ShellMarker
    ChildModel = DecodeAsciiBrep(ShellHead + b"+2 1 *" + ShellTail)
    assert ChildModel is not None
    assert ChildModel.validate() == ()
    assert {
        (Vertex.point.x, Vertex.point.y, Vertex.point.z)
        for Vertex in ChildModel.vertices
    } == {
        (11.0, -7.0, 5.0),
        (13.0, -7.0, 5.0),
        (11.0, -4.0, 5.0),
    }


# this definition exists because focused behavior needs one stable owner
def TestABDCNLINO() -> None:
    DataValue = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 3.0, 0.0)),
        ((0, 1, 2),),
    )
    DataValue = DataValue.replace(
        b"Locations 0\n",
        b"Locations 2\n1\n0 -1 0 0\n1 0 0 0\n0 0 1 0\n1\n1 0 0 10\n0 1 0 0\n0 0 1 0\n",
        1,
    )
    DataValue = DataValue.replace(b"+2 0 *", b"+2 2 *", 1)
    HeadData, MarkerData, TailData = DataValue.rpartition(b"+1 0")
    assert MarkerData
    DecodedData = DecodeAsciiBrep(HeadData + b"+1 1" + TailData)
    assert DecodedData is not None
    assert DecodedData.validate() == ()
    assert {
        (VertexData.point.x, VertexData.point.y, VertexData.point.z)
        for VertexData in DecodedData.vertices
    } == {
        (10.0, 0.0, 0.0),
        (10.0, 2.0, 0.0),
        (7.0, 0.0, 0.0),
    }


# this definition exists because focused behavior needs one stable owner
def TestSVREPVL() -> None:
    DataValueA = LocatedTB()
    Version = b"CASCADE Topology V1, (c) Matra-Datavision"
    Split = DataValueA.replace(
        Version,
        b"CASCADE\nTopology V1, (c) Matra-Datavision",
        1,
    )
    UnsupportedFirst = DataValueA.replace(
        Version,
        b"CASCADE Topology V2, (c) Matra-Datavision\n" + Version,
        1,
    )
    Payload = DataValueA[DataValueA.index(Version) :]
    BareCarriageReturn = b"junk\r" + Payload
    assert not IsSVAB(Split)
    assert not IsSVAB(UnsupportedFirst)
    assert not IsSVAB(BareCarriageReturn)


# this definition exists because focused behavior needs one stable owner
def TestSVMLTN() -> None:
    DataValueA = LocatedTB()
    Location = b"1\n1 0 0 0\n0 1 0 0\n0 0 1 0\n"
    Unique = DataValueA.replace(
        b"Locations 1\n" + Location,
        b"Locations 2\n" + Location + b"2 1 2 0\n",
        1,
    )
    Duplicate = Unique.replace(b"2 1 2 0", b"2 1 1 0", 1)
    Identity = Unique.replace(b"2 1 2 0", b"2 1 1 1 -1 0", 1)
    Singular = DataValueA.replace(
        Location,
        b"1\n0 0 0 0\n0 0 0 0\n0 0 0 0\n",
        1,
    )
    assert IsSVAB(Unique)
    assert not IsSVAB(Duplicate)
    assert not IsSVAB(Identity)
    assert not IsSVAB(Singular)


# this definition exists because focused behavior needs one stable owner
def TestSVRFTLP() -> None:
    Immediate = FaceTF(1, b"\n2 1\n\n")
    SameLine = FaceTF(1, b" 2 1\n\n")
    BlankLine = FaceTF(1, b"\n\n2 1\n\n")
    Indented = FaceTF(1, b"\n 2 1\n\n")
    SplitIndex = FaceTF(1, b"\n2\n1\n\n")
    Trailing = FaceTF(1, b"\n2 1 0101000\n\n")
    SurfaceZeroValid = FaceTF(0, b"\n2 1\n\n")
    SurfaceZeroMissing = FaceTF(0, b"\n\n")
    assert IsSVAB(Immediate)
    assert not IsSVAB(SameLine)
    assert not IsSVAB(BlankLine)
    assert not IsSVAB(Indented)
    assert not IsSVAB(SplitIndex)
    assert not IsSVAB(Trailing)
    assert IsSVAB(SurfaceZeroValid)
    assert not IsSVAB(SurfaceZeroMissing)


# this definition exists because focused behavior needs one stable owner
def TestSVBPNTT() -> None:
    DataValueA = PolygonTF()
    Wrong = DataValueA.replace(b"6 1 1 0", b"6 1 2 0", 1)
    Closed = DataValueA.replace(
        b"PolygonOnTriangulations 1\n2 1 4\np 0 0\n",
        b"PolygonOnTriangulations 2\n2 1 2\np 0 0\n2 1 4\np 0 0\n",
        1,
    ).replace(b"6 1 1 0", b"7 1 2 1 0", 1)
    ClosedWrong = Closed.replace(b"7 1 2 1 0", b"7 1 2 2 0", 1)
    assert IsSVAB(DataValueA)
    assert not IsSVAB(Wrong)
    assert IsSVAB(Closed)
    assert not IsSVAB(ClosedWrong)


# this definition exists because focused behavior needs one stable owner
def TestSVRIOAB() -> None:
    DataValueA = LocatedTB()
    Tshapes = next(
        LineValue
        for LineValue in DataValueA.splitlines()
        if LineValue.startswith(b"TShapes ")
    )
    ShapeCount = int(Tshapes.split()[1])
    SurfaceLine = next(
        LineValue
        for Index, LineValue in enumerate(DataValueA.splitlines())
        if Index > 0 and DataValueA.splitlines()[Index - 1].startswith(b"Surfaces ")
    )
    SurfaceTokens = SurfaceLine.split()
    SurfaceTokens[-1] = b"0" * 40
    LongNumber = DataValueA.replace(
        SurfaceLine,
        b" ".join(SurfaceTokens),
        1,
    )
    RootHead, RootSeparator, RootTail = DataValueA.rpartition(b"+1 1")
    assert RootSeparator
    Malformed = (
        b"CASCADE Topology V1, (c) Matra-Datavision\n",
        DataValueA[: len(DataValueA) // 2],
        DataValueA[:-10],
        DataValueA + b" trailing",
        DataValueA.replace(b"V1,", b"V2,", 1),
        DataValueA.replace(Tshapes, f"TShapes {ShapeCount + 1}".encode("ascii"), 1),
        DataValueA.replace(b"+1 1", b"+999999 1", 1),
        DataValueA.replace(b"Locations 1\n1\n1 ", b"Locations 1\n1\nnan ", 1),
        LongNumber,
        RootHead + b"+2 1" + RootTail,
    )
    assert all(not IsSVAB(Value) for Value in Malformed)


# this definition exists because focused behavior needs one stable owner
def TestNFDOPFSAKR() -> None:
    PathValueA = KExamples / "Piston_shaft.FCStd"
    if not PathValueA.is_file():
        PytestLib.skip(f"bundled FreeCAD example is unavailable: {PathValueA.name}")
    Document = ReadNativeFcstd(PathValueA.read_bytes(), str(PathValueA))
    Payloads = tuple(
        Value for Value in Document.brep_payloads if Value.role == PayloadRole.BREP
    )
    assert len(Payloads) == 1
    assert Payloads[0].data is not None
    assert Document.brep is not None
    assert Document.brep.bodies[0].design_body_id == Document.bodies[0].id
    assert Document.brep.bodies[0].attributes["brep_payload_id"] == Payloads[0].id
    assert Document.brep.validate(frozenset({Document.bodies[0].id})) == ()


# this definition exists because focused behavior needs one stable owner
def TestNFLISRO() -> None:
    PathValueA = KExamples / "Alternator.FCStd"
    if not PathValueA.is_file():
        PytestLib.skip(f"bundled FreeCAD example is unavailable: {PathValueA.name}")
    Document = ReadNativeFcstd(PathValueA.read_bytes(), str(PathValueA))
    Payloads = tuple(
        Value for Value in Document.brep_payloads if Value.role == PayloadRole.BREP
    )
    assert len(Payloads) == 1
    assert Payloads[0].data is not None
    assert Payloads[0].attributes["feature_id"] != Document.bodies[0].final_feature_id
    assert Document.brep is None


# this definition exists because focused behavior needs one stable owner
def TestFSOMMDB() -> None:
    DataValueA = TriangleMeshBrep(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((0, 1, 2),),
    )
    Digest = Hashlib.sha256(DataValueA).hexdigest()
    Bodies = (
        BodyValue("body:first", "First", "feature:first"),
        BodyValue("body:second", "Second", "feature:second"),
    )
    Payloads = tuple(
        BrepPayload(
            f"payload:{Index}",
            "opencascade",
            "shape",
            "CASCADE Topology V1",
            Digest,
            data=DataValueA,
            attributes={"feature_id": BodyValueA.final_feature_id},
            role=PayloadRole.BREP,
            file_extension=".brep",
        )
        for Index, BodyValueA in enumerate(Bodies, 1)
    )
    Model = DecodedDocBrep(Payloads, Bodies)
    assert Model is not None
    assert {Value.design_body_id for Value in Model.bodies} == {
        "body:first",
        "body:second",
    }
    assert Model.validate(frozenset(Value.id for Value in Bodies)) == ()
    OwnedPayload = BrepPayload(
        "payload:owned",
        "opencascade",
        "shape",
        "CASCADE Topology V1",
        Digest,
        data=DataValueA,
        attributes={"body_id": Bodies[0].id},
        role=PayloadRole.BREP,
        file_extension=".brep",
    )
    SelectedModel = DecodedDocBrep(
        (OwnedPayload, *Payloads),
        Bodies,
    )
    assert SelectedModel is not None
    assert len(SelectedModel.bodies) == 2
