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

import pytest as Pytest

from convert.adapters import (
    AdapterInfo,
    AdapterRegistry,
    ApplicationUsabilityError,
    CarrierReason,
    CapabilityTransfer,
    ReadOptions,
    TransferMode,
    WriteOptions,
    WriteResult,
)
from convert.engine import ConversionEngine
from interchange import Capability
from tests.convert.registry_test_support import BuildSource, ResultAdapter


# source identity must retain an adapters reported alias rather than caller normalization
def CheckSrcAlias() -> None:
    InfoData = AdapterInfo(
        "format.canonical",
        "Canonical",
        "1",
        (".canonical",),
        aliases=("format.alias",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    AdapterData = ResultAdapter(InfoData)
    RegistryData = AdapterRegistry()
    RegistryData.register(AdapterData)
    SourceData = BuildSource()
    SourceData = ReplaceValue(
        SourceData,
        source=ReplaceValue(SourceData.source, format_id="FORMAT.ALIAS"),
    )
    ResultData = ConversionEngine(RegistryData).convert(
        SourceData.to_json().encode("utf-8"),
        BytesIO(),
        source_format="format.alias",
        destination_format="format.canonical",
        read_options=ReadOptions(include_tessellation=True),
    )
    assert ResultData.source_format == "FORMAT.ALIAS"


# default reads preserve every available representation unless callers opt out explicitly
def CheckReadOpts() -> None:
    OptionsData = ReadOptions()
    assert OptionsData.include_brep is True
    assert OptionsData.include_tessellation is True


# roundtrip safety reports only capability loss while usability remains independently truthful
def CheckSafety() -> None:
    ResultData = WriteResult(
        None,
        "format.empty",
        0,
        requirements=("companion file",),
    )
    assert ResultData.transfers == ()
    assert ResultData.dropped == frozenset()
    assert ResultData.roundtrip_safe is True
    assert ResultData.near_lossless is False
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is False


# metadata cannot contradict typed usability fields because consumers trust both representations
@Pytest.mark.parametrize(
    ("MetadataMap", "FieldValues"),
    (
        ({"application_usable": True}, {"application_usable": False}),
        ({"vendor_loadable": True}, {"vendor_loadable": False}),
    ),
)
def CheckMetaRule(
    MetadataMap: dict[str, bool],
    FieldValues: dict[str, bool],
) -> None:
    with Pytest.raises(ValueError, match="contradicts the write result"):
        WriteResult(
            None,
            "format.contradictory",
            0,
            metadata=MetadataMap,
            **FieldValues,
        )


# application usability implies vendor loading because unusable vendor output cannot satisfy that claim
def CheckUsableRule() -> None:
    with Pytest.raises(ValueError, match="must be vendor-loadable"):
        WriteResult(
            None,
            "format.impossible",
            0,
            application_usable=True,
            vendor_loadable=False,
        )


# native and carrier projections both include mixed transfers for truthful preservation views
def CheckMixedViews() -> None:
    ResultData = WriteResult(
        None,
        "format.mixed",
        1,
        transfers=(
            CapabilityTransfer(
                Capability.PARAMETRIC_HISTORY,
                TransferMode.MIXED,
            ),
        ),
        application_usable=True,
        vendor_loadable=True,
    )
    ExpectedCaps = frozenset({Capability.PARAMETRIC_HISTORY})
    assert ResultData.native_capabilities == ExpectedCaps
    assert ResultData.carrier_capabilities == ExpectedCaps


# carrier opt in must never rewrite factual usability evidence from an adapter result
def CheckCarFacts() -> None:
    InfoData = AdapterInfo(
        "format.claimed-carrier",
        "Claimed carrier",
        "1",
        (".carrier",),
        capabilities=frozenset(Capability),
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(ResultAdapter(InfoData))
    ResultData = RegistryData.write(
        BuildSource(),
        BytesIO(),
        format_id=InfoData.format_id,
        options=WriteOptions(values={"allow_carrier": True}),
    )
    assert ResultData.native_capabilities == frozenset()
    assert ResultData.carrier_capabilities == ResultData.transferred_capabilities
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is False
    assert ResultData.metadata["application_usable"] is False
    assert ResultData.metadata["vendor_loadable"] is False


# independent flags distinguish vendor readability from complete application usability
class LoadableAdapter(ResultAdapter):

    # partial usability evidence exercises the registrys independent field preservation
    def WriteData(
        SelfValue,
        DocumentData,
        TargetData,
        OptionsData=None,
    ) -> WriteResult:
        return ReplaceValue(
            super().WriteData(DocumentData, TargetData, OptionsData),
            application_usable=False,
            vendor_loadable=True,
        )


setattr(LoadableAdapter, "write", LoadableAdapter.WriteData)


# registry policy must preserve truthful independent usability fields from writers
def CheckFieldTruth() -> None:
    InfoData = AdapterInfo(
        "format.loadable-unusable",
        "Loadable but unusable",
        "1",
        (".loadable",),
        capabilities=frozenset(Capability),
        native_capabilities=frozenset(Capability),
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(LoadableAdapter(InfoData))
    ResultData = RegistryData.write(
        BuildSource(),
        BytesIO(),
        format_id=InfoData.format_id,
        options=WriteOptions(values={"allow_carrier": True}),
    )
    assert ResultData.application_usable is False
    assert ResultData.vendor_loadable is True
    assert ResultData.near_lossless is False


# structured failures need stable wire fields so api clients never parse exception messages
def CheckErrorMap() -> None:
    InfoData = AdapterInfo(
        "format.carrier",
        "Carrier",
        "1",
        (".carrier",),
        capabilities=frozenset(Capability),
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(ResultAdapter(InfoData))
    with Pytest.raises(ApplicationUsabilityError) as ErrorInfo:
        RegistryData.write(BuildSource(), BytesIO(), format_id=InfoData.format_id)
    ErrorData = ErrorInfo.value
    assert ErrorData.code == "output_not_application_usable"
    assert ErrorData.issues == (
        "application_unusable",
        "vendor_unloadable",
        "carrier_only",
        "unimplemented_translation",
    )
    PayloadData = ErrorData.to_dict()
    assert PayloadData["format_id"] == InfoData.format_id
    assert PayloadData["issues"] == ErrorData.issues
    assert PayloadData["application_usable"] is False
    assert PayloadData["vendor_loadable"] is False
    assert PayloadData["requirements"] == ()
    assert PayloadData["dropped"] == ()
    assert PayloadData["source_opaque_capabilities"] == ()
    assert set(PayloadData["unimplemented_capabilities"]) == {
        CapabilityData.value for CapabilityData in ErrorData.carrier_capabilities
    }
    assert set(PayloadData["carrier_reasons"].values()) == {
        CarrierReason.WRITER_UNIMPLEMENTED.value
    }
