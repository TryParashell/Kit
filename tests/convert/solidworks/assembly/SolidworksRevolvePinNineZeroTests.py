# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
import hashlib as Hashlib
import math as MathInfo
from pathlib import Path as FilePath
import struct as StructLib
import pytest as PytestLib
from convert import write_document as WriteDocument
from convert.adapters.freecad import read_freecad as ReadFreecad
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.rightangle.Program import (
    EncodeProgram as EncodeConfig,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.rightangle.Program import (
    GetCoverage as GetConfigCoverage,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.rightangle.Program import (
    KConfigOps,
    KFieldOwners as KConfigOwners,
    KReferenceDigest as KConfigDigest,
    KReferenceLength as KConfigLength,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.rightangle.Program import (
    EncodeProgram,
    GetCoverage,
    KAngleOffsets,
    KFieldOwners,
    KProfileOffsets,
    KReferenceDigest,
    KReferenceLength,
    KResolvedOps,
)
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as Stream,
    KIT_RESOLVED_STREAM as StreamA,
    RESOLVED_FEATURES_STREAM as StreamB,
)
from convert.adapters.solidworks.envelopes.revolve.pin.rightangle.Envelope import (
    BuildEnvelope,
    CalcPin90Bounds as CalcPinNineZeroBounds,
    EncodeConfig as EncodeEnvelopeConfig,
    EncodeFeatures,
    EncodeHeader,
    KHeaderIdentity,
    KHeaderStamps,
    KHeaderUser,
)

# centralizes shared evidence so every related assertion uses one value
KProfileMetres = (
    (0.0, -0.05),
    (0.0, 0.0),
    (0.0025, 0.0),
    (0.0025, -0.03),
    (0.0015, -0.02999),
    (0.0015, -0.05),
)

# centralizes shared evidence so every related assertion uses one value
KHeaderDigest = "9d146ad95cacd429338ca34ba74acb4b725ae8bce2c4d3018e99e3fcd4873880"

# centralizes shared evidence so every related assertion uses one value
KSourcePath = (
    FilePath(__file__).parents[4]
    / ".rescratch"
    / "sw"
    / "fcstd"
    / "kit_revolve_pin_top_90.FCStd"
)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KSourcePath.is_file(),
    reason="top plane partial pin revolution corpus unavailable",
)
def TestPNZPWSCE(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KSourcePath)
    TargetPath = TmpPath / "Pin90Public.SLDPRT"
    ResultData = WriteDocument(SourceData, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    EnvelopeData = BuildEnvelope()
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.near_lossless is True
    assert ResultData.metadata["runtime"] == "python-stdlib"
    assert StreamA not in ArchiveData.streams
    assert ArchiveData.require(StreamB) == EncodeFeatures()
    assert ArchiveData.require(Stream) == EnvelopeData.Config0Payload
    assert (
        ArchiveData.require("Contents/Config-0-ModelHeader")
        == EnvelopeData.HeaderPayload
    )
    assert ArchiveData.require("Header2") == EnvelopeData.HeaderPayload


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZCPHETC() -> None:
    PayloadData = EncodeConfig()
    CoverageData = GetConfigCoverage()
    assert len(PayloadData) == KConfigLength == 24902
    assert Hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
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


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZCOTWG() -> None:
    CursorValue = 0
    for StartPos, FieldWidth, OwnerIndex, KindNameA, DefaultValue in KConfigOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KConfigOwners)
        CursorValue += FieldWidth
    assert CursorValue == KConfigLength


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZMHIBE() -> None:
    HeaderData = EncodeHeader()
    assert len(HeaderData) == 2305
    assert Hashlib.sha256(HeaderData).hexdigest() == KHeaderDigest
    assert KHeaderIdentity == (1786479979, 106, 103, 1786479985)
    assert KHeaderStamps == ((1786479985, 1786479985), (1786479985,))
    assert KHeaderUser == "odin"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZMHBFP() -> None:
    HeaderBounds = CalcPinNineZeroBounds()
    assert HeaderBounds[:3] == (0.00125, 0.00125, 0.025)
    assert HeaderBounds[3:6] == (0.0025, 0.0025, 0.05)
    assert HeaderBounds[6:9] == (0.0, 0.0, 0.0)
    assert MathInfo.isclose(
        HeaderBounds[9], 0.025062422069704278, rel_tol=0.0, abs_tol=1e-18
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZECECS() -> None:
    EnvelopeData = BuildEnvelope()
    assert EnvelopeData.Config0Payload == EncodeEnvelopeConfig() == EncodeConfig()
    assert EnvelopeData.HeaderPayload == EncodeHeader()
    assert EnvelopeData.HeaderStamps == KHeaderStamps
    assert EnvelopeData.HeaderBounds == CalcPinNineZeroBounds()
    assert EnvelopeData.HeaderCreation == KHeaderIdentity[0]
    assert EncodeFeatures() == EncodeProgram()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZPHETC() -> None:
    PayloadData = EncodeProgram()
    CoverageData = GetCoverage()
    assert len(PayloadData) == KReferenceLength == 12537
    assert Hashlib.sha256(PayloadData).hexdigest() == KReferenceDigest
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


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZPOTWG() -> None:
    CursorValue = 0
    AllowedKinds = {"definition", "classref", "objectref", "null", "string"}
    for StartPos, FieldWidth, OwnerIndex, KindName, DefaultValue in KResolvedOps:
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


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZPCBAV() -> None:
    PayloadData = EncodeProgram()
    AngleBytes = StructLib.pack("<d", MathInfo.pi / 2.0)
    assert KAngleOffsets == (11481, 12019)
    assert all(
        (
            PayloadData[OffsetValue : OffsetValue + 8] == AngleBytes
            for OffsetValue in KAngleOffsets
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZPCAPV() -> None:
    PayloadData = EncodeProgram()
    assert (
        tuple(
            (
                (
                    StructLib.unpack_from("<d", PayloadData, XOffset)[0],
                    StructLib.unpack_from("<d", PayloadData, YOffset)[0],
                )
                for XOffset, YOffset in KProfileOffsets
            )
        )
        == KProfileMetres
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZPRVWO() -> None:
    with PytestLib.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({11451: "D100"})


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPNZPASWAO() -> None:
    AngleValue = MathInfo.radians(120.0)
    PayloadData = EncodeProgram(dict.fromkeys(KAngleOffsets, AngleValue))
    assert all(
        (
            StructLib.unpack_from("<d", PayloadData, OffsetValue)[0] == AngleValue
            for OffsetValue in KAngleOffsets
        )
    )
    assert len(PayloadData) == KReferenceLength
