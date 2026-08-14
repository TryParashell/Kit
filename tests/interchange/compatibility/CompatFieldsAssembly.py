# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# historical assembly fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsAssembly = (
    (
        "interchange.assembly.AssemblyData",
        (
            "root_definition_id",
            "definitions",
            "instances",
            "documents",
            "mate_entities",
            "mates",
            "mate_groups",
            "attributes",
        ),
    ),
    (
        "interchange.assembly.ComponentDefinition",
        (
            "id",
            "name",
            "kind",
            "document_id",
            "configuration_name",
            "configuration_id",
            "bounding_box",
            "body_ids",
            "mesh_ids",
            "source_path",
            "source_format_id",
            "source_sha256",
            "provenance",
            "attributes",
        ),
    ),
    ("interchange.assembly.ComponentDocument", ("id", "document")),
    (
        "interchange.assembly.ComponentInstance",
        (
            "id",
            "name",
            "definition_id",
            "owner_definition_id",
            "transform",
            "order",
            "reference_number",
            "configuration_name",
            "configuration_id",
            "suppressed",
            "hidden",
            "fixed",
            "flexible",
            "exclude_from_bom",
            "provenance",
            "attributes",
        ),
    ),
    (
        "interchange.assembly.MateConstraint",
        (
            "id",
            "name",
            "kind",
            "owner_definition_id",
            "entity_ids",
            "order",
            "value",
            "parameter_ids",
            "alignment",
            "suppressed",
            "driving",
            "provenance",
            "attributes",
        ),
    ),
    (
        "interchange.assembly.MateEntity",
        (
            "id",
            "owner_definition_id",
            "instance_path",
            "kind",
            "source_entity_id",
            "selection_id",
            "frame",
            "radius",
            "provenance",
            "attributes",
        ),
    ),
    (
        "interchange.assembly.MateGroup",
        (
            "id",
            "name",
            "owner_definition_id",
            "mate_ids",
            "parent_group_id",
            "order",
            "provenance",
            "attributes",
        ),
    ),
    ("interchange.assembly.Matrix4", ("values",)),
)
