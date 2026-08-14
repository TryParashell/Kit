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
from typing import Any as AnyValue

import pytest as Pytest

from convert.adapters import (
    AdapterInfo,
    AdapterRegistry,
    ApplicationUsabilityError,
    CarrierReason,
    CapabilityTransfer,
    TransferMode,
    WriteResult,
)
from interchange import CadDocument, Capability, InferCaps
from tests.convert.registry.RegistryTestSupport import BuildSource, ResultAdapter


# one sorted capability view keeps transfer fixtures deterministic across hash seeds
def GetCapabilities(DocumentData: CadDocument) -> tuple[Capability, ...]:
    ReturnCaps = DocumentData.capabilities | InferCaps(
        DocumentData,
        RoundtripMeta=Capability.ROUNDTRIP_METADATA in DocumentData.capabilities,
    )

    # capability wire names provide stable ordering for transfer assertions across runs
    return tuple(sorted(ReturnCaps, key=lambda CapabilityData: CapabilityData.value))


# writer gaps remain explicit carriers so default policy can reject incomplete translation
class MixedAdapter(ResultAdapter):

    # one native transfer plus writer gaps exercises mixed preservation without capability loss
    def WriteData(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: AnyValue,
        OptionsData: AnyValue = None,
    ) -> WriteResult:
        ResultData = super().WriteData(DocumentData, TargetData, OptionsData)
        TransferValues = tuple(
            CapabilityTransfer(
                CapabilityData,
                TransferMode.NATIVE if IndexValue == 0 else TransferMode.CARRIER,
            )
            for IndexValue, CapabilityData in enumerate(GetCapabilities(DocumentData))
        )
        return ReplaceValue(
            ResultData,
            transfers=TransferValues,
            application_usable=True,
            vendor_loadable=True,
        )


setattr(MixedAdapter, "write", MixedAdapter.WriteData)


# default policy rejects writer gaps even when resulting bytes are vendor loadable
def CheckWriterGap() -> None:
    InfoData = AdapterInfo(
        "format.mixed-gap",
        "Mixed gap",
        "1",
        (".mixed",),
        capabilities=frozenset(Capability),
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(MixedAdapter(InfoData))
    TargetData = BytesIO()
    with Pytest.raises(ApplicationUsabilityError) as ErrorInfo:
        RegistryData.write(BuildSource(), TargetData, format_id=InfoData.format_id)
    assert TargetData.getvalue() == b""
    assert ErrorInfo.value.application_usable is True
    assert ErrorInfo.value.vendor_loadable is True
    assert "unimplemented_translation" in ErrorInfo.value.issues
    assert ErrorInfo.value.unimplemented_capabilities


# target format limits remain truthful reversible carriers rather than implementation gaps
class TargetAdapter(ResultAdapter):

    # native seed plus intrinsic carriers proves near losslessness accepts target limitations
    def WriteData(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: AnyValue,
        OptionsData: AnyValue = None,
    ) -> WriteResult:
        ResultData = super().WriteData(DocumentData, TargetData, OptionsData)
        TransferValues = tuple(
            CapabilityTransfer(
                CapabilityData,
                TransferMode.NATIVE if IndexValue == 0 else TransferMode.CARRIER,
                None if IndexValue == 0 else CarrierReason.TARGET_UNSUPPORTED,
            )
            for IndexValue, CapabilityData in enumerate(GetCapabilities(DocumentData))
        )
        return ReplaceValue(
            ResultData,
            transfers=TransferValues,
            application_usable=True,
            vendor_loadable=True,
        )


setattr(TargetAdapter, "write", TargetAdapter.WriteData)


# intrinsic target limitations remain acceptable when output is usable and reversible
def CheckTargetGap() -> None:
    InfoData = AdapterInfo(
        "format.target-limited",
        "Target limited",
        "1",
        (".limited",),
        capabilities=frozenset(Capability),
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(TargetAdapter(InfoData))
    TargetData = BytesIO()
    ResultData = RegistryData.write(
        BuildSource(),
        TargetData,
        format_id=InfoData.format_id,
    )
    assert TargetData.getvalue()
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.carrier_capabilities
    assert ResultData.near_lossless is True
    assert all(
        TransferData.carrier_reason is CarrierReason.TARGET_UNSUPPORTED
        for TransferData in ResultData.transfers
        if TransferData.mode is TransferMode.CARRIER
    )


# carrier only target limits model formats with no native representation for this document
class OnlyCarrier(ResultAdapter):

    # every intrinsic carrier proves native emptiness alone does not make usable output invalid
    def WriteData(
        SelfValue,
        DocumentData: CadDocument,
        TargetData: AnyValue,
        OptionsData: AnyValue = None,
    ) -> WriteResult:
        ResultData = super().WriteData(DocumentData, TargetData, OptionsData)
        TransferValues = tuple(
            CapabilityTransfer(
                CapabilityData,
                TransferMode.CARRIER,
                CarrierReason.TARGET_UNSUPPORTED,
            )
            for CapabilityData in GetCapabilities(DocumentData)
        )
        return ReplaceValue(
            ResultData,
            transfers=TransferValues,
            application_usable=True,
            vendor_loadable=True,
        )


setattr(OnlyCarrier, "write", OnlyCarrier.WriteData)


# usable carrier only documents remain near lossless when every carrier is intrinsic
def CheckOnlyCar() -> None:
    InfoData = AdapterInfo(
        "format.target-empty",
        "Target empty",
        "1",
        (".empty",),
        capabilities=frozenset(Capability),
    )
    RegistryData = AdapterRegistry()
    RegistryData.register(OnlyCarrier(InfoData))
    TargetData = BytesIO()
    ResultData = RegistryData.write(
        BuildSource(),
        TargetData,
        format_id=InfoData.format_id,
    )
    assert TargetData.getvalue()
    assert ResultData.native_capabilities == frozenset()
    assert ResultData.carrier_capabilities == ResultData.transferred_capabilities
    assert ResultData.application_usable is True
    assert ResultData.vendor_loadable is True
    assert ResultData.near_lossless is True
