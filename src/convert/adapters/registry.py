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

from .adapter_protocols import CadReaderAdapter
from .adapter_protocols import CadWriterAdapter
from .contract_types import KSourceType
from .contract_types import KTargetType
from .read_options import ReadOptions
from .registry_binding import AdapterBinding
from .registry_catalog_api import FormatCatalog
from .registry_catalog_api import ReaderCatalog
from .registry_catalog_api import WriterCatalog
from .registry_compat import SetExtendSigMut
from .registry_compat import InstallApiMut
from .registry_compat import SetReadSigsMut
from .registry_compat import SetRegSigsMut
from .registry_compat import SetWriteSigMut
from .registry_discovery_api import DiscoveryApi
from .registry_discovery_api import ExtendApi
from .registry_errors import AdapterDiscoveryError
from .registry_errors import AdapterNotFoundError
from .registry_errors import AdapterRegistryError
from .registry_errors import AmbiguousAdapterError
from .registry_errors import CapabilityLossError
from .registry_read_api import ReadApi
from .registry_read_api import ReadSelectApi
from .registry_register_api import BindingApi
from .registry_register_api import RegisterApi
from .registry_write_api import WriteApi
from .registry_write_api import WriteSelectApi
from .usability_error import ApplicationUsabilityError
from .write_options import WriteOptions
from .write_result import WriteResult

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
