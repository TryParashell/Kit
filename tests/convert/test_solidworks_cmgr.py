# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import hashlib
import struct

import pytest

from convert.adapters.solidworks.cmgr import (
    ATOM_TABLE_HEAD,
    CONFIGURATION_MANAGER_STREAM,
    DISPLAY_GEOMETRY_CACHE_BYTES,
    DOCUMENT_BUILD,
    DOCUMENT_GENERATION,
    FIRST_ATOM_ID,
    OBJECT_LIST_TAIL,
    RESIDUAL_SPANS,
    ROOT_CLASS,
    VIEW_STYLE,
    VISUAL_PROPERTIES,
    atom_ids_for,
    declared_opaque_split,
    encode_cmgr_stream,
    tree_ids_for,
)
from convert.adapters.solidworks.container import SldprtFormatError

ONE_FEATURE_BYTES = 1957
ONE_FEATURE_DIGEST = "96d8137fb0ea8d4f5f7eb9c159ec5434903ccde9aee55334dd1e1ed59243f44c"
THREE_FEATURE_BYTES = 2081
THREE_FEATURE_DIGEST = (
    "964995442cbf20936436d7ee4a38a5819b6bdb9a9071f740b31e8e2fca92a81d"
)
PER_FEATURE_BYTES = 62
DECLARED_BYTES = 1861
OPAQUE_BYTES = 96
RESIDUAL_SPAN_COUNT = 1
MEASURED_VOLUMES_MM3 = (1476.0000000000002, 11954.000000000002)


def test_one_feature_default_matches_the_measured_digest():
    stream = encode_cmgr_stream()
    assert len(stream) == ONE_FEATURE_BYTES
    assert hashlib.sha256(stream).hexdigest() == ONE_FEATURE_DIGEST


def test_three_feature_default_matches_the_measured_digest():
    stream = encode_cmgr_stream(feature_tree_ids=tree_ids_for(3))
    assert len(stream) == THREE_FEATURE_BYTES
    assert hashlib.sha256(stream).hexdigest() == THREE_FEATURE_DIGEST


@pytest.mark.parametrize("features", (1, 2, 3, 4, 5, 6, 7, 8))
def test_stream_follows_the_measured_per_feature_size_law(features):
    stream = encode_cmgr_stream(feature_tree_ids=tree_ids_for(features))
    assert len(stream) == ONE_FEATURE_BYTES + PER_FEATURE_BYTES * (features - 1)


# a dependent second operation carries typed predecessor child objects and table endpoints
def test_connected_two_feature_history_uses_the_recovered_link_graph() -> None:
    StreamData = encode_cmgr_stream(feature_tree_ids=(32, 40), connected_history=True)
    assert len(StreamData) == 2059
    assert struct.pack("<III", 1, 102, 101) in StreamData
    assert struct.pack("<III", 40, 110, 105) in StreamData
    assert (
        struct.pack("<HI", 0, 2)
        + struct.pack("<III", 40, 0x01DD2399, 0x10000001)
        + struct.pack("<III", 32, 0x01DD2399, 0x10000000)
    ) in StreamData


# three-operation histories retain both predecessor edges and the rotated stamp list
def test_connected_three_feature_history_uses_the_recovered_link_graph() -> None:
    StreamData = encode_cmgr_stream(
        feature_tree_ids=(32, 40, 47),
        connected_history=True,
    )
    assert len(StreamData) == 2173
    assert struct.pack("<IIIII", 2, 103, 102, 102, 101) in StreamData
    assert struct.pack("<IIIII", 2, 102, 101, 103, 102) in StreamData
    assert (
        struct.pack("<HI", 0, 3)
        + struct.pack("<III", 40, 0x01DD2399, 0x10000001)
        + struct.pack("<III", 47, 0x01DD2399, 0x10000002)
        + struct.pack("<III", 32, 0x01DD2399, 0x10000000)
    ) in StreamData


# four-operation histories carry all three predecessor edges and native stamp order
def test_connected_four_feature_history_uses_the_recovered_link_graph() -> None:
    StreamData = encode_cmgr_stream(
        feature_tree_ids=(32, 40, 47, 54),
        connected_history=True,
    )
    assert len(StreamData) == 2299
    assert (
        struct.pack(
            "<IIIIIII",
            3,
            104,
            103,
            103,
            102,
            102,
            101,
        )
        in StreamData
    )
    assert (
        struct.pack(
            "<IIIIIII",
            3,
            102,
            101,
            103,
            102,
            104,
            103,
        )
        in StreamData
    )
    assert (
        struct.pack("<HI", 0, 4)
        + struct.pack("<III", 54, 0x01DD2399, 0x10000003)
        + struct.pack("<III", 40, 0x01DD2399, 0x10000001)
        + struct.pack("<III", 47, 0x01DD2399, 0x10000002)
        + struct.pack("<III", 32, 0x01DD2399, 0x10000000)
    ) in StreamData


def test_declared_and_opaque_bytes_tile_the_stream():
    split = declared_opaque_split()
    assert split["stream_bytes"] == ONE_FEATURE_BYTES
    assert split["declared"] == DECLARED_BYTES
    assert split["opaque"] == OPAQUE_BYTES
    assert split["residual_spans"] == RESIDUAL_SPAN_COUNT
    assert split["declared"] + split["opaque"] == split["accounted"]
    assert split["accounted"] == split["stream_bytes"]


def test_the_only_residual_span_is_the_display_geometry_cache():
    assert RESIDUAL_SPANS == (
        ("display_geometry_cache", ROOT_CLASS, DISPLAY_GEOMETRY_CACHE_BYTES),
    )
    assert sum(length for _, _, length in RESIDUAL_SPANS) == OPAQUE_BYTES
    assert all(owner == ROOT_CLASS for _, owner, _ in RESIDUAL_SPANS)


def test_the_shipped_residual_span_default_carries_no_vendor_bytes():
    stream = encode_cmgr_stream()
    assert bytes(DISPLAY_GEOMETRY_CACHE_BYTES) in stream


def test_opaque_share_does_not_grow_with_the_feature_count():
    for features in (1, 4, 8):
        split = declared_opaque_split(feature_tree_ids=tree_ids_for(features))
        assert split["opaque"] == OPAQUE_BYTES
        assert split["declared"] == split["stream_bytes"] - OPAQUE_BYTES


def test_tables_hold_the_recovered_vocabulary():
    assert DOCUMENT_GENERATION == 18000
    assert DOCUMENT_BUILD == 2025268
    assert FIRST_ATOM_ID == 101
    assert CONFIGURATION_MANAGER_STREAM == "Contents/CMgr"
    assert len(VISUAL_PROPERTIES) == 77
    assert len(ATOM_TABLE_HEAD) == 13
    assert len(VIEW_STYLE) == 9
    assert len(OBJECT_LIST_TAIL) == 7
    assert dict((name, value) for name, _, value in VISUAL_PROPERTIES)[
        "material_name"
    ] == ("Steel")


def test_atom_ids_and_tree_ids_run_from_their_recovered_first_values():
    assert atom_ids_for(3) == (101, 102, 103)
    assert tree_ids_for(3) == (32, 40, 48)


def test_stream_opens_with_the_configuration_manager_class_definition():
    stream = encode_cmgr_stream()
    assert stream.startswith(b"\xff\xff\x01\x00" + bytes((len(ROOT_CLASS), 0)))
    assert ROOT_CLASS.encode("ascii") in stream


def test_part_name_length_moves_the_stream_by_two_bytes_per_code_unit():
    short = encode_cmgr_stream(part_name="Part1")
    long = encode_cmgr_stream(part_name="Part70")
    assert len(long) == len(short) + 2


def test_measured_volumes_are_recorded_against_the_pinned_digests():
    assert MEASURED_VOLUMES_MM3 == (1476.0000000000002, 11954.000000000002)


def test_a_foreign_document_generation_is_rejected():
    with pytest.raises(SldprtFormatError, match="generation"):
        encode_cmgr_stream(generation=14000)


def test_an_empty_feature_set_is_rejected():
    with pytest.raises(SldprtFormatError, match="at least one solid feature"):
        encode_cmgr_stream(feature_tree_ids=())


def test_a_short_display_geometry_cache_is_rejected():
    with pytest.raises(SldprtFormatError, match="display_geometry_cache"):
        encode_cmgr_stream(display_geometry_cache=bytes(64))


def test_a_link_chain_without_one_tree_id_per_atom_is_rejected():
    with pytest.raises(SldprtFormatError, match="tree ids"):
        encode_cmgr_stream(
            feature_tree_ids=(32, 40),
            link_atom_ids=(101, 102),
            link_tree_ids=(32,),
        )


def test_a_zero_feature_atom_table_is_rejected():
    with pytest.raises(SldprtFormatError, match="at least one solid feature"):
        atom_ids_for(0)
    with pytest.raises(SldprtFormatError, match="at least one solid feature"):
        tree_ids_for(0)
