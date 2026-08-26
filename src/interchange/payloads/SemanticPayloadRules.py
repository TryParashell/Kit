# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.payloads.PayloadRoles import PayloadRole
from interchange.payloads.PayloadRuleModel import PayloadRule

# semantic evidence recovers payload roles when native format tags are incomplete
KSemanticPayloadRules = (
    PayloadRule(
        PayloadRole.KFeatureHistory, ".osmx", schemas=frozenset({"catprtcont"})
    ),
    PayloadRule(
        PayloadRole.KAssemblyStructure, ".osmx", schemas=frozenset({"catprodcont"})
    ),
    PayloadRule(PayloadRole.KBrep, ".cgm", schemas=frozenset({"cgmgeom"})),
    PayloadRule(PayloadRole.KBrep, ".mfbrp", schemas=frozenset({"catmfbrp"})),
    PayloadRule(PayloadRole.KTessellation, ".cgr", schemas=frozenset({"catcgrcont"})),
    PayloadRule(
        PayloadRole.KBrep,
        "",
        kinds=frozenset({"brep", "brep_mode", "brep_topology", "native_brep", "shape"}),
    ),
    PayloadRule(PayloadRole.KBrep, "", kinds=frozenset({"resolved-assembly"})),
    PayloadRule(
        PayloadRole.KTessellation,
        "",
        kinds=frozenset({"native_tessellation", "tessellation"}),
    ),
    PayloadRule(
        PayloadRole.KFeatureHistory,
        "",
        kinds=frozenset({"feature-records", "feature_history", "native_feature_graph"}),
    ),
    PayloadRule(
        PayloadRole.KAssemblyStructure,
        "",
        kinds=frozenset({"assembly_structure", "mate-list", "native_product_graph"}),
    ),
    PayloadRule(PayloadRole.KDocument, "", kinds=frozenset({"native_document"})),
)
