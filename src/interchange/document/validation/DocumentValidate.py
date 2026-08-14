# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue

from interchange.brep.topology.BrepModel import BrepModel
from interchange.document.models.DocumentError import DocumentError
from interchange.document.models.DocumentIdentity import GetIdGroups
from interchange.enums.EnumDocument import Capability


# validation orchestration preserves diagnostic order while focused checks evolve independently
def GetDocErrors(DocumentValue: AnyValue) -> tuple[str, ...]:
    from interchange.document.validation.DocumentAssemblyValidate import GetAssemblyErrs
    from interchange.document.validation.DocumentFeatureValidate import GetFeatureErrs
    from interchange.document.validation.DocumentReferenceValidate import GetRefErrors

    ErrorValues: list[str] = []
    if not isinstance(DocumentValue.Capabilities, frozenset) or any(
        not isinstance(CapabilityValue, Capability)
        for CapabilityValue in DocumentValue.Capabilities
    ):
        ErrorValues.append("document capabilities must be Capability values")
    IdentitySets: dict[str, set[str]] = {}
    for NameValue, LabelText, ItemValues in GetIdGroups(DocumentValue):
        IdValues = [ItemValue.EntityId for ItemValue in ItemValues]
        if len(IdValues) != len(set(IdValues)):
            ErrorValues.append(f"duplicate {LabelText} id")
        CanonicalName = NameValue.title().replace("_", "")
        IdentitySets[CanonicalName] = set(IdValues)
    ErrorValues.extend(GetRefErrors(DocumentValue, IdentitySets))
    ErrorValues.extend(GetFeatureErrs(DocumentValue, IdentitySets))
    if DocumentValue.BrepModel is not None:
        if not isinstance(DocumentValue.BrepModel, BrepModel):
            ErrorValues.append("document B-rep must be a BrepModel")
        else:
            ErrorValues.extend(
                DocumentValue.BrepModel.GetErrors(
                    frozenset(BodyValue.EntityId for BodyValue in DocumentValue.Bodies)
                )
            )
    if DocumentValue.Assembly is not None:
        ErrorValues.extend(GetAssemblyErrs(DocumentValue, IdentitySets))
    if not DocumentValue.Configurations:
        ErrorValues.append("document has no configuration")
    if (
        not DocumentValue.FeatureTimeline
        and DocumentValue.BrepModel is None
        and not DocumentValue.BrepPayloads
        and not DocumentValue.Meshes
        and DocumentValue.Assembly is None
    ):
        ErrorValues.append(
            "document has neither feature history, B-rep, mesh, nor assembly data"
        )
    return tuple(ErrorValues)


# explicit assertion gives callers one exception containing every validation failure
def AssertValid(DocumentValue: AnyValue) -> None:
    ErrorValues = GetDocErrors(DocumentValue)
    if ErrorValues:
        raise DocumentError("; ".join(ErrorValues))
