# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Any as AnyValue
from typing import Mapping as TypeMap


# timeline checks protect ordering and every feature dependency from invalid references
def GetFeatureErrs(
    DocumentValue: AnyValue, IdentitySets: TypeMap[str, set[str]]
) -> tuple[str, ...]:
    ErrorValues: list[str] = []
    FeatureOrders = {
        FeatureValue.EntityId: FeatureValue.Order
        for FeatureValue in DocumentValue.FeatureTimeline
    }
    if len(FeatureOrders) != len(DocumentValue.FeatureTimeline):
        ErrorValues.append("feature ids are not unique")
    if len(
        {FeatureValue.Order for FeatureValue in DocumentValue.FeatureTimeline}
    ) != len(DocumentValue.FeatureTimeline):
        ErrorValues.append("feature order values are not unique")
    for FeatureValue in DocumentValue.FeatureTimeline:
        if (
            FeatureValue.SketchId
            and FeatureValue.SketchId not in IdentitySets["Sketches"]
        ):
            ErrorValues.append(
                f"feature {FeatureValue.EntityId} references missing sketch"
            )
        for InputId in FeatureValue.InputFeatureIds:
            if InputId not in FeatureOrders:
                ErrorValues.append(
                    f"feature {FeatureValue.EntityId} references missing input {InputId}"
                )
            elif FeatureOrders[InputId] >= FeatureValue.Order:
                ErrorValues.append(
                    f"feature {FeatureValue.EntityId} has a forward dependency"
                )
        for ParameterId in FeatureValue.ParameterIds:
            if ParameterId not in IdentitySets["Parameters"]:
                ErrorValues.append(
                    f"feature {FeatureValue.EntityId} references missing parameter"
                )
        for SelectionId in FeatureValue.SelectionIds:
            if SelectionId not in IdentitySets["Selections"]:
                ErrorValues.append(
                    f"feature {FeatureValue.EntityId} references missing selection"
                )
    for BodyValue in DocumentValue.Bodies:
        if BodyValue.FinalFeatureId not in IdentitySets["FeatureTimeline"]:
            ErrorValues.append(
                f"body {BodyValue.EntityId} references missing final feature"
            )
    return tuple(ErrorValues)
