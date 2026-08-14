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

    # document kind lookup belongs here so clients need no format specific branching
    def GetExtensions(SelfValue, **NamedValues: object) -> tuple[str, ...]:
        Assembly = IsAssemblyFlag(NamedValues)
        return SelfValue.AssemblyExts if Assembly else SelfValue.PartExts

    # historical representation keeps logs and diagnostics comparable across package upgrades
    def __repr__(SelfValue) -> str:
        FieldValues = ", ".join(
            f"{LegacyName}={getattr(SelfValue, ModelName)!r}"
            for LegacyName, ModelName in KLegacyFields
        )
        return f"AdapterInfo({FieldValues})"


# historical dataclass reflection remains available because plugin tooling inspects legacy field names
KLegacyFields = (
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
KModelFields = tuple(ModelName for LegacyName, ModelName in KLegacyFields)


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
