# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace

import pytest

from convert.adapters.solidworks.container import SldprtFormatError
from convert.adapters.solidworks.donor_library import donor_by_id
from convert.adapters.solidworks.format import CONFIGURATION_STREAM
from convert.adapters.solidworks.native import (
    HORIZONTAL_AXIS_SUBELEMENT,
    NORMAL_AXIS_SUBELEMENT,
    VERTICAL_AXIS_SUBELEMENT,
    _donor_equation_texts,
    _matrix_frame,
    _patch_donor_equations,
    _patch_donor_plane_frames,
    _plane_frame_block,
    _serialized_string,
    NativeMarker,
    NativeModel,
    NativeOperation,
    NativeSketch,
    expression_equation_texts,
    native_axis_bindings,
    operation_axis_subelement,
)
from interchange import (
    CadDocument,
    CadSource,
    Expression,
    Parameter,
    ParameterRole,
    ParameterValue,
    SupportPlane,
    Transform,
    UnitSystem,
    ValueKind,
    Vector3,
)

METADATA_DONOR_ID = "arcboss_cut_cut_cut_through_rev_meta"


def _document(parameters: tuple[Parameter, ...]) -> CadDocument:
    return CadDocument(
        source=CadSource("freecad.fcstd", "Metadata.FCStd", "0" * 64),
        configurations=(),
        parameters=parameters,
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        units=UnitSystem.MILLIMETER,
    )


def _parameter(
    name: str,
    value: ParameterValue,
    source: str | None,
) -> Parameter:
    return Parameter(
        id=f"freecad:parameter:{name}",
        name=name,
        value=value,
        role=ParameterRole.DRIVING,
        owner_id="freecad:object:Owner",
        expression=None if source is None else Expression(source, (), "freecad"),
    )


def _plane(name: str, axes: tuple[Vector3, Vector3, Vector3]) -> SupportPlane:
    return SupportPlane(
        id=f"freecad:plane:{name}",
        name=name,
        transform=Transform(Vector3(0.0, 0.0, 0.0), axes[0], axes[1], axes[2]),
    )


def test_expression_equations_encode_reference_and_binding() -> None:
    document = _document(
        (
            _parameter(
                "Sketch004.9",
                ParameterValue(5.0, ValueKind.LENGTH, "mm"),
                "<<Attributes002>>.Diameter",
            ),
        )
    )
    assert expression_equation_texts(document) == (
        '"Kit_Attributes002_Diameter"= 5mm',
        '"Kit_Sketch004_9"= "Kit_Attributes002_Diameter"',
    )


def test_expression_equations_share_one_reference_variable() -> None:
    document = _document(
        (
            _parameter(
                "LeadInFeed",
                ParameterValue(0.0, ValueKind.NUMBER, ""),
                "HorizFeed",
            ),
            _parameter(
                "LeadOutFeed",
                ParameterValue(0.0, ValueKind.NUMBER, ""),
                "HorizFeed",
            ),
        )
    )
    assert expression_equation_texts(document) == (
        '"Kit_HorizFeed"= 0',
        '"Kit_LeadInFeed"= "Kit_HorizFeed"',
        '"Kit_LeadOutFeed"= "Kit_HorizFeed"',
    )


def test_expression_equations_decline_compound_sources() -> None:
    document = _document(
        (
            _parameter(
                "Width",
                ParameterValue(5.0, ValueKind.LENGTH, "mm"),
                "Length / 2",
            ),
        )
    )
    assert expression_equation_texts(document) is None


def test_expression_equations_decline_conflicting_reference_values() -> None:
    document = _document(
        (
            _parameter("A", ParameterValue(1.0, ValueKind.NUMBER, ""), "Shared"),
            _parameter("B", ParameterValue(2.0, ValueKind.NUMBER, ""), "Shared"),
        )
    )
    assert expression_equation_texts(document) is None


def test_documents_without_expressions_need_no_equations() -> None:
    assert expression_equation_texts(_document(())) == ()


def test_metadata_donor_carries_spare_planes_and_equations() -> None:
    donor = donor_by_id(METADATA_DONOR_ID)
    assert len(donor.spare_plane_ids) == 4
    assert len(donor.spare_plane_ids) == len(donor.spare_plane_names)
    assert len(donor.spare_plane_ids) == len(donor.spare_plane_frames)
    assert len(donor.spare_equations) == 24
    assert len(set(donor.spare_equations)) == len(donor.spare_equations)
    configuration = donor.container[CONFIGURATION_STREAM]
    for text in donor.spare_equations:
        assert configuration.count(_serialized_string(text)) == 1


def test_metadata_donor_spare_plane_frames_decode_where_declared() -> None:
    donor = donor_by_id(METADATA_DONOR_ID)
    stream = donor.stream
    for offset in donor.spare_plane_frames:
        frame = _matrix_frame(stream, offset, offset + 121)
        assert frame is not None
        assert frame[0] == offset
        assert frame[1] == 121


def test_plane_frame_block_is_recovered_by_the_decoder() -> None:
    plane = _plane(
        "XZ_Plane",
        (
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, -2.220446049250313e-16, 1.0),
            Vector3(0.0, -1.0, -2.220446049250313e-16),
        ),
    )
    block = _plane_frame_block(plane)
    assert block is not None
    assert len(block) == 121
    frame = _matrix_frame(block, 0, len(block))
    assert frame is not None
    _, _, origin, normal, u_axis, v_axis = frame
    assert origin == (0.0, 0.0, 0.0)
    assert normal == (0.0, -1.0, 0.0)
    assert u_axis == (1.0, 0.0, 0.0)
    assert v_axis == (0.0, 0.0, 1.0)


def test_plane_frame_block_rejects_a_non_orthonormal_frame() -> None:
    plane = _plane(
        "Skewed",
        (
            Vector3(1.0, 0.0, 0.0),
            Vector3(1.0, 1.0, 0.0),
            Vector3(0.0, 0.0, 1.0),
        ),
    )
    assert _plane_frame_block(plane) is None


def test_plane_frames_are_patched_in_place_without_moving_the_stream() -> None:
    donor = donor_by_id(METADATA_DONOR_ID)
    stream = donor.stream
    plane = _plane(
        "XY_Plane001",
        (
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
            Vector3(0.0, 0.0, 1.0),
        ),
    )
    block = _plane_frame_block(plane)
    assert block is not None
    offset = donor.spare_plane_frames[0]
    patched = _patch_donor_plane_frames(stream, ((offset, block),))
    assert len(patched) == len(stream)
    assert patched[:offset] == stream[:offset]
    assert patched[offset + 121 :] == stream[offset + 121 :]
    frame = _matrix_frame(patched, offset, offset + 121)
    assert frame is not None
    assert frame[4] == (1.0, 0.0, 0.0)
    assert frame[5] == (0.0, 1.0, 0.0)


def test_plane_frame_patch_rejects_an_offset_past_the_stream() -> None:
    donor = donor_by_id(METADATA_DONOR_ID)
    stream = donor.stream
    with pytest.raises(SldprtFormatError, match="outside the resolved stream"):
        _patch_donor_plane_frames(stream, ((len(stream) - 4, b"\0" * 121),))


def test_equation_patch_replaces_only_the_named_relation_text() -> None:
    donor = donor_by_id(METADATA_DONOR_ID)
    configuration = donor.container[CONFIGURATION_STREAM]
    texts = tuple(
        f'"KitPatched{index:02d}"= {index}'
        for index in range(1, len(donor.spare_equations) + 1)
    )
    patched = _patch_donor_equations(configuration, donor, texts)
    for original, replacement in zip(donor.spare_equations, texts, strict=True):
        assert _serialized_string(original) not in patched
        assert patched.count(_serialized_string(replacement)) == 1


def test_equation_patch_rejects_a_relation_text_that_is_absent() -> None:
    donor = donor_by_id(METADATA_DONOR_ID)
    absent = replace(donor, spare_equations=('"KitMissing"= 1',))
    with pytest.raises(SldprtFormatError, match="does not appear exactly once"):
        _patch_donor_equations(
            donor.container[CONFIGURATION_STREAM], absent, ('"KitOther"= 2',)
        )


def test_donor_equation_texts_pad_the_unused_spares_with_reserved_names() -> None:
    donor = donor_by_id(METADATA_DONOR_ID)
    document = _document(
        (
            _parameter(
                "Sketch004.9",
                ParameterValue(5.0, ValueKind.LENGTH, "mm"),
                "<<Attributes002>>.Diameter",
            ),
        )
    )
    texts = _donor_equation_texts(document, donor)
    assert texts is not None
    assert len(texts) == len(donor.spare_equations)
    assert texts[:2] == expression_equation_texts(document)
    assert all(text.startswith('"KitReserved') for text in texts[2:])


def test_donor_equation_texts_decline_when_the_spares_run_out() -> None:
    donor = donor_by_id(METADATA_DONOR_ID)
    narrow = replace(donor, spare_equations=donor.spare_equations[:1])
    document = _document(
        (
            _parameter(
                "Sketch004.9",
                ParameterValue(5.0, ValueKind.LENGTH, "mm"),
                "<<Attributes002>>.Diameter",
            ),
        )
    )
    assert _donor_equation_texts(document, narrow) is None


def _marker(
    offset: int,
    semantic: str,
    coordinates: tuple[float, float] | None,
    endpoints: tuple[int, int] | None,
    profile_role: int,
) -> NativeMarker:
    return NativeMarker(
        offset=offset,
        length=32,
        prefix="",
        native_kind=1,
        locus="",
        profile_role=profile_role,
        state=None,
        object_index=None,
        local_id=None,
        coordinates_mm=coordinates,
        endpoint_indices=endpoints,
        construction=profile_role == 2,
        semantic=semantic,
    )


def _sketch(markers: tuple[NativeMarker, ...]) -> NativeSketch:
    return NativeSketch(
        object_id=55,
        name="Sketch5",
        support_plane_id=3,
        native_offset=0,
        native_end=1,
        markers=markers,
        profiles=(),
        dimensions=(),
        constraints=(),
    )


def _operation(kind: str) -> NativeOperation:
    return NativeOperation(
        object_id=60,
        name="Revolve1",
        kind=kind,
        profile_id=55,
        dependencies=(),
        native_offset=0,
        native_end=1,
        length_mm=None,
        radius_mm=None,
        family_code=None,
        operation_code=None,
        schema_code=None,
        direction_code=None,
        termination_code=None,
        selection_offsets=(),
        selected_local_ids=(),
    )


def test_extrusion_direction_is_the_profile_sketch_normal_axis() -> None:
    sketch = _sketch(())
    assert (
        operation_axis_subelement(_operation("join"), sketch) == NORMAL_AXIS_SUBELEMENT
    )
    assert (
        operation_axis_subelement(_operation("cut"), sketch) == NORMAL_AXIS_SUBELEMENT
    )
    assert operation_axis_subelement(_operation("native"), sketch) is None


def test_revolution_axis_is_read_from_the_profile_construction_line() -> None:
    vertical = _sketch(
        (
            _marker(0, "circle", (0.0, -154.0), None, 1),
            _marker(32, "circle", (0.0, -216.0), None, 1),
            _marker(64, "line", None, (0, 1), 2),
        )
    )
    assert (
        operation_axis_subelement(_operation("revolve_join"), vertical)
        == VERTICAL_AXIS_SUBELEMENT
    )
    horizontal = _sketch(
        (
            _marker(0, "circle", (-20.0, 4.0), None, 1),
            _marker(32, "circle", (20.0, 4.0), None, 1),
            _marker(64, "line", None, (0, 1), 2),
        )
    )
    assert (
        operation_axis_subelement(_operation("revolve_cut"), horizontal)
        == HORIZONTAL_AXIS_SUBELEMENT
    )
    skewed = _sketch(
        (
            _marker(0, "circle", (0.0, 0.0), None, 1),
            _marker(32, "circle", (10.0, 10.0), None, 1),
            _marker(64, "line", None, (0, 1), 2),
        )
    )
    assert operation_axis_subelement(_operation("revolve_join"), skewed) is None


def test_axis_bindings_key_the_operation_and_its_profile_sketch() -> None:
    sketch = _sketch(())
    model = NativeModel(
        configurations=(),
        features=(),
        planes=(),
        sketches=(sketch,),
        operations=(replace(_operation("join"), object_id=32),),
        names=(),
        classes=(),
        scalars=(),
    )
    assert native_axis_bindings(model) == frozenset({(32, 55, NORMAL_AXIS_SUBELEMENT)})


def test_axis_bindings_ignore_operations_without_a_profile_sketch() -> None:
    model = NativeModel(
        configurations=(),
        features=(),
        planes=(),
        sketches=(),
        operations=(replace(_operation("join"), profile_id=None),),
        names=(),
        classes=(),
        scalars=(),
    )
    assert native_axis_bindings(model) == frozenset()
