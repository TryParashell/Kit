# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import replace as ReplaceValue
from io import BytesIO
from pathlib import Path as FilePath
from typing import Any as AnyValue

import pytest as Pytest

from convert.adapters import (
    AdapterInfo,
    AdapterRegistry,
    ApplicationUsabilityError,
    WriteOptions,
    WriteResult,
)
from interchange import CadDocument, Capability
from tests.convert.registry_test_support import BuildSource, ResultAdapter


# requirement producing output isolates dependency policy from carrier and capability behavior
class NeedAdapter(ResultAdapter):

    # external dependency evidence exercises default and self contained rejection gates
    def WriteData(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: AnyValue,
        OptionsData: AnyValue = None,
    ) -> WriteResult:
        return ReplaceValue(
            super().WriteData(DocumentData, TargetData, OptionsData),
            requirements=("external application",),
        )


setattr(NeedAdapter, "write", NeedAdapter.WriteData)


# one dependency registry keeps requirement policy tests focused on caller options
def BuildRegistry(FormatId: str) -> tuple[AdapterRegistry, AdapterInfo]:
    InfoData = AdapterInfo(
        FormatId,
        FormatId,
        "1",
        (".requirement",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(NeedAdapter(InfoData))
    return RegistryData, InfoData


# default writes reject external requirements even when reversible carriers are allowed
@Pytest.mark.parametrize("OptionValues", ({}, {"allow_carrier": True}))
def CheckNeeds(OptionValues: dict[str, bool]) -> None:
    RegistryData, InfoData = BuildRegistry("format.requirement")
    TargetData = BytesIO()
    with Pytest.raises(ApplicationUsabilityError) as ErrorInfo:
        RegistryData.write(
            BuildSource(),
            TargetData,
            format_id=InfoData.format_id,
            options=WriteOptions(values=OptionValues),
        )
    assert TargetData.getvalue() == b""
    assert ErrorInfo.value.issues == ("external_requirements",)
    assert ErrorInfo.value.requirements == ("external application",)


# self contained stream policy restores original bytes after rejecting dependencies
def CheckStream() -> None:
    RegistryData, InfoData = BuildRegistry("format.self-contained-stream")
    TargetData = BytesIO(b"original")
    with Pytest.raises(ApplicationUsabilityError) as ErrorInfo:
        RegistryData.write(
            BuildSource(),
            TargetData,
            format_id=InfoData.format_id,
            options=WriteOptions(
                values={
                    "allow_carrier": True,
                    "require_self_contained": True,
                }
            ),
        )
    assert TargetData.getvalue() == b"original"
    assert ErrorInfo.value.issues == ("external_requirements",)
    assert ErrorInfo.value.requirements == ("external application",)


# companion bundle output exercises rollback across every generated staged file
class BundleAdapter(ResultAdapter):

    # path restriction forces bundle rollback through transactional filesystem staging
    def CanWrite(SelfValue, DocumentData: CadDocument, TargetData: AnyValue) -> bool:
        return isinstance(TargetData, (str, FilePath))

    # generated companions prove rejection restores both destination and neighboring files
    def WriteData(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: AnyValue,
        OptionsData: AnyValue = None,
    ) -> WriteResult:
        OutputPath = FilePath(TargetData).expanduser().resolve()
        OutputPath.parent.mkdir(parents=True, exist_ok=True)
        OutputPath.write_bytes(b"generated")
        (OutputPath.parent / "component.bin").write_bytes(b"generated component")
        return WriteResult(
            OutputPath,
            SelfValue.info.format_id,
            len(b"generated"),
            requirements=("external component file",),
            application_usable=True,
            vendor_loadable=True,
        )


setattr(BundleAdapter, "supports", BundleAdapter.CanWrite)
setattr(BundleAdapter, "write", BundleAdapter.WriteData)


# rejected bundles restore every preexisting file before surfacing dependency evidence
def CheckBundle(TmpPath: FilePath) -> None:
    InfoData = AdapterInfo(
        "format.self-contained-path",
        "Self contained path",
        "1",
        (".bundle",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(BundleAdapter(InfoData))
    TargetPath = TmpPath / "existing.bundle"
    ComponentPath = TmpPath / "component.bin"
    TargetPath.write_bytes(b"original")
    ComponentPath.write_bytes(b"original component")
    with Pytest.raises(ApplicationUsabilityError) as ErrorInfo:
        RegistryData.write(
            BuildSource(),
            TargetPath,
            format_id=InfoData.format_id,
            options=WriteOptions(
                overwrite=True,
                values={
                    "allow_carrier": True,
                    "require_self_contained": True,
                },
            ),
        )
    assert TargetPath.read_bytes() == b"original"
    assert ComponentPath.read_bytes() == b"original component"
    assert tuple(sorted(PathValue.name for PathValue in TmpPath.iterdir())) == (
        "component.bin",
        "existing.bundle",
    )
    assert ErrorInfo.value.issues == ("external_requirements",)
    assert ErrorInfo.value.requirements == ("external component file",)
