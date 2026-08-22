# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import sys as System
from pathlib import Path as FilePath

# repository location keeps reverse engineering tools independent from package installation
KRepositoryRoot = FilePath(__file__).resolve().parents[2]


# source insertion permits direct script execution without requiring a mutable environment
def EnableSource() -> None:
    SourceText = str(KRepositoryRoot / "src")
    if SourceText not in System.path:
        System.path.insert(0, SourceText)
