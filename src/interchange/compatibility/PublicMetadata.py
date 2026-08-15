# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from inspect import Signature as FuncSig
from typing import Any as AnyValue
from typing import Mapping as TypeMap


# relocated definitions retain historical module identities for reflection and pickle compatibility
def BindModules(TargetValues: tuple[AnyValue, ...], ModuleName: str) -> None:
    for TargetValue in TargetValues:
        TargetValue.__module__ = ModuleName


# renamed public definitions retain historical names without constraining compliant implementation identifiers
def BindNameMut(
    TargetValue: AnyValue,
    ModuleName: str,
    LegacyName: str,
    ModuleScope: dict[str, AnyValue],
) -> None:
    TargetValue.__name__ = LegacyName
    TargetValue.__qualname__ = LegacyName
    TargetValue.__module__ = ModuleName
    ModuleScope[LegacyName] = TargetValue


# relocated public functions retain their historical reflection contract and import surface
def BindFunctionMut(
    TargetFunc: AnyValue,
    ModuleName: str,
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
    ModuleScope: dict[str, AnyValue],
) -> None:
    BindNameMut(TargetFunc, ModuleName, LegacyName, ModuleScope)
    TargetFunc.__annotations__ = dict(AnnotationMap)
    TargetFunc.__signature__ = SignatureInfo
