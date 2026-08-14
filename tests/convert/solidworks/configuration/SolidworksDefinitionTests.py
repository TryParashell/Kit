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

from convert.adapters.solidworks.container.Container import SldprtFormatError
from convert.adapters.solidworks.container.Definition import ASSEMBLY_CLSID, DOCUMENT_GENERATION, DRAFTING_STANDARDS, LINE_FONT_BINDINGS, LINE_STYLES, OPAQUE_SPANS, PART_CLSID, encode_body, encode_definition_stream, encode_string

RECORDED_BODY_BYTES = 3618
RECORDED_BODY_DIGEST = (
    "f5b20e1c8dbe0efece6a9d07f0806a0c8d051509a8c38431024e61986d887a9e"
)
RECORDED_BODY_USER = "odin"
RECORDED_DECLARED_BYTES = 3618
RECORDED_OPAQUE_BYTES = 0
RECORDED_OPAQUE_SPANS = 0
DEFAULT_STREAM_BYTES = 3736
DEFAULT_STREAM_DIGEST = (
    "7479a6640fa3647a4801f41bc2bd1cc4a08c845620fc0a4412dd2aa407aadf19"
)
CLSID_OFFSET = 20
CLSID_BYTES = 16
VIEW_BLOCK_BYTES = 72
IDENTITY_VIEW = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)


def test_body_is_byte_identical_to_the_recorded_body():
    encoded = encode_body(standard=DRAFTING_STANDARDS[0], user=RECORDED_BODY_USER)
    assert len(encoded) == RECORDED_BODY_BYTES
    assert hashlib.sha256(encoded).hexdigest() == RECORDED_BODY_DIGEST


# typed ownership now covers every byte of the definition body
def test_declared_bytes_cover_the_complete_body():
    opaque = sum(len(span) for span in OPAQUE_SPANS)
    assert len(OPAQUE_SPANS) == RECORDED_OPAQUE_SPANS
    assert opaque == RECORDED_OPAQUE_BYTES
    assert RECORDED_DECLARED_BYTES + opaque == RECORDED_BODY_BYTES
    encoded = encode_body(standard=DRAFTING_STANDARDS[0], user=RECORDED_BODY_USER)
    assert len(encoded) - opaque == RECORDED_DECLARED_BYTES


# source inspection prevents fixed vendor blocks from returning to the writer
def test_definition_writer_contains_no_encoded_vendor_blocks() -> None:
    ProgramPath = (
        Path(__file__).parents[4] / "src/convert/adapters/solidworks/container/Definition.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "OPAQUE_SPANS = (" not in SourceText


def test_tables_hold_the_recorded_settings():
    assert len(LINE_STYLES) == 7
    assert len(LINE_FONT_BINDINGS) == 40
    assert DOCUMENT_GENERATION == 18000
    assert DRAFTING_STANDARDS == ("moBS_c", "moISO_c", "moANSI_c")


def test_default_stream_matches_the_recorded_digest():
    stream = encode_definition_stream()
    assert len(stream) == DEFAULT_STREAM_BYTES
    assert hashlib.sha256(stream).hexdigest() == DEFAULT_STREAM_DIGEST


@pytest.mark.parametrize(
    ("standard", "expected"),
    (("moBS_c", 3736), ("moISO_c", 3737), ("moANSI_c", 3738)),
)
def test_every_drafting_standard_emits_its_recorded_length(standard, expected):
    stream = encode_definition_stream(standard=standard)
    assert len(stream) == expected
    assert stream.count(standard.encode("ascii")) == 1


@pytest.mark.parametrize(
    ("user", "expected"),
    (
        ("Kit", 3736),
        ("odin", 3738),
        ("Parashell", 3748),
        ("abcdefghijklmnopqrstuvwxyz1", 3784),
    ),
)
def test_user_name_length_moves_the_stream_by_two_bytes_per_code_unit(user, expected):
    stream = encode_definition_stream(user=user)
    assert len(stream) == expected
    assert stream.count(encode_string(user)) == 1


def test_assembly_selects_the_assembly_clsid():
    part = encode_definition_stream()
    assembly = encode_definition_stream(assembly=True)
    assert part[CLSID_OFFSET : CLSID_OFFSET + CLSID_BYTES] == PART_CLSID
    assert assembly[CLSID_OFFSET : CLSID_OFFSET + CLSID_BYTES] == ASSEMBLY_CLSID
    assert len(assembly) == DEFAULT_STREAM_BYTES


def test_view_block_adds_seventy_two_bytes():
    stream = encode_definition_stream(view=IDENTITY_VIEW)
    assert len(stream) == DEFAULT_STREAM_BYTES + VIEW_BLOCK_BYTES
    assert stream[CLSID_OFFSET + CLSID_BYTES + 3] == 1


def test_unknown_drafting_standard_is_rejected():
    with pytest.raises(SldprtFormatError):
        encode_definition_stream(standard="moDIN_c")


def test_short_view_block_is_rejected():
    with pytest.raises(SldprtFormatError):
        encode_definition_stream(view=(1.0, 0.0, 0.0))
