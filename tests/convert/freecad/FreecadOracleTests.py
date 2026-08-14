# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

from convert import convert

SAMPLE = Path(__file__).parents[3] / "examples" / ".SLDPRT" / "example.SLDPRT"
ORACLE = Path(os.environ.get("KIT_FREECAD_ORACLE", ""))


@pytest.mark.skipif(not ORACLE.is_file(), reason="KIT_FREECAD_ORACLE is unavailable")
def test_freecad_recomputes_exact_shape_and_parameter_edits(tmp_path) -> None:
    output = tmp_path / "example.FCStd"
    convert(SAMPLE, output)
    code = (
        "import FreeCAD as App;"
        f"d=App.open(r'{output}');"
        "[o.touch() for o in d.Objects];"
        "d.recompute();"
        "p=d.getObject('Parameters');"
        "s=d.getObject('Sketch1');"
        "f=d.getObject('Fillet1');"
        "before_volume=f.Shape.Volume;"
        "before_area=f.Shape.Area;"
        "before_width=s.Shape.BoundBox.XLength;"
        "before_bounds=(f.Shape.BoundBox.XMin,f.Shape.BoundBox.YMin,"
        "f.Shape.BoundBox.ZMin,f.Shape.BoundBox.XMax,"
        "f.Shape.BoundBox.YMax,f.Shape.BoundBox.ZMax);"
        "p.set(p.getCellFromAlias('sldprt_parameter_26_D1'),'250 mm');"
        "[o.touch() for o in d.Objects];"
        "d.recompute();"
        "print('KIT_RESULT',before_volume,before_area,before_width,*before_bounds,"
        "f.Shape.Volume,s.Shape.BoundBox.XLength,"
        "f.Shape.isValid(),len(f.Shape.Solids))"
    )
    completed = subprocess.run(
        [str(ORACLE), "-c", code],
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    line = next(
        value
        for value in completed.stdout.splitlines()
        if value.startswith("KIT_RESULT")
    )
    values = line.split()
    assert float(values[1]) == pytest.approx(881814.3482038012, abs=1e-8)
    assert float(values[2]) == pytest.approx(106818.8072010044, abs=1e-8)
    assert float(values[3]) == pytest.approx(248.6, abs=1e-10)
    assert tuple(float(value) for value in values[4:10]) == pytest.approx(
        (-124.3, -89.75, 0.0, 125.05, 89.75, 20.0), abs=1e-10
    )
    assert float(values[10]) != pytest.approx(float(values[1]))
    assert float(values[11]) == pytest.approx(250.0, abs=1e-10)
    assert values[12:14] == ["True", "1"]
