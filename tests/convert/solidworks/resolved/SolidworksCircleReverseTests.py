# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import hashlib as Hashlib
from pathlib import Path as FilePath
import pytest as PytestLib
from convert.adapters.solidworks.container.Archive import (
    encode_string as EncodeString,
    read_string as ReadString,
)
from convert.adapters.solidworks.programs.configuration.circle.reverse.Program import (
    EncodeProgram as EncodeConfig,
    ReferenceLength,
)
from convert.adapters.solidworks.programs.configuration.circle.reverse.Registry import (
    ConfigOps,
    FieldOwners as ConfigOwners,
)
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.programs.resolved.circle.reverse.Program import (
    EncodeProgram as EncodeResolved,
)
from convert.adapters.solidworks.programs.resolved.circle.reverse.Registry import (
    FieldOwners as ResolvedOwners,
    ResolvedOps,
)

# centralizes shared evidence so every related assertion uses one value
KRepoRoot = FilePath(__file__).resolve().parents[4]

# centralizes shared evidence so every related assertion uses one value
KReverseOracle = KRepoRoot / ".rescratch" / "circle_autodim_r5_h10_reverse.SLDPRT"

# centralizes shared evidence so every related assertion uses one value
KResolvedDigest = "b9735d3134c944dc8e66e64d62aa84c117edcf06a17e5d69601e552b9150655d"

# centralizes shared evidence so every related assertion uses one value
KConfigDigest = "fc1cb072c15c9f334bab288234353e3dc27db5aa83abd61c6fdd95364ac276a8"


# keeps this focused behavior isolated so regressions remain immediately visible
def CanonResolved(OracleData: bytes) -> bytes:
    PathOffset = 9853
    _, PathWidth = ReadString(OracleData, PathOffset)
    PartOffset = PathOffset + PathWidth + 2
    _, PartWidth = ReadString(OracleData, PartOffset)
    return (
        OracleData[:PathOffset]
        + EncodeString("")
        + OracleData[PathOffset + PathWidth : PartOffset]
        + EncodeString("Part2")
        + OracleData[PartOffset + PartWidth :]
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def CanonConfig(OracleData: bytes) -> bytes:
    PartOffset = 44
    _, PartWidth = ReadString(OracleData, PartOffset)
    return (
        OracleData[:PartOffset]
        + EncodeString("Part1")
        + OracleData[PartOffset + PartWidth :]
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRRPCETF() -> None:
    PayloadData = EncodeResolved()
    assert len(PayloadData) == 12514
    assert Hashlib.sha256(PayloadData).hexdigest() == KResolvedDigest
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


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRCPCETF() -> None:
    PayloadData = EncodeConfig()
    assert len(PayloadData) == ReferenceLength == 25158
    assert Hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
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


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRPMCO() -> None:
    if not KReverseOracle.is_file():
        PytestLib.skip("controlled reverse circle oracle is unavailable")
    ArchiveData = SldprtArchive.open(KReverseOracle)
    OracleResolved = ArchiveData.require("Contents/Config-0-ResolvedFeatures")
    OracleConfig = ArchiveData.require("Contents/Config-0")
    assert len(OracleResolved) == 12700
    assert len(OracleConfig) == 25190
    assert EncodeResolved() == CanonResolved(OracleResolved)
    assert EncodeConfig() == CanonConfig(OracleConfig)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRPRVWO() -> None:
    with PytestLib.raises(SldprtFormatError, match="field width changed"):
        EncodeResolved({9853: "saved paths are intentionally unsupported"})
    with PytestLib.raises(SldprtFormatError, match="field width changed"):
        EncodeConfig({44: "saved document names are intentionally unsupported"})
