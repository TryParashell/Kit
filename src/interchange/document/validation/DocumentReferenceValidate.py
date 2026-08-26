# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.document.models.DocumentModel import (  # lgtm[py/cyclic-import]
    CadDocument,
)


# configuration checks protect inheritance and override links from dangling identifiers
def GetConfigErrs(
    DocumentValue: CadDocument, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for ConfigValue in DocumentValue.configurations:
        if (
            ConfigValue.parent_id
            and ConfigValue.parent_id not in IdentitySets["configurations"]
        ):
            ErrorValues.append(f"configuration {ConfigValue.id} has missing parent")
        for OverrideValue in ConfigValue.overrides:
            if OverrideValue.parameter_id not in IdentitySets["parameters"]:
                ErrorValues.append(
                    f"configuration {ConfigValue.id} references missing parameter {OverrideValue.parameter_id}"
                )
    return tuple(ErrorValues)


# parameter checks protect expression dependency links from dangling identifiers
def GetParamErrs(
    DocumentValue: CadDocument, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for ParamValue in DocumentValue.parameters:
        if ParamValue.expression:
            for ReferenceValue in ParamValue.expression.parameter_ids:
                if ReferenceValue not in IdentitySets["parameters"]:
                    ErrorValues.append(
                        f"parameter {ParamValue.id} references missing parameter {ReferenceValue}"
                    )
    return tuple(ErrorValues)


# plane checks protect geometric support and offset links from dangling identifiers
def GetPlaneErrs(
    DocumentValue: CadDocument, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for PlaneValue in DocumentValue.support_planes:
        if (
            PlaneValue.support_selection_id
            and PlaneValue.support_selection_id not in IdentitySets["selections"]
        ):
            ErrorValues.append(f"plane {PlaneValue.id} references missing selection")
        if (
            PlaneValue.offset_parameter_id
            and PlaneValue.offset_parameter_id not in IdentitySets["parameters"]
        ):
            ErrorValues.append(
                f"plane {PlaneValue.id} references missing offset parameter"
            )
    return tuple(ErrorValues)


# sketch checks protect support constraint and parameter links from dangling identifiers
def GetSketchErrs(
    DocumentValue: CadDocument, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for SketchValue in DocumentValue.sketches:
        if SketchValue.support_plane_id not in IdentitySets["support_planes"]:
            ErrorValues.append(f"sketch {SketchValue.id} references missing plane")
        EntityIds = {EntityValue.id for EntityValue in SketchValue.entities}
        for RelationValue in SketchValue.constraints:
            for ReferenceValue in RelationValue.references:
                if ReferenceValue.entity_id not in EntityIds:
                    ErrorValues.append(
                        f"constraint {RelationValue.id} references missing entity {ReferenceValue.entity_id}"
                    )
            if (
                RelationValue.parameter_id
                and RelationValue.parameter_id not in IdentitySets["parameters"]
            ):
                ErrorValues.append(
                    f"constraint {RelationValue.id} references missing parameter"
                )
    return tuple(ErrorValues)


# reference validation preserves historical diagnostic ordering across focused checks
def GetRefErrors(
    DocumentValue: CadDocument, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    return (
        *GetConfigErrs(DocumentValue, IdentitySets),
        *GetParamErrs(DocumentValue, IdentitySets),
        *GetPlaneErrs(DocumentValue, IdentitySets),
        *GetSketchErrs(DocumentValue, IdentitySets),
    )
