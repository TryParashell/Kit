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

from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter

# historical reader annotations need local resolution after binding moves behind the registry facade
globals()["CadReaderAdapter"] = CadReaderAdapter

# historical writer annotations need local resolution after binding moves behind the registry facade
globals()["CadWriterAdapter"] = CadWriterAdapter


# one format binding coordinates independently registered reader and writer implementations
@DataClass(slots=True, init=False)
class AdapterBinding:
    ReaderData: CadReaderAdapter | None = None
    WriterData: CadWriterAdapter | None = None

    # historical construction remains necessary because diagnostics instantiate bindings outside the registry
    def __init__(SelfValue, *ArgValues: object, **NamedValues: object) -> None:
        if len(ArgValues) > 2:
            raise TypeError(
                f"AdapterBinding() takes from 0 to 2 positional arguments but {len(ArgValues)} were given"
            )
        AllowedNames = {"reader", "writer", "ReaderData", "WriterData"}
        UnknownNames = tuple(
            FieldName for FieldName in NamedValues if FieldName not in AllowedNames
        )
        if UnknownNames:
            raise TypeError(
                "AdapterBinding() got an unexpected keyword argument "
                f"{UnknownNames[0]!r}"
            )
        if HasBindConflict(ArgValues, NamedValues, "reader", "ReaderData", 0):
            raise TypeError("AdapterBinding() got multiple values for 'reader'")
        if HasBindConflict(ArgValues, NamedValues, "writer", "WriterData", 1):
            raise TypeError("AdapterBinding() got multiple values for 'writer'")
        SelfValue.ReaderData = NamedValues.get(
            "reader",
            NamedValues.get(
                "ReaderData",
                ArgValues[0] if ArgValues else None,
            ),
        )
        SelfValue.WriterData = NamedValues.get(
            "writer",
            NamedValues.get(
                "WriterData",
                ArgValues[1] if len(ArgValues) == 2 else None,
            ),
        )

    # legacy attributes remain readable because binding is part of the established public api
    def __getattr__(SelfValue, FieldName: str) -> object:
        AliasMap = {"reader": "ReaderData", "writer": "WriterData"}
        if FieldName in AliasMap:
            return object.__getattribute__(SelfValue, AliasMap[FieldName])
        raise AttributeError(FieldName)

    # legacy assignments remain writable because registry coordination mutates binding slots
    def __setattr__(SelfValue, FieldName: str, FieldValue: object) -> None:
        AliasMap = {"reader": "ReaderData", "writer": "WriterData"}
        object.__setattr__(SelfValue, AliasMap.get(FieldName, FieldName), FieldValue)

    # historical representation keeps registry state diagnostics stable for external callers
    def __repr__(SelfValue) -> str:
        return (
            f"AdapterBinding(reader={SelfValue.ReaderData!r}, "
            f"writer={SelfValue.WriterData!r})"
        )

    # legacy pickle output must retain historical slot keys for older package releases
    def __getstate__(SelfValue) -> tuple[None, dict[str, object]]:
        return None, {
            "reader": SelfValue.ReaderData,
            "writer": SelfValue.WriterData,
        }


# conflict detection stays separate because positional and dual keyword aliases share one rule
def HasBindConflict(
    ArgValues: tuple[object, ...],
    NamedValues: dict[str, object],
    LegacyName: str,
    ModelName: str,
    ArgIndex: int,
) -> bool:
    return (LegacyName in NamedValues and ModelName in NamedValues) or (
        len(ArgValues) > ArgIndex
        and (LegacyName in NamedValues or ModelName in NamedValues)
    )


setattr(
    AdapterBinding,
    "__signature__",
    CallSignature(
        (
            SigParam(
                "reader",
                SigParam.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation="CadReaderAdapter | None",
            ),
            SigParam(
                "writer",
                SigParam.POSITIONAL_OR_KEYWORD,
                default=None,
                annotation="CadWriterAdapter | None",
            ),
        ),
        return_annotation=None,
    ),
)
setattr(AdapterBinding, "__match_args__", ("reader", "writer"))

for LegacyName, ModelName in (
    ("reader", "ReaderData"),
    ("writer", "WriterData"),
):
    setattr(AdapterBinding.__dataclass_fields__[ModelName], "name", LegacyName)

# binding reflection needs historical keys because diagnostics inspect dataclass metadata directly
AdapterBinding.__dataclass_fields__ = {
    "reader": AdapterBinding.__dataclass_fields__["ReaderData"],
    "writer": AdapterBinding.__dataclass_fields__["WriterData"],
}

# binding annotation reflection needs historical keys because registry integrations generate forms
AdapterBinding.__annotations__ = {
    "reader": AdapterBinding.__annotations__["ReaderData"],
    "writer": AdapterBinding.__annotations__["WriterData"],
}

setattr(
    AdapterBinding.__init__,
    "__signature__",
    CallSignature(
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            *AdapterBinding.__signature__.parameters.values(),
        ),
        return_annotation=None,
    ),
)
setattr(
    AdapterBinding.__init__,
    "__annotations__",
    {
        **AdapterBinding.__annotations__,
        "return": None,
    },
)
