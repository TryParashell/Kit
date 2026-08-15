# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import is_dataclass as IsDataClass
from typing import cast as CastValue
from typing import get_args as GetTypeArgs
from typing import get_origin as GetTypeOrigin
from typing import get_type_hints as GetTypeHints
from typing import Protocol as TypeProtocol
from typing import runtime_checkable as RuntimeCheck

from interchange.core.Reflection import GetDataFields
from interchange.serialization.Wire import GetWireField


# identity validation needs only one stable member shared by every indexed model
@RuntimeCheck
class Identified(TypeProtocol):
    EntityId: str


# readable duplicate diagnostics need labels derived consistently from model types
def FormatTypeLabel(SourceValue: type[object]) -> str:
    return "".join(
        (
            f" {Character.casefold()}"
            if IndexValue and Character.isupper()
            else Character.casefold()
        )
        for IndexValue, Character in enumerate(SourceValue.__name__)
    )


# validation needs identified collections without maintaining a fragile manual registry
def GetIdFields(ValueType: type[object]) -> tuple[tuple[str, str], ...]:
    RawHints: object = GetTypeHints(ValueType)
    TypeHints = CastValue(dict[str, object], RawHints)
    ResultValue: list[tuple[str, str]] = []
    for ItemValue in GetDataFields(ValueType):
        FieldHint = TypeHints[ItemValue.name]
        RawArguments: object = GetTypeArgs(FieldHint)
        Arguments = CastValue(tuple[object, ...], RawArguments)
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
                for MemberField in GetDataFields(MemberType)
            )
        ):
            continue
        ResultValue.append((ItemValue.name, FormatTypeLabel(MemberType)))
    return tuple(ResultValue)


# shared identity extraction keeps document and assembly duplicate checks aligned
def GetIdGroups(
    SourceValue: object,
) -> tuple[tuple[str, str, tuple[Identified, ...]], ...]:
    ResultValue: list[tuple[str, str, tuple[Identified, ...]]] = []
    for NameValue, LabelText in GetIdFields(type(SourceValue)):
        RawItems: object = getattr(SourceValue, NameValue)
        if not isinstance(RawItems, tuple):
            raise TypeError(f"{NameValue} is not an identified model collection")
        RawValues = CastValue(tuple[object, ...], RawItems)
        if not all(isinstance(ItemValue, Identified) for ItemValue in RawValues):
            raise TypeError(f"{NameValue} is not an identified model collection")
        ItemValues = CastValue(tuple[Identified, ...], RawValues)
        ResultValue.append((NameValue, LabelText, ItemValues))
    return tuple(ResultValue)
