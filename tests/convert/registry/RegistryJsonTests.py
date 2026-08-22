# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace as ReplaceValue

import pytest as Pytest

from convert.adapters import ReadOptions
from convert.adapters.json import JsonAdapter
from interchange import (
    BrepPayload,
    Capability,
    Configuration,
    Mesh as SurfaceMesh,
    PayloadRole,
    Vector3 as SpaceVector,
)
from tests.convert.registry.RegistryTestSupport import BuildSource


# representation filtering must update payload collections meshes and declared capabilities together
def CheckReadFilter() -> None:
    BrepData = BrepPayload(
        "payload:brep",
        "test.brep",
        "shape",
        "1",
        "0" * 64,
        b"brep",
        "",
        None,
        {},
        PayloadRole.KBrep,
        ".brep",
    )
    MeshPayload = BrepPayload(
        "payload:tessellation",
        "test.mesh",
        "tessellation",
        "1",
        "1" * 64,
        b"mesh",
        "",
        None,
        {},
        PayloadRole.KTessellation,
        ".mesh",
    )
    MeshData = SurfaceMesh(
        "mesh:json",
        "JSON mesh",
        (
            SpaceVector(0.0, 0.0, 0.0),
            SpaceVector(1.0, 0.0, 0.0),
            SpaceVector(0.0, 1.0, 0.0),
        ),
        ((0, 1, 2),),
        (),
        None,
        {},
    )
    SourceData = ReplaceValue(
        BuildSource(),
        configurations=(
            Configuration("configuration:first", "Shared", True, None, (), (), {}),
            Configuration("configuration:second", "Second", False, None, (), (), {}),
            Configuration("configuration:third", "Shared", False, None, (), (), {}),
        ),
        meshes=(MeshData,),
        brep_payloads=(BrepData, MeshPayload),
        capabilities=frozenset(
            {
                Capability.KBrep,
                Capability.KTessellation,
                Capability.KNativePayloads,
            }
        ),
    )
    PayloadData = SourceData.ToJson().encode("utf-8")
    RestoredData = JsonAdapter().read(
        PayloadData,
        ReadOptions(
            configuration="Shared",
            include_brep=False,
            include_tessellation=False,
        ),
    )
    ActiveIds = [
        ItemData.EntityId
        for ItemData in RestoredData.Configurations
        if ItemData.IsActive
    ]
    assert ActiveIds == ["configuration:first", "configuration:third"]
    assert not RestoredData.Meshes
    assert not RestoredData.BrepPayloads
    assert not RestoredData.Capabilities & {
        Capability.KBrep,
        Capability.KTessellation,
        Capability.KNativePayloads,
    }


# unknown configuration selection must fail rather than silently activating an arbitrary state
def CheckMissingCfg() -> None:
    PayloadData = BuildSource().ToJson().encode("utf-8")
    with Pytest.raises(ValueError, match="configuration"):
        JsonAdapter().read(
            PayloadData,
            ReadOptions(configuration="configuration:missing"),
        )
