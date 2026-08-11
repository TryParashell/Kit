# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import hashlib
from pathlib import Path
import struct

import pytest

from convert import write_document
from convert.adapters.freecad import read_freecad
from convert.adapters.solidworks.container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.format import (
    KIT_RESOLVED_STREAM,
    RESOLVED_FEATURES_STREAM,
)
from convert.adapters.solidworks.resolved import (
    BOSS_KIND,
    CUT_KIND,
    FeatureEdit,
    locate_features,
    patch_features,
    rectangle_corners_mm,
)
from convert.adapters.solidworks.resolved_bosscutcircle_program import (
    EncodeProgram,
    KFieldOwners,
    KResolvedOps,
)


# the repository root anchors controlled evidence outside production modules
KRepoRoot = Path(__file__).resolve().parents[2]

# the tracked oracle proves exact typed reconstruction without runtime reads
KOracleStream = (
    KRepoRoot
    / "tests"
    / "fixtures"
    / "solidworks"
    / "donors"
    / "boss_cut_cut_blind"
    / "resolved.bin"
)

# the strict source gate exercises public FreeCAD lowering without a carrier
KSourcePath = (
    KRepoRoot / ".rescratch" / "gates" / "fcstd" / "gate_boss_cut_circle.FCStd"
)

# the pinned digest makes unreviewed field drift fail immediately
KProgramDigest = "ea2e72fee693b357d6ccea3aac0f9a64a428f5b851aff0d77faf422491d939a6"


# public selection must preserve the typed family and its load critical directions
@pytest.mark.skipif(
    not KSourcePath.is_file(),
    reason="boss plus rectangular and circular blind-cut corpus unavailable",
)
def test_boss_cut_circle_public_writer_selects_typed_program(
    tmp_path: Path,
) -> None:
    SourceData = read_freecad(KSourcePath)
    TargetPath = tmp_path / "BossCutCirclePublic.SLDPRT"
    ResultData = write_document(SourceData, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    FeatureData = locate_features(ArchiveData.require(RESOLVED_FEATURES_STREAM))
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.near_lossless is True
    assert ResultData.metadata["runtime"] == "python-stdlib"
    assert KIT_RESOLVED_STREAM not in ArchiveData.streams
    assert tuple(ItemData.name for ItemData in FeatureData) == (
        "Boss-Extrude1",
        "Cut-Extrude1",
        "Cut-Extrude2",
    )
    assert tuple(ItemData.depth_mm for ItemData in FeatureData) == pytest.approx(
        (15.0, 5.0, 9.0)
    )
    assert tuple(ItemData.reversed for ItemData in FeatureData) == (True, False, False)
    assert FeatureData[0].bounds_mm == pytest.approx((-30.0, -20.0, 30.0, 20.0))
    assert FeatureData[1].bounds_mm == pytest.approx((-24.0, -4.0, 24.0, 4.0))
    assert FeatureData[2].arcs[0].centre_mm == pytest.approx((0.0, 12.0))
    assert FeatureData[2].arcs[0].radius_mm == pytest.approx(6.0)


# complete interval ownership prevents hidden vendor spans entering resolved output
def test_boss_cut_circle_program_closes_every_typed_field() -> None:
    PayloadData = EncodeProgram()
    assert len(PayloadData) == 21021
    assert hashlib.sha256(PayloadData).hexdigest() == KProgramDigest
    assert PayloadData == KOracleStream.read_bytes()
    assert len(KResolvedOps) == 5302
    assert len(KFieldOwners) == 520
    CursorPos = 0
    ObjectCount = 0
    DefineCount = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in KResolvedOps:
        assert StartPos == CursorPos
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KFieldOwners)
        assert KindName in {
            "definition",
            "classref",
            "objectref",
            "null",
            "string",
        } or KindName.startswith(("primitive:", "direct:"))
        ObjectCount += KindName in {"definition", "classref", "objectref", "null"}
        DefineCount += KindName == "definition"
        CursorPos += FieldWidth
    assert CursorPos == len(PayloadData)
    assert ObjectCount == 734
    assert DefineCount == 46


# native decoding must retain both rectangles and the full circular cut
def test_boss_cut_circle_program_exposes_complete_feature_tree() -> None:
    FeatureData = locate_features(EncodeProgram())
    assert tuple(ItemData.kind for ItemData in FeatureData) == (
        BOSS_KIND,
        CUT_KIND,
        CUT_KIND,
    )
    assert tuple(ItemData.feature_id for ItemData in FeatureData) == (32, 40, 47)
    assert tuple(ItemData.sketch_id for ItemData in FeatureData) == (26, 33, 41)
    assert tuple(ItemData.name for ItemData in FeatureData) == (
        "Boss-Extrude1",
        "Cut-Extrude1",
        "Cut-Extrude2",
    )
    assert tuple(len(ItemData.points) for ItemData in FeatureData) == (4, 4, 0)
    assert tuple(len(ItemData.arcs) for ItemData in FeatureData) == (0, 0, 1)
    assert tuple(ItemData.depth_mm for ItemData in FeatureData) == pytest.approx(
        (40.0, 15.0, 50.0)
    )
    CircleData = FeatureData[2].arcs[0]
    assert CircleData.centre_mm == pytest.approx((40.0, 15.0))
    assert CircleData.radius_mm == pytest.approx(25.0)
    assert CircleData.sweep_angle_degrees == pytest.approx(360.0)


# independent source geometry must drive every coupled native field coherently
def test_boss_cut_circle_program_accepts_semantic_feature_edits() -> None:
    PatchedData = patch_features(
        EncodeProgram(),
        {
            0: FeatureEdit(
                corners_mm=rectangle_corners_mm(-30.0, -20.0, 30.0, 20.0),
                depth_mm=15.0,
                reversed=True,
                end_condition_code=0,
                update_depth_copies=True,
            ),
            1: FeatureEdit(
                corners_mm=rectangle_corners_mm(-24.0, -4.0, 24.0, 4.0),
                depth_mm=5.0,
                reversed=False,
                end_condition_code=0,
                update_depth_copies=True,
            ),
            2: FeatureEdit(
                depth_mm=9.0,
                reversed=False,
                end_condition_code=0,
                update_depth_copies=True,
                radii_mm=(6.0,),
                arc_centres_mm=((0.0, 12.0),),
            ),
        },
    )
    FeatureData = locate_features(PatchedData)
    assert FeatureData[0].bounds_mm == pytest.approx((-30.0, -20.0, 30.0, 20.0))
    assert FeatureData[1].bounds_mm == pytest.approx((-24.0, -4.0, 24.0, 4.0))
    assert tuple(ItemData.depth_mm for ItemData in FeatureData) == pytest.approx(
        (15.0, 5.0, 9.0)
    )
    assert tuple(ItemData.reversed for ItemData in FeatureData) == (True, False, False)
    assert all(ItemData.end_condition_code == 0 for ItemData in FeatureData)
    CircleData = FeatureData[2].arcs[0]
    assert CircleData.centre_mm == pytest.approx((0.0, 12.0))
    assert CircleData.radius_mm == pytest.approx(6.0)
    for ItemData in FeatureData:
        CopyValues = tuple(
            struct.unpack_from("<d", PatchedData, OffsetPos)[0]
            for OffsetPos in ItemData.depth_copy_offsets
        )
        ExpectedDepth = ItemData.depth_mm / 1000.0
        assert CopyValues == pytest.approx(
            (
                ExpectedDepth,
                ExpectedDepth,
                -ExpectedDepth,
                -ExpectedDepth,
                ExpectedDepth,
                ExpectedDepth,
            )
        )


# fixed topology programs must reject overrides that change record width
def test_boss_cut_circle_program_rejects_variable_width_overrides() -> None:
    StringField = next(ItemData for ItemData in KResolvedOps if ItemData[3] == "string")
    with pytest.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({StringField[0]: "variable width metadata is unsupported"})


# source inspection ensures production carries typed vocabulary rather than payloads
def test_boss_cut_circle_program_contains_no_vendor_blocks() -> None:
    ProgramPath = (
        KRepoRoot
        / "src"
        / "convert"
        / "adapters"
        / "solidworks"
        / "resolved_bosscutcircle_program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()
    assert ".rescratch" not in SourceText
    assert "tests/fixtures" not in SourceText
