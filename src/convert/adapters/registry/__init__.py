# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Iterable as TypeIterable

from interchange import CadDocument

from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.registry.RegistryBinding import AdapterBinding
from convert.adapters.registry.RegistryCatalogApi import FormatCatalog
from convert.adapters.registry.RegistryCatalogApi import ReaderCatalog
from convert.adapters.registry.RegistryCatalogApi import WriterCatalog
from convert.adapters.registry.RegistryCompat import SetExtendSigMut
from convert.adapters.registry.RegistryCompat import InstallApiMut
from convert.adapters.registry.RegistryCompat import SetReadSigsMut
from convert.adapters.registry.RegistryCompat import SetRegSigsMut
from convert.adapters.registry.RegistryCompat import SetWriteSigMut
from convert.adapters.registry.RegistryDiscoveryApi import DiscoveryApi
from convert.adapters.registry.RegistryDiscoveryApi import ExtendApi
from convert.adapters.registry.RegistryErrors import AdapterDiscoveryError
from convert.adapters.registry.RegistryErrors import AdapterNotFoundError
from convert.adapters.registry.RegistryErrors import AdapterRegistryError
from convert.adapters.registry.RegistryErrors import AmbiguousAdapterError
from convert.adapters.registry.RegistryErrors import CapabilityLossError
from convert.adapters.registry.RegistryReadApi import ReadApi
from convert.adapters.registry.RegistryReadApi import ReadSelectApi
from convert.adapters.registry.RegistryRegisterApi import BindingApi
from convert.adapters.registry.RegistryRegisterApi import RegisterApi
from convert.adapters.registry.RegistryWriteApi import WriteApi
from convert.adapters.registry.RegistryWriteApi import WriteSelectApi
from convert.adapters.base.UsabilityError import ApplicationUsabilityError
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult

# historical reader annotations need resolution after bindings move behind this compatibility facade
globals()["CadReaderAdapter"] = CadReaderAdapter

# historical writer annotations need resolution after bindings move behind this compatibility facade
globals()["CadWriterAdapter"] = CadWriterAdapter

# historical source annotations need resolution after methods move behind this compatibility facade
globals()["Source"] = KSourceType

# historical destination annotations need resolution after methods move behind this compatibility facade
globals()["Destination"] = KTargetType

# historical read option annotations need resolution after methods move behind this compatibility facade
globals()["ReadOptions"] = ReadOptions

# historical write option annotations need resolution after methods move behind this compatibility facade
globals()["WriteOptions"] = WriteOptions

# historical result annotations need resolution after methods move behind this compatibility facade
globals()["WriteResult"] = WriteResult

# historical document annotations need resolution after methods move behind this compatibility facade
globals()["CadDocument"] = CadDocument

# historical iterable annotations need resolution after methods move behind this compatibility facade
globals()["Iterable"] = TypeIterable


# registry composition keeps each independent responsibility in one focused mixin module
class AdapterRegistry(
    BindingApi,
    RegisterApi,
    DiscoveryApi,
    ExtendApi,
    ReaderCatalog,
    WriterCatalog,
    FormatCatalog,
    ReadSelectApi,
    ReadApi,
    WriteSelectApi,
    WriteApi,
):

    # empty isolated state supports independent applications tests and transactional discovery
    def __init__(SelfValue) -> None:
        SelfValue.BindingMap: dict[str, AdapterBinding] = {}
        SelfValue.AliasMap: dict[str, str] = {}


InstallApiMut(AdapterRegistry)
SetRegSigsMut(AdapterRegistry)
SetReadSigsMut(AdapterRegistry)
SetWriteSigMut(AdapterRegistry)
SetExtendSigMut(AdapterRegistry)

for PublicType, PublicName in (
    (AdapterBinding, "AdapterBinding"),
    (AdapterDiscoveryError, "AdapterDiscoveryError"),
    (AdapterNotFoundError, "AdapterNotFoundError"),
    (AdapterRegistryError, "AdapterRegistryError"),
    (AmbiguousAdapterError, "AmbiguousAdapterError"),
    (CapabilityLossError, "CapabilityLossError"),
    (ApplicationUsabilityError, "ApplicationUsabilityError"),
):
    setattr(PublicType, "__name__", PublicName)
    setattr(PublicType, "__qualname__", PublicName)
    setattr(PublicType, "__module__", __name__)
