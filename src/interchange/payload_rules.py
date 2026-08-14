# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from .model_base import ModelBase, ModelDataMut
from .payload_roles import PayloadRole


# legacy payload inference needs declarative evidence that remains independently testable
@ModelDataMut(
    DefaultMap={
        "FormatIds": frozenset(),
        "Kinds": frozenset(),
        "Schemas": frozenset(),
        "SourceSuffixes": frozenset(),
    }
)
class PayloadRule(ModelBase):
    ValueRole: PayloadRole
    FileExtension: str
    FormatIds: frozenset[str]
    Kinds: frozenset[str]
    Schemas: frozenset[str]
    SourceSuffixes: frozenset[str]


# suffix evidence remains explicit because unknown formats still expose useful filenames
KSuffixPayloadRules = (
    PayloadRule(PayloadRole.KBrep, ".brep", SourceSuffixes=frozenset({".brep"})),
    PayloadRule(PayloadRole.KBrep, ".brp", SourceSuffixes=frozenset({".brp"})),
    PayloadRule(PayloadRole.KBrep, ".x_b", SourceSuffixes=frozenset({".x_b"})),
    PayloadRule(PayloadRole.KBrep, ".x_t", SourceSuffixes=frozenset({".x_t"})),
    PayloadRule(PayloadRole.KBrep, ".sat", SourceSuffixes=frozenset({".sat"})),
    PayloadRule(PayloadRole.KBrep, ".sab", SourceSuffixes=frozenset({".sab"})),
    PayloadRule(PayloadRole.KBrep, ".cgm", SourceSuffixes=frozenset({".cgm"})),
    PayloadRule(PayloadRole.KBrep, ".mfbrp", SourceSuffixes=frozenset({".mfbrp"})),
    PayloadRule(PayloadRole.KTessellation, ".cgr", SourceSuffixes=frozenset({".cgr"})),
    PayloadRule(
        PayloadRole.KVerification, ".sha256", SourceSuffixes=frozenset({".sha256"})
    ),
    PayloadRule(PayloadRole.KDocument, ".FCStd", SourceSuffixes=frozenset({".fcstd"})),
    PayloadRule(
        PayloadRole.KDocument, ".sldprt", SourceSuffixes=frozenset({".sldprt"})
    ),
    PayloadRule(
        PayloadRole.KDocument, ".sldasm", SourceSuffixes=frozenset({".sldasm"})
    ),
    PayloadRule(
        PayloadRole.KDocument, ".catpart", SourceSuffixes=frozenset({".catpart"})
    ),
    PayloadRule(
        PayloadRole.KDocument, ".catproduct", SourceSuffixes=frozenset({".catproduct"})
    ),
)


from .payload_rule_data import KFormatPayloadRules


# legacy payload recovery needs ordered evidence matching historical output
KLegacyPayloadRules = KFormatPayloadRules + KSuffixPayloadRules
