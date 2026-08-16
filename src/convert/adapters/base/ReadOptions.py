# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as DataClass
from dataclasses import field as DataField
from typing import Mapping as TypeMap
from typing import TYPE_CHECKING as IsTypeCheck
from typing import overload as Overload

from interchange import frozen_mapping as FreezeMapping

from convert.adapters.base.ContractCompat import ContractBase


# read policy stays immutable so adapters receive consistent filtering and validation intent
@DataClass(frozen=True, slots=True)
class ReadOptions(ContractBase):
    ConfigName: str | None = None
    IncludeBrep: bool = True
    IncludeMesh: bool = True
    StrictMode: bool = True
    OptionValues: TypeMap[str, object] = DataField(default_factory=FreezeMapping)

    if IsTypeCheck:

        # historical keywords remain typed because adapter consumers construct this public policy directly
        @Overload
        def __init__(
            self,
            configuration: str | None = None,
            include_brep: bool = True,
            include_tessellation: bool = True,
            strict: bool = True,
            values: TypeMap[str, object] = FreezeMapping(),
        ) -> None: ...  # lgtm[py/ineffectual-statement]

        # canonical keywords remain typed because dataclass replacement reconstructs policies from storage fields
        @Overload
        def __init__(
            self,
            ConfigName: str | None = None,
            IncludeBrep: bool = True,
            IncludeMesh: bool = True,
            StrictMode: bool = True,
            OptionValues: TypeMap[str, object] = FreezeMapping(),
        ) -> None: ...  # lgtm[py/ineffectual-statement]

        # broad implementation parameters exist only to connect both statically checked constructor forms
        def __init__(self, *ArgValues: object, **NamedValues: object) -> None: ...  # lgtm[py/ineffectual-statement]

    # historical configuration access remains typed because readers consume this public selection field
    @property
    def configuration(self) -> str | None:
        return self.ConfigName

    # historical brep access remains typed because readers consume this public filtering field
    @property
    def include_brep(self) -> bool:
        return self.IncludeBrep

    # historical tessellation access remains typed because readers consume this public filtering field
    @property
    def include_tessellation(self) -> bool:
        return self.IncludeMesh

    # historical strictness access remains typed because readers consume this public validation field
    @property
    def strict(self) -> bool:
        return self.StrictMode

    # historical option access remains typed because adapters consume this public extension field
    @property
    def values(self) -> TypeMap[str, object]:
        return self.OptionValues
