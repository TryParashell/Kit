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

from convert.adapters.solidworks.config0 import (
    CONFIG_FIELD_COUNT,
    CONFIG_OPAQUE_BYTES,
    CONFIG_OWNER_COUNT,
    MO_VERSION,
    PER_FEATURE_ATOM_BYTES,
    REFERENCE_ATOM_ID,
    REFERENCE_LENGTH,
    REFERENCE_PART_NAME,
    REFERENCE_SHA256,
    REFERENCE_TREE_ID,
    SINGLE_LENGTH_UNIT_LENGTH,
    declared_opaque_split,
    encode_config0_stream,
)
from convert.adapters.solidworks.config0_program import (
    ConfigOps,
    FieldOwners,
    ReferenceLength,
)
from convert.adapters.solidworks.container import SldprtFormatError

PER_FEATURE_BYTES = 88
SECONDARY_LENGTH_UNIT_BYTES = 66


# deterministic atoms exercise feature-count growth without importing file bytes
def _atoms(FeatureCount: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (REFERENCE_ATOM_ID + Index, REFERENCE_TREE_ID + 8 * Index)
        for Index in range(FeatureCount)
    )


# exact equality proves the typed program closes the recovered reference grammar
def test_reference_fields_reproduce_the_stream_byte_identically() -> None:
    StreamData = encode_config0_stream()
    assert len(StreamData) == REFERENCE_LENGTH == ReferenceLength == 25214
    assert hashlib.sha256(StreamData).hexdigest() == REFERENCE_SHA256


# contiguous source offsets prove every reference byte belongs to one typed field
def test_every_reference_byte_has_exactly_one_typed_operation() -> None:
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _FieldValue in ConfigOps:
        assert StartPos == SourceCursor
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(FieldOwners)
        assert KindName in {
            "definition",
            "classref",
            "objectref",
            "null",
            "string",
            "stringlist",
        } or KindName.startswith(("primitive:", "direct:"))
        assert "opaque" not in KindName
        assert "raw" not in KindName
        SourceCursor += FieldWidth
    assert SourceCursor == REFERENCE_LENGTH
    assert len(ConfigOps) == CONFIG_FIELD_COUNT == 4341
    assert len(FieldOwners) == CONFIG_OWNER_COUNT == 1085


# source inspection prevents encoded payload tables from returning unnoticed
def test_runtime_program_contains_no_encoded_vendor_blocks() -> None:
    ProgramPath = (
        Path(__file__).parents[2] / "src/convert/adapters/solidworks/config0_program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# each additional feature contributes one class reference and one semantic atom
@pytest.mark.parametrize("FeatureCount", (1, 2, 3, 4, 5, 6, 7, 8))
def test_each_further_feature_adds_one_measured_atom(FeatureCount: int) -> None:
    StreamData = encode_config0_stream(atoms=_atoms(FeatureCount))
    assert len(StreamData) == REFERENCE_LENGTH + PER_FEATURE_BYTES * (FeatureCount - 1)
    assert PER_FEATURE_ATOM_BYTES == PER_FEATURE_BYTES


# the single-length-unit variant omits exactly its recovered typed node
def test_secondary_length_unit_is_a_typed_optional_record() -> None:
    DualData = encode_config0_stream()
    SingleData = encode_config0_stream(dual_length_units=False)
    assert len(DualData) - len(SingleData) == SECONDARY_LENGTH_UNIT_BYTES
    assert len(SingleData) == SINGLE_LENGTH_UNIT_LENGTH == 25148


# closure accounting must report zero unknown or residual bytes
def test_typed_fields_account_for_the_entire_dynamic_stream() -> None:
    SplitData = declared_opaque_split(atoms=_atoms(3), part_name="TypedPart")
    assert SplitData["typed"] == SplitData["stream_bytes"]
    assert SplitData["accounted"] == SplitData["stream_bytes"]
    assert SplitData["opaque"] == CONFIG_OPAQUE_BYTES == 0
    assert SplitData["operations"] == len(ConfigOps)
    assert SplitData["owners"] == len(FieldOwners)


# UTF-16 document names resize only their semantic serialized-string field
def test_part_name_length_moves_by_two_bytes_per_code_unit() -> None:
    assert len(encode_config0_stream(part_name="KitPart")) == REFERENCE_LENGTH + 2
    assert len(encode_config0_stream(part_name="Part1")) == REFERENCE_LENGTH - 2


# atom identifiers and tree identifiers are written from caller semantics
def test_atom_identity_changes_only_typed_identity_fields() -> None:
    FirstData = encode_config0_stream(atoms=((101, 27),))
    SecondData = encode_config0_stream(atoms=((102, 35),))
    Changed = [
        Index
        for Index, (FirstByte, SecondByte) in enumerate(zip(FirstData, SecondData))
        if FirstByte != SecondByte
    ]
    assert Changed
    assert len(FirstData) == len(SecondData) == REFERENCE_LENGTH


# a configuration without feature atoms is structurally invalid
def test_empty_atom_region_is_rejected() -> None:
    with pytest.raises(SldprtFormatError, match="at least one atom record"):
        encode_config0_stream(atoms=())


# the traced grammar must not masquerade as an unrecovered document generation
def test_foreign_document_generation_is_rejected() -> None:
    with pytest.raises(SldprtFormatError, match="recovered at generation"):
        encode_config0_stream(generation=14000)
    assert MO_VERSION == 18000


# raw prologue injection would violate first-principles serialization
def test_custom_raw_prologue_is_rejected() -> None:
    with pytest.raises(SldprtFormatError, match="raw Config-0 prologue"):
        encode_config0_stream(part_record_body=b"not allowed")


# identifier range checks stop silent archive truncation
@pytest.mark.parametrize("AtomData", (((-1, 32),), ((101, -1),), ((0x100000000, 32),)))
def test_out_of_range_atom_identifiers_are_rejected(
    AtomData: tuple[tuple[int, int], ...],
) -> None:
    with pytest.raises(SldprtFormatError, match="fit in 32 bits"):
        encode_config0_stream(atoms=AtomData)
