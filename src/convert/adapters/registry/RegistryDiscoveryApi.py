# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Iterable as TypeIterable
from typing import Protocol

from convert.adapters.registry.RegistryDiscover import FindAdapters
from convert.adapters.registry.RegistryBinding import AdapterBinding
from convert.adapters.registry.RegistryErrors import DiscoveryError
from convert.adapters.registry.RegistryRegisterApi import IsReplaceFlag
from convert.adapters.registry.RegistryState import CopyState
from convert.adapters.registry.RegistryState import RegistryHost

# historical iterable annotations need local resolution after public methods move to the registry facade
Iterable = TypeIterable

# built in discovery remains rooted above infrastructure packages after registry became a facade package
KDefaultPackage = "convert.adapters"


# discovery api ownership isolates package introspection from ordinary registry operations
# discovery composition needs only the typed bulk registration boundary
class DiscoveryHost(Protocol):

    # package discovery delegates mutation so transaction policy remains centralized
    def ExtendAll(
        self,
        AdapterValues: TypeIterable[object],
        **NamedValues: object,
    ) -> None: ...  # lgtm[py/ineffectual-statement]


# discovery api ownership isolates package introspection from ordinary registry operations
class DiscoveryApi(DiscoveryHost):

    # package failures retain one stable public category while preserving detailed causes
    def Introspect(
        self,
        PackageName: str = KDefaultPackage,
    ) -> tuple[str, ...]:
        try:
            AdapterValues = FindAdapters(PackageName)
            self.ExtendAll(AdapterValues)
        except DiscoveryError:
            raise
        except Exception as ErrorInfo:
            raise DiscoveryError(
                f"could not register adapters from {PackageName}"
            ) from ErrorInfo
        return tuple(
            sorted({AdapterData.info.FormatId for AdapterData in AdapterValues})
        )


# bulk api ownership isolates all or nothing extension from single adapter registration
# bulk composition needs typed state plus the single adapter registration boundary
class ExtendHost(RegistryHost, Protocol):

    # bulk registration delegates each validated item through one transactional operation
    def RegisterOne(
        self,
        AdapterData: object,
        **NamedValues: object,
    ) -> None: ...  # lgtm[py/ineffectual-statement]


# bulk api ownership isolates all or nothing extension from single adapter registration
class ExtendApi(ExtendHost):
    BindingMap: dict[str, AdapterBinding]
    AliasMap: dict[str, str]

    # complete rollback prevents earlier adapters from surviving a later registration failure
    def ExtendAll(
        self,
        AdapterValues: TypeIterable[object],
        **NamedValues: object,
    ) -> None:
        PriorState = CopyState(self.BindingMap, self.AliasMap)
        ReplaceFlag = IsReplaceFlag(NamedValues, "extend")
        try:
            for AdapterData in AdapterValues:
                self.RegisterOne(AdapterData, ReplaceFlag=ReplaceFlag)
        except Exception:
            self.BindingMap, self.AliasMap = PriorState
            raise
