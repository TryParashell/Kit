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

from convert import write_document
from convert.adapters.freecad import read_freecad
from convert.adapters.solidworks.container import SldprtArchive, SldprtFormatError
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
from convert.adapters.solidworks.format import (
    CONFIGURATION_STREAM,
    KIT_RESOLVED_STREAM,
    RESOLVED_FEATURES_STREAM,
)
from convert.adapters.solidworks.revolve_pin90_envelope import (
    BuildEnvelope,
    CalcPin90Bounds,
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

# this digest freezes the coupled partial model header without embedding its bytes
KHeaderDigest = "9d146ad95cacd429338ca34ba74acb4b725ae8bce2c4d3018e99e3fcd4873880"

# the corpus source exercises the complete public FreeCAD to SOLIDWORKS path
KSourcePath = (
    Path(__file__).parents[2]
    / ".rescratch"
    / "sw"
    / "fcstd"
    / "kit_revolve_pin_top_90.FCStd"
)


# the public writer must select every coupled partial stream without a carrier
@pytest.mark.skipif(
    not KSourcePath.is_file(),
    reason="top plane partial pin revolution corpus unavailable",
)
def test_pin90_public_writer_selects_coupled_envelope(tmp_path: Path) -> None:
    SourceData = read_freecad(KSourcePath)
    TargetPath = tmp_path / "Pin90Public.SLDPRT"
    ResultData = write_document(SourceData, TargetPath, allow_carrier=False)
    ArchiveData = SldprtArchive.open(TargetPath)
    EnvelopeData = BuildEnvelope()
    assert ResultData.vendor_loadable is True
    assert ResultData.application_usable is True
    assert ResultData.near_lossless is True
    assert ResultData.metadata["runtime"] == "python-stdlib"
    assert KIT_RESOLVED_STREAM not in ArchiveData.streams
    assert ArchiveData.require(RESOLVED_FEATURES_STREAM) == EncodeFeatures()
    assert ArchiveData.require(CONFIGURATION_STREAM) == EnvelopeData.Config0Payload
    assert (
        ArchiveData.require("Contents/Config-0-ModelHeader")
        == EnvelopeData.HeaderPayload
    )
    assert ArchiveData.require("Header2") == EnvelopeData.HeaderPayload


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


# the recovered grammar must reproduce the partial topology header exactly
def test_pin90_model_header_is_byte_exact() -> None:
    HeaderData = EncodeHeader()
    assert len(HeaderData) == 2305
    assert hashlib.sha256(HeaderData).hexdigest() == KHeaderDigest
    assert KHeaderIdentity == (1786479979, 106, 103, 1786479985)
    assert KHeaderStamps == ((1786479985, 1786479985), (1786479985,))
    assert KHeaderUser == "odin"


# quadrant bounds must follow the source profile rather than a full radial cache
def test_pin90_model_header_bounds_follow_profile() -> None:
    HeaderBounds = CalcPin90Bounds()
    assert HeaderBounds[:3] == (0.00125, 0.00125, 0.025)
    assert HeaderBounds[3:6] == (0.0025, 0.0025, 0.05)
    assert HeaderBounds[6:9] == (0.0, 0.0, 0.0)
    assert math.isclose(
        HeaderBounds[9],
        0.025062422069704278,
        rel_tol=0.0,
        abs_tol=1.0e-18,
    )


# one immutable carrier prevents feature configuration and header identity drift
def test_pin90_envelope_carries_every_coupled_stream() -> None:
    EnvelopeData = BuildEnvelope()
    assert EnvelopeData.Config0Payload == EncodeEnvelopeConfig() == EncodeConfig()
    assert EnvelopeData.HeaderPayload == EncodeHeader()
    assert EnvelopeData.HeaderStamps == KHeaderStamps
    assert EnvelopeData.HeaderBounds == CalcPin90Bounds()
    assert EnvelopeData.HeaderCreation == KHeaderIdentity[0]
    assert EncodeFeatures() == EncodeProgram()


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
