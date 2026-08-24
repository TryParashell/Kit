# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from pathlib import Path as FilePath
from typing import Mapping as TypeMap

from interchange import Capability
from interchange import Diagnostic
from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.CapabilityView import CapabilityView
from convert.adapters.base.ContractCompat import ContractBase
from convert.adapters.base.ResultOutputs import ResultOutputs
from convert.adapters.base.ResultPolicy import ResultPolicy
from convert.adapters.base.TransferContract import CapTransfer
from convert.adapters.base.WriteValidate import CheckDropped
from convert.adapters.base.WriteValidate import CheckNeeds
from convert.adapters.base.WriteValidate import CheckTransfers
from convert.adapters.base.WriteValidate import CheckUsability


# construction rejects contradictory evidence before registry policy can trust it
def CheckResult(SelfValue: WriteResult) -> None:
    if SelfValue.bytes_written < 0:
        raise ValueError("bytes written cannot be negative")
    CheckDropped(SelfValue.dropped)
    CheckTransfers(SelfValue.transfers, SelfValue.dropped)
    CheckNeeds(SelfValue.requirements)
    CheckUsability(
        SelfValue.application_usable,
        SelfValue.vendor_loadable,
        SelfValue.metadata,
    )


# writer outcomes centralize transactional output and preservation evidence for callers
@DataClass(frozen=True, slots=True)
class WriteResult(ResultOutputs, ResultPolicy, CapabilityView, ContractBase):
    path: FilePath | None
    adapter: str
    bytes_written: int
    diagnostics: tuple[Diagnostic, ...] = ()
    metadata: TypeMap[str, object] = DataField(default_factory=FreezeMapping)
    transfers: tuple[CapTransfer, ...] = ()
    dropped: frozenset[Capability] = frozenset()
    requirements: tuple[str, ...] = ()
    application_usable: bool = False
    vendor_loadable: bool = False

    # construction rejects contradictory evidence before registry policy can trust it
    def __post_init__(self) -> None:
        CheckResult(self)

    # legacy callers need losslessness policy exposed as a typed predicate
    @property
    def near_lossless(self) -> bool:
        return self.IsNearLossless

    # legacy callers need the full transferred capability set without reflection
    @property
    def transferred_capabilities(self) -> frozenset[Capability]:
        return self.TransferCaps

    # legacy callers need native capability accounting without reflection
    @property
    def native_capabilities(self) -> frozenset[Capability]:
        return self.NativeCaps

    # legacy callers need carrier capability accounting without reflection
    @property
    def carrier_capabilities(self) -> frozenset[Capability]:
        return self.CarrierCaps
