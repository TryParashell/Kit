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
import pytest as PytestLib
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.core.Native import (
    _HEADER_OBJECTS as Objects,
    _NativeIdentity as NativeIdentity,
    _SOLIDWORKS_CONFIGURATION_FLAGS as Flags,
    _header_payload as HeaderPayload,
)
from convert.adapters.solidworks.envelopes.revolve.pin.default.Envelope import (
    BuildEnvelope,
    CalcPinBounds,
    EncodeConfig,
    EncodeHeader,
    GetCoverage,
    KConfigBytes,
    KConfigFields,
    KConfigOwners,
    KHeaderIdentity,
    KHeaderStamps,
    KHeaderUser,
    KPinPointsMm,
)

# centralizes shared evidence so every related assertion uses one value
KFixtureRoot = (
    FilePath(__file__).resolve().parents[4]
    / "examples"
    / "Fixtures"
    / "SolidWorks"
    / "donors"
)

# centralizes shared evidence so every related assertion uses one value
KConfigDigest = "f5409831ddedb4c2c396e4b9485dc114acaf0d277e763edf35ac5daca1f0faf9"

# centralizes shared evidence so every related assertion uses one value
KHeaderDigest = "36335512255914fd6c84f47bb315368dfba48ab66dbee8b5c5195361f36f7d60"


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPCPHETC() -> None:
    PayloadData = EncodeConfig()
    CoverageData = GetCoverage()
    assert len(PayloadData) == KConfigBytes == 24902
    assert Hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
    assert CoverageData == {
        "stream_bytes": 24902,
        "typed": 24902,
        "opaque": 0,
        "accounted": 24902,
        "operations": KConfigFields,
        "owners": KConfigOwners,
    }
    assert KConfigFields == 4297
    assert KConfigOwners == 1058
    assert b"C:\\Users" not in PayloadData
    assert b".rescratch" not in PayloadData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPCPMCO() -> None:
    OracleData = (
        KFixtureRoot / "revolve_pin_top_full" / "container" / "Contents__Config-0.bin"
    ).read_bytes()
    assert EncodeConfig() == OracleData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPMHMCO() -> None:
    CreatedStamp, ModifiedStamp, BaselineStamp, HeaderStamp = KHeaderIdentity
    IdentityData = NativeIdentity(
        CreatedStamp, ModifiedStamp, BaselineStamp, HeaderStamp, Flags, "Part1"
    )
    HeaderData = HeaderPayload(
        IdentityData,
        "Default",
        (*Objects, (26, "Sketch1", True), (31, "Revolve1", False)),
        "",
        KHeaderUser,
        32,
        {26: KHeaderStamps[0], 31: KHeaderStamps[1]},
        CalcPinBounds(),
    )
    OracleData = (
        KFixtureRoot
        / "revolve_pin_top_full"
        / "container"
        / "Contents__Config-0-ModelHeader.bin"
    ).read_bytes()
    assert len(HeaderData) == 2305
    assert Hashlib.sha256(HeaderData).hexdigest() == KHeaderDigest
    assert HeaderData == OracleData
    assert EncodeHeader() == OracleData


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPECCACF() -> None:
    EnvelopeData = BuildEnvelope()
    assert EnvelopeData.Config0Payload == EncodeConfig()
    assert EnvelopeData.HeaderPayload == EncodeHeader()
    assert EnvelopeData.HeaderStamps == KHeaderStamps
    assert EnvelopeData.HeaderBounds == CalcPinBounds()
    assert EnvelopeData.HeaderCreation == KHeaderIdentity[0]


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPMHBFP() -> None:
    HeaderBounds = CalcPinBounds(KPinPointsMm)
    assert HeaderBounds[:3] == (0.0, 0.0, 0.025)
    assert HeaderBounds[3:6] == (0.0025, 0.0025, 0.05)
    assert HeaderBounds[6:9] == (-0.0025, -0.0025, 0.0)
    assert MathInfo.isclose(
        HeaderBounds[9], 0.025248762345905198, rel_tol=0.0, abs_tol=1e-18
    )
    WiderBounds = CalcPinBounds(
        tuple(((PointData[0] * 2.0, PointData[1] * 1.2) for PointData in KPinPointsMm))
    )
    assert WiderBounds[3:6] == (0.005, 0.005, 0.06)
    assert WiderBounds[6:9] == (-0.005, -0.005, 0.0)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPMHBRIP() -> None:
    with PytestLib.raises(SldprtFormatError, match="at least three"):
        CalcPinBounds(((0.0, 0.0), (1.0, 0.0)))
    with PytestLib.raises(SldprtFormatError, match="finite"):
        CalcPinBounds(((0.0, 0.0), (1.0, 0.0), (MathInfo.nan, -1.0)))
    with PytestLib.raises(SldprtFormatError, match="vertical axis"):
        CalcPinBounds(((1.0, 0.0), (2.0, 0.0), (2.0, -1.0)))
