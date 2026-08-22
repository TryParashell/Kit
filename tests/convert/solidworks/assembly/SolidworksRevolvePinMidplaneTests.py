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
from convert import ApplicationUsabilityError, write_document as WriteDocument
from convert.adapters.freecad import read_freecad as ReadFreecad
from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Program import (
    EncodeProgram as EncodeConfig,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Program import (
    GetCoverage as GetConfigCoverage,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Program import (
    KReferenceDigest as KConfigDigest,
    KReferenceLength as KConfigLength,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.midplane.Registry import (
    KConfigOps,
    KFieldOwners as KConfigOwners,
)
from convert.adapters.solidworks.container.Container import (
    SldprtArchive,
    SldprtFormatError,
)
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM as Stream,
    RESOLVED_FEATURES_STREAM as StreamA,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.midplane.Program import (
    EncodeProgram,
    GetCoverage,
    KFirstAngleOffsets,
    KProfileOffsets,
    KReferenceDigest,
    KReferenceLength,
    KSecondAngleOffsets,
    KSingleEndOffset,
)
from convert.adapters.solidworks.programs.resolved.revolve.pin.midplane.Registry import (
    KFieldOwners,
    KResolvedOps,
)
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import (
    CalcPinBounds,
)
from convert.adapters.solidworks.envelopes.revolve.pin.midplane.Envelope import (
    BuildEnvelope,
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
KHeaderDigest = "4cb455532120074010565342eab6df3b83df1bf45ad0c25bf391664790de07ca"

# centralizes shared evidence so every related assertion uses one value
KSourcePath = (
    FilePath(__file__).parents[4]
    / ".rescratch"
    / "sw"
    / "fcstd"
    / "kit_revolve_pin_top_midplane.FCStd"
)

# centralizes shared evidence so every related assertion uses one value
KOraclePath = (
    FilePath(__file__).parents[4]
    / ".rescratch"
    / "revolve_pin_midplane"
    / "revolve_pin_top_midplane.oracle.SLDPRT"
)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KSourcePath.is_file(),
    reason="top plane symmetric pin revolution corpus unavailable",
)
def TestMPPWRFC(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KSourcePath)
    with PytestLib.raises(ApplicationUsabilityError):
        WriteDocument(
            SourceData, TmpPath / "MidplanePinPending.SLDPRT", allow_carrier=False
        )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPCPHETC() -> None:
    PayloadData = EncodeConfig()
    assert len(PayloadData) == KConfigLength == 24902
    assert Hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
    assert GetConfigCoverage() == {
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
def TestMPCOTWG() -> None:
    CursorValue = 0
    for StartPos, FieldWidth, OwnerIndex, _, _ in KConfigOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KConfigOwners)
        CursorValue += FieldWidth
    assert CursorValue == KConfigLength


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPMHIBE() -> None:
    HeaderData = EncodeHeader()
    assert len(HeaderData) == 2305
    assert Hashlib.sha256(HeaderData).hexdigest() == KHeaderDigest
    assert KHeaderIdentity == (1786487434, 106, 103, 1786487442)
    assert KHeaderStamps == ((1786487441, 1786487442), (1786487442,))
    assert KHeaderUser == "odin"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPMHBFP() -> None:
    HeaderBounds = CalcPinBounds()
    assert HeaderBounds[:3] == (0.0, 0.0, 0.025)
    assert HeaderBounds[3:6] == (0.0025, 0.0025, 0.05)
    assert HeaderBounds[6:9] == (-0.0025, -0.0025, 0.0)
    assert HeaderBounds[9] == PytestLib.approx(0.025248762345905194, abs=1e-17)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPECECS() -> None:
    EnvelopeData = BuildEnvelope()
    assert EnvelopeData.Config0Payload == EncodeEnvelopeConfig() == EncodeConfig()
    assert EnvelopeData.HeaderPayload == EncodeHeader()
    assert EnvelopeData.HeaderStamps == KHeaderStamps
    assert EnvelopeData.HeaderBounds == CalcPinBounds()
    assert EnvelopeData.HeaderCreation == KHeaderIdentity[0]
    assert EncodeFeatures() == EncodeProgram()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPPHETC() -> None:
    PayloadData = EncodeProgram()
    assert len(PayloadData) == KReferenceLength == 14065
    assert Hashlib.sha256(PayloadData).hexdigest() == KReferenceDigest
    assert GetCoverage() == {
        "stream_bytes": 14065,
        "typed": 14065,
        "opaque": 0,
        "accounted": 14065,
        "operations": 3374,
        "owners": 506,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPPOTWG() -> None:
    CursorValue = 0
    AllowedKinds = {"definition", "classref", "objectref", "null", "string"}
    for StartPos, FieldWidth, OwnerIndex, KindName, _ in KResolvedOps:
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
def TestMPPCBEV() -> None:
    PayloadData = EncodeProgram()
    assert KSingleEndOffset == 10437
    assert StructLib.unpack_from("<I", PayloadData, KSingleEndOffset)[0] == 0
    assert KFirstAngleOffsets == (11281, 11795, 11819)
    assert KSecondAngleOffsets == (13033, 13547, 13571)
    assert all(
        (
            StructLib.unpack_from("<d", PayloadData, OffsetValue)[0] == MathInfo.tau
            for OffsetValue in KFirstAngleOffsets
        )
    )
    assert all(
        (
            StructLib.unpack_from("<d", PayloadData, OffsetValue)[0] == 0.0
            for OffsetValue in KSecondAngleOffsets
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPPCAPV() -> None:
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
def TestMPPRVWO() -> None:
    with PytestLib.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({11251: "D100"})


# keeps this focused behavior isolated so regressions remain immediately visible
def TestMPPAIFAO() -> None:
    AngleValue = MathInfo.pi
    PayloadData = EncodeProgram(dict.fromkeys(KFirstAngleOffsets, AngleValue))
    assert all(
        (
            StructLib.unpack_from("<d", PayloadData, OffsetValue)[0] == AngleValue
            for OffsetValue in KFirstAngleOffsets
        )
    )
    assert all(
        (
            StructLib.unpack_from("<d", PayloadData, OffsetValue)[0] == 0.0
            for OffsetValue in KSecondAngleOffsets
        )
    )
    assert len(PayloadData) == KReferenceLength


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(not KOraclePath.is_file(), reason="midplane oracle unavailable")
def TestMPPMLO() -> None:
    ArchiveData = SldprtArchive.open(KOraclePath)
    assert ArchiveData.require(Stream) == EncodeConfig()
    assert ArchiveData.require(StreamA) == EncodeProgram()
    assert ArchiveData.require("Contents/Config-0-ModelHeader") == EncodeHeader()
    assert ArchiveData.require("Header2") == EncodeHeader()
