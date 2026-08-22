# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import asdict as AsDict
from dataclasses import is_dataclass as IsDataclass
from enum import Enum as EnumBase
from importlib import import_module as ImportModule
from inspect import getattr_static as GetStaticAttr
from inspect import signature as GetSignature
import pickle as PickleCodec
from types import FunctionType as FuncType
from typing import Protocol, cast as TypeCast, runtime_checkable, TypeVar

import interchange as InterchangeApi
from interchange.serialization import KTypeRegistry
from interchange.serialization import from_data as FromData
from interchange.serialization import to_data as ToData

from tests.interchange.compatibility.PythonCompatEnumNames import KCompatEnumNames
from tests.interchange.compatibility.PythonCompatFacades import KPythonCompatFacades
from tests.interchange.compatibility.PythonCompatMethods import KPythonCompatMethods
from tests.interchange.compatibility.PythonCompatPickles import KPythonCompatPickles
from tests.interchange.compatibility.CompatFieldsAssembly import KCompatFieldsAssembly
from tests.interchange.compatibility.CompatFieldsBrep import KCompatFieldsBrep
from tests.interchange.compatibility.CompatFieldsDocument import KCompatFieldsDocument
from tests.interchange.compatibility.CompatFieldsGeometry import KCompatFieldsGeometry
from tests.interchange.compatibility.CompatFieldsHistory import KCompatFieldsHistory
from tests.interchange.compatibility.CompatFieldsMesh import KCompatFieldsMesh
from tests.interchange.compatibility.CompatFieldsTypes import KCompatFieldsTypes
from tests.interchange.compatibility.PythonCompatTopNames import KPythonCompatTopNames

# compatibility construction must validate dynamic calls before tests trust their concrete result
CompatType = TypeVar("CompatType")


# historical constructors remain callable even when reflected keywords differ from storage names
def CallLegacy(
    ClassType: type[CompatType],
    *ArgValues: object,
    **NamedValues: object,
) -> CompatType:
    FactoryValue: object = ClassType
    if not callable(FactoryValue):
        raise TypeError("compatibility constructor is not callable")
    ResultValue: object = FactoryValue(*ArgValues, **NamedValues)
    if not isinstance(ResultValue, ClassType):
        raise TypeError("compatibility constructor returned the wrong model")
    return ResultValue


# split field expectations combine here so reflection checks use one immutable sequence
KPythonCompatFields = (
    *KCompatFieldsAssembly,
    *KCompatFieldsBrep,
    *KCompatFieldsDocument,
    *KCompatFieldsGeometry,
    *KCompatFieldsHistory,
    *KCompatFieldsMesh,
    *KCompatFieldsTypes,
)


# reflection assertions require the narrow dataclass field surface shared by supported records
class CompatField(Protocol):
    name: str
    kw_only: bool


# reflection assertions require the dataclass metadata exposed by every supported compatibility record
class CompatDataclass(Protocol):
    __match_args__: tuple[str, ...]
    __annotations__: dict[str, object]
    __dataclass_fields__: dict[str, CompatField]


# descriptor checks need a runtime structural contract for wrapped class and static methods
@runtime_checkable
class MethodDescriptor(Protocol):

    @property
    def __func__(self) -> FuncType: ...  # lgtm[py/ineffectual-statement]


# top level names are contractual because adapters historically imported them without module qualification
def CheckTopLevel() -> None:
    assert set(InterchangeApi.__all__) == set(KPythonCompatTopNames)
    for NameText in KPythonCompatTopNames:
        assert hasattr(InterchangeApi, NameText)


# explicit facade exports prevent compatibility from leaking current implementation details
def CheckExports() -> None:
    for ModuleName, ExportNames in KPythonCompatFacades:
        ModuleValue = ImportModule(ModuleName)
        assert ModuleValue.__all__ == ExportNames
        for ExportName in ExportNames:
            assert getattr(ModuleValue, ExportName) is getattr(
                InterchangeApi, ExportName, getattr(ModuleValue, ExportName)
            )


# dataclass reflection must stay standard because callers use matching fields annotations and asdict
def CheckClasses() -> None:
    for QualifiedName, FieldNames in KPythonCompatFields:
        ModuleName, ClassName = QualifiedName.rsplit(".", 1)
        ClassType = TypeCast(type[object], getattr(ImportModule(ModuleName), ClassName))
        assert IsDataclass(ClassType)
        DataclassType = TypeCast(type[CompatDataclass], ClassType)
        assert ClassType.__name__ == ClassName
        assert ClassType.__qualname__ == ClassName
        assert ClassType.__module__ == ModuleName
        assert (
            tuple(
                FieldValue.name
                for FieldValue in DataclassType.__dataclass_fields__.values()
            )
            == FieldNames
        )
        assert DataclassType.__match_args__ == tuple(
            FieldValue.name
            for FieldValue in DataclassType.__dataclass_fields__.values()
            if not FieldValue.kw_only
        )
        assert tuple(DataclassType.__annotations__) == tuple(
            FieldValue.name
            for FieldValue in DataclassType.__dataclass_fields__.values()
            if FieldValue.name in DataclassType.__annotations__
        )


# representative values prove standard mapping reflection and positional matching remain functional
def CheckReflection() -> None:
    VectorValue = InterchangeApi.Vector2(1.0, 2.0)
    assert AsDict(VectorValue) == {"x": 1.0, "y": 2.0}
    assert (
        str(GetSignature(InterchangeApi.Vector2)) == "(x: 'float', y: 'float') -> None"
    )
    assert InterchangeApi.Vector2.__match_args__ == ("x", "y")
    assert repr(VectorValue) == "Vector2(x=1.0, y=2.0)"


# historical methods remain ordinary reflected descriptors instead of transparent lookup aliases
def CheckMethods() -> None:
    for QualifiedName, MethodNames in KPythonCompatMethods:
        ModuleName, ClassName = QualifiedName.rsplit(".", 1)
        ClassType = getattr(ImportModule(ModuleName), ClassName)
        for MethodName in MethodNames:
            DescriptorValue = GetStaticAttr(ClassType, MethodName)
            RawMethod: object = (
                DescriptorValue.__func__
                if isinstance(DescriptorValue, MethodDescriptor)
                else DescriptorValue
            )
            if not isinstance(RawMethod, FuncType):
                raise TypeError(f"compatibility method {MethodName} is not a function")
            MethodValue = RawMethod
            assert MethodValue.__name__ == MethodName
            assert MethodValue.__qualname__ == f"{ClassName}.{MethodName}"
            assert MethodValue.__module__ == ModuleName


# every public enum exposes historical names without changing its stable wire values
def CheckEnumNames() -> None:
    for TypeName in KCompatEnumNames:
        EnumType = getattr(InterchangeApi, TypeName)
        assert issubclass(EnumType, EnumBase)
        for MemberValue in EnumType:
            assert (
                MemberValue.name
                == MemberValue.value.upper()
                .replace("mm", "MILLIMETER")
                .replace("in", "INCH")
                or getattr(EnumType, MemberValue.name) is MemberValue
            )
            assert getattr(EnumType, MemberValue.name) is MemberValue


# adapters require the exact historical constructor attribute and predicate contract
def CheckAdapters() -> None:
    ValuesSet = frozenset({InterchangeApi.Capability.KParameters})
    AdapterValue = CallLegacy(InterchangeApi.AdapterCapabilities, values=ValuesSet)
    assert AdapterValue.values == ValuesSet
    assert AdapterValue.supports(InterchangeApi.Capability.KParameters)
    assert not AdapterValue.supports(InterchangeApi.Capability.KBrep)
    assert (
        str(GetSignature(InterchangeApi.AdapterCapabilities))
        == "(values: 'frozenset[Capability]' = frozenset()) -> None"
    )
    assert FromData(ToData(AdapterValue)) == AdapterValue


# historical global identities ensure existing pickle streams resolve after internal module splits
def CheckPickle() -> None:
    ValuesSet = frozenset({InterchangeApi.Capability.KParameters})
    SourceValues = (
        InterchangeApi.Vector2(1.0, 2.0),
        CallLegacy(InterchangeApi.AdapterCapabilities, values=ValuesSet),
        InterchangeApi.FeatureConfigurationState("default"),
        InterchangeApi.Matrix4(),
    )
    for SourceValue in SourceValues:
        RestoredValue = PickleCodec.loads(PickleCodec.dumps(SourceValue))
        assert RestoredValue == SourceValue
        assert type(RestoredValue) is type(SourceValue)


# authentic baseline bytes ensure loading does not only work for newly emitted streams
def CheckOldPickle() -> None:
    ExpectedValues = (
        InterchangeApi.Vector2(1, 2),
        CallLegacy(
            InterchangeApi.AdapterCapabilities,
            frozenset({InterchangeApi.Capability.KParameters}),
        ),
        InterchangeApi.FeatureConfigurationState("x"),
        InterchangeApi.Matrix4(),
    )
    for PickleText, ExpectedValue in zip(KPythonCompatPickles, ExpectedValues):
        RestoredValue = PickleCodec.loads(bytes.fromhex(PickleText))
        assert RestoredValue == ExpectedValue
        assert type(RestoredValue) is type(ExpectedValue)


# lowercase serialization imports remain first class historical functions rather than accidental aliases
def CheckSerialApi() -> None:
    SerializeModule = ImportModule("interchange.serialization")
    for FunctionName in dict(KPythonCompatFacades)["interchange.serialization"]:
        FunctionValue = getattr(SerializeModule, FunctionName)
        assert FunctionValue.__name__ == FunctionName
        assert FunctionValue.__qualname__ == FunctionName
        assert FunctionValue.__module__ == "interchange.serialization"
        assert PickleCodec.loads(PickleCodec.dumps(FunctionValue)) is FunctionValue


# registration remains restricted to historical public models and enums despite split implementation imports
def CheckRegistry() -> None:
    IntendedTypes = {
        getattr(ImportModule(ModuleName), ExportName)
        for ModuleName, ExportNames in KPythonCompatFacades
        for ExportName in ExportNames
        if isinstance(getattr(ImportModule(ModuleName), ExportName), type)
        and (
            hasattr(
                getattr(ImportModule(ModuleName), ExportName), "__dataclass_fields__"
            )
            or issubclass(getattr(ImportModule(ModuleName), ExportName), EnumBase)
        )
    }
    assert set(KTypeRegistry.values()) == IntendedTypes
    assert set(KTypeRegistry) == {ClassType.__name__ for ClassType in IntendedTypes}
