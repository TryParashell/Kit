# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations as Annotations
import dataclasses as DataClasses
import inspect as Inspect
import pickle as Pickle
import typing as Typing
import pytest as Pytest
from convert import adapters as AdapterPackage
from convert.adapters import AdapterBinding
from convert.adapters import AdapterInfo
from convert.adapters import AdapterRegistry
from convert.adapters import ApplicationUsabilityError as AppUsabilityError
from convert.adapters import CadAdapter
from convert.adapters import CadReaderAdapter
from convert.adapters import CadWriterAdapter
from convert.adapters import CapabilityLossError
from convert.adapters import CarrierReason
from convert.adapters import TransferMode
from convert.adapters import WriteResult
from convert.adapters.catia.Adapter import CatiaAdapter
from convert.adapters.json import JsonAdapter
from interchange import Capability


# dynamic compatibility checks need runtime invocation without weakening production contracts
def CallCompat(
    TargetValue: object,
    *ArgValues: object,
    **NamedValues: object,
) -> object:
    if not callable(TargetValue):
        raise TypeError("compatibility target must be callable")
    return TargetValue(*ArgValues, **NamedValues)


# protocol metadata remains intentionally runtime owned across supported python versions
def GetTypeMember(ClassValue: type[object], MemberName: str) -> object:
    return Typing.cast(object, type.__getattribute__(ClassValue, MemberName))


# this definition exists because focused behavior needs one stable owner
def CheckProtocols() -> None:
    for ProtocolType in (CadReaderAdapter, CadWriterAdapter, CadAdapter):
        assert ProtocolType.__module__ == "convert.adapters.base"
        assert Pickle.loads(Pickle.dumps(ProtocolType)) is ProtocolType
        assert GetTypeMember(ProtocolType, "_is_runtime_protocol") is True
    if hasattr(CadReaderAdapter, "__protocol_attrs__"):
        assert GetTypeMember(CadReaderAdapter, "__protocol_attrs__") == {
            "info",
            "probe",
            "read",
        }
    if hasattr(CadWriterAdapter, "__protocol_attrs__"):
        assert GetTypeMember(CadWriterAdapter, "__protocol_attrs__") == {
            "info",
            "supports",
            "write",
        }
    assert isinstance(JsonAdapter(), CadAdapter)
    assert isinstance(JsonAdapter(), CadReaderAdapter)
    assert isinstance(JsonAdapter(), CadWriterAdapter)
    assert isinstance(CatiaAdapter(), CadAdapter)
    assert isinstance(CatiaAdapter(), CadReaderAdapter)
    assert isinstance(CatiaAdapter(), CadWriterAdapter)
    assert (
        str(Inspect.signature(CadReaderAdapter.read))
        == "(self, source: 'Source', options: 'ReadOptions | None' = None) -> 'CadDocument'"
    )
    assert (
        str(Inspect.signature(CadWriterAdapter.write))
        == "(self, document: 'CadDocument', destination: 'Destination', options: 'WriteOptions | None' = None) -> 'WriteResult'"
    )
    assert CadReaderAdapter.read.__module__ == "convert.adapters.base"
    assert CadWriterAdapter.write.__module__ == "convert.adapters.base"
    assert tuple(CadReaderAdapter.probe.__dict__) == ("__signature__",)
    assert tuple(CadReaderAdapter.read.__dict__) == ("__signature__",)
    assert tuple(CadWriterAdapter.supports.__dict__) == ("__signature__",)
    assert tuple(CadWriterAdapter.write.__dict__) == ("__signature__",)
    assert Typing.get_type_hints(CadReaderAdapter.read)["source"] is not None
    assert Typing.get_type_hints(CadWriterAdapter.write)["destination"] is not None
    assert "GetInfo" not in CadReaderAdapter.__dict__
    assert "ProbeSource" not in CadReaderAdapter.__dict__
    assert "ReadSource" not in CadReaderAdapter.__dict__
    assert "CanWrite" not in CadWriterAdapter.__dict__
    assert "WriteTarget" not in CadWriterAdapter.__dict__


# this definition exists because focused behavior needs one stable owner
def CheckInfo() -> None:
    FieldNames = tuple(
        (FieldData.name for FieldData in DataClasses.fields(AdapterInfo))
    )
    assert FieldNames == (
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
    assert (
        str(Inspect.signature(AdapterInfo))
        == "(format_id: 'str', name: 'str', version: 'str', extensions: 'tuple[str, ...]', aliases: 'tuple[str, ...]' = (), capabilities: 'frozenset[Capability]' = frozenset(), media_types: 'tuple[str, ...]' = (), native_capabilities: 'frozenset[Capability]' = frozenset(), part_extensions: 'tuple[str, ...]' = (), assembly_extensions: 'tuple[str, ...]' = ()) -> None"
    )
    InfoData = AdapterInfo("format.test", "Test", "1", (".test",))
    assert InfoData.format_id == "format.test"
    for ProtocolValue in range(Pickle.HIGHEST_PROTOCOL + 1):
        EncodedData = Pickle.dumps(InfoData, protocol=ProtocolValue)
        assert Pickle.loads(EncodedData) == InfoData
    ReplacedInfo = Typing.cast(
        AdapterInfo,
        CallCompat(DataClasses.replace, InfoData, format_id="format.other"),
    )
    assert ReplacedInfo.format_id == "format.other"
    assert (
        str(Inspect.signature(AdapterInfo.__init__))
        == "(self, format_id: 'str', name: 'str', version: 'str', extensions: 'tuple[str, ...]', aliases: 'tuple[str, ...]' = (), capabilities: 'frozenset[Capability]' = frozenset(), media_types: 'tuple[str, ...]' = (), native_capabilities: 'frozenset[Capability]' = frozenset(), part_extensions: 'tuple[str, ...]' = (), assembly_extensions: 'tuple[str, ...]' = ()) -> None"
    )
    assert (
        str(Inspect.signature(AdapterInfo.extensions_for))
        == "(self, *, assembly: 'bool') -> 'tuple[str, ...]'"
    )
    assert AdapterInfo.extensions_for.__name__ == "extensions_for"
    assert AdapterInfo.extensions_for.__module__ == "convert.adapters.base"
    assert InfoData.extensions_for(assembly=False) == ()
    with Pytest.raises(TypeError):
        CallCompat(InfoData.extensions_for, assembly=False, Assembly=False)
    with Pytest.raises(TypeError):
        CallCompat(
            AdapterInfo,
            "format.test",
            "Test",
            "1",
            (".test",),
            format_id="other",
        )
    with Pytest.raises(TypeError):
        CallCompat(
            AdapterInfo,
            "format.test",
            "Test",
            "1",
            (".test",),
            FormatId="other",
            format_id="other",
        )
    with Pytest.raises(TypeError):
        DataClasses.replace(InfoData, FormatId="format.other")


# this definition exists because focused behavior needs one stable owner
def CheckBinding() -> None:
    AdapterData = JsonAdapter()
    BindingData = AdapterBinding(reader=AdapterData, writer=AdapterData)
    assert BindingData.reader is AdapterData
    assert BindingData.writer is AdapterData
    assert BindingData.ReaderData is AdapterData
    assert BindingData.WriterData is AdapterData
    assert (
        str(Inspect.signature(AdapterBinding))
        == "(reader: 'CadReaderAdapter | None' = None, writer: 'CadWriterAdapter | None' = None) -> None"
    )
    assert tuple(
        (FieldData.name for FieldData in DataClasses.fields(AdapterBinding))
    ) == ("reader", "writer")
    assert AdapterBinding.__match_args__ == ("reader", "writer")
    assert Pickle.loads(Pickle.dumps(AdapterBinding())).reader is None
    BindingBytes = Pickle.dumps(BindingData, protocol=4)
    assert b"reader" in BindingBytes
    assert b"writer" in BindingBytes
    assert b"ReaderData" not in BindingBytes
    assert b"WriterData" not in BindingBytes
    assert AdapterBinding.__module__ == "convert.adapters.registry"
    assert set(Typing.get_type_hints(AdapterBinding)) == {"reader", "writer"}
    assert (
        str(Inspect.signature(AdapterBinding.__init__))
        == "(self, reader: 'CadReaderAdapter | None' = None, writer: 'CadWriterAdapter | None' = None) -> None"
    )
    with Pytest.raises(TypeError):
        CallCompat(AdapterBinding, reader=AdapterData, ReaderData=AdapterData)
    with Pytest.raises(TypeError):
        CallCompat(AdapterBinding, writer=AdapterData, WriterData=AdapterData)


# this definition exists because focused behavior needs one stable owner
def CheckErrors() -> None:
    LossError = CapabilityLossError(
        format_id="format.test", dropped=frozenset({Capability.BREP})
    )
    assert LossError.format_id == "format.test"
    assert LossError.dropped == frozenset({Capability.BREP})
    ResultData = WriteResult(None, "format.test", 0)
    UsableError = AppUsabilityError(format_id="format.test", result=ResultData)
    assert UsableError.format_id == "format.test"
    assert UsableError.application_usable is False
    for ErrorType in (CapabilityLossError, AppUsabilityError):
        assert ErrorType.__module__ == "convert.adapters.registry"
        assert Pickle.loads(Pickle.dumps(ErrorType)) is ErrorType
    with Pytest.raises(TypeError):
        CallCompat(
            CapabilityLossError,
            "format.test",
            frozenset[Capability](),
            format_id="other",
        )
    with Pytest.raises(TypeError):
        AppUsabilityError("format.test", ResultData, result=ResultData)
    with Pytest.raises(TypeError):
        CallCompat(
            CapabilityLossError,
            format_id="format.test",
            dropped=frozenset[Capability](),
            unknown=True,
        )
    with Pytest.raises(TypeError):
        AppUsabilityError(format_id="format.test", result=ResultData, unknown=True)


# this definition exists because focused behavior needs one stable owner
def CheckRegistry() -> None:
    RegistryData = AdapterRegistry()
    AdapterData = JsonAdapter()
    RegistryData.register(AdapterData)
    for MethodName in (
        "register_reader",
        "register_writer",
        "register",
        "read",
        "read_with_adapter",
        "write",
        "extend",
    ):
        MethodData = getattr(AdapterRegistry, MethodName)
        assert MethodData.__name__ == MethodName
        assert MethodData.__module__ == "convert.adapters.registry"
        assert "NamedValues" not in str(Inspect.signature(MethodData))
        assert Typing.get_type_hints(MethodData)
    with Pytest.raises(TypeError):
        CallCompat(RegistryData.register, AdapterData, unknown=True)
    with Pytest.raises(TypeError):
        CallCompat(
            RegistryData.register,
            AdapterData,
            replace=False,
            ReplaceFlag=False,
        )
    with Pytest.raises(TypeError):
        CallCompat(RegistryData.read, b"{}", unknown=True)
    with Pytest.raises(TypeError):
        CallCompat(
            RegistryData.read,
            b"{}",
            format_id="interchange.json",
            FormatId="interchange.json",
        )
    with Pytest.raises(TypeError):
        CallCompat(RegistryData.write, None, None, unknown=True)
    with Pytest.raises(TypeError):
        CallCompat(RegistryData.extend, (), unknown=True)
    with Pytest.raises(TypeError):
        CallCompat(RegistryData.extend, (), replace=False, ReplaceFlag=False)


# this definition exists because focused behavior needs one stable owner
def CheckRegWords() -> None:
    RegistryData = AdapterRegistry()
    AdapterData = JsonAdapter()
    for MethodName in ("register_reader", "register_writer", "register"):
        MethodData = getattr(RegistryData, MethodName)
        with Pytest.raises(TypeError):
            MethodData(AdapterData, unknown=True)
        with Pytest.raises(TypeError):
            MethodData(AdapterData, replace=False, ReplaceFlag=False)


# this definition exists because focused behavior needs one stable owner
def CheckReadWords() -> None:
    RegistryData = AdapterRegistry()
    for MethodName in ("read", "read_with_adapter"):
        MethodData = getattr(RegistryData, MethodName)
        with Pytest.raises(TypeError):
            MethodData(b"{}", unknown=True)
        with Pytest.raises(TypeError):
            MethodData(b"{}", format_id="test", FormatId="test")
        with Pytest.raises(TypeError):
            MethodData(b"{}", options=None, OptionsData=None)


# this definition exists because focused behavior needs one stable owner
def CheckWriteWords() -> None:
    RegistryData = AdapterRegistry()
    with Pytest.raises(TypeError):
        CallCompat(
            RegistryData.write,
            None,
            None,
            format_id="test",
            FormatId="test",
        )
    with Pytest.raises(TypeError):
        CallCompat(RegistryData.write, None, None, options=None, OptionsData=None)


# this definition exists because focused behavior needs one stable owner
def CheckExports() -> None:
    for TransferType in (CarrierReason, TransferMode):
        assert TransferType.__module__ == "convert.adapters.base"
        assert Pickle.loads(Pickle.dumps(TransferType)) is TransferType
    assert set(AdapterPackage.__all__) == {
        "AdapterBinding",
        "AdapterDiscoveryError",
        "AdapterInfo",
        "AdapterNotFoundError",
        "AdapterRegistry",
        "AdapterRegistryError",
        "AmbiguousAdapterError",
        "ApplicationUsabilityError",
        "CadAdapter",
        "CadReaderAdapter",
        "CadWriterAdapter",
        "CapabilityLossError",
        "CapabilityTransfer",
        "CarrierReason",
        "Destination",
        "ProbeResult",
        "ReadOptions",
        "Source",
        "TransferMode",
        "WriteOptions",
        "WriteResult",
        "is_windows_device_name",
    }
    assert not any((NameValue.endswith("_api") for NameValue in AdapterPackage.__all__))
    assert not hasattr(AdapterPackage, "IsDeviceName")
    assert not hasattr(AdapterPackage, "adapter_protocols")
    assert not hasattr(AdapterPackage, "registry_binding")
    assert not hasattr(AdapterPackage, "registry_errors")


# this binding exists because shared behavior needs one stable value
globals()["ApplicationUsabilityError"] = AppUsabilityError

# this binding exists because shared behavior needs one stable value
globals()["annotations"] = Annotations
