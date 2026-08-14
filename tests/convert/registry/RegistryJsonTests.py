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
        data=b"brep",
        role=PayloadRole.BREP,
        file_extension=".brep",
    )
    MeshPayload = BrepPayload(
        "payload:tessellation",
        "test.mesh",
        "tessellation",
        "1",
        "1" * 64,
        data=b"mesh",
        role=PayloadRole.TESSELLATION,
        file_extension=".mesh",
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
    )
    SourceData = ReplaceValue(
        BuildSource(),
        configurations=(
            Configuration("configuration:first", "Shared", True),
            Configuration("configuration:second", "Second"),
            Configuration("configuration:third", "Shared"),
        ),
        meshes=(MeshData,),
        brep_payloads=(BrepData, MeshPayload),
        capabilities=frozenset(
            {
                Capability.BREP,
                Capability.TESSELLATION,
                Capability.NATIVE_PAYLOADS,
            }
        ),
    )
    PayloadData = SourceData.to_json().encode("utf-8")
    RestoredData = JsonAdapter().read(
        PayloadData,
        ReadOptions(
            configuration="Shared",
            include_brep=False,
            include_tessellation=False,
        ),
    )
    ActiveIds = [
        ItemData.id for ItemData in RestoredData.configurations if ItemData.active
    ]
    assert ActiveIds == ["configuration:first", "configuration:third"]
    assert not RestoredData.meshes
    assert not RestoredData.brep_payloads
    assert not RestoredData.capabilities & {
        Capability.BREP,
        Capability.TESSELLATION,
        Capability.NATIVE_PAYLOADS,
    }


# unknown configuration selection must fail rather than silently activating an arbitrary state
def CheckMissingCfg() -> None:
    PayloadData = BuildSource().to_json().encode("utf-8")
    with Pytest.raises(ValueError, match="configuration"):
        JsonAdapter().read(
            PayloadData,
            ReadOptions(configuration="configuration:missing"),
        )
