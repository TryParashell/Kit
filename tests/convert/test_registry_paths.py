# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from pathlib import Path as FilePath

import pytest as Pytest

from convert.adapters import (
    AdapterInfo,
    AdapterRegistry,
    ApplicationUsabilityError,
    WriteOptions,
)
from interchange import Capability
from tests.convert.registry_test_support import BuildSource, CarrierAdapter


# one carrier registry keeps path rollback cases focused on filesystem state changes
def BuildRegistry(FormatId: str) -> tuple[AdapterRegistry, AdapterInfo]:
    InfoData = AdapterInfo(
        FormatId,
        FormatId,
        "1",
        (".carrier",),
        capabilities=frozenset(Capability),
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(CarrierAdapter(InfoData))
    return RegistryData, InfoData


# a rejected staged write must restore an existing destination byte for byte
def CheckExisting(TmpPath: FilePath) -> None:
    RegistryData, InfoData = BuildRegistry("format.path-carrier")
    TargetPath = TmpPath / "existing.carrier"
    TargetPath.write_bytes(b"original")
    with Pytest.raises(ApplicationUsabilityError):
        RegistryData.write(
            BuildSource(),
            TargetPath,
            format_id=InfoData.format_id,
            options=WriteOptions(overwrite=True),
        )
    assert TargetPath.read_bytes() == b"original"
    assert tuple(TmpPath.iterdir()) == (TargetPath,)


# carrier opt in commits the exact staged artifact without leaving temporary siblings
def CheckCommit(TmpPath: FilePath) -> None:
    RegistryData, InfoData = BuildRegistry("format.path-carrier")
    TargetPath = TmpPath / "existing.carrier"
    TargetPath.write_bytes(b"original")
    ResultData = RegistryData.write(
        BuildSource(),
        TargetPath,
        format_id=InfoData.format_id,
        options=WriteOptions(
            overwrite=True,
            values={"allow_carrier": True},
        ),
    )
    assert ResultData.path == TargetPath.resolve()
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is False
    assert TargetPath.read_bytes() == b"carrier"
    assert tuple(TmpPath.iterdir()) == (TargetPath,)


# rollback removes only ancestors created for the failed staging transaction
def CheckNewFolders(TmpPath: FilePath) -> None:
    RegistryData, InfoData = BuildRegistry("format.nested-carrier")
    AbsentRoot = TmpPath / "absent"
    with Pytest.raises(ApplicationUsabilityError):
        RegistryData.write(
            BuildSource(),
            AbsentRoot / "one" / "two" / "blocked.carrier",
            format_id=InfoData.format_id,
        )
    assert not AbsentRoot.exists()
    ExistingRoot = TmpPath / "existing"
    ExistingRoot.mkdir()
    with Pytest.raises(ApplicationUsabilityError):
        RegistryData.write(
            BuildSource(),
            ExistingRoot / "one" / "two" / "blocked.carrier",
            format_id=InfoData.format_id,
        )
    assert ExistingRoot.is_dir()
    assert tuple(ExistingRoot.iterdir()) == ()


# injected creation failure proves partial directory setup remains transactionally clean
def CheckPartMake(TmpPath: FilePath, MonkeyPatch) -> None:
    RegistryData, InfoData = BuildRegistry("format.partial-directory")
    TargetPath = TmpPath / "partial" / "one" / "two" / "blocked.partial"
    FailurePath = TmpPath / "partial" / "one"
    OriginalMake = FilePath.mkdir

    # forced failure isolates cleanup after only some ancestors were created
    def FailMakeMut(PathValue: FilePath, *ArgValues, **NamedValues) -> None:
        if PathValue == FailurePath:
            raise OSError("forced staging directory failure")
        OriginalMake(PathValue, *ArgValues, **NamedValues)

    MonkeyPatch.setattr(FilePath, "mkdir", FailMakeMut)
    with Pytest.raises(OSError, match="forced staging directory failure"):
        RegistryData.write(
            BuildSource(),
            TargetPath,
            format_id=InfoData.format_id,
        )
    assert not (TmpPath / "partial").exists()


# racing directory creation must preserve the peer owned ancestor during rollback
def CheckConcurrent(TmpPath: FilePath, MonkeyPatch) -> None:
    RegistryData, InfoData = BuildRegistry("format.concurrent-directory")
    SharedPath = TmpPath / "concurrent"
    TargetPath = SharedPath / "one" / "two" / "blocked.concurrent"
    OriginalMake = FilePath.mkdir
    InjectedFlag = False

    # simulated peer ownership prevents cleanup from deleting a concurrently created folder
    def RaceMakeMut(PathValue: FilePath, *ArgValues, **NamedValues) -> None:
        nonlocal InjectedFlag
        if PathValue == SharedPath and not InjectedFlag:
            InjectedFlag = True
            OriginalMake(PathValue, *ArgValues, **NamedValues)
            raise FileExistsError(PathValue)
        OriginalMake(PathValue, *ArgValues, **NamedValues)

    MonkeyPatch.setattr(FilePath, "mkdir", RaceMakeMut)
    with Pytest.raises(ApplicationUsabilityError):
        RegistryData.write(
            BuildSource(),
            TargetPath,
            format_id=InfoData.format_id,
        )
    assert SharedPath.is_dir()
    assert tuple(SharedPath.iterdir()) == ()
