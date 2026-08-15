# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# historical brep fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsBrep = (
    (
        "interchange.brep.BrepBody",
        (
            "id",
            "provenance",
            "attributes",
            "region_ids",
            "transform",
            "design_body_id",
            "wire_ids",
            "vertex_ids",
        ),
    ),
    (
        "interchange.brep.BrepCoedge",
        ("id", "provenance", "attributes", "edge_id", "pcurve_id", "reversed"),
    ),
    ("interchange.brep.BrepCurve", ("id", "provenance", "attributes")),
    (
        "interchange.brep.BrepEdge",
        (
            "id",
            "provenance",
            "attributes",
            "start_vertex_id",
            "end_vertex_id",
            "curve_id",
            "start_parameter",
            "end_parameter",
            "tolerance",
            "degenerate",
        ),
    ),
    ("interchange.brep.BrepEntity", ("id", "provenance", "attributes")),
    (
        "interchange.brep.BrepFace",
        (
            "id",
            "provenance",
            "attributes",
            "surface_id",
            "loop_ids",
            "same_sense",
            "tolerance",
        ),
    ),
    (
        "interchange.brep.BrepFaceUse",
        ("id", "provenance", "attributes", "face_id", "reversed"),
    ),
    (
        "interchange.brep.BrepLoop",
        ("id", "provenance", "attributes", "coedge_ids", "outer"),
    ),
    (
        "interchange.brep.BrepModel",
        (
            "curves",
            "pcurves",
            "surfaces",
            "vertices",
            "edges",
            "coedges",
            "loops",
            "wires",
            "faces",
            "face_uses",
            "shells",
            "shell_uses",
            "regions",
            "bodies",
            "schema_version",
        ),
    ),
    ("interchange.brep.BrepPcurve", ("id", "provenance", "attributes")),
    (
        "interchange.brep.BrepRegion",
        ("id", "provenance", "attributes", "shell_use_ids", "solid"),
    ),
    (
        "interchange.brep.BrepShell",
        ("id", "provenance", "attributes", "face_use_ids", "closed"),
    ),
    (
        "interchange.brep.BrepShellUse",
        ("id", "provenance", "attributes", "shell_id", "reversed"),
    ),
    ("interchange.brep.BrepSurface", ("id", "provenance", "attributes")),
    (
        "interchange.brep.BrepVertex",
        ("id", "provenance", "attributes", "point", "tolerance"),
    ),
    (
        "interchange.brep.BrepWire",
        ("id", "provenance", "attributes", "coedge_ids", "closed"),
    ),
    (
        "interchange.brep.CircleCurve",
        (
            "id",
            "provenance",
            "attributes",
            "center",
            "axis",
            "reference_direction",
            "radius",
        ),
    ),
    (
        "interchange.brep.CirclePcurve",
        ("id", "provenance", "attributes", "center", "radius"),
    ),
    (
        "interchange.brep.ConeSurface",
        (
            "id",
            "provenance",
            "attributes",
            "origin",
            "axis",
            "reference_direction",
            "radius",
            "half_angle",
        ),
    ),
    (
        "interchange.brep.CylinderSurface",
        (
            "id",
            "provenance",
            "attributes",
            "origin",
            "axis",
            "reference_direction",
            "radius",
        ),
    ),
    (
        "interchange.brep.EllipseCurve",
        (
            "id",
            "provenance",
            "attributes",
            "center",
            "axis",
            "reference_direction",
            "major_radius",
            "minor_radius",
        ),
    ),
    (
        "interchange.brep.IntersectionCurve",
        (
            "id",
            "provenance",
            "attributes",
            "first_surface_id",
            "second_surface_id",
            "samples",
            "tolerance",
        ),
    ),
    (
        "interchange.brep.LineCurve",
        ("id", "provenance", "attributes", "origin", "direction"),
    ),
    (
        "interchange.brep.LinePcurve",
        ("id", "provenance", "attributes", "origin", "direction"),
    ),
    (
        "interchange.brep.NativeCurve",
        ("id", "provenance", "attributes", "format_id", "entity_type", "data"),
    ),
    (
        "interchange.brep.NativePcurve",
        ("id", "provenance", "attributes", "format_id", "entity_type", "data"),
    ),
    (
        "interchange.brep.NativeSurface",
        ("id", "provenance", "attributes", "format_id", "entity_type", "data"),
    ),
    (
        "interchange.brep.NurbsCurve",
        (
            "id",
            "provenance",
            "attributes",
            "degree",
            "control_points",
            "knots",
            "multiplicities",
            "weights",
            "periodic",
        ),
    ),
    (
        "interchange.brep.NurbsPcurve",
        (
            "id",
            "provenance",
            "attributes",
            "degree",
            "control_points",
            "knots",
            "multiplicities",
            "weights",
            "periodic",
        ),
    ),
    (
        "interchange.brep.NurbsSurface",
        (
            "id",
            "provenance",
            "attributes",
            "degree_u",
            "degree_v",
            "control_points",
            "knots_u",
            "knots_v",
            "multiplicities_u",
            "multiplicities_v",
            "weights",
            "periodic_u",
            "periodic_v",
        ),
    ),
    (
        "interchange.brep.OffsetSurface",
        ("id", "provenance", "attributes", "base_surface_id", "distance"),
    ),
    (
        "interchange.brep.PlaneSurface",
        ("id", "provenance", "attributes", "origin", "normal", "reference_direction"),
    ),
    (
        "interchange.brep.SphereSurface",
        (
            "id",
            "provenance",
            "attributes",
            "center",
            "axis",
            "reference_direction",
            "radius",
        ),
    ),
    (
        "interchange.brep.TorusSurface",
        (
            "id",
            "provenance",
            "attributes",
            "center",
            "axis",
            "reference_direction",
            "major_radius",
            "minor_radius",
        ),
    ),
)
