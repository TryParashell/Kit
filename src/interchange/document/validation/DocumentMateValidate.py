# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

from interchange.assembly.AssemblyData import AssemblyData  # lgtm[py/cyclic-import]
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.MateEntity import MateEntity
from interchange.document.models.DocumentModel import CadDocument  # lgtm[py/cyclic-import]


# mate checks protect entity ownership and parameter references across component documents
def GetMateErrors(
    DocumentValue: CadDocument,
    AssemblyValue: AssemblyData,
    Definitions: TypeMap[str, ComponentDef],
    Entities: TypeMap[str, MateEntity],
    DocumentValues: TypeMap[str, CadDocument],
    IdentitySets: TypeMap[str, set[str]],
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    for MateValue in AssemblyValue.mates:
        if MateValue.owner_definition_id not in Definitions:
            ErrorValues.append(
                f"mate {MateValue.id} references missing owner definition"
            )
        if not MateValue.entity_ids:
            ErrorValues.append(f"mate {MateValue.id} has no entities")
        for EntityId in MateValue.entity_ids:
            EntityValue = Entities.get(EntityId)
            if EntityValue is None:
                ErrorValues.append(
                    f"mate {MateValue.id} references missing entity {EntityId}"
                )
            elif EntityValue.owner_definition_id != MateValue.owner_definition_id:
                ErrorValues.append(
                    f"mate {MateValue.id} references entity from another assembly"
                )
        OwnerDef = Definitions.get(MateValue.owner_definition_id)
        TargetDocument: CadDocument | None = DocumentValue
        if OwnerDef is not None and OwnerDef.document_id:
            TargetDocument = DocumentValues.get(OwnerDef.document_id)
        if TargetDocument is not None:
            TargetParamIds = (
                IdentitySets["parameters"]
                if TargetDocument is DocumentValue
                else {ParamValue.id for ParamValue in TargetDocument.parameters}
            )
            for ParameterId in MateValue.parameter_ids:
                if ParameterId not in TargetParamIds:
                    ErrorValues.append(
                        f"mate {MateValue.id} references missing parameter {ParameterId}"
                    )
    return tuple(ErrorValues)
