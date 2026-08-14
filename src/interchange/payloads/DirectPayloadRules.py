# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.payloads.PayloadRoles import PayloadRole
from interchange.payloads.PayloadRules import PayloadRule


# direct format evidence preserves exact roles before generic semantic fallbacks
KDirectPayloadRules = (
    PayloadRule(
        PayloadRole.KDocument,
        ".catpart",
        frozenset({"catia.v5", "catia.v5.cfv2"}),
        frozenset({"native_document"}),
        frozenset({"catpart", "catprtcont"}),
    ),
    PayloadRule(
        PayloadRole.KDocument,
        ".catproduct",
        frozenset({"catia.v5", "catia.v5.cfv2"}),
        frozenset({"native_document"}),
        frozenset({"catproduct", "catprodcont"}),
    ),
    PayloadRule(
        PayloadRole.KDocument,
        ".FCStd",
        frozenset({"freecad.fcstd"}),
        frozenset({"native_document"}),
    ),
    PayloadRule(
        PayloadRole.KDocument,
        ".sldprt",
        frozenset({"solidworks.sldprt"}),
        frozenset({"native_document"}),
    ),
    PayloadRule(
        PayloadRole.KDocument,
        ".sldasm",
        frozenset({"solidworks.sldasm"}),
        frozenset({"native_document"}),
    ),
    PayloadRule(
        PayloadRole.KVerification,
        ".sha256",
        Kinds=frozenset({"native_document_binding"}),
        Schemas=frozenset({"sha256"}),
    ),
    PayloadRule(
        PayloadRole.KFeatureHistory,
        ".osmx",
        frozenset({"catia.v5.osmx"}),
        frozenset({"native_feature_graph"}),
    ),
    PayloadRule(
        PayloadRole.KAssemblyStructure,
        ".osmx",
        frozenset({"catia.v5.osmx"}),
        frozenset({"native_product_graph"}),
    ),
    PayloadRule(
        PayloadRole.KAssemblyStructure, ".bin", frozenset({"solidworks.mates"})
    ),
    PayloadRule(PayloadRole.KBrep, ".x_b", frozenset({"parasolid", "parasolid.x_b"})),
    PayloadRule(PayloadRole.KBrep, ".x_t", frozenset({"parasolid.x_t"})),
    PayloadRule(PayloadRole.KBrep, ".sat", frozenset({"acis.sat"})),
    PayloadRule(PayloadRole.KBrep, ".sab", frozenset({"acis.sab"})),
    PayloadRule(PayloadRole.KBrep, "", frozenset({"acis"})),
    PayloadRule(
        PayloadRole.KBrep,
        ".brep",
        frozenset({"freecad.brep", "opencascade", "opencascade.brep"}),
    ),
    PayloadRule(PayloadRole.KBrep, ".cgm", frozenset({"catia.cgm"})),
    PayloadRule(PayloadRole.KBrep, ".mfbrp", frozenset({"catia.v5.mfbrp"})),
    PayloadRule(PayloadRole.KBrep, ".bin", frozenset({"catia.v5.brep-mode"})),
    PayloadRule(PayloadRole.KTessellation, ".cgr", frozenset({"catia.cgr"})),
)
