# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue
from typing import Mapping as TypeMap


# configuration checks protect inheritance and override links from dangling identifiers
def GetConfigErrs(
    DocumentValue: AnyValue, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for ConfigValue in DocumentValue.Configurations:
        if (
            ConfigValue.ParentId
            and ConfigValue.ParentId not in IdentitySets["Configurations"]
        ):
            ErrorValues.append(
                f"configuration {ConfigValue.EntityId} has missing parent"
            )
        for OverrideValue in ConfigValue.Overrides:
            if OverrideValue.ParameterId not in IdentitySets["Parameters"]:
                ErrorValues.append(
                    f"configuration {ConfigValue.EntityId} references missing parameter {OverrideValue.ParameterId}"
                )
    return tuple(ErrorValues)


# parameter checks protect expression dependency links from dangling identifiers
def GetParamErrs(
    DocumentValue: AnyValue, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for ParamValue in DocumentValue.Parameters:
        if ParamValue.Expression:
            for ReferenceValue in ParamValue.Expression.ParameterIds:
                if ReferenceValue not in IdentitySets["Parameters"]:
                    ErrorValues.append(
                        f"parameter {ParamValue.EntityId} references missing parameter {ReferenceValue}"
                    )
    return tuple(ErrorValues)


# plane checks protect geometric support and offset links from dangling identifiers
def GetPlaneErrs(
    DocumentValue: AnyValue, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for PlaneValue in DocumentValue.SupportPlanes:
        if (
            PlaneValue.SupportSelectionId
            and PlaneValue.SupportSelectionId not in IdentitySets["Selections"]
        ):
            ErrorValues.append(
                f"plane {PlaneValue.EntityId} references missing selection"
            )
        if (
            PlaneValue.OffsetParameterId
            and PlaneValue.OffsetParameterId not in IdentitySets["Parameters"]
        ):
            ErrorValues.append(
                f"plane {PlaneValue.EntityId} references missing offset parameter"
            )
    return tuple(ErrorValues)


# sketch checks protect support constraint and parameter links from dangling identifiers
def GetSketchErrs(
    DocumentValue: AnyValue, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for SketchValue in DocumentValue.Sketches:
        if SketchValue.SupportPlaneId not in IdentitySets["SupportPlanes"]:
            ErrorValues.append(
                f"sketch {SketchValue.EntityId} references missing plane"
            )
        EntityIds = {EntityValue.EntityId for EntityValue in SketchValue.Entities}
        for RelationValue in SketchValue.Constraints:
            for ReferenceValue in RelationValue.References:
                if ReferenceValue.EntityId not in EntityIds:
                    ErrorValues.append(
                        f"constraint {RelationValue.EntityId} references missing entity {ReferenceValue.EntityId}"
                    )
            if (
                RelationValue.ParameterId
                and RelationValue.ParameterId not in IdentitySets["Parameters"]
            ):
                ErrorValues.append(
                    f"constraint {RelationValue.EntityId} references missing parameter"
                )
    return tuple(ErrorValues)


# reference validation preserves historical diagnostic ordering across focused checks
def GetRefErrors(
    DocumentValue: AnyValue, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    return (
        *GetConfigErrs(DocumentValue, IdentitySets),
        *GetParamErrs(DocumentValue, IdentitySets),
        *GetPlaneErrs(DocumentValue, IdentitySets),
        *GetSketchErrs(DocumentValue, IdentitySets),
    )
