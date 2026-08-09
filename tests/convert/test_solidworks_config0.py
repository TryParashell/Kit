# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import hashlib

import pytest

from convert.adapters.solidworks.config0 import (
    ATOM_DEFINITION_POSITION,
    CHAR_FORMAT_SERIALIZE,
    DETAIL_DEFS_CLASS,
    DETAIL_DEFS_SERIALIZE,
    DETAIL_OWNERS,
    DETAIL_REGION_BODIES,
    DETAIL_REGION_FIRST_NODE,
    DETAIL_REGION_LAST_NODE,
    DETAIL_REGION_PLAN,
    HIGH_WATER_POSITION,
    UNIT_NODE_BODIES,
    UNIT_NODE_RECORDS,
    UNIT_OWNERS,
    UNIT_RECORD_SERIALIZE,
    MAP_COUNTER_BASE,
    MEASURED_VOLUME_MM3,
    MO_VERSION,
    MODETAILDEFS_C_FIELDS,
    NODE_PLAN,
    PER_FEATURE_ATOM_BYTES,
    PER_SOLID_BODY_BYTES,
    PROLOGUE_CLASS,
    PROLOGUE_LENGTH,
    REFERENCE_ATOM_ID,
    REFERENCE_HIGH_WATER,
    REFERENCE_LENGTH,
    REFERENCE_PART_NAME,
    REFERENCE_SHA256,
    REFERENCE_TREE_ID,
    RESIDUAL_BYTES,
    RESIDUAL_MODETAILDEFS_C_TAIL,
    RESIDUAL_MORELMGR_C_HEAD,
    RESIDUAL_SPANS,
    SINGLE_LENGTH_UNIT_LENGTH,
    build_nodes,
    declared_detail_bytes,
    declared_opaque_split,
    declared_unit_bytes,
    encode_config0_stream,
    encode_detail_region,
)
from convert.adapters.solidworks.container import SldprtFormatError

PER_FEATURE_BYTES = 88
SECONDARY_LENGTH_UNIT_BYTES = 66
DERIVED_FRAMING_BYTES = 1045
DECLARED_BYTES = 19051
OPAQUE_BYTES = 5118
DECLARED_SHARE_PERCENT = 75.6
NAMED_OPAQUE_SHARE_PERCENT = 20.3
NODE_COUNT = 123
CLASS_DEFINITION_COUNT = 39
DETAIL_REGION_BYTES = 17484
DETAIL_DECLARED_BYTES = 17402
CHAR_FORMAT_INSTANCES = 81
UNIT_RECORD_COUNT = 17
UNIT_DECLARED_BYTES = 1077
UNIT_RESIDUAL_BYTES = 4
RESIDUAL_SPAN_COUNT = 67


def _atoms(features: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (REFERENCE_ATOM_ID + index, REFERENCE_TREE_ID + 8 * index)
        for index in range(features)
    )


def test_reference_payload_is_reproduced_byte_identically():
    stream = encode_config0_stream()
    assert len(stream) == REFERENCE_LENGTH
    assert len(stream) == 25214
    assert hashlib.sha256(stream).hexdigest() == REFERENCE_SHA256


@pytest.mark.parametrize("features", (1, 2, 3, 4, 5, 6, 7, 8))
def test_each_further_feature_adds_the_measured_atom_region(features):
    stream = encode_config0_stream(atoms=_atoms(features))
    assert len(stream) == REFERENCE_LENGTH + PER_FEATURE_BYTES * (features - 1)
    assert PER_FEATURE_ATOM_BYTES == PER_FEATURE_BYTES


def test_the_secondary_length_unit_record_is_a_named_variant():
    dual = encode_config0_stream()
    single = encode_config0_stream(dual_length_units=False)
    assert len(dual) - len(single) == SECONDARY_LENGTH_UNIT_BYTES
    assert len(single) == SINGLE_LENGTH_UNIT_LENGTH
    assert len(single) == 25148


def test_declared_and_opaque_bytes_tile_the_stream():
    split = declared_opaque_split()
    assert split["stream_bytes"] == REFERENCE_LENGTH
    assert split["derived_framing"] == DERIVED_FRAMING_BYTES
    assert split["declared"] == DECLARED_BYTES
    assert split["opaque"] == OPAQUE_BYTES
    assert split["accounted"] == split["stream_bytes"]
    assert (
        split["derived_framing"] + split["declared"] + split["opaque"]
        == split["stream_bytes"]
    )


def test_the_named_opaque_share_is_pinned_and_cannot_silently_grow():
    split = declared_opaque_split()
    declared_share = 100.0 * split["declared"] / split["stream_bytes"]
    opaque_share = 100.0 * split["opaque"] / split["stream_bytes"]
    assert round(declared_share, 1) == DECLARED_SHARE_PERCENT
    assert round(opaque_share, 1) == NAMED_OPAQUE_SHARE_PERCENT
    assert split["opaque"] <= OPAQUE_BYTES
    assert split["opaque"] <= 5118


def test_the_atom_region_is_the_only_content_that_grows_with_the_feature_set():
    split_one = declared_opaque_split(atoms=_atoms(1))
    split_three = declared_opaque_split(atoms=_atoms(3))
    assert split_three["opaque"] == split_one["opaque"]
    assert (
        split_three["stream_bytes"] - split_one["stream_bytes"] == 2 * PER_FEATURE_BYTES
    )


def test_every_opaque_byte_sits_in_a_span_named_for_its_owning_class():
    split = declared_opaque_split()
    assert sum(length for _name, length in RESIDUAL_SPANS) == RESIDUAL_BYTES
    assert RESIDUAL_BYTES == split["opaque"]
    assert len(RESIDUAL_SPANS) == RESIDUAL_SPAN_COUNT
    assert RESIDUAL_SPANS[0] == ("RESIDUAL_MORELMGR_C_HEAD", 36)
    assert RESIDUAL_SPANS[1] == ("RESIDUAL_MODETAILDEFS_C_TAIL", 2)
    assert ("RESIDUAL_MOUNITSYSUNITS_C_N011_TAIL", 2) in RESIDUAL_SPANS
    assert ("RESIDUAL_MOFORCEUNITS_C_N012_TAIL", 2) in RESIDUAL_SPANS
    assert len(RESIDUAL_MORELMGR_C_HEAD) == 36
    assert len(RESIDUAL_MODETAILDEFS_C_TAIL) == 2
    for name, length in RESIDUAL_SPANS:
        assert length > 0
        assert name.isupper() or name.startswith("RESIDUAL_")


def test_the_detail_defs_region_reconstructs_from_declared_fields():
    region = encode_detail_region()
    assert len(region) == DETAIL_REGION_BYTES
    declared, framing = declared_detail_bytes()
    assert declared == DETAIL_DECLARED_BYTES
    assert declared + framing + len(RESIDUAL_MORELMGR_C_HEAD) + len(
        RESIDUAL_MODETAILDEFS_C_TAIL
    ) == len(region)
    assert framing == 2 * (DETAIL_REGION_LAST_NODE - DETAIL_REGION_FIRST_NODE)


def test_the_detail_defs_region_tiles_its_node_bodies():
    assert len(DETAIL_REGION_PLAN) == DETAIL_REGION_LAST_NODE - (
        DETAIL_REGION_FIRST_NODE - 1
    )
    assert len(DETAIL_REGION_BODIES) == len(DETAIL_REGION_PLAN)
    for entry, body in zip(DETAIL_REGION_PLAN, DETAIL_REGION_BODIES, strict=True):
        assert len(body) == entry[3]
    assert DETAIL_REGION_PLAN[0][1] == "moRelMgr_c"


def test_every_declared_detail_field_names_its_owning_class():
    assert DETAIL_DEFS_CLASS == "moDetailDefs_c"
    assert DETAIL_DEFS_SERIALIZE == 0x3CB15020
    assert CHAR_FORMAT_SERIALIZE == 0x3CA7E750
    assert DETAIL_OWNERS[0].startswith("/moDetailDefs_c")
    for item in MODETAILDEFS_C_FIELDS:
        assert 0 <= item[1] < len(DETAIL_OWNERS)
        assert DETAIL_OWNERS[item[1]].startswith("/moDetailDefs_c")
    fonts = sum(
        1
        for item in MODETAILDEFS_C_FIELDS
        if item[0] == "s" and DETAIL_OWNERS[item[1]].endswith("/utCharFormat_c")
    )
    assert fonts == CHAR_FORMAT_INSTANCES


def test_every_unit_record_is_declared_from_its_recovered_serializer():
    assert len(UNIT_NODE_RECORDS) == UNIT_RECORD_COUNT
    declared, residual = declared_unit_bytes()
    assert declared == UNIT_DECLARED_BYTES
    assert residual == UNIT_RESIDUAL_BYTES
    addresses = dict(UNIT_RECORD_SERIALIZE)
    assert addresses["moUserUnits_c"] == 0x3CBC8E80
    assert addresses["moLengthUserUnits_c"] == 0x3CBC8CB0
    assert addresses["moAngleUserUnits_c"] == 0x3CBC89E0
    assert addresses["moDensityUnits_c"] == 0x3CBC8A40
    assert addresses["moEnergyUnits_c"] == 0x3CBC8C30
    for entry in UNIT_NODE_RECORDS:
        position, owner, fields, tail = entry
        assert NODE_PLAN[position][3] is UNIT_NODE_BODIES[position]
        assert owner in addresses
        assert UNIT_NODE_BODIES[position].endswith(bytes.fromhex(tail))
        for item in fields:
            assert 0 <= item[1] < len(UNIT_OWNERS)
            assert UNIT_OWNERS[item[1]].startswith("/")
        assert len(tail) % 2 == 0


def test_the_moUserUnits_c_block_is_sixty_two_bytes_in_every_unit_record():
    for entry in UNIT_NODE_RECORDS:
        widths = [
            item[3] if item[0] == "i" else (8 if item[2] == "double" else 4)
            for item in entry[2]
            if UNIT_OWNERS[item[1]].endswith("moUserUnits_c")
        ]
        assert sum(widths) == 62


def test_the_node_plan_matches_the_walked_reference_shape():
    assert len(NODE_PLAN) == NODE_COUNT
    definitions = [entry for entry in NODE_PLAN if entry[0] == "definition"]
    assert len(definitions) == CLASS_DEFINITION_COUNT
    assert NODE_PLAN[ATOM_DEFINITION_POSITION][1] == "moAtom_c"
    assert NODE_PLAN[HIGH_WATER_POSITION - 1][1] == "moCThreadRefMgr_c"
    assert MAP_COUNTER_BASE == 4
    assert MO_VERSION == 18000
    assert PROLOGUE_CLASS == "moPart_c"
    assert PROLOGUE_LENGTH == 26


def test_every_detail_region_node_position_names_a_plan_node():
    for position in range(DETAIL_REGION_FIRST_NODE, DETAIL_REGION_LAST_NODE + 1):
        assert 0 <= position < len(NODE_PLAN)
        assert NODE_PLAN[position][0] in {"null", "classref", "definition"}


def test_the_atom_region_carries_one_record_per_feature():
    nodes = build_nodes(
        REFERENCE_PART_NAME,
        _atoms(3),
        1,
        MO_VERSION,
        True,
        REFERENCE_HIGH_WATER,
    )
    assert sum(1 for entry in nodes if entry[1] == "moAtom_c") == 3


def test_stream_opens_with_the_part_class_definition_prologue():
    stream = encode_config0_stream()
    assert stream.startswith(
        b"\xff\xff\x01\x00" + bytes((len(PROLOGUE_CLASS), 0)) + b"moPart_c"
    )


def test_part_name_length_moves_the_stream_by_two_bytes_per_code_unit():
    assert len(encode_config0_stream(part_name="KitPart")) == REFERENCE_LENGTH + 2
    assert len(encode_config0_stream(part_name="Part1")) == REFERENCE_LENGTH - 2


def test_measured_volume_is_recorded_against_the_reference_payload():
    assert MEASURED_VOLUME_MM3 == 8000.000000000001
    assert PER_SOLID_BODY_BYTES == 16


def test_an_empty_atom_region_is_rejected():
    with pytest.raises(SldprtFormatError, match="at least one atom record"):
        encode_config0_stream(atoms=())


def test_a_foreign_document_generation_is_rejected():
    with pytest.raises(SldprtFormatError, match="recovered at generation"):
        encode_config0_stream(generation=14000)
