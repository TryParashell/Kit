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
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import (
    EncodeProgram as EncodeConfig,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import (
    GetCoverage as GetConfigCoverage,
)
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import (
    KAnnotationMatrixOffset,
    KConfigOps,
    KFieldOwners as KConfigOwners,
    KReferenceDigest as KConfigDigest,
    KReferenceLength as KConfigLength,
)
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.resolved.revolve.pin.front.Program import (
    EncodeProgram,
    GetCoverage,
    KAngleOffsets,
    KFieldOwners,
    KProfileOffsets,
    KReferenceDigest,
    KReferenceLength,
    KResolvedOps,
)
from convert.adapters.solidworks.envelopes.revolve.pin.front.Envelope import (
    BuildEnvelope,
    CalcPinFrontBounds,
    EncodeConfig as EncodeEnvelopeConfig,
    EncodeFeatures,
    EncodeHeader,
    KHeaderIdentity,
    KHeaderLogReference,
    KHeaderModelReference,
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
KHeaderDigest = "6f7bd56fa6997638046a3013475af74469a90e115ae28ee3e338431bfb14820b"

# centralizes shared evidence so every related assertion uses one value
KSourcePath = (
    FilePath(__file__).parents[4]
    / ".rescratch"
    / "sw"
    / "fcstd"
    / "kit_revolve_pin_front.FCStd"
)


# keeps this focused behavior isolated so regressions remain immediately visible
@PytestLib.mark.skipif(
    not KSourcePath.is_file(), reason="front plane pin revolution corpus unavailable"
)
def TestFPPWRFC(TmpPath: FilePath) -> None:
    SourceData = ReadFreecad(KSourcePath)
    with PytestLib.raises(ApplicationUsabilityError):
        WriteDocument(
            SourceData, TmpPath / "FrontPinPending.SLDPRT", allow_carrier=False
        )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPCPHETC() -> None:
    PayloadData = EncodeConfig()
    CoverageData = GetConfigCoverage()
    assert len(PayloadData) == KConfigLength == 24976
    assert Hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
    assert CoverageData == {
        "stream_bytes": 24976,
        "typed": 24976,
        "opaque": 0,
        "accounted": 24976,
        "operations": 4298,
        "owners": 1058,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPCOTWG() -> None:
    CursorValue = 0
    for StartPos, FieldWidth, OwnerIndex, _, _ in KConfigOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KConfigOwners)
        CursorValue += FieldWidth
    assert CursorValue == KConfigLength


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPCCAM() -> None:
    PayloadData = EncodeConfig()
    assert StructLib.unpack_from("<9d", PayloadData, KAnnotationMatrixOffset) == (
        1.0,
        0.0,
        0.0,
        -0.0,
        -0.0,
        -1.0,
        0.0,
        1.0,
        0.0,
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPMHIBE() -> None:
    HeaderData = EncodeHeader()
    assert len(HeaderData) == 2305
    assert Hashlib.sha256(HeaderData).hexdigest() == KHeaderDigest
    assert KHeaderIdentity == (1785928014, 106, 103, 1785928015)
    assert KHeaderStamps == ((1785928015, 1785928015), (1785928015,))
    assert KHeaderUser == "odin"
    assert (KHeaderLogReference, KHeaderModelReference) == ("Part1", "Part2")


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPMHBFP() -> None:
    HeaderBounds = CalcPinFrontBounds()
    assert HeaderBounds[:3] == (0.0, -0.025, 0.0)
    assert HeaderBounds[3:6] == (0.0025, 0.0, 0.0025)
    assert HeaderBounds[6:9] == (-0.0025, -0.05, -0.0025)
    assert HeaderBounds[9] == 0.025248762345905194


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPECECS() -> None:
    EnvelopeData = BuildEnvelope()
    assert EnvelopeData.Config0Payload == EncodeEnvelopeConfig() == EncodeConfig()
    assert EnvelopeData.HeaderPayload == EncodeHeader()
    assert EnvelopeData.HeaderStamps == KHeaderStamps
    assert EnvelopeData.HeaderBounds == CalcPinFrontBounds()
    assert EnvelopeData.HeaderCreation == KHeaderIdentity[0]
    assert EncodeFeatures() == EncodeProgram()


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPPHETC() -> None:
    PayloadData = EncodeProgram()
    CoverageData = GetCoverage()
    assert len(PayloadData) == KReferenceLength == 12265
    assert Hashlib.sha256(PayloadData).hexdigest() == KReferenceDigest
    assert CoverageData == {
        "stream_bytes": 12265,
        "typed": 12265,
        "opaque": 0,
        "accounted": 12265,
        "operations": 3005,
        "owners": 503,
    }
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPPOTWG() -> None:
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
def TestFPPCAAV() -> None:
    PayloadData = EncodeProgram()
    AngleBytes = StructLib.pack("<d", MathInfo.tau)
    assert KAngleOffsets == (11209, 11723, 11747)
    assert all(
        (
            PayloadData[OffsetValue : OffsetValue + 8] == AngleBytes
            for OffsetValue in KAngleOffsets
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPPCAPV() -> None:
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
def TestFPPRVWO() -> None:
    with PytestLib.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({11179: "D100"})


# keeps this focused behavior isolated so regressions remain immediately visible
def TestFPPASWAO() -> None:
    AngleValue = MathInfo.radians(270.0)
    PayloadData = EncodeProgram(dict.fromkeys(KAngleOffsets, AngleValue))
    assert all(
        (
            StructLib.unpack_from("<d", PayloadData, OffsetValue)[0] == AngleValue
            for OffsetValue in KAngleOffsets
        )
    )
    assert len(PayloadData) == KReferenceLength
