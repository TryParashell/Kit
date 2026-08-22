# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from interchange.payloads.PayloadRoles import PayloadRole
from interchange.payloads.PayloadRuleModel import PayloadRule

# suffix evidence remains explicit because unknown formats still expose useful filenames
KSuffixPayloadRules = (
    PayloadRule(PayloadRole.KBrep, ".brep", source_suffixes=frozenset({".brep"})),
    PayloadRule(PayloadRole.KBrep, ".brp", source_suffixes=frozenset({".brp"})),
    PayloadRule(PayloadRole.KBrep, ".x_b", source_suffixes=frozenset({".x_b"})),
    PayloadRule(PayloadRole.KBrep, ".x_t", source_suffixes=frozenset({".x_t"})),
    PayloadRule(PayloadRole.KBrep, ".sat", source_suffixes=frozenset({".sat"})),
    PayloadRule(PayloadRole.KBrep, ".sab", source_suffixes=frozenset({".sab"})),
    PayloadRule(PayloadRole.KBrep, ".cgm", source_suffixes=frozenset({".cgm"})),
    PayloadRule(PayloadRole.KBrep, ".mfbrp", source_suffixes=frozenset({".mfbrp"})),
    PayloadRule(PayloadRole.KTessellation, ".cgr", source_suffixes=frozenset({".cgr"})),
    PayloadRule(
        PayloadRole.KVerification, ".sha256", source_suffixes=frozenset({".sha256"})
    ),
    PayloadRule(PayloadRole.KDocument, ".FCStd", source_suffixes=frozenset({".fcstd"})),
    PayloadRule(
        PayloadRole.KDocument, ".sldprt", source_suffixes=frozenset({".sldprt"})
    ),
    PayloadRule(
        PayloadRole.KDocument, ".sldasm", source_suffixes=frozenset({".sldasm"})
    ),
    PayloadRule(
        PayloadRole.KDocument, ".catpart", source_suffixes=frozenset({".catpart"})
    ),
    PayloadRule(
        PayloadRole.KDocument, ".catproduct", source_suffixes=frozenset({".catproduct"})
    ),
)


from interchange.payloads.PayloadRuleData import KFormatPayloadRules

# legacy payload recovery needs ordered evidence matching historical output
KLegacyPayloadRules: tuple[PayloadRule, ...] = KFormatPayloadRules + KSuffixPayloadRules
