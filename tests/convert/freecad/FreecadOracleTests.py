# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
import os as OsModule
from pathlib import Path as FilePath
import subprocess as Subprocess
import pytest as Pytest
from convert import convert as Convert

# this binding exists because shared behavior needs one stable value
KSample = FilePath(__file__).parents[3] / 'examples' / '.SLDPRT' / 'example.SLDPRT'

# this binding exists because shared behavior needs one stable value
KOracle = FilePath(OsModule.environ.get('KIT_FREECAD_ORACLE', ''))

# this definition exists because focused behavior needs one stable owner
@Pytest.mark.skipif(not KOracle.is_file(), reason='KIT_FREECAD_ORACLE is unavailable')
def TestRecomputes(TmpPath) -> None:
    Output = TmpPath / 'example.FCStd'
    Convert(KSample, Output)
    CodeValue = f"import FreeCAD as App;d=App.open(r'{Output}');[o.touch() for o in d.Objects];d.recompute();p=d.getObject('Parameters');s=d.getObject('Sketch1');f=d.getObject('Fillet1');before_volume=f.Shape.Volume;before_area=f.Shape.Area;before_width=s.Shape.BoundBox.XLength;before_bounds=(f.Shape.BoundBox.XMin,f.Shape.BoundBox.YMin,f.Shape.BoundBox.ZMin,f.Shape.BoundBox.XMax,f.Shape.BoundBox.YMax,f.Shape.BoundBox.ZMax);p.set(p.getCellFromAlias('sldprt_parameter_26_D1'),'250 mm');[o.touch() for o in d.Objects];d.recompute();print('KIT_RESULT',before_volume,before_area,before_width,*before_bounds,f.Shape.Volume,s.Shape.BoundBox.XLength,f.Shape.isValid(),len(f.Shape.Solids))"
    Completed = Subprocess.run([str(KOracle), '-c', CodeValue], check=True, capture_output=True, text=True, timeout=120)
    LineValue = next((Value for Value in Completed.stdout.splitlines() if Value.startswith('KIT_RESULT')))
    Values = LineValue.split()
    assert float(Values[1]) == Pytest.approx(881814.3482038012, abs=1e-08)
    assert float(Values[2]) == Pytest.approx(106818.8072010044, abs=1e-08)
    assert float(Values[3]) == Pytest.approx(248.6, abs=1e-10)
    assert tuple((float(Value) for Value in Values[4:10])) == Pytest.approx((-124.3, -89.75, 0.0, 125.05, 89.75, 20.0), abs=1e-10)
    assert float(Values[10]) != Pytest.approx(float(Values[1]))
    assert float(Values[11]) == Pytest.approx(250.0, abs=1e-10)
    assert Values[12:14] == ['True', '1']

# this binding exists because shared behavior needs one stable value
globals()['ORACLE'] = KOracle

# this binding exists because shared behavior needs one stable value
globals()['Path'] = FilePath

# this binding exists because shared behavior needs one stable value
globals()['SAMPLE'] = KSample

# this binding exists because shared behavior needs one stable value
globals()['annotations'] = Annotations

# this binding exists because shared behavior needs one stable value
globals()['convert'] = Convert

# this binding exists because shared behavior needs one stable value
globals()['os'] = OsModule

# this binding exists because shared behavior needs one stable value
globals()['pytest'] = Pytest

# this binding exists because shared behavior needs one stable value
globals()['subprocess'] = Subprocess
