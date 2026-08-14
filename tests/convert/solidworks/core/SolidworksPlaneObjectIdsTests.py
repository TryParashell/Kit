# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations
from convert.adapters.solidworks.core.Native import (
    _principal_plane_ids as PrincipalPlaneIds,
    _repair_plane_object_ids as RepairPlaneObjectIds,
    _write_object_ids as WriteObjectIds,
)
from interchange import (
    CadDocument,
    CadSource,
    SupportPlane,
    Transform,
    UnitSystem,
    Vector3 as VectorThree,
)

# centralizes shared evidence so every related assertion uses one value
KFront = Transform(
    VectorThree(0.0, 0.0, 0.0),
    VectorThree(1.0, 0.0, 0.0),
    VectorThree(0.0, 1.0, 0.0),
    VectorThree(0.0, 0.0, 1.0),
)

# centralizes shared evidence so every related assertion uses one value
KTopInfo = Transform(
    VectorThree(0.0, 0.0, 0.0),
    VectorThree(1.0, 0.0, 0.0),
    VectorThree(0.0, 0.0, -1.0),
    VectorThree(0.0, 1.0, 0.0),
)

# centralizes shared evidence so every related assertion uses one value
KRight = Transform(
    VectorThree(0.0, 0.0, 0.0),
    VectorThree(0.0, 0.0, -1.0),
    VectorThree(0.0, 1.0, 0.0),
    VectorThree(1.0, 0.0, 0.0),
)


# keeps this focused behavior isolated so regressions remain immediately visible
def Document(Planes: tuple[SupportPlane, ...]) -> CadDocument:
    return CadDocument(
        source=CadSource("freecad.fcstd", "Duplicate.FCStd", ""),
        units=UnitSystem.MILLIMETER,
        configurations=(),
        parameters=(),
        support_planes=Planes,
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestCDPDNSAPOI() -> None:
    Planes = (
        SupportPlane("plane:a", "XY_Plane", KFront),
        SupportPlane("plane:b", "XY_Plane001", KFront),
        SupportPlane("plane:c", "YZ_Plane", KRight),
        SupportPlane("plane:d", "YZ_Plane001", KRight),
        SupportPlane("plane:e", "XZ_Plane", KTopInfo),
        SupportPlane("plane:f", "XZ_Plane001", KTopInfo),
    )
    Principal = PrincipalPlaneIds(Planes)
    assert Principal == {"plane:a": 2, "plane:c": 4, "plane:e": 3}
    ObjectIds = WriteObjectIds(Document(Planes))
    Assigned = tuple((ObjectIds[f"plane:{Plane.id}"] for Plane in Planes))
    assert len(set(Assigned)) == len(Assigned)
    assert Assigned[0] == 2
    assert Assigned[2] == 4
    assert Assigned[4] == 3
    assert all(
        (ItemValue >= 26 for ItemValue in (Assigned[1], Assigned[3], Assigned[5]))
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPPIKTFMP() -> None:
    Planes = (
        SupportPlane("plane:first", "XY_Plane", KFront),
        SupportPlane("plane:second", "XY_Plane001", KFront),
    )
    assert PrincipalPlaneIds(Planes) == {"plane:first": 2}


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRPOIRCWDR() -> None:
    ObjectIds = {
        "plane:xy": 2,
        "plane:xz": 26,
        "plane:yz": 4,
        "plane:xz001": 27,
        "sketch:one": 26,
        "feature:one": 32,
        "configuration:default": 2,
    }
    RepairPlaneObjectIds(ObjectIds)
    assert ObjectIds["plane:xy"] == 2
    assert ObjectIds["plane:yz"] == 4
    assert ObjectIds["sketch:one"] == 26
    assert ObjectIds["feature:one"] == 32
    assert ObjectIds["configuration:default"] == 2
    Planes = tuple(
        (
            ItemValue
            for LookupKey, ItemValue in ObjectIds.items()
            if LookupKey.startswith("plane:")
        )
    )
    assert len(set(Planes)) == len(Planes)
    assert 26 not in Planes
    assert ObjectIds["plane:xz"] not in {26, 32}
    assert ObjectIds["plane:xz001"] not in {26, 32}


# keeps this focused behavior isolated so regressions remain immediately visible
def TestRPOIII() -> None:
    ObjectIds = {
        "plane:xy": 2,
        "plane:xz": 26,
        "plane:yz": 4,
        "sketch:one": 26,
        "feature:one": 32,
    }
    RepairPlaneObjectIds(ObjectIds)
    OnceInfo = dict(ObjectIds)
    RepairPlaneObjectIds(ObjectIds)
    assert ObjectIds == OnceInfo
