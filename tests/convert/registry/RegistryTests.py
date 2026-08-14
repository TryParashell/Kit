# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from io import BytesIO

import pytest as Pytest

from convert.adapters import (
    AdapterInfo,
    AdapterRegistry,
    AdapterRegistryError,
    AmbiguousAdapterError,
    CapabilityLossError,
)
from interchange import Capability
from tests.convert.registry.RegistryTestSupport import BuildAdapter, BuildSource, ResultAdapter


# nested module discovery must not depend on packages reexporting their adapter class
def CheckNestedPack(TmpPath, MonkeyPatch) -> None:
    PackageName = f"kitnested{TmpPath.name.replace('-', '')}"
    PackagePath = TmpPath / PackageName
    FormatPath = PackagePath / "nested"
    FormatPath.mkdir(parents=True)
    (PackagePath / "__init__.py").write_text("", encoding="utf-8")
    (FormatPath / "__init__.py").write_text("", encoding="utf-8")
    (FormatPath / "implementation.py").write_text(
        "from convert.adapters.json.Adapter import JsonAdapter\n"
        "class NestedAdapter(JsonAdapter):\n    Discovered = True\n",
        encoding="utf-8",
    )
    MonkeyPatch.syspath_prepend(str(TmpPath))
    RegistryData = AdapterRegistry()
    assert RegistryData.introspect(PackageName) == ("interchange.json",)
    assert type(RegistryData.reader("interchange.json")).__name__ == "NestedAdapter"


# complete tie reporting lets callers choose among every equally strong reader
def CheckReaderTie() -> None:
    RegistryData = AdapterRegistry()
    FormatIds = ("format.alpha", "format.beta", "format.gamma")
    RegistryData.extend(BuildAdapter(FormatId) for FormatId in FormatIds)
    SourceData = BuildSource().to_json().encode("utf-8")
    with Pytest.raises(AmbiguousAdapterError) as ErrorInfo:
        RegistryData.select_reader(SourceData)
    assert all(FormatId in str(ErrorInfo.value) for FormatId in FormatIds)


# attributed results prevent adapters from claiming formats outside their registered namespace
def CheckResults() -> None:
    SourceData = BuildSource().to_json().encode("utf-8")
    ReaderRegistry = AdapterRegistry()
    ReaderRegistry.register(BuildAdapter("format.probe", ProbeFormat="format.other"))
    with Pytest.raises(AdapterRegistryError, match="returned probe format"):
        ReaderRegistry.select_reader(SourceData)
    WriterRegistry = AdapterRegistry()
    WriterRegistry.register(BuildAdapter("format.write", WriteFormat="format.other"))
    with Pytest.raises(AdapterRegistryError, match="returned write format"):
        WriterRegistry.write(
            BuildSource(),
            BytesIO(),
            format_id="format.write",
        )


# case folding keeps documented aliases portable across adapters and caller conventions
def CheckAliasCase() -> None:
    InfoData = AdapterInfo(
        "format.primary",
        "Primary",
        "1",
        (".primary", ".alias"),
        aliases=("format.alias",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    AdapterData = ResultAdapter(
        InfoData,
        ProbeFormat="FORMAT.ALIAS",
        WriteFormat="Format.Alias",
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(AdapterData)
    SourceData = BuildSource().to_json().encode("utf-8")
    assert RegistryData.select_reader(SourceData) is AdapterData
    ResultData = RegistryData.write(
        BuildSource(),
        BytesIO(),
        format_id="format.primary",
    )
    assert ResultData.adapter == "Format.Alias"


# unsupported document capabilities must fail before a destination receives partial bytes
def CheckLossGate() -> None:
    AdapterData = ResultAdapter(
        AdapterInfo(
            "format.lossy",
            "Lossy",
            "1",
            (".lossy",),
            capabilities=frozenset({Capability.PARAMETRIC_HISTORY}),
        )
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(AdapterData)
    TargetData = BytesIO()
    with Pytest.raises(CapabilityLossError) as ErrorInfo:
        RegistryData.write(BuildSource(), TargetData, format_id="format.lossy")
    assert ErrorInfo.value.dropped
    assert Capability.EDITABLE_SKETCHES in ErrorInfo.value.dropped
    assert TargetData.getvalue() == b""


# native claims stay bounded by preservation support so metadata cannot overpromise output
def CheckNativeCaps() -> None:
    AdapterData = ResultAdapter(
        AdapterInfo(
            "format.invalid-native",
            "Invalid native",
            "1",
            (".invalid",),
            native_capabilities=frozenset({Capability.BREP}),
        )
    )
    with Pytest.raises(AdapterRegistryError, match="preservation capabilities"):
        AdapterRegistry().register(AdapterData)
