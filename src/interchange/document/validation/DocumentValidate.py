# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from collections.abc import Iterable as IterableBase
from typing import cast as CastValue
from typing import TypeGuard

from interchange.brep.topology.BrepModel import BrepModel
from interchange.document.models.DocumentError import DocumentError
from interchange.document.models.DocumentIdentity import GetIdGroups
from interchange.document.models.DocumentModel import CadDocument  # lgtm[py/cyclic-import]
from interchange.enums.EnumDocument import Capability


# decoded capability collections need runtime checks before validation trusts their members
def HasValidCaps(SourceValue: object) -> bool:
    if not isinstance(SourceValue, frozenset):
        return False
    ItemValues = CastValue(IterableBase[object], SourceValue)
    return all(isinstance(ItemValue, Capability) for ItemValue in ItemValues)


# malformed decoded roots must narrow brep values before topology methods are called
def IsBrepModel(SourceValue: object) -> TypeGuard[BrepModel]:
    return isinstance(SourceValue, BrepModel)


# validation orchestration preserves diagnostic order while focused checks evolve independently
def GetDocErrors(DocumentValue: CadDocument) -> tuple[str, ...]:
    from interchange.document.validation.DocumentAssemblyValidate import GetAssemblyErrs  # lgtm[py/cyclic-import]
    from interchange.document.validation.DocumentFeatureValidate import GetFeatureErrs  # lgtm[py/cyclic-import]
    from interchange.document.validation.DocumentReferenceValidate import GetRefErrors  # lgtm[py/cyclic-import]

    ErrorValues: list[str] = []
    if not HasValidCaps(DocumentValue.capabilities):
        ErrorValues.append("document capabilities must be Capability values")
    IdentitySets: dict[str, set[str]] = {}
    for NameValue, LabelText, ItemValues in GetIdGroups(DocumentValue):
        IdValues = [ItemValue.id for ItemValue in ItemValues]
        if len(IdValues) != len(set(IdValues)):
            ErrorValues.append(f"duplicate {LabelText} id")
        IdentitySets[NameValue] = set(IdValues)
    ErrorValues.extend(GetRefErrors(DocumentValue, IdentitySets))
    ErrorValues.extend(GetFeatureErrs(DocumentValue, IdentitySets))
    BrepValue: object = DocumentValue.brep
    if BrepValue is not None:
        if not IsBrepModel(BrepValue):
            ErrorValues.append("document B-rep must be a BrepModel")
        else:
            ErrorValues.extend(
                BrepValue.GetErrors(
                    frozenset(BodyValue.id for BodyValue in DocumentValue.bodies)
                )
            )
    if DocumentValue.assembly is not None:
        ErrorValues.extend(GetAssemblyErrs(DocumentValue, IdentitySets))
    if not DocumentValue.configurations:
        ErrorValues.append("document has no configuration")
    if (
        not DocumentValue.feature_timeline
        and DocumentValue.brep is None
        and not DocumentValue.brep_payloads
        and not DocumentValue.meshes
        and DocumentValue.assembly is None
    ):
        ErrorValues.append(
            "document has neither feature history, B-rep, mesh, nor assembly data"
        )
    return tuple(ErrorValues)


# explicit assertion gives callers one exception containing every validation failure
def AssertValid(DocumentValue: CadDocument) -> None:
    ErrorValues = GetDocErrors(DocumentValue)
    if ErrorValues:
        raise DocumentError("; ".join(ErrorValues))
