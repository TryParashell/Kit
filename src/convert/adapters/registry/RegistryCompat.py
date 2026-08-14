# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from inspect import Parameter as SigParam
from inspect import Signature as CallSignature
from typing import Any as AnyValue
from typing import Iterable as TypeIterable
from typing import Mapping as TypeMap

from interchange import CadDocument

from convert.adapters.base.AdapterProtocols import CadReaderAdapter
from convert.adapters.base.AdapterProtocols import CadWriterAdapter
from convert.adapters.base.ContractTypes import KSourceType
from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.base.WriteResult import WriteResult

# historical source annotations need resolution where split registry methods are defined
globals()["Source"] = KSourceType

# historical destination annotations need resolution where split registry methods are defined
globals()["Destination"] = KTargetType

# historical iterable annotations need resolution where split registry methods are defined
globals()["Iterable"] = TypeIterable

# legacy method mapping keeps the public registry api stable after responsibility splitting
KMethodAliases: TypeMap[str, str] = {
    "register_reader": "RegisterReader",
    "register_writer": "RegisterWriter",
    "register": "RegisterOne",
    "introspect": "Introspect",
    "readers": "GetReaders",
    "writers": "GetWriters",
    "reader": "GetReader",
    "writer": "GetWriter",
    "select_reader": "PickReader",
    "select_writer": "PickWriter",
    "read": "ReadDocument",
    "read_with_adapter": "ReadAdapter",
    "write": "WriteDocument",
    "format_ids": "GetFormatIds",
    "extend": "ExtendAll",
}


# compatibility installation stays centralized so the registry facade remains structurally small
def InstallApiMut(RegistryType: type) -> None:
    for LegacyName, MethodName in KMethodAliases.items():
        MethodValue = getattr(RegistryType, MethodName)
        setattr(MethodValue, "__name__", LegacyName)
        setattr(MethodValue, "__qualname__", f"AdapterRegistry.{LegacyName}")
        setattr(MethodValue, "__module__", "convert.adapters.registry")
        setattr(RegistryType, LegacyName, MethodValue)
    setattr(RegistryType, "_bindings", property(GetBindings, SetBindingsMut))
    setattr(RegistryType, "_aliases", property(GetAliases, SetAliasesMut))


# historical method reflection stays explicit because sdk consumers generate calls from signatures
def SetMethodSigMut(
    RegistryType: type,
    MethodName: str,
    ParamValues: tuple[SigParam, ...],
    ReturnType: object,
) -> None:
    MethodValue = getattr(RegistryType, MethodName)
    setattr(
        MethodValue,
        "__signature__",
        CallSignature(ParamValues, return_annotation=ReturnType),
    )


# runtime annotation metadata stays explicit because sdk consumers inspect methods without signatures
def SetCallMetaMut(
    MethodValue: AnyValue,
    AnnotMap: TypeMap[str, AnyValue],
    KwDefaults: TypeMap[str, AnyValue] | None = None,
) -> None:
    setattr(MethodValue, "__annotations__", dict(AnnotMap))
    setattr(MethodValue, "__defaults__", None)
    setattr(
        MethodValue,
        "__kwdefaults__",
        None if KwDefaults is None else dict(KwDefaults),
    )


# public registration signatures stay centralized because all three aliases share keyword policy
def SetRegSigsMut(RegistryType: type) -> None:
    for MethodName, AdapterType in (
        ("register_reader", "CadReaderAdapter"),
        ("register_writer", "CadWriterAdapter"),
        ("register", "object"),
    ):
        SetMethodSigMut(
            RegistryType,
            MethodName,
            (
                SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
                SigParam(
                    "adapter",
                    SigParam.POSITIONAL_OR_KEYWORD,
                    annotation=AdapterType,
                ),
                SigParam(
                    "replace",
                    SigParam.KEYWORD_ONLY,
                    default=False,
                    annotation="bool",
                ),
            ),
            "None",
        )
        SetCallMetaMut(
            getattr(RegistryType, MethodName),
            {
                "adapter": AdapterType,
                "replace": "bool",
                "return": "None",
            },
            {"replace": False},
        )


# public read signatures stay centralized because document and adapter variants share arguments
def SetReadSigsMut(RegistryType: type) -> None:
    for MethodName, ReturnType in (
        ("read", "CadDocument"),
        ("read_with_adapter", "tuple[CadDocument, CadReaderAdapter]"),
    ):
        SetMethodSigMut(
            RegistryType,
            MethodName,
            (
                SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
                SigParam(
                    "source",
                    SigParam.POSITIONAL_OR_KEYWORD,
                    annotation="Source",
                ),
                SigParam(
                    "format_id",
                    SigParam.KEYWORD_ONLY,
                    default=None,
                    annotation="str | None",
                ),
                SigParam(
                    "options",
                    SigParam.KEYWORD_ONLY,
                    default=None,
                    annotation="ReadOptions | None",
                ),
            ),
            ReturnType,
        )
        SetCallMetaMut(
            getattr(RegistryType, MethodName),
            {
                "source": "Source",
                "format_id": "str | None",
                "options": "ReadOptions | None",
                "return": ReturnType,
            },
            {"format_id": None, "options": None},
        )


# public write reflection stays isolated because it owns two positional and two optional arguments
def SetWriteSigMut(RegistryType: type) -> None:
    SetMethodSigMut(
        RegistryType,
        "write",
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            SigParam(
                "document",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="CadDocument",
            ),
            SigParam(
                "destination",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="Destination",
            ),
            SigParam(
                "format_id",
                SigParam.KEYWORD_ONLY,
                default=None,
                annotation="str | None",
            ),
            SigParam(
                "options",
                SigParam.KEYWORD_ONLY,
                default=None,
                annotation="WriteOptions | None",
            ),
        ),
        "WriteResult",
    )
    SetCallMetaMut(
        getattr(RegistryType, "write"),
        {
            "document": "CadDocument",
            "destination": "Destination",
            "format_id": "str | None",
            "options": "WriteOptions | None",
            "return": "WriteResult",
        },
        {"format_id": None, "options": None},
    )


# public extension reflection stays isolated because bulk registration has one iterable contract
def SetExtendSigMut(RegistryType: type) -> None:
    SetMethodSigMut(
        RegistryType,
        "extend",
        (
            SigParam("self", SigParam.POSITIONAL_OR_KEYWORD),
            SigParam(
                "adapters",
                SigParam.POSITIONAL_OR_KEYWORD,
                annotation="Iterable[object]",
            ),
            SigParam(
                "replace",
                SigParam.KEYWORD_ONLY,
                default=False,
                annotation="bool",
            ),
        ),
        "None",
    )
    SetCallMetaMut(
        getattr(RegistryType, "extend"),
        {
            "adapters": "Iterable[object]",
            "replace": "bool",
            "return": "None",
        },
        {"replace": False},
    )


# private binding access survives because existing diagnostic consumers may inspect registry state
def GetBindings(SelfValue: AnyValue) -> AnyValue:
    return SelfValue.BindingMap


# private binding replacement survives because rollback code historically assigned complete maps
def SetBindingsMut(SelfValue: AnyValue, FieldValue: AnyValue) -> None:
    SelfValue.BindingMap = FieldValue


# private alias access survives because existing diagnostic consumers may inspect registry state
def GetAliases(SelfValue: AnyValue) -> AnyValue:
    return SelfValue.AliasMap


# private alias replacement survives because rollback code historically assigned complete maps
def SetAliasesMut(SelfValue: AnyValue, FieldValue: AnyValue) -> None:
    SelfValue.AliasMap = FieldValue
