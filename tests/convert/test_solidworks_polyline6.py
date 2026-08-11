# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace
import hashlib
import math
from pathlib import Path

import pytest

from convert import write_document
from convert.adapters.freecad import read_freecad
from convert.adapters.solidworks import SldprtArchive
from convert.adapters.solidworks.container import SldprtFormatError
from convert.adapters.solidworks.format import (
    CONFIGURATION_STREAM,
    KEYWORDS_STREAM,
    RESOLVED_FEATURES_STREAM,
)
from convert.adapters.solidworks.native import (
    HasVendorPartEncoding,
    decode_native_model,
)
from convert.adapters.solidworks.resolved_polyline6_program import (
    EncodeProgram,
    KDepthOffset,
    KFieldOwners,
    KPointOffsets,
    KResolvedOps,
    PadFieldMap,
)


# the repository root keeps controlled corpus evidence outside production modules
KRepoRoot = Path(__file__).resolve().parents[2]

# the tracked six line oracle proves exact emission without runtime donor reads
KDonorStream = (
    KRepoRoot
    / "tests"
    / "fixtures"
    / "solidworks"
    / "donors"
    / "poly6_boss"
    / "resolved.bin"
)

# the pinned gate digest makes unreviewed field drift fail immediately
KGateDigest = "b973bd5326bbdb65b8e8b5e8345e0bdbdef20d345bf70d9f7562e5a74077bfb4"

# the donor polygon supplies an independent exact parameterization witness
KDonorPoints = (
    (0.0, 0.0),
    (40.0, 0.0),
    (40.0, 10.0),
    (15.0, 10.0),
    (15.0, 25.0),
    (0.0, 25.0),
)

# the controlled fcstd exercises public first principles dispatch and readback
KFreeCadPolyline = KRepoRoot / ".rescratch" / "gates" / "fcstd" / "gate_polyline6.FCStd"


# complete interval ownership prevents hidden vendor spans entering resolved output
def test_polyline6_program_closes_every_typed_field() -> None:
    PayloadData = EncodeProgram()
    assert len(PayloadData) == 12283
    assert hashlib.sha256(PayloadData).hexdigest() == KGateDigest
    assert len(KResolvedOps) == 3022
    assert len(KFieldOwners) == 516
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
    assert ObjectCount == 380
    assert DefineCount == 45


# an independent polygon proves semantic overrides reproduce native bytes exactly
def test_polyline6_program_reproduces_controlled_oracle() -> None:
    OracleData = KDonorStream.read_bytes()
    ProgramData = EncodeProgram(PadFieldMap(KDonorPoints, 8.0))
    assert ProgramData == OracleData


# fixed topology programs must refuse overrides that alter record width
def test_polyline6_program_rejects_variable_width_overrides() -> None:
    with pytest.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({32: "a deliberately incompatible comment width"})


# malformed source parameters must fail before any target bytes are emitted
def test_polyline6_parameter_validation_is_strict() -> None:
    with pytest.raises(SldprtFormatError, match="exactly six"):
        PadFieldMap(KDonorPoints[:5], 8.0)
    with pytest.raises(SldprtFormatError, match="finite"):
        PadFieldMap((*KDonorPoints[:5], (math.inf, 25.0)), 8.0)
    with pytest.raises(SldprtFormatError, match="unique"):
        PadFieldMap((*KDonorPoints[:5], KDonorPoints[0]), 8.0)
    with pytest.raises(SldprtFormatError, match="intersect"):
        PadFieldMap(
            ((0.0, 0.0), (2.0, 2.0), (0.0, 2.0), (2.0, 0.0), (3.0, 0.0), (3.0, 3.0)),
            8.0,
        )
    with pytest.raises(SldprtFormatError, match="positive"):
        PadFieldMap(KDonorPoints, 0.0)


# semantic field helpers keep geometry and extrusion parameters independently addressable
def test_polyline6_parameter_offsets_are_native_fields() -> None:
    FieldValues = PadFieldMap(KDonorPoints, 8.0)
    assert tuple(FieldValues) == (*KPointOffsets, KDepthOffset)
    assert tuple(FieldValues[OffsetPos] for OffsetPos in KPointOffsets) == (
        0.0,
        0.0,
        0.04,
        0.0,
        0.04,
        0.01,
        0.015,
        0.01,
        0.015,
        0.025,
        0.0,
        0.025,
    )
    assert FieldValues[KDepthOffset] == 0.008


# the public writer selects the live proven editable six line pad family
@pytest.mark.skipif(
    not KFreeCadPolyline.is_file(),
    reason="six line FreeCAD corpus unavailable",
)
def test_FreeCadPolylineSixWritesNativeParametricSolidWorksPart(
    tmp_path: Path,
) -> None:
    SourceData = read_freecad(KFreeCadPolyline)
    TargetPath = tmp_path / "FreeCadPolylineSix.SLDPRT"
    ResultData = write_document(SourceData, TargetPath, allow_carrier=True)
    ArchiveData = SldprtArchive.from_bytes(TargetPath.read_bytes())
    ResolvedData = ArchiveData.require(RESOLVED_FEATURES_STREAM)
    NativeData = decode_native_model(
        ArchiveData.require(KEYWORDS_STREAM),
        ResolvedData,
        ArchiveData.require(CONFIGURATION_STREAM),
        resolved_stream=RESOLVED_FEATURES_STREAM,
    )
    assert HasVendorPartEncoding(SourceData)
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.near_lossless is True
    assert len(ResolvedData) == 12283
    assert hashlib.sha256(ResolvedData).hexdigest() == KGateDigest
    assert tuple(
        (ItemData.kind, ItemData.coordinates)
        for ItemData in NativeData.sketches[0].profiles
    ) == (
        (
            "polyline",
            (
                -20.0,
                -20.0,
                20.0,
                -20.0,
                20.0,
                0.0,
                0.0,
                0.0,
                0.0,
                20.0,
                -20.0,
                20.0,
            ),
        ),
    )
    assert len(NativeData.operations) == 1
    assert NativeData.operations[0].object_id == 32
    assert NativeData.operations[0].profile_id == 26
    assert NativeData.operations[0].direction_code == 0
    assert NativeData.operations[0].termination_code == 0
    assert NativeData.operations[0].length_mm == pytest.approx(10.0)


# segment count changes remain outside the fixed six edge native grammar
@pytest.mark.skipif(
    not KFreeCadPolyline.is_file(),
    reason="six line FreeCAD corpus unavailable",
)
def test_FreeCadPolylineSixRejectsOtherSegmentCounts() -> None:
    SourceData = read_freecad(KFreeCadPolyline)
    SketchData = SourceData.sketches[0]
    ProfileData = SketchData.closed_profile_entity_ids[0]
    FiveLineData = replace(
        SourceData,
        sketches=(
            replace(
                SketchData,
                entities=SketchData.entities[:-1],
                closed_profile_entity_ids=(ProfileData[:-1],),
            ),
        ),
    )
    assert not HasVendorPartEncoding(FiveLineData)
