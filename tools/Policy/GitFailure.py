# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations


# repository access failures need a dedicated boundary so policy violations remain distinguishable
class GitFailure(RuntimeError):

    # callers need useful git context without depending on subprocess implementation details
    def __init__(CaseSelf, MessageText: str) -> None:
        super().__init__(MessageText)
