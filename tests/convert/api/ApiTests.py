# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from io import BytesIO as ByteStream
from pathlib import Path as FilePath
from typing import cast as CastValue

import pytest as Pytest

import convert.api.ApiConvert as ApiConvert
import convert.api.ApiWrite as ApiWrite
from convert import ApplicationUsabilityError
from convert import available_adapters as GetAdapters
from convert import convert as ConvertLegacy
from convert import open_document as OpenLegacy
from convert import write_document as WriteLegacy
from convert.adapters import AdapterRegistry
from interchange import Capability
from interchange.document.models.DocumentModel import CadDocument
from tests.convert.api.ApiTestCapture import CaptureEngine
from tests.convert.api.ApiTestPaths import KCatPartPath
from tests.convert.api.ApiTestPaths import KFcstdPath
from tests.convert.api.ApiTestPaths import KSamplePath


# neutral interchange remains mandatory because independent adapters must never call each other
def CheckApiBridge(TmpPath: FilePath) -> None:
    FormatNames = {AdapterData.format_id for AdapterData in GetAdapters()}
    RegistryData = AdapterRegistry()
    RegistryData.introspect()
    assert FormatNames == {
        AdapterData.info.format_id for AdapterData in RegistryData.readers()
    }
    DocumentData = OpenLegacy(KSamplePath)
    OutputPath = TmpPath / "example.json"
    ResultData = ConvertLegacy(KSamplePath, OutputPath)
    assert ResultData.source_format == "solidworks.sldprt"
    assert ResultData.destination_format == "interchange.json"
    assert ResultData.roundtrip_safe is True
    assert ResultData.near_lossless is True
    assert ResultData.dropped == frozenset()
    assert ResultData.requirements == ()
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.output.native_capabilities == frozenset(
        TransferData.capability for TransferData in ResultData.transfers
    )
    assert ResultData.output.carrier_capabilities == frozenset()
    assert OpenLegacy(OutputPath) == DocumentData


# exact replay must stay usable because unchanged native bytes need no carrier translation
@Pytest.mark.parametrize(
    ("SourcePath", "FileName"),
    (
        (KSamplePath, "exact.SLDPRT"),
        (KFcstdPath, "exact.FCStd"),
        (KCatPartPath, "exact.CATPart"),
    ),
)
def CheckExactSwap(
    SourcePath: FilePath,
    FileName: str,
    TmpPath: FilePath,
) -> None:
    if not SourcePath.is_file():
        Pytest.skip(f"bundled exact replay fixture is unavailable: {SourcePath.name}")
    TargetPath = TmpPath / FileName
    ResultData = ConvertLegacy(SourcePath, TargetPath)
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.requirements == ()
    assert ResultData.dropped == frozenset()
    assert ResultData.output.native_capabilities
    assert ResultData.output.path == TargetPath.resolve()


# reversible carriers remain available because portable swaps must preserve unsupported semantics
def CheckCarryOut(TmpPath: FilePath) -> None:
    TargetPath = TmpPath / "portable.CATPart"
    ResultData = ConvertLegacy(KSamplePath, TargetPath)
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is False
    assert ResultData.near_lossless is False
    assert ResultData.roundtrip_safe is True
    assert ResultData.requirements == ()
    assert ResultData.dropped == frozenset()
    assert ResultData.output.carrier_capabilities
    assert TargetPath.is_file()


# strict mode must reject carrier output because callers explicitly require application usability
def CheckStrictGate(TmpPath: FilePath) -> None:
    TargetPath = TmpPath / "blocked.CATPart"
    with Pytest.raises(ApplicationUsabilityError) as CapturedError:
        ConvertLegacy(KSamplePath, TargetPath, allow_carrier=False)
    assert CapturedError.value.code == "output_not_application_usable"
    assert CapturedError.value.format_id == "catia.v5"
    assert "carrier_only" in CapturedError.value.issues
    assert not TargetPath.exists()
    assert tuple(TmpPath.iterdir()) == ()


# direct document writes need the same usability policy as one step conversions
def CheckWriteGate(TmpPath: FilePath) -> None:
    DocumentData = OpenLegacy(KSamplePath)
    TargetPath = TmpPath / "portable.CATPart"
    ResultData = WriteLegacy(DocumentData, TargetPath)
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is False
    assert ResultData.requirements == ()
    assert ResultData.dropped == frozenset()
    StrictPath = TmpPath / "blocked.CATPart"
    with Pytest.raises(ApplicationUsabilityError):
        WriteLegacy(DocumentData, StrictPath, allow_carrier=False)
    assert not StrictPath.exists()


# public options must override conflicting user values so runtime output stays self contained
def CheckForcedVals(MonkeyPatch: Pytest.MonkeyPatch) -> None:
    CapturedVals: list[dict[str, object]] = []
    SentinelValue = object()
    EngineValue = CaptureEngine(CapturedVals, SentinelValue)
    MonkeyPatch.setattr(ApiWrite, "KConvertEngine", EngineValue)
    MonkeyPatch.setattr(ApiConvert, "KConvertEngine", EngineValue)
    assert id(
        WriteLegacy(
            CastValue(CadDocument, object()),
            ByteStream(),
            values={"require_self_contained": False},
        )
    ) == id(SentinelValue)
    assert id(
        ConvertLegacy(
            b"source",
            ByteStream(),
            write_values={"require_self_contained": False},
        )
    ) == id(SentinelValue)
    assert len(CapturedVals) == 2
    assert all(ValueData["portable"] is True for ValueData in CapturedVals)
    assert all(ValueData["allow_carrier"] is True for ValueData in CapturedVals)
    assert all(
        ValueData["require_self_contained"] is True for ValueData in CapturedVals
    )


# carrier reporting must distinguish preserved opaque semantics from native target capabilities
def CheckCarryMode(TmpPath: FilePath) -> None:
    ResultData = ConvertLegacy(
        KSamplePath,
        TmpPath / "example.CATPart",
        allow_carrier=True,
    )
    assert ResultData.roundtrip_safe is True
    assert ResultData.dropped == frozenset()
    assert ResultData.requirements == ()
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is False
    assert ResultData.output.native_capabilities == frozenset()
    assert (
        ResultData.output.carrier_capabilities
        == ResultData.output.transferred_capabilities
    )


# native replay reporting must attribute every preserved capability to the target format
def CheckNativeMode(TmpPath: FilePath) -> None:
    TargetPath = TmpPath / "example.SLDPRT"
    ResultData = ConvertLegacy(KSamplePath, TargetPath)
    assert TargetPath.read_bytes() == KSamplePath.read_bytes()
    assert ResultData.roundtrip_safe is True
    assert ResultData.dropped == frozenset()
    assert ResultData.requirements == ()
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.output.metadata["mode"] == "exact"
    assert ResultData.output.metadata["compatibility"] == "native-exact"
    assert (
        ResultData.output.native_capabilities
        == ResultData.output.transferred_capabilities
    )
    assert ResultData.output.carrier_capabilities == frozenset()


# tessellation selection stays public because callers may avoid large display payloads
def CheckTessellate() -> None:
    WithoutMesh = OpenLegacy(
        KCatPartPath,
        include_brep=False,
        include_tessellation=False,
    )
    WithMesh = OpenLegacy(
        KCatPartPath,
        include_brep=False,
        include_tessellation=True,
    )
    assert Capability.KTessellation not in WithoutMesh.Capabilities
    assert Capability.KTessellation in WithMesh.Capabilities
