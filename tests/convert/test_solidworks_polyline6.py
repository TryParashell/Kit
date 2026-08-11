# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pytest

from convert.adapters.solidworks.container import SldprtFormatError
from convert.adapters.solidworks.resolved_polyline6_program import (
    EncodeProgram,
    KFieldOwners,
    KResolvedOps,
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

# six unique vertices drive the closed line chain without duplicated endpoints
KPointOffsets = (
    6119,
    6127,
    6297,
    6305,
    6924,
    6932,
    7086,
    7094,
    7248,
    7256,
    7410,
    7418,
)

# the extrusion parameter remains independent from sketch geometry
KDepthOffset = 11090

# the donor polygon supplies an independent exact parameterization witness
KDonorPoints = (
    (0.0, 0.0),
    (40.0, 0.0),
    (40.0, 10.0),
    (15.0, 10.0),
    (15.0, 25.0),
    (0.0, 25.0),
)


# callers need one validated mapping from source millimetres into native metres
def PolyOverrides(
    PointsMm: tuple[tuple[float, float], ...], DepthMm: float
) -> dict[int, float]:
    if len(PointsMm) != 6:
        raise ValueError("polyline program requires exactly six vertices")
    PointValues = tuple(Coordinate for PointPair in PointsMm for Coordinate in PointPair)
    if not all(math.isfinite(ValueItem) for ValueItem in PointValues):
        raise ValueError("polyline vertices must be finite")
    if not math.isfinite(DepthMm) or DepthMm <= 0.0:
        raise ValueError("polyline depth must be finite and positive")
    FieldValues = {
        OffsetPos: ValueMeters / 1000.0
        for OffsetPos, ValueMeters in zip(KPointOffsets, PointValues, strict=True)
    }
    FieldValues[KDepthOffset] = DepthMm / 1000.0
    return FieldValues


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
    ProgramData = EncodeProgram(PolyOverrides(KDonorPoints, 8.0))
    assert ProgramData == OracleData


# fixed topology programs must refuse overrides that alter record width
def test_polyline6_program_rejects_variable_width_overrides() -> None:
    with pytest.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({32: "a deliberately incompatible comment width"})


# malformed source parameters must fail before any target bytes are emitted
def test_polyline6_parameter_validation_is_strict() -> None:
    with pytest.raises(ValueError, match="exactly six"):
        PolyOverrides(KDonorPoints[:5], 8.0)
    with pytest.raises(ValueError, match="finite"):
        PolyOverrides((*KDonorPoints[:5], (math.inf, 25.0)), 8.0)
    with pytest.raises(ValueError, match="positive"):
        PolyOverrides(KDonorPoints, 0.0)
