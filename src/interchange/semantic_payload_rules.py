# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .payload_roles import PayloadRole
from .payload_rules import PayloadRule


# semantic evidence recovers payload roles when native format tags are incomplete
KSemanticPayloadRules = (
    PayloadRule(
        PayloadRole.KFeatureHistory, ".osmx", Schemas=frozenset({"catprtcont"})
    ),
    PayloadRule(
        PayloadRole.KAssemblyStructure, ".osmx", Schemas=frozenset({"catprodcont"})
    ),
    PayloadRule(PayloadRole.KBrep, ".cgm", Schemas=frozenset({"cgmgeom"})),
    PayloadRule(PayloadRole.KBrep, ".mfbrp", Schemas=frozenset({"catmfbrp"})),
    PayloadRule(PayloadRole.KTessellation, ".cgr", Schemas=frozenset({"catcgrcont"})),
    PayloadRule(
        PayloadRole.KBrep,
        "",
        Kinds=frozenset({"brep", "brep_mode", "brep_topology", "native_brep", "shape"}),
    ),
    PayloadRule(PayloadRole.KBrep, "", Kinds=frozenset({"resolved-assembly"})),
    PayloadRule(
        PayloadRole.KTessellation,
        "",
        Kinds=frozenset({"native_tessellation", "tessellation"}),
    ),
    PayloadRule(
        PayloadRole.KFeatureHistory,
        "",
        Kinds=frozenset({"feature-records", "feature_history", "native_feature_graph"}),
    ),
    PayloadRule(
        PayloadRole.KAssemblyStructure,
        "",
        Kinds=frozenset({"assembly_structure", "mate-list", "native_product_graph"}),
    ),
    PayloadRule(PayloadRole.KDocument, "", Kinds=frozenset({"native_document"})),
)
