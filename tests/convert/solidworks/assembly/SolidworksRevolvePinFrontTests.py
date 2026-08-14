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
import struct

import pytest

from convert import ApplicationUsabilityError, write_document
from convert.adapters.freecad import read_freecad
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import EncodeProgram as EncodeConfig
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import GetCoverage as GetConfigCoverage
from convert.adapters.solidworks.programs.configuration.revolve.pin.front.Program import KAnnotationMatrixOffset, KConfigOps, KFieldOwners as KConfigOwners, KReferenceDigest as KConfigDigest, KReferenceLength as KConfigLength
from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.programs.resolved.revolve.pin.front.Program import EncodeProgram, GetCoverage, KAngleOffsets, KFieldOwners, KProfileOffsets, KReferenceDigest, KReferenceLength, KResolvedOps
from convert.adapters.solidworks.envelopes.revolve.pin.front.Envelope import BuildEnvelope, CalcPinFrontBounds, EncodeConfig as EncodeEnvelopeConfig, EncodeFeatures, EncodeHeader, KHeaderIdentity, KHeaderLogReference, KHeaderModelReference, KHeaderStamps, KHeaderUser


# the canonical profile values independently verify every editable sketch vertex
KProfileMetres = (
    (0.0, -0.05),
    (0.0, 0.0),
    (0.0025, 0.0),
    (0.0025, -0.03),
    (0.0015, -0.02999),
    (0.0015, -0.05),
)

# this digest freezes the coupled front plane model header without embedding its bytes
KHeaderDigest = "6f7bd56fa6997638046a3013475af74469a90e115ae28ee3e338431bfb14820b"

# the corpus source proves production remains fail closed before a live vendor gate
KSourcePath = (
    Path(__file__).parents[4]
    / ".rescratch"
    / "sw"
    / "fcstd"
    / "kit_revolve_pin_front.FCStd"
)


# production selection must remain disabled until the pending live vendor gate passes
@pytest.mark.skipif(
    not KSourcePath.is_file(),
    reason="front plane pin revolution corpus unavailable",
)
def test_front_pin_public_writer_remains_fail_closed(tmp_path: Path) -> None:
    SourceData = read_freecad(KSourcePath)
    with pytest.raises(ApplicationUsabilityError):
        write_document(
            SourceData,
            tmp_path / "FrontPinPending.SLDPRT",
            allow_carrier=False,
        )


# the front plane configuration must remain wholly typed and byte exact
def test_front_pin_config_program_has_exact_typed_coverage() -> None:
    PayloadData = EncodeConfig()
    CoverageData = GetConfigCoverage()
    assert len(PayloadData) == KConfigLength == 24976
    assert hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
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


# every configuration operation must tile its stream under a recovered serializer
def test_front_pin_config_operations_tile_without_gaps() -> None:
    CursorValue = 0
    for StartPos, FieldWidth, OwnerIndex, _KindName, _DefaultValue in KConfigOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KConfigOwners)
        CursorValue += FieldWidth
    assert CursorValue == KConfigLength


# the annotation view carries the explicit front plane orientation basis
def test_front_pin_config_carries_annotation_matrix() -> None:
    PayloadData = EncodeConfig()
    assert struct.unpack_from("<9d", PayloadData, KAnnotationMatrixOffset) == (
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


# the recovered grammar must reproduce the front plane header exactly
def test_front_pin_model_header_is_byte_exact() -> None:
    HeaderData = EncodeHeader()
    assert len(HeaderData) == 2305
    assert hashlib.sha256(HeaderData).hexdigest() == KHeaderDigest
    assert KHeaderIdentity == (1785928014, 106, 103, 1785928015)
    assert KHeaderStamps == ((1785928015, 1785928015), (1785928015,))
    assert KHeaderUser == "odin"
    assert (KHeaderLogReference, KHeaderModelReference) == ("Part1", "Part2")


# front plane bounds map the profile axis into negative model y
def test_front_pin_model_header_bounds_follow_profile() -> None:
    HeaderBounds = CalcPinFrontBounds()
    assert HeaderBounds[:3] == (0.0, -0.025, 0.0)
    assert HeaderBounds[3:6] == (0.0025, 0.0, 0.0025)
    assert HeaderBounds[6:9] == (-0.0025, -0.05, -0.0025)
    assert HeaderBounds[9] == 0.025248762345905194


# one immutable carrier prevents feature configuration and header identity drift
def test_front_pin_envelope_carries_every_coupled_stream() -> None:
    EnvelopeData = BuildEnvelope()
    assert EnvelopeData.Config0Payload == EncodeEnvelopeConfig() == EncodeConfig()
    assert EnvelopeData.HeaderPayload == EncodeHeader()
    assert EnvelopeData.HeaderStamps == KHeaderStamps
    assert EnvelopeData.HeaderBounds == CalcPinFrontBounds()
    assert EnvelopeData.HeaderCreation == KHeaderIdentity[0]
    assert EncodeFeatures() == EncodeProgram()


# exact typed coverage prevents hidden vendor bytes entering front revolution output
def test_front_pin_program_has_exact_typed_coverage() -> None:
    PayloadData = EncodeProgram()
    CoverageData = GetCoverage()
    assert len(PayloadData) == KReferenceLength == 12265
    assert hashlib.sha256(PayloadData).hexdigest() == KReferenceDigest
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


# every recovered operation must tile the stream under a known serializer owner
def test_front_pin_program_operations_tile_without_gaps() -> None:
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


# the traced angle copies preserve one editable full revolution parameter
def test_front_pin_program_carries_all_angle_values() -> None:
    PayloadData = EncodeProgram()
    AngleBytes = struct.pack("<d", math.tau)
    assert KAngleOffsets == (11209, 11723, 11747)
    assert all(
        PayloadData[OffsetValue : OffsetValue + 8] == AngleBytes
        for OffsetValue in KAngleOffsets
    )


# recovered coordinate offsets must encode the stepped pin profile exactly
def test_front_pin_program_carries_all_profile_vertices() -> None:
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
def test_front_pin_program_rejects_variable_width_override() -> None:
    with pytest.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({11179: "D100"})


# numeric overrides remain typed while recovered object framing stays immutable
def test_front_pin_program_accepts_same_width_angle_override() -> None:
    AngleValue = math.radians(270.0)
    PayloadData = EncodeProgram(dict.fromkeys(KAngleOffsets, AngleValue))
    assert all(
        struct.unpack_from("<d", PayloadData, OffsetValue)[0] == AngleValue
        for OffsetValue in KAngleOffsets
    )
    assert len(PayloadData) == KReferenceLength
