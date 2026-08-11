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
import struct

import pytest

from convert.adapters.solidworks.config0 import (
    CONFIG_FIELD_COUNT,
    CONFIG_OPAQUE_BYTES,
    CONFIG_OWNER_COUNT,
    FILLET_ANNOTATION_BYTES,
    FILLET_ATOM_LINK_STAMP,
    FILLET_ATOM_LINK_STAMP_RELATIVES,
    FILLET_ATOM_PARENT_RELATIVE,
    MO_VERSION,
    PATTERN_ANNOTATION_BYTES,
    PER_FEATURE_ATOM_BYTES,
    REFERENCE_ATOM_ID,
    REFERENCE_LENGTH,
    REFERENCE_SHA256,
    REFERENCE_TREE_ID,
    SINGLE_LENGTH_UNIT_LENGTH,
    TWO_VIEW_ANNOTATION_BYTES,
    declared_opaque_split,
    encode_config0_stream,
)
from convert.adapters.solidworks.archive import encode_class_definition
from convert.adapters.solidworks.config0_program import (
    ConfigOps,
    FieldOwners,
    ReferenceLength,
    ShiftMapReference,
)
from convert.adapters.solidworks.config0_box_program import (
    ConfigOps as BoxConfigOps,
    EncodeProgram as EncodeBoxConfigProgram,
    FieldOwners as BoxFieldOwners,
    ReferenceLength as BoxReferenceLength,
)
from convert.adapters.solidworks.config0_two_view_program import (
    AnnotationOps,
    FieldOwners as AnnotationFieldOwners,
    ReferenceLength as AnnotationReferenceLength,
)
from convert.adapters.solidworks.config0_fillet_views_program import (
    AnnotationOps as FilletAnnotationOps,
    FieldOwners as FilletFieldOwners,
    ReferenceLength as FilletReferenceLength,
)
from convert.adapters.solidworks.config0_pattern_views_program import (
    AnnotationOps as PatternAnnotationOps,
    FieldOwners as PatternFieldOwners,
    ReferenceLength as PatternReferenceLength,
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


# dimensioned boxes use a closed fixed topology configuration field program
def test_DimensionedBoxConfigurationIsEntirelyTyped() -> None:
    SourceCursor = 0
    for StartPos, FieldWidth, OwnerIndex, KindName, _FieldValue in BoxConfigOps:
        assert StartPos == SourceCursor
        assert FieldWidth > 0
        assert 0 <= OwnerIndex < len(BoxFieldOwners)
        assert "opaque" not in KindName.casefold()
        assert "raw" not in KindName.casefold()
        SourceCursor += FieldWidth
    assert SourceCursor == BoxReferenceLength == 25158
    assert len(EncodeBoxConfigProgram()) == BoxReferenceLength
    ProgramPath = (
        Path(__file__).parents[2]
        / "src/convert/adapters/solidworks/config0_box_program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# the two-view variant remains a field program rather than an embedded vendor record
def test_two_view_runtime_program_contains_no_encoded_vendor_blocks() -> None:
    ProgramPath = (
        Path(__file__).parents[2]
        / "src/convert/adapters/solidworks/config0_two_view_program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# a revolved-cut configuration couples a count of two to two typed annotation views
def test_two_view_annotation_manager_is_typed_and_counted() -> None:
    SingleData = encode_config0_stream(annotation_view_count=1)
    DoubleData = encode_config0_stream(annotation_view_count=2)
    AnnotationTag = encode_class_definition("moAnnotationView_c", 1)
    AnnotationStart = DoubleData.index(AnnotationTag)
    assert struct.unpack_from("<H", DoubleData, AnnotationStart - 2)[0] == 2
    assert len(DoubleData) - len(SingleData) == TWO_VIEW_ANNOTATION_BYTES == 260
    assert DoubleData.count(AnnotationTag) == 1
    assert "*Top".encode("utf-16-le") in DoubleData
    assert "*Right".encode("utf-16-le") in DoubleData
    assert AnnotationReferenceLength == 584
    assert len(AnnotationOps) == 113
    assert len(AnnotationFieldOwners) == 45


# terminal fillets need their predecessor atom and distinct two view manager together
def test_terminal_fillet_configuration_is_typed_and_linked() -> None:
    StreamData = encode_config0_stream(
        part_name="Part1",
        atoms=((101, 34),),
        high_water=(101, 103),
        annotation_view_count=2,
        terminal_parent_tree_id=32,
    )
    AtomTag = encode_class_definition("moAtom_c", 1)
    AtomStart = StreamData.index(AtomTag)
    assert len(StreamData) == 25470
    assert struct.unpack_from(
        "<I", StreamData, AtomStart + FILLET_ATOM_PARENT_RELATIVE
    ) == (32,)
    assert all(
        struct.unpack_from("<I", StreamData, AtomStart + RelativeOffset)[0]
        == FILLET_ATOM_LINK_STAMP
        for RelativeOffset in FILLET_ATOM_LINK_STAMP_RELATIVES
    )
    assert FILLET_ANNOTATION_BYTES == 258
    assert FilletReferenceLength == 582
    assert len(FilletAnnotationOps) == 113
    assert len(FilletFieldOwners) == 45


# generated fillet views must remain field programs instead of hidden stream captures
def test_fillet_view_program_contains_no_encoded_vendor_blocks() -> None:
    ProgramPath = (
        Path(__file__).parents[2]
        / "src/convert/adapters/solidworks/config0_fillet_views_program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# linear patterns use their recovered two-view manager without opaque bytes
def test_linear_pattern_annotation_manager_is_typed_and_counted() -> None:
    SingleData = encode_config0_stream(
        part_name="Part1",
        atoms=((102, 40), (101, 32)),
        high_water=(102, 105),
    )
    PatternData = encode_config0_stream(
        part_name="Part1",
        atoms=((102, 40), (101, 32)),
        high_water=(102, 105),
        annotation_view_count=2,
        annotation_view_variant="linear_pattern",
    )
    AnnotationTag = encode_class_definition("moAnnotationView_c", 1)
    AnnotationStart = PatternData.index(AnnotationTag)
    assert struct.unpack_from("<H", PatternData, AnnotationStart - 2)[0] == 2
    assert len(PatternData) == 25488
    assert len(PatternData) - len(SingleData) == PATTERN_ANNOTATION_BYTES == 188
    assert PatternReferenceLength == 512
    assert len(PatternAnnotationOps) == 104
    assert len(PatternFieldOwners) == 45


# circular patterns share the byte-identical recovered native pattern view manager
def test_circular_pattern_annotation_manager_matches_native_pattern_manager() -> None:
    LinearData = encode_config0_stream(
        part_name="Part1",
        atoms=((102, 40), (101, 32)),
        high_water=(102, 105),
        annotation_view_count=2,
        annotation_view_variant="linear_pattern",
    )
    CircularData = encode_config0_stream(
        part_name="Part1",
        atoms=((102, 46), (101, 32)),
        high_water=(102, 105),
        annotation_view_count=2,
        annotation_view_variant="circular_pattern",
    )
    ExpectedData = encode_config0_stream(
        part_name="Part1",
        atoms=((102, 46), (101, 32)),
        high_water=(102, 105),
        annotation_view_count=2,
        annotation_view_variant="linear_pattern",
    )
    assert CircularData == ExpectedData
    assert len(CircularData) == len(LinearData)


# generated pattern views must remain typed programs instead of hidden stream captures
def test_pattern_view_program_contains_no_encoded_vendor_blocks() -> None:
    ProgramPath = (
        Path(__file__).parents[2]
        / "src/convert/adapters/solidworks/config0_pattern_views_program.py"
    )
    SourceText = ProgramPath.read_text(encoding="utf-8")
    assert "bytes.fromhex" not in SourceText
    assert "base64" not in SourceText
    assert "b85decode" not in SourceText
    assert "opaque" not in SourceText.casefold()


# unsupported annotation cardinalities cannot create an inconsistent manager record
@pytest.mark.parametrize("ViewCount", (0, 3))
def test_unknown_annotation_view_count_is_rejected(ViewCount: int) -> None:
    with pytest.raises(SldprtFormatError, match="one or two"):
        encode_config0_stream(annotation_view_count=ViewCount)


# each additional feature contributes one class reference and one semantic atom
@pytest.mark.parametrize("FeatureCount", (1, 2, 3, 4, 5, 6, 7, 8))
def test_each_further_feature_adds_one_measured_atom(FeatureCount: int) -> None:
    StreamData = encode_config0_stream(atoms=_atoms(FeatureCount))
    assert len(StreamData) == REFERENCE_LENGTH + PER_FEATURE_BYTES * (FeatureCount - 1)
    assert PER_FEATURE_ATOM_BYTES == PER_FEATURE_BYTES
    AtomDefinition = b"\xff\xff\x01\x00\x08\x00moAtom_c"
    AtomPos = StreamData.index(AtomDefinition)
    assert struct.unpack_from("<II", StreamData, AtomPos - 8) == (
        100 + FeatureCount,
        FeatureCount,
    )


# later map targets advance once per inserted atom while pre-atom targets stay fixed
def test_dynamic_atoms_renumber_only_post_atom_map_references() -> None:
    assert ShiftMapReference("classref", 57, 1) == 57
    assert ShiftMapReference("classref", 58, 1) == 59
    assert ShiftMapReference("objectref", 58, 1) == 58
    assert ShiftMapReference("objectref", 59, 1) == 60


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
