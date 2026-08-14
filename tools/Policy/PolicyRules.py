# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations


# large directories become hard to navigate so direct ownership stays intentionally bounded
KMaxDirectFiles = 32

# ascii stems keep imports predictable across every operating system and review tool
KStemPattern = r"^[A-Z][A-Za-z]*$"

# fixed ecosystem identities stay explicit so ordinary nested files cannot borrow exemptions
KToolPathSet = frozenset(
    {
        ".gitattributes",
        ".github/CODE_OF_CONDUCT.md",
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/dependabot.yml",
        ".gitignore",
        ".hoplite/settings.json",
        ".kiro/settings/mcp.json",
        "HEADER_NOTICE",
        "pyproject.toml",
        "uv.lock",
    }
)

# pytest discovery and python packages require these exact lowercase standard names
KStandardNames = frozenset({"__init__.py", "conftest.py"})

# native libraries keep vendor identity names because loaders resolve those names externally
KBinarySuffixes = frozenset({".dll"})
