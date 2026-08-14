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

import pytest

from convert.adapters.solidworks.container.Archive import encode_string, read_string
from convert.adapters.solidworks.programs.configuration.circle.reverse.Program import ConfigOps, EncodeProgram as EncodeConfig, FieldOwners as ConfigOwners, ReferenceLength
from convert.adapters.solidworks.container.Container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.programs.resolved.circle.reverse.Program import EncodeProgram as EncodeResolved, FieldOwners as ResolvedOwners, ResolvedOps


# the repository root anchors optional oracle verification outside production paths
KRepoRoot = Path(__file__).resolve().parents[4]

# the controlled oracle independently proves canonical replay when locally available
KReverseOracle = KRepoRoot / ".rescratch" / "circle_autodim_r5_h10_reverse.SLDPRT"

# a pinned digest makes any unreviewed field drift immediately visible
KResolvedDigest = "b9735d3134c944dc8e66e64d62aa84c117edcf06a17e5d69601e552b9150655d"

# a second pinned digest protects the coupled configuration field program
KConfigDigest = "fc1cb072c15c9f334bab288234353e3dc27db5aa83abd61c6fdd95364ac276a8"


# saved source paths are document metadata and must not become production constants
def CanonResolved(OracleData: bytes) -> bytes:
    PathOffset = 9853
    _, PathWidth = read_string(OracleData, PathOffset)
    PartOffset = PathOffset + PathWidth + 2
    _, PartWidth = read_string(OracleData, PartOffset)
    return (
        OracleData[:PathOffset]
        + encode_string("")
        + OracleData[PathOffset + PathWidth : PartOffset]
        + encode_string("Part2")
        + OracleData[PartOffset + PartWidth :]
    )


# saved document names are canonicalized so configuration bytes stay reusable
def CanonConfig(OracleData: bytes) -> bytes:
    PartOffset = 44
    _, PartWidth = read_string(OracleData, PartOffset)
    return (
        OracleData[:PartOffset]
        + encode_string("Part1")
        + OracleData[PartOffset + PartWidth :]
    )


# complete interval ownership prevents hidden vendor spans entering resolved output
def test_reverse_resolved_program_closes_every_typed_field() -> None:
    PayloadData = EncodeResolved()
    assert len(PayloadData) == 12514
    assert hashlib.sha256(PayloadData).hexdigest() == KResolvedDigest
    assert len(ResolvedOps) == 2873
    assert len(ResolvedOwners) == 538
    CursorPos = 0
    ObjectCount = 0
    DefineCount = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in ResolvedOps:
        assert StartPos == CursorPos
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(ResolvedOwners)
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
    assert ObjectCount == 338
    assert DefineCount == 49
    assert b"C:\\Users" not in PayloadData
    assert "circle_autodim".encode("utf-16le") not in PayloadData


# coupled configuration ownership ensures reverse output contains no untyped gaps
def test_reverse_config_program_closes_every_typed_field() -> None:
    PayloadData = EncodeConfig()
    assert len(PayloadData) == ReferenceLength == 25158
    assert hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
    assert len(ConfigOps) == 4345
    assert len(ConfigOwners) == 1058
    CursorPos = 0
    ObjectCount = 0
    DefineCount = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in ConfigOps:
        assert StartPos == CursorPos
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(ConfigOwners)
        assert KindName in {
            "definition",
            "classref",
            "objectref",
            "null",
            "string",
            "stringlist",
        } or KindName.startswith(("primitive:", "direct:"))
        ObjectCount += KindName in {"definition", "classref", "objectref", "null"}
        DefineCount += KindName == "definition"
        CursorPos += FieldWidth
    assert CursorPos == len(PayloadData)
    assert ObjectCount == 129
    assert DefineCount == 40
    assert b"C:\\Users" not in PayloadData
    assert "circle_autodim".encode("utf-16le") not in PayloadData


# local oracle comparison proves canonicalization changes metadata strings alone
def test_reverse_programs_match_canonical_oracle() -> None:
    if not KReverseOracle.is_file():
        pytest.skip("controlled reverse circle oracle is unavailable")
    ArchiveData = SldprtArchive.open(KReverseOracle)
    OracleResolved = ArchiveData.require("Contents/Config-0-ResolvedFeatures")
    OracleConfig = ArchiveData.require("Contents/Config-0")
    assert len(OracleResolved) == 12700
    assert len(OracleConfig) == 25190
    assert EncodeResolved() == CanonResolved(OracleResolved)
    assert EncodeConfig() == CanonConfig(OracleConfig)


# fixed topology writers must reject any override that changes record width
def test_reverse_programs_reject_variable_width_overrides() -> None:
    with pytest.raises(SldprtFormatError, match="field width changed"):
        EncodeResolved({9853: "saved paths are intentionally unsupported"})
    with pytest.raises(SldprtFormatError, match="field width changed"):
        EncodeConfig({44: "saved document names are intentionally unsupported"})
