# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# historical types fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsTypes = (
    ("interchange.types.BoundingBox", ("minimum", "maximum")),
    (
        "interchange.types.CadSource",
        (
            "format_id",
            "path",
            "sha256",
            "container_version",
            "application_version",
            "attributes",
        ),
    ),
    (
        "interchange.types.Configuration",
        (
            "id",
            "name",
            "active",
            "parent_id",
            "overrides",
            "suppressed_feature_ids",
            "attributes",
        ),
    ),
    (
        "interchange.types.Diagnostic",
        ("code", "message", "severity", "entity_id", "provenance", "attributes"),
    ),
    ("interchange.types.Expression", ("source", "parameter_ids", "language")),
    (
        "interchange.types.Parameter",
        (
            "id",
            "name",
            "value",
            "role",
            "expression",
            "owner_id",
            "provenance",
            "attributes",
        ),
    ),
    ("interchange.types.ParameterOverride", ("parameter_id", "value")),
    ("interchange.types.ParameterValue", ("value", "kind", "unit")),
    (
        "interchange.types.Provenance",
        ("adapter", "native_id", "confidence", "spans", "attributes"),
    ),
    ("interchange.types.ProvenanceSpan", ("stream", "offset", "length", "record_kind")),
    ("interchange.types.Transform", ("origin", "x_axis", "y_axis", "z_axis")),
    ("interchange.types.Vector2", ("x", "y")),
    ("interchange.types.Vector3", ("x", "y", "z")),
)
