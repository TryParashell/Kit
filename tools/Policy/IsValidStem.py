# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import re as Regex

from tools.Policy.PolicyRules import KStemPattern


# one predicate keeps filename enforcement identical across full and changed scans
def IsValidStem(StemText: str) -> bool:
    return Regex.fullmatch(KStemPattern, StemText) is not None
