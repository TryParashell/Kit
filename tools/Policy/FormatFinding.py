# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from tools.Policy.PathFinding import PathFinding


# escaped paths keep each diagnostic on one line even for unusual legal filenames
def FormatFinding(FindingInfo: PathFinding) -> str:
    return (
        f"{FindingInfo.RepoPath!r}: {FindingInfo.RuleCode}: "
        f"{FindingInfo.MessageText}"
    )
