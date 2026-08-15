# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import dataclasses as DataClasses
import inspect as Inspect
import pickle as Pickle
import typing as Typing

import convert as ConvertPackage
import convert.api as ApiModule
import convert.engine as EngineModule
from convert.adapters import AdapterRegistry
from convert.adapters import Destination
from convert.adapters import ReadOptions
from convert.adapters import Source
from convert.adapters import WriteOptions
from convert.adapters import WriteResult
from interchange import CadDocument
from interchange import PayloadRole

# api signatures stay explicit because generated wrappers must match every historical parameter exactly
KApiSigns = {
    "available_adapters": "() -> 'tuple[AdapterInfo, ...]'",
    "open_document": "(source: 'Source', *, source_format: 'str | None' = None, configuration: 'str | None' = None, include_brep: 'bool' = True, include_tessellation: 'bool' = True, strict: 'bool' = True) -> 'CadDocument'",
    "write_document": "(document: 'CadDocument', destination: 'Destination', *, destination_format: 'str | None' = None, configuration: 'str | None' = None, overwrite: 'bool' = False, validate: 'bool' = True, allow_carrier: 'bool' = True, values: 'Mapping[str, Any] | None' = None) -> 'WriteResult'",
    "convert": "(source: 'Source', destination: 'Destination', *, source_format: 'str | None' = None, destination_format: 'str | None' = None, configuration: 'str | None' = None, include_brep: 'bool' = True, include_tessellation: 'bool' = True, strict: 'bool' = True, overwrite: 'bool' = False, allow_carrier: 'bool' = True, write_values: 'Mapping[str, Any] | None' = None) -> 'ConversionResult'",
    "extract_brep": "(source: 'Source | CadDocument', directory: 'str | Path', *, source_format: 'str | None' = None, overwrite: 'bool' = False) -> 'tuple[Path, ...]'",
}

# simple api annotations stay explicit because runtime schema tools consume their historical string forms
KSimpleAnnots = {
    "available_adapters": {"return": "tuple[AdapterInfo, ...]"},
    "open_document": {
        "source": "Source",
        "source_format": "str | None",
        "configuration": "str | None",
        "include_brep": "bool",
        "include_tessellation": "bool",
        "strict": "bool",
        "return": "CadDocument",
    },
    "extract_brep": {
        "source": "Source | CadDocument",
        "directory": "str | Path",
        "source_format": "str | None",
        "overwrite": "bool",
        "return": "tuple[Path, ...]",
    },
}

# write api annotations stay separate because their portable output contract has independent parameters
KWriteAnnots = {
    "write_document": {
        "document": "CadDocument",
        "destination": "Destination",
        "destination_format": "str | None",
        "configuration": "str | None",
        "overwrite": "bool",
        "validate": "bool",
        "allow_carrier": "bool",
        "values": "Mapping[str, Any] | None",
        "return": "WriteResult",
    },
}

# conversion annotations stay separate because the orchestration entry point owns the broadest contract
KConvertAnnots = {
    "convert": {
        "source": "Source",
        "destination": "Destination",
        "source_format": "str | None",
        "destination_format": "str | None",
        "configuration": "str | None",
        "include_brep": "bool",
        "include_tessellation": "bool",
        "strict": "bool",
        "overwrite": "bool",
        "allow_carrier": "bool",
        "write_values": "Mapping[str, Any] | None",
        "return": "ConversionResult",
    },
}

# one merged annotation catalog keeps reflection assertions independent from declaration layout
KApiAnnots = KSimpleAnnots | KWriteAnnots | KConvertAnnots

# api defaults stay explicit because wrapper bodies otherwise hide keyword reflection from callers
KApiDefaults = {
    "available_adapters": None,
    "open_document": {
        "source_format": None,
        "configuration": None,
        "include_brep": True,
        "include_tessellation": True,
        "strict": True,
    },
    "write_document": {
        "destination_format": None,
        "configuration": None,
        "overwrite": False,
        "validate": True,
        "allow_carrier": True,
        "values": None,
    },
    "convert": {
        "source_format": None,
        "destination_format": None,
        "configuration": None,
        "include_brep": True,
        "include_tessellation": True,
        "strict": True,
        "overwrite": False,
        "allow_carrier": True,
        "write_values": None,
    },
    "extract_brep": {"source_format": None, "overwrite": False},
}

# engine signatures stay explicit because custom registry users inspect coordinator methods directly
KEngineSigns = {
    "__init__": "(self, registry: 'AdapterRegistry')",
    "read": "(self, source: 'Source', *, format_id: 'str | None' = None, options: 'ReadOptions | None' = None) -> 'CadDocument'",
    "write": "(self, document: 'CadDocument', destination: 'Destination', *, format_id: 'str | None' = None, options: 'WriteOptions | None' = None) -> 'WriteResult'",
    "convert": "(self, source: 'Source', destination: 'Destination', *, source_format: 'str | None' = None, destination_format: 'str | None' = None, read_options: 'ReadOptions | None' = None, write_options: 'WriteOptions | None' = None) -> 'ConversionResult'",
}

# engine annotations stay explicit because type hint resolution is part of the public integration contract
KEngineAnnots = {
    "__init__": {"registry": "AdapterRegistry"},
    "read": {
        "source": "Source",
        "format_id": "str | None",
        "options": "ReadOptions | None",
        "return": "CadDocument",
    },
    "write": {
        "document": "CadDocument",
        "destination": "Destination",
        "format_id": "str | None",
        "options": "WriteOptions | None",
        "return": "WriteResult",
    },
    "convert": {
        "source": "Source",
        "destination": "Destination",
        "source_format": "str | None",
        "destination_format": "str | None",
        "read_options": "ReadOptions | None",
        "write_options": "WriteOptions | None",
        "return": "ConversionResult",
    },
}

# engine defaults stay explicit because dynamic wrappers must preserve keyword only call metadata
KEngineDefaults = {
    "__init__": None,
    "read": {"format_id": None, "options": None},
    "write": {"format_id": None, "options": None},
    "convert": {
        "source_format": None,
        "destination_format": None,
        "read_options": None,
        "write_options": None,
    },
}

# engine hints stay explicit because resolved public types must survive implementation splitting
KEngineHints = {
    "__init__": {"registry": AdapterRegistry},
    "read": {
        "source": Source,
        "format_id": str | None,
        "options": ReadOptions | None,
        "return": CadDocument,
    },
    "write": {
        "document": CadDocument,
        "destination": Destination,
        "format_id": str | None,
        "options": WriteOptions | None,
        "return": WriteResult,
    },
    "convert": {
        "source": Source,
        "destination": Destination,
        "source_format": str | None,
        "destination_format": str | None,
        "read_options": ReadOptions | None,
        "write_options": WriteOptions | None,
        "return": EngineModule.ConversionResult,
    },
}

# result properties stay explicit because direct class reflection must expose every historical descriptor
KPropertyNames = (
    "transfers",
    "dropped",
    "requirements",
    "application_usable",
    "vendor_loadable",
    "roundtrip_safe",
    "near_lossless",
)

# result property annotations stay explicit because inherited getter metadata remains public reflection
KPropertyAnnots = {
    "transfers": "tuple[CapabilityTransfer, ...]",
    "dropped": "frozenset[Capability]",
    "requirements": "tuple[str, ...]",
    "application_usable": "bool",
    "vendor_loadable": "bool",
    "roundtrip_safe": "bool",
    "near_lossless": "bool",
}


# public wrappers need exact metadata because documentation schema and pickle consumers all depend on it
def CheckApiCalls() -> None:
    assert ApiModule.PayloadRole is PayloadRole
    for PublicName in KApiSigns:
        CallValue = getattr(ApiModule, PublicName)
        assert getattr(ConvertPackage, PublicName) is CallValue
        assert (CallValue.__module__, CallValue.__name__, CallValue.__qualname__) == (
            "convert.api",
            PublicName,
            PublicName,
        )
        assert str(Inspect.signature(CallValue)) == KApiSigns[PublicName]
        assert CallValue.__annotations__ == KApiAnnots[PublicName]
        assert CallValue.__kwdefaults__ == KApiDefaults[PublicName]
        assert Typing.get_type_hints(CallValue)
        assert Pickle.loads(Pickle.dumps(CallValue)) is CallValue


# engine methods need exact metadata because callers use custom registries through this public class
def CheckEngineApi() -> None:
    EngineType = EngineModule.ConversionEngine
    assert (EngineType.__module__, EngineType.__name__, EngineType.__qualname__) == (
        "convert.engine",
        "ConversionEngine",
        "ConversionEngine",
    )
    assert str(Inspect.signature(EngineType)) == "(registry: 'AdapterRegistry')"
    assert Pickle.loads(Pickle.dumps(EngineType)) is EngineType
    RegistryData = AdapterRegistry()
    assert EngineType(RegistryData).registry is RegistryData
    for PublicName in KEngineSigns:
        CallValue = getattr(EngineType, PublicName)
        assert (CallValue.__module__, CallValue.__name__, CallValue.__qualname__) == (
            "convert.engine",
            PublicName,
            f"ConversionEngine.{PublicName}",
        )
        assert str(Inspect.signature(CallValue)) == KEngineSigns[PublicName]
        assert CallValue.__annotations__ == KEngineAnnots[PublicName]
        assert CallValue.__kwdefaults__ == KEngineDefaults[PublicName]
        assert Typing.get_type_hints(CallValue) == KEngineHints[PublicName]
        assert Pickle.loads(Pickle.dumps(CallValue)) is CallValue


# result identity must remain exact because dataclass reflection pattern matching and pickle all expose it
def CheckResultData() -> None:
    ResultType = EngineModule.ConversionResult
    assert (ResultType.__module__, ResultType.__name__, ResultType.__qualname__) == (
        "convert.engine",
        "ConversionResult",
        "ConversionResult",
    )
    assert DataClasses.is_dataclass(ResultType)
    assert tuple(FieldData.name for FieldData in DataClasses.fields(ResultType)) == (
        "document",
        "output",
        "source_format",
        "destination_format",
    )
    assert (
        str(Inspect.signature(ResultType))
        == "(document: 'CadDocument', output: 'WriteResult', source_format: 'str', destination_format: 'str') -> None"
    )
    assert ResultType.__mro__ == (ResultType, object)
    assert ResultType.__slots__ == (
        "document",
        "output",
        "source_format",
        "destination_format",
    )
    assert ResultType.__match_args__ == ResultType.__slots__
    assert Typing.get_type_hints(ResultType) == {
        "document": CadDocument,
        "output": WriteResult,
        "source_format": str,
        "destination_format": str,
    }
    assert Pickle.loads(Pickle.dumps(ResultType)) is ResultType


# result descriptors must remain direct because inspect static and schema tools do not infer split ownership
def CheckResultMeta() -> None:
    ResultType = EngineModule.ConversionResult
    for PublicName in KPropertyNames:
        PropertyValue = ResultType.__dict__[PublicName]
        assert isinstance(PropertyValue, property)
        GetterValue = PropertyValue.fget
        assert GetterValue is not None
        assert (
            GetterValue.__module__,
            GetterValue.__name__,
            GetterValue.__qualname__,
        ) == (
            "convert.engine",
            PublicName,
            f"ConversionResult.{PublicName}",
        )
        assert tuple(Inspect.signature(GetterValue).parameters) == ("self",)
        assert GetterValue.__annotations__ == {"return": KPropertyAnnots[PublicName]}
        assert "return" in Typing.get_type_hints(GetterValue)
