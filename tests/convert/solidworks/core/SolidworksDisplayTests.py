# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from pathlib import Path as FilePath
import pytest as PytestLib
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.core.Display import (
    decode_display_lists as DecodeDisplayLists,
    decode_tessellation_faces as DecodeTessellationFaces,
    is_component_path as IsComponentPath,
    neutral_meshes as NeutralMeshes,
)

# centralizes shared evidence so every related assertion uses one value
KAssembly = FilePath(__file__).parents[4] / "examples" / "Random" / "V8_engine.SLDASM"


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    "ItemValue",
    (
        "Rotor@Assembly",
        "Custom instance name@Root/Nested occurrence@Subassembly",
        "Part-1@Assembly",
    ),
)
def TestCPDNRGNS(ItemValue: str) -> None:
    assert IsComponentPath(ItemValue)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.parametrize(
    "ItemValue",
    (
        "Top Plane@Rotor@Assembly",
        "Belt1-1^Assembly-1@Assembly",
        "C:/Parts/Rotor.SLDPRT",
        "@Assembly",
    ),
)
def TestCPDRERAF(ItemValue: str) -> None:
    assert not IsComponentPath(ItemValue)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDLREFAGG() -> None:
    DataValue = SldprtArchive.open(KAssembly).require("Contents/DisplayLists")
    Faces = DecodeTessellationFaces(DataValue)
    Components = DecodeDisplayLists(DataValue)
    assert len(Faces) == 4391
    assert sum((len(FaceInfo.positions_mm) for FaceInfo in Faces)) == 492148
    assert sum((len(FaceInfo.triangle_indices) for FaceInfo in Faces)) == 391218
    assert len(Components) == 65
    assert sum((len(Component.faces) for Component in Components)) == 4391


# keeps this focused behavior isolated so regressions remain immediately visible
def TestDGISTMAMTS() -> None:
    DataValue = SldprtArchive.open(KAssembly).require("Contents/DisplayLists")
    Component = DecodeDisplayLists(DataValue)[0]
    FaceInfo = Component.faces[0]
    assert Component.occurrence_path == "Journal_bearig_crank-1@V8_engine"
    assert Component.source_path.endswith("Journal_bearig_crank.SLDPRT")
    assert FaceInfo.face_id == 33
    assert FaceInfo.positions_mm[0] == PytestLib.approx(
        (-13.599040918052197, 7.011139299720526, -0.9284935076721013)
    )
    assert FaceInfo.normals[0] == PytestLib.approx(
        (0.8888262510299683, -0.4582444131374359, 0.0)
    )
    assert max(
        (Index for Triangle in FaceInfo.triangle_indices for Index in Triangle)
    ) < len(FaceInfo.positions_mm)
    MeshInfo = NeutralMeshes((Component,))[0]
    assert MeshInfo.vertices[0].x == PytestLib.approx(-13.599040918052197)
    assert MeshInfo.attributes["occurrence_path"] == Component.occurrence_path
    assert MeshInfo.provenance is not None
    assert MeshInfo.provenance.spans[0].stream == "Contents/DisplayLists"
