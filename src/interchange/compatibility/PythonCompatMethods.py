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
from typing import Any as AnyValue
from typing import Mapping as TypeMap


# cloned functions preserve canonical methods while historical identities remain independently reflectable
def CloneMethod(
    MethodFunc: AnyValue,
    ClassType: type,
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
) -> AnyValue:
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


# existing descriptors need matching aliases because class and static binding affect call semantics
def BindAliasMut(
    ClassType: type,
    SourceName: str,
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
) -> None:
    DescriptorValue = GetStaticAttr(ClassType, SourceName)
    if isinstance(DescriptorValue, classmethod):
        MethodFunc = DescriptorValue.__func__
        LegacyValue = classmethod(
            CloneMethod(MethodFunc, ClassType, LegacyName, AnnotationMap, SignatureInfo)
        )
    elif isinstance(DescriptorValue, staticmethod):
        MethodFunc = DescriptorValue.__func__
        LegacyValue = staticmethod(
            CloneMethod(MethodFunc, ClassType, LegacyName, AnnotationMap, SignatureInfo)
        )
    else:
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
    ClassType: type,
    MethodFunc: AnyValue,
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
) -> None:
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
    ClassType: type,
    MethodFunc: AnyValue,
    LegacyName: str,
    AnnotationMap: TypeMap[str, str],
    SignatureInfo: FuncSig,
) -> None:
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
    ParamKind: AnyValue = FuncParam.POSITIONAL_OR_KEYWORD,
    DefaultValue: AnyValue = FuncParam.empty,
    AnnotValue: AnyValue = FuncParam.empty,
) -> FuncParam:
    return FuncParam(
        ParamName,
        ParamKind,
        default=DefaultValue,
        annotation=AnnotValue,
    )


# compact signature data keeps historical method contracts readable in focused binders
def MakeLegacySig(
    ParamSpecs: tuple[tuple[AnyValue, ...], ...],
    ReturnAnnot: AnyValue,
) -> FuncSig:
    ParamValues = []
    for SpecValue in ParamSpecs:
        ParamName = SpecValue[0]
        AnnotValue = SpecValue[1] if len(SpecValue) > 1 else FuncParam.empty
        DefaultValue = SpecValue[2] if len(SpecValue) > 2 else FuncParam.empty
        ParamKind = (
            SpecValue[3] if len(SpecValue) > 3 else FuncParam.POSITIONAL_OR_KEYWORD
        )
        ParamValues.append(MakeParam(ParamName, ParamKind, DefaultValue, AnnotValue))
    return FuncSig(ParamValues, return_annotation=ReturnAnnot)
