# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from inspect import getattr_static as GetStaticAttr
from inspect import Parameter as FuncParam
from inspect import Signature as FuncSig
from types import FunctionType as FuncType
from typing import cast as CastValue
from typing import Mapping as TypeMap
from typing import TypeAlias

# historical signature rows accept only the four parameter shapes used by public facades
CompatParam: TypeAlias = (
    tuple[str]
    | tuple[str, str]
    | tuple[str, str, object]
    | tuple[str, str, object, object]
)


# descriptor internals cross generic stdlib types so their concrete function shape is checked once
def GetMethodFunc(SourceValue: object, SourceName: str) -> FuncType:
    MethodValue: object = getattr(SourceValue, "__func__", None)
    if not isinstance(MethodValue, FuncType):
        raise TypeError(f"{SourceName} is not a Python function")
    return MethodValue


# cloned functions preserve canonical methods while historical identities remain independently reflectable
def CloneMethod(
    MethodFunc: FuncType,
    ClassType: type[object],
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
) -> FuncType:
    LegacyFunc = FuncType(
        MethodFunc.__code__,
        MethodFunc.__globals__,
        LegacyName,
        MethodFunc.__defaults__,
        MethodFunc.__closure__,
    )
    LegacyFunc.__kwdefaults__ = MethodFunc.__kwdefaults__
    LegacyFunc.__dict__.update(MethodFunc.__dict__)
    LegacyFunc.__annotations__ = dict(AnnotationMap)
    LegacyFunc.__qualname__ = f"{ClassType.__name__}.{LegacyName}"
    LegacyFunc.__module__ = ClassType.__module__
    setattr(LegacyFunc, "__signature__", SignatureInfo)
    return LegacyFunc


# concrete compatibility methods take precedence because their signatures remain statically visible
def GetAliasSource(ClassType: type[object], SourceName: str, LegacyName: str) -> object:
    try:
        return GetStaticAttr(ClassType, LegacyName)
    except AttributeError:
        return GetStaticAttr(ClassType, SourceName)


# existing descriptors need matching aliases because class and static binding affect call semantics
def BindAliasMut(
    ClassType: type[object],
    SourceName: str,
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
) -> None:
    DescriptorValue = GetAliasSource(ClassType, SourceName, LegacyName)
    LegacyValue: object
    if isinstance(DescriptorValue, classmethod):
        MethodValue = GetMethodFunc(CastValue(object, DescriptorValue), SourceName)
        LegacyValue = classmethod(
            CloneMethod(
                MethodValue, ClassType, LegacyName, AnnotationMap, SignatureInfo
            )
        )
    elif isinstance(DescriptorValue, staticmethod):
        MethodValue = GetMethodFunc(CastValue(object, DescriptorValue), SourceName)
        LegacyValue = staticmethod(
            CloneMethod(
                MethodValue, ClassType, LegacyName, AnnotationMap, SignatureInfo
            )
        )
    else:
        if not isinstance(DescriptorValue, FuncType):
            raise TypeError(f"{SourceName} is not a Python function")
        LegacyValue = CloneMethod(
            DescriptorValue,
            ClassType,
            LegacyName,
            AnnotationMap,
            SignatureInfo,
        )
    setattr(ClassType, LegacyName, LegacyValue)


# split free functions need instance descriptors when historical classes owned their behavior
def BindDirectMut(
    ClassType: type[object],
    MethodFunc: object,
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
) -> None:
    if not isinstance(MethodFunc, FuncType):
        raise TypeError(f"{LegacyName} is not a Python function")
    LegacyFunc = CloneMethod(
        MethodFunc,
        ClassType,
        LegacyName,
        AnnotationMap,
        SignatureInfo,
    )
    setattr(ClassType, LegacyName, LegacyFunc)


# split lookup functions need static descriptors matching their historical class ownership
def BindStaticMut(
    ClassType: type[object],
    MethodFunc: object,
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
) -> None:
    if not isinstance(MethodFunc, FuncType):
        raise TypeError(f"{LegacyName} is not a Python function")
    LegacyFunc = CloneMethod(
        MethodFunc,
        ClassType,
        LegacyName,
        AnnotationMap,
        SignatureInfo,
    )
    setattr(ClassType, LegacyName, staticmethod(LegacyFunc))


# compact parameter creation keeps exact historical signatures declarative and consistent
def MakeParam(
    ParamName: str,
    ParamKind: object = FuncParam.POSITIONAL_OR_KEYWORD,
    DefaultValue: object = FuncParam.empty,
    AnnotValue: object = FuncParam.empty,
) -> FuncParam:
    if not isinstance(ParamKind, type(FuncParam.POSITIONAL_OR_KEYWORD)):
        raise TypeError("parameter kind must be an inspect parameter kind")
    return FuncParam(
        ParamName,
        ParamKind,
        default=DefaultValue,
        annotation=AnnotValue,
    )


# compact signature data keeps historical method contracts readable in focused binders
def MakeLegacySig(
    ParamSpecs: tuple[CompatParam, ...],
    ReturnAnnot: str,
) -> FuncSig:
    ParamValues: list[FuncParam] = []
    for SpecValue in ParamSpecs:
        ParamName = SpecValue[0]
        AnnotValue: object = SpecValue[1] if len(SpecValue) > 1 else FuncParam.empty
        DefaultValue: object = SpecValue[2] if len(SpecValue) > 2 else FuncParam.empty
        ParamKind = (
            SpecValue[3] if len(SpecValue) > 3 else FuncParam.POSITIONAL_OR_KEYWORD
        )
        ParamValues.append(MakeParam(ParamName, ParamKind, DefaultValue, AnnotValue))
    return FuncSig(ParamValues, return_annotation=ReturnAnnot)
