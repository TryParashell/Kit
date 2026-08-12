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
from convert.adapters.solidworks.config0_revolve_pin_midplane_program import (
    EncodeProgram as EncodeConfig,
)
from convert.adapters.solidworks.config0_revolve_pin_midplane_program import (
    GetCoverage as GetConfigCoverage,
)
from convert.adapters.solidworks.config0_revolve_pin_midplane_program import (
    KConfigOps,
    KFieldOwners as KConfigOwners,
    KReferenceDigest as KConfigDigest,
    KReferenceLength as KConfigLength,
)
from convert.adapters.solidworks.container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.format import (
    CONFIGURATION_STREAM,
    RESOLVED_FEATURES_STREAM,
)
from convert.adapters.solidworks.resolved_revolve_pin_midplane_program import (
    EncodeProgram,
    GetCoverage,
    KFieldOwners,
    KFirstAngleOffsets,
    KProfileOffsets,
    KReferenceDigest,
    KReferenceLength,
    KResolvedOps,
    KSecondAngleOffsets,
    KSingleEndOffset,
)
from convert.adapters.solidworks.revolve_pin_envelope import CalcPinBounds
from convert.adapters.solidworks.revolve_pin_midplane_envelope import (
    BuildEnvelope,
    EncodeConfig as EncodeEnvelopeConfig,
    EncodeFeatures,
    EncodeHeader,
    KHeaderIdentity,
    KHeaderStamps,
    KHeaderUser,
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

# this digest freezes the coupled symmetric model header without embedding its bytes
KHeaderDigest = "4cb455532120074010565342eab6df3b83df1bf45ad0c25bf391664790de07ca"

# the corpus source proves production remains fail closed before its live vendor gate
KSourcePath = (
    Path(__file__).parents[2]
    / ".rescratch"
    / "sw"
    / "fcstd"
    / "kit_revolve_pin_top_midplane.FCStd"
)

# the authored oracle supports optional exact stream regression without production access
KOraclePath = (
    Path(__file__).parents[2]
    / ".rescratch"
    / "revolve_pin_midplane"
    / "revolve_pin_top_midplane.oracle.SLDPRT"
)


# production selection must remain disabled until the pending live vendor gate passes
@pytest.mark.skipif(
    not KSourcePath.is_file(),
    reason="top plane symmetric pin revolution corpus unavailable",
)
def test_midplane_pin_public_writer_remains_fail_closed(tmp_path: Path) -> None:
    SourceData = read_freecad(KSourcePath)
    with pytest.raises(ApplicationUsabilityError):
        write_document(
            SourceData,
            tmp_path / "MidplanePinPending.SLDPRT",
            allow_carrier=False,
        )


# the symmetric configuration must remain wholly typed and byte exact
def test_midplane_pin_config_program_has_exact_typed_coverage() -> None:
    PayloadData = EncodeConfig()
    assert len(PayloadData) == KConfigLength == 24902
    assert hashlib.sha256(PayloadData).hexdigest() == KConfigDigest
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


# every configuration operation must tile its stream under a recovered serializer
def test_midplane_pin_config_operations_tile_without_gaps() -> None:
    CursorValue = 0
    for StartPos, FieldWidth, OwnerIndex, _KindName, _DefaultValue in KConfigOps:
        assert StartPos == CursorValue
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(KConfigOwners)
        CursorValue += FieldWidth
    assert CursorValue == KConfigLength


# the recovered grammar must reproduce the symmetric header exactly
def test_midplane_pin_model_header_is_byte_exact() -> None:
    HeaderData = EncodeHeader()
    assert len(HeaderData) == 2305
    assert hashlib.sha256(HeaderData).hexdigest() == KHeaderDigest
    assert KHeaderIdentity == (1786487434, 106, 103, 1786487442)
    assert KHeaderStamps == ((1786487441, 1786487442), (1786487442,))
    assert KHeaderUser == "odin"


# full revolution bounds remain symmetric about both radial model axes
def test_midplane_pin_model_header_bounds_follow_profile() -> None:
    HeaderBounds = CalcPinBounds()
    assert HeaderBounds[:3] == (0.0, 0.0, 0.025)
    assert HeaderBounds[3:6] == (0.0025, 0.0025, 0.05)
    assert HeaderBounds[6:9] == (-0.0025, -0.0025, 0.0)
    assert HeaderBounds[9] == 0.025248762345905194


# one immutable carrier prevents feature configuration and header identity drift
def test_midplane_pin_envelope_carries_every_coupled_stream() -> None:
    EnvelopeData = BuildEnvelope()
    assert EnvelopeData.Config0Payload == EncodeEnvelopeConfig() == EncodeConfig()
    assert EnvelopeData.HeaderPayload == EncodeHeader()
    assert EnvelopeData.HeaderStamps == KHeaderStamps
    assert EnvelopeData.HeaderBounds == CalcPinBounds()
    assert EnvelopeData.HeaderCreation == KHeaderIdentity[0]
    assert EncodeFeatures() == EncodeProgram()


# exact typed coverage prevents hidden vendor bytes entering symmetric output
def test_midplane_pin_program_has_exact_typed_coverage() -> None:
    PayloadData = EncodeProgram()
    assert len(PayloadData) == KReferenceLength == 14065
    assert hashlib.sha256(PayloadData).hexdigest() == KReferenceDigest
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


# every recovered operation must tile the stream under a known serializer owner
def test_midplane_pin_program_operations_tile_without_gaps() -> None:
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


# the recovered two end structure preserves symmetric revolution semantics
def test_midplane_pin_program_carries_both_end_values() -> None:
    PayloadData = EncodeProgram()
    assert KSingleEndOffset == 10437
    assert struct.unpack_from("<I", PayloadData, KSingleEndOffset)[0] == 0
    assert KFirstAngleOffsets == (11281, 11795, 11819)
    assert KSecondAngleOffsets == (13033, 13547, 13571)
    assert all(
        struct.unpack_from("<d", PayloadData, OffsetValue)[0] == math.tau
        for OffsetValue in KFirstAngleOffsets
    )
    assert all(
        struct.unpack_from("<d", PayloadData, OffsetValue)[0] == 0.0
        for OffsetValue in KSecondAngleOffsets
    )


# recovered coordinate offsets must encode the stepped pin profile exactly
def test_midplane_pin_program_carries_all_profile_vertices() -> None:
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
def test_midplane_pin_program_rejects_variable_width_override() -> None:
    with pytest.raises(SldprtFormatError, match="field width changed"):
        EncodeProgram({11251: "D100"})


# first angle edits remain typed while the explicit opposite end stays unchanged
def test_midplane_pin_program_accepts_independent_first_angle_override() -> None:
    AngleValue = math.pi
    PayloadData = EncodeProgram(dict.fromkeys(KFirstAngleOffsets, AngleValue))
    assert all(
        struct.unpack_from("<d", PayloadData, OffsetValue)[0] == AngleValue
        for OffsetValue in KFirstAngleOffsets
    )
    assert all(
        struct.unpack_from("<d", PayloadData, OffsetValue)[0] == 0.0
        for OffsetValue in KSecondAngleOffsets
    )
    assert len(PayloadData) == KReferenceLength


# local oracle traces optionally prove all coupled typed streams byte exact
@pytest.mark.skipif(not KOraclePath.is_file(), reason="midplane oracle unavailable")
def test_midplane_pin_programs_match_local_oracle() -> None:
    ArchiveData = SldprtArchive.open(KOraclePath)
    assert ArchiveData.require(CONFIGURATION_STREAM) == EncodeConfig()
    assert ArchiveData.require(RESOLVED_FEATURES_STREAM) == EncodeProgram()
    assert ArchiveData.require("Contents/Config-0-ModelHeader") == EncodeHeader()
    assert ArchiveData.require("Header2") == EncodeHeader()
