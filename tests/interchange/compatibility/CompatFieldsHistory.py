# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# historical history fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsHistory = (
    ("interchange.history.AdapterCapabilities", ("values",)),
    (
        "interchange.history.Body",
        (
            "id",
            "name",
            "final_feature_id",
            "topology",
            "material_id",
            "provenance",
            "attributes",
        ),
    ),
    (
        "interchange.history.BrepPayload",
        (
            "id",
            "format_id",
            "kind",
            "schema",
            "sha256",
            "data",
            "source_stream",
            "provenance",
            "attributes",
            "role",
            "file_extension",
        ),
    ),
    (
        "interchange.history.ChamferFeature",
        ("distance", "mode", "second_distance", "angle"),
    ),
    (
        "interchange.history.CircularPatternFeature",
        ("angle", "instance_count", "axis_selection_id", "reversed"),
    ),
    ("interchange.history.CombineFeature", ("operation",)),
    ("interchange.history.DomeFeature", ("height",)),
    (
        "interchange.history.ExtrusionFeature",
        (
            "length",
            "end_condition",
            "reversed",
            "symmetric",
            "direction",
            "second_length",
            "second_end_condition",
            "offset",
            "second_offset",
            "draft_angle",
            "second_draft_angle",
            "up_to_reference",
            "second_up_to_reference",
        ),
    ),
    (
        "interchange.history.FeatureConfigurationState",
        ("configuration_id", "suppressed", "parameter_override_ids"),
    ),
    (
        "interchange.history.FeatureStep",
        (
            "id",
            "name",
            "kind",
            "order",
            "input_feature_ids",
            "sketch_id",
            "parameter_ids",
            "operation",
            "definition",
            "selection_ids",
            "suppressed",
            "configuration_states",
            "provenance",
            "attributes",
        ),
    ),
    ("interchange.history.FilletFeature", ("radius", "variable_radius_parameter_ids")),
    ("interchange.history.HoleFeature", ("diameter", "depth", "end_condition")),
    (
        "interchange.history.LinearPatternFeature",
        ("spacing", "instance_count", "direction_selection_id", "reversed"),
    ),
    ("interchange.history.MoveBodyFeature", ("translation", "copy")),
    (
        "interchange.history.NativeFeatureDefinition",
        ("format_id", "type_id", "object_data"),
    ),
    (
        "interchange.history.ReferencePlaneFeature",
        ("support_plane_id", "reference_plane_id", "offset"),
    ),
    (
        "interchange.history.RevolutionFeature",
        ("angle", "axis_entity_id", "reversed", "symmetric"),
    ),
    ("interchange.history.ScaleFeature", ("factors",)),
    ("interchange.history.ShellFeature", ("thickness", "outward")),
    (
        "interchange.history.TopologySummary",
        (
            "solid_count",
            "shell_count",
            "face_count",
            "edge_count",
            "vertex_count",
            "volume",
            "surface_area",
            "bounding_box",
            "valid",
        ),
    ),
)
