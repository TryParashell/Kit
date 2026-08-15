# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Iterable as TypeIterable

from convert.adapters.registry.RegistryDiscover import FindAdapters
from convert.adapters.registry.RegistryErrors import DiscoveryError
from convert.adapters.registry.RegistryRegisterApi import IsReplaceFlag
from convert.adapters.registry.RegistryState import CopyState

# historical iterable annotations need local resolution after public methods move to the registry facade
globals()["Iterable"] = TypeIterable

# built in discovery remains rooted above infrastructure packages after registry became a facade package
KDefaultPackage = "convert.adapters"


# discovery api ownership isolates package introspection from ordinary registry operations
class DiscoveryApi:

    # package failures retain one stable public category while preserving detailed causes
    def Introspect(
        SelfValue,
        PackageName: str = KDefaultPackage,
    ) -> tuple[str, ...]:
        try:
            AdapterValues = FindAdapters(PackageName)
            SelfValue.ExtendAll(AdapterValues)
        except DiscoveryError:
            raise
        except Exception as ErrorInfo:
            raise DiscoveryError(
                f"could not register adapters from {PackageName}"
            ) from ErrorInfo
        return tuple(
            sorted({AdapterData.info.format_id for AdapterData in AdapterValues})
        )


# bulk api ownership isolates all or nothing extension from single adapter registration
class ExtendApi:

    # complete rollback prevents earlier adapters from surviving a later registration failure
    def ExtendAll(
        SelfValue,
        AdapterValues: TypeIterable[object],
        **NamedValues: object,
    ) -> None:
        PriorState = CopyState(SelfValue.BindingMap, SelfValue.AliasMap)
        ReplaceFlag = IsReplaceFlag(NamedValues, "extend")
        try:
            for AdapterData in AdapterValues:
                SelfValue.RegisterOne(AdapterData, ReplaceFlag=ReplaceFlag)
        except Exception:
            SelfValue.BindingMap, SelfValue.AliasMap = PriorState
            raise
