# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from .direct_payload_rules import KDirectPayloadRules
from .semantic_payload_rules import KSemanticPayloadRules


# format evidence stays ordered because stronger native tags must win before fallbacks
KFormatPayloadRules = KDirectPayloadRules + KSemanticPayloadRules
