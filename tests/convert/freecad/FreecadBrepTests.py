# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
from dataclasses import replace as Replace
import hashlib as Hashlib
import io as IoStream
import os as OsModule
from pathlib import Path as FilePath
import subprocess as Subprocess
import xml.etree.ElementTree as XmlTree
import zipfile as Zipfile
import pytest as Pytest

# this binding keeps fixture paths aligned with the imported pathlib contract
Path = FilePath
from convert.Security.PathBoundary import ResolveTemp
from convert.Security.ProgramBoundary import GetFreecadPath
from convert import (
    ApplicationUsabilityError as AppUsabilityError,
    open_document as OpenDoc,
    write_document as WriteDoc,
)
from convert.adapters.base.TransferContract import CarrierReason, TransferMode
from convert.adapters.freecad import FreeCADAdapter as FreeCadAdapter
from convert.adapters.freecad.Brep import (
    FreeCADBrepWriteError as FreeCadBrepWriteError,
    brep_model_brep as BrepModelBrep,
    proven_ascii_brep as ProvenAsciiBrep,
    triangle_mesh_brep as TriangleMeshBrep,
)
from convert.geometry.Opencascade import (
    decode_ascii_brep as DecodeAsciiBrep,
    is_structurally_valid_ascii_brep as IsStructurallyValidAscii,
)
from interchange import (
    BrepBody,
    BrepCoedge,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepPayload,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepVertex,
    BrepWire,
    CadDocument as CadDoc,
    CadSource,
    CircleCurve,
    CirclePcurve,
    ConeSurface,
    Configuration as Config,
    CylinderSurface,
    EllipseCurve,
    LineCurve,
    LinePcurve,
    Mesh as MeshRecord,
    NativeCurve,
    NurbsCurve,
    NurbsPcurve,
    NurbsSurface,
    OffsetSurface,
    PayloadRole,
    Provenance,
    SphereSurface,
    TorusSurface,
    Transform,
    Vector2 as VectorTwo,
    Vector3 as VectorThree,
    frozen_mapping as FrozenMapping,
)
from interchange.brep.topology.BrepModel import BrepModel
from interchange.enums.EnumDocument import Capability
from tests.interchange.brep.BrepTests import triangle_brep as TriangleBrep

# this binding exists because shared behavior needs one stable value
KOracle = GetFreecadPath()

# this binding exists because shared behavior needs one stable value
KRootValue = FilePath(__file__).parents[3]


# this definition exists because focused behavior needs one stable owner
def RawBrepDoc(DataValue: bytes) -> CadDoc:
    Payload = BrepPayload(
        "payload:brep",
        "freecad.brep",
        "shape",
        "Open CASCADE ASCII BRep V1",
        Hashlib.sha256(DataValue).hexdigest(),
        DataValue,
        role=PayloadRole.BREP,
        file_extension=".brp",
    )
    return CadDoc(
        source=CadSource("test", "shape.brp", ""),
        configurations=(Config("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep_payloads=(Payload,),
        capabilities=frozenset({Capability.BREP, Capability.NATIVE_PAYLOADS}),
    )


# this definition exists because focused behavior needs one stable owner
def CylinderBand() -> BrepModel:
    Vertices = (
        BrepVertex("vertex:lower", VectorThree(10.0, 0.0, 0.0)),
        BrepVertex("vertex:upper", VectorThree(10.0, 0.0, 20.0)),
    )
    Curves = (
        CircleCurve(
            "curve:lower",
            VectorThree(0.0, 0.0, 0.0),
            VectorThree(0.0, 0.0, 1.0),
            VectorThree(1.0, 0.0, 0.0),
            10.0,
        ),
        CircleCurve(
            "curve:upper",
            VectorThree(0.0, 0.0, 20.0),
            VectorThree(0.0, 0.0, 1.0),
            VectorThree(1.0, 0.0, 0.0),
            10.0,
        ),
    )
    Edges = (
        BrepEdge(
            "edge:lower",
            "vertex:lower",
            "vertex:lower",
            "curve:lower",
            0.0,
            2.0 * 3.141592653589793,
        ),
        BrepEdge(
            "edge:upper",
            "vertex:upper",
            "vertex:upper",
            "curve:upper",
            0.0,
            2.0 * 3.141592653589793,
        ),
    )
    Coedges = (
        BrepCoedge("coedge:lower", "edge:lower"),
        BrepCoedge("coedge:upper", "edge:upper"),
    )
    return BrepModel(
        curves=Curves,
        surfaces=(
            CylinderSurface(
                "surface:cylinder",
                VectorThree(0.0, 0.0, 0.0),
                VectorThree(0.0, 0.0, 1.0),
                VectorThree(1.0, 0.0, 0.0),
                10.0,
            ),
        ),
        vertices=Vertices,
        edges=Edges,
        coedges=Coedges,
        loops=(
            BrepLoop("loop:lower", ("coedge:lower",), True),
            BrepLoop("loop:upper", ("coedge:upper",), False),
        ),
        faces=(
            BrepFace("face:cylinder", "surface:cylinder", ("loop:lower", "loop:upper")),
        ),
        face_uses=(BrepFaceUse("face-use:cylinder", "face:cylinder"),),
        shells=(BrepShell("shell:cylinder", ("face-use:cylinder",), False),),
        shell_uses=(BrepShellUse("shell-use:cylinder", "shell:cylinder"),),
        regions=(BrepRegion("region:cylinder", ("shell-use:cylinder",), False),),
        bodies=(
            BrepBody(
                "brep-body:cylinder", ("region:cylinder",), Transform(), "body:cylinder"
            ),
        ),
    )


# this definition exists because focused behavior needs one stable owner
def TestTriangleIs() -> None:
    Vertices = ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 3.0, 0.0), (0, 3, 0))
    Triangles = ((0, 1, 2), (0, 2, 3))
    First = TriangleMeshBrep(Vertices, Triangles)
    Second = TriangleMeshBrep(Vertices, Triangles)
    assert First == Second
    assert First.startswith(b"DBRep_DrawableShape\n\nCASCADE Topology V1")
    assert b"Curves 5\n" in First
    assert b"Surfaces 2\n" in First
    assert b"TShapes 14\n" in First
    assert b"\nSh\n" in First
    assert First.endswith(b"\n+1 0 \n")


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("Vertices", "Triangles", "Message"),
    [
        (((0, 0, 0), (1, 0, 0)), ((0, 1, 2),), "in range"),
        (((0, 0, 0), (1, 0, 0), (2, 0, 0)), ((0, 1, 2),), "area"),
        (((0, 0, 0), (1, 0, 0), (0, 1, 0)), (), "at least one"),
    ],
)
def TestTriangle(
    Vertices: tuple[tuple[float, float, float], ...],
    Triangles: tuple[tuple[int, int, int], ...],
    Message: str,
) -> None:
    with Pytest.raises(ValueError, match=Message):
        TriangleMeshBrep(Vertices, Triangles)


# this definition exists because focused behavior needs one stable owner
def TestTriangleFor() -> None:
    Result = TriangleMeshBrep(
        ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1)),
        ((0, 1, 2), (1, 0, 3), (0, 1, 4)),
    )
    assert b"TShapes 25\n" in Result
    assert b"\nCo\n" in Result


# this definition exists because focused behavior needs one stable owner
def TestNeutralBrep() -> None:
    Model = TriangleBrep()
    First = BrepModelBrep(Model)
    Second = BrepModelBrep(Model)
    assert First == Second
    assert First.startswith(b"DBRep_DrawableShape\n\nCASCADE Topology V1")
    assert b"Curve2ds 3\n" in First
    assert b"Curves 3\n" in First
    assert b"Surfaces 1\n" in First
    assert b"TShapes 9\n" in First
    assert b"\nFa\n0  9.9999999999999995e-08 1 0\n" in First
    assert First.endswith(b"\n+1 0 \n")


# this definition exists because focused behavior needs one stable owner
def TestPeriodic() -> None:
    Encoded = BrepModelBrep(CylinderBand())
    assert IsStructurallyValidAscii(Encoded)
    assert b"Curve2ds 4\n" in Encoded
    assert b"Curves 3\n" in Encoded
    assert b"TShapes 8\n" in Encoded
    assert b"3  3 4 CN 1 0 0 20\n" in Encoded


# this definition exists because focused behavior needs one stable owner
def TestPeriodicAs() -> None:
    EncodedData = BrepModelBrep(CylinderBand())
    DecodedData = DecodeAsciiBrep(EncodedData, id_prefix="cylinder-proof")
    assert DecodedData is not None
    assert not DecodedData.validate()
    assert len(DecodedData.curves) == 3
    assert isinstance(DecodedData.curves[0], CircleCurve)
    assert isinstance(DecodedData.curves[1], CircleCurve)
    assert isinstance(DecodedData.curves[2], LineCurve)
    assert len(DecodedData.surfaces) == 1
    assert isinstance(DecodedData.surfaces[0], CylinderSurface)
    assert len(DecodedData.bodies) == 1


# this definition exists because focused behavior needs one stable owner
def TestSuppliedThe() -> None:
    Expected = {
        "Random/Addons/Belt_tensioner_pulley.SLDPRT",
        "Random/Cylinder_heads/Cylinder_head.SLDPRT",
        "Random/Cylinder_heads/Exhaust_manifold.SLDPRT",
        "Random/Cylinder_heads/Exhaust_manifold_2.SLDPRT",
        "Random/Cylinder_heads/Timing_belt_roller.SLDPRT",
        "Random/Cylinder_heads/Timing_belt_roller_2.SLDPRT",
        "Random/Pistons/Piston.SLDPRT",
        "Random/Pistons/Piston_ring.SLDPRT",
        "Random/Pistons/Piston_shaft.SLDPRT",
        "Single Turbo Dual Overhead Cam V8 - KDP - 2024/10MM x 20MM x 13MM head 316 Stainless Steel Socket Head Screw.SLDPRT",
        "Single Turbo Dual Overhead Cam V8 - KDP - 2024/8MM x 15mm - 12 point screw.SLDPRT",
        "Single Turbo Dual Overhead Cam V8 - KDP - 2024/CUIETA DE ENTRADA DE GASES.SLDPRT",
        "Single Turbo Dual Overhead Cam V8 - KDP - 2024/SEGUIDOR DE LEVA.SLDPRT",
    }
    Expected = {
        PathValue
        for PathValue in Expected
        if (KRootValue / "examples" / PathValue).is_file()
    }
    Accepted: set[str] = set()
    for Source in sorted((KRootValue / "examples").rglob("*.SLDPRT")):
        if not Source.is_file() or Source.name.startswith("~$"):
            continue
        DocValue = OpenDoc(Source)
        if DocValue.brep is None:
            continue
        try:
            Encoded = BrepModelBrep(DocValue.brep)
        except FreeCadBrepWriteError:
            continue
        assert IsStructurallyValidAscii(Encoded)
        Accepted.add(Source.relative_to(KRootValue / "examples").as_posix())
    assert Accepted == Expected


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.parametrize(
    ("Collection", "Entity"),
    (
        (
            "curves",
            CircleCurve(
                "curve:circle",
                VectorThree(0.0, 0.0, 0.0),
                VectorThree(0.0, 0.0, 1.0),
                VectorThree(1.0, 0.0, 0.0),
                1.0,
            ),
        ),
        (
            "curves",
            EllipseCurve(
                "curve:ellipse",
                VectorThree(0.0, 0.0, 0.0),
                VectorThree(0.0, 0.0, 1.0),
                VectorThree(1.0, 0.0, 0.0),
                2.0,
                1.0,
            ),
        ),
        (
            "curves",
            NurbsCurve(
                "curve:nurbs",
                1,
                (VectorThree(0.0, 0.0, 0.0), VectorThree(1.0, 0.0, 0.0)),
                (0.0, 1.0),
                (2, 2),
            ),
        ),
        (
            "pcurves",
            LinePcurve("pcurve:line", VectorTwo(0.0, 0.0), VectorTwo(1.0, 0.0)),
        ),
        ("pcurves", CirclePcurve("pcurve:circle", VectorTwo(0.0, 0.0), 1.0)),
        (
            "pcurves",
            NurbsPcurve(
                "pcurve:nurbs",
                1,
                (VectorTwo(0.0, 0.0), VectorTwo(1.0, 0.0)),
                (0.0, 1.0),
                (2, 2),
            ),
        ),
        (
            "surfaces",
            CylinderSurface(
                "surface:cylinder",
                VectorThree(0.0, 0.0, 0.0),
                VectorThree(0.0, 0.0, 1.0),
                VectorThree(1.0, 0.0, 0.0),
                1.0,
            ),
        ),
        (
            "surfaces",
            ConeSurface(
                "surface:cone",
                VectorThree(0.0, 0.0, 0.0),
                VectorThree(0.0, 0.0, 1.0),
                VectorThree(1.0, 0.0, 0.0),
                1.0,
                0.5,
            ),
        ),
        (
            "surfaces",
            SphereSurface(
                "surface:sphere",
                VectorThree(0.0, 0.0, 0.0),
                VectorThree(0.0, 0.0, 1.0),
                VectorThree(1.0, 0.0, 0.0),
                1.0,
            ),
        ),
        (
            "surfaces",
            TorusSurface(
                "surface:torus",
                VectorThree(0.0, 0.0, 0.0),
                VectorThree(0.0, 0.0, 1.0),
                VectorThree(1.0, 0.0, 0.0),
                2.0,
                0.5,
            ),
        ),
        (
            "surfaces",
            NurbsSurface(
                "surface:nurbs",
                1,
                1,
                (
                    (VectorThree(0.0, 0.0, 0.0), VectorThree(0.0, 1.0, 0.0)),
                    (VectorThree(1.0, 0.0, 0.0), VectorThree(1.0, 1.0, 0.0)),
                ),
                (0.0, 1.0),
                (0.0, 1.0),
                (2, 2),
                (2, 2),
            ),
        ),
        ("surfaces", OffsetSurface("surface:offset", "surface:0", 1.0)),
    ),
    ids=(
        "circle-curve",
        "ellipse-curve",
        "nurbs-curve",
        "line-pcurve",
        "circle-pcurve",
        "nurbs-pcurve",
        "cylinder-surface",
        "cone-surface",
        "sphere-surface",
        "torus-surface",
        "nurbs-surface",
        "offset-surface",
    ),
)
def TestOpenCascade(Collection: str, Entity: object) -> None:
    Model = TriangleBrep()
    Narrowed = Replace(Model, **{Collection: (*getattr(Model, Collection), Entity)})
    Encoded = BrepModelBrep(Narrowed)
    assert IsStructurallyValidAscii(Encoded)


# this definition exists because focused behavior needs one stable owner
def Decoded(Prefix: str, XOffset: float = 0.0) -> BrepModel:
    Vertices = (
        (XOffset, 0.0, 0.0),
        (XOffset + 2.0, 0.0, 0.0),
        (XOffset, 3.0, 0.0),
        (XOffset, 0.0, 4.0),
    )
    Encoded = TriangleMeshBrep(Vertices, ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)))
    Model = DecodeAsciiBrep(Encoded, id_prefix=Prefix)
    assert Model is not None
    return Model


# this definition exists because focused behavior needs one stable owner
def TestSolid() -> None:
    Model = Decoded("encoder:solid")
    Encoded = BrepModelBrep(Model)
    Restored = DecodeAsciiBrep(Encoded, id_prefix="proof:solid")
    assert Restored is not None
    assert len(Restored.regions) == 1
    assert Restored.regions[0].solid
    assert Restored.shells[0].closed
    assert Restored.validate() == ()


# this definition exists because focused behavior needs one stable owner
def TestMultipleAs() -> None:
    First = Decoded("encoder:first")
    Second = Decoded("encoder:second", 10.0)
    Model = BrepModel(
        curves=(*First.curves, *Second.curves),
        surfaces=(*First.surfaces, *Second.surfaces),
        vertices=(*First.vertices, *Second.vertices),
        edges=(*First.edges, *Second.edges),
        coedges=(*First.coedges, *Second.coedges),
        loops=(*First.loops, *Second.loops),
        faces=(*First.faces, *Second.faces),
        face_uses=(*First.face_uses, *Second.face_uses),
        shells=(*First.shells, *Second.shells),
        shell_uses=(*First.shell_uses, *Second.shell_uses),
        regions=(*First.regions, *Second.regions),
        bodies=(*First.bodies, *Second.bodies),
    )
    assert Model.validate() == ()
    Encoded = BrepModelBrep(Model)
    assert b"\nCo\n" in Encoded
    Restored = DecodeAsciiBrep(Encoded, id_prefix="proof:multiple")
    assert Restored is not None
    assert len(Restored.regions) == 2
    assert all((Region.solid for Region in Restored.regions))
    assert Restored.validate() == ()


# this definition exists because focused behavior needs one stable owner
def TestFreeWireIs() -> None:
    Model = TriangleBrep()
    WireValue = BrepWire(
        "wire:free", tuple((Coedge.id for Coedge in Model.coedges)), closed=True
    )
    Narrowed = Replace(
        Model,
        loops=(),
        wires=(WireValue,),
        faces=(),
        face_uses=(),
        shells=(),
        shell_uses=(),
        regions=(),
        bodies=(
            Replace(
                Model.bodies[0],
                region_ids=(),
                design_body_id="",
                wire_ids=(WireValue.id,),
            ),
        ),
    )
    assert Narrowed.validate() == ()
    Encoded = BrepModelBrep(Narrowed)
    assert IsStructurallyValidAscii(Encoded)
    assert b"\nWi\n" in Encoded


# this definition exists because focused behavior needs one stable owner
def TestNeutralBreA() -> None:
    Model = TriangleBrep()
    Unsupported = Replace(
        Model,
        curves=(
            NativeCurve(Model.curves[0].id, "catia", "cgm_curve"),
            *Model.curves[1:],
        ),
    )
    with Pytest.raises(
        FreeCadBrepWriteError, match="writer_unimplemented.*NativeCurve"
    ) as Error:
        BrepModelBrep(Unsupported)
    assert Error.value.reason == "writer_unimplemented"


# this definition exists because focused behavior needs one stable owner
def TestNeutralBreB() -> None:
    Model = TriangleBrep()
    Transformed = Replace(
        Model,
        bodies=(
            Replace(
                Model.bodies[0], transform=Transform(origin=VectorThree(1.0, 0.0, 0.0))
            ),
        ),
    )
    with Pytest.raises(
        FreeCadBrepWriteError, match="writer_unimplemented.*identity body transforms"
    ):
        BrepModelBrep(Transformed)


# this definition exists because focused behavior needs one stable owner
def TestSupportedIs() -> None:
    Model = TriangleBrep()
    Model = Replace(Model, bodies=(Replace(Model.bodies[0], design_body_id=""),))
    DocValue = CadDoc(
        source=CadSource("json", "triangle.json", ""),
        configurations=(Config("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep=Model,
        capabilities=frozenset({Capability.BREP}),
    )
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    assert Capability.BREP in Result.native_capabilities
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        ShapeNames = [
            NameValue
            for NameValue in Archive.namelist()
            if NameValue.endswith(".Shape.brp")
        ]
        assert ShapeNames == ["BRep.Shape.brp"]
        assert Archive.read(ShapeNames[0]) == BrepModelBrep(Model)
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
    assert any(
        (
            Value.get("type") == "Part::Feature" and Value.get("name") == "BRep"
            for Value in RootValue.findall("./Objects/Object")
        )
    )


# this definition exists because focused behavior needs one stable owner
def TestPublicSdkAs(TmpPath: Path) -> None:
    Model = TriangleBrep()
    Model = Replace(Model, bodies=(Replace(Model.bodies[0], design_body_id=""),))
    DocValue = CadDoc(
        source=CadSource("json", "triangle.json", ""),
        configurations=(Config("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep=Model,
        capabilities=frozenset({Capability.BREP}),
    )
    Target = TmpPath / "triangle.FCStd"
    Result = WriteDoc(DocValue, Target)
    assert Result.near_lossless is True
    assert Capability.BREP in Result.native_capabilities
    assert OpenDoc(Target).brep == Model


# this definition exists because focused behavior needs one stable owner
def TestUnprovenTo() -> None:
    Model = TriangleBrep()
    Surface = Model.surfaces[0]
    Unproven = Replace(
        Model,
        surfaces=(
            CylinderSurface(
                Surface.id,
                VectorThree(0.0, 0.0, 0.0),
                VectorThree(0.0, 0.0, 1.0),
                VectorThree(1.0, 0.0, 0.0),
                1.0,
            ),
        ),
        bodies=(Replace(Model.bodies[0], design_body_id=""),),
    )
    MeshValue = MeshRecord(
        "mesh:fallback",
        "Fallback",
        (
            VectorThree(0.0, 0.0, 0.0),
            VectorThree(1.0, 0.0, 0.0),
            VectorThree(0.0, 1.0, 0.0),
        ),
        ((0, 1, 2),),
    )
    DocValue = CadDoc(
        source=CadSource("json", "unproven.json", ""),
        configurations=(Config("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        meshes=(MeshValue,),
        brep=Unproven,
        capabilities=frozenset({Capability.BREP, Capability.TESSELLATION}),
    )
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    Transfers = {Value.capability: Value for Value in Result.transfers}
    assert Transfers[Capability.BREP].mode is TransferMode.CARRIER
    assert (
        Transfers[Capability.BREP].carrier_reason is CarrierReason.WRITER_UNIMPLEMENTED
    )
    assert Transfers[Capability.TESSELLATION].mode is TransferMode.NATIVE
    assert Result.application_usable is True
    assert Result.vendor_loadable is True
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        RootValue = XmlTree.fromstring(Archive.read("Document.xml"))
        MeshNames = {
            Value.get("name", "")
            for Value in RootValue.findall("./Objects/Object")
            if Value.get("type") == "Mesh::Feature"
        }
        assert MeshNames
        assert any(
            (
                BoolValue.get("value", "").casefold() in {"1", "true"}
                for Value in RootValue.findall("./ObjectData/Object")
                if Value.get("name") in MeshNames
                for PropValue in Value.findall(
                    "./Properties/Property[@name='Visibility']"
                )
                if (BoolValue := PropValue.find("Bool")) is not None
            )
        )
        Representations = {
            String.get("value")
            for PropValue in RootValue.findall(".//Property[@name='Representation']")
            if (String := PropValue.find("String")) is not None
        }
        assert "faceted" in Representations
        assert "neutral-brep" not in Representations
        ShapeEntries = [
            NameValue
            for NameValue in Archive.namelist()
            if NameValue.endswith(".Shape.brp")
        ]
        assert len(ShapeEntries) == 1
        assert IsStructurallyValidAscii(Archive.read(ShapeEntries[0]))
    Restored = FreeCadAdapter().read(Output.getvalue())
    assert Restored.brep == Unproven
    assert Restored.meshes == (MeshValue,)


# this definition exists because focused behavior needs one stable owner
def TestPublicSdkA(TmpPath: Path) -> None:
    DataValue = (
        b"DBRep_DrawableShape\n\nCASCADE Topology V1, (c) Open Cascade\nnot-a-brep\n"
    )
    DocValue = RawBrepDoc(DataValue)
    Blocked = TmpPath / "blocked.FCStd"
    with Pytest.raises(AppUsabilityError) as Captured:
        WriteDoc(DocValue, Blocked, allow_carrier=False)
    assert (
        Captured.value.carrier_reasons[Capability.BREP] is CarrierReason.SOURCE_OPAQUE
    )
    assert (
        Captured.value.carrier_reasons[Capability.NATIVE_PAYLOADS]
        is CarrierReason.SOURCE_OPAQUE
    )
    assert not Blocked.exists()
    Explicit = TmpPath / "explicit.FCStd"
    Result = WriteDoc(DocValue, Explicit, allow_carrier=True)
    assert Result.near_lossless is False
    Restored = OpenDoc(Explicit)
    assert Restored.brep_payloads[0].data == DataValue


# this definition exists because focused behavior needs one stable owner
def TestStructural() -> None:
    DataValue = BrepModelBrep(TriangleBrep()).replace(
        b"+6 0 +5 0 +4 0 *", b"-6 0 +5 0 +4 0 *"
    )
    assert IsStructurallyValidAscii(DataValue)
    assert ProvenAsciiBrep(DataValue) is None
    DocValue = RawBrepDoc(DataValue)
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    Transfers = {Value.capability: Value for Value in Result.transfers}
    assert Transfers[Capability.BREP].mode is TransferMode.CARRIER
    assert Transfers[Capability.BREP].carrier_reason is CarrierReason.SOURCE_OPAQUE
    assert Result.application_usable is False
    assert Result.vendor_loadable is True
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        assert not any(
            (NameValue.endswith(".Shape.brp") for NameValue in Archive.namelist())
        )
    assert FreeCadAdapter().read(Output.getvalue()).brep_payloads[0].data == DataValue


# this definition exists because focused behavior needs one stable owner
def TestForgedThe() -> None:
    DataValue = BrepModelBrep(TriangleBrep()).replace(
        b"+6 0 +5 0 +4 0 *", b"-6 0 +5 0 +4 0 *"
    )
    DocValue = RawBrepDoc(DataValue)
    Payload = Replace(
        DocValue.brep_payloads[0],
        source_stream="Forged.Shape.brp",
        provenance=Provenance("freecad.fcstd", "Forged.Shape", 1.0),
        attributes=FrozenMapping(
            {
                "freecad_object": "Forged",
                "freecad_property": "Shape",
                "freecad_property_data": {
                    "tag": "Property",
                    "attributes": {"name": "Shape", "type": "Part::PropertyPartShape"},
                    "children": (
                        {
                            "tag": "Part",
                            "attributes": {"file": "Forged.Shape.brp"},
                            "children": (),
                        },
                    ),
                },
            }
        ),
    )
    DocValue = Replace(DocValue, brep_payloads=(Payload,))
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    Transfers = {Value.capability: Value for Value in Result.transfers}
    assert Transfers[Capability.BREP].mode is TransferMode.CARRIER
    assert Transfers[Capability.NATIVE_PAYLOADS].mode is TransferMode.CARRIER
    assert Result.application_usable is False
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        assert not any(
            (NameValue.endswith(".Shape.brp") for NameValue in Archive.namelist())
        )
    assert FreeCadAdapter().read(Output.getvalue()).brep_payloads[0].data == DataValue


# this definition exists because focused behavior needs one stable owner
def TestPublicSdk(TmpPath: Path) -> None:
    DataValue = BrepModelBrep(TriangleBrep())
    DocValue = RawBrepDoc(DataValue)
    Target = TmpPath / "valid.FCStd"
    Result = WriteDoc(DocValue, Target)
    assert Result.near_lossless is False
    assert Capability.BREP in Result.native_capabilities
    assert Capability.NATIVE_PAYLOADS in Result.native_capabilities
    assert Capability.NATIVE_PAYLOADS in Result.carrier_capabilities
    Transfers = {Value.capability: Value for Value in Result.transfers}
    assert Transfers[Capability.NATIVE_PAYLOADS].mode is TransferMode.MIXED
    assert (
        Transfers[Capability.NATIVE_PAYLOADS].carrier_reason
        is CarrierReason.WRITER_UNIMPLEMENTED
    )
    with Zipfile.ZipFile(Target) as Archive:
        ShapeEntries = [
            NameValue
            for NameValue in Archive.namelist()
            if NameValue.endswith(".Shape.brp")
        ]
        assert len(ShapeEntries) == 1
        assert Archive.read(ShapeEntries[0]) == ProvenAsciiBrep(DataValue)
    assert OpenDoc(Target).brep_payloads[0].data == DataValue


# this definition exists because focused behavior needs one stable owner
def TestUnsupported() -> None:
    Model = TriangleBrep()
    Model = Replace(
        Model,
        curves=(
            NativeCurve(Model.curves[0].id, "catia", "cgm_curve"),
            *Model.curves[1:],
        ),
        bodies=(Replace(Model.bodies[0], design_body_id=""),),
    )
    DocValue = CadDoc(
        source=CadSource("catia", "triangle.CATPart", ""),
        configurations=(Config("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep=Model,
        capabilities=frozenset({Capability.BREP}),
    )
    Output = IoStream.BytesIO()
    Result = FreeCadAdapter().write(DocValue, Output)
    assert Capability.BREP in Result.carrier_capabilities
    assert Capability.BREP not in Result.native_capabilities
    assert Result.application_usable is False
    assert Result.vendor_loadable is True
    with Zipfile.ZipFile(IoStream.BytesIO(Output.getvalue())) as Archive:
        assert not any(
            (NameValue.endswith(".Shape.brp") for NameValue in Archive.namelist())
        )


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.skipif(not KOracle.is_file(), reason="KIT_FREECAD_ORACLE is unavailable")
def TestPeriodicIs(TmpPath: Path) -> None:
    PathValue = ResolveTemp(TmpPath / "cylinder-band.brp")
    PathValue.write_bytes(BrepModelBrep(CylinderBand()))
    CodeValue = "import os;import Part;s=Part.Shape();s.read(os.environ['KIT_ORACLE_PATH']);print('KIT_SEAM',s.ShapeType,len(s.Faces),len(s.Wires),len(s.Edges),len(s.Vertexes),s.isValid())"
    OracleEnv = OsModule.environ.copy()
    OracleEnv["KIT_ORACLE_PATH"] = str(PathValue)
    Completed = Subprocess.run(
        [str(KOracle), "-c", CodeValue],
        check=True,
        capture_output=True,
        env=OracleEnv,
        text=True,
        timeout=60,
    )
    LineValue = next(
        (
            Value
            for Value in Completed.stdout.splitlines()
            if Value.startswith("KIT_SEAM")
        )
    )
    assert LineValue.split()[1:] == ["Shell", "1", "1", "3", "2", "True"]


# this definition exists because focused behavior needs one stable owner
@Pytest.mark.skipif(not KOracle.is_file(), reason="KIT_FREECAD_ORACLE is unavailable")
def TestTriangleAs(TmpPath: Path) -> None:
    Tetrahedron = ResolveTemp(TmpPath / "tetrahedron.brp")
    Tetrahedron.write_bytes(
        TriangleMeshBrep(
            ((0, 0, 0), (2, 0, 0), (0, 3, 0), (0, 0, 4)),
            ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
        )
    )
    Square = ResolveTemp(TmpPath / "square.brp")
    Square.write_bytes(
        TriangleMeshBrep(
            ((0, 0, 0), (2, 0, 0), (2, 3, 0), (0, 3, 0)), ((0, 1, 2), (0, 2, 3))
        )
    )
    CodeValue = "import os;import Part;t=Part.Shape();t.read(os.environ['KIT_ORACLE_FIRST']);s=Part.Shape();s.read(os.environ['KIT_ORACLE_SECOND']);print('KIT_BREP',t.ShapeType,len(t.Solids),len(t.Faces),len(t.Edges),len(t.Vertexes),t.isValid(),t.Volume,t.BoundBox.XLength,t.BoundBox.YLength,t.BoundBox.ZLength,s.ShapeType,len(s.Faces),len(s.Edges),len(s.Vertexes),s.isValid())"
    OracleEnv = OsModule.environ.copy()
    OracleEnv["KIT_ORACLE_FIRST"] = str(Tetrahedron)
    OracleEnv["KIT_ORACLE_SECOND"] = str(Square)
    Completed = Subprocess.run(
        [str(KOracle), "-c", CodeValue],
        check=True,
        capture_output=True,
        env=OracleEnv,
        text=True,
        timeout=60,
    )
    LineValue = next(
        (
            Value
            for Value in Completed.stdout.splitlines()
            if Value.startswith("KIT_BREP")
        )
    )
    Values = LineValue.split()[1:]
    assert Values[:6] == ["Solid", "1", "4", "6", "4", "True"]
    assert tuple((float(Value) for Value in Values[6:10])) == Pytest.approx(
        (4.0, 2.0, 3.0, 4.0), abs=1e-12
    )
    assert Values[10:] == ["Shell", "2", "5", "4", "True"]


# this binding exists because shared behavior needs one stable value
globals()["ApplicationUsabilityError"] = AppUsabilityError

# this binding exists because shared behavior needs one stable value
globals()["CadDocument"] = CadDoc

# this binding exists because shared behavior needs one stable value
globals()["Configuration"] = Config

# this binding exists because shared behavior needs one stable value
globals()["ET"] = XmlTree

# this binding exists because shared behavior needs one stable value
globals()["FreeCADAdapter"] = FreeCadAdapter

# this binding exists because shared behavior needs one stable value
globals()["FreeCADBrepWriteError"] = FreeCadBrepWriteError

# this binding exists because shared behavior needs one stable value
globals()["Mesh"] = MeshRecord

# this binding exists because shared behavior needs one stable value
globals()["ORACLE"] = KOracle

# this binding exists because shared behavior needs one stable value
globals()["Path"] = FilePath

# this binding exists because shared behavior needs one stable value
globals()["ROOT"] = KRootValue

# this binding exists because shared behavior needs one stable value
globals()["Vector2"] = VectorTwo

# this binding exists because shared behavior needs one stable value
globals()["Vector3"] = VectorThree

# this binding exists because shared behavior needs one stable value
globals()["_cylinder_band_brep"] = CylinderBand

# this binding exists because shared behavior needs one stable value
globals()["_decoded_tetrahedron"] = Decoded

# this binding exists because shared behavior needs one stable value
globals()["_raw_brep_document"] = RawBrepDoc

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations

# this binding exists because shared behavior needs one stable value
globals()["brep_model_brep"] = BrepModelBrep

# this binding exists because shared behavior needs one stable value
globals()["decode_ascii_brep"] = DecodeAsciiBrep

# this binding exists because shared behavior needs one stable value
globals()["frozen_mapping"] = FrozenMapping

# this binding exists because shared behavior needs one stable value
globals()["hashlib"] = Hashlib

# this binding exists because shared behavior needs one stable value
globals()["io"] = IoStream

# this binding exists because shared behavior needs one stable value
globals()["is_structurally_valid_ascii_brep"] = IsStructurallyValidAscii

# this binding exists because shared behavior needs one stable value
globals()["open_document"] = OpenDoc

# this binding exists because shared behavior needs one stable value
globals()["os"] = OsModule

# this binding exists because shared behavior needs one stable value
globals()["proven_ascii_brep"] = ProvenAsciiBrep

# this binding exists because shared behavior needs one stable value
globals()["pytest"] = Pytest

# this binding exists because shared behavior needs one stable value
globals()["replace"] = Replace

# this binding exists because shared behavior needs one stable value
globals()["subprocess"] = Subprocess

# this binding exists because shared behavior needs one stable value
globals()["triangle_brep"] = TriangleBrep

# this binding exists because shared behavior needs one stable value
globals()["triangle_mesh_brep"] = TriangleMeshBrep

# this binding exists because shared behavior needs one stable value
globals()["write_document"] = WriteDoc

# this binding exists because shared behavior needs one stable value
globals()["zipfile"] = Zipfile
