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
from convert.adapters.solidworks.native import (
    _HEADER_OBJECTS,
    _NativeIdentity,
    _SOLIDWORKS_CONFIGURATION_FLAGS,
    _header_payload,
)
from convert.adapters.solidworks.revolve_pin_envelope import (
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


# the repository fixture is development evidence and never a runtime dependency
KFixtureRoot = (
    Path(__file__).resolve().parents[1] / "fixtures" / "solidworks" / "donors"
)

# this digest freezes the completely owned configuration test vector
KConfigDigest = "f5409831ddedb4c2c396e4b9485dc114acaf0d277e763edf35ac5daca1f0faf9"

# this digest freezes the shared model header grammar and pin inputs
KHeaderDigest = "36335512255914fd6c84f47bb315368dfba48ab66dbee8b5c5195361f36f7d60"


# complete operation coverage prevents hidden vendor bytes entering pin output
def test_pin_config_program_has_exact_typed_coverage() -> None:
    PayloadData = EncodeConfig()
    CoverageData = GetCoverage()
    assert len(PayloadData) == KConfigBytes == 24902
    assert hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
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


# fixture equality proves the typed operations reproduce every configuration byte
def test_pin_config_program_matches_controlled_oracle() -> None:
    OracleData = (
        KFixtureRoot / "revolve_pin_top_full" / "container" / "Contents__Config-0.bin"
    ).read_bytes()
    assert EncodeConfig() == OracleData


# the existing header grammar becomes exact when supplied recovered pin semantics
def test_pin_model_header_matches_controlled_oracle() -> None:
    CreatedStamp, ModifiedStamp, BaselineStamp, HeaderStamp = KHeaderIdentity
    IdentityData = _NativeIdentity(
        CreatedStamp,
        ModifiedStamp,
        BaselineStamp,
        HeaderStamp,
        _SOLIDWORKS_CONFIGURATION_FLAGS,
        "Part1",
    )
    HeaderData = _header_payload(
        IdentityData,
        "Default",
        (*_HEADER_OBJECTS, (26, "Sketch1", True), (31, "Revolve1", False)),
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
    assert hashlib.sha256(HeaderData).hexdigest() == KHeaderDigest
    assert HeaderData == OracleData
    assert EncodeHeader() == OracleData


# one carrier keeps every proven load critical override synchronized
def test_pin_envelope_carrier_contains_all_coupled_fields() -> None:
    EnvelopeData = BuildEnvelope()
    assert EnvelopeData.Config0Payload == EncodeConfig()
    assert EnvelopeData.HeaderPayload == EncodeHeader()
    assert EnvelopeData.HeaderStamps == KHeaderStamps
    assert EnvelopeData.HeaderBounds == CalcPinBounds()
    assert EnvelopeData.HeaderCreation == KHeaderIdentity[0]


# source geometry must calculate header bounds rather than copy cached coordinates
def test_pin_model_header_bounds_follow_profile() -> None:
    HeaderBounds = CalcPinBounds(KPinPointsMm)
    assert HeaderBounds[:3] == (0.0, 0.0, 0.025)
    assert HeaderBounds[3:6] == (0.0025, 0.0025, 0.05)
    assert HeaderBounds[6:9] == (-0.0025, -0.0025, 0.0)
    assert math.isclose(
        HeaderBounds[9],
        0.025248762345905198,
        rel_tol=0.0,
        abs_tol=1.0e-18,
    )
    WiderBounds = CalcPinBounds(
        tuple((PointData[0] * 2.0, PointData[1] * 1.2) for PointData in KPinPointsMm)
    )
    assert WiderBounds[3:6] == (0.005, 0.005, 0.06)
    assert WiderBounds[6:9] == (-0.005, -0.005, 0.0)


# malformed profiles must fail before corrupting a load critical model header
def test_pin_model_header_bounds_reject_invalid_profiles() -> None:
    with pytest.raises(SldprtFormatError, match="at least three"):
        CalcPinBounds(((0.0, 0.0), (1.0, 0.0)))
    with pytest.raises(SldprtFormatError, match="finite"):
        CalcPinBounds(((0.0, 0.0), (1.0, 0.0), (math.nan, -1.0)))
    with pytest.raises(SldprtFormatError, match="vertical axis"):
        CalcPinBounds(((1.0, 0.0), (2.0, 0.0), (2.0, -1.0)))
