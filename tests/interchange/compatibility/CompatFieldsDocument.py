# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# historical document fields stay isolated so dataclass reflection expectations remain reviewable
KCompatFieldsDocument = (
    (
        "interchange.document.CadDocument",
        (
            "source",
            "configurations",
            "parameters",
            "support_planes",
            "sketches",
            "selections",
            "feature_timeline",
            "bodies",
            "meshes",
            "brep_payloads",
            "diagnostics",
            "capabilities",
            "metadata",
            "units",
            "schema_version",
            "assembly",
            "brep",
        ),
    ),
)
