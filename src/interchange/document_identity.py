# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import fields as GetFields
from dataclasses import is_dataclass as IsDataClass
from functools import cache as CacheResult
from typing import Any as AnyValue
from typing import get_args as GetTypeArgs
from typing import get_origin as GetTypeOrigin
from typing import get_type_hints as GetTypeHints

from .wire import GetWireField


# readable duplicate diagnostics need labels derived consistently from model types
def FormatTypeLabel(SourceValue: type[AnyValue]) -> str:
    return "".join(
        (
            f" {Character.casefold()}"
            if IndexValue and Character.isupper()
            else Character.casefold()
        )
        for IndexValue, Character in enumerate(SourceValue.__name__)
    )


# validation needs identified collections without maintaining a fragile manual registry
@CacheResult
def GetIdFields(ValueType: type[AnyValue]) -> tuple[tuple[str, str], ...]:
    TypeHints = GetTypeHints(ValueType)
    ResultValue: list[tuple[str, str]] = []
    for ItemValue in GetFields(ValueType):
        FieldHint = TypeHints[ItemValue.name]
        Arguments = GetTypeArgs(FieldHint)
        if (
            GetTypeOrigin(FieldHint) is not tuple
            or len(Arguments) != 2
            or Arguments[1] is not Ellipsis
        ):
            continue
        MemberType = Arguments[0]
        if (
            not isinstance(MemberType, type)
            or not IsDataClass(MemberType)
            or not any(
                GetWireField(MemberField.name, MemberType) == "id"
                for MemberField in GetFields(MemberType)
            )
        ):
            continue
        ResultValue.append((ItemValue.name, FormatTypeLabel(MemberType)))
    return tuple(ResultValue)


# shared identity extraction keeps document and assembly duplicate checks aligned
def GetIdGroups(
    SourceValue: AnyValue,
) -> tuple[tuple[str, str, tuple[AnyValue, ...]], ...]:
    return tuple(
        (
            NameValue,
            LabelText,
            getattr(SourceValue, NameValue),
        )
        for NameValue, LabelText in GetIdFields(type(SourceValue))
    )
