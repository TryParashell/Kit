# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap

# renamed fields retain historical keys so serialized documents remain byte compatible
KWireFields: TypeMap[str, str] = {
    "AxisVector": "axis",
    "BrepModel": "brep",
    "ConfigStates": "configuration_states",
    "EndPoint": "end",
    "EntityId": "id",
    "EntityKind": "kind",
    "EntityName": "name",
    "ErrorCode": "code",
    "FilePath": "path",
    "IsActive": "active",
    "IsClosed": "closed",
    "IsConstruction": "construction",
    "IsCopy": "copy",
    "IsDegenerate": "degenerate",
    "IsDriving": "driving",
    "IsExcludedBom": "exclude_from_bom",
    "IsFixed": "fixed",
    "IsFlexible": "flexible",
    "HasSameSense": "same_sense",
    "IsHidden": "hidden",
    "IsOuter": "outer",
    "IsOutward": "outward",
    "IsPeriodic": "periodic",
    "IsPeriodicU": "periodic_u",
    "IsPeriodicV": "periodic_v",
    "IsReversed": "reversed",
    "IsSolid": "solid",
    "IsSuppressed": "suppressed",
    "IsSymmetric": "symmetric",
    "IsValid": "valid",
    "Level": "severity",
    "MessageText": "message",
    "KnotValues": "knots",
    "KnotValuesU": "knots_u",
    "KnotValuesV": "knots_v",
    "ParamOverrideIds": "parameter_override_ids",
    "PayloadData": "data",
    "PointName": "point",
    "RefDirection": "reference_direction",
    "SchemaText": "schema",
    "SecondUpToRef": "second_up_to_reference",
    "SelectionPath": "path",
    "SourceDigest": "sha256",
    "UnitName": "unit",
    "ValueMode": "mode",
    "ValueRole": "role",
    "VariableRadiusParamIds": "variable_radius_parameter_ids",
    "XCoord": "x",
    "YCoord": "y",
    "ZCoord": "z",
}


# record specific names resolve collisions without weakening the historical wire contract
KTypeWireFields: TypeMap[str, TypeMap[str, str]] = {
    "BrepVertex": {"Point": "point"},
    "CadSource": {"FilePath": "path"},
    "ComponentDef": {"SourceDigest": "source_sha256"},
    "ConstraintRef": {"EntityId": "entity_id"},
    "Diagnostic": {"EntityId": "entity_id"},
    "PointGeometry": {"Point": "point"},
    "Selection": {"Point": "point", "SelectionPath": "path"},
    "SelectPathElem": {
        "EntityId": "entity_id",
        "EntityKind": "entity_kind",
    },
}
