from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from convert.adapters.freecad.brep import triangle_mesh_brep


ORACLE = Path(os.environ.get("KIT_FREECAD_ORACLE", ""))


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
