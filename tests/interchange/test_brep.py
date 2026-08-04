# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import is_dataclass, replace

import interchange
from interchange import (
    BrepBody,
    BrepCoedge,
    BrepCurve,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepPcurve,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepSurface,
    BrepVertex,
    CadDocument,
    Capability,
    LineCurve,
    NurbsCurve,
    PlaneSurface,
    Transform,
    Vector3,
    filter_document,
    infer_capabilities,
)

from tests.interchange.test_document import document


def triangle_brep() -> BrepModel:
    vertices = (
        BrepVertex("vertex:0", Vector3(0.0, 0.0, 0.0)),
        BrepVertex("vertex:1", Vector3(1.0, 0.0, 0.0)),
        BrepVertex("vertex:2", Vector3(0.0, 1.0, 0.0)),
    )
    curves = (
        LineCurve("curve:0", Vector3(0.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0)),
        LineCurve("curve:1", Vector3(1.0, 0.0, 0.0), Vector3(-1.0, 1.0, 0.0)),
        LineCurve("curve:2", Vector3(0.0, 1.0, 0.0), Vector3(0.0, -1.0, 0.0)),
    )
    edges = tuple(
        BrepEdge(
            f"edge:{index}",
            f"vertex:{index}",
            f"vertex:{(index + 1) % 3}",
            f"curve:{index}",
            0.0,
            1.0,
        )
        for index in range(3)
    )
    coedges = tuple(
        BrepCoedge(f"coedge:{index}", f"edge:{index}") for index in range(3)
    )
    return BrepModel(
        curves=curves,
        surfaces=(
            PlaneSurface(
                "surface:0",
                Vector3(0.0, 0.0, 0.0),
                Vector3(0.0, 0.0, 1.0),
                Vector3(1.0, 0.0, 0.0),
            ),
        ),
        vertices=vertices,
        edges=edges,
        coedges=coedges,
        loops=(BrepLoop("loop:0", tuple(value.id for value in coedges), True),),
        faces=(BrepFace("face:0", "surface:0", ("loop:0",)),),
        face_uses=(BrepFaceUse("face-use:0", "face:0"),),
        shells=(BrepShell("shell:0", ("face-use:0",), False),),
        shell_uses=(BrepShellUse("shell-use:0", "shell:0"),),
        regions=(BrepRegion("region:0", ("shell-use:0",), False),),
        bodies=(
            BrepBody(
                "brep-body:0",
                ("region:0",),
                Transform(),
                "body:1",
            ),
        ),
    )


def test_neutral_brep_roundtrips_and_drives_capability_inference() -> None:
    source = replace(document(), brep=triangle_brep(), capabilities=frozenset())
    source.assert_valid()
    assert Capability.BREP in infer_capabilities(source)
    restored = CadDocument.from_json(source.to_json())
    assert restored == source


def test_neutral_brep_filter_removes_geometry_without_removing_history() -> None:
    source = replace(
        document(),
        brep=triangle_brep(),
        capabilities=frozenset({Capability.BREP, Capability.PARAMETRIC_HISTORY}),
    )
    filtered = filter_document(
        source,
        include_brep=False,
        include_tessellation=True,
        keep_payload_records=True,
    )
    assert filtered.brep is None
    assert Capability.BREP not in filtered.capabilities
    assert Capability.PARAMETRIC_HISTORY in filtered.capabilities


def test_neutral_brep_validation_rejects_broken_topology() -> None:
    model = triangle_brep()
    broken = replace(model, edges=(replace(model.edges[0], curve_id="missing"),))
    errors = broken.validate(frozenset({"body:1"}))
    assert any("missing curve" in error for error in errors)


def test_neutral_brep_validation_rejects_invalid_nurbs_and_schema() -> None:
    model = triangle_brep()
    invalid_curve = NurbsCurve(
        "curve:0",
        2,
        (
            Vector3(0.0, 0.0, 0.0),
            Vector3(0.5, 0.5, 0.0),
            Vector3(1.0, 0.0, 0.0),
        ),
        (0.0, 1.0),
        (2, 2),
    )
    invalid = replace(
        model,
        curves=(invalid_curve, *model.curves[1:]),
        schema_version="",
    )
    errors = invalid.validate(frozenset({"body:1"}))
    assert "B-rep schema version must be a non-empty string" in errors
    assert "B-rep curve curve:0 is invalid" in errors


def test_every_public_brep_geometry_type_belongs_to_one_family() -> None:
    families = (BrepCurve, BrepPcurve, BrepSurface)
    values = {
        value
        for name, value in vars(interchange).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and is_dataclass(value)
        and value not in families
        and any(issubclass(value, family) for family in families)
    }
    assert values
    for value in values:
        assert sum(issubclass(value, family) for family in families) == 1
