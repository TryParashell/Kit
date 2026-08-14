# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace

from convert.adapters.solidworks.core.Native import HORIZONTAL_AXIS_SUBELEMENT, NORMAL_AXIS_SUBELEMENT, VERTICAL_AXIS_SUBELEMENT, _matrix_frame, _plane_frame_block, _plane_payload, NativeMarker, NativeModel, NativeOperation, NativeSketch, expression_equation_texts, native_axis_bindings, operation_axis_subelement
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


def test_authored_plane_payload_carries_a_decodable_reference_frame() -> None:
    plane = _plane(
        "XY_Plane001",
        (
            Vector3(1.0, 0.0, 0.0),
            Vector3(0.0, 1.0, 0.0),
            Vector3(0.0, 0.0, 1.0),
        ),
    )
    payload = _plane_payload(plane)
    assert payload.endswith(_plane_frame_block(plane))
    offset = len(payload) - 121
    frame = _matrix_frame(payload, offset, len(payload))
    assert frame is not None
    assert frame[0] == offset
    assert frame[1] == 121
    assert frame[3] == (0.0, 0.0, 1.0)
    assert frame[4] == (1.0, 0.0, 0.0)
    assert frame[5] == (0.0, 1.0, 0.0)


def test_authored_plane_payload_is_empty_for_a_non_orthonormal_frame() -> None:
    plane = _plane(
        "Skewed001",
        (
            Vector3(1.0, 0.0, 0.0),
            Vector3(1.0, 1.0, 0.0),
            Vector3(0.0, 0.0, 1.0),
        ),
    )
    assert _plane_payload(plane) == b""


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
