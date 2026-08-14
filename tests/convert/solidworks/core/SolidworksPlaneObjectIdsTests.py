# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from convert.adapters.solidworks.core.Native import _principal_plane_ids, _repair_plane_object_ids, _write_object_ids
from interchange import (
    CadDocument,
    CadSource,
    SupportPlane,
    Transform,
    UnitSystem,
    Vector3,
)

_FRONT = Transform(
    Vector3(0.0, 0.0, 0.0),
    Vector3(1.0, 0.0, 0.0),
    Vector3(0.0, 1.0, 0.0),
    Vector3(0.0, 0.0, 1.0),
)
_TOP = Transform(
    Vector3(0.0, 0.0, 0.0),
    Vector3(1.0, 0.0, 0.0),
    Vector3(0.0, 0.0, -1.0),
    Vector3(0.0, 1.0, 0.0),
)
_RIGHT = Transform(
    Vector3(0.0, 0.0, 0.0),
    Vector3(0.0, 0.0, -1.0),
    Vector3(0.0, 1.0, 0.0),
    Vector3(1.0, 0.0, 0.0),
)


def _document(planes: tuple[SupportPlane, ...]) -> CadDocument:
    return CadDocument(
        source=CadSource("freecad.fcstd", "Duplicate.FCStd", ""),
        units=UnitSystem.MILLIMETER,
        configurations=(),
        parameters=(),
        support_planes=planes,
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
    )


def test_coincident_duplicate_planes_do_not_share_a_principal_object_id() -> None:
    planes = (
        SupportPlane("plane:a", "XY_Plane", _FRONT),
        SupportPlane("plane:b", "XY_Plane001", _FRONT),
        SupportPlane("plane:c", "YZ_Plane", _RIGHT),
        SupportPlane("plane:d", "YZ_Plane001", _RIGHT),
        SupportPlane("plane:e", "XZ_Plane", _TOP),
        SupportPlane("plane:f", "XZ_Plane001", _TOP),
    )
    principal = _principal_plane_ids(planes)
    assert principal == {"plane:a": 2, "plane:c": 4, "plane:e": 3}
    object_ids = _write_object_ids(_document(planes))
    assigned = tuple(object_ids[f"plane:{plane.id}"] for plane in planes)
    assert len(set(assigned)) == len(assigned)
    assert assigned[0] == 2
    assert assigned[2] == 4
    assert assigned[4] == 3
    assert all(value >= 26 for value in (assigned[1], assigned[3], assigned[5]))


def test_principal_plane_ids_keeps_the_first_matching_plane() -> None:
    planes = (
        SupportPlane("plane:first", "XY_Plane", _FRONT),
        SupportPlane("plane:second", "XY_Plane001", _FRONT),
    )
    assert _principal_plane_ids(planes) == {"plane:first": 2}


def test_repair_plane_object_ids_resolves_collisions_with_donor_records() -> None:
    object_ids = {
        "plane:xy": 2,
        "plane:xz": 26,
        "plane:yz": 4,
        "plane:xz001": 27,
        "sketch:one": 26,
        "feature:one": 32,
        "configuration:default": 2,
    }
    _repair_plane_object_ids(object_ids)
    assert object_ids["plane:xy"] == 2
    assert object_ids["plane:yz"] == 4
    assert object_ids["sketch:one"] == 26
    assert object_ids["feature:one"] == 32
    assert object_ids["configuration:default"] == 2
    planes = tuple(
        value for key, value in object_ids.items() if key.startswith("plane:")
    )
    assert len(set(planes)) == len(planes)
    assert 26 not in planes
    assert object_ids["plane:xz"] not in {26, 32}
    assert object_ids["plane:xz001"] not in {26, 32}


def test_repair_plane_object_ids_is_idempotent() -> None:
    object_ids = {
        "plane:xy": 2,
        "plane:xz": 26,
        "plane:yz": 4,
        "sketch:one": 26,
        "feature:one": 32,
    }
    _repair_plane_object_ids(object_ids)
    once = dict(object_ids)
    _repair_plane_object_ids(object_ids)
    assert object_ids == once
