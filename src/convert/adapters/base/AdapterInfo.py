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
from typing import TYPE_CHECKING as IsTypeCheck
from typing import overload as Overload

from interchange import Capability

from convert.adapters.base.ContractCompat import ContractBase


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
    FormatId: str
    DisplayName: str
    VersionText: str
    Extensions: tuple[str, ...]
    AliasNames: tuple[str, ...] = ()
    Capabilities: frozenset[Capability] = frozenset()
    MediaTypes: tuple[str, ...] = ()
    NativeCaps: frozenset[Capability] = frozenset()
    PartExts: tuple[str, ...] = ()
    AssemblyExts: tuple[str, ...] = ()

    if IsTypeCheck:

        # historical keywords remain typed because plugin constructors depend on this public contract
        @Overload
        def __init__(
            self,
            format_id: str,
            name: str,
            version: str,
            extensions: tuple[str, ...],
            aliases: tuple[str, ...] = (),
            capabilities: frozenset[Capability] = frozenset(),
            media_types: tuple[str, ...] = (),
            native_capabilities: frozenset[Capability] = frozenset(),
            part_extensions: tuple[str, ...] = (),
            assembly_extensions: tuple[str, ...] = (),
        ) -> None: ...  # lgtm[py/ineffectual-statement]

        # canonical keywords remain typed because dataclass replacement constructs records from storage fields
        @Overload
        def __init__(
            self,
            FormatId: str,
            DisplayName: str,
            VersionText: str,
            Extensions: tuple[str, ...],
            AliasNames: tuple[str, ...] = (),
            Capabilities: frozenset[Capability] = frozenset(),
            MediaTypes: tuple[str, ...] = (),
            NativeCaps: frozenset[Capability] = frozenset(),
            PartExts: tuple[str, ...] = (),
            AssemblyExts: tuple[str, ...] = (),
        ) -> None: ...  # lgtm[py/ineffectual-statement]

        # broad implementation parameters exist only to connect both statically checked constructor forms
        def __init__(
            self, *ArgValues: object, **NamedValues: object
        ) -> None: ...  # lgtm[py/ineffectual-statement]

        # both keyword eras remain visible because document routing callers upgraded independently
        @Overload
        def extensions_for(
            self, *, assembly: bool
        ) -> tuple[str, ...]: ...  # lgtm[py/ineffectual-statement]

        # both keyword eras remain visible because document routing callers upgraded independently
        @Overload
        def extensions_for(
            self, *, Assembly: bool
        ) -> tuple[str, ...]: ...  # lgtm[py/ineffectual-statement]

        # dynamic dispatch still validates collisions while overloads describe every supported spelling
        def extensions_for(self, **NamedValues: object) -> tuple[str, ...]:
            return self.GetExtensions(**NamedValues)

    # historical format access remains typed because registry callers use the established public field
    @property
    def format_id(self) -> str:
        return self.FormatId

    # historical display access remains typed because external catalogs render this established public field
    @property
    def name(self) -> str:
        return self.DisplayName

    # historical version access remains typed because plugin diagnostics expose this established public field
    @property
    def version(self) -> str:
        return self.VersionText

    # historical extension access remains typed because selectors consume this established public field
    @property
    def extensions(self) -> tuple[str, ...]:
        return self.Extensions

    # historical alias access remains typed because registry namespaces consume this established public field
    @property
    def aliases(self) -> tuple[str, ...]:
        return self.AliasNames

    # historical capability access remains typed because policy callers compare this established public field
    @property
    def capabilities(self) -> frozenset[Capability]:
        return self.Capabilities

    # historical media access remains typed because discovery consumers inspect this established public field
    @property
    def media_types(self) -> tuple[str, ...]:
        return self.MediaTypes

    # historical native capability access remains typed because transfer policy consumes this public field
    @property
    def native_capabilities(self) -> frozenset[Capability]:
        return self.NativeCaps

    # historical part extension access remains typed because document routing consumes this public field
    @property
    def part_extensions(self) -> tuple[str, ...]:
        return self.PartExts

    # historical assembly extension access remains typed because document routing consumes this public field
    @property
    def assembly_extensions(self) -> tuple[str, ...]:
        return self.AssemblyExts

    # document kind lookup belongs here so clients need no format specific branching
    def GetExtensions(self, **NamedValues: object) -> tuple[str, ...]:
        Assembly = IsAssemblyFlag(NamedValues)
        return self.AssemblyExts if Assembly else self.PartExts

    # historical representation keeps logs and diagnostics comparable across package upgrades
    def __repr__(self) -> str:
        FieldValues = ", ".join(
            f"{LegacyName}={getattr(self, ModelName)!r}"
            for LegacyName, ModelName in KLegacyFields
        )
        return f"AdapterInfo({FieldValues})"


# historical dataclass reflection remains available because plugin tooling inspects legacy field names
KLegacyFields: tuple[tuple[str, str], ...] = (
    ("format_id", "FormatId"),
    ("name", "DisplayName"),
    ("version", "VersionText"),
    ("extensions", "Extensions"),
    ("aliases", "AliasNames"),
    ("capabilities", "Capabilities"),
    ("media_types", "MediaTypes"),
    ("native_capabilities", "NativeCaps"),
    ("part_extensions", "PartExts"),
    ("assembly_extensions", "AssemblyExts"),
)

# canonical field order remains necessary for immutable slot pickle restoration
KModelFields = tuple(FieldPair[1] for FieldPair in KLegacyFields)


# immutable slot pickles read canonical storage despite historical field reflection
def GetPickleState(SelfValue: AdapterInfo) -> tuple[object, ...]:
    return tuple(getattr(SelfValue, ModelName) for ModelName in KModelFields)


# canonical restoration prevents historical reflected names from targeting invalid slots
def SetPickleState(SelfValue: AdapterInfo, FieldValues: tuple[object, ...]) -> None:
    for ModelName, FieldValue in zip(KModelFields, FieldValues):
        object.__setattr__(SelfValue, ModelName, FieldValue)


setattr(AdapterInfo, "__getstate__", GetPickleState)
setattr(AdapterInfo, "__setstate__", SetPickleState)

for LegacyName, ModelName in KLegacyFields:
    setattr(AdapterInfo.__dataclass_fields__[ModelName], "name", LegacyName)

# plugin reflection needs legacy mapping keys because direct field lookups are established behavior
AdapterInfo.__dataclass_fields__ = {
    LegacyName: AdapterInfo.__dataclass_fields__[ModelName]
    for LegacyName, ModelName in KLegacyFields
}

# runtime annotation inspection needs historical keys because third party forms resolve them directly
AdapterInfo.__annotations__ = {
    LegacyName: AdapterInfo.__annotations__[ModelName]
    for LegacyName, ModelName in KLegacyFields
}


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
