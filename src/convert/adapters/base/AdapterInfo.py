# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass
from inspect import Parameter as SigParam
from inspect import Signature as CallSignature

from interchange import Capability

from convert.adapters.base.ContractCompat import ContractBase

from typing_extensions import override as Override


# legacy extension keywords need one strict translation point before document kind lookup
def IsAssemblyFlag(NamedValues: dict[str, object]) -> bool:
    AllowedNames = {"assembly", "Assembly"}
    UnknownNames = tuple(
        NameText for NameText in NamedValues if NameText not in AllowedNames
    )
    if UnknownNames:
        raise TypeError(
            "AdapterInfo.extensions_for() got an unexpected keyword argument "
            f"{UnknownNames[0]!r}"
        )
    if "assembly" in NamedValues and "Assembly" in NamedValues:
        raise TypeError(
            "AdapterInfo.extensions_for() got multiple values for 'assembly'"
        )
    if not NamedValues:
        raise TypeError(
            "AdapterInfo.extensions_for() missing required keyword only argument "
            "'assembly'"
        )
    Assembly = NamedValues.get("assembly", NamedValues.get("Assembly"))
    if not isinstance(Assembly, bool):
        raise TypeError("assembly must be a boolean")
    return Assembly


# adapter metadata gives discovery and selection one immutable format description
@DataClass(frozen=True, slots=True)
class AdapterInfo(ContractBase):
    format_id: str
    name: str
    version: str
    extensions: tuple[str, ...]
    aliases: tuple[str, ...] = ()
    capabilities: frozenset[Capability] = frozenset()
    media_types: tuple[str, ...] = ()
    native_capabilities: frozenset[Capability] = frozenset()
    part_extensions: tuple[str, ...] = ()
    assembly_extensions: tuple[str, ...] = ()

    # canonical format access remains typed because registry internals read this storage field
    @property
    def FormatId(self) -> str:
        return self.format_id

    # canonical display access remains typed because catalogs render this storage field
    @property
    def DisplayName(self) -> str:
        return self.name

    # canonical version access remains typed because plugin diagnostics expose this storage field
    @property
    def VersionText(self) -> str:
        return self.version

    # canonical extension access remains typed because selectors consume this storage field
    @property
    def Extensions(self) -> tuple[str, ...]:
        return self.extensions

    # canonical alias access remains typed because registry namespaces consume this storage field
    @property
    def AliasNames(self) -> tuple[str, ...]:
        return self.aliases

    # canonical capability access remains typed because policy callers compare this storage field
    @property
    def Capabilities(self) -> frozenset[Capability]:
        return self.capabilities

    # canonical media access remains typed because discovery consumers inspect this storage field
    @property
    def MediaTypes(self) -> tuple[str, ...]:
        return self.media_types

    # canonical native capability access remains typed because transfer policy consumes this field
    @property
    def NativeCaps(self) -> frozenset[Capability]:
        return self.native_capabilities

    # canonical part extension access remains typed because document routing consumes this field
    @property
    def PartExts(self) -> tuple[str, ...]:
        return self.part_extensions

    # canonical assembly extension access remains typed because document routing consumes this field
    @property
    def AssemblyExts(self) -> tuple[str, ...]:
        return self.assembly_extensions

    # document kind lookup belongs here so clients need no format specific branching
    def GetExtensions(self, **NamedValues: object) -> tuple[str, ...]:
        Assembly = IsAssemblyFlag(NamedValues)
        return self.assembly_extensions if Assembly else self.part_extensions

    # document kind lookup belongs here so clients need no format specific branching
    def GetExtensions(self, **NamedValues: object) -> tuple[str, ...]:
        Assembly = IsAssemblyFlag(NamedValues)
        return self.assembly_extensions if Assembly else self.part_extensions

    # historical representation keeps logs and diagnostics comparable across package upgrades
    @Override
    def __repr__(self) -> str:
        FieldValues = ", ".join(
            f"{ModelName}={getattr(self, ModelName)!r}"
            for ModelName in KModelFields
        )
        return f"AdapterInfo({FieldValues})"


# canonical field order remains necessary for immutable slot pickle restoration
KModelFields: tuple[str, ...] = (
    "format_id",
    "name",
    "version",
    "extensions",
    "aliases",
    "capabilities",
    "media_types",
    "native_capabilities",
    "part_extensions",
    "assembly_extensions",
)


# immutable slot pickles read canonical storage despite historical field reflection
def GetPickleState(SelfValue: AdapterInfo) -> tuple[object, ...]:
    return tuple(getattr(SelfValue, ModelName) for ModelName in KModelFields)


# canonical restoration prevents historical reflected names from targeting invalid slots
def SetPickleState(SelfValue: AdapterInfo, FieldValues: tuple[object, ...]) -> None:
    for ModelName, FieldValue in zip(KModelFields, FieldValues):
        object.__setattr__(SelfValue, ModelName, FieldValue)


setattr(AdapterInfo, "__getstate__", GetPickleState)
setattr(AdapterInfo, "__setstate__", SetPickleState)


setattr(AdapterInfo, "extensions_for", AdapterInfo.GetExtensions)

setattr(AdapterInfo.GetExtensions, "__module__", "convert.adapters.base")
setattr(AdapterInfo.GetExtensions, "__name__", "extensions_for")
setattr(AdapterInfo.GetExtensions, "__qualname__", "AdapterInfo.extensions_for")
setattr(
    AdapterInfo.GetExtensions,
    "__annotations__",
    {"assembly": "bool", "return": "tuple[str, ...]"},
)
setattr(
    AdapterInfo.GetExtensions,
    "__signature__",
    CallSignature(
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            SigParam(
                "assembly",
                SigParam.KEYWORD_ONLY,
                annotation="bool",
            ),
        ),
        return_annotation="tuple[str, ...]",
    ),
)

setattr(
    AdapterInfo,
    "__match_args__",
    (
        "format_id",
        "name",
        "version",
        "extensions",
        "aliases",
        "capabilities",
        "media_types",
        "native_capabilities",
        "part_extensions",
        "assembly_extensions",
    ),
)

setattr(
    AdapterInfo.__init__,
    "__signature__",
    CallSignature(
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            *AdapterInfo.__signature__.parameters.values(),
        ),
        return_annotation=None,
    ),
)
setattr(
    AdapterInfo.__init__,
    "__annotations__",
    {
        **AdapterInfo.__annotations__,
        "return": None,
    },
)
