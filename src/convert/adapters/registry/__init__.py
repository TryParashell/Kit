# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from typing import Iterable as TypeIterable

from interchange import CadDocument as KCadDocument

from convert.adapters.base.AdapterProtocols import CadReaderAdapter as KCadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter as KCadWriterAdapter
from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.ReadOptions import ReadOptions as KReadOptions
from convert.adapters.registry.RegistryBinding import AdapterBinding
from convert.adapters.registry.RegistryCatalogApi import FormatCatalog
from convert.adapters.registry.RegistryCatalogApi import ReaderCatalog
from convert.adapters.registry.RegistryCatalogApi import WriterCatalog
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
from convert.adapters.base.WriteOptions import WriteOptions as KWriteOptions
from convert.adapters.base.WriteResult import WriteResult as KWriteResult

# historical reader annotations need resolution after bindings move behind this compatibility facade
CadReaderAdapter = KCadReaderAdapter

# historical writer annotations need resolution after bindings move behind this compatibility facade
CadWriterAdapter = KCadWriterAdapter

# historical source annotations need resolution after methods move behind this compatibility facade
Source = KSourceType

# historical destination annotations need resolution after methods move behind this compatibility facade
Destination = KTargetType

# historical read option annotations need resolution after methods move behind this compatibility facade
ReadOptions = KReadOptions

# historical write option annotations need resolution after methods move behind this compatibility facade
WriteOptions = KWriteOptions

# historical result annotations need resolution after methods move behind this compatibility facade
WriteResult = KWriteResult

# historical document annotations need resolution after methods move behind this compatibility facade
CadDocument = KCadDocument

# historical iterable annotations need resolution after methods move behind this compatibility facade
Iterable = TypeIterable


# registry composition keeps each independent responsibility in one focused mixin module
class AdapterRegistry(
    BindingApi,
    RegisterApi,
    ExtendApi,
    DiscoveryApi,
    ReaderCatalog,
    WriterCatalog,
    FormatCatalog,
    ReadSelectApi,
    ReadApi,
    WriteSelectApi,
    WriteApi,
):
    BindingMap: dict[str, AdapterBinding]
    AliasMap: dict[str, str]

    # empty isolated state supports independent applications tests and transactional discovery
    def __init__(self) -> None:
        self.BindingMap = {}
        self.AliasMap = {}

    # public registration keeps the historical reader spelling statically visible
    def register_reader(
        self,
        adapter: CadReaderAdapter,
        *,
        replace: bool = False,
    ) -> None:
        self.RegisterReader(adapter, ReplaceFlag=replace)

    # public registration keeps the historical writer spelling statically visible
    def register_writer(
        self,
        adapter: CadWriterAdapter,
        *,
        replace: bool = False,
    ) -> None:
        self.RegisterWriter(adapter, ReplaceFlag=replace)

    # public registration accepts either adapter direction without runtime alias installation
    def register(
        self,
        adapter: object,
        *,
        replace: bool = False,
    ) -> None:
        self.RegisterOne(adapter, ReplaceFlag=replace)

    # discovery stays public because callers can populate registries from alternate packages
    def introspect(self, package_name: str = "convert.adapters") -> tuple[str, ...]:
        return self.Introspect(package_name)

    # reader enumeration exposes the established lower case registry contract
    def readers(self) -> tuple[CadReaderAdapter, ...]:
        return self.GetReaders()

    # writer enumeration exposes the established lower case registry contract
    def writers(self) -> tuple[CadWriterAdapter, ...]:
        return self.GetWriters()

    # reader lookup retains the lower case contract used by direct integrations
    def reader(self, format_id: str) -> CadReaderAdapter:
        return self.GetReader(format_id)

    # writer lookup retains the lower case contract used by direct integrations
    def writer(self, format_id: str) -> CadWriterAdapter:
        return self.GetWriter(format_id)

    # reader selection remains callable through its historical lower case surface
    def select_reader(self, source: Source) -> CadReaderAdapter:
        return self.PickReader(source)

    # writer selection remains callable through its historical lower case surface
    def select_writer(
        self,
        document: CadDocument,
        destination: Destination,
    ) -> CadWriterAdapter:
        return self.PickWriter(document, destination)

    # document reads expose concrete keyword fields for static api consumers
    def read(
        self,
        source: Source,
        *,
        format_id: str | None = None,
        options: ReadOptions | None = None,
    ) -> CadDocument:
        return self.ReadDocument(source, FormatId=format_id, OptionsData=options)

    # adapter aware reads expose both stable document and reader contracts
    def read_with_adapter(
        self,
        source: Source,
        *,
        format_id: str | None = None,
        options: ReadOptions | None = None,
    ) -> tuple[CadDocument, CadReaderAdapter]:
        return self.ReadAdapter(source, FormatId=format_id, OptionsData=options)

    # document writes expose concrete keyword fields for static api consumers
    def write(
        self,
        document: CadDocument,
        destination: Destination,
        *,
        format_id: str | None = None,
        options: WriteOptions | None = None,
    ) -> WriteResult:
        return self.WriteDocument(
            document, destination, FormatId=format_id, OptionsData=options
        )

    # format inspection remains public without exposing normalized map implementation details
    def format_ids(self) -> tuple[str, ...]:
        return self.GetFormatIds()

    # bulk registration keeps rollback behavior while accepting the historical lower case keywords
    def extend(self, adapters: Iterable[object], *, replace: bool = False) -> None:
        self.ExtendAll(adapters, ReplaceFlag=replace)


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
