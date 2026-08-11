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
import struct

import pytest

from convert.adapters.solidworks.container import SldprtFormatError
from convert.adapters.solidworks.config0_revolve_pin90_program import (
    EncodeProgram as EncodeConfig,
)
from convert.adapters.solidworks.config0_revolve_pin90_program import (
    GetCoverage as GetConfigCoverage,
)
from convert.adapters.solidworks.config0_revolve_pin90_program import (
    KConfigOps,
    KFieldOwners as KConfigOwners,
    KReferenceDigest as KConfigDigest,
    KReferenceLength as KConfigLength,
)
from convert.adapters.solidworks.resolved_revolve_pin90_program import (
    EncodeProgram,
    GetCoverage,
    KAngleOffsets,
    KFieldOwners,
    KProfileOffsets,
    KReferenceDigest,
    KReferenceLength,
    KResolvedOps,
)


# the canonical profile values independently verify every editable sketch vertex
KProfileMetres = (
    (0.0, -0.05),
    (0.0, 0.0),
    (0.0025, 0.0),
    (0.0025, -0.03),
    (0.0015, -0.02999),
    (0.0015, -0.05),
)


# the topology specific configuration must remain wholly typed and byte exact
def test_pin90_config_program_has_exact_typed_coverage() -> None:
    PayloadData = EncodeConfig()
    CoverageData = GetConfigCoverage()
    assert len(PayloadData) == KConfigLength == 24902
    assert hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
    assert CoverageData == {
        "stream_bytes": 24902,
        "typed": 24902,
        "opaque": 0,
        "accounted": 24902,
        "operations": 4297,
        "owners": 1058,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# every configuration operation must tile its stream under a recovered serializer
def test_pin90_config_operations_tile_without_gaps() -> None:
    CursorValue = 0
    for StartPos, FieldWidth, OwnerIndex, _KindName, _DefaultValue in KConfigOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KConfigOwners)
        CursorValue += FieldWidth
    assert CursorValue == KConfigLength


# exact typed coverage prevents hidden vendor bytes entering partial revolution output
def test_pin90_program_has_exact_typed_coverage() -> None:
    PayloadData = EncodeProgram()
    CoverageData = GetCoverage()
    assert len(PayloadData) == KReferenceLength == 12537
    assert hashlib.sha256(PayloadData).hexdigest() == KReferenceDigest
    assert CoverageData == {
        "stream_bytes": 12537,
        "typed": 12537,
        "opaque": 0,
        "accounted": 12537,
        "operations": 3073,
        "owners": 506,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# every recovered operation must tile the stream under a known serializer owner
def test_pin90_program_operations_tile_without_gaps() -> None:
    CursorValue = 0
    AllowedKinds = {
        "definition",
        "classref",
        "objectref",
        "null",
        "string",
    }
    for StartPos, FieldWidth, OwnerIndex, KindName, _DefaultValue in KResolvedOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KFieldOwners)
        assert (
            KindName in AllowedKinds
            or KindName.startswith("primitive:")
            or KindName.startswith("direct:")
        )
        CursorValue += FieldWidth
    assert CursorValue == KReferenceLength


# the traced angle copies must preserve one editable ninety degree parameter
def test_pin90_program_carries_both_angle_values() -> None:
    PayloadData = EncodeProgram()
    AngleBytes = struct.pack("<d", math.pi / 2.0)
    assert KAngleOffsets == (11481, 12019)
    assert all(
        PayloadData[OffsetValue : OffsetValue + 8] == AngleBytes
        for OffsetValue in KAngleOffsets
    )


# recovered coordinate offsets must encode the FreeCAD stepped pin profile exactly
def test_pin90_program_carries_all_profile_vertices() -> None:
    PayloadData = EncodeProgram()
    assert (
        tuple(
            (
                struct.unpack_from("<d", PayloadData, XOffset)[0],
                struct.unpack_from("<d", PayloadData, YOffset)[0],
            )
            for XOffset, YOffset in KProfileOffsets
        )
        == KProfileMetres
    )


# fixed width enforcement prevents malformed archive fields from escaping validation
def test_pin90_program_rejects_variable_width_override() -> None:
    with pytest.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({11451: "D100"})


# numeric overrides remain typed while the recovered object framing stays immutable
def test_pin90_program_accepts_same_width_angle_override() -> None:
    AngleValue = math.radians(120.0)
    PayloadData = EncodeProgram(dict.fromkeys(KAngleOffsets, AngleValue))
    assert all(
        struct.unpack_from("<d", PayloadData, OffsetValue)[0] == AngleValue
        for OffsetValue in KAngleOffsets
    )
    assert len(PayloadData) == KReferenceLength
