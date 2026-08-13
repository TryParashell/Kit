# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# historical method identities stay explicit because reflection includes defining class and module
KPythonCompatMethods = (
    (
        "interchange.assembly.AssemblyData",
        ("definition", "document", "children"),
    ),
    (
        "interchange.assembly.Matrix4",
        ("rows", "is_finite", "transform_point"),
    ),
    ("interchange.brep.BrepModel", ("validate",)),
    (
        "interchange.document.CadDocument",
        (
            "to_dict",
            "from_dict",
            "to_json",
            "from_json",
            "write_json",
            "read_json",
            "validate",
            "_validate_assembly",
            "assert_valid",
            "parameter",
            "sketch",
            "feature",
            "plane",
            "_lookup",
        ),
    ),
    ("interchange.history.AdapterCapabilities", ("supports",)),
)
