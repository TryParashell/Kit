from __future__ import annotations

from dataclasses import replace
import hashlib
import io
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile

import pytest

from convert import ApplicationUsabilityError, open_document, write_document
from convert.adapters.base import CarrierReason
from convert.adapters.freecad import FreeCADAdapter
from convert.adapters.freecad.brep import (
    FreeCADBrepWriteError,
    brep_model_brep,
    triangle_mesh_brep,
)
from convert.opencascade import decode_ascii_brep, is_structurally_valid_ascii_brep
from interchange import (
    BrepModel,
    BrepPayload,
    BrepWire,
    CadDocument,
    CadSource,
    CircleCurve,
    CirclePcurve,
    Capability,
    ConeSurface,
    Configuration,
    CylinderSurface,
    EllipseCurve,
    LinePcurve,
    NativeCurve,
    NurbsCurve,
    NurbsPcurve,
    NurbsSurface,
    OffsetSurface,
    PayloadRole,
    SphereSurface,
    TorusSurface,
    Transform,
    Vector2,
    Vector3,
)
from tests.interchange.test_brep import triangle_brep


ORACLE = Path(os.environ.get("KIT_FREECAD_ORACLE", ""))
ROOT = Path(__file__).parents[2]


def _raw_brep_document(data: bytes) -> CadDocument:
    payload = BrepPayload(
        "payload:brep",
        "freecad.brep",
        "shape",
        "Open CASCADE ASCII BRep V1",
        hashlib.sha256(data).hexdigest(),
        data,
        role=PayloadRole.BREP,
        file_extension=".brp",
    )
    return CadDocument(
        source=CadSource("test", "shape.brp", ""),
        configurations=(Configuration("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep_payloads=(payload,),
        capabilities=frozenset({Capability.BREP, Capability.NATIVE_PAYLOADS}),
    )


def test_triangle_mesh_brep_is_deterministic_open_cascade_serialization() -> None:
    vertices = ((0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 3.0, 0.0), (0, 3, 0))
    triangles = ((0, 1, 2), (0, 2, 3))
    first = triangle_mesh_brep(vertices, triangles)
    second = triangle_mesh_brep(vertices, triangles)
    assert first == second
    assert first.startswith(b"DBRep_DrawableShape\n\nCASCADE Topology V1")
    assert b"Curves 5\n" in first
    assert b"Surfaces 2\n" in first
    assert b"TShapes 14\n" in first
    assert b"\nSh\n" in first
    assert first.endswith(b"\n+1 0 \n")


@pytest.mark.parametrize(
    ("vertices", "triangles", "message"),
    [
        (((0, 0, 0), (1, 0, 0)), ((0, 1, 2),), "in range"),
        (((0, 0, 0), (1, 0, 0), (2, 0, 0)), ((0, 1, 2),), "area"),
        (((0, 0, 0), (1, 0, 0), (0, 1, 0)), (), "at least one"),
    ],
)
def test_triangle_mesh_brep_rejects_invalid_facets(
    vertices, triangles, message
) -> None:
    with pytest.raises(ValueError, match=message):
        triangle_mesh_brep(vertices, triangles)


def test_triangle_mesh_brep_falls_back_for_nonmanifold_edges() -> None:
    result = triangle_mesh_brep(
        ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1)),
        ((0, 1, 2), (1, 0, 3), (0, 1, 4)),
    )
    assert b"TShapes 25\n" in result
    assert b"\nCo\n" in result


def test_neutral_brep_is_deterministic_open_cascade_serialization() -> None:
    model = triangle_brep()
    first = brep_model_brep(model)
    second = brep_model_brep(model)
    assert first == second
    assert first.startswith(b"DBRep_DrawableShape\n\nCASCADE Topology V1")
    assert b"Curve2ds 3\n" in first
    assert b"Curves 3\n" in first
    assert b"Surfaces 1\n" in first
    assert b"TShapes 9\n" in first
    assert b"\nFa\n0  9.9999999999999995e-08 1 0\n" in first
    assert first.endswith(b"\n+1 0 \n")


@pytest.mark.parametrize(
    "source",
    (
        ROOT / "examples" / ".SLDPRT" / "example.SLDPRT",
        ROOT / "examples" / "Random" / "Cover.SLDPRT",
    ),
)
def test_supplied_solidworks_analytic_brep_serializes_to_native_open_cascade(
    source: Path,
) -> None:
    document = open_document(source)
    assert document.brep is not None
    encoded = brep_model_brep(document.brep)
    assert is_structurally_valid_ascii_brep(encoded)
    assert f"Curve2ds {len(document.brep.coedges)}\n".encode("ascii") in encoded


@pytest.mark.parametrize(
    ("collection", "entity"),
    (
        (
            "curves",
            CircleCurve(
                "curve:circle",
                Vector3(0.0, 0.0, 0.0),
                Vector3(0.0, 0.0, 1.0),
                Vector3(1.0, 0.0, 0.0),
                1.0,
            ),
        ),
        (
            "curves",
            EllipseCurve(
                "curve:ellipse",
                Vector3(0.0, 0.0, 0.0),
                Vector3(0.0, 0.0, 1.0),
                Vector3(1.0, 0.0, 0.0),
                2.0,
                1.0,
            ),
        ),
        (
            "curves",
            NurbsCurve(
                "curve:nurbs",
                1,
                (Vector3(0.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0)),
                (0.0, 1.0),
                (2, 2),
            ),
        ),
        (
            "pcurves",
            LinePcurve("pcurve:line", Vector2(0.0, 0.0), Vector2(1.0, 0.0)),
        ),
        ("pcurves", CirclePcurve("pcurve:circle", Vector2(0.0, 0.0), 1.0)),
        (
            "pcurves",
            NurbsPcurve(
                "pcurve:nurbs",
                1,
                (Vector2(0.0, 0.0), Vector2(1.0, 0.0)),
                (0.0, 1.0),
                (2, 2),
            ),
        ),
        (
            "surfaces",
            CylinderSurface(
                "surface:cylinder",
                Vector3(0.0, 0.0, 0.0),
                Vector3(0.0, 0.0, 1.0),
                Vector3(1.0, 0.0, 0.0),
                1.0,
            ),
        ),
        (
            "surfaces",
            ConeSurface(
                "surface:cone",
                Vector3(0.0, 0.0, 0.0),
                Vector3(0.0, 0.0, 1.0),
                Vector3(1.0, 0.0, 0.0),
                1.0,
                0.5,
            ),
        ),
        (
            "surfaces",
            SphereSurface(
                "surface:sphere",
                Vector3(0.0, 0.0, 0.0),
                Vector3(0.0, 0.0, 1.0),
                Vector3(1.0, 0.0, 0.0),
                1.0,
            ),
        ),
        (
            "surfaces",
            TorusSurface(
                "surface:torus",
                Vector3(0.0, 0.0, 0.0),
                Vector3(0.0, 0.0, 1.0),
                Vector3(1.0, 0.0, 0.0),
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
                    (Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)),
                    (Vector3(1.0, 0.0, 0.0), Vector3(1.0, 1.0, 0.0)),
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
def test_open_cascade_geometry_families_are_structurally_serialized(
    collection: str, entity: object
) -> None:
    model = triangle_brep()
    narrowed = replace(
        model,
        **{collection: (*getattr(model, collection), entity)},
    )
    encoded = brep_model_brep(narrowed)
    assert is_structurally_valid_ascii_brep(encoded)


def _decoded_tetrahedron(prefix: str, x_offset: float = 0.0) -> BrepModel:
    vertices = (
        (x_offset, 0.0, 0.0),
        (x_offset + 2.0, 0.0, 0.0),
        (x_offset, 3.0, 0.0),
        (x_offset, 0.0, 4.0),
    )
    encoded = triangle_mesh_brep(
        vertices,
        ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
    )
    model = decode_ascii_brep(encoded, id_prefix=prefix)
    assert model is not None
    return model


def test_solid_topology_roundtrips_through_independent_decoder() -> None:
    model = _decoded_tetrahedron("encoder:solid")
    encoded = brep_model_brep(model)
    decoded = decode_ascii_brep(encoded, id_prefix="proof:solid")
    assert decoded is not None
    assert len(decoded.regions) == 1
    assert decoded.regions[0].solid
    assert decoded.shells[0].closed
    assert decoded.validate() == ()


def test_multiple_body_roots_roundtrip_as_distinct_solid_regions() -> None:
    first = _decoded_tetrahedron("encoder:first")
    second = _decoded_tetrahedron("encoder:second", 10.0)
    model = BrepModel(
        curves=(*first.curves, *second.curves),
        surfaces=(*first.surfaces, *second.surfaces),
        vertices=(*first.vertices, *second.vertices),
        edges=(*first.edges, *second.edges),
        coedges=(*first.coedges, *second.coedges),
        loops=(*first.loops, *second.loops),
        faces=(*first.faces, *second.faces),
        face_uses=(*first.face_uses, *second.face_uses),
        shells=(*first.shells, *second.shells),
        shell_uses=(*first.shell_uses, *second.shell_uses),
        regions=(*first.regions, *second.regions),
        bodies=(*first.bodies, *second.bodies),
    )
    assert model.validate() == ()
    encoded = brep_model_brep(model)
    assert b"\nCo\n" in encoded
    decoded = decode_ascii_brep(encoded, id_prefix="proof:multiple")
    assert decoded is not None
    assert len(decoded.regions) == 2
    assert all(region.solid for region in decoded.regions)
    assert decoded.validate() == ()


def test_free_wire_body_is_serialized_as_native_wire() -> None:
    model = triangle_brep()
    wire = BrepWire(
        "wire:free",
        tuple(coedge.id for coedge in model.coedges),
        closed=True,
    )
    narrowed = replace(
        model,
        loops=(),
        wires=(wire,),
        faces=(),
        face_uses=(),
        shells=(),
        shell_uses=(),
        regions=(),
        bodies=(
            replace(
                model.bodies[0],
                region_ids=(),
                design_body_id="",
                wire_ids=(wire.id,),
            ),
        ),
    )
    assert narrowed.validate() == ()
    encoded = brep_model_brep(narrowed)
    assert is_structurally_valid_ascii_brep(encoded)
    assert b"\nWi\n" in encoded


def test_neutral_brep_marks_unsupported_geometry_as_writer_unimplemented() -> None:
    model = triangle_brep()
    unsupported = replace(
        model,
        curves=(
            NativeCurve(model.curves[0].id, "catia", "cgm_curve"),
            *model.curves[1:],
        ),
    )
    with pytest.raises(
        FreeCADBrepWriteError, match="writer_unimplemented.*NativeCurve"
    ) as error:
        brep_model_brep(unsupported)
    assert error.value.reason == "writer_unimplemented"


def test_neutral_brep_rejects_unrepresentable_body_transform() -> None:
    model = triangle_brep()
    transformed = replace(
        model,
        bodies=(
            replace(
                model.bodies[0],
                transform=Transform(origin=Vector3(1.0, 0.0, 0.0)),
            ),
        ),
    )
    with pytest.raises(
        FreeCADBrepWriteError, match="writer_unimplemented.*identity body transforms"
    ):
        brep_model_brep(transformed)


def test_supported_neutral_brep_is_embedded_as_native_fcstd_shape() -> None:
    model = triangle_brep()
    model = replace(
        model,
        bodies=(replace(model.bodies[0], design_body_id=""),),
    )
    document = CadDocument(
        source=CadSource("json", "triangle.json", ""),
        configurations=(Configuration("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep=model,
        capabilities=frozenset({Capability.BREP}),
    )
    output = io.BytesIO()
    result = FreeCADAdapter().write(document, output)
    assert Capability.BREP in result.native_capabilities
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        shape_names = [
            name for name in archive.namelist() if name.endswith(".Shape.brp")
        ]
        assert shape_names == ["BRep.Shape.brp"]
        assert archive.read(shape_names[0]) == brep_model_brep(model)
        root = ET.fromstring(archive.read("Document.xml"))
    assert any(
        value.get("type") == "Part::Feature" and value.get("name") == "BRep"
        for value in root.findall("./Objects/Object")
    )


def test_public_sdk_accepts_supported_neutral_brep_as_near_lossless(
    tmp_path: Path,
) -> None:
    model = triangle_brep()
    model = replace(
        model,
        bodies=(replace(model.bodies[0], design_body_id=""),),
    )
    document = CadDocument(
        source=CadSource("json", "triangle.json", ""),
        configurations=(Configuration("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep=model,
        capabilities=frozenset({Capability.BREP}),
    )
    destination = tmp_path / "triangle.FCStd"
    result = write_document(document, destination)
    assert result.near_lossless is True
    assert Capability.BREP in result.native_capabilities
    assert open_document(destination).brep == model


def test_public_sdk_rejects_header_only_brep_and_preserves_explicit_carrier(
    tmp_path: Path,
) -> None:
    data = (
        b"DBRep_DrawableShape\n\nCASCADE Topology V1, (c) Open Cascade\n"
        b"not-a-brep\n"
    )
    document = _raw_brep_document(data)
    blocked = tmp_path / "blocked.FCStd"
    with pytest.raises(ApplicationUsabilityError) as captured:
        write_document(document, blocked, allow_carrier=False)
    assert (
        captured.value.carrier_reasons[Capability.BREP] is CarrierReason.SOURCE_OPAQUE
    )
    assert (
        captured.value.carrier_reasons[Capability.NATIVE_PAYLOADS]
        is CarrierReason.SOURCE_OPAQUE
    )
    assert not blocked.exists()
    explicit = tmp_path / "explicit.FCStd"
    result = write_document(document, explicit, allow_carrier=True)
    assert result.near_lossless is False
    restored = open_document(explicit)
    assert restored.brep_payloads[0].data == data


def test_public_sdk_accepts_strictly_decoded_raw_brep_payload(tmp_path: Path) -> None:
    data = brep_model_brep(triangle_brep())
    document = _raw_brep_document(data)
    destination = tmp_path / "valid.FCStd"
    result = write_document(document, destination)
    assert result.near_lossless is True
    assert {Capability.BREP, Capability.NATIVE_PAYLOADS} <= result.native_capabilities
    with zipfile.ZipFile(destination) as archive:
        shape_entries = [
            name for name in archive.namelist() if name.endswith(".Shape.brp")
        ]
        assert len(shape_entries) == 1
        assert archive.read(shape_entries[0]) == data


def test_unsupported_neutral_brep_remains_an_explicit_carrier() -> None:
    model = triangle_brep()
    model = replace(
        model,
        curves=(
            NativeCurve(model.curves[0].id, "catia", "cgm_curve"),
            *model.curves[1:],
        ),
        bodies=(replace(model.bodies[0], design_body_id=""),),
    )
    document = CadDocument(
        source=CadSource("catia", "triangle.CATPart", ""),
        configurations=(Configuration("default", "Default", active=True),),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        brep=model,
        capabilities=frozenset({Capability.BREP}),
    )
    output = io.BytesIO()
    result = FreeCADAdapter().write(document, output)
    assert Capability.BREP in result.carrier_capabilities
    assert Capability.BREP not in result.native_capabilities
    with zipfile.ZipFile(io.BytesIO(output.getvalue())) as archive:
        assert not any(name.endswith(".Shape.brp") for name in archive.namelist())


@pytest.mark.skipif(not ORACLE.is_file(), reason="KIT_FREECAD_ORACLE is unavailable")
def test_triangle_mesh_brep_loads_as_native_part_shape(tmp_path: Path) -> None:
    tetrahedron = tmp_path / "tetrahedron.brp"
    tetrahedron.write_bytes(
        triangle_mesh_brep(
            ((0, 0, 0), (2, 0, 0), (0, 3, 0), (0, 0, 4)),
            ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)),
        )
    )
    square = tmp_path / "square.brp"
    square.write_bytes(
        triangle_mesh_brep(
            ((0, 0, 0), (2, 0, 0), (2, 3, 0), (0, 3, 0)),
            ((0, 1, 2), (0, 2, 3)),
        )
    )
    code = (
        "import Part;"
        "t=Part.Shape();"
        f"t.read(r'{tetrahedron}');"
        "s=Part.Shape();"
        f"s.read(r'{square}');"
        "print('KIT_BREP',t.ShapeType,len(t.Solids),len(t.Faces),len(t.Edges),"
        "len(t.Vertexes),t.isValid(),t.Volume,t.BoundBox.XLength,"
        "t.BoundBox.YLength,t.BoundBox.ZLength,s.ShapeType,len(s.Faces),"
        "len(s.Edges),len(s.Vertexes),s.isValid())"
    )
    completed = subprocess.run(
        [str(ORACLE), "-c", code],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    line = next(
        value for value in completed.stdout.splitlines() if value.startswith("KIT_BREP")
    )
    values = line.split()[1:]
    assert values[:6] == ["Solid", "1", "4", "6", "4", "True"]
    assert tuple(float(value) for value in values[6:10]) == pytest.approx(
        (4.0, 2.0, 3.0, 4.0), abs=1e-12
    )
    assert values[10:] == ["Shell", "2", "5", "4", "True"]
