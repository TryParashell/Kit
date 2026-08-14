# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from typing import Mapping as TypeMap


# exceptional legacy fields stay explicit because three names differ from their wire spellings
KPythonCompatAnnots: TypeMap[str, tuple[str, ...]] = {
    "ComponentDef": (
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
    "ConstraintRef": ("entity_id", "point"),
    "SelectPathElem": ("entity_kind", "entity_id", "subelement"),
}
