# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceData
from pathlib import Path as FilePath

import pytest as Pytest

from convert.adapters import AdapterDiscoveryError
from convert.adapters import AdapterRegistry, AdapterRegistryError
from convert.adapters.json import JsonAdapter


# empty format packages must fail because silent omission would make catalog coverage misleading
def CheckEmptyPack(TmpPath: FilePath, MonkeyPatch: Pytest.MonkeyPatch) -> None:
    PackageName = f"kit_empty_{TmpPath.name.replace('-', '_')}"
    PackagePath = TmpPath / PackageName
    FormatPath = PackagePath / "empty"
    FormatPath.mkdir(parents=True)
    (PackagePath / "__init__.py").write_text("", encoding="utf-8")
    (FormatPath / "__init__.py").write_text("__all__ = []\n", encoding="utf-8")
    MonkeyPatch.syspath_prepend(str(TmpPath))
    with Pytest.raises(AdapterDiscoveryError, match="contains no adapter"):
        AdapterRegistry().introspect(PackageName)


# discovery must inspect package contents because export lists are optional implementation details
def CheckHiddenPack(TmpPath: FilePath, MonkeyPatch: Pytest.MonkeyPatch) -> None:
    PackageName = f"kit_hidden_{TmpPath.name.replace('-', '_')}"
    PackagePath = TmpPath / PackageName
    FormatPath = PackagePath / "hidden"
    FormatPath.mkdir(parents=True)
    (PackagePath / "__init__.py").write_text("", encoding="utf-8")
    (FormatPath / "__init__.py").write_text(
        "from convert.adapters.json.Adapter import JsonAdapter as _JsonAdapter\n"
        "class HiddenAdapter(_JsonAdapter):\n    discovered = True\n"
        "__all__ = []\n",
        encoding="utf-8",
    )
    MonkeyPatch.syspath_prepend(str(TmpPath))
    RegistryData = AdapterRegistry()
    assert RegistryData.introspect(PackageName) == ("interchange.json",)


# single module adapters must remain discoverable because package folders are not required
def CheckSingleMod(TmpPath: FilePath, MonkeyPatch: Pytest.MonkeyPatch) -> None:
    PackageName = f"kit_module_{TmpPath.name.replace('-', '_')}"
    PackagePath = TmpPath / PackageName
    PackagePath.mkdir()
    (PackagePath / "__init__.py").write_text("", encoding="utf-8")
    (PackagePath / "single.py").write_text(
        "from convert.adapters.json.Adapter import JsonAdapter as _JsonAdapter\n"
        "class SingleAdapter(_JsonAdapter):\n    discovered = True\n",
        encoding="utf-8",
    )
    MonkeyPatch.syspath_prepend(str(TmpPath))
    RegistryData = AdapterRegistry()
    assert RegistryData.introspect(PackageName) == ("interchange.json",)


# identifier validation must use case insensitive comparison because format names are wire contracts
def CheckAliasCase() -> None:
    RegistryData = AdapterRegistry()
    AdapterData = JsonAdapter()
    RegistryData.register(AdapterData)
    assert RegistryData.reader("INTERCHANGE.JSON") is AdapterData
    assert RegistryData.writer("Interchange.Json") is AdapterData

    # conflicting canonical identifiers need isolation because rejection must target metadata differences
    class ConflictJson(JsonAdapter):

        # altered metadata exists because registry conflicts need an independently constructed adapter
        @property
        def GetInfo(SelfValue):
            return ReplaceData(super().info, format_id="INTERCHANGE.JSON")

        locals()["info"] = GetInfo

    with Pytest.raises(AdapterRegistryError, match="metadata differ"):
        RegistryData.register(ConflictJson())


# alias identity validation stays separate because canonical collisions have different failures
def CheckAliasIds() -> None:

    # self aliases need isolation because canonical duplication has its own validation failure
    class SelfAliasJson(JsonAdapter):

        # altered metadata exists because self alias rejection needs an independent adapter
        @property
        def GetInfo(SelfValue):
            return ReplaceData(super().info, aliases=("INTERCHANGE.JSON",))

        locals()["info"] = GetInfo

    with Pytest.raises(AdapterRegistryError, match="alias must differ"):
        AdapterRegistry().register(SelfAliasJson())

    # duplicate aliases need isolation because case folding must reject equivalent spellings
    class DupAliasJson(JsonAdapter):

        # altered metadata exists because duplicate alias rejection needs an independent adapter
        @property
        def GetInfo(SelfValue):
            return ReplaceData(super().info, aliases=("kit.json", "KIT.JSON"))

        locals()["info"] = GetInfo

    with Pytest.raises(AdapterRegistryError, match="aliases must be unique"):
        AdapterRegistry().register(DupAliasJson())


# metadata type validation stays separate because immutable text fields form one contract
def CheckInfoTypes() -> None:

    # mutable extension data needs isolation because adapter metadata must remain immutable
    class MutableExtJson(JsonAdapter):

        # altered metadata exists because mutable extension rejection needs an independent adapter
        @property
        def GetInfo(SelfValue):
            return ReplaceData(super().info, extensions=[".json"])

        locals()["info"] = GetInfo

    with Pytest.raises(AdapterRegistryError, match="extensions has an invalid type"):
        AdapterRegistry().register(MutableExtJson())

    # numeric versions need isolation because adapter metadata must remain text based
    class NumericVerJson(JsonAdapter):

        # altered metadata exists because numeric version rejection needs an independent adapter
        @property
        def GetInfo(SelfValue):
            return ReplaceData(super().info, version=1)

        locals()["info"] = GetInfo

    with Pytest.raises(AdapterRegistryError, match="version has an invalid type"):
        AdapterRegistry().register(NumericVerJson())
