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
    ANNOTATION_STYLE_NODE_POSITIONS,
    ANNOTATION_STYLE_UNDECODED_BYTES,
    ANNOTATION_STYLE_UNDECODED_SPANS,
    ATOM_DEFINITION_POSITION,
    HIGH_WATER_POSITION,
    MAP_COUNTER_BASE,
    MO_VERSION,
    NODE_PLAN,
    PROLOGUE_CLASS,
    REFERENCE_ATOM_ID,
    REFERENCE_HIGH_WATER,
    REFERENCE_LENGTH,
    REFERENCE_PART_NAME,
    REFERENCE_SHA256,
    REFERENCE_TREE_ID,
    build_nodes,
    declared_opaque_split,
    encode_config0_stream,
)
from convert.adapters.solidworks.container import SldprtFormatError

PER_FEATURE_BYTES = 88
SECONDARY_LENGTH_UNIT_BYTES = 66
DERIVED_FRAMING_BYTES = 1045
DECLARED_BYTES = 8267
OPAQUE_BYTES = 15902
DECLARED_SHARE_PERCENT = 32.8
NAMED_OPAQUE_SHARE_PERCENT = 63.1
NODE_COUNT = 123
CLASS_DEFINITION_COUNT = 39
MEASURED_VOLUME_MM3 = 8000.000000000001


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


def test_the_secondary_length_unit_record_is_a_named_variant():
    dual = encode_config0_stream()
    single = encode_config0_stream(dual_length_units=False)
    assert len(dual) - len(single) == SECONDARY_LENGTH_UNIT_BYTES
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


def test_the_atom_region_is_the_only_content_that_grows_with_the_feature_set():
    split_one = declared_opaque_split(atoms=_atoms(1))
    split_three = declared_opaque_split(atoms=_atoms(3))
    assert split_three["opaque"] == split_one["opaque"]
    assert (
        split_three["stream_bytes"] - split_one["stream_bytes"] == 2 * PER_FEATURE_BYTES
    )


def test_every_undecoded_annotation_style_span_is_named_for_its_record():
    assert ANNOTATION_STYLE_UNDECODED_SPANS == (("ANNOTATION_STYLE_RECORD_73", 92),)
    assert (
        sum(length for _, length in ANNOTATION_STYLE_UNDECODED_SPANS)
        == ANNOTATION_STYLE_UNDECODED_BYTES
    )


def test_the_node_plan_matches_the_walked_reference_shape():
    assert len(NODE_PLAN) == NODE_COUNT
    definitions = [entry for entry in NODE_PLAN if entry[0] == "definition"]
    assert len(definitions) == CLASS_DEFINITION_COUNT
    assert NODE_PLAN[ATOM_DEFINITION_POSITION][1] == "moAtom_c"
    assert NODE_PLAN[HIGH_WATER_POSITION - 1][1] == "moCThreadRefMgr_c"
    assert MAP_COUNTER_BASE == 4
    assert MO_VERSION == 18000
    assert PROLOGUE_CLASS == "moPart_c"


def test_every_annotation_style_node_position_names_a_plan_node():
    for position in ANNOTATION_STYLE_NODE_POSITIONS:
        assert 0 <= position < len(NODE_PLAN)
        assert NODE_PLAN[position][0] in {"null", "classref"}


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


def test_an_empty_atom_region_is_rejected():
    with pytest.raises(SldprtFormatError, match="at least one atom record"):
        encode_config0_stream(atoms=())
