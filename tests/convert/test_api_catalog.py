# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from inspect import isabstract as IsAbstract

import pytest as Pytest

from convert import available_adapters as GetAdapters
from convert.adapters import AdapterInfo, AdapterRegistry
from interchange import Capability
from tests.convert.api_test_helpers import GetPackNames, ListFormatPacks


# deterministic introspection prevents import order from changing the public format catalog
def CheckDiscovery() -> None:
    PackageNames = ListFormatPacks()
    FirstRegistry = AdapterRegistry()
    FirstIds = FirstRegistry.introspect()
    SecondRegistry = AdapterRegistry()
    SecondIds = SecondRegistry.introspect()
    ReaderValues = FirstRegistry.readers()
    WriterValues = FirstRegistry.writers()
    assert PackageNames
    assert GetPackNames(ReaderValues, PackageNames) == set(PackageNames)
    assert GetPackNames(WriterValues, PackageNames) == set(PackageNames)
    assert FirstIds == SecondIds == tuple(sorted(FirstIds))
    assert tuple(ValueData.info.format_id for ValueData in ReaderValues) == FirstIds
    assert tuple(ValueData.info.format_id for ValueData in WriterValues) == FirstIds
    for AdapterData in ReaderValues:
        for FormatId in (AdapterData.info.format_id, *AdapterData.info.aliases):
            assert FirstRegistry.reader(FormatId) is AdapterData
    for AdapterData in WriterValues:
        for FormatId in (AdapterData.info.format_id, *AdapterData.info.aliases):
            assert FirstRegistry.writer(FormatId) is AdapterData
    assert FirstRegistry.introspect() == FirstIds
    assert FirstRegistry.readers() == ReaderValues
    assert FirstRegistry.writers() == WriterValues
    assert all(
        not IsAbstract(type(AdapterData))
        and not getattr(type(AdapterData), "_is_protocol", False)
        for AdapterData in (*ReaderValues, *WriterValues)
    )
    assert all(
        AdapterData.info.capabilities == frozenset(Capability)
        for AdapterData in (*ReaderValues, *WriterValues)
    )


# document kind extensions remain introspective so clients need no format specific branches
def CheckDocExts() -> None:
    AdapterMap = {InfoData.format_id: InfoData for InfoData in GetAdapters()}
    assert AdapterMap["solidworks.sldprt"].part_extensions == (".sldprt",)
    assert AdapterMap["solidworks.sldprt"].assembly_extensions == (".sldasm",)
    assert AdapterMap["catia.v5"].part_extensions == (".catpart",)
    assert AdapterMap["catia.v5"].assembly_extensions == (".catproduct",)
    assert AdapterMap["freecad.fcstd"].part_extensions == (".FCStd",)
    assert AdapterMap["freecad.fcstd"].assembly_extensions == (".FCStd",)
    for InfoData in AdapterMap.values():
        assert set(InfoData.extensions_for(assembly=False)) <= set(InfoData.extensions)
        assert set(InfoData.extensions_for(assembly=True)) <= set(InfoData.extensions)
    with Pytest.raises(TypeError):
        AdapterMap["freecad.fcstd"].extensions_for(assembly=1)
    AssemblyInfo = AdapterInfo(
        "format.assembly-only",
        "Assembly only",
        "1",
        (".assembly",),
        assembly_extensions=(".assembly",),
    )
    assert AssemblyInfo.extensions_for(assembly=False) == ()
    assert AssemblyInfo.extensions_for(assembly=True) == (".assembly",)
