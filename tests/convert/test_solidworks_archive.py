# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import json
from pathlib import Path
import struct

import pytest

from convert.adapters.solidworks.archive import (
    BIG_CLASS_TAG_BIT,
    BIG_OBJECT_TAG,
    CLASS_REFERENCE_KIND,
    CLASS_TAG_BIT,
    DEFINITION_KIND,
    LayoutTable,
    Model,
    NULL_KIND,
    NULL_TAG,
    Node,
    OBJECT_REFERENCE_KIND,
    STREAM_HEADER_SIZE,
    SegmentationError,
    StaticSegment,
    ArchiveError,
    build_model,
    container_mo_version,
    encode_class_definition,
    encode_class_reference,
    encode_null,
    encode_object_reference,
    encode_string,
    implied_bases,
    read_string,
    read_tag,
    resolve_base,
    segment,
    verify,
)
from convert.adapters.solidworks.container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.format import RESOLVED_FEATURES_STREAM

ROOT = Path(__file__).parents[2]
LAYOUTS = ROOT / "re" / "data" / "class_layouts.json"
SEGMENTS = ROOT / "re" / "data" / "segments"
DONORS = ROOT / "tests" / "fixtures" / "solidworks" / "donors"
RECORDED_LABELS = (
    "baseline",
    "circle",
    "cutbase",
    "padplane",
    "planetop",
    "three",
    "twopad",
    "vendor_cojinete",
    "vendor_ring",
)
FIXTURES_VERIFYING_BYTE_IDENTICALLY = 0
CONFIRMED_CLASS_FLOOR = 50
FIXTURE_OBJECT_FLOOR = 7487
FIXTURE_BASE_SEED = 109


def _layouts() -> LayoutTable:
    return LayoutTable.load(LAYOUTS)


def _recorded(label: str) -> dict:
    path = SEGMENTS / f"segments_{label}.json"
    if not path.is_file():
        pytest.skip(f"no recorded segmentation for {label}")
    return json.loads(path.read_text(encoding="utf-8"))


def _recorded_part(payload: dict) -> tuple[bytes, int | None]:
    part = Path(payload["part"])
    if not part.is_file():
        pytest.skip(f"traced part {part} is not present in this checkout")
    archive = SldprtArchive.from_bytes(part.read_bytes())
    blob = archive.streams[RESOLVED_FEATURES_STREAM]
    assert len(blob) == payload["stream_length"]
    return blob, container_mo_version(archive.streams)


def _authored_mo_version() -> int | None:
    found: set[int] = set()
    for label in RECORDED_LABELS:
        if label.startswith("vendor_"):
            continue
        path = SEGMENTS / f"segments_{label}.json"
        if not path.is_file():
            continue
        part = Path(json.loads(path.read_text(encoding="utf-8"))["part"])
        if not part.is_file():
            continue
        version = container_mo_version(
            SldprtArchive.from_bytes(part.read_bytes()).streams
        )
        if version is not None:
            found.add(version)
    if len(found) != 1:
        return None
    return found.pop()


def _static_segments(blob: bytes, payload: dict) -> tuple[StaticSegment, ...]:
    rows = []
    for item in payload["segments"]:
        offset = item["offset"]
        schema = (
            struct.unpack_from("<H", blob, offset + 2)[0]
            if item["kind"] == DEFINITION_KIND
            else 0
        )
        rows.append(
            StaticSegment(
                index=item["index"],
                offset=offset,
                header=item["header"],
                end=item["end"],
                kind=item["kind"],
                token=item["tag"],
                wide=False,
                schema=schema,
                class_name=item["class_name"],
                class_index=item["class_index"],
                object_index=item["object_index"],
                depth=item["depth"],
                parent=item["parent"],
            )
        )
    return tuple(rows)


def _donor_streams() -> tuple[tuple[str, bytes], ...]:
    rows = []
    for donor in sorted(DONORS.iterdir()):
        stream = donor / "resolved.bin"
        if stream.is_file():
            rows.append((donor.name, stream.read_bytes()))
    return tuple(rows)


@pytest.mark.parametrize("label", RECORDED_LABELS)
def test_recorded_segmentation_round_trips_byte_identically(label: str) -> None:
    payload = _recorded(label)
    blob = _recorded_part(payload)[0]
    segments = _static_segments(blob, payload)
    model = build_model(blob, segments, payload["base_map_index"], segments[0].offset)
    assert len(model.nodes) == payload["object_count"]
    assert model.emit() == blob


@pytest.mark.parametrize("label", RECORDED_LABELS)
def test_static_segmentation_agrees_with_the_recorded_offsets(label: str) -> None:
    payload = _recorded(label)
    blob, version = _recorded_part(payload)
    layouts = _layouts()
    expected = [item["offset"] for item in payload["segments"]]
    header = payload["segments"][0]["offset"]
    try:
        produced = segment(
            blob,
            payload["base_map_index"],
            layouts,
            header_size=header,
            mo_version=version,
        )
        reached = [item.offset for item in produced]
    except SegmentationError as failure:
        reached = [item.offset for item in failure.reached]
        assert failure.offset in expected, (label, failure.offset)
    assert reached
    assert reached == expected[: len(reached)], label


@pytest.mark.parametrize("label", RECORDED_LABELS)
def test_recorded_segmentation_matches_the_counter_rule(label: str) -> None:
    payload = _recorded(label)
    base = payload["base_map_index"]
    counter = base
    for item in payload["segments"]:
        assert item["map_index"] == counter, (label, item["offset"])
        if item["kind"] == DEFINITION_KIND:
            counter += 2
        elif item["kind"] == CLASS_REFERENCE_KIND:
            counter += 1


def test_null_tag_round_trips() -> None:
    encoded = encode_null()
    assert encoded == b"\x00\x00"
    tag = read_tag(encoded, 0)
    assert tag.kind == NULL_KIND
    assert tag.size == 2
    assert tag.token == NULL_TAG


def test_class_definition_tag_round_trips() -> None:
    encoded = encode_class_definition("moExtrusion_c", 1)
    tag = read_tag(encoded, 0)
    assert tag.kind == DEFINITION_KIND
    assert tag.class_name == "moExtrusion_c"
    assert tag.schema == 1
    assert tag.size == len(encoded)
    assert encode_class_definition(tag.class_name, tag.schema) == encoded


def test_class_reference_tag_round_trips() -> None:
    encoded = encode_class_reference(109)
    assert struct.unpack_from("<H", encoded, 0)[0] == CLASS_TAG_BIT | 109
    tag = read_tag(encoded, 0)
    assert tag.kind == CLASS_REFERENCE_KIND
    assert tag.index == 109
    assert tag.wide is False
    assert encode_class_reference(tag.index, wide=tag.wide) == encoded


def test_object_reference_tag_round_trips() -> None:
    encoded = encode_object_reference(230)
    tag = read_tag(encoded, 0)
    assert tag.kind == OBJECT_REFERENCE_KIND
    assert tag.index == 230
    assert tag.wide is False
    assert encode_object_reference(tag.index, wide=tag.wide) == encoded


def test_big_object_tag_escape_round_trips() -> None:
    encoded = encode_object_reference(BIG_OBJECT_TAG)
    assert struct.unpack_from("<H", encoded, 0)[0] == BIG_OBJECT_TAG
    assert struct.unpack_from("<I", encoded, 2)[0] == BIG_OBJECT_TAG
    tag = read_tag(encoded, 0)
    assert tag.kind == OBJECT_REFERENCE_KIND
    assert tag.wide is True
    assert tag.index == BIG_OBJECT_TAG
    assert tag.size == 6
    assert encode_object_reference(tag.index, wide=True) == encoded


def test_big_class_tag_escape_round_trips() -> None:
    encoded = encode_class_reference(0x12345)
    assert struct.unpack_from("<I", encoded, 2)[0] == 0x12345 | BIG_CLASS_TAG_BIT
    tag = read_tag(encoded, 0)
    assert tag.kind == CLASS_REFERENCE_KIND
    assert tag.wide is True
    assert tag.index == 0x12345
    assert encode_class_reference(tag.index, wide=True) == encoded


def test_narrow_indices_may_be_forced_wide() -> None:
    encoded = encode_class_reference(7, wide=True)
    assert len(encoded) == 6
    tag = read_tag(encoded, 0)
    assert tag.index == 7
    assert tag.wide is True


def test_short_string_round_trips() -> None:
    encoded = encode_string("Boss-Extrude1")
    assert encoded[:3] == b"\xff\xfe\xff"
    assert encoded[3] == 13
    text, consumed = read_string(encoded, 0)
    assert text == "Boss-Extrude1"
    assert consumed == len(encoded)


def test_long_string_round_trips() -> None:
    text = "n" * 300
    encoded = encode_string(text)
    assert encoded[:4] == b"\xff\xfe\xff\xff"
    assert struct.unpack_from("<H", encoded, 4)[0] == 300
    decoded, consumed = read_string(encoded, 0)
    assert decoded == text
    assert consumed == len(encoded)


def test_empty_string_round_trips() -> None:
    encoded = encode_string("")
    assert encoded == b"\xff\xfe\xff\x00"
    assert read_string(encoded, 0) == ("", 4)


def test_unrepresentable_values_raise_instead_of_truncating() -> None:
    with pytest.raises(ArchiveError):
        encode_string("n" * 0xFFFE)
    with pytest.raises(ArchiveError):
        encode_class_definition("cl\u00e4ss", 1)
    with pytest.raises(ArchiveError):
        encode_class_definition("", 1)
    with pytest.raises(ArchiveError):
        encode_object_reference(-1)
    with pytest.raises(ArchiveError):
        encode_class_reference(0x40000000)
    with pytest.raises(ArchiveError):
        read_tag(b"\xff\xff\x01", 0)
    with pytest.raises(ArchiveError):
        read_string(b"\x01\x02\x03\x04", 0)
    assert issubclass(ArchiveError, SldprtFormatError)


def test_counter_rule_assigns_indices_from_the_base() -> None:
    model = Model(header=b"\x00" * STREAM_HEADER_SIZE, base=109)
    model.nodes.append(
        Node(kind=DEFINITION_KIND, body=b"\x01\x00\x00\x00", class_name="alpha")
    )
    model.nodes.append(Node(kind=NULL_KIND, body=b""))
    model.nodes.append(
        Node(kind=DEFINITION_KIND, body=b"\x02\x00\x00\x00", class_name="beta")
    )
    model.nodes.append(Node(kind=CLASS_REFERENCE_KIND, body=b"", target=0))
    model.nodes.append(Node(kind=OBJECT_REFERENCE_KIND, body=b"", target=2))
    model.assign()
    assert [node.class_index for node in model.nodes] == [109, 0, 111, 0, 0]
    assert [node.object_index for node in model.nodes] == [110, 0, 112, 113, 0]
    emitted = model.emit()
    expected = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("alpha", 0)
        + b"\x01\x00\x00\x00"
        + encode_null()
        + encode_class_definition("beta", 0)
        + b"\x02\x00\x00\x00"
        + encode_class_reference(109)
        + encode_object_reference(112)
    )
    assert emitted == expected


def test_below_base_tokens_survive_as_literals() -> None:
    model = Model(header=b"", base=109)
    model.nodes.append(Node(kind=CLASS_REFERENCE_KIND, body=b"", literal=4))
    model.nodes.append(Node(kind=OBJECT_REFERENCE_KIND, body=b"", literal=2))
    emitted = model.emit()
    assert emitted == encode_class_reference(4) + encode_object_reference(2)
    assert model.nodes[0].object_index == 109


def test_model_rejects_an_unknown_node_kind() -> None:
    model = Model(header=b"", base=1)
    model.nodes.append(Node(kind="bogus", body=b""))
    with pytest.raises(ArchiveError):
        model.emit()


def _single_class_table(entry: dict) -> LayoutTable:
    return LayoutTable.from_mapping({"version": 1, "classes": {"solo": entry}})


def test_segment_refuses_an_opaque_leaf_run() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [
                {"slot": "leaf", "rule": "opaque", "note": "needs a trace"}
            ],
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1) + b"\x00" * 8
    )
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert failure.value.class_name == "solo"
    assert failure.value.slot == "leaf"
    assert failure.value.offset == STREAM_HEADER_SIZE
    assert "opaque" in str(failure.value)


def test_segment_refuses_a_varying_child_count() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": ["*", "..."],
            "runs": {"lead": 0},
            "variable_runs": [
                {
                    "slot": "lead",
                    "rule": "opaque",
                    "note": "child count varies across instances",
                }
            ],
        }
    )
    blob = b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1)
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert failure.value.class_name == "solo"
    assert "child count" in str(failure.value)


def test_segment_refuses_a_class_without_a_layout_entry() -> None:
    layouts = LayoutTable.from_mapping({"version": 1, "classes": {}})
    blob = b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1)
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert failure.value.class_name == "solo"
    assert "no layout entry" in str(failure.value)


def test_segment_refuses_a_run_past_the_end_of_the_stream() -> None:
    layouts = _single_class_table(
        {"confidence": "confirmed", "child_slots": [], "runs": {"leaf": 64}}
    )
    blob = b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1)
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert "past" in str(failure.value)


def test_segment_refuses_an_unresolved_reference_at_or_above_the_base() -> None:
    layouts = _single_class_table(
        {"confidence": "confirmed", "child_slots": [], "runs": {"leaf": 0}}
    )
    blob = b"\x00" * STREAM_HEADER_SIZE + encode_class_reference(120)
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert "no definition has been seen" in str(failure.value)


def test_a_below_base_class_index_binds_from_the_declared_slot() -> None:
    layouts = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "parent": {
                    "confidence": "confirmed",
                    "child_slots": ["owned"],
                    "runs": {"lead": 0, "0": 0},
                },
                "owned": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 3},
                },
            },
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("parent", 1)
        + encode_class_reference(42)
        + bytes(range(3))
    )
    segments = segment(blob, 109, layouts)
    assert [item.class_name for item in segments] == ["parent", "owned"]
    assert segments[1].class_index == 42
    assert segments[1].end == len(blob)
    assert verify(blob, 109, layouts).identical


def test_a_below_base_class_index_keeps_its_alias_when_the_table_names_it() -> None:
    layouts = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "parent": {
                    "confidence": "confirmed",
                    "child_slots": ["owned"],
                    "runs": {"lead": 0, "0": 0},
                },
                "owned": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 9},
                },
                "external#42": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 3},
                },
            },
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("parent", 1)
        + encode_class_reference(42)
        + bytes(range(3))
    )
    segments = segment(blob, 109, layouts)
    assert [item.class_name for item in segments] == ["parent", "external#42"]


def test_a_polymorphic_slot_leaves_a_below_base_index_unbound() -> None:
    layouts = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "parent": {
                    "confidence": "confirmed",
                    "child_slots": ["*"],
                    "runs": {"lead": 0, "0": 0},
                },
            },
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("parent", 1)
        + encode_class_reference(42)
    )
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert failure.value.class_name == "external#42"
    assert "no layout entry" in str(failure.value)


def _base_refinement_table() -> LayoutTable:
    return LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "first": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 0},
                },
                "second": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 0},
                },
            },
        }
    )


def test_resolve_base_refines_from_an_unresolved_class_reference() -> None:
    layouts = _base_refinement_table()
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("first", 1)
        + encode_class_definition("second", 1)
        + encode_class_reference(203)
        + encode_class_reference(201)
    )
    resolution = resolve_base(blob, 109, layouts)
    assert resolution.base == 201
    assert resolution.segmented
    assert resolution.seed == 109
    assert 201 in resolution.implied
    assert resolution.tried[0] == 109
    assert verify(blob, resolution.base, layouts).identical


def test_resolve_base_keeps_a_seed_that_already_segments() -> None:
    layouts = _base_refinement_table()
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("first", 1)
        + encode_class_reference(109)
    )
    resolution = resolve_base(blob, 109, layouts)
    assert resolution.base == 109
    assert resolution.tried == (109,)
    assert resolution.implied == ()
    assert resolution.segmented


def test_resolve_base_rejects_an_unusable_seed_or_limit() -> None:
    layouts = _base_refinement_table()
    blob = b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("first", 1)
    with pytest.raises(ArchiveError):
        resolve_base(blob, 0, layouts)
    with pytest.raises(ArchiveError):
        resolve_base(blob, 109, layouts, limit=0)


def test_implied_bases_ignores_an_unresolved_object_reference() -> None:
    layouts = _base_refinement_table()
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("first", 1)
        + encode_object_reference(18000)
    )
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert failure.value.unresolved_index == 18000
    assert failure.value.unresolved_kind == OBJECT_REFERENCE_KIND
    assert implied_bases(failure.value, 109) == ()


def test_segment_tiles_and_re_emits_a_synthetic_stream() -> None:
    layouts = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "parent": {
                    "confidence": "confirmed",
                    "child_slots": ["child", "*"],
                    "runs": {"lead": 4, "0": 2, "1": 6},
                },
                "child": {
                    "confidence": "confirmed",
                    "child_slots": [],
                    "runs": {"leaf": 8},
                },
            },
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("parent", 1)
        + bytes(range(4))
        + encode_class_definition("child", 1)
        + bytes(range(8))
        + bytes(range(2))
        + encode_null()
        + bytes(range(6))
    )
    segments = segment(blob, 109, layouts)
    assert [item.class_name for item in segments] == ["parent", "child", "null"]
    assert [item.depth for item in segments] == [0, 1, 1]
    assert [item.parent for item in segments] == [-1, 0, 0]
    report = verify(blob, 109, layouts)
    assert report.segmented
    assert report.tiled
    assert report.identical
    assert report.object_count == 3
    assert report.definition_count == 2
    assert report.gaps == ()
    assert report.overlaps == ()
    assert report.trailing_bytes == 0


def test_string_and_count_and_conditional_rules_measure_a_run() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [
                {
                    "slot": "leaf",
                    "rule": "count",
                    "at": 2,
                    "count_width": 2,
                    "stride": 4,
                },
                {"slot": "leaf", "rule": "string", "at": 1, "tail": 0},
                {
                    "slot": "leaf",
                    "rule": "conditional",
                    "at": 4,
                    "width": 8,
                    "predicate": "flag",
                    "predicate_at": 0,
                    "predicate_width": 1,
                    "values": [1],
                    "tail": 3,
                },
            ],
        }
    )
    body = (
        b"\x00\x00"
        + struct.pack("<H", 3)
        + b"\x00" * 12
        + b"\x00"
        + encode_string("ab")
        + b"\x01\x00\x00\x00"
        + b"\x00" * 8
        + b"\x00" * 3
    )
    blob = b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1) + body
    segments = segment(blob, 109, layouts)
    assert len(segments) == 1
    assert segments[0].end == len(blob)
    assert verify(blob, 109, layouts).identical


def test_conditional_rule_omits_an_absent_element() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [
                {
                    "slot": "leaf",
                    "rule": "conditional",
                    "at": 1,
                    "width": 16,
                    "predicate": "flag",
                    "predicate_at": 0,
                    "predicate_width": 1,
                    "values": [1],
                    "tail": 2,
                }
            ],
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("solo", 1)
        + b"\x00"
        + b"\x00\x00"
    )
    segments = segment(blob, 109, layouts)
    assert segments[0].end == len(blob)


def test_unresolved_repeat_count_is_refused() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": ["*"],
            "runs": {"lead": 0, "0": 0},
            "repeat_count": "unresolved",
        }
    )
    blob = b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1)
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert "child count" in str(failure.value)


def _prefix_table(prefix: int, tail: dict | None = None) -> LayoutTable:
    entry: dict = {
        "confidence": "partial",
        "child_slots": ["*", "*", "..."],
        "runs": {"lead": 4, "0": 2, "1": 6},
        "repeat_count": None,
        "repeat_prefix": prefix,
    }
    if tail is not None:
        entry["variable_runs"] = [tail]
    return LayoutTable.from_mapping({"version": 1, "classes": {"solo": entry}})


def _prefix_stream() -> bytes:
    return (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("solo", 1)
        + bytes(range(4))
        + encode_null()
        + bytes(range(2))
        + encode_null()
        + bytes(range(6))
        + encode_null()
    )


def test_a_repeat_prefix_walks_the_known_children_and_refuses_the_tail() -> None:
    layouts = _prefix_table(
        2, {"slot": "tail", "rule": "opaque", "note": "the child count is not pinned"}
    )
    layout = layouts["solo"]
    assert layout.walks_a_prefix
    assert not layout.repeats
    assert layout.run_keys() == ("lead", "0", "tail")
    assert layout.run_key(0) == "0"
    assert layout.run_key(1) == "tail"
    with pytest.raises(SegmentationError) as failure:
        segment(_prefix_stream(), 109, layouts)
    assert failure.value.class_name == "solo"
    assert failure.value.slot == "tail"
    assert failure.value.offset == STREAM_HEADER_SIZE
    assert "not pinned" in str(failure.value)
    assert [item.kind for item in failure.value.reached] == [
        DEFINITION_KIND,
        NULL_KIND,
        NULL_KIND,
    ]
    assert [item.offset for item in failure.value.reached[1:]] == [
        STREAM_HEADER_SIZE + 10 + 4,
        STREAM_HEADER_SIZE + 10 + 4 + 2 + 2,
    ]


def test_a_prefix_of_one_refuses_before_the_second_child() -> None:
    layouts = _prefix_table(1)
    with pytest.raises(SegmentationError) as failure:
        segment(_prefix_stream(), 109, layouts)
    assert failure.value.slot == "tail"
    assert len(failure.value.reached) == 2


def test_a_class_with_no_prefix_is_still_refused_at_its_lead() -> None:
    layouts = _prefix_table(0)
    with pytest.raises(SegmentationError) as failure:
        segment(_prefix_stream(), 109, layouts)
    assert failure.value.slot == "lead"
    assert "child count" in str(failure.value)


def test_repeat_prefix_is_validated() -> None:
    with pytest.raises(ArchiveError):
        _prefix_table(-1)
    with pytest.raises(ArchiveError):
        _prefix_table(4)
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {
                "version": 1,
                "classes": {
                    "solo": {
                        "confidence": "confirmed",
                        "child_slots": ["*"],
                        "runs": {"lead": 0, "0": 0},
                        "repeat_prefix": 1,
                    }
                },
            }
        )


def test_a_repeat_count_of_zero_reads_no_children() -> None:
    layouts = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "list": {
                    "confidence": "confirmed",
                    "child_slots": ["*", "..."],
                    "runs": {"lead": 2, "0": 0},
                    "repeat_count": {"run": "lead", "at": 0, "width": 2},
                },
            },
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("list", 1)
        + struct.pack("<H", 0)
        + encode_class_definition("list", 1)
        + struct.pack("<H", 1)
        + encode_null()
    )
    segments = segment(blob, 109, layouts)
    assert [item.depth for item in segments] == [0, 0, 1]
    assert segments[0].end == segments[1].offset
    assert verify(blob, 109, layouts).identical


def test_the_shipped_table_drives_sgSketch_from_run_groups() -> None:
    layout = _layouts()["sgSketch"]
    assert layout.walks_groups
    assert layout.child_slots == ()
    assert layout.repeat_count is None
    assert layout.repeat_prefix == 0
    assert not layout.repeats
    assert not layout.walks_a_prefix
    assert layout.run_keys() == ("lead",)
    assert layout.constant_run("lead", 18000) == 49
    assert not layout.variable_runs
    assert [group.name for group in layout.groups] == [
        "entity",
        "point",
        "relation",
        "constraint",
        "lists",
        "chain",
    ]
    shape = {group.name: group for group in layout.groups}
    assert shape["entity"].element == (8, 39, 0, 87)
    assert (shape["entity"].count_back, shape["entity"].count_width) == (49, 2)
    assert shape["entity"].trailer == 4
    assert shape["point"].element == (8, 80)
    assert (shape["point"].count_back, shape["point"].count_width) == (12, 2)
    assert shape["point"].trailer == 13
    assert shape["relation"].element_runs(18000) == (0, 16, 17, 4)
    assert shape["relation"].element_runs(14000) == (0, 16, 16, 4)
    assert shape["relation"].trailer == 2
    assert shape["constraint"].element == (0, 16, 17, 0, 4, 26, 0, 0, 6)
    assert shape["constraint"].trailer == 8
    assert shape["lists"].repeat == 1
    assert shape["lists"].element == (170, 38)
    assert shape["lists"].slots == ("suObList", "suObList")
    assert shape["chain"].element == (0,)
    assert shape["chain"].slots == ("moSketchChain_c",)
    assert (shape["chain"].count_back, shape["chain"].count_width) == (4, 2)
    assert shape["chain"].trailer == 21
    for group in layout.groups:
        assert group.note
        assert len(group.slots) == len(group.element)


def test_run_groups_are_validated() -> None:
    def table(group: dict) -> LayoutTable:
        return LayoutTable.from_mapping(
            {
                "version": 1,
                "classes": {
                    "solo": {
                        "confidence": "partial",
                        "child_slots": [],
                        "runs": {"lead": 0},
                        "groups": [group],
                    }
                },
            }
        )

    sound = {
        "name": "loop",
        "count": {"back": 2, "width": 2},
        "slots": ["*"],
        "element": [0],
    }
    assert table(sound)["solo"].walks_groups
    with pytest.raises(ArchiveError):
        table({**sound, "name": ""})
    with pytest.raises(ArchiveError):
        table({**sound, "element": []})
    with pytest.raises(ArchiveError):
        table({**sound, "element": [-1]})
    with pytest.raises(ArchiveError):
        table({**sound, "slots": ["*", "*"]})
    with pytest.raises(ArchiveError):
        table({**sound, "trailer": -1})
    with pytest.raises(ArchiveError):
        table({**sound, "count": {"back": 1, "width": 2}})
    with pytest.raises(ArchiveError):
        table({**sound, "count": {"back": 2, "width": 3}})
    with pytest.raises(ArchiveError):
        table({"name": "loop", "slots": ["*"], "element": [0]})
    with pytest.raises(ArchiveError):
        table({**sound, "repeat": 1})
    with pytest.raises(ArchiveError):
        table({"name": "loop", "repeat": 0, "slots": ["*"], "element": [0]})
    with pytest.raises(ArchiveError):
        table({**sound, "element_by_version": {"nope": [0]}})
    with pytest.raises(ArchiveError):
        table({**sound, "element_by_version": {"18000": [0, 0]}})
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {
                "version": 1,
                "classes": {
                    "solo": {
                        "confidence": "partial",
                        "child_slots": ["*"],
                        "runs": {"lead": 0, "0": 0},
                        "groups": [sound],
                    }
                },
            }
        )
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {
                "version": 1,
                "classes": {
                    "solo": {
                        "confidence": "partial",
                        "child_slots": [],
                        "runs": {},
                        "groups": [sound],
                    }
                },
            }
        )


def test_a_run_group_walks_its_count_element_and_trailer() -> None:
    layouts = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "solo": {
                    "confidence": "partial",
                    "child_slots": [],
                    "runs": {"lead": 2},
                    "groups": [
                        {
                            "name": "pairs",
                            "count": {"back": 2, "width": 2},
                            "slots": ["*", "*"],
                            "element": [1, 3],
                            "trailer": 5,
                        },
                        {
                            "name": "singles",
                            "count": {"back": 5, "width": 1},
                            "slots": ["*"],
                            "element": [0],
                            "trailer": 0,
                        },
                    ],
                }
            },
        }
    )
    body = (
        struct.pack("<H", 2)
        + encode_null()
        + b"\x00"
        + encode_null()
        + b"\x00" * 3
        + encode_null()
        + b"\x00"
        + encode_null()
        + b"\x00" * 3
        + b"\x01\x00\x00\x00\x00"
        + encode_null()
    )
    blob = b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1) + body
    segments = segment(blob, 109, layouts)
    assert [item.depth for item in segments] == [0, 1, 1, 1, 1, 1]
    assert segments[-1].end == len(blob)
    assert verify(blob, 109, layouts).identical


def test_a_run_group_whose_counts_are_all_zero_reads_no_children() -> None:
    layouts = LayoutTable.from_mapping(
        {
            "version": 1,
            "classes": {
                "solo": {
                    "confidence": "partial",
                    "child_slots": [],
                    "runs": {"lead": 2},
                    "groups": [
                        {
                            "name": "loop",
                            "count": {"back": 2, "width": 2},
                            "slots": ["*"],
                            "element": [0],
                            "trailer": 3,
                        }
                    ],
                }
            },
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("solo", 1)
        + struct.pack("<H", 0)
        + b"\x00" * 3
    )
    segments = segment(blob, 109, layouts)
    assert len(segments) == 1
    assert segments[0].end == len(blob)
    assert verify(blob, 109, layouts).identical


def test_a_count_rule_without_a_width_is_refused() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [{"slot": "leaf", "rule": "count", "at": 0}],
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1) + b"\x00" * 4
    )
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert "count width" in str(failure.value)


def test_a_conditional_rule_without_a_predicate_is_refused() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "variable_runs": [{"slot": "leaf", "rule": "conditional", "at": 0}],
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1) + b"\x00" * 4
    )
    with pytest.raises(SegmentationError) as failure:
        segment(blob, 109, layouts)
    assert "predicate" in str(failure.value)


def test_container_mo_version_reads_the_storage_name() -> None:
    names = (
        "Contents/Config-0-ResolvedFeatures",
        "_DL_VERSION_11000/DLUpdateStamp",
        "_MO_VERSION_14000/Biography",
        "_MO_VERSION_14000/History",
    )
    assert container_mo_version(names) == 14000
    assert container_mo_version(("_MO_VERSION_18000\\History",)) == 18000
    assert container_mo_version(("_MO_VERSION_18000",)) == 18000
    assert container_mo_version(("_MO_VERSION_14000/H", "_MO_VERSION_18000/H")) == 18000
    assert container_mo_version(("Contents/Definition", "Header2")) is None
    assert container_mo_version(("_MO_VERSION_beta/History",)) is None
    assert container_mo_version(()) is None


@pytest.mark.parametrize("label", RECORDED_LABELS)
def test_recorded_parts_carry_a_readable_document_version(label: str) -> None:
    payload = _recorded(label)
    version = _recorded_part(payload)[1]
    assert version == (14000 if label.startswith("vendor_") else 18000), label


def test_a_version_gated_run_is_taken_for_a_version_it_names() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "runs_by_version": {"leaf": {"18000": 8, "14000": 4}},
        }
    )
    entry = layouts["solo"]
    assert entry.constant_run("leaf", 18000) == 8
    assert entry.constant_run("leaf", 14000) == 4
    assert entry.constant_run_keys == frozenset({"leaf"})
    head = b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1)
    wide = segment(head + b"\x00" * 8, 109, layouts, mo_version=18000)
    assert wide[0].end == len(head) + 8
    narrow = segment(head + b"\x00" * 4, 109, layouts, mo_version=14000)
    assert narrow[0].end == len(head) + 4


def test_a_version_the_gate_omits_falls_back_to_the_plain_run() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": ["*"],
            "runs": {"lead": 2, "0": 6},
            "runs_by_version": {"0": {"18000": 10}},
        }
    )
    entry = layouts["solo"]
    assert entry.constant_run("0", 18000) == 10
    assert entry.constant_run("0", 14000) == 6
    assert entry.constant_run("0", None) == 6
    assert entry.constant_run("lead", 18000) == 2
    assert entry.constant_run("missing", 18000) is None
    blob = (
        b"\x00" * STREAM_HEADER_SIZE
        + encode_class_definition("solo", 1)
        + b"\x00" * 2
        + encode_null()
        + b"\x00" * 6
    )
    assert segment(blob, 109, layouts, mo_version=14000)[-1].end == len(blob)
    assert segment(blob, 109, layouts)[-1].end == len(blob)


def test_a_version_gated_run_without_a_fallback_is_refused() -> None:
    layouts = _single_class_table(
        {
            "confidence": "partial",
            "child_slots": [],
            "runs": {},
            "runs_by_version": {"leaf": {"18000": 4}},
        }
    )
    blob = (
        b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1) + b"\x00" * 4
    )
    assert segment(blob, 109, layouts, mo_version=18000)[0].end == len(blob)
    with pytest.raises(SegmentationError) as missed:
        segment(blob, 109, layouts, mo_version=14000)
    assert missed.value.class_name == "solo"
    assert missed.value.slot == "leaf"
    assert "document version 14000" in str(missed.value)
    with pytest.raises(SegmentationError) as unknown:
        segment(blob, 109, layouts)
    assert "no document version was supplied" in str(unknown.value)


def test_segment_rejects_a_negative_document_version() -> None:
    layouts = _single_class_table(
        {"confidence": "confirmed", "child_slots": [], "runs": {"leaf": 0}}
    )
    blob = b"\x00" * STREAM_HEADER_SIZE + encode_class_definition("solo", 1)
    with pytest.raises(ArchiveError):
        segment(blob, 109, layouts, mo_version=-1)


def test_runs_by_version_is_validated() -> None:
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"runs_by_version": []}}}
        )
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"runs_by_version": {"leaf": 4}}}}
        )
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"runs_by_version": {"leaf": {}}}}}
        )
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {
                "version": 1,
                "classes": {"solo": {"runs_by_version": {"leaf": {"v8": 4}}}},
            }
        )
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {
                "version": 1,
                "classes": {"solo": {"runs_by_version": {"leaf": {"18000": -1}}}},
            }
        )


def test_the_shipped_table_gates_moCompFeature_c_on_the_document_version() -> None:
    entry = _layouts()["moCompFeature_c"]
    assert entry.child_slots == ("moUnitComponent_c",)
    assert entry.runs == {"lead": 0}
    assert entry.runs_by_version == {"0": {18000: 89, 14000: 85, 13000: 85}}
    assert entry.constant_run("0", 18000) == 89
    assert entry.constant_run("0", 14000) == 85
    assert entry.constant_run("0", 13000) == 85
    assert entry.constant_run("0", None) is None
    assert not entry.variable_runs


def test_layout_table_validates_its_input() -> None:
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping({"version": 1})
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping({"version": 1, "classes": {"solo": 3}})
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"child_slots": "abc"}}}
        )
    with pytest.raises(ArchiveError):
        LayoutTable.from_mapping(
            {"version": 1, "classes": {"solo": {"runs": {"leaf": -1}}}}
        )
    with pytest.raises(ArchiveError):
        LayoutTable.load(ROOT / "re" / "data" / "class_layouts_missing.json")


def test_shipped_layout_table_matches_the_recorded_classes() -> None:
    layouts = _layouts()
    assert layouts.version == 1
    confirmed = [
        name
        for name, entry in layouts.classes.items()
        if entry.confidence == "confirmed"
    ]
    assert len(confirmed) >= CONFIRMED_CLASS_FLOOR
    for name, entry in layouts.classes.items():
        assert entry.confidence in {"confirmed", "partial", "not found"}
        assert entry.source
        assert set(entry.runs_by_version) <= set(entry.run_keys()), name
        for key, gated in entry.runs_by_version.items():
            assert gated, (name, key)
            for version, length in gated.items():
                assert version > 0, (name, key)
                assert length >= 0, (name, key)
        if entry.confidence == "confirmed":
            assert not entry.repeats
            for key in entry.run_keys():
                elements = entry.variable_runs.get(key, ())
                assert key in entry.constant_run_keys or elements, (name, key)
                assert all(element.rule != "opaque" for element in elements), (
                    name,
                    key,
                )
        for slot, elements in entry.variable_runs.items():
            assert elements
            assert slot in set(entry.run_keys()) | {"lead"}
            for element in elements:
                assert element.rule in {"string", "count", "conditional", "opaque"}
    recorded = set()
    for label in RECORDED_LABELS:
        path = SEGMENTS / f"segments_{label}.json"
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item in payload["segments"]:
            if item["kind"] in {DEFINITION_KIND, CLASS_REFERENCE_KIND}:
                recorded.add(item["class_name"])
    assert recorded <= set(layouts.classes)


def test_fixture_verification_count_does_not_regress() -> None:
    layouts = _layouts()
    streams = _donor_streams()
    assert len(streams) == 32
    version = _authored_mo_version()
    identical = 0
    for _, blob in streams:
        report = verify(
            blob,
            109,
            layouts,
            header_size=STREAM_HEADER_SIZE,
            mo_version=version,
        )
        if report.identical:
            identical += 1
    assert identical >= FIXTURES_VERIFYING_BYTE_IDENTICALLY


def _donor_feature_count(name: str) -> int:
    meta = DONORS / name / "meta.json"
    if not meta.is_file():
        return -1
    features = json.loads(meta.read_text(encoding="utf-8")).get("features")
    return len(features) if isinstance(features, list) else -1


def test_fixture_object_reach_does_not_regress() -> None:
    layouts = _layouts()
    version = _authored_mo_version()
    reached = 0
    for name, blob in _donor_streams():
        features = _donor_feature_count(name)
        seed = FIXTURE_BASE_SEED + features - 1 if features > 0 else FIXTURE_BASE_SEED
        resolution = resolve_base(
            blob,
            seed,
            layouts,
            header_size=STREAM_HEADER_SIZE,
            mo_version=version,
        )
        report = verify(
            blob,
            resolution.base,
            layouts,
            header_size=STREAM_HEADER_SIZE,
            mo_version=version,
        )
        assert report.object_count > 0, name
        reached += report.object_count
    assert reached >= FIXTURE_OBJECT_FLOOR


def test_resolved_external_classes_carry_measured_runs() -> None:
    layouts = _layouts()
    resolved = {
        name: entry
        for name, entry in layouts.classes.items()
        if entry.source == "re/data/external_classes.json"
    }
    assert resolved
    for name, entry in resolved.items():
        assert not entry.repeats, name
        for key in entry.run_keys():
            elements = entry.variable_runs.get(key, ())
            assert key in entry.constant_run_keys or elements, (name, key)
            for element in elements:
                assert element.rule != "opaque", (name, key)
    aliases = {name for name in resolved if name.startswith("external#")}
    assert aliases
    for alias in aliases:
        assert layouts.classes[alias].child_slots == resolved[alias].child_slots


def test_fixture_segmentation_failures_name_the_blocking_class() -> None:
    layouts = _layouts()
    version = _authored_mo_version()
    for name, blob in _donor_streams():
        report = verify(
            blob,
            109,
            layouts,
            header_size=STREAM_HEADER_SIZE,
            mo_version=version,
        )
        if report.identical:
            continue
        assert report.blocking_class, name
        assert report.blocking_slot, name
        assert report.blocking_offset >= STREAM_HEADER_SIZE, name
        assert (
            report.blocking_class in layouts.classes
            or report.blocking_class.startswith("external#")
            or report.blocking_class == "<stream>"
        ), name
